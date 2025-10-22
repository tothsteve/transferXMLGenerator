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
from typing import Dict, List, Any, Optional
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

        # Get period from first and last transaction
        # Note: Revolut CSV is ordered newest-to-oldest, so first row is the latest date
        latest_date = self._parse_revolut_date(rows[0].get('Date completed (UTC)', ''))
        earliest_date = self._parse_revolut_date(rows[-1].get('Date completed (UTC)', ''))

        # Get account from first transaction
        account_name = rows[0].get('Account', 'Unknown Account')

        # Extract currency from account name (e.g., "USD Main", "HUF Main")
        currency = 'HUF'  # Default
        if account_name:
            parts = account_name.split()
            if parts:
                potential_currency = parts[0].upper()
                if len(potential_currency) == 3:  # Currency codes are 3 letters
                    currency = potential_currency

        # Get opening and closing balances
        # CSV is ordered newest-to-oldest, so:
        # - Last row balance = opening balance (earliest date)
        # - First row balance = closing balance (latest date)
        closing_balance = self._parse_amount(rows[0].get('Balance', '0'))

        last_balance = self._parse_amount(rows[-1].get('Balance', '0'))
        last_amount = self._parse_amount(rows[-1].get('Amount', '0'))
        opening_balance = last_balance - last_amount

        # Generate statement number from period (earliest to latest)
        statement_number = f"REVOLUT_{earliest_date.strftime('%Y%m%d')}_{latest_date.strftime('%Y%m%d')}"

        return StatementMetadata(
            bank_code=self.BANK_CODE,
            bank_name=self.BANK_NAME,
            bank_bic=self.BANK_BIC,
            account_number=account_name,  # Revolut doesn't provide traditional account numbers in CSV
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
        state = row.get('State', '').upper()
        if state != 'COMPLETED':
            logger.debug(f"Skipping non-completed transaction: {state}")
            return None

        # Parse dates
        booking_date = self._parse_revolut_date(row.get('Date completed (UTC)', ''))
        value_date = booking_date  # Revolut doesn't distinguish booking vs value date

        if not booking_date:
            logger.warning(f"Transaction missing date: {row}")
            return None

        # Parse amounts and currency
        # CRITICAL: Use "Total amount" which includes fees, not "Amount"
        # Amount = transaction only
        # Total amount = transaction + fee (actual account impact)
        total_amount = self._parse_amount(row.get('Total amount', '0'))
        base_amount = self._parse_amount(row.get('Amount', '0'))
        currency = row.get('Payment currency', 'HUF').upper()

        # Get transaction type
        revolut_type = row.get('Type', '').upper()
        transaction_type = self._map_transaction_type(revolut_type)

        # Extract description
        description = row.get('Description', '').strip()
        reference = row.get('Reference', '').strip()

        # Build short description
        short_description = f"{revolut_type}: {description}"

        # Initialize transaction with TOTAL AMOUNT (includes fees)
        transaction = NormalizedTransaction(
            transaction_type=transaction_type,
            booking_date=booking_date,
            value_date=value_date,
            amount=total_amount,  # Use total amount, not base amount
            currency=currency,
            description=description,
            short_description=short_description,
            transaction_id=row.get('ID', ''),
            reference=reference,  # CRITICAL for invoice matching
            transaction_type_code=revolut_type,
        )

        # Parse fee
        fee = self._parse_amount(row.get('Fee', '0'))
        if fee and fee != Decimal('0'):
            transaction.fee_amount = abs(fee)  # Fees are always positive

        # Parse original currency/amount - ALWAYS populate from CSV
        # Revolut ALWAYS provides Orig currency and Orig amount for ALL transactions
        # This is the "transaction currency" before any fees or conversions
        orig_currency = row.get('Orig currency', '').strip().upper()
        orig_amount_str = row.get('Orig amount', '').strip()

        if orig_currency and orig_amount_str:
            # Orig amount in CSV can be SIGNED (see EXCHANGE transactions) or UNSIGNED
            orig_amount = self._parse_amount(orig_amount_str)

            # ALWAYS populate both fields - Revolut provides this for ALL transactions
            transaction.original_currency = orig_currency
            transaction.original_amount = orig_amount  # Use CSV value as-is (it's already signed correctly)

        # Store exchange rate - both in field and raw_data
        exchange_rate_str = row.get('Exchange rate', '').strip()
        if exchange_rate_str:
            try:
                exchange_rate = self._parse_amount(exchange_rate_str)
                if exchange_rate and exchange_rate != Decimal('0'):
                    transaction.exchange_rate = exchange_rate
                    # Also keep in raw_data for debugging
                    transaction.raw_data['exchange_rate'] = exchange_rate_str
                    transaction.raw_data['base_amount_without_fee'] = str(base_amount)
            except Exception as e:
                logger.warning(f"Failed to parse exchange rate '{exchange_rate_str}': {e}")
                # Keep in raw_data even if parsing failed
                transaction.raw_data['exchange_rate'] = exchange_rate_str

        # Type-specific parsing
        if revolut_type == 'CARD_PAYMENT':
            self._parse_card_payment(row, transaction)
        elif revolut_type == 'TRANSFER':
            self._parse_transfer(row, transaction)
        elif revolut_type == 'TOPUP':
            self._parse_topup(row, transaction)

        # Store raw data
        transaction.raw_data = dict(row)

        return transaction

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

    def _map_transaction_type(self, revolut_type: str) -> str:
        """
        Map Revolut transaction types to our normalized types.

        Our types (from BankTransaction model):
        - TRANSFER: Bank transfers
        - POS: Card payments
        - FEE: Bank fees
        - INTEREST: Interest
        - CORRECTION: Corrections
        - OTHER: Other
        """
        mapping = {
            'TRANSFER': 'TRANSFER',
            'CARD_PAYMENT': 'POS',
            'TOPUP': 'TRANSFER',  # Top-ups are incoming transfers
            'EXCHANGE': 'OTHER',  # Currency exchanges
            'FEE': 'FEE',
            'ATM': 'POS',  # ATM withdrawals treated as POS
        }

        return mapping.get(revolut_type, 'OTHER')

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
