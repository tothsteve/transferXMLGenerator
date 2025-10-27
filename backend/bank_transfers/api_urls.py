from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import (
    BankAccountViewSet, BeneficiaryViewSet, TransferTemplateViewSet,
    TransferViewSet, TransferBatchViewSet, ExcelImportView,
    CompanyUsersView, CompanyUserDetailView, InvoiceViewSet, InvoiceSyncLogViewSet,
    TrustedPartnerViewSet, ExchangeRateViewSet,
    BankStatementViewSet, BankTransactionViewSet, OtherCostViewSet,
    CompanyBillingoSettingsViewSet, BillingoInvoiceViewSet, BillingoSyncLogViewSet
)
from .authentication import AuthenticationViewSet
from .views.nav_views import (
    NavConfigurationViewSet, InvoiceLineItemViewSet
)

router = DefaultRouter()
router.register(r'auth', AuthenticationViewSet, basename='auth')
router.register(r'bank-accounts', BankAccountViewSet, basename='bankaccount')
router.register(r'beneficiaries', BeneficiaryViewSet, basename='beneficiary')
router.register(r'templates', TransferTemplateViewSet, basename='transfertemplate')
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'batches', TransferBatchViewSet, basename='transferbatch')

# NAV Invoice Synchronization endpoints
router.register(r'nav/configurations', NavConfigurationViewSet, basename='navconfig')
router.register(r'nav/invoices', InvoiceViewSet, basename='invoice')
router.register(r'nav/line-items', InvoiceLineItemViewSet, basename='invoicelineitem')
router.register(r'nav/sync-logs', InvoiceSyncLogViewSet, basename='invoicesynclog')

# Trusted Partners endpoints
router.register(r'trusted-partners', TrustedPartnerViewSet, basename='trustedpartner')

# MNB Exchange Rate endpoints
router.register(r'exchange-rates', ExchangeRateViewSet, basename='exchangerate')

# Bank Statement Import endpoints
router.register(r'bank-statements', BankStatementViewSet, basename='bankstatement')
router.register(r'bank-transactions', BankTransactionViewSet, basename='banktransaction')
router.register(r'other-costs', OtherCostViewSet, basename='othercost')

# Billingo Integration endpoints
router.register(r'billingo-settings', CompanyBillingoSettingsViewSet, basename='billingosettings')
router.register(r'billingo-invoices', BillingoInvoiceViewSet, basename='billingoinvoice')
router.register(r'billingo-sync-logs', BillingoSyncLogViewSet, basename='billingosynclog')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/excel/', ExcelImportView.as_view(), name='excel-import'),
    # User Management endpoints
    path('company/users/', CompanyUsersView.as_view(), name='company-users'),
    path('company/users/<int:user_id>/', CompanyUserDetailView.as_view(), name='company-user-detail'),
    # JWT Token endpoints
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
