"""
Invoice Pydantic Schemas

Type-safe DTOs for NAV invoice operations including:
- Invoice synchronization from NAV API
- Invoice queries and filtering
- Trusted partner management
- Payment status updates
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Literal
from enum import Enum


class InvoiceDirection(str, Enum):
    """Invoice direction choices"""
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class InvoiceOperation(str, Enum):
    """Invoice operation types"""
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    STORNO = "STORNO"


class PaymentStatus(str, Enum):
    """Payment status choices"""
    PAID = "PAID"
    UNPAID = "UNPAID"
    PREPARED = "PREPARED"


class InvoiceSyncInput(BaseModel):
    """
    Input parameters for NAV invoice synchronization.

    Validates sync parameters including date ranges, direction, and environment.
    """
    company_id: int = Field(gt=0, description="Company ID to sync invoices for")
    date_from: Optional[datetime] = Field(
        default=None,
        description="Start date for invoice sync (invoice issue date)"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="End date for invoice sync (invoice issue date)"
    )
    direction: InvoiceDirection = Field(
        default=InvoiceDirection.OUTBOUND,
        description="Invoice direction (INBOUND or OUTBOUND)"
    )
    environment: Optional[Literal["production", "test"]] = Field(
        default=None,
        description="NAV API environment to use (defaults to auto-detect)"
    )
    prefer_production: bool = Field(
        default=True,
        description="Prefer production environment if available"
    )
    page_size: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Number of invoices per API request"
    )

    @field_validator('date_to')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure date_to is not before date_from"""
        if v is not None and 'date_from' in info.data:
            date_from = info.data['date_from']
            if date_from is not None and v < date_from:
                raise ValueError("date_to cannot be before date_from")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "company_id": 1,
                "date_from": "2025-12-01T00:00:00",
                "date_to": "2025-12-30T23:59:59",
                "direction": "OUTBOUND",
                "environment": "production",
                "prefer_production": True,
                "page_size": 100
            }
        }
    )


class InvoiceSyncOutput(BaseModel):
    """
    Result of invoice synchronization operation.

    Contains sync statistics, error information, and sync log ID.
    """
    success: bool = Field(description="Whether sync completed successfully")
    invoices_processed: int = Field(default=0, description="Total invoices processed from NAV")
    invoices_created: int = Field(default=0, description="Number of new invoices created")
    invoices_updated: int = Field(default=0, description="Number of existing invoices updated")
    invoices_skipped: int = Field(default=0, description="Number of invoices skipped (no changes)")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    sync_log_id: Optional[int] = Field(default=None, description="ID of sync log record")
    synced_at: datetime = Field(default_factory=datetime.now, description="Timestamp of sync")
    environment_used: Optional[str] = Field(default=None, description="NAV environment used")
    date_range: Optional[str] = Field(default=None, description="Date range synced")
    direction: Optional[str] = Field(default=None, description="Invoice direction synced")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "invoices_processed": 150,
                "invoices_created": 120,
                "invoices_updated": 25,
                "invoices_skipped": 5,
                "errors": [],
                "warnings": ["Invoice ABC123 has no payment due date"],
                "sync_log_id": 456,
                "synced_at": "2025-12-30T10:30:00",
                "environment_used": "production",
                "date_range": "2025-12-01 to 2025-12-30",
                "direction": "OUTBOUND"
            }
        }
    )


class InvoiceQueryInput(BaseModel):
    """
    Input for querying/filtering invoices.

    Supports comprehensive filtering by dates, status, amounts, partners.
    """
    direction: Optional[InvoiceDirection] = Field(
        default=None,
        description="Filter by invoice direction"
    )
    issue_date_from: Optional[date] = Field(
        default=None,
        description="Filter by issue date from"
    )
    issue_date_to: Optional[date] = Field(
        default=None,
        description="Filter by issue date to"
    )
    payment_status: Optional[PaymentStatus] = Field(
        default=None,
        description="Filter by payment status"
    )
    supplier_tax_number: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Filter by supplier tax number"
    )
    customer_tax_number: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Filter by customer tax number"
    )
    amount_from: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Filter by minimum gross amount"
    )
    amount_to: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Filter by maximum gross amount"
    )
    currency_code: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Filter by currency code"
    )
    search: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Search across invoice numbers, names, tax numbers"
    )

    @field_validator('currency_code')
    @classmethod
    def uppercase_currency(cls, v: Optional[str]) -> Optional[str]:
        """Ensure currency code is uppercase"""
        if v is None:
            return None
        return v.upper().strip()

    model_config = ConfigDict(str_strip_whitespace=True)


class TrustedPartnerInput(BaseModel):
    """
    Input for creating/updating trusted partner.

    Trusted partners have their invoices automatically marked as PREPARED.
    """
    supplier_name: str = Field(
        min_length=1,
        max_length=255,
        description="Supplier/partner name"
    )
    tax_numbers: List[str] = Field(
        min_items=1,
        description="List of tax numbers (supports multiple tax IDs)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether this trusted partner is active"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional notes about the partner"
    )

    @field_validator('tax_numbers')
    @classmethod
    def clean_tax_numbers(cls, v: List[str]) -> List[str]:
        """Remove duplicates and strip whitespace from tax numbers"""
        cleaned = [tax_num.strip() for tax_num in v if tax_num.strip()]
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for tax_num in cleaned:
            if tax_num not in seen:
                seen.add(tax_num)
                result.append(tax_num)
        if not result:
            raise ValueError("At least one valid tax number is required")
        return result

    @field_validator('supplier_name')
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip whitespace from supplier name"""
        v = v.strip()
        if not v:
            raise ValueError("Supplier name cannot be empty")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "supplier_name": "Trusted Vendor Ltd.",
                "tax_numbers": ["12345678-2-42", "12345678-2-43"],
                "is_active": True,
                "notes": "Monthly recurring supplier"
            }
        }
    )


class PaymentStatusUpdateInput(BaseModel):
    """
    Input for bulk payment status update.

    Allows updating multiple invoices to PREPARED or PAID status.
    """
    invoice_ids: List[int] = Field(
        min_items=1,
        description="List of invoice IDs to update"
    )
    new_status: PaymentStatus = Field(
        description="New payment status to set"
    )
    payment_date: Optional[date] = Field(
        default=None,
        description="Payment date (required if status is PAID)"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional notes about the payment status change"
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

    @field_validator('payment_date')
    @classmethod
    def validate_payment_date(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure payment_date is provided when status is PAID"""
        if 'new_status' in info.data:
            new_status = info.data['new_status']
            if new_status == PaymentStatus.PAID and v is None:
                raise ValueError("payment_date is required when new_status is PAID")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invoice_ids": [123, 456, 789],
                "new_status": "PREPARED",
                "payment_date": None,
                "notes": "Prepared for payment batch #45"
            }
        }
    )


class PaymentStatusUpdateOutput(BaseModel):
    """Result of payment status update operation"""
    success: bool = Field(description="Whether update completed successfully")
    updated_count: int = Field(default=0, description="Number of invoices updated")
    failed_count: int = Field(default=0, description="Number of invoices that failed to update")
    errors: List[str] = Field(default_factory=list, description="List of errors if any")
    updated_invoice_ids: List[int] = Field(default_factory=list, description="IDs of successfully updated invoices")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "updated_count": 3,
                "failed_count": 0,
                "errors": [],
                "updated_invoice_ids": [123, 456, 789]
            }
        }
    )
