from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import (
    BankAccountViewSet, BeneficiaryViewSet, TransferTemplateViewSet,
    TransferViewSet, TransferBatchViewSet, ExcelImportView,
    CompanyUsersView, CompanyUserDetailView
)
from .authentication import AuthenticationViewSet
from .views.nav_views import (
    NavConfigurationViewSet, InvoiceViewSet, InvoiceLineItemViewSet, InvoiceSyncLogViewSet
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

urlpatterns = [
    path('', include(router.urls)),
    path('upload/excel/', ExcelImportView.as_view(), name='excel-import'),
    # User Management endpoints
    path('company/users/', CompanyUsersView.as_view(), name='company-users'),
    path('company/users/<int:user_id>/', CompanyUserDetailView.as_view(), name='company-user-detail'),
    # JWT Token endpoints
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
