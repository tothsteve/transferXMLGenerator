"""
Bank Statement Pydantic Schemas

Type-safe DTOs for bank statement operations including:
- Bank statement upload and parsing
- Transaction matching with invoices
- Match approval and confidence scoring
- Other cost categorization
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Literal
from enum import Enum


class BankCode(str, Enum):
    """Supported bank codes"""
    GRANIT = "GRANIT"
    REVOLUT = "REVOLUT"
    MAGNET = "MAGNET"
    KH = "KH"


class TransactionType(str, Enum):
    """Bank transaction types"""
    AFR_CREDIT = "AFR_CREDIT"  # Incoming transfer
    POS_PURCHASE = "POS_PURCHASE"  # Card payment
    ATM_WITHDRAWAL = "ATM_WITHDRAWAL"  # Cash withdrawal
    BANK_FEE = "BANK_FEE"  # Bank fee
    INTEREST = "INTEREST"  # Interest payment
    OTHER = "OTHER"  # Other transaction type


class MatchMethod(str, Enum):
    """Transaction matching methods"""
    EXACT_AMOUNT = "EXACT_AMOUNT"
    FUZZY_NAME = "FUZZY_NAME"
    INVOICE_NUMBER = "INVOICE_NUMBER"
    TAX_NUMBER = "TAX_NUMBER"
    DATE_AMOUNT = "DATE_AMOUNT"
    MANUAL = "MANUAL"
    MANUAL_BATCH = "MANUAL_BATCH"
    AUTO_CATEGORY = "AUTO_CATEGORY"


class MatchConfidenceLevel(str, Enum):
    """Match confidence levels"""
    VERY_HIGH = "VERY_HIGH"  # >= 0.95
    HIGH = "HIGH"  # >= 0.80
    MEDIUM = "MEDIUM"  # >= 0.60
    LOW = "LOW"  # >= 0.40
    VERY_LOW = "VERY_LOW"  # < 0.40


class BankStatementUploadInput(BaseModel):
    """
    Input for bank statement PDF upload.

    Validates file metadata before processing.
    """
    file_name: str = Field(
        min_length=1,
        max_length=255,
        description="Name of the uploaded file"
    )
    file_size: int = Field(
        gt=0,
        le=10_485_760,  # 10 MB max
        description="File size in bytes (max 10MB)"
    )
    mime_type: str = Field(
        description="MIME type of the file (should be application/pdf)"
    )
    company_id: int = Field(gt=0, description="Company ID for this statement")

    @field_validator('mime_type')
    @classmethod
    def validate_pdf_mime_type(cls, v: str) -> str:
        """Ensure file is a PDF"""
        allowed_types = ['application/pdf', 'application/x-pdf']
        if v.lower() not in allowed_types:
            raise ValueError(f"Only PDF files are supported. Got: {v}")
        return v

    @field_validator('file_name')
    @classmethod
    def validate_pdf_extension(cls, v: str) -> str:
        """Ensure filename has .pdf extension"""
        v = v.strip()
        if not v.lower().endswith('.pdf'):
            raise ValueError("File must have .pdf extension")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "file_name": "bank_statement_2025_12.pdf",
                "file_size": 524288,
                "mime_type": "application/pdf",
                "company_id": 1
            }
        }
    )


class TransactionParseResult(BaseModel):
    """Single parsed transaction from bank statement"""
    booking_date: date
    value_date: Optional[date] = None
    amount: Decimal
    description: Optional[str] = None
    payer_name: Optional[str] = None
    beneficiary_name: Optional[str] = None
    payer_account: Optional[str] = None
    beneficiary_account: Optional[str] = None
    reference: Optional[str] = None
    payment_id: Optional[str] = None
    transaction_type: Optional[str] = None


class BankStatementParseOutput(BaseModel):
    """
    Result of bank statement parsing operation.

    Contains parsed transactions and metadata.
    """
    success: bool = Field(description="Whether parsing completed successfully")
    bank_code: Optional[BankCode] = Field(default=None, description="Detected bank code")
    statement_id: Optional[int] = Field(default=None, description="Created bank statement ID")
    account_number: Optional[str] = Field(default=None, description="Account number from statement")
    statement_period_from: Optional[date] = Field(default=None, description="Statement period start")
    statement_period_to: Optional[date] = Field(default=None, description="Statement period end")
    opening_balance: Optional[Decimal] = Field(default=None, description="Opening balance")
    closing_balance: Optional[Decimal] = Field(default=None, description="Closing balance")
    total_transactions: int = Field(default=0, description="Number of transactions parsed")
    transactions_created: int = Field(default=0, description="Number of transaction records created")
    duplicates_skipped: int = Field(default=0, description="Number of duplicate transactions skipped")
    auto_matched: int = Field(default=0, description="Number of automatically matched transactions")
    errors: List[str] = Field(default_factory=list, description="List of parsing errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "bank_code": "GRANIT",
                "statement_id": 789,
                "account_number": "12345678-12345678-12345678",
                "statement_period_from": "2025-12-01",
                "statement_period_to": "2025-12-30",
                "opening_balance": "1500000.00",
                "closing_balance": "1850000.50",
                "total_transactions": 45,
                "transactions_created": 42,
                "duplicates_skipped": 3,
                "auto_matched": 25,
                "errors": [],
                "warnings": ["Transaction on line 15 has no payer name"]
            }
        }
    )


class TransactionMatchInput(BaseModel):
    """
    Input for manually matching transaction to invoice(s).

    Supports both single invoice and batch invoice matching.
    """
    transaction_id: int = Field(gt=0, description="Bank transaction ID to match")
    invoice_ids: List[int] = Field(
        min_items=1,
        description="List of invoice IDs to match (1 for single, 2+ for batch)"
    )
    match_notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional notes about this manual match"
    )

    @field_validator('invoice_ids')
    @classmethod
    def validate_unique_ids(cls, v: List[int]) -> List[int]:
        """Ensure invoice IDs are unique and positive"""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate invoice IDs are not allowed")
        for invoice_id in v:
            if invoice_id <= 0:
                raise ValueError(f"Invalid invoice ID: {invoice_id}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_id": 456,
                "invoice_ids": [123, 789],
                "match_notes": "Batch payment covering 2 invoices from same supplier"
            }
        }
    )


class MatchedInvoiceInfo(BaseModel):
    """Information about a matched invoice"""
    invoice_id: int
    invoice_number: str
    amount: Decimal
    supplier_name: Optional[str] = None


class TransactionMatchOutput(BaseModel):
    """
    Result of transaction matching operation.

    Contains match details and confidence information.
    """
    success: bool = Field(description="Whether matching completed successfully")
    transaction_id: int = Field(description="Bank transaction ID")
    is_batch_match: bool = Field(default=False, description="Whether this is a batch match (multiple invoices)")
    matched_invoices: List[MatchedInvoiceInfo] = Field(
        default_factory=list,
        description="List of matched invoices"
    )
    total_matched_amount: Decimal = Field(description="Total amount of matched invoices")
    transaction_amount: Decimal = Field(description="Amount of the bank transaction")
    match_confidence: Decimal = Field(
        ge=0,
        le=1,
        description="Match confidence score (0.0 to 1.0)"
    )
    match_method: MatchMethod = Field(description="Method used for matching")
    match_notes: Optional[str] = Field(default=None, description="Notes about the match")
    errors: List[str] = Field(default_factory=list, description="List of errors if any")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "transaction_id": 456,
                "is_batch_match": True,
                "matched_invoices": [
                    {"invoice_id": 123, "invoice_number": "INV-001", "amount": "150000.00", "supplier_name": "Supplier Ltd."},
                    {"invoice_id": 789, "invoice_number": "INV-002", "amount": "200000.00", "supplier_name": "Supplier Ltd."}
                ],
                "total_matched_amount": "350000.00",
                "transaction_amount": "350000.00",
                "match_confidence": "1.00",
                "match_method": "MANUAL_BATCH",
                "match_notes": "Batch payment covering 2 invoices",
                "errors": []
            }
        }
    )


class MatchApprovalInput(BaseModel):
    """
    Input for approving an automatic match.

    Upgrades confidence to 1.00 and marks as manually approved.
    """
    transaction_id: int = Field(gt=0, description="Bank transaction ID to approve")
    approval_notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional notes about why this match was approved"
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class OtherCostCategorizationInput(BaseModel):
    """
    Input for categorizing transaction as other cost.

    Used for expenses that don't match invoices (fees, interest, etc.).
    """
    transaction_id: int = Field(gt=0, description="Bank transaction ID")
    category: str = Field(
        min_length=1,
        max_length=100,
        description="Cost category (e.g., 'BANK_FEE', 'INTEREST', 'ATM_FEE')"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Description of the cost"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Additional notes"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Optional tags for categorization"
    )

    @field_validator('category')
    @classmethod
    def uppercase_category(cls, v: str) -> str:
        """Ensure category is uppercase"""
        return v.upper().strip()

    @field_validator('tags')
    @classmethod
    def clean_tags(cls, v: List[str]) -> List[str]:
        """Clean and deduplicate tags"""
        cleaned = [tag.strip().lower() for tag in v if tag.strip()]
        return list(set(cleaned))

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "transaction_id": 456,
                "category": "BANK_FEE",
                "description": "Monthly account maintenance fee",
                "notes": "Charged on last day of month",
                "tags": ["recurring", "monthly", "overhead"]
            }
        }
    )
