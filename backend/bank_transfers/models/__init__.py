"""
Models package for bank_transfers app.

This package organizes models into feature-based modules for better maintainability.
All models are imported here to ensure Django discovers them for migrations.
"""

# Company and user management models
from .company import (
    Company,
    CompanyUser,
    UserProfile,
    FeatureTemplate,
    CompanyFeature,
    CompanyFeatureManager,
)

# Banking and transfer models
from .banking import (
    BankAccount,
    Beneficiary,
    TransferTemplate,
    TemplateBeneficiary,
    Transfer,
    TransferBatch,
)

# NAV invoice integration models
from .invoices import (
    NavConfigurationManager,
    NavConfiguration,
    Invoice,
    InvoiceLineItem,
    InvoiceSyncLog,
    BankTransactionInvoiceMatch,
    TrustedPartner,
)

# Exchange rate models
from .exchange_rates import (
    ExchangeRate,
    ExchangeRateSyncLog,
)

# Bank statement and transaction models
from .bank_statements import (
    BankStatement,
    BankTransaction,
    OtherCost,
)

# Billingo integration models
from .billingo import (
    CompanyBillingoSettings,
    BillingoInvoice,
    BillingoRelatedDocument,
    BillingoInvoiceItem,
    BillingoSyncLog,
    BillingoSpending,
)

# Base tables models
from .base_tables import (
    SupplierCategory,
    SupplierType,
    Supplier,
    Customer,
    ProductPrice,
)

__all__ = [
    # Company models
    'Company',
    'CompanyUser',
    'UserProfile',
    'FeatureTemplate',
    'CompanyFeature',
    'CompanyFeatureManager',
    # Banking models
    'BankAccount',
    'Beneficiary',
    'TransferTemplate',
    'TemplateBeneficiary',
    'Transfer',
    'TransferBatch',
    # Invoice models
    'NavConfigurationManager',
    'NavConfiguration',
    'Invoice',
    'InvoiceLineItem',
    'InvoiceSyncLog',
    'BankTransactionInvoiceMatch',
    'TrustedPartner',
    # Exchange rate models
    'ExchangeRate',
    'ExchangeRateSyncLog',
    # Bank statement models
    'BankStatement',
    'BankTransaction',
    'OtherCost',
    # Billingo models
    'CompanyBillingoSettings',
    'BillingoInvoice',
    'BillingoRelatedDocument',
    'BillingoInvoiceItem',
    'BillingoSyncLog',
    'BillingoSpending',
    # Base tables models
    'SupplierCategory',
    'SupplierType',
    'Supplier',
    'Customer',
    'ProductPrice',
]
