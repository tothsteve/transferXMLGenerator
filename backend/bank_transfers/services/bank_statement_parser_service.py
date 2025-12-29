"""
Bank statement parsing service.

This service handles the complete PDF parsing workflow:
1. File upload and duplicate detection
2. Bank detection and adapter selection
3. PDF parsing
4. Transaction storage
5. Invoice matching
"""

import hashlib
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
from django.db import transaction as db_transaction
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile

from ..models import BankStatement, BankTransaction, Company
from ..bank_adapters import BankAdapterFactory, BankStatementParseError

logger = logging.getLogger(__name__)


def sanitize_raw_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw_data to JSON-serializable format.

    Handles date, datetime, and Decimal objects that can't be directly
    serialized to JSON for PostgreSQL JSONField storage.
    """
    if not isinstance(data, dict):
        return {}

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, (date, datetime)):
            sanitized[key] = value.isoformat()
        elif isinstance(value, Decimal):
            sanitized[key] = str(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_raw_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_raw_data(item) if isinstance(item, dict)
                else item.isoformat() if isinstance(item, (date, datetime))
                else str(item) if isinstance(item, Decimal)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


class BankStatementParserService:
    """
    Service for parsing bank statement PDFs and creating transactions.

    Usage:
        service = BankStatementParserService(company, user)
        statement = service.parse_and_save(uploaded_file)
    """

    def __init__(self, company: Company, user):
        self.company = company
        self.user = user

    def parse_and_save(self, uploaded_file: UploadedFile) -> BankStatement:
        """
        Parse uploaded PDF and save statement with transactions.

        Args:
            uploaded_file: Django UploadedFile instance

        Returns:
            BankStatement instance

        Raises:
            BankStatementParseError: If parsing fails
            ValueError: If file already exists or validation fails
        """
        # Read file bytes
        pdf_bytes = uploaded_file.read()
        uploaded_file.seek(0)  # Reset for potential re-reading

        # Calculate file hash for duplicate detection
        file_hash = self._calculate_hash(pdf_bytes)

        # Check for duplicate file
        if BankStatement.objects.filter(company=self.company, file_hash=file_hash).exists():
            raise ValueError("Ez a fájl már fel lett töltve korábban")

        # Detect bank and get adapter
        try:
            adapter = BankAdapterFactory.get_adapter(pdf_bytes, uploaded_file.name)
        except BankStatementParseError as e:
            logger.error(f"Bank detection failed: {e}")
            raise

        # Create statement record with UPLOADED status
        statement = BankStatement(
            company=self.company,
            bank_code=adapter.get_bank_code(),
            bank_name=adapter.get_bank_name(),
            bank_bic=adapter.get_bank_bic(),
            file_name=uploaded_file.name,
            file_hash=file_hash,
            file_size=uploaded_file.size,
            file_path=f"bank_statements/{self.company.id}/{file_hash[:8]}/{uploaded_file.name}",
            uploaded_by=self.user,
            uploaded_at=timezone.now(),
            status='UPLOADED',
            account_number='',  # Will be updated after parsing
            opening_balance=Decimal('0.00'),  # Will be updated after parsing
            statement_period_from=timezone.now().date(),  # Will be updated after parsing
            statement_period_to=timezone.now().date()  # Will be updated after parsing
        )
        statement.save()

        # Parse PDF in transaction
        try:
            with db_transaction.atomic():
                self._parse_statement(statement, adapter, pdf_bytes)

        except Exception as e:
            # Mark as ERROR and save error message
            statement.status = 'ERROR'
            statement.parse_error = str(e)
            statement.save()
            logger.error(f"Parsing failed for statement {statement.id}: {e}", exc_info=True)
            raise BankStatementParseError(f"Parsing failed: {e}") from e

        return statement

    def _parse_statement(self, statement: BankStatement, adapter, pdf_bytes: bytes):
        """
        Parse PDF and create transactions.

        Args:
            statement: BankStatement instance
            adapter: Bank adapter instance
            pdf_bytes: PDF file bytes
        """
        # Update status
        statement.status = 'PARSING'
        statement.parse_started_at = timezone.now()
        statement.save()

        # Parse PDF
        try:
            result = adapter.parse(pdf_bytes)
        except Exception as e:
            raise BankStatementParseError(f"Adapter parse failed: {e}") from e

        # Extract metadata and transactions
        metadata = result.get('metadata')
        transactions_data = result.get('transactions', [])

        if not metadata:
            raise BankStatementParseError("No metadata found in parse result")

        # Update statement with metadata
        statement.account_number = metadata.account_number
        statement.account_iban = metadata.account_iban
        statement.statement_period_from = metadata.period_from
        statement.statement_period_to = metadata.period_to
        statement.statement_number = metadata.statement_number
        statement.opening_balance = metadata.opening_balance
        statement.closing_balance = metadata.closing_balance or Decimal('0.00')

        # Check for duplicate statement period
        existing = BankStatement.objects.filter(
            company=self.company,
            bank_code=statement.bank_code,
            account_number=statement.account_number,
            statement_period_from=statement.statement_period_from,
            statement_period_to=statement.statement_period_to
        ).exclude(id=statement.id).first()

        if existing:
            raise ValueError(
                f"Már létezik kivonat ehhez az időszakhoz: "
                f"{statement.statement_period_from} - {statement.statement_period_to}"
            )

        # Create transactions
        created_count = 0
        for trans_data in transactions_data:
            self._create_transaction(statement, trans_data)
            created_count += 1

        # Calculate credit/debit statistics
        from django.db.models import Sum, Count, Q

        transaction_stats = BankTransaction.objects.filter(
            bank_statement=statement
        ).aggregate(
            credit_count=Count('id', filter=Q(amount__gt=0)),
            debit_count=Count('id', filter=Q(amount__lt=0)),
            total_credits=Sum('amount', filter=Q(amount__gt=0)),
            total_debits=Sum('amount', filter=Q(amount__lt=0))
        )

        # Update statement with statistics
        statement.total_transactions = created_count
        statement.credit_count = transaction_stats['credit_count'] or 0
        statement.debit_count = transaction_stats['debit_count'] or 0
        statement.total_credits = transaction_stats['total_credits'] or Decimal('0.00')
        statement.total_debits = abs(transaction_stats['total_debits'] or Decimal('0.00'))
        statement.status = 'PARSED'
        statement.parse_completed_at = timezone.now()
        statement.save()

        logger.info(
            f"Successfully parsed statement {statement.id}: "
            f"{created_count} transactions for {statement.bank_name} "
            f"{statement.account_number}"
        )

        # Run automatic transaction matching to NAV invoices
        try:
            from .transaction_matching_service import TransactionMatchingService

            matching_service = TransactionMatchingService(self.company)
            match_results = matching_service.match_statement(statement)

            # Update statement matched_count
            statement.matched_count = match_results['matched_count']
            statement.save()

            logger.info(
                f"Transaction matching completed for statement {statement.id}: "
                f"{match_results['matched_count']}/{created_count} transactions matched "
                f"({match_results['match_rate']}%), "
                f"{match_results['auto_paid_count']} invoices auto-marked as paid"
            )
        except Exception as e:
            logger.error(f"Transaction matching failed for statement {statement.id}: {e}", exc_info=True)
            # Don't fail the entire parsing if matching fails
            pass

    def _create_transaction(self, statement: BankStatement, trans_data) -> BankTransaction:
        """
        Create BankTransaction from normalized transaction data.

        Args:
            statement: BankStatement instance
            trans_data: NormalizedTransaction instance

        Returns:
            BankTransaction instance
        """
        transaction = BankTransaction(
            company=self.company,
            bank_statement=statement,

            # Core fields
            transaction_type=trans_data.transaction_type,
            booking_date=trans_data.booking_date,
            value_date=trans_data.value_date,
            amount=trans_data.amount,
            currency=trans_data.currency,
            description=trans_data.description,
            short_description=trans_data.short_description or '',

            # AFR/Transfer fields
            payment_id=trans_data.payment_id or '',
            transaction_id=trans_data.transaction_id or '',

            payer_name=trans_data.payer_name or '',
            payer_iban=trans_data.payer_iban or '',
            payer_account_number=trans_data.payer_account_number or '',
            payer_bic=trans_data.payer_bic or '',

            beneficiary_name=trans_data.beneficiary_name or '',
            beneficiary_iban=trans_data.beneficiary_iban or '',
            beneficiary_account_number=trans_data.beneficiary_account_number or '',
            beneficiary_bic=trans_data.beneficiary_bic or '',

            reference=trans_data.reference or '',
            partner_id=trans_data.partner_id or '',
            transaction_type_code=trans_data.transaction_type_code or '',
            fee_amount=trans_data.fee_amount,

            # POS/Card fields
            card_number=trans_data.card_number or '',
            merchant_name=trans_data.merchant_name or '',
            merchant_location=trans_data.merchant_location or '',
            original_amount=trans_data.original_amount,
            original_currency=trans_data.original_currency or '',
            exchange_rate=trans_data.exchange_rate,

            # Matching fields (will be filled by matching service)
            matched_invoice=None,
            match_confidence=Decimal('0.00'),
            match_method='',

            # Raw data from adapter - sanitize for JSON storage
            raw_data=sanitize_raw_data(trans_data.raw_data or {}),
        )

        transaction.save()

        # Auto-categorize system transactions (bank fees, interest)
        self._auto_categorize_system_transaction(transaction)

        return transaction

    def _auto_categorize_system_transaction(self, transaction: BankTransaction) -> None:
        """
        Auto-categorize system transactions that don't need invoice matching.

        Creates OtherCost record and marks transaction as "matched" for frontend display:
        - BANK_FEE: Bank fees and charges
        - INTEREST_CREDIT: Interest income
        - INTEREST_DEBIT: Interest charges

        These transactions will appear as matched on the frontend with method "SYSTEM_AUTO_CATEGORIZED".

        Args:
            transaction: BankTransaction instance
        """
        from decimal import Decimal
        from django.utils import timezone
        from ..models import OtherCost

        # Map transaction types to OtherCost categories
        SYSTEM_TRANSACTION_CATEGORIES = {
            'BANK_FEE': 'BANK_FEE',
            'INTEREST_CREDIT': 'INTEREST',
            'INTEREST_DEBIT': 'INTEREST',
        }

        category = SYSTEM_TRANSACTION_CATEGORIES.get(transaction.transaction_type)

        if category:
            # Create OtherCost record automatically
            OtherCost.objects.create(
                company=self.company,
                bank_transaction=transaction,
                category=category,
                amount=abs(transaction.amount),
                currency=transaction.currency,
                date=transaction.value_date,
                notes=f"Auto-categorized {transaction.transaction_type} from bank statement import",
                tags=f"auto-categorized,{transaction.transaction_type.lower()}"
            )

            # Mark transaction as "matched" for frontend display
            # This ensures it shows up as handled/categorized, not as unmatched
            transaction.match_confidence = Decimal('1.00')
            transaction.match_method = 'SYSTEM_AUTO_CATEGORIZED'
            transaction.matched_at = timezone.now()
            transaction.match_notes = (
                f"System transaction auto-categorized as {category}. "
                f"No invoice matching needed for {transaction.transaction_type}."
            )
            transaction.save()

            logger.info(
                f"Auto-categorized transaction {transaction.id} "
                f"({transaction.transaction_type}) as OtherCost category '{category}' "
                f"and marked as matched (SYSTEM_AUTO_CATEGORIZED)"
            )

    def _calculate_hash(self, file_bytes: bytes) -> str:
        """Calculate SHA256 hash of file"""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def get_supported_banks():
        """Get list of supported banks"""
        return BankAdapterFactory.list_supported_banks()
