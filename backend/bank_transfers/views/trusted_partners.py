"""
Trusted Partners Management ViewSet

This module handles trusted partner operations for automated payment processing:
- CRUD operations for trusted partners
- Automatic statistics updates (invoice counts, dates)
- Available partners discovery from NAV invoices
- Search and filtering capabilities

Domain: Trusted Partners & Auto-Payment
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Count, Max, Q
from django.core.paginator import Paginator

from ..models import TrustedPartner, Invoice
from ..serializers import TrustedPartnerSerializer
from ..permissions import IsCompanyMember


class TrustedPartnerViewSet(viewsets.ModelViewSet):
    """
    Megbízható partnerek kezelése automatikus fizetés feldolgozáshoz

    list: Az összes megbízható partner listája
    create: Új megbízható partner hozzáadása
    retrieve: Egy konkrét partner részletei
    update: Partner módosítása
    destroy: Partner törlése
    available_partners: Elérhető partnerek NAV számlákból

    Jogosultság: Authentikált felhasználó
    """
    serializer_class = TrustedPartnerSerializer
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filterset_fields = ['is_active', 'auto_pay']
    search_fields = ['partner_name', 'tax_number']
    ordering_fields = ['partner_name', 'tax_number', 'invoice_count', 'last_invoice_date', 'created_at']
    ordering = ['partner_name']

    def get_queryset(self):
        """Company-scoped queryset"""
        return TrustedPartner.objects.filter(company=self.request.company)

    def perform_create(self, serializer):
        """Auto-set company and update statistics"""
        partner = serializer.save(company=self.request.company)
        partner.update_statistics()

    def perform_update(self, serializer):
        """Update statistics after modification"""
        partner = serializer.save()
        partner.update_statistics()

    @swagger_auto_schema(
        operation_summary="Megbízható partnerek listája",
        operation_description="List of trusted partners for automatic payment processing"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Új megbízható partner",
        operation_description="Create a new trusted partner"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partner részletei",
        operation_description="Get detailed information about a specific trusted partner"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partner módosítása",
        operation_description="Update a trusted partner's information"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partner törlése",
        operation_description="Delete a trusted partner"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def available_partners(self, request):
        """
        Get available partners from NAV invoices that can be added as trusted partners.
        Supports search and ordering parameters.
        """
        # Get distinct suppliers from invoices that are not already trusted partners
        existing_tax_numbers = set(
            TrustedPartner.objects.filter(company=request.company)
            .values_list('tax_number', flat=True)
        )

        # Build base query
        query = Invoice.objects.filter(
            company=request.company,
            supplier_tax_number__isnull=False,
            supplier_name__isnull=False
        ).exclude(
            supplier_tax_number__in=existing_tax_numbers
        )

        # Apply search filter (case-insensitive)
        search = request.query_params.get('search', '').strip()
        if search:
            query = query.filter(
                Q(supplier_name__icontains=search) |
                Q(supplier_tax_number__icontains=search)
            )

        # Group by supplier and annotate with statistics
        available = query.values(
            'supplier_name', 'supplier_tax_number'
        ).annotate(
            invoice_count=Count('id'),
            last_invoice_date=Max('issue_date')
        )

        # Apply ordering (default: last_invoice_date descending)
        ordering = request.query_params.get('ordering', '-last_invoice_date')

        # Map ordering fields for the annotated query
        ordering_map = {
            'partner_name': 'supplier_name',
            '-partner_name': '-supplier_name',
            'tax_number': 'supplier_tax_number',
            '-tax_number': '-supplier_tax_number',
            'invoice_count': 'invoice_count',
            '-invoice_count': '-invoice_count',
            'last_invoice_date': 'last_invoice_date',
            '-last_invoice_date': '-last_invoice_date',
        }

        if ordering in ordering_map:
            available = available.order_by(ordering_map[ordering])
        else:
            # Default ordering: most recent invoices first
            available = available.order_by('-last_invoice_date')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # Convert to list to enable pagination
        available_list = list(available)

        # Create paginator
        paginator = Paginator(available_list, page_size)
        page_obj = paginator.get_page(page)

        # Format the response
        partners_data = []
        for item in page_obj.object_list:
            partners_data.append({
                'partner_name': item['supplier_name'],
                'tax_number': item['supplier_tax_number'],
                'invoice_count': item['invoice_count'],
                'last_invoice_date': item['last_invoice_date'].strftime('%Y-%m-%d') if item['last_invoice_date'] else None,
            })

        return Response({
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'results': partners_data
        })
