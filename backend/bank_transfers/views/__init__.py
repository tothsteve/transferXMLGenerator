"""
Bank Transfers Views - Feature-based vertical slices

This package organizes ViewSets by feature/domain instead of having one monolithic api_views.py file.
Each module exports its ViewSets which are then imported by api_urls.py for URL routing.
"""

# Bank Accounts
from .bank_accounts import BankAccountViewSet

# Beneficiaries
from .beneficiaries import BeneficiaryViewSet

# Transfers
from .transfers import (
    TransferTemplateViewSet, TransferViewSet, TransferBatchViewSet, ExcelImportView
)

# Company Users
from .company_users import CompanyUsersView, CompanyUserDetailView

# NAV Invoices
from .invoices import InvoiceViewSet, InvoiceSyncLogViewSet

# Trusted Partners
from .trusted_partners import TrustedPartnerViewSet

# Exchange Rates
from .exchange_rates import ExchangeRateViewSet

# Bank Statements
from .bank_statements import BankStatementViewSet, BankTransactionViewSet, OtherCostViewSet

# Billingo Integration
from .billingo import (
    CompanyBillingoSettingsViewSet, BillingoInvoiceViewSet,
    BillingoSyncLogViewSet, BillingoSpendingViewSet
)

# Base Tables
from .base_tables import (
    SupplierCategoryViewSet, SupplierTypeViewSet, SupplierViewSet,
    CustomerViewSet, ProductPriceViewSet
)

# NAV Views (legacy location)
from .nav_views import NavConfigurationViewSet, InvoiceLineItemViewSet

__all__ = [
    # Bank Accounts
    'BankAccountViewSet',
    # Beneficiaries
    'BeneficiaryViewSet',
    # Transfers
    'TransferTemplateViewSet',
    'TransferViewSet',
    'TransferBatchViewSet',
    'ExcelImportView',
    # Company Users
    'CompanyUsersView',
    'CompanyUserDetailView',
    # NAV Invoices
    'InvoiceViewSet',
    'InvoiceSyncLogViewSet',
    # Trusted Partners
    'TrustedPartnerViewSet',
    # Exchange Rates
    'ExchangeRateViewSet',
    # Bank Statements
    'BankStatementViewSet',
    'BankTransactionViewSet',
    'OtherCostViewSet',
    # Billingo Integration
    'CompanyBillingoSettingsViewSet',
    'BillingoInvoiceViewSet',
    'BillingoSyncLogViewSet',
    'BillingoSpendingViewSet',
    # Base Tables
    'SupplierCategoryViewSet',
    'SupplierTypeViewSet',
    'SupplierViewSet',
    'CustomerViewSet',
    'ProductPriceViewSet',
    # NAV Views
    'NavConfigurationViewSet',
    'InvoiceLineItemViewSet',
]
