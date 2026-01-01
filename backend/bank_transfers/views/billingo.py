"""
Billingo Integration ViewSets

This module handles Billingo accounting integration operations:
- API settings configuration (API key management)
- Invoice synchronization (manual and automatic)
- Invoice listing with advanced filtering
- Sync logs and history tracking
- Spendings (cost) synchronization and listing

Domain: Billingo Accounting Integration
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)

from ..models import (
    CompanyBillingoSettings, BillingoInvoice, BillingoSyncLog,
    BillingoSpending
)
from ..serializers import (
    CompanyBillingoSettingsSerializer, BillingoInvoiceSerializer,
    BillingoInvoiceListSerializer, BillingoSyncLogSerializer,
    BillingoSyncTriggerSerializer, BillingoSpendingListSerializer,
    BillingoSpendingDetailSerializer
)
from ..permissions import IsCompanyMember, IsCompanyAdmin, RequireBillingoSync
from ..filters import BillingoInvoiceFilterSet


class CompanyBillingoSettingsViewSet(viewsets.ModelViewSet):
    """
    Billingo API beállítások kezelése

    Lehetővé teszi a Billingo API kulcs konfigurálását és
    a szinkronizálás engedélyezését/tiltását cégenként.
    """
    serializer_class = CompanyBillingoSettingsSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBillingoSync]

    def get_queryset(self):
        """Csak a cég beállítása"""
        company = getattr(self.request, 'company', None)
        if not company:
            return CompanyBillingoSettings.objects.none()

        return CompanyBillingoSettings.objects.filter(company=company)

    def create(self, request, *args, **kwargs):
        """
        Create or update Billingo settings for the company.

        Since each company can only have one settings record (enforced by unique constraint),
        this endpoint implements update-or-create logic:
        - If settings exist: UPDATE them
        - If settings don't exist: CREATE them
        """
        company = request.company

        # Check if settings already exist for this company
        try:
            instance = CompanyBillingoSettings.objects.get(company=company)
            # Settings exist - perform update
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CompanyBillingoSettings.DoesNotExist:
            # Settings don't exist - perform create
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(company=company)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        operation_description="Billingo szinkronizálás manuális indítása",
        request_body=BillingoSyncTriggerSerializer,
        responses={
            200: openapi.Response(
                description="Szinkronizálás sikeres",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'invoices_processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'invoices_created': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'invoices_updated': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'duration_seconds': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: 'Érvénytelen kérés',
            404: 'Nincs Billingo beállítás',
            500: 'Szinkronizálási hiba'
        }
    )
    @action(detail=False, methods=['post'])
    def trigger_sync(self, request):
        """
        Trigger manual Billingo sync for current company.

        POST /api/billingo-settings/trigger_sync/
        Body: { "full_sync": true|false }  (optional, defaults to false for incremental sync)
        """
        from ..services.billingo_sync_service import BillingoSyncService, BillingoAPIError

        company = request.company

        # Check if Billingo settings exist
        try:
            settings = CompanyBillingoSettings.objects.get(company=company)
        except CompanyBillingoSettings.DoesNotExist:
            return Response(
                {'error': 'Nincs Billingo beállítás konfigurálva ennél a cégnél'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not settings.is_active:
            return Response(
                {'error': 'Billingo szinkronizálás le van tiltva ennél a cégnél'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get full_sync parameter from request body (default: False for incremental sync)
        full_sync = request.data.get('full_sync', False)

        # Trigger sync
        try:
            service = BillingoSyncService()
            result = service.sync_company(company, sync_type='MANUAL', full_sync=full_sync)

            return Response({
                'status': 'success',
                'invoices_processed': result['invoices_processed'],
                'invoices_created': result['invoices_created'],
                'invoices_updated': result['invoices_updated'],
                'invoices_skipped': result['invoices_skipped'],
                'items_extracted': result['items_extracted'],
                'api_calls': result['api_calls'],
                'duration_seconds': result['duration_seconds'],
                'errors': result.get('errors', [])
            })

        except BillingoAPIError as e:
            logger.error(f"Billingo sync failed for company {company.id}: {str(e)}")
            return Response(
                {'error': f'Billingo szinkronizálás hiba: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during Billingo sync: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Váratlan hiba történt: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Billingo API kulcs tesztelése",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['api_key'],
            properties={
                'api_key': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Billingo API kulcs teszteléshez'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="API kulcs érvényes",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'organization_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'organization_tax_number': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: 'Érvénytelen kérés',
        }
    )
    @action(detail=False, methods=['post'])
    def test_credentials(self, request):
        """
        Test Billingo API credentials.

        POST /api/billingo-settings/test_credentials/
        Body: { "api_key": "your-api-key-here" }

        Returns:
            200: { "valid": true, "organization_name": "...", "organization_tax_number": "..." }
            200: { "valid": false, "error": "..." }
        """
        from ..services.billingo_sync_service import BillingoSyncService

        api_key = request.data.get('api_key')

        if not api_key:
            return Response(
                {'error': 'API kulcs megadása kötelező'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Test credentials using service
        try:
            service = BillingoSyncService()
            result = service.validate_and_test_credentials(api_key)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Credential validation error: {str(e)}", exc_info=True)
            return Response(
                {'valid': False, 'error': f'Váratlan hiba: {str(e)}'},
                status=status.HTTP_200_OK  # Return 200 with valid:false instead of 500
            )


class BillingoInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Billingo számlák megtekintése

    Szinkronizált számlák lekérdezése Billingo-ból.
    Csak olvasható - a számlák az API szinkronizálással frissülnek.

    Szűrések (django-filter FilterSet):
    - invoice_number: számlaszám alapján keresés (operator support)
    - partner_name: partner név alapján (operator support)
    - partner_tax_number: partner adószáma alapján (operator support)
    - payment_status: fizetési státusz (paid, unpaid, overdue stb.)
    - cancelled: true/false - sztornózott számlák
    - invoice_date: számla dátuma (operator support)
    - due_date: esedékesség dátuma (operator support)
    - gross_total: bruttó összeg (operator support)
    - net_total: nettó összeg (operator support)

    Operator support: contains, equals, startsWith, endsWith, isEmpty, isNotEmpty, =, !=, <, <=, >, >=, etc.
    """
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBillingoSync]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BillingoInvoiceFilterSet
    search_fields = ['invoice_number', 'partner_name', 'partner_tax_number']
    ordering_fields = ['invoice_number', 'partner_name', 'invoice_date', 'due_date', 'gross_total', 'net_total', 'payment_status']
    ordering = ['-invoice_date']

    def get_queryset(self):
        """Company-scoped queryset with prefetch optimization"""
        company = getattr(self.request, 'company', None)
        if not company:
            return BillingoInvoice.objects.none()

        return BillingoInvoice.objects.filter(company=company).prefetch_related('items')

    def get_serializer_class(self):
        """Use list serializer for list view, detail for retrieve"""
        if self.action == 'list':
            return BillingoInvoiceListSerializer
        return BillingoInvoiceSerializer


class BillingoSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Billingo szinkronizálási naplók megtekintése

    Audit log a Billingo szinkronizálási műveletekről.
    Csak olvasható - a naplókat a sync service hozza létre.

    Szűrések:
    - sync_type: MANUAL vagy AUTOMATIC
    - status: RUNNING, COMPLETED, FAILED, PARTIAL
    - from_date: started_at >= (YYYY-MM-DD)
    - to_date: started_at <= (YYYY-MM-DD)
    """
    serializer_class = BillingoSyncLogSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBillingoSync]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['started_at', 'sync_duration_seconds', 'invoices_processed']
    ordering = ['-started_at']

    def get_queryset(self):
        """Csak a cég szinkronizálási naplói"""
        company = getattr(self.request, 'company', None)
        if not company:
            return BillingoSyncLog.objects.none()

        queryset = BillingoSyncLog.objects.filter(company=company)

        # Filter by sync type
        sync_type = self.request.query_params.get('sync_type')
        if sync_type:
            queryset = queryset.filter(sync_type=sync_type.upper())

        # Filter by status
        sync_status = self.request.query_params.get('status')
        if sync_status:
            queryset = queryset.filter(status=sync_status.upper())

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(started_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(started_at__lte=to_date)

        return queryset


class BillingoSpendingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Billingo költségek megtekintése

    Szinkronizált költségek lekérdezése Billingo-ból.
    Csak olvasható - a költségek az API szinkronizálással frissülnek.

    Szűrések:
    - category: kategória (advertisement, development, stb.)
    - paid: true/false - kifizetett költségek
    - partner_tax_code: partner adószáma
    - invoice_number: számlaszám keresés
    - from_date: számla dátuma >= (YYYY-MM-DD)
    - to_date: számla dátuma <= (YYYY-MM-DD)
    - payment_method: fizetési mód
    """
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBillingoSync]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'partner_name', 'partner_tax_code', 'comment']
    ordering_fields = ['invoice_date', 'due_date', 'total_gross_local']
    ordering = ['-invoice_date']

    def get_queryset(self):
        """Csak a cég költségei"""
        company = getattr(self.request, 'company', None)
        if not company:
            return BillingoSpending.objects.none()

        queryset = BillingoSpending.objects.filter(company=company)

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by paid status
        paid = self.request.query_params.get('paid')
        if paid is not None:
            if paid.lower() == 'true':
                queryset = queryset.filter(paid_at__isnull=False)
            else:
                queryset = queryset.filter(paid_at__isnull=True)

        # Filter by partner tax code
        partner_tax_code = self.request.query_params.get('partner_tax_code')
        if partner_tax_code:
            queryset = queryset.filter(partner_tax_code=partner_tax_code)

        # Filter by invoice number
        invoice_number = self.request.query_params.get('invoice_number')
        if invoice_number:
            queryset = queryset.filter(invoice_number__icontains=invoice_number)

        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(invoice_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(invoice_date__lte=to_date)

        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        return queryset

    def get_serializer_class(self):
        """Use list serializer for list view, detail for retrieve"""
        if self.action == 'list':
            return BillingoSpendingListSerializer
        return BillingoSpendingDetailSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsCompanyMember, IsCompanyAdmin])
    def trigger_sync(self, request):
        """
        Trigger manual Billingo spendings sync.
        ADMIN role required.

        POST params:
        - full_sync: boolean (default: false) - If true, ignores last sync date
        """
        from ..management.commands.sync_billingo_spendings import Command as SyncCommand

        company = request.company
        full_sync = request.data.get('full_sync', False)

        sync_command = SyncCommand()
        result = sync_command.sync_company_spendings(company, full_sync=full_sync)

        if result.get('error'):
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'success': True,
            'spendings_created': result['created'],
            'spendings_updated': result['updated'],
            'spendings_skipped': result['skipped'],
            'spendings_processed': result['created'] + result['updated']
        })
