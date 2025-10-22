"""
Abstract base class for bank statement adapters.

All bank-specific parsers must implement this interface for multi-bank support.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
import logging

logger = logging.getLogger(__name__)


@dataclass
class NormalizedTransaction:
    """
    Normalized transaction data model.

    All bank adapters must return this standardized format regardless of
    bank-specific PDF structure or terminology.
    """
    # Required fields
    transaction_type: str  # One of BankTransaction.TRANSACTION_TYPES
    booking_date: date
    value_date: date
    amount: Decimal  # Negative for debit, positive for credit
    currency: str
    description: str

    # Optional fields (populated based on transaction type)
    short_description: str = ""

    # AFR/Transfer fields
    payment_id: Optional[str] = None
    transaction_id: Optional[str] = None

    payer_name: Optional[str] = None
    payer_iban: Optional[str] = None
    payer_account_number: Optional[str] = None
    payer_bic: Optional[str] = None

    beneficiary_name: Optional[str] = None
    beneficiary_iban: Optional[str] = None
    beneficiary_account_number: Optional[str] = None
    beneficiary_bic: Optional[str] = None

    reference: Optional[str] = None  # CRITICAL for invoice matching
    partner_id: Optional[str] = None  # End-to-end ID between partners
    transaction_type_code: Optional[str] = None  # Bank-specific transaction type code
    fee_amount: Optional[Decimal] = None  # Transaction fee

    # POS/Card fields
    card_number: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_location: Optional[str] = None
    original_amount: Optional[Decimal] = None
    original_currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None  # For currency conversions

    # Raw data storage
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate required fields"""
        if not self.transaction_type:
            raise ValueError("transaction_type is required")
        if not self.booking_date:
            raise ValueError("booking_date is required")
        if not self.value_date:
            raise ValueError("value_date is required")
        if self.amount is None:
            raise ValueError("amount is required")
        if not self.currency:
            raise ValueError("currency is required")


@dataclass
class StatementMetadata:
    """
    Statement-level metadata extracted from PDF header/footer.
    """
    # Bank identification
    bank_code: str
    bank_name: str
    bank_bic: str

    # Account details
    account_number: str
    account_iban: str

    # Statement period
    period_from: date
    period_to: date
    statement_number: str

    # Balances
    opening_balance: Decimal
    closing_balance: Optional[Decimal] = None

    # Additional metadata
    raw_metadata: Dict[str, Any] = field(default_factory=dict)


class BankStatementParseError(Exception):
    """Raised when PDF parsing fails"""
    pass


class BankStatementAdapter(ABC):
    """
    Abstract base class for bank statement parsers.

    Each bank must implement this interface to support multi-bank parsing.

    Example implementations:
    - GranitBankAdapter (GRÁNIT Bank Nyrt.)
    - OTPBankAdapter (OTP Bank Nyrt.) - future
    - KHBankAdapter (K&H Bank Zrt.) - future
    - CIBBankAdapter (CIB Bank Zrt.) - future
    - ErsteBankAdapter (Erste Bank Hungary Zrt.) - future
    """

    # Bank identification (must be set by subclasses)
    BANK_CODE: str = None  # e.g., 'GRANIT', 'OTP', 'KH'
    BANK_NAME: str = None  # e.g., 'GRÁNIT Bank Nyrt.'
    BANK_BIC: str = None   # e.g., 'GNBAHUHB'

    @classmethod
    @abstractmethod
    def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
        """
        Detect if this adapter can parse the given PDF.

        Should check for bank-specific identifiers in the PDF (e.g., bank name, BIC code, logo).

        Args:
            pdf_bytes: Raw PDF file bytes
            filename: Original filename (may contain hints)

        Returns:
            True if this adapter can handle the PDF, False otherwise

        Example:
            @classmethod
            def detect(cls, pdf_bytes: bytes, filename: str) -> bool:
                try:
                    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                        first_page_text = pdf.pages[0].extract_text()
                        return 'GRÁNIT Bank' in first_page_text and 'GNBAHUHB' in first_page_text
                except:
                    return False
        """
        pass

    @abstractmethod
    def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parse bank statement PDF and extract ALL transactions.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            Dictionary with keys:
            {
                'metadata': StatementMetadata,
                'transactions': List[NormalizedTransaction]
            }

        Raises:
            BankStatementParseError: If parsing fails (invalid PDF, unrecognized format, etc.)

        Example:
            def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
                with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                    # Extract metadata from header
                    metadata = self._parse_metadata(pdf)

                    # Extract all transactions
                    transactions = self._parse_transactions(pdf)

                    return {
                        'metadata': metadata,
                        'transactions': transactions
                    }
        """
        pass

    @classmethod
    def get_bank_code(cls) -> str:
        """Return bank identifier code"""
        if not cls.BANK_CODE:
            raise NotImplementedError(f"{cls.__name__} must define BANK_CODE")
        return cls.BANK_CODE

    @classmethod
    def get_bank_name(cls) -> str:
        """Return bank display name"""
        if not cls.BANK_NAME:
            raise NotImplementedError(f"{cls.__name__} must define BANK_NAME")
        return cls.BANK_NAME

    @classmethod
    def get_bank_bic(cls) -> str:
        """Return bank BIC code"""
        if not cls.BANK_BIC:
            raise NotImplementedError(f"{cls.__name__} must define BANK_BIC")
        return cls.BANK_BIC

    def _clean_amount(self, amount_str: str) -> Decimal:
        """
        Clean and parse amount string to Decimal.

        Handles various formats:
        - "4 675 505" → 4675505.00
        - "-229 125" → -229125.00
        - "10,260.50" → 10260.50
        - "1.234,56" → 1234.56 (European format)
        """
        if not amount_str:
            return Decimal('0.00')

        # Remove spaces
        cleaned = amount_str.strip().replace(' ', '')

        # Handle negative sign
        is_negative = cleaned.startswith('-')
        if is_negative:
            cleaned = cleaned[1:]

        # Detect decimal separator (last comma or dot)
        if ',' in cleaned and '.' in cleaned:
            # Both present - assume European format: 1.234,56
            if cleaned.rindex(',') > cleaned.rindex('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format: 1,234.56
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Only comma - assume decimal separator
            cleaned = cleaned.replace(',', '.')

        try:
            result = Decimal(cleaned)
            return -result if is_negative else result
        except Exception as e:
            logger.warning(f"Failed to parse amount '{amount_str}': {e}")
            return Decimal('0.00')

    def _clean_account_number(self, account_str: str) -> str:
        """
        Clean account number (remove spaces, keep dashes).

        "1210 0011-1901 4874" → "12100011-19014874"
        """
        if not account_str:
            return ""
        return account_str.replace(' ', '').strip()

    def _clean_iban(self, iban_str: str) -> str:
        """
        Clean IBAN (remove spaces).

        "HU62 1210 0011 1901 4874 0000 0000" → "HU62121000111901487400000000"
        """
        if not iban_str:
            return ""
        return iban_str.replace(' ', '').strip().upper()

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse date string in various formats.

        Supports:
        - "2025.01.31"
        - "2025-01-31"
        - "2025/01/31"
        """
        if not date_str:
            return None

        from datetime import datetime

        formats = [
            '%Y.%m.%d',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d.%m.%Y',
            '%d-%m-%Y',
            '%d/%m/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        logger.warning(f"Failed to parse date: {date_str}")
        return None
