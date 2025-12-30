"""
Transaction Matching Service - Auto-match bank transactions to NAV invoices.

This service implements 3 matching strategies with confidence scoring:
1. Reference Exact Match (1.00) - Invoice number or tax number in reference field
2. Amount + IBAN Match (0.95) - Exact amount + supplier IBAN match
3. Fuzzy Name Match (0.70-0.90) - Amount + name similarity

Auto-updates invoice payment status for high-confidence matches (≥0.90).
"""

import logging
from datetime import timedelta
from decimal import Decimal
from itertools import combinations
from typing import Dict, Any, Optional, Tuple, List
from django.db.models import QuerySet, Q
from django.utils import timezone
from rapidfuzz import fuzz

from ..models import BankStatement, BankTransaction, Invoice
from ..schemas.bank_statement import (
    TransactionMatchInput,
    TransactionMatchOutput,
    MatchedInvoiceInfo,
    MatchMethod,
)

logger = logging.getLogger(__name__)


class TransactionMatchingService:
    """
    Automatically match bank transactions to NAV invoices.

    Usage:
        service = TransactionMatchingService(company)
        results = service.match_statement(statement)
    """

    # Matching thresholds
    AUTO_PAYMENT_THRESHOLD = Decimal('0.90')  # Auto-mark invoice as PAID if confidence ≥ 0.90
    FUZZY_NAME_MIN_SIMILARITY = 70  # Minimum name similarity percentage (70%)
    AMOUNT_TOLERANCE_PERCENT = Decimal('0.01')  # ±1% tolerance for fuzzy amount matching
    CANDIDATE_DATE_RANGE_DAYS = 90  # ±90 days from transaction date

    # System transaction types that don't need matching (auto-categorized as OtherCost)
    SYSTEM_TRANSACTION_TYPES = [
        'BANK_FEE',          # Bank fees and charges
        'INTEREST_CREDIT',   # Interest income
        'INTEREST_DEBIT',    # Interest charges
    ]

    def __init__(self, company):
        """
        Initialize matching service for a company.

        Args:
            company: Company instance
        """
        self.company = company

    def match_statement(self, statement: BankStatement) -> Dict[str, Any]:
        """
        Match all unmatched transactions in a bank statement.

        Args:
            statement: BankStatement instance

        Returns:
            Dictionary with matching statistics:
            {
                'statement_id': int,
                'total_transactions': int,
                'matched_count': int,
                'match_rate': float,
                'auto_paid_count': int,
                'confidence_distribution': {
                    '1.00': int,
                    '0.95': int,
                    '0.85': int,
                    ...
                }
            }
        """
        logger.info(f"Starting transaction matching for statement {statement.id}")

        from ..models import BankTransactionInvoiceMatch

        # Get all unmatched transactions
        # Must check BOTH matched_invoice (old ForeignKey) AND many-to-many relationship
        matched_transaction_ids = BankTransactionInvoiceMatch.objects.filter(
            transaction__bank_statement=statement
        ).values_list('transaction_id', flat=True)

        transactions = BankTransaction.objects.filter(
            bank_statement=statement,
            matched_invoice__isnull=True,  # Old single match FK
            matched_transfer__isnull=True,  # Transfer match
            matched_reimbursement__isnull=True  # Reimbursement pair
        ).exclude(
            id__in=matched_transaction_ids  # Exclude batch matched transactions
        ).exclude(
            transaction_type__in=self.SYSTEM_TRANSACTION_TYPES  # Skip system transactions (auto-categorized)
        ).order_by('booking_date')

        matched_count = 0
        auto_paid_count = 0
        confidence_distribution = {}

        for transaction in transactions:
            result = self.match_transaction(transaction)

            if result['matched']:
                matched_count += 1

                # Track confidence distribution
                conf_str = str(result['confidence'])
                confidence_distribution[conf_str] = confidence_distribution.get(conf_str, 0) + 1

                # Track auto-payment updates
                if result.get('auto_paid'):
                    auto_paid_count += 1

        # Calculate TOTAL matched count (new matches + existing matches)
        total_transactions_in_statement = BankTransaction.objects.filter(
            bank_statement=statement
        ).count()

        # Count ALL matched transactions (including batch matches and auto-categorized OtherCost)
        total_matched = BankTransaction.objects.filter(
            bank_statement=statement
        ).filter(
            Q(matched_invoice__isnull=False) |
            Q(matched_transfer__isnull=False) |
            Q(matched_reimbursement__isnull=False) |
            Q(id__in=matched_transaction_ids) |
            Q(other_cost_detail__isnull=False)  # Include auto-categorized system transactions
        ).count()

        match_rate = (total_matched / total_transactions_in_statement * 100) if total_transactions_in_statement > 0 else 0

        logger.info(
            f"Matching completed for statement {statement.id}: "
            f"{matched_count} new matches, {total_matched}/{total_transactions_in_statement} total matched ({match_rate:.1f}%), "
            f"{auto_paid_count} invoices auto-marked as paid"
        )

        return {
            'statement_id': statement.id,
            'total_transactions': total_transactions_in_statement,
            'matched_count': total_matched,  # Return TOTAL matched (not just new)
            'match_rate': round(match_rate, 1),
            'auto_paid_count': auto_paid_count,
            'confidence_distribution': confidence_distribution
        }

    def match_transaction(self, transaction: BankTransaction, user=None) -> Dict[str, Any]:
        """
        Match a single transaction using priority cascade.

        Priority order:
        1. Transfer matching (from executed TransferBatch) - highest confidence
        2. Invoice matching (NAV invoices) - medium confidence
        3. Reimbursement pairing (internal offsetting) - manual review

        Args:
            transaction: BankTransaction instance
            user: User instance (optional) - if provided, indicates manual matching

        Returns:
            Dictionary with match result:
            {
                'matched': bool,
                'transfer_id': int (if matched to transfer),
                'invoice_id': int (if matched to invoice),
                'reimbursement_id': int (if matched to reimbursement),
                'confidence': Decimal (if matched),
                'method': str (if matched),
                'auto_paid': bool (if invoice was auto-marked as paid)
            }
        """
        # Skip system transactions (they're auto-categorized as OtherCost)
        if transaction.transaction_type in self.SYSTEM_TRANSACTION_TYPES:
            logger.debug(
                f"Skipping matching for system transaction {transaction.id} "
                f"(type={transaction.transaction_type}, auto-categorized as OtherCost)"
            )
            return {'matched': False, 'skipped': True, 'reason': 'system_transaction'}

        # Priority 1: Try transfer matching (highest confidence)
        result = self._try_transfer_matching(transaction, user)
        if result['matched']:
            return result

        # Priority 2: Try learned pattern matching (recurring subscriptions/expenses)
        result = self._try_learned_pattern_matching(transaction, user)
        if result['matched']:
            return result

        # Priority 3: Try invoice matching (medium confidence)
        result = self._try_invoice_matching(transaction, user)
        if result['matched']:
            return result

        # Priority 4: Try reimbursement pairing (requires manual review)
        result = self._try_reimbursement_matching(transaction, user)
        if result['matched']:
            return result

        # No match found
        logger.debug(f"No match found for transaction {transaction.id}")
        return {'matched': False}

    def match_transaction_to_invoices(
        self,
        input_data: TransactionMatchInput,
        user=None
    ) -> TransactionMatchOutput:
        """
        Type-safe manual transaction-to-invoice matching with Pydantic I/O.

        This method provides type-safe manual matching of bank transactions to NAV invoices,
        supporting both single and batch invoice matching.

        Args:
            input_data: TransactionMatchInput with transaction and invoice IDs
            user: User instance performing the match (optional)

        Returns:
            TransactionMatchOutput with match results and confidence

        Raises:
            ValueError: If transaction or invoices don't exist or belong to wrong company

        Example:
            >>> match_input = TransactionMatchInput(
            ...     transaction_id=456,
            ...     invoice_ids=[123, 789],
            ...     match_notes="Batch payment for 2 invoices"
            ... )
            >>> result = service.match_transaction_to_invoices(match_input, user=request.user)
            >>> print(f"Matched with {result.match_confidence} confidence")
        """
        from ..models import BankTransactionInvoiceMatch
        from django.utils import timezone

        # Get transaction
        try:
            transaction = BankTransaction.objects.get(
                id=input_data.transaction_id,
                bank_statement__company=self.company
            )
        except BankTransaction.DoesNotExist:
            return TransactionMatchOutput(
                success=False,
                transaction_id=input_data.transaction_id,
                total_matched_amount=Decimal('0'),
                transaction_amount=Decimal('0'),
                match_confidence=Decimal('0'),
                match_method=MatchMethod.MANUAL,
                errors=[f"Transaction {input_data.transaction_id} not found or belongs to different company"]
            )

        # Get invoices
        invoices = Invoice.objects.filter(
            id__in=input_data.invoice_ids,
            company=self.company
        )

        if not invoices.exists():
            return TransactionMatchOutput(
                success=False,
                transaction_id=input_data.transaction_id,
                total_matched_amount=Decimal('0'),
                transaction_amount=transaction.amount,
                match_confidence=Decimal('0'),
                match_method=MatchMethod.MANUAL,
                errors=["No invoices found with provided IDs for this company"]
            )

        if invoices.count() != len(input_data.invoice_ids):
            return TransactionMatchOutput(
                success=False,
                transaction_id=input_data.transaction_id,
                total_matched_amount=Decimal('0'),
                transaction_amount=transaction.amount,
                match_confidence=Decimal('0'),
                match_method=MatchMethod.MANUAL,
                errors=["Some invoice IDs not found or belong to different company"]
            )

        # Calculate total matched amount
        total_matched_amount = sum(inv.invoice_gross_amount for inv in invoices)

        # Determine if this is a batch match
        is_batch_match = len(invoices) > 1

        # Set match method
        match_method = MatchMethod.MANUAL_BATCH if is_batch_match else MatchMethod.MANUAL

        # Build match notes
        match_notes = input_data.match_notes or ""
        if is_batch_match:
            match_notes = f"Manual batch match to {len(invoices)} invoices. " + match_notes

        # Create matches with full confidence for manual matches
        matched_invoice_infos = []
        for invoice in invoices:
            # Create or update match record
            match_record, created = BankTransactionInvoiceMatch.objects.update_or_create(
                transaction=transaction,
                invoice=invoice,
                defaults={
                    'match_confidence': Decimal('1.00'),  # Full confidence for manual
                    'match_method': 'MANUAL_BATCH' if is_batch_match else 'MANUAL',
                    'matched_at': timezone.now(),
                    'matched_by': user,
                    'match_notes': match_notes,
                    'is_approved': True,
                    'approved_at': timezone.now(),
                    'approved_by': user,
                }
            )

            matched_invoice_infos.append(MatchedInvoiceInfo(
                invoice_id=invoice.id,
                invoice_number=invoice.nav_invoice_number or f"Invoice #{invoice.id}",
                amount=invoice.invoice_gross_amount,
                supplier_name=invoice.supplier_name
            ))

            # Auto-mark invoice as PAID for manual matches
            if invoice.payment_status == 'UNPAID':
                invoice.mark_as_paid(
                    payment_date=transaction.booking_date,
                    auto_marked=False  # Manual match
                )

        # Update transaction with match metadata
        transaction.match_confidence = Decimal('1.00')
        transaction.match_method = 'MANUAL_BATCH' if is_batch_match else 'MANUAL'
        transaction.matched_at = timezone.now()
        transaction.matched_by = user
        transaction.match_notes = match_notes
        transaction.save()

        logger.info(
            f"Manual {'batch ' if is_batch_match else ''}match: Transaction {transaction.id} "
            f"matched to {len(invoices)} invoice(s) - Total: {total_matched_amount}"
        )

        return TransactionMatchOutput(
            success=True,
            transaction_id=transaction.id,
            is_batch_match=is_batch_match,
            matched_invoices=matched_invoice_infos,
            total_matched_amount=total_matched_amount,
            transaction_amount=transaction.amount,
            match_confidence=Decimal('1.00'),
            match_method=match_method,
            match_notes=match_notes,
            errors=[]
        )

    def _try_transfer_matching(self, transaction: BankTransaction, user=None) -> Dict[str, Any]:
        """
        Try to match transaction to executed Transfer from TransferBatch.

        Args:
            transaction: BankTransaction instance
            user: User instance (optional) for manual matching

        Returns:
            Match result dictionary
        """
        from django.utils import timezone

        matched_transfer, confidence = self._match_by_transfer(transaction)

        if not matched_transfer:
            return {'matched': False}

        # Save match to transaction with metadata
        transaction.matched_transfer = matched_transfer
        transaction.match_confidence = confidence
        transaction.match_method = 'TRANSFER_EXACT'
        transaction.matched_at = timezone.now()
        transaction.matched_by = user  # NULL for automatic, User for manual
        transaction.match_notes = (
            f"Matched to Transfer #{matched_transfer.id} "
            f"({matched_transfer.beneficiary.name}) - "
            f"Amount: {matched_transfer.amount} {matched_transfer.currency} - "
            f"{'Manual match' if user else 'Automatic match'}"
        )
        transaction.save()

        logger.info(
            f"Transaction {transaction.id} matched to transfer {matched_transfer.id} "
            f"({matched_transfer.beneficiary.name}) via TRANSFER_EXACT (confidence: {confidence})"
        )

        return {
            'matched': True,
            'transfer_id': matched_transfer.id,
            'confidence': confidence,
            'method': 'TRANSFER_EXACT',
            'auto_paid': False  # Transfers don't have payment status
        }

    def _try_invoice_matching(self, transaction: BankTransaction, user=None) -> Dict[str, Any]:
        """
        Try to match transaction to NAV invoice(s).

        Supports both single invoice matching and batch invoice matching (one payment for multiple invoices).

        Args:
            transaction: BankTransaction instance
            user: User instance (optional) for manual matching

        Returns:
            Match result dictionary
        """
        from django.utils import timezone
        from ..models import BankTransactionInvoiceMatch

        # Get candidate invoices for matching
        candidate_invoices = self._get_candidate_invoices(transaction)

        if not candidate_invoices.exists():
            return {'matched': False}

        # Try matching strategies in order of confidence
        matched_invoice = None
        matched_invoices_batch = []
        confidence = Decimal('0.00')
        method = ''

        # Strategy 1: Reference Exact Match (highest confidence - single invoice)
        matched_invoice, confidence = self._match_by_reference(transaction, candidate_invoices)
        if matched_invoice:
            method = 'REFERENCE_EXACT'

        # Strategy 2: Amount + IBAN Match (exact amount + account - single invoice)
        if not matched_invoice:
            matched_invoice, confidence = self._match_by_amount_iban(transaction, candidate_invoices)
            if matched_invoice:
                method = 'AMOUNT_IBAN'

        # Strategy 3: Amount + Date Only (exact amount - single invoice)
        if not matched_invoice:
            matched_invoice, confidence = self._match_by_amount_date_only(transaction, candidate_invoices)
            if matched_invoice:
                method = 'AMOUNT_DATE_ONLY'

        # Strategy 4: Fuzzy Name Match (amount + name similarity - single invoice)
        if not matched_invoice:
            matched_invoice, confidence = self._match_by_fuzzy_name(transaction, candidate_invoices)
            if matched_invoice:
                method = 'FUZZY_NAME'

        # Strategy 5: Batch Invoice Match (multiple invoices - only if no single match found)
        if not matched_invoice:
            matched_invoices_batch = self._match_by_batch_invoices(transaction, candidate_invoices)
            if matched_invoices_batch:
                method = 'BATCH_INVOICES'
                # All invoices in batch have same confidence
                confidence = matched_invoices_batch[0][1]

        # If no match found
        if not matched_invoice and not matched_invoices_batch:
            return {'matched': False}

        # === Handle BATCH match (multiple invoices) ===
        if matched_invoices_batch:
            invoice_numbers = ', '.join(inv.nav_invoice_number for inv, _ in matched_invoices_batch)
            total_amount = sum(inv.invoice_gross_amount for inv, _ in matched_invoices_batch)

            # Build match notes
            match_notes = (
                f"Batch match to {len(matched_invoices_batch)} invoices: {invoice_numbers} - "
                f"{matched_invoices_batch[0][0].supplier_name} - "
                f"Total: {total_amount} HUF - "
                f"Method: {method} (confidence: {confidence}) - "
                f"{'Manual match' if user else 'Automatic match'}"
            )

            # Save transaction metadata
            transaction.match_confidence = confidence
            transaction.match_method = method
            transaction.matched_at = timezone.now()
            transaction.matched_by = user
            transaction.match_notes = match_notes
            transaction.save()

            # Create BankTransactionInvoiceMatch records for each invoice
            auto_paid_count = 0
            invoice_ids = []

            for invoice, inv_confidence in matched_invoices_batch:
                # Create match record in through table
                BankTransactionInvoiceMatch.objects.create(
                    transaction=transaction,
                    invoice=invoice,
                    match_confidence=inv_confidence,
                    match_method=method,
                    matched_by=user,
                    match_notes=f"Part of batch payment ({len(matched_invoices_batch)} invoices)"
                )
                invoice_ids.append(invoice.id)

                # Auto-update invoice payment status if high confidence
                if inv_confidence >= self.AUTO_PAYMENT_THRESHOLD and invoice.payment_status != 'PAID':
                    self._update_invoice_payment_status(invoice, transaction, auto=True)
                    auto_paid_count += 1

            logger.info(
                f"Transaction {transaction.id} matched to {len(matched_invoices_batch)} invoices "
                f"({invoice_numbers}) via {method} (confidence: {confidence}) - "
                f"{auto_paid_count} invoices auto-marked as paid"
            )

            return {
                'matched': True,
                'invoice_ids': invoice_ids,
                'batch_match': True,
                'invoice_count': len(matched_invoices_batch),
                'confidence': confidence,
                'method': method,
                'auto_paid': auto_paid_count > 0
            }

        # === Handle SINGLE invoice match ===
        # Build match notes with details
        match_notes = (
            f"Matched to Invoice #{matched_invoice.id} "
            f"({matched_invoice.nav_invoice_number}) - "
            f"{matched_invoice.supplier_name} - "
            f"Amount: {matched_invoice.invoice_gross_amount} HUF - "
            f"Method: {method} (confidence: {confidence}) - "
            f"{'Manual match' if user else 'Automatic match'}"
        )

        # Save match to transaction with metadata (backward compatibility)
        transaction.matched_invoice = matched_invoice
        transaction.match_confidence = confidence
        transaction.match_method = method
        transaction.matched_at = timezone.now()
        transaction.matched_by = user
        transaction.match_notes = match_notes
        transaction.save()

        # Also create BankTransactionInvoiceMatch record (new ManyToMany system)
        BankTransactionInvoiceMatch.objects.create(
            transaction=transaction,
            invoice=matched_invoice,
            match_confidence=confidence,
            match_method=method,
            matched_by=user,
            match_notes="Single invoice match"
        )

        logger.info(
            f"Transaction {transaction.id} matched to invoice {matched_invoice.id} "
            f"({matched_invoice.payment_status}) via {method} (confidence: {confidence})"
        )

        # Auto-update invoice payment status if high confidence AND invoice not already paid
        auto_paid = False
        if confidence >= self.AUTO_PAYMENT_THRESHOLD and matched_invoice.payment_status != 'PAID':
            self._update_invoice_payment_status(matched_invoice, transaction, auto=True)
            auto_paid = True
        elif matched_invoice.payment_status == 'PAID':
            logger.info(
                f"Invoice {matched_invoice.nav_invoice_number} already PAID - "
                f"match serves as payment verification"
            )

        return {
            'matched': True,
            'invoice_id': matched_invoice.id,
            'invoice_ids': [matched_invoice.id],
            'batch_match': False,
            'invoice_count': 1,
            'confidence': confidence,
            'method': method,
            'auto_paid': auto_paid
        }

    def _try_reimbursement_matching(self, transaction: BankTransaction, user=None) -> Dict[str, Any]:
        """
        Try to match transaction to offsetting reimbursement transaction.

        Args:
            transaction: BankTransaction instance
            user: User instance (optional) for manual matching

        Returns:
            Match result dictionary
        """
        from django.utils import timezone

        matched_reimbursement, confidence = self._match_by_reimbursement(transaction)

        if not matched_reimbursement:
            return {'matched': False}

        # Build match notes for both transactions
        match_timestamp = timezone.now()
        match_notes = (
            f"Reimbursement pair: TX #{transaction.id} ↔ TX #{matched_reimbursement.id} - "
            f"Amounts: {transaction.amount} ↔ {matched_reimbursement.amount} HUF - "
            f"Dates: {transaction.booking_date} ↔ {matched_reimbursement.booking_date} - "
            f"REQUIRES MANUAL REVIEW - "
            f"{'Manual match' if user else 'Automatic match'}"
        )

        # Save match to BOTH transactions (bidirectional) with metadata
        transaction.matched_reimbursement = matched_reimbursement
        transaction.match_confidence = confidence
        transaction.match_method = 'REIMBURSEMENT_PAIR'
        transaction.matched_at = match_timestamp
        transaction.matched_by = user
        transaction.match_notes = match_notes
        transaction.save()

        # Also update the paired transaction with same metadata
        matched_reimbursement.matched_reimbursement = transaction
        matched_reimbursement.match_confidence = confidence
        matched_reimbursement.match_method = 'REIMBURSEMENT_PAIR'
        matched_reimbursement.matched_at = match_timestamp
        matched_reimbursement.matched_by = user
        matched_reimbursement.match_notes = match_notes
        matched_reimbursement.save()

        logger.info(
            f"Transaction {transaction.id} paired with reimbursement transaction {matched_reimbursement.id} "
            f"(confidence: {confidence}) - MANUAL REVIEW RECOMMENDED"
        )

        return {
            'matched': True,
            'reimbursement_id': matched_reimbursement.id,
            'confidence': confidence,
            'method': 'REIMBURSEMENT_PAIR',
            'auto_paid': False
        }

    def _try_learned_pattern_matching(self, transaction: BankTransaction, user=None) -> Dict[str, Any]:
        """
        Try to match transaction to learned pattern from previous OtherCost categorizations.

        This enables automatic categorization of recurring transactions (subscriptions, utilities)
        based on exact merchant/beneficiary name matching.

        Supported transaction types:
        - POS_PURCHASE: Card payments (merchant_name)
        - TRANSFER_DEBIT: Outgoing transfers (beneficiary_name)
        - AFR_DEBIT: Automated transfers (beneficiary_name)

        Args:
            transaction: BankTransaction instance
            user: User instance (optional) for manual matching

        Returns:
            Match result dictionary
        """
        from decimal import Decimal
        from django.utils import timezone
        from ..models import OtherCost

        # Only process supported transaction types
        SUPPORTED_TYPES = ['POS_PURCHASE', 'TRANSFER_DEBIT', 'AFR_DEBIT']
        if transaction.transaction_type not in SUPPORTED_TYPES:
            return {'matched': False}

        # Get counterparty name based on transaction type
        if transaction.transaction_type == 'POS_PURCHASE':
            counterparty_name = transaction.merchant_name
        else:
            counterparty_name = transaction.beneficiary_name

        if not counterparty_name:
            return {'matched': False}

        # Normalize name for exact matching (case-insensitive)
        counterparty_norm = counterparty_name.strip().upper()

        # Find existing OtherCost records with matching counterparty
        # Only look at manually created OtherCost (not auto-categorized system transactions)
        existing_patterns = OtherCost.objects.filter(
            company=self.company,
            bank_transaction__isnull=False  # Only patterns from bank transactions
        ).select_related('bank_transaction').exclude(
            bank_transaction__transaction_type__in=self.SYSTEM_TRANSACTION_TYPES
        )

        for pattern in existing_patterns:
            pattern_tx = pattern.bank_transaction

            # Get pattern counterparty name
            if pattern_tx.transaction_type == 'POS_PURCHASE':
                pattern_name = pattern_tx.merchant_name
            else:
                pattern_name = pattern_tx.beneficiary_name

            if not pattern_name:
                continue

            # Exact match (case-insensitive)
            pattern_name_norm = pattern_name.strip().upper()
            if counterparty_norm == pattern_name_norm:
                # Found matching pattern! Create OtherCost with same category
                OtherCost.objects.create(
                    company=self.company,
                    bank_transaction=transaction,
                    category=pattern.category,
                    amount=abs(transaction.amount),
                    currency=transaction.currency,
                    date=transaction.value_date,
                    notes=f"Auto-categorized based on learned pattern from transaction #{pattern_tx.id} ({pattern_name})",
                    tags=f"learned-pattern,{pattern.category.lower()}"
                )

                # Mark transaction as matched
                transaction.match_confidence = Decimal('1.00')
                transaction.match_method = 'LEARNED_PATTERN'
                transaction.matched_at = timezone.now()
                transaction.matched_by = user
                transaction.match_notes = (
                    f"Learned pattern match: '{counterparty_name}' → Category: {pattern.category} "
                    f"(based on pattern from transaction #{pattern_tx.id})"
                )
                transaction.save()

                logger.info(
                    f"Transaction {transaction.id} auto-categorized as {pattern.category} "
                    f"using learned pattern from transaction {pattern_tx.id} "
                    f"(merchant: '{counterparty_name}')"
                )

                return {
                    'matched': True,
                    'confidence': Decimal('1.00'),
                    'method': 'LEARNED_PATTERN',
                    'auto_paid': False,
                    'pattern_source_id': pattern_tx.id,
                    'category': pattern.category
                }

        # No matching pattern found
        return {'matched': False}

    def _match_by_transfer(
        self,
        transaction: BankTransaction
    ) -> Tuple[Optional['Transfer'], Decimal]:
        """
        Match transaction to executed Transfer from TransferBatch.

        Logic:
        1. Get all Transfers from TransferBatches marked as used_in_bank=True
        2. Match by amount + date + beneficiary (account, name, or merchant name)
        3. Confidence: 1.00 (we created these transfers ourselves)

        Matching criteria:
        - Amount must match exactly
        - Date within ±14 days of execution date (to account for bank processing delays)
        - At least one of:
          * Account number match (exact)
          * Beneficiary name similarity ≥80%
          * Merchant name similarity ≥80% (for POS transactions)

        Args:
            transaction: BankTransaction instance

        Returns:
            Tuple of (matched_transfer, confidence) or (None, 0.00)
        """
        from ..models import Transfer, TransferBatch

        # Only match debit transactions (we pay out)
        if transaction.amount >= 0:
            return None, Decimal('0.00')

        amount = abs(transaction.amount)

        # Get all transfers from batches marked as used_in_bank
        executed_batches = TransferBatch.objects.filter(
            company=self.company,
            used_in_bank=True
        ).prefetch_related('transfers__beneficiary')

        # Get candidate transfers within ±14 days of transaction date
        # (Banks may process transfers with delays)
        date_min = transaction.booking_date - timedelta(days=14)
        date_max = transaction.booking_date + timedelta(days=14)

        for batch in executed_batches:
            for transfer in batch.transfers.all():
                # Check amount match
                if transfer.amount != amount:
                    continue

                # Check date match (±14 days from execution date)
                if not (date_min <= transfer.execution_date <= date_max):
                    continue

                # Check beneficiary match
                # Option 1: Account number match
                if transaction.beneficiary_account_number:
                    trans_account = self._clean_account_number(transaction.beneficiary_account_number)
                    beneficiary_account = self._clean_account_number(transfer.beneficiary.account_number)

                    if trans_account == beneficiary_account:
                        logger.debug(
                            f"Transfer match: transaction {transaction.id} → "
                            f"transfer {transfer.id} (account number match)"
                        )
                        return transfer, Decimal('1.00')

                # Option 2: Beneficiary name similarity ≥80%
                if transaction.beneficiary_name and transfer.beneficiary.name:
                    similarity = self._calculate_name_similarity(
                        transaction.beneficiary_name,
                        transfer.beneficiary.name
                    )

                    if similarity >= 80:
                        logger.debug(
                            f"Transfer match: transaction {transaction.id} → "
                            f"transfer {transfer.id} (name similarity {similarity}%)"
                        )
                        return transfer, Decimal('1.00')

                # Option 3: Merchant name similarity ≥80% (for POS transactions)
                if transaction.merchant_name and transfer.beneficiary.name:
                    similarity = self._calculate_name_similarity(
                        transaction.merchant_name,
                        transfer.beneficiary.name
                    )

                    if similarity >= 80:
                        logger.debug(
                            f"Transfer match: transaction {transaction.id} → "
                            f"transfer {transfer.id} (merchant name similarity {similarity}%)"
                        )
                        return transfer, Decimal('1.00')

        return None, Decimal('0.00')

    def _match_by_reimbursement(
        self,
        transaction: BankTransaction
    ) -> Tuple[Optional[BankTransaction], Decimal]:
        """
        Match transaction to offsetting reimbursement transaction.

        Logic:
        1. Find transactions with same absolute amount
        2. Opposite signs (one debit, one credit)
        3. Within ±5 days of each other
        4. Neither already matched to invoice/transfer
        5. Confidence: 0.70 (requires manual review)

        Args:
            transaction: BankTransaction instance

        Returns:
            Tuple of (matched_transaction, confidence) or (None, 0.00)
        """
        amount = abs(transaction.amount)

        # Date range: ±5 days
        date_min = transaction.booking_date - timedelta(days=5)
        date_max = transaction.booking_date + timedelta(days=5)

        # Find offsetting transactions
        candidates = BankTransaction.objects.filter(
            company=self.company,
            booking_date__gte=date_min,
            booking_date__lte=date_max,
            matched_invoice__isnull=True,  # Not matched to invoice
            matched_transfer__isnull=True,  # Not matched to transfer
            matched_reimbursement__isnull=True  # Not already paired
        ).exclude(
            id=transaction.id  # Exclude self
        )

        for candidate in candidates:
            # Check amount match (absolute values)
            if abs(candidate.amount) != amount:
                continue

            # Check opposite signs
            if (transaction.amount > 0 and candidate.amount > 0) or \
               (transaction.amount < 0 and candidate.amount < 0):
                continue

            # Found offsetting pair
            logger.debug(
                f"Reimbursement match: transaction {transaction.id} ({transaction.amount} HUF) ↔ "
                f"transaction {candidate.id} ({candidate.amount} HUF) - MANUAL REVIEW RECOMMENDED"
            )
            return candidate, Decimal('0.70')

        return None, Decimal('0.00')

    def _match_by_reference(
        self,
        transaction: BankTransaction,
        invoices: QuerySet
    ) -> Tuple[Optional[Invoice], Decimal]:
        """
        Match by exact invoice number or tax number in reference field.

        Examples:
        - Reference: "2025-000052" → Match invoice.nav_invoice_number
        - Reference: "28778367-2-16" → Match invoice.supplier_tax_number

        Args:
            transaction: BankTransaction instance
            invoices: QuerySet of candidate Invoice objects

        Returns:
            Tuple of (matched_invoice, confidence) or (None, 0.00)
        """
        if not transaction.reference:
            return None, Decimal('0.00')

        ref = transaction.reference.strip().upper()

        # Try exact invoice number match
        for invoice in invoices:
            if invoice.nav_invoice_number and invoice.nav_invoice_number.upper() in ref:
                # Check direction compatibility
                if not self._is_direction_compatible(transaction, invoice):
                    logger.debug(
                        f"Reference match REJECTED: transaction {transaction.id} → "
                        f"invoice {invoice.id} (direction mismatch: "
                        f"invoice={invoice.invoice_direction}, trans_amount={transaction.amount})"
                    )
                    continue

                logger.debug(
                    f"Reference match: transaction {transaction.id} → "
                    f"invoice {invoice.id} (invoice number in reference)"
                )
                return invoice, Decimal('1.00')

        # Try tax number match (normalized)
        ref_normalized = self._normalize_tax_number(ref)
        for invoice in invoices:
            if invoice.supplier_tax_number:
                supplier_tax_normalized = self._normalize_tax_number(invoice.supplier_tax_number)
                if supplier_tax_normalized and supplier_tax_normalized in ref_normalized:
                    # Check direction compatibility
                    if not self._is_direction_compatible(transaction, invoice):
                        logger.debug(
                            f"Reference match REJECTED: transaction {transaction.id} → "
                            f"invoice {invoice.id} (direction mismatch: "
                            f"invoice={invoice.invoice_direction}, trans_amount={transaction.amount})"
                        )
                        continue

                    logger.debug(
                        f"Reference match: transaction {transaction.id} → "
                        f"invoice {invoice.id} (tax number in reference)"
                    )
                    return invoice, Decimal('1.00')

        return None, Decimal('0.00')

    def _match_by_amount_iban(
        self,
        transaction: BankTransaction,
        invoices: QuerySet
    ) -> Tuple[Optional[Invoice], Decimal]:
        """
        Match by exact amount + supplier IBAN match.

        Logic:
        1. Transaction amount (absolute) must equal invoice gross_amount_huf
        2. Transaction beneficiary_iban must match invoice supplier_bank_account_number

        Args:
            transaction: BankTransaction instance
            invoices: QuerySet of candidate Invoice objects

        Returns:
            Tuple of (matched_invoice, confidence) or (None, 0.00)
        """
        if not transaction.beneficiary_iban:
            return None, Decimal('0.00')

        amount = abs(transaction.amount)
        iban_normalized = self._normalize_iban(transaction.beneficiary_iban)

        for invoice in invoices:
            # Skip invoices with no amount
            if not invoice.invoice_gross_amount:
                continue

            # Check amount match
            if invoice.invoice_gross_amount != amount:
                continue

            # Check IBAN match
            if invoice.supplier_bank_account_number:
                supplier_iban = self._normalize_iban(invoice.supplier_bank_account_number)
                if iban_normalized == supplier_iban:
                    # Check direction compatibility
                    if not self._is_direction_compatible(transaction, invoice):
                        logger.debug(
                            f"Amount+IBAN match REJECTED: transaction {transaction.id} → "
                            f"invoice {invoice.id} (direction mismatch: "
                            f"invoice={invoice.invoice_direction}, trans_amount={transaction.amount})"
                        )
                        continue

                    logger.debug(
                        f"Amount+IBAN match: transaction {transaction.id} → "
                        f"invoice {invoice.id} (amount={amount}, IBAN match)"
                    )
                    return invoice, Decimal('0.95')

        return None, Decimal('0.00')

    def _match_by_fuzzy_name(
        self,
        transaction: BankTransaction,
        invoices: QuerySet
    ) -> Tuple[Optional[Invoice], Decimal]:
        """
        Match by amount + fuzzy name similarity.

        Logic:
        1. Transaction amount (absolute) must equal invoice gross_amount_huf (±1% tolerance)
        2. Calculate name similarity between transaction counterparty name and invoice.supplier_name
           - Uses beneficiary_name for regular transactions
           - Falls back to merchant_name for POS transactions
        3. Confidence = 0.70 + (similarity_ratio * 0.20)
           - 70% similarity → 0.70 confidence
           - 80% similarity → 0.78 confidence
           - 90% similarity → 0.86 confidence
           - 100% similarity → 0.90 confidence

        Args:
            transaction: BankTransaction instance
            invoices: QuerySet of candidate Invoice objects

        Returns:
            Tuple of (matched_invoice, confidence) or (None, 0.00)
        """
        # Use beneficiary_name for regular transactions, merchant_name for POS transactions
        counterparty_name = transaction.beneficiary_name or transaction.merchant_name

        if not counterparty_name:
            return None, Decimal('0.00')

        amount = abs(transaction.amount)
        best_match = None
        best_confidence = Decimal('0.00')

        for invoice in invoices:
            # Skip invoices with no amount
            if not invoice.invoice_gross_amount:
                continue

            # Amount match with ±1% tolerance
            invoice_amount = invoice.invoice_gross_amount
            tolerance = invoice_amount * self.AMOUNT_TOLERANCE_PERCENT

            if abs(amount - invoice_amount) > tolerance:
                continue

            # Calculate name similarity
            similarity = self._calculate_name_similarity(
                counterparty_name,
                invoice.supplier_name
            )

            # Only consider if similarity ≥ minimum threshold
            if similarity >= self.FUZZY_NAME_MIN_SIMILARITY:
                # Check direction compatibility
                if not self._is_direction_compatible(transaction, invoice):
                    logger.debug(
                        f"Fuzzy name match REJECTED: transaction {transaction.id} → "
                        f"invoice {invoice.id} (direction mismatch: "
                        f"invoice={invoice.invoice_direction}, trans_amount={transaction.amount})"
                    )
                    continue

                # Calculate confidence: 0.70 + (similarity/100 * 0.20)
                # This gives us 0.70 for 70% similarity up to 0.90 for 100% similarity
                confidence = Decimal('0.70') + (Decimal(str(similarity / 100)) * Decimal('0.20'))

                if confidence > best_confidence:
                    best_match = invoice
                    best_confidence = confidence

                    logger.debug(
                        f"Fuzzy name candidate: transaction {transaction.id} → "
                        f"invoice {invoice.id} (similarity={similarity:.1f}%, confidence={confidence})"
                    )

        if best_match:
            logger.debug(
                f"Fuzzy name match: transaction {transaction.id} → "
                f"invoice {best_match.id} (confidence={best_confidence})"
            )

        return best_match, best_confidence

    def _match_by_amount_date_only(
        self,
        transaction: BankTransaction,
        invoices: QuerySet
    ) -> Tuple[Optional[Invoice], Decimal]:
        """
        Match by amount + date + direction only (fallback strategy).

        This is a LOW CONFIDENCE match for transactions that have:
        - Amount match (±1% tolerance)
        - Correct date range (already filtered by _get_candidate_invoices)
        - Correct direction (already checked)
        - BUT: No reference, no IBAN, no name match

        Typical use case: POS purchases with no merchant/beneficiary name

        Logic:
        1. Transaction amount (absolute) must match invoice amount (±1% tolerance)
        2. Invoice already passed date/direction filters in _get_candidate_invoices
        3. Confidence: 0.60 (requires manual review)

        Args:
            transaction: BankTransaction instance
            invoices: QuerySet of candidate Invoice objects (already date/direction filtered)

        Returns:
            Tuple of (matched_invoice, confidence) or (None, 0.00)
        """
        amount = abs(transaction.amount)
        best_match = None

        for invoice in invoices:
            # Skip invoices with no amount
            if not invoice.invoice_gross_amount:
                continue

            # Amount match with ±1% tolerance
            invoice_amount = invoice.invoice_gross_amount
            tolerance = invoice_amount * self.AMOUNT_TOLERANCE_PERCENT

            if abs(amount - invoice_amount) <= tolerance:
                # Check direction compatibility (should already be compatible from candidate filtering)
                if not self._is_direction_compatible(transaction, invoice):
                    logger.debug(
                        f"Amount+Date match REJECTED: transaction {transaction.id} → "
                        f"invoice {invoice.id} (direction mismatch: "
                        f"invoice={invoice.invoice_direction}, trans_amount={transaction.amount})"
                    )
                    continue

                # Found a match - use first one (could have multiple invoices with same amount)
                best_match = invoice
                logger.debug(
                    f"Amount+Date only match: transaction {transaction.id} → "
                    f"invoice {invoice.id} (amount match, no other verification)"
                )
                break  # Take first match

        if best_match:
            logger.info(
                f"Amount+Date only match (LOW CONFIDENCE): transaction {transaction.id} → "
                f"invoice {best_match.id} ({best_match.nav_invoice_number}) - "
                f"MANUAL REVIEW RECOMMENDED"
            )

        return best_match, Decimal('0.60') if best_match else Decimal('0.00')

    def _match_by_batch_invoices(
        self,
        transaction: BankTransaction,
        invoices: QuerySet
    ) -> List[Tuple[Invoice, Decimal]]:
        """
        Match transaction to MULTIPLE invoices (batch payment).

        Business case: Company pays multiple invoices from same supplier in one payment.
        Example: Payment of 450 HUF covers 3 invoices: 100 HUF, 150 HUF, 200 HUF

        Algorithm:
        1. Group candidate invoices by supplier (partner_tax_number)
        2. For each supplier, try combinations of 2-5 invoices
        3. Check if sum of invoice amounts equals transaction amount (±1% tolerance)
        4. Calculate confidence: Base 0.85 + bonuses
           - IBAN match bonus: +0.10 (if ANY invoice has matching IBAN)
           - Name similarity bonus: +0.05 (if average name similarity >= 70%)

        Args:
            transaction: BankTransaction instance
            invoices: QuerySet of candidate Invoice objects

        Returns:
            List of (invoice, confidence) tuples for all matched invoices
            Empty list if no batch match found
        """
        # Only match debit transactions (we pay suppliers)
        if transaction.amount >= 0:
            return []

        amount = abs(transaction.amount)

        # Group invoices by supplier (partner_tax_number)
        supplier_invoices = {}
        for invoice in invoices:
            # Only consider INBOUND invoices (we pay suppliers)
            if invoice.invoice_direction != 'INBOUND':
                continue

            # Skip invoices with no amount
            if not invoice.invoice_gross_amount:
                continue

            # Skip if no supplier tax number (can't group)
            if not invoice.supplier_tax_number:
                continue

            tax_number = self._normalize_tax_number(invoice.supplier_tax_number)
            if tax_number not in supplier_invoices:
                supplier_invoices[tax_number] = []
            supplier_invoices[tax_number].append(invoice)

        # Try combinations for each supplier
        best_match = []
        best_confidence = Decimal('0.00')

        for tax_number, supplier_invoice_list in supplier_invoices.items():
            # Need at least 2 invoices for batch matching
            if len(supplier_invoice_list) < 2:
                continue

            # Try combinations of 2 to 5 invoices
            for combo_size in range(2, min(6, len(supplier_invoice_list) + 1)):
                for invoice_combo in combinations(supplier_invoice_list, combo_size):
                    # Calculate total amount
                    total_amount = sum(inv.invoice_gross_amount for inv in invoice_combo)

                    # Check amount match with ±1% tolerance
                    tolerance = amount * self.AMOUNT_TOLERANCE_PERCENT
                    if abs(total_amount - amount) > tolerance:
                        continue

                    # Found a matching combination!
                    # Calculate confidence: Base 0.85 + bonuses

                    # Base confidence for batch matching
                    confidence = Decimal('0.85')

                    # IBAN bonus: +0.10 if ANY invoice has matching IBAN
                    if transaction.beneficiary_iban:
                        iban_normalized = self._normalize_iban(transaction.beneficiary_iban)
                        for invoice in invoice_combo:
                            if invoice.supplier_bank_account_number:
                                supplier_iban = self._normalize_iban(invoice.supplier_bank_account_number)
                                if iban_normalized == supplier_iban:
                                    confidence += Decimal('0.10')
                                    break  # Only add bonus once

                    # Name similarity bonus: +0.05 if average similarity >= 70%
                    if transaction.beneficiary_name:
                        total_similarity = 0.0
                        count = 0
                        for invoice in invoice_combo:
                            if invoice.supplier_name:
                                similarity = self._calculate_name_similarity(
                                    transaction.beneficiary_name,
                                    invoice.supplier_name
                                )
                                total_similarity += similarity
                                count += 1

                        if count > 0:
                            avg_similarity = total_similarity / count
                            if avg_similarity >= 70:
                                confidence += Decimal('0.05')

                    # Check if this is better than previous matches
                    if confidence > best_confidence:
                        best_match = [(inv, confidence) for inv in invoice_combo]
                        best_confidence = confidence

                        logger.debug(
                            f"Batch invoice candidate: transaction {transaction.id} → "
                            f"{len(invoice_combo)} invoices from {invoice_combo[0].supplier_name} "
                            f"(total={total_amount} HUF, confidence={confidence})"
                        )

        if best_match:
            invoice_numbers = ', '.join(inv.nav_invoice_number for inv, _ in best_match)
            logger.info(
                f"Batch invoice match: transaction {transaction.id} → "
                f"{len(best_match)} invoices ({invoice_numbers}) "
                f"(confidence={best_confidence})"
            )

        return best_match

    def _get_candidate_invoices(self, transaction: BankTransaction) -> QuerySet:
        """
        Get potential invoice candidates for matching.

        Filters:
        1. Same company
        2. Direction = 'INBOUND' or 'OUTBOUND'
           - INBOUND: We pay suppliers (transaction debit)
           - OUTBOUND: Customers pay us (transaction credit)
        3. Payment status = 'UNPAID', 'PREPARED', or 'PAID'
           - UNPAID/PREPARED: Need to match and mark as paid
           - PAID: Verify payment actually happened (reconciliation/audit)
        4. Payment date based matching:
           - Uses payment_due_date (or fulfillment_date as fallback)
           - Transaction value_date - 10 days should fall within payment_due_date ± 30 days
           - This matches the business logic: we pay shortly before/after due date
        5. Not a STORNO invoice

        Args:
            transaction: BankTransaction instance

        Returns:
            QuerySet of Invoice objects
        """
        from django.db.models import Q, F
        from django.db.models.functions import Coalesce

        # Calculate adjusted transaction date (value_date - 10 days buffer)
        adjusted_trans_date = transaction.value_date - timedelta(days=10)

        # Payment due date range: ±30 days from the due date
        # This allows for early payments (30 days before) and late payments (up to due date)

        return Invoice.objects.annotate(
            # Use payment_due_date, fallback to fulfillment_date
            effective_due_date=Coalesce('payment_due_date', 'fulfillment_date')
        ).filter(
            company=self.company,
            invoice_direction__in=['INBOUND', 'OUTBOUND'],  # Both directions
            payment_status__in=['UNPAID', 'PREPARED', 'PAID'],  # Include PAID for verification
        ).exclude(
            invoice_operation='STORNO'  # Exclude STORNO invoices
        ).filter(
            # Adjusted transaction date should be between (due_date - 30 days) and (due_date)
            # This means: we look for invoices where payment is expected around the transaction date
            effective_due_date__gte=adjusted_trans_date,
            effective_due_date__lte=adjusted_trans_date + timedelta(days=30)
        ).select_related('company')

    def _update_invoice_payment_status(
        self,
        invoice: Invoice,
        transaction: BankTransaction,
        auto: bool = True
    ):
        """
        Update invoice payment status to PAID.

        Supports both single invoice matches and batch invoice matches.
        For batch matches, this method is called once per invoice in the batch.

        Args:
            invoice: Invoice instance to mark as paid
            transaction: BankTransaction instance that paid this invoice
            auto: If True, sets auto_marked_paid flag (default: True for automatic matches)
        """
        invoice.mark_as_paid(
            payment_date=transaction.booking_date,
            auto_marked=auto
        )

        logger.info(
            f"Invoice {invoice.nav_invoice_number} auto-marked as PAID "
            f"via {transaction.match_method} match (confidence: {transaction.match_confidence})"
        )

    def _is_direction_compatible(self, transaction: BankTransaction, invoice: Invoice) -> bool:
        """
        Check if transaction direction is compatible with invoice direction.

        Business Logic:
        - OUTBOUND invoice (we issued to customer) → expects INCOMING payment (CREDIT, positive amount)
        - INBOUND invoice (we received from supplier) → expects OUTGOING payment (DEBIT, negative amount)

        Args:
            transaction: BankTransaction instance
            invoice: Invoice instance

        Returns:
            True if directions are compatible, False otherwise
        """
        if invoice.invoice_direction == 'OUTBOUND':
            # We issued the invoice → expect incoming payment (positive amount)
            return transaction.amount > 0
        elif invoice.invoice_direction == 'INBOUND':
            # We received the invoice → expect outgoing payment (negative amount)
            return transaction.amount < 0
        else:
            # Unknown direction - allow match (with warning)
            logger.warning(
                f"Invoice {invoice.id} has unknown direction: {invoice.invoice_direction}"
            )
            return True

    def _normalize_tax_number(self, tax_number: str) -> str:
        """
        Normalize tax number for comparison.

        Removes dashes, spaces, and converts to uppercase.

        Args:
            tax_number: Tax number string

        Returns:
            Normalized tax number (digits only)
        """
        if not tax_number:
            return ''

        # Remove all non-digit characters
        return ''.join(filter(str.isdigit, tax_number))

    def _normalize_iban(self, iban: str) -> str:
        """
        Normalize IBAN for comparison.

        Removes spaces and converts to uppercase.

        Args:
            iban: IBAN string

        Returns:
            Normalized IBAN
        """
        if not iban:
            return ''

        return iban.replace(' ', '').replace('-', '').upper().strip()

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names using fuzzy matching.

        Uses multiple rapidfuzz algorithms and returns the maximum:
        - token_sort_ratio: Handles different word orders
        - partial_ratio: Handles partial name matches (e.g., "Bubbles02" in "Bubbles-Car Kft.")

        Args:
            name1: First name string
            name2: Second name string

        Returns:
            Similarity percentage (0.0 to 100.0)
        """
        if not name1 or not name2:
            return 0.0

        # Normalize names
        name1_norm = name1.strip().upper()
        name2_norm = name2.strip().upper()

        # Try multiple algorithms and take the best result
        token_sort_sim = fuzz.token_sort_ratio(name1_norm, name2_norm)
        partial_sim = fuzz.partial_ratio(name1_norm, name2_norm)

        # Return the maximum similarity
        # Example: "Bubbles02" vs "Bubbles-Car Kft."
        #   token_sort_ratio: 56%
        #   partial_ratio: 87.5%
        #   max: 87.5% ✓
        similarity = max(token_sort_sim, partial_sim)

        return float(similarity)
