"""
Serializers Package

This package organizes serializers into feature-based modules for better maintainability.
All serializers are exported from their respective modules to maintain backward compatibility.

Module Structure:
- banking.py: Bank accounts, beneficiaries, templates, transfers, batches
- invoices.py: NAV invoice synchronization and trusted partners
- exchange_rates.py: MNB exchange rate integration
- bank_statements.py: Bank statement import and transaction matching
- billingo.py: Billingo invoice management integration
- base_tables.py: Base tables (suppliers, customers, product prices)
"""

# Banking serializers
from .banking import (
    BankAccountSerializer,
    BeneficiarySerializer,
    TemplateBeneficiarySerializer,
    TransferTemplateSerializer,
    TransferSerializer,
    TransferBatchSerializer,
    TransferCreateFromTemplateSerializer,
    BulkTransferSerializer,
    ExcelImportSerializer,
    XMLGenerateSerializer,
)

# Invoice serializers
from .invoices import (
    NavConfigurationSerializer,
    InvoiceLineItemSerializer,
    InvoiceSerializer,
    InvoiceSummarySerializer,
    InvoiceListSerializer,
    InvoiceDetailSerializer,
    InvoiceSyncLogSerializer,
    InvoiceStatsSerializer,
    TrustedPartnerSerializer,
)

# Exchange rate serializers
from .exchange_rates import (
    ExchangeRateSerializer,
    ExchangeRateSyncLogSerializer,
    ExchangeRateListSerializer,
    CurrentRatesSerializer,
    ExchangeRateHistorySerializer,
    CurrencyConversionSerializer,
)

# Bank statement serializers
from .bank_statements import (
    BankTransactionInvoiceMatchSerializer,
    BankTransactionSerializer,
    BankStatementListSerializer,
    BankStatementDetailSerializer,
    BankStatementUploadSerializer,
    OtherCostSerializer,
    SupportedBanksSerializer,
)

# Billingo serializers
from .billingo import (
    BillingoInvoiceItemSerializer,
    BillingoRelatedDocumentSerializer,
    BillingoInvoiceSerializer,
    BillingoInvoiceListSerializer,
    CompanyBillingoSettingsSerializer,
    BillingoSyncLogSerializer,
    BillingoSyncTriggerSerializer,
    BillingoSpendingListSerializer,
    BillingoSpendingDetailSerializer,
)

# Base tables serializers
from .base_tables import (
    SupplierCategorySerializer,
    SupplierTypeSerializer,
    SupplierSerializer,
    CustomerSerializer,
    ProductPriceSerializer,
)

__all__ = [
    # Banking
    'BankAccountSerializer',
    'BeneficiarySerializer',
    'TemplateBeneficiarySerializer',
    'TransferTemplateSerializer',
    'TransferSerializer',
    'TransferBatchSerializer',
    'TransferCreateFromTemplateSerializer',
    'BulkTransferSerializer',
    'ExcelImportSerializer',
    'XMLGenerateSerializer',

    # Invoices
    'NavConfigurationSerializer',
    'InvoiceLineItemSerializer',
    'InvoiceSerializer',
    'InvoiceSummarySerializer',
    'InvoiceListSerializer',
    'InvoiceDetailSerializer',
    'InvoiceSyncLogSerializer',
    'InvoiceStatsSerializer',
    'TrustedPartnerSerializer',

    # Exchange rates
    'ExchangeRateSerializer',
    'ExchangeRateSyncLogSerializer',
    'ExchangeRateListSerializer',
    'CurrentRatesSerializer',
    'ExchangeRateHistorySerializer',
    'CurrencyConversionSerializer',

    # Bank statements
    'BankTransactionInvoiceMatchSerializer',
    'BankTransactionSerializer',
    'BankStatementListSerializer',
    'BankStatementDetailSerializer',
    'BankStatementUploadSerializer',
    'OtherCostSerializer',
    'SupportedBanksSerializer',

    # Billingo
    'BillingoInvoiceItemSerializer',
    'BillingoRelatedDocumentSerializer',
    'BillingoInvoiceSerializer',
    'BillingoInvoiceListSerializer',
    'CompanyBillingoSettingsSerializer',
    'BillingoSyncLogSerializer',
    'BillingoSyncTriggerSerializer',
    'BillingoSpendingListSerializer',
    'BillingoSpendingDetailSerializer',

    # Base tables
    'SupplierCategorySerializer',
    'SupplierTypeSerializer',
    'SupplierSerializer',
    'CustomerSerializer',
    'ProductPriceSerializer',
]
