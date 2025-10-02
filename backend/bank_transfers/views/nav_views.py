"""
Django REST Framework views for NAV Invoice data.

These views provide READ-ONLY API access to NAV invoice data with comprehensive
filtering, search, and pagination capabilities. All views are read-only and
never modify NAV data.

CRITICAL: All views are READ-ONLY. They do not support creating, updating,
          or deleting NAV data, only querying existing local data.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import NavConfiguration, InvoiceLineItem
from ..serializers import NavConfigurationSerializer, InvoiceLineItemSerializer
from ..services.invoice_sync_service import InvoiceSyncService


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