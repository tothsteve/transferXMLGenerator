"""
Beneficiary ViewSet - Beneficiary (kedvezményezett) management endpoints

Handles CRUD operations for company beneficiaries with advanced filtering,
search capabilities, and frequent status management.
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema

from ..models import Beneficiary
from ..serializers import BeneficiarySerializer
from ..permissions import IsCompanyMember, RequireBeneficiaryManagement
from ..services.beneficiary_service import BeneficiaryService
from ..filters import BeneficiaryFilterSet


class BeneficiaryViewSet(viewsets.ModelViewSet):
    """
    Kedvezményezettek kezelése

    Filtering: Uses BeneficiaryFilterSet for declarative filtering (~35 lines of manual logic replaced)

    Támogatott szűrések:
    - is_active: true/false
    - is_frequent: true/false
    - search: multi-field search (név, számlaszám, adószám, leírás, közlemény)
    - vat_number: adószám alapján szűrés
    - has_vat_number: true/false - adószámmal rendelkező beneficiaries
    - has_account_number: true/false - számlaszámmal rendelkező beneficiaries

    Jogosultság: BENEFICIARY_MANAGEMENT (írás) vagy BENEFICIARY_VIEW (olvasás)
    """
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBeneficiaryManagement]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BeneficiaryFilterSet
    ordering_fields = ['name', 'account_number', 'vat_number', 'description', 'remittance_information', 'is_active', 'is_frequent', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """
        Company-scoped queryset.

        Filtering is handled by BeneficiaryFilterSet.
        """
        if not hasattr(self.request, 'company') or not self.request.company:
            return Beneficiary.objects.none()

        return Beneficiary.objects.filter(company=self.request.company)

    def perform_create(self, serializer):
        """Assign company on creation"""
        serializer.save(company=self.request.company)

    @swagger_auto_schema(
        operation_description="Gyakori kedvezményezettek listája",
        responses={200: BeneficiarySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def frequent(self, request):
        """Gyakori kedvezményezettek listája"""
        beneficiaries = BeneficiaryService.get_frequent_beneficiaries(request.company)
        serializer = self.get_serializer(beneficiaries, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Kedvezményezett gyakori státuszának váltása",
        responses={200: BeneficiarySerializer}
    )
    @action(detail=True, methods=['post'])
    def toggle_frequent(self, request, pk=None):
        """Gyakori státusz váltása"""
        beneficiary = self.get_object()
        beneficiary = BeneficiaryService.toggle_frequent_status(beneficiary)
        serializer = self.get_serializer(beneficiary)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Adószámmal rendelkező, de számlaszám nélküli kedvezményezettek",
        responses={200: BeneficiarySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def vat_only(self, request):
        """Adószámmal rendelkező, de számlaszám nélküli kedvezményezettek listája"""
        filters = {
            'has_vat_number': True,
            'has_account_number': False,
            'is_active': True
        }
        beneficiaries = BeneficiaryService.get_company_beneficiaries(request.company, filters)
        serializer = self.get_serializer(beneficiaries, many=True)
        return Response(serializer.data)
