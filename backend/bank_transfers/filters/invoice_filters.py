"""
Invoice FilterSet - Declarative filtering for NAV invoices

This FilterSet replaces ~150 lines of manual filtering logic in InvoiceViewSet
with a clean, testable, declarative approach.
"""

import django_filters
from django.db import models
from datetime import date
from ..models import Invoice


class InvoiceFilterSet(django_filters.FilterSet):
    """
    Comprehensive filtering for NAV Invoice queryset.

    Supported filters:
    - direction: Invoice direction (INBOUND/OUTBOUND)
    - Date ranges: issue_date, fulfillment_date, payment_due_date
    - payment_status: PAID, UNPAID, PREPARED (or legacy: paid, unpaid, overdue)
    - Amount range: amount_from, amount_to
    - currency: Currency code filter
    - operation: Invoice operation (CREATE, STORNO, MODIFY)
    - payment_method: Payment method filter
    - search: Multi-field search (invoice number, names, tax numbers)
    - hide_storno_invoices: Hide STORNO/MODIFY invoices and storno'd invoices (default: true)
    """

    # Direction filter
    direction = django_filters.ChoiceFilter(
        field_name='invoice_direction',
        choices=[('INBOUND', 'Bejövő'), ('OUTBOUND', 'Kimenő')],
        label='Irány'
    )

    # Issue date range filters
    issue_date_from = django_filters.DateFilter(
        field_name='issue_date',
        lookup_expr='gte',
        label='Kiállítás dátuma (tól)'
    )
    issue_date_to = django_filters.DateFilter(
        field_name='issue_date',
        lookup_expr='lte',
        label='Kiállítás dátuma (ig)'
    )

    # Fulfillment date range filters
    fulfillment_date_from = django_filters.DateFilter(
        field_name='fulfillment_date',
        lookup_expr='gte',
        label='Teljesítés dátuma (tól)'
    )
    fulfillment_date_to = django_filters.DateFilter(
        field_name='fulfillment_date',
        lookup_expr='lte',
        label='Teljesítés dátuma (ig)'
    )

    # Payment due date range filters
    payment_due_date_from = django_filters.DateFilter(
        field_name='payment_due_date',
        lookup_expr='gte',
        label='Fizetési határidő (tól)'
    )
    payment_due_date_to = django_filters.DateFilter(
        field_name='payment_due_date',
        lookup_expr='lte',
        label='Fizetési határidő (ig)'
    )

    # Payment status filter (with custom method for legacy support)
    payment_status = django_filters.CharFilter(
        method='filter_payment_status',
        label='Fizetési státusz'
    )

    # Amount range filters
    amount_from = django_filters.NumberFilter(
        field_name='invoice_gross_amount',
        lookup_expr='gte',
        label='Összeg (tól)'
    )
    amount_to = django_filters.NumberFilter(
        field_name='invoice_gross_amount',
        lookup_expr='lte',
        label='Összeg (ig)'
    )

    # Currency filter
    currency = django_filters.CharFilter(
        field_name='currency_code',
        lookup_expr='iexact',
        label='Pénznem'
    )

    # Invoice operation filter
    operation = django_filters.ChoiceFilter(
        field_name='invoice_operation',
        choices=[
            ('CREATE', 'Létrehozás'),
            ('STORNO', 'Sztornó'),
            ('MODIFY', 'Módosítás')
        ],
        label='Művelet típusa'
    )

    # Payment method filter
    payment_method = django_filters.CharFilter(
        field_name='payment_method',
        lookup_expr='iexact',
        label='Fizetési mód'
    )

    # Multi-field search filter
    search = django_filters.CharFilter(
        method='filter_search',
        label='Keresés'
    )

    # Hide STORNO invoices filter
    hide_storno_invoices = django_filters.BooleanFilter(
        method='filter_hide_storno',
        label='Sztornó számlák elrejtése',
        initial=True
    )

    def filter_payment_status(self, queryset, name, value):
        """
        Filter by payment status with support for both new and legacy formats.

        New format: PAID, UNPAID, PREPARED
        Legacy format: paid, unpaid, overdue
        """
        if not value:
            return queryset

        value_upper = value.upper()

        # New format
        if value_upper in ['PAID', 'UNPAID', 'PREPARED']:
            return queryset.filter(payment_status=value_upper)

        # Legacy format support
        if value.lower() == 'paid':
            return queryset.filter(payment_date__isnull=False)
        elif value.lower() == 'unpaid':
            return queryset.filter(payment_date__isnull=True)
        elif value.lower() == 'overdue':
            return queryset.filter(
                payment_date__isnull=True,
                payment_due_date__lt=date.today()
            )

        return queryset

    def filter_search(self, queryset, name, value):
        """
        Search across multiple invoice fields:
        - NAV invoice number
        - Supplier/customer names
        - Supplier/customer tax numbers
        - Original invoice number
        """
        if not value:
            return queryset

        return queryset.filter(
            models.Q(nav_invoice_number__icontains=value) |
            models.Q(supplier_name__icontains=value) |
            models.Q(customer_name__icontains=value) |
            models.Q(supplier_tax_number__icontains=value) |
            models.Q(customer_tax_number__icontains=value) |
            models.Q(original_invoice_number__icontains=value)
        )

    def filter_hide_storno(self, queryset, name, value):
        """
        Hide STORNO/MODIFY invoices and invoices that have been storno'd.

        This excludes:
        1. Invoices with operation type STORNO or MODIFY
        2. Invoices that have been cancelled by a STORNO invoice (using ForeignKey relationship)
        """
        if value:
            return queryset.exclude(
                models.Q(invoice_operation__in=['STORNO', 'MODIFY']) |
                models.Q(storno_invoices__isnull=False)
            )
        return queryset

    class Meta:
        model = Invoice
        fields = [
            'direction', 'issue_date_from', 'issue_date_to',
            'fulfillment_date_from', 'fulfillment_date_to',
            'payment_due_date_from', 'payment_due_date_to',
            'payment_status', 'amount_from', 'amount_to',
            'currency', 'operation', 'payment_method',
            'search', 'hide_storno_invoices'
        ]
