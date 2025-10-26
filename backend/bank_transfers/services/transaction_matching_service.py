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
from typing import Dict, Any, Optional, Tuple
from django.db.models import QuerySet
from django.utils import timezone
from rapidfuzz import fuzz

from ..models import BankStatement, BankTransaction, Invoice

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

        # Get all unmatched transactions
        transactions = BankTransaction.objects.filter(
            bank_statement=statement,
            matched_invoice__isnull=True
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

        total_transactions = transactions.count()
        match_rate = (matched_count / total_transactions * 100) if total_transactions > 0 else 0

        logger.info(
            f"Matching completed for statement {statement.id}: "
            f"{matched_count}/{total_transactions} matched ({match_rate:.1f}%), "
            f"{auto_paid_count} invoices auto-marked as paid"
        )

        return {
            'statement_id': statement.id,
            'total_transactions': total_transactions,
            'matched_count': matched_count,
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
        # Priority 1: Try transfer matching (highest confidence)
        result = self._try_transfer_matching(transaction, user)
        if result['matched']:
            return result

        # Priority 2: Try invoice matching (medium confidence)
        result = self._try_invoice_matching(transaction, user)
        if result['matched']:
            return result

        # Priority 3: Try reimbursement pairing (requires manual review)
        result = self._try_reimbursement_matching(transaction, user)
        if result['matched']:
            return result

        # No match found
        logger.debug(f"No match found for transaction {transaction.id}")
        return {'matched': False}

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
        Try to match transaction to NAV invoice.

        Args:
            transaction: BankTransaction instance
            user: User instance (optional) for manual matching

        Returns:
            Match result dictionary
        """
        from django.utils import timezone

        # Get candidate invoices for matching
        candidate_invoices = self._get_candidate_invoices(transaction)

        if not candidate_invoices.exists():
            return {'matched': False}

        # Try matching strategies in order of confidence
        matched_invoice = None
        confidence = Decimal('0.00')
        method = ''

        # Strategy 1: Reference Exact Match (highest confidence)
        matched_invoice, confidence = self._match_by_reference(transaction, candidate_invoices)
        if matched_invoice:
            method = 'REFERENCE_EXACT'

        # Strategy 2: Amount + IBAN Match
        if not matched_invoice:
            matched_invoice, confidence = self._match_by_amount_iban(transaction, candidate_invoices)
            if matched_invoice:
                method = 'AMOUNT_IBAN'

        # Strategy 3: Fuzzy Name Match
        if not matched_invoice:
            matched_invoice, confidence = self._match_by_fuzzy_name(transaction, candidate_invoices)
            if matched_invoice:
                method = 'FUZZY_NAME'

        # Strategy 4: Amount + Date Only (lowest confidence - fallback for transactions with no identifying info)
        if not matched_invoice:
            matched_invoice, confidence = self._match_by_amount_date_only(transaction, candidate_invoices)
            if matched_invoice:
                method = 'AMOUNT_DATE_ONLY'

        # If no match found
        if not matched_invoice:
            return {'matched': False}

        # Build match notes with details
        match_notes = (
            f"Matched to Invoice #{matched_invoice.id} "
            f"({matched_invoice.nav_invoice_number}) - "
            f"{matched_invoice.supplier_name} - "
            f"Amount: {matched_invoice.invoice_gross_amount} HUF - "
            f"Method: {method} (confidence: {confidence}) - "
            f"{'Manual match' if user else 'Automatic match'}"
        )

        # Save match to transaction with metadata
        transaction.matched_invoice = matched_invoice
        transaction.match_confidence = confidence
        transaction.match_method = method
        transaction.matched_at = timezone.now()
        transaction.matched_by = user
        transaction.match_notes = match_notes
        transaction.save()

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
        2. Calculate name similarity between transaction.beneficiary_name and invoice.supplier_name
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
        if not transaction.beneficiary_name:
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
                transaction.beneficiary_name,
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

        Args:
            invoice: Invoice instance
            transaction: BankTransaction instance
            auto: If True, sets auto_marked_paid flag
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

        Uses rapidfuzz token_sort_ratio for best results with different word orders.

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

        # Use token_sort_ratio to handle different word orders
        # Example: "IT Cardigan Kft." vs "Kft. IT Cardigan" → high similarity
        similarity = fuzz.token_sort_ratio(name1_norm, name2_norm)

        return float(similarity)
