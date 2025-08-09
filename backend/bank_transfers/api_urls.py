from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    BankAccountViewSet, BeneficiaryViewSet, TransferTemplateViewSet,
    TransferViewSet, TransferBatchViewSet, ExcelImportView
)

router = DefaultRouter()
router.register(r'bank-accounts', BankAccountViewSet)
router.register(r'beneficiaries', BeneficiaryViewSet)
router.register(r'templates', TransferTemplateViewSet)
router.register(r'transfers', TransferViewSet)
router.register(r'batches', TransferBatchViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload/excel/', ExcelImportView.as_view(), name='excel-import'),
]
