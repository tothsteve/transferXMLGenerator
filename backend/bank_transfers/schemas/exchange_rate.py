"""
Exchange Rate Pydantic Schemas

Type-safe DTOs for currency exchange rate operations including:
- Currency conversion
- Exchange rate synchronization with MNB API
- Rate lookups and queries
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List


class CurrencyConversionInput(BaseModel):
    """
    Input parameters for currency conversion.

    Validates currency codes, amounts, and optional rate dates.
    """
    amount: Decimal = Field(
        gt=0,
        decimal_places=2,
        max_digits=15,
        description="Amount to convert (must be positive)"
    )
    from_currency: str = Field(
        min_length=3,
        max_length=3,
        description="Source currency code (ISO 4217, e.g., 'USD')"
    )
    to_currency: str = Field(
        default='HUF',
        min_length=3,
        max_length=3,
        description="Target currency code (ISO 4217, defaults to HUF)"
    )
    rate_date: Optional[date] = Field(
        default=None,
        description="Date for exchange rate (defaults to today)"
    )

    @field_validator('from_currency', 'to_currency')
    @classmethod
    def uppercase_and_validate_currency(cls, v: str) -> str:
        """Ensure currency codes are uppercase and valid format"""
        v = v.upper().strip()
        if not v.isalpha():
            raise ValueError(f"Currency code must contain only letters: {v}")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "amount": "1000.50",
                "from_currency": "USD",
                "to_currency": "HUF",
                "rate_date": "2025-12-30"
            }
        }
    )


class CurrencyConversionOutput(BaseModel):
    """
    Result of currency conversion operation.

    Contains original and converted amounts with rate metadata.
    """
    original_amount: Decimal = Field(description="Original amount before conversion")
    original_currency: str = Field(description="Original currency code")
    converted_amount: Decimal = Field(description="Converted amount")
    converted_currency: str = Field(description="Target currency code")
    exchange_rate: Decimal = Field(description="Exchange rate used (1 from_currency = X to_currency)")
    rate_date: date = Field(description="Date of the exchange rate")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_amount": "1000.50",
                "original_currency": "USD",
                "converted_amount": "383691.75",
                "converted_currency": "HUF",
                "exchange_rate": "383.50",
                "rate_date": "2025-12-30"
            }
        }
    )


class ExchangeRateSyncInput(BaseModel):
    """
    Input parameters for MNB exchange rate synchronization.

    Specifies date range and currencies to sync from Magyar Nemzeti Bank API.
    """
    start_date: Optional[date] = Field(
        default=None,
        description="Start date for sync (defaults to today)"
    )
    end_date: Optional[date] = Field(
        default=None,
        description="End date for sync (defaults to today)"
    )
    currencies: Optional[List[str]] = Field(
        default=None,
        description="List of currency codes to sync (defaults to USD, EUR)"
    )
    force_update: bool = Field(
        default=False,
        description="Force update even if rates already exist"
    )

    @field_validator('currencies')
    @classmethod
    def uppercase_currencies(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Ensure all currency codes are uppercase"""
        if v is None:
            return None
        return [currency.upper().strip() for currency in v]

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure end_date is not before start_date"""
        if v is not None and 'start_date' in info.data:
            start_date = info.data['start_date']
            if start_date is not None and v < start_date:
                raise ValueError("end_date cannot be before start_date")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "start_date": "2025-12-01",
                "end_date": "2025-12-30",
                "currencies": ["USD", "EUR"],
                "force_update": False
            }
        }
    )


class ExchangeRateRecord(BaseModel):
    """Single exchange rate record"""
    currency: str = Field(description="Currency code")
    rate: Decimal = Field(description="Exchange rate to HUF")
    rate_date: date = Field(description="Date of the rate")
    unit: int = Field(default=1, description="Number of currency units (usually 1)")


class ExchangeRateSyncOutput(BaseModel):
    """
    Result of exchange rate synchronization operation.

    Contains sync statistics and error information.
    """
    success: bool = Field(description="Whether sync completed successfully")
    rates_fetched: int = Field(default=0, description="Number of rates fetched from MNB")
    rates_created: int = Field(default=0, description="Number of new rate records created")
    rates_updated: int = Field(default=0, description="Number of existing rate records updated")
    rates_skipped: int = Field(default=0, description="Number of rates skipped (already exist)")
    currencies_synced: List[str] = Field(default_factory=list, description="List of currencies synced")
    sync_date_range: Optional[str] = Field(default=None, description="Date range synced")
    errors: List[str] = Field(default_factory=list, description="List of errors if any")
    synced_at: datetime = Field(default_factory=datetime.now, description="Timestamp of sync")
    sync_log_id: Optional[int] = Field(default=None, description="ID of sync log record")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "rates_fetched": 60,
                "rates_created": 58,
                "rates_updated": 2,
                "rates_skipped": 0,
                "currencies_synced": ["USD", "EUR"],
                "sync_date_range": "2025-12-01 to 2025-12-30",
                "errors": [],
                "synced_at": "2025-12-30T10:30:00",
                "sync_log_id": 123
            }
        }
    )


class ExchangeRateQueryInput(BaseModel):
    """
    Input for querying exchange rates.

    Supports filtering by currency, date range.
    """
    currency: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Currency code to query"
    )
    from_date: Optional[date] = Field(
        default=None,
        description="Start date for rate query"
    )
    to_date: Optional[date] = Field(
        default=None,
        description="End date for rate query"
    )

    @field_validator('currency')
    @classmethod
    def uppercase_currency(cls, v: Optional[str]) -> Optional[str]:
        """Ensure currency code is uppercase"""
        if v is None:
            return None
        return v.upper().strip()

    model_config = ConfigDict(str_strip_whitespace=True)
