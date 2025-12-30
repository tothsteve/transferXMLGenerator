"""
Pydantic schemas for type-safe service layer DTOs.

This package contains Pydantic v2 models that provide:
- Type-safe input/output validation for service layer
- Independent validation logic decoupled from Django models
- Cross-field validation capabilities
- Better OpenAPI schema generation
- Easier testing without Django dependencies
"""

from .exchange_rate import (
    CurrencyConversionInput,
    CurrencyConversionOutput,
    ExchangeRateSyncInput,
    ExchangeRateSyncOutput,
)
from .invoice import (
    InvoiceSyncInput,
    InvoiceSyncOutput,
    InvoiceQueryInput,
    TrustedPartnerInput,
    PaymentStatusUpdateInput,
)
from .bank_statement import (
    BankStatementUploadInput,
    BankStatementParseOutput,
    TransactionMatchInput,
    TransactionMatchOutput,
)
from .transfer import (
    TransferCreateInput,
    TransferBulkCreateInput,
    TemplateLoadInput,
    XmlGenerationInput,
    XmlGenerationOutput,
)

__all__ = [
    # Exchange Rate schemas
    'CurrencyConversionInput',
    'CurrencyConversionOutput',
    'ExchangeRateSyncInput',
    'ExchangeRateSyncOutput',
    # Invoice schemas
    'InvoiceSyncInput',
    'InvoiceSyncOutput',
    'InvoiceQueryInput',
    'TrustedPartnerInput',
    'PaymentStatusUpdateInput',
    # Bank Statement schemas
    'BankStatementUploadInput',
    'BankStatementParseOutput',
    'TransactionMatchInput',
    'TransactionMatchOutput',
    # Transfer schemas
    'TransferCreateInput',
    'TransferBulkCreateInput',
    'TemplateLoadInput',
    'XmlGenerationInput',
    'XmlGenerationOutput',
]
