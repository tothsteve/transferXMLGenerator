"""
Revolut Bank statement parser - CSV FORMAT.

Revolut provides clean CSV exports with structured columns, making parsing much
easier than PDF-based banks.

Supported transaction types:
- TRANSFER: Outgoing/incoming transfers
- CARD_PAYMENT: Card purchases
- TOPUP: Account deposits
- EXCHANGE: Currency exchanges
- FEE: Bank fees
"""

import csv
import logging
from io import BytesIO, StringIO
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime

from .base import (
    BankStatementAdapter,
    NormalizedTransaction,
    StatementMetadata,
    BankStatementParseError,
)

logger = logging.getLogger(__name__)


class RevolutAdapter(BankStatementAdapter):
    """
    Revolut Bank CSV statement parser.

    CSV Columns:
    - Date started (UTC), Date completed (UTC), ID, Type, State, Description,
    - Reference, Payer, Card number, Card label, Card state,
    - Orig currency, Orig amount, Payment currency, Amount, Total amount,
    - Exchange rate, Fee, Fee currency, Balance, Account,
    - Beneficiary account number, Beneficiary sort code or routing number,
    - Beneficiary IBAN, Beneficiary BIC, MCC, Related transaction id, Spend program
    """

    BANK_CODE = 'REVOLUT'
    BANK_NAME = 'Revolut Bank'
    BANK_BIC = 'REVOLT21'  # Revolut's BIC code

    @classmethod
    def detect(cls, file_bytes: bytes, filename: str) -> bool:
        """
        Detect if this is a Revolut CSV statement.

        Revolut CSVs have a specific header structure with columns like:
        "Date started (UTC)", "Date completed (UTC)", "Type", "State", etc.
        """
        try:
            # Try to decode as CSV
            text = file_bytes.decode('utf-8')

            # Check first line for Revolut-specific headers
            first_line = text.split('\n')[0].lower()

            return all([
                'date started' in first_line,
                'date completed' in first_line,
                'type' in first_line,
                'state' in first_line,
                'description' in first_line,
            ])
        except Exception as e:
            logger.debug(f"Failed to detect Revolut CSV: {e}")
            return False

    def parse(self, file_bytes: bytes) -> Dict[str, Any]:
        """Parse Revolut CSV statement."""
        try:
            # Decode CSV
            text = file_bytes.decode('utf-8')
            csv_reader = csv.DictReader(StringIO(text))

            # Parse transactions
            transactions = []
            rows = list(csv_reader)

            if not rows:
                raise BankStatementParseError("CSV contains no transaction data")

            # Extract metadata from transactions
            metadata = self._parse_metadata_from_transactions(rows)

            # Parse each transaction
            for row in rows:
                try:
                    transaction = self._parse_transaction(row)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.warning(f"Failed to parse transaction row: {e}", exc_info=True)
                    continue

            logger.info(f"Successfully parsed {len(transactions)} transactions from Revolut CSV")

            return {
                'metadata': metadata,
                'transactions': transactions
            }

        except BankStatementParseError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse Revolut CSV: {e}", exc_info=True)
            raise BankStatementParseError(f"Failed to parse Revolut statement: {str(e)}")

    def _parse_metadata_from_transactions(self, rows: List[Dict]) -> StatementMetadata:
        """
        Extract statement metadata from transaction rows.

        Since Revolut CSV doesn't have a header section, we extract:
        - Period from first/last transaction dates
        - Account details from transaction data
        - Opening/closing balances from balance column
        """
        if not rows:
            raise BankStatementParseError("No transactions to extract metadata from")

        # Extract period and account
        earliest_date, latest_date = self._extract_date_range(rows)
        account_name = rows[0].get('Account', 'Unknown Account')
        currency = self._extract_currency_from_account(account_name)

        # Calculate balances
        opening_balance, closing_balance = self._calculate_balances(rows)

        # Generate statement number
        statement_number = (
            f"REVOLUT_{earliest_date.strftime('%Y%m%d')}_{latest_date.strftime('%Y%m%d')}"
        )

        return StatementMetadata(
            bank_code=self.BANK_CODE,
            bank_name=self.BANK_NAME,
            bank_bic=self.BANK_BIC,
            account_number=account_name,
            account_iban='',  # Will be filled from account settings if needed
            period_from=earliest_date,
            period_to=latest_date,
            statement_number=statement_number,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            raw_metadata={
                'account_name': account_name,
                'currency': currency,
                'total_transactions': len(rows),
            }
        )

    def _extract_date_range(self, rows: List[Dict]) -> Tuple[date, date]:
        """Extract earliest and latest transaction dates from rows."""
        # Note: Revolut CSV is ordered newest-to-oldest
        latest_date = self._parse_revolut_date(rows[0].get('Date completed (UTC)', ''))
        earliest_date = self._parse_revolut_date(rows[-1].get('Date completed (UTC)', ''))
        return earliest_date, latest_date

    def _extract_currency_from_account(self, account_name: str) -> str:
        """Extract currency code from account name (e.g., 'USD Main' -> 'USD')."""
        currency = 'HUF'  # Default
        if account_name:
            parts = account_name.split()
            if parts:
                potential_currency = parts[0].upper()
                if len(potential_currency) == 3:  # Currency codes are 3 letters
                    currency = potential_currency
        return currency

    def _calculate_balances(self, rows: List[Dict]) -> Tuple[Decimal, Decimal]:
        """Calculate opening and closing balances from transaction rows."""
        # CSV is ordered newest-to-oldest:
        # - First row balance = closing balance (latest date)
        # - Last row balance = opening balance (earliest date)
        closing_balance = self._parse_amount(rows[0].get('Balance', '0'))

        last_balance = self._parse_amount(rows[-1].get('Balance', '0'))
        last_amount = self._parse_amount(rows[-1].get('Amount', '0'))
        opening_balance = last_balance - last_amount

        return opening_balance, closing_balance

    def _parse_transaction(self, row: Dict[str, str]) -> Optional[NormalizedTransaction]:
        """
        Parse a single CSV row into a NormalizedTransaction.

        Row columns:
        - Date started (UTC), Date completed (UTC), ID, Type, State, Description,
        - Reference, Payer, Card number, Card label, Card state,
        - Orig currency, Orig amount, Payment currency, Amount, Total amount,
        - Exchange rate, Fee, Fee currency, Balance, Account,
        - Beneficiary account number, Beneficiary sort code or routing number,
        - Beneficiary IBAN, Beneficiary BIC, MCC, Related transaction id, Spend program
        """
        # Only process completed transactions
        if not self._is_completed_transaction(row):
            return None

        # Parse dates
        booking_date = self._extract_transaction_date(row)
        if not booking_date:
            return None

        # Parse amounts and build base transaction
        transaction = self._build_base_transaction(row, booking_date)

        # Add optional fields
        self._add_fee_if_present(row, transaction)
        self._add_original_currency(row, transaction)
        self._add_exchange_rate(row, transaction)

        # Type-specific parsing
        self._parse_type_specific_fields(row, transaction)

        # Store raw data
        transaction.raw_data = dict(row)

        return transaction

    def _is_completed_transaction(self, row: Dict[str, str]) -> bool:
        """Check if transaction is in COMPLETED state."""
        state = row.get('State', '').upper()
        if state != 'COMPLETED':
            logger.debug(f"Skipping non-completed transaction: {state}")
            return False
        return True

    def _extract_transaction_date(self, row: Dict[str, str]) -> Optional[date]:
        """Extract and validate transaction date."""
        booking_date = self._parse_revolut_date(row.get('Date completed (UTC)', ''))
        if not booking_date:
            logger.warning(f"Transaction missing date: {row}")
        return booking_date

    def _build_base_transaction(
        self,
        row: Dict[str, str],
        booking_date: date
    ) -> NormalizedTransaction:
        """Build base transaction object with core fields."""
        # Parse amounts and currency
        # CRITICAL: Use "Total amount" which includes fees, not "Amount"
        total_amount = self._parse_amount(row.get('Total amount', '0'))
        currency = row.get('Payment currency', 'HUF').upper()

        # Get transaction type (with direction based on amount)
        revolut_type = row.get('Type', '').upper()
        transaction_type = self._map_transaction_type(revolut_type, total_amount)

        # Extract description
        description = row.get('Description', '').strip()
        reference = row.get('Reference', '').strip()
        short_description = f"{revolut_type}: {description}"

        return NormalizedTransaction(
            transaction_type=transaction_type,
            booking_date=booking_date,
            value_date=booking_date,  # Revolut doesn't distinguish booking vs value
            amount=total_amount,  # Use total amount (includes fees)
            currency=currency,
            description=description,
            short_description=short_description,
            transaction_id=row.get('ID', ''),
            reference=reference,  # CRITICAL for invoice matching
            transaction_type_code=revolut_type,
        )

    def _add_fee_if_present(
        self,
        row: Dict[str, str],
        transaction: NormalizedTransaction
    ) -> None:
        """Add fee amount if present in row."""
        fee = self._parse_amount(row.get('Fee', '0'))
        if fee and fee != Decimal('0'):
            transaction.fee_amount = abs(fee)  # Fees are always positive

    def _add_original_currency(
        self,
        row: Dict[str, str],
        transaction: NormalizedTransaction
    ) -> None:
        """Add original currency and amount (always present in Revolut CSV)."""
        orig_currency = row.get('Orig currency', '').strip().upper()
        orig_amount_str = row.get('Orig amount', '').strip()

        if orig_currency and orig_amount_str:
            orig_amount = self._parse_amount(orig_amount_str)
            # ALWAYS populate - Revolut provides this for ALL transactions
            transaction.original_currency = orig_currency
            transaction.original_amount = orig_amount

    def _add_exchange_rate(
        self,
        row: Dict[str, str],
        transaction: NormalizedTransaction
    ) -> None:
        """Add exchange rate to transaction and raw_data."""
        exchange_rate_str = row.get('Exchange rate', '').strip()
        if not exchange_rate_str:
            return

        try:
            exchange_rate = self._parse_amount(exchange_rate_str)
            if exchange_rate and exchange_rate != Decimal('0'):
                transaction.exchange_rate = exchange_rate
                # Keep in raw_data for debugging
                base_amount = self._parse_amount(row.get('Amount', '0'))
                transaction.raw_data['exchange_rate'] = exchange_rate_str
                transaction.raw_data['base_amount_without_fee'] = str(base_amount)
        except Exception as e:
            logger.warning(f"Failed to parse exchange rate '{exchange_rate_str}': {e}")
            transaction.raw_data['exchange_rate'] = exchange_rate_str

    def _parse_type_specific_fields(
        self,
        row: Dict[str, str],
        transaction: NormalizedTransaction
    ) -> None:
        """Parse type-specific fields based on transaction type."""
        revolut_type = row.get('Type', '').upper()

        if revolut_type == 'CARD_PAYMENT':
            self._parse_card_payment(row, transaction)
        elif revolut_type == 'TRANSFER':
            self._parse_transfer(row, transaction)
        elif revolut_type == 'TOPUP':
            self._parse_topup(row, transaction)

    def _parse_card_payment(self, row: Dict[str, str], transaction: NormalizedTransaction):
        """Parse card payment specific fields."""
        transaction.card_number = row.get('Card number', '').strip()
        transaction.merchant_name = row.get('Description', '').strip()

        # MCC code is in separate column
        mcc = row.get('MCC', '').strip()
        if mcc:
            transaction.raw_data['mcc'] = mcc

        # Payer is card holder
        payer = row.get('Payer', '').strip()
        if payer:
            transaction.payer_name = payer

    def _parse_transfer(self, row: Dict[str, str], transaction: NormalizedTransaction):
        """Parse transfer specific fields."""
        payer = row.get('Payer', '').strip()

        # Determine if incoming or outgoing
        if transaction.amount < 0:
            # Outgoing transfer - we are payer, extract beneficiary
            transaction.payer_name = payer
            transaction.beneficiary_name = transaction.description.replace('To ', '').strip()
            transaction.beneficiary_account_number = row.get('Beneficiary account number', '').strip()
            transaction.beneficiary_iban = row.get('Beneficiary IBAN', '').strip()
            transaction.beneficiary_bic = row.get('Beneficiary BIC', '').strip()
        else:
            # Incoming transfer - extract payer
            transaction.payer_name = payer or transaction.description.replace('From ', '').strip()

    def _parse_topup(self, row: Dict[str, str], transaction: NormalizedTransaction):
        """Parse top-up specific fields."""
        # Top-ups usually have payer in description
        description = row.get('Description', '')
        if 'from' in description.lower():
            payer = description.split('from')[-1].strip()
            transaction.payer_name = payer

    def _map_transaction_type(self, revolut_type: str, amount: Decimal) -> str:
        """
        Map Revolut transaction types to detailed types with direction.

        Uses amount sign to determine direction:
        - Positive amount = CREDIT (incoming)
        - Negative amount = DEBIT (outgoing)

        Returns detailed types matching GRANIT format:
        - TRANSFER_CREDIT / TRANSFER_DEBIT
        - POS_PURCHASE
        - BANK_FEE
        - INTEREST_CREDIT / INTEREST_DEBIT
        - OTHER
        """
        is_credit = amount > 0

        # Transfers
        if revolut_type in ('TRANSFER', 'TOPUP'):
            return 'TRANSFER_CREDIT' if is_credit else 'TRANSFER_DEBIT'

        # Card payments (always debit for Revolut)
        if revolut_type in ('CARD_PAYMENT', 'ATM'):
            return 'POS_PURCHASE'

        # Fees (always debit)
        if revolut_type == 'FEE':
            return 'BANK_FEE'

        # Interest (rare but possible)
        if revolut_type == 'INTEREST':
            return 'INTEREST_CREDIT' if is_credit else 'INTEREST_DEBIT'

        # Currency exchanges and other
        return 'OTHER'

    def _parse_revolut_date(self, date_str: str) -> Optional[date]:
        """
        Parse Revolut date format: "2025-09-20"

        Revolut uses ISO 8601 format.
        """
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        except ValueError as e:
            logger.warning(f"Failed to parse Revolut date '{date_str}': {e}")
            return None

    def _parse_amount(self, amount_str: str) -> Decimal:
        """
        Parse Revolut amount format.

        Revolut uses decimal point format: "12362.60", "-551.30"
        Negative sign indicates debit.
        """
        if not amount_str:
            return Decimal('0.00')

        try:
            return Decimal(amount_str.strip())
        except Exception as e:
            logger.warning(f"Failed to parse Revolut amount '{amount_str}': {e}")
            return Decimal('0.00')
