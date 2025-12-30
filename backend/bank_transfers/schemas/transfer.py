"""
Transfer Pydantic Schemas

Type-safe DTOs for bank transfer operations including:
- Transfer creation (single and bulk)
- Template loading
- XML generation (SEPA and HUF formats)
- CSV export (KH Bank format)
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date
from typing import Optional, List, Literal
from enum import Enum


class Currency(str, Enum):
    """Supported currencies"""
    HUF = "HUF"
    EUR = "EUR"
    USD = "USD"


class ExportFormat(str, Enum):
    """Export file formats"""
    XML = "XML"
    CSV = "CSV"


class TransferStatus(str, Enum):
    """Transfer processing status"""
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class TransferCreateInput(BaseModel):
    """
    Input for creating a single bank transfer.

    Validates all required fields for a transfer including account numbers,
    amounts, dates, and remittance information.
    """
    company_id: int = Field(gt=0, description="Company ID for this transfer")
    beneficiary_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Beneficiary ID (optional if providing manual beneficiary details)"
    )
    beneficiary_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Beneficiary name (required if beneficiary_id not provided)"
    )
    beneficiary_account: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=50,
        description="Beneficiary account number (required if beneficiary_id not provided)"
    )
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
        max_digits=15,
        description="Transfer amount (must be positive)"
    )
    currency: Currency = Field(
        default=Currency.HUF,
        description="Transfer currency (HUF, EUR, or USD)"
    )
    execution_date: date = Field(
        description="Requested execution date for the transfer"
    )
    remittance_information: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Remittance information / payment reference"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Internal description/notes about this transfer"
    )

    @field_validator('execution_date')
    @classmethod
    def validate_future_date(cls, v: date) -> date:
        """Ensure execution date is not in the past"""
        from datetime import date as date_class
        if v < date_class.today():
            raise ValueError("execution_date cannot be in the past")
        return v

    @field_validator('beneficiary_account')
    @classmethod
    def clean_account_number(cls, v: Optional[str]) -> Optional[str]:
        """Remove spaces and dashes from account number"""
        if v is None:
            return None
        # Remove spaces, dashes, and other common separators
        cleaned = v.replace(' ', '').replace('-', '').replace('_', '')
        if not cleaned:
            raise ValueError("Account number cannot be empty after cleaning")
        return cleaned

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "company_id": 1,
                "beneficiary_id": 123,
                "beneficiary_name": None,
                "beneficiary_account": None,
                "amount": "250000.00",
                "currency": "HUF",
                "execution_date": "2025-12-31",
                "remittance_information": "Invoice payment #INV-12345",
                "description": "Monthly payment to supplier"
            }
        }
    )


class TransferBulkCreateInput(BaseModel):
    """
    Input for bulk transfer creation.

    Allows creating multiple transfers in one operation with validation.
    """
    company_id: int = Field(gt=0, description="Company ID for all transfers")
    transfers: List[TransferCreateInput] = Field(
        min_items=1,
        max_items=1000,
        description="List of transfers to create (max 1000)"
    )
    batch_description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Description for this batch of transfers"
    )
    auto_create_batch: bool = Field(
        default=True,
        description="Automatically create a TransferBatch for these transfers"
    )

    @field_validator('transfers')
    @classmethod
    def validate_company_consistency(cls, v: List[TransferCreateInput], info) -> List[TransferCreateInput]:
        """Ensure all transfers have the same company_id"""
        if 'company_id' in info.data:
            expected_company_id = info.data['company_id']
            for idx, transfer in enumerate(v):
                if transfer.company_id != expected_company_id:
                    raise ValueError(
                        f"Transfer {idx} has company_id {transfer.company_id}, "
                        f"expected {expected_company_id}"
                    )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_id": 1,
                "transfers": [
                    {
                        "company_id": 1,
                        "beneficiary_id": 123,
                        "amount": "100000.00",
                        "currency": "HUF",
                        "execution_date": "2025-12-31",
                        "remittance_information": "Payment 1"
                    },
                    {
                        "company_id": 1,
                        "beneficiary_id": 456,
                        "amount": "200000.00",
                        "currency": "HUF",
                        "execution_date": "2025-12-31",
                        "remittance_information": "Payment 2"
                    }
                ],
                "batch_description": "December end-of-month payments",
                "auto_create_batch": True
            }
        }
    )


class TemplateLoadInput(BaseModel):
    """
    Input for loading a transfer template.

    Generates transfer instances from template beneficiaries.
    """
    template_id: int = Field(gt=0, description="Transfer template ID to load")
    execution_date: date = Field(
        description="Execution date for all generated transfers"
    )
    override_amounts: Optional[dict[int, Decimal]] = Field(
        default=None,
        description="Optional dict of {beneficiary_id: new_amount} to override template amounts"
    )
    exclude_beneficiaries: List[int] = Field(
        default_factory=list,
        description="List of beneficiary IDs to exclude from template loading"
    )

    @field_validator('execution_date')
    @classmethod
    def validate_future_date(cls, v: date) -> date:
        """Ensure execution date is not in the past"""
        from datetime import date as date_class
        if v < date_class.today():
            raise ValueError("execution_date cannot be in the past")
        return v

    @field_validator('override_amounts')
    @classmethod
    def validate_override_amounts(cls, v: Optional[dict[int, Decimal]]) -> Optional[dict[int, Decimal]]:
        """Ensure override amounts are positive"""
        if v is None:
            return None
        for beneficiary_id, amount in v.items():
            if amount <= 0:
                raise ValueError(f"Override amount for beneficiary {beneficiary_id} must be positive")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "template_id": 5,
                "execution_date": "2025-12-31",
                "override_amounts": {123: "150000.00"},
                "exclude_beneficiaries": [456]
            }
        }
    )


class XmlGenerationInput(BaseModel):
    """
    Input for XML export generation.

    Validates transfer batch and export parameters.
    """
    batch_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Transfer batch ID (optional - can provide transfer_ids instead)"
    )
    transfer_ids: Optional[List[int]] = Field(
        default=None,
        min_items=1,
        description="List of transfer IDs to include (optional if batch_id provided)"
    )
    originator_account: str = Field(
        min_length=10,
        max_length=50,
        description="Originator bank account number"
    )
    format_type: Literal["HUF", "SEPA"] = Field(
        default="HUF",
        description="XML format type (HUF for domestic, SEPA for EUR)"
    )
    mark_as_processed: bool = Field(
        default=True,
        description="Mark transfers as processed after XML generation"
    )

    @field_validator('transfer_ids', 'batch_id')
    @classmethod
    def validate_either_batch_or_transfers(cls, v, info):
        """Ensure either batch_id or transfer_ids is provided, not both"""
        field_name = info.field_name
        if field_name == 'transfer_ids':
            batch_id = info.data.get('batch_id')
            transfer_ids = v
            if batch_id is None and transfer_ids is None:
                raise ValueError("Either batch_id or transfer_ids must be provided")
            if batch_id is not None and transfer_ids is not None:
                raise ValueError("Cannot provide both batch_id and transfer_ids")
        return v

    @field_validator('originator_account')
    @classmethod
    def clean_account_number(cls, v: str) -> str:
        """Remove spaces and dashes from account number"""
        cleaned = v.replace(' ', '').replace('-', '').replace('_', '')
        if not cleaned:
            raise ValueError("Account number cannot be empty after cleaning")
        return cleaned

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "batch_id": 789,
                "transfer_ids": None,
                "originator_account": "12345678-12345678-12345678",
                "format_type": "HUF",
                "mark_as_processed": True
            }
        }
    )


class XmlGenerationOutput(BaseModel):
    """
    Result of XML generation operation.

    Contains file content and metadata.
    """
    success: bool = Field(description="Whether XML generation completed successfully")
    file_name: str = Field(description="Generated XML filename")
    file_content: str = Field(description="XML file content as string")
    file_size: int = Field(description="File size in bytes")
    transfer_count: int = Field(description="Number of transfers in the XML")
    total_amount: Decimal = Field(description="Total amount of all transfers")
    currency: str = Field(description="Currency of transfers")
    execution_date: Optional[date] = Field(default=None, description="Execution date")
    transfers_marked_processed: int = Field(
        default=0,
        description="Number of transfers marked as processed"
    )
    errors: List[str] = Field(default_factory=list, description="List of errors if any")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "file_name": "transfers_20251230_123456.xml",
                "file_content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>...",
                "file_size": 4096,
                "transfer_count": 15,
                "total_amount": "2500000.00",
                "currency": "HUF",
                "execution_date": "2025-12-31",
                "transfers_marked_processed": 15,
                "errors": []
            }
        }
    )


class CsvGenerationInput(BaseModel):
    """
    Input for CSV export generation (KH Bank format).

    Note: KH Bank has a limit of 40 transfers per CSV file.
    """
    batch_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Transfer batch ID"
    )
    transfer_ids: Optional[List[int]] = Field(
        default=None,
        min_items=1,
        max_items=40,
        description="List of transfer IDs (max 40 for KH Bank)"
    )
    mark_as_processed: bool = Field(
        default=True,
        description="Mark transfers as processed after CSV generation"
    )

    @field_validator('transfer_ids')
    @classmethod
    def validate_kh_limit(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Enforce KH Bank 40 transfer limit"""
        if v is not None and len(v) > 40:
            raise ValueError("KH Bank CSV format supports maximum 40 transfers per file")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": 789,
                "transfer_ids": None,
                "mark_as_processed": True
            }
        }
    )


class CsvGenerationOutput(BaseModel):
    """Result of CSV generation operation"""
    success: bool = Field(description="Whether CSV generation completed successfully")
    file_name: str = Field(description="Generated CSV filename")
    file_content: str = Field(description="CSV file content as string")
    file_size: int = Field(description="File size in bytes")
    transfer_count: int = Field(description="Number of transfers in the CSV")
    total_amount: Decimal = Field(description="Total amount of all transfers")
    transfers_marked_processed: int = Field(
        default=0,
        description="Number of transfers marked as processed"
    )
    errors: List[str] = Field(default_factory=list, description="List of errors if any")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "file_name": "transfers_kh_20251230.csv",
                "file_content": "Header1,Header2,...",
                "file_size": 2048,
                "transfer_count": 30,
                "total_amount": "1500000.00",
                "transfers_marked_processed": 30,
                "errors": []
            }
        }
    )
