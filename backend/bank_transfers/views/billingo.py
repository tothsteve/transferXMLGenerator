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


class BillingoInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Billingo számlák megtekintése

    Szinkronizált számlák lekérdezése Billingo-ból.
    Csak olvasható - a számlák az API szinkronizálással frissülnek.

    Szűrések:
    - invoice_number: számlaszám alapján keresés
    - partner_tax_number: partner adószáma alapján
    - payment_status: fizetési státusz (paid, unpaid, overdue stb.)
    - cancelled: true/false - sztornózott számlák
    - from_date: számla dátuma >= (YYYY-MM-DD)
    - to_date: számla dátuma <= (YYYY-MM-DD)
    """
    permission_classes = [IsAuthenticated, IsCompanyMember, RequireBillingoSync]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'partner_name', 'partner_tax_number']
    ordering_fields = ['invoice_number', 'partner_name', 'invoice_date', 'due_date', 'gross_total', 'net_total', 'payment_status']
    ordering = ['-invoice_date']

    def _apply_string_filter(self, queryset, field_name, value, operator='contains'):
        """Apply operator-based filter for string fields"""
        if value:
            if operator == 'contains':
                return queryset.filter(**{f'{field_name}__icontains': value})
            elif operator == 'notContains':
                return queryset.exclude(**{f'{field_name}__icontains': value})
            elif operator == 'equals':
                return queryset.filter(**{f'{field_name}__iexact': value})
            elif operator == 'notEqual':
                return queryset.exclude(**{f'{field_name}__iexact': value})
            elif operator == 'startsWith':
                return queryset.filter(**{f'{field_name}__istartswith': value})
            elif operator == 'endsWith':
                return queryset.filter(**{f'{field_name}__iendswith': value})
        elif operator == 'isEmpty':
            return queryset.filter(**{f'{field_name}__isnull': True}) | queryset.filter(**{field_name: ''})
        elif operator == 'isNotEmpty':
            return queryset.exclude(**{f'{field_name}__isnull': True}).exclude(**{field_name: ''})
        return queryset

    def _apply_boolean_filter(self, queryset, field_name, value, operator='is'):
        """Apply operator-based filter for boolean fields"""
        if value is not None:
            bool_value = value.lower() == 'true' if isinstance(value, str) else bool(value)
            if operator == 'is':
                return queryset.filter(**{field_name: bool_value})
        return queryset

    def _apply_date_filter(self, queryset, field_name, value, operator='is'):
        """Apply operator-based filter for date fields"""
        if value:
            if operator == 'is':
                return queryset.filter(**{field_name: value})
            elif operator == 'not':
                return queryset.exclude(**{field_name: value})
            elif operator == 'after':
                return queryset.filter(**{f'{field_name}__gt': value})
            elif operator == 'onOrAfter':
                return queryset.filter(**{f'{field_name}__gte': value})
            elif operator == 'before':
                return queryset.filter(**{f'{field_name}__lt': value})
            elif operator == 'onOrBefore':
                return queryset.filter(**{f'{field_name}__lte': value})
        elif operator == 'isEmpty':
            return queryset.filter(**{f'{field_name}__isnull': True})
        elif operator == 'isNotEmpty':
            return queryset.exclude(**{f'{field_name}__isnull': True})
        return queryset

    def _apply_numeric_filter(self, queryset, field_name, value, operator='='):
        """Apply operator-based filter for numeric fields"""
        if value:
            if operator == '=':
                return queryset.filter(**{field_name: value})
            elif operator == '!=':
                return queryset.exclude(**{field_name: value})
            elif operator == '>':
                return queryset.filter(**{f'{field_name}__gt': value})
            elif operator == '>=':
                return queryset.filter(**{f'{field_name}__gte': value})
            elif operator == '<':
                return queryset.filter(**{f'{field_name}__lt': value})
            elif operator == '<=':
                return queryset.filter(**{f'{field_name}__lte': value})
        elif operator == 'isEmpty':
            return queryset.filter(**{f'{field_name}__isnull': True})
        elif operator == 'isNotEmpty':
            return queryset.exclude(**{f'{field_name}__isnull': True})
        return queryset

    def get_queryset(self):
        """Csak a cég számlái"""
        company = getattr(self.request, 'company', None)
        if not company:
            return BillingoInvoice.objects.none()

        queryset = BillingoInvoice.objects.filter(company=company).prefetch_related('items')

        # String filters with operator support
        queryset = self._apply_string_filter(
            queryset, 'invoice_number',
            self.request.query_params.get('invoice_number'),
            self.request.query_params.get('invoice_number_operator', 'contains')
        )

        queryset = self._apply_string_filter(
            queryset, 'partner_name',
            self.request.query_params.get('partner_name'),
            self.request.query_params.get('partner_name_operator', 'contains')
        )

        queryset = self._apply_string_filter(
            queryset, 'type',
            self.request.query_params.get('type'),
            self.request.query_params.get('type_operator', 'contains')
        )

        queryset = self._apply_string_filter(
            queryset, 'payment_status',
            self.request.query_params.get('payment_status'),
            self.request.query_params.get('payment_status_operator', 'equals')
        )

        # Boolean filter with operator support
        queryset = self._apply_boolean_filter(
            queryset, 'cancelled',
            self.request.query_params.get('cancelled'),
            self.request.query_params.get('cancelled_operator', 'is')
        )

        # Date filters with operator support
        queryset = self._apply_date_filter(
            queryset, 'invoice_date',
            self.request.query_params.get('invoice_date'),
            self.request.query_params.get('invoice_date_operator', 'is')
        )

        queryset = self._apply_date_filter(
            queryset, 'due_date',
            self.request.query_params.get('due_date'),
            self.request.query_params.get('due_date_operator', 'is')
        )

        # Numeric filters with operator support
        queryset = self._apply_numeric_filter(
            queryset, 'gross_total',
            self.request.query_params.get('gross_total'),
            self.request.query_params.get('gross_total_operator', '=')
        )

        queryset = self._apply_numeric_filter(
            queryset, 'net_total',
            self.request.query_params.get('net_total'),
            self.request.query_params.get('net_total_operator', '=')
        )

        # Legacy filters for backward compatibility (will be removed later)
        # These handle old query params like from_date, to_date, etc.
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(invoice_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(invoice_date__lte=to_date)

        due_date_from = self.request.query_params.get('due_date_from')
        due_date_to = self.request.query_params.get('due_date_to')
        if due_date_from:
            queryset = queryset.filter(due_date__gte=due_date_from)
        if due_date_to:
            queryset = queryset.filter(due_date__lte=due_date_to)

        gross_total_min = self.request.query_params.get('gross_total_min')
        gross_total_max = self.request.query_params.get('gross_total_max')
        if gross_total_min:
            queryset = queryset.filter(gross_total__gte=gross_total_min)
        if gross_total_max:
            queryset = queryset.filter(gross_total__lte=gross_total_max)

        net_total_min = self.request.query_params.get('net_total_min')
        net_total_max = self.request.query_params.get('net_total_max')
        if net_total_min:
            queryset = queryset.filter(net_total__gte=net_total_min)
        if net_total_max:
            queryset = queryset.filter(net_total__lte=net_total_max)

        partner_tax_number = self.request.query_params.get('partner_tax_number')
        if partner_tax_number:
            queryset = queryset.filter(partner_tax_number=partner_tax_number)

        # Filter for invoices with related documents (corrections, storno, etc.)
        # Only apply this filter to list view, not to retrieve (detail) view
        # If hide_related_invoices=true (default), exclude both parent and child invoices
        if self.action == 'list':
            hide_related = self.request.query_params.get('hide_related_invoices', 'true').lower() == 'true'
            if hide_related:
                from ..models import BillingoRelatedDocument

                # Get invoice IDs that have related documents (parent invoices)
                invoices_with_related = BillingoRelatedDocument.objects.filter(
                    invoice__company=company
                ).values_list('invoice_id', flat=True).distinct()

                # Get invoice IDs that are referenced in related_documents (child invoices)
                related_invoice_ids = BillingoRelatedDocument.objects.filter(
                    invoice__company=company
                ).values_list('related_invoice_id', flat=True).distinct()

                # Combine both exclusions - hide invoices that are either parent or child
                all_related_ids = set(invoices_with_related) | set(related_invoice_ids)

                if all_related_ids:
                    queryset = queryset.exclude(id__in=all_related_ids)

        return queryset

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
