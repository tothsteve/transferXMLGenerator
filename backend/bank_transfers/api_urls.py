from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import (
    BankAccountViewSet, BeneficiaryViewSet, TransferTemplateViewSet,
    TransferViewSet, TransferBatchViewSet, ExcelImportView, DebugAuthView,
    CompanyUsersView, CompanyUserDetailView
)
from .authentication import AuthenticationViewSet

router = DefaultRouter()
router.register(r'auth', AuthenticationViewSet, basename='auth')
router.register(r'bank-accounts', BankAccountViewSet, basename='bankaccount')
router.register(r'beneficiaries', BeneficiaryViewSet, basename='beneficiary')
router.register(r'templates', TransferTemplateViewSet, basename='transfertemplate')
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'batches', TransferBatchViewSet, basename='transferbatch')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/excel/', ExcelImportView.as_view(), name='excel-import'),
    path('debug/auth/', DebugAuthView.as_view(), name='debug-auth'),
    # User Management endpoints
    path('company/users/', CompanyUsersView.as_view(), name='company-users'),
    path('company/users/<int:user_id>/', CompanyUserDetailView.as_view(), name='company-user-detail'),
    # JWT Token endpoints
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
