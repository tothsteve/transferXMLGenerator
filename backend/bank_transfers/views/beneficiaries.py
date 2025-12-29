"""
Beneficiary ViewSet - Beneficiary (kedvezményezett) management endpoints

Handles CRUD operations for company beneficiaries with advanced filtering,
search capabilities, and frequent status management.
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

from ..models import Beneficiary
from ..serializers import BeneficiarySerializer
from ..permissions import IsCompanyMember, RequireBeneficiaryManagement
from ..services.beneficiary_service import BeneficiaryService


class BeneficiaryViewSet(viewsets.ModelViewSet):
    """
    Kedvezményezettek kezelése

    Támogatott szűrések:
    - is_active: true/false
    - is_frequent: true/false
    - search: név, számlaszám, adószám és leírás alapján keresés
    - vat_number: adószám alapján szűrés
    - has_vat_number: true/false - adószámmal rendelkező beneficiaries
    - has_account_number: true/false - számlaszámmal rendelkező beneficiaries

    Jogosultság: BENEFICIARY_MANAGEMENT (írás) vagy BENEFICIARY_VIEW (olvasás)
    """
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBeneficiaryManagement]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['name', 'account_number', 'vat_number', 'description', 'remittance_information', 'is_active', 'is_frequent', 'created_at']
    ordering = ['name']  # Default ordering

    def get_queryset(self):
        if not hasattr(self.request, 'company') or not self.request.company:
            return Beneficiary.objects.none()

        # Build filters from query parameters
        filters = {}

        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            filters['is_active'] = is_active.lower() == 'true'

        is_frequent = self.request.query_params.get('is_frequent', None)
        if is_frequent is not None:
            filters['is_frequent'] = is_frequent.lower() == 'true'

        search = self.request.query_params.get('search', None)
        if search:
            filters['search'] = search

        # VAT number specific filters
        vat_number = self.request.query_params.get('vat_number', None)
        if vat_number:
            filters['vat_number'] = vat_number

        has_vat_number = self.request.query_params.get('has_vat_number', None)
        if has_vat_number is not None:
            filters['has_vat_number'] = has_vat_number.lower() == 'true'

        has_account_number = self.request.query_params.get('has_account_number', None)
        if has_account_number is not None:
            filters['has_account_number'] = has_account_number.lower() == 'true'

        return BeneficiaryService.get_company_beneficiaries(self.request.company, filters)

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
