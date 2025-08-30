"""
Django REST Framework views for NAV Invoice data.

These views provide READ-ONLY API access to NAV invoice data with comprehensive
filtering, search, and pagination capabilities. All views are read-only and
never modify NAV data.

CRITICAL: All views are READ-ONLY. They do not support creating, updating,
          or deleting NAV data, only querying existing local data.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Q, Count, Sum, Max
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from ..models import (
    NavConfiguration, Invoice, InvoiceLineItem, InvoiceSyncLog, Company
)
from ..serializers import (
    NavConfigurationSerializer, InvoiceSerializer, InvoiceSummarySerializer,
    InvoiceLineItemSerializer, InvoiceSyncLogSerializer, InvoiceStatsSerializer
)
from ..services.invoice_sync_service import InvoiceSyncService


class InvoiceFilter(filters.FilterSet):
    """
    Advanced filtering for Invoice model with Hungarian business logic.
    """
    
    # Date range filters
    issue_date_from = filters.DateFilter(field_name='issue_date', lookup_expr='gte')
    issue_date_to = filters.DateFilter(field_name='issue_date', lookup_expr='lte')
    fulfillment_date_from = filters.DateFilter(field_name='fulfillment_date', lookup_expr='gte')
    fulfillment_date_to = filters.DateFilter(field_name='fulfillment_date', lookup_expr='lte')
    
    # Amount range filters
    amount_from = filters.NumberFilter(field_name='invoice_gross_amount', lookup_expr='gte')
    amount_to = filters.NumberFilter(field_name='invoice_gross_amount', lookup_expr='lte')
    
    # Multi-choice filters
    invoice_direction = filters.ChoiceFilter(choices=[
        ('OUTBOUND', 'Kimenő'),
        ('INBOUND', 'Bejövő')
    ])
    currency_code = filters.ChoiceFilter(choices=[
        ('HUF', 'HUF'),
        ('EUR', 'EUR'),
        ('USD', 'USD')
    ])
    sync_status = filters.ChoiceFilter(choices=[
        ('PENDING', 'Függőben'),
        ('SYNCED', 'Szinkronizálva'),
        ('ERROR', 'Hiba')
    ])
    
    # Text search filters
    partner_name = filters.CharFilter(method='filter_partner_name')
    tax_number = filters.CharFilter(method='filter_tax_number')
    
    class Meta:
        model = Invoice
        fields = {
            'company': ['exact'],
            'nav_invoice_number': ['icontains'],
            'invoice_direction': ['exact'],
            'currency_code': ['exact'],
            'sync_status': ['exact'],
        }
    
    def filter_partner_name(self, queryset, name, value):
        """Filter by partner name (supplier or customer)."""
        return queryset.filter(
            Q(supplier_name__icontains=value) | Q(customer_name__icontains=value)
        )
    
    def filter_tax_number(self, queryset, name, value):
        """Filter by tax number (supplier or customer)."""
        return queryset.filter(
            Q(supplier_tax_number__icontains=value) | Q(customer_tax_number__icontains=value)
        )


class NavConfigurationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    READ-ONLY ViewSet for NAV configurations.
    
    Provides read-only access to NAV configuration data without exposing
    sensitive credential information.
    """
    
    queryset = NavConfiguration.objects.all()
    serializer_class = NavConfigurationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['company__name', 'tax_number', 'technical_user_login']
    filterset_fields = ['api_environment', 'sync_enabled', 'is_active']
    ordering_fields = ['company__name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter by user's accessible companies."""
        # TODO: Add company-based filtering based on user permissions
        return super().get_queryset().select_related('company')
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test NAV API connection for specific configuration.
        
        READ-ONLY OPERATION: Only tests connection, doesn't modify anything.
        """
        nav_config = self.get_object()
        sync_service = InvoiceSyncService()
        
        try:
            nav_client = sync_service._initialize_nav_client(nav_config)
            connection_success = nav_client.test_connection()
            
            return Response({
                'success': connection_success,
                'message': 'NAV kapcsolat sikeres' if connection_success else 'NAV kapcsolat sikertelen',
                'configuration': {
                    'company_name': nav_config.company.name,
                    'tax_number': nav_config.tax_number,
                    'environment': nav_config.api_environment
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Kapcsolat teszt hiba: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    READ-ONLY ViewSet for NAV invoices.
    
    Provides comprehensive read-only access to invoice data with advanced
    filtering, search, and statistical capabilities.
    """
    
    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InvoiceFilter
    search_fields = [
        'nav_invoice_number', 'supplier_name', 'customer_name',
        'supplier_tax_number', 'customer_tax_number'
    ]
    ordering_fields = [
        'issue_date', 'fulfillment_date', 'invoice_gross_amount',
        'created_at', 'nav_invoice_number'
    ]
    ordering = ['-issue_date', '-created_at']
    
    def get_queryset(self):
        """Optimize queryset with related data."""
        return super().get_queryset().select_related('company').prefetch_related('line_items')
    
    def get_serializer_class(self):
        """Use different serializers based on action."""
        if self.action == 'list':
            return InvoiceSummarySerializer
        return InvoiceSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get invoice statistics and dashboard data.
        
        READ-ONLY OPERATION: Only queries existing data for statistics.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Basic counts
        total_count = queryset.count()
        outbound_count = queryset.filter(invoice_direction='OUTBOUND').count()
        inbound_count = queryset.filter(invoice_direction='INBOUND').count()
        
        # Amount aggregations
        amount_stats = queryset.aggregate(
            total_gross=Sum('invoice_gross_amount'),
            total_net=Sum('invoice_net_amount'),
            total_vat=Sum('invoice_vat_amount')
        )
        
        # Currency breakdown
        currency_stats = queryset.values('currency_code').annotate(
            count=Count('id'),
            total_amount=Sum('invoice_gross_amount')
        ).order_by('-total_amount')
        
        # Recent activity
        last_30_days = timezone.now() - timedelta(days=30)
        recent_count = queryset.filter(created_at__gte=last_30_days).count()
        
        # Sync statistics
        # Remove last_sync tracking since field was removed
        
        sync_enabled_count = NavConfiguration.objects.filter(
            sync_enabled=True,
            is_active=True
        ).count()
        
        # Prepare statistics data
        stats_data = {
            'total_invoices': total_count,
            'outbound_invoices': outbound_count,
            'inbound_invoices': inbound_count,
            'total_gross_amount': amount_stats['total_gross'] or Decimal('0'),
            'total_net_amount': amount_stats['total_net'] or Decimal('0'),
            'total_vat_amount': amount_stats['total_vat'] or Decimal('0'),
            'currency_breakdown': {
                item['currency_code']: {
                    'count': item['count'],
                    'total_amount': item['total_amount']
                } for item in currency_stats
            },
            'sync_enabled_companies': sync_enabled_count,
            'recent_invoices_count': recent_count
        }
        
        serializer = InvoiceStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent invoices (last 30 days).
        
        READ-ONLY OPERATION: Queries recent invoice data only.
        """
        days = int(request.query_params.get('days', 30))
        date_from = timezone.now() - timedelta(days=days)
        
        recent_invoices = self.get_queryset().filter(
            created_at__gte=date_from
        ).order_by('-created_at')[:20]
        
        serializer = InvoiceSummarySerializer(recent_invoices, many=True)
        return Response({
            'count': recent_invoices.count(),
            'days': days,
            'invoices': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_company(self, request):
        """
        Get invoices grouped by company.
        
        READ-ONLY OPERATION: Aggregates invoice data by company.
        """
        company_stats = self.get_queryset().values(
            'company__name',
            'company__id'
        ).annotate(
            invoice_count=Count('id'),
            total_gross_amount=Sum('invoice_gross_amount'),
            outbound_count=Count('id', filter=Q(invoice_direction='OUTBOUND')),
            inbound_count=Count('id', filter=Q(invoice_direction='INBOUND')),
            last_invoice_date=Max('issue_date')
        ).order_by('-total_gross_amount')
        
        return Response({
            'companies': list(company_stats)
        })


class InvoiceLineItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    READ-ONLY ViewSet for invoice line items.
    
    Provides detailed read-only access to invoice line item data.
    """
    
    queryset = InvoiceLineItem.objects.all()
    serializer_class = InvoiceLineItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['invoice__company', 'invoice__id', 'vat_rate']
    search_fields = ['line_description', 'product_code_value']
    ordering_fields = ['line_number', 'line_gross_amount', 'created_at']
    ordering = ['invoice', 'line_number']
    
    def get_queryset(self):
        """Optimize queryset with invoice data."""
        return super().get_queryset().select_related('invoice', 'invoice__company')


class InvoiceSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    READ-ONLY ViewSet for invoice synchronization logs.
    
    Provides audit trail and monitoring data for NAV synchronization processes.
    """
    
    queryset = InvoiceSyncLog.objects.all()
    serializer_class = InvoiceSyncLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'company', 'sync_status', 'direction_synced'
    ]
    search_fields = ['company__name', 'last_error_message']
    ordering_fields = ['sync_start_time', 'sync_end_time', 'invoices_processed']
    ordering = ['-sync_start_time']
    
    def get_queryset(self):
        """Optimize queryset with company data."""
        return super().get_queryset().select_related('company')
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """
        Get recent synchronization activity.
        
        READ-ONLY OPERATION: Shows recent sync logs for monitoring.
        """
        days = int(request.query_params.get('days', 7))
        date_from = timezone.now() - timedelta(days=days)
        
        recent_logs = self.get_queryset().filter(
            sync_start_time__gte=date_from
        ).order_by('-sync_start_time')[:50]
        
        # Summary statistics
        total_syncs = recent_logs.count()
        successful_syncs = recent_logs.filter(sync_status='COMPLETED').count()
        failed_syncs = recent_logs.filter(sync_status='ERROR').count()
        total_invoices_processed = recent_logs.aggregate(
            total=Sum('invoices_processed')
        )['total'] or 0
        
        serializer = self.get_serializer(recent_logs, many=True)
        
        return Response({
            'period_days': days,
            'summary': {
                'total_syncs': total_syncs,
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'success_rate': round((successful_syncs / total_syncs * 100), 1) if total_syncs > 0 else 0,
                'total_invoices_processed': total_invoices_processed
            },
            'recent_logs': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def trigger_sync(self, request):
        """
        Trigger manual invoice synchronization.
        
        READ-ONLY OPERATION: Initiates sync process that only queries NAV data.
        """
        company_id = request.data.get('company_id')
        direction = request.data.get('direction', 'BOTH')
        days = int(request.data.get('days', 30))
        
        if not company_id:
            return Response({
                'error': 'company_id kötelező paraméter'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({
                'error': 'Cég nem található'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate date range
        date_to = timezone.now()
        date_from = date_to - timedelta(days=days)
        
        # Initialize sync service
        sync_service = InvoiceSyncService()
        
        try:
            if direction == 'BOTH':
                # Sync both directions
                outbound_result = sync_service.sync_company_invoices(
                    company=company,
                    date_from=date_from,
                    date_to=date_to,
                    direction='OUTBOUND'
                )
                inbound_result = sync_service.sync_company_invoices(
                    company=company,
                    date_from=date_from,
                    date_to=date_to,
                    direction='INBOUND'
                )
                
                return Response({
                    'success': True,
                    'message': f'Szinkronizáció elindítva: {company.name}',
                    'results': {
                        'outbound': outbound_result,
                        'inbound': inbound_result
                    }
                })
            else:
                # Sync single direction
                result = sync_service.sync_company_invoices(
                    company=company,
                    date_from=date_from,
                    date_to=date_to,
                    direction=direction
                )
                
                return Response({
                    'success': True,
                    'message': f'Szinkronizáció elindítva: {company.name} ({direction})',
                    'result': result
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Szinkronizáció hiba: {str(e)}',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)