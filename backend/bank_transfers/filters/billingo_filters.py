"""
Billingo Invoice Filtering

This module provides type-safe filtering for BillingoInvoice queryset using django-filter.
Supports advanced operator-based filtering for MUI DataGrid compatibility.
"""

import django_filters
from django.db import models
from ..models import BillingoInvoice


class BillingoInvoiceFilterSet(django_filters.FilterSet):
    """
    Type-safe filtering for BillingoInvoice queryset.

    Supports advanced operator-based filtering compatible with MUI DataGrid:
    - String fields: contains, notContains, equals, notEqual, startsWith, endsWith, isEmpty, isNotEmpty
    - Date fields: is, not, after, onOrAfter, before, onOrBefore, isEmpty, isNotEmpty
    - Numeric fields: =, !=, >, >=, <, <=, isEmpty, isNotEmpty
    - Boolean fields: is

    Example usage:
        GET /api/billingo-invoices/?invoice_number=INV-001&invoice_number_operator=contains
        GET /api/billingo-invoices/?invoice_date=2025-01-01&invoice_date_operator=onOrAfter
        GET /api/billingo-invoices/?gross_total=100000&gross_total_operator=>=
    """

    # String filters with operator support
    invoice_number = django_filters.CharFilter(method='filter_invoice_number')
    invoice_number_operator = django_filters.CharFilter(method='noop')

    partner_name = django_filters.CharFilter(method='filter_partner_name')
    partner_name_operator = django_filters.CharFilter(method='noop')

    partner_tax_number = django_filters.CharFilter(method='filter_partner_tax_number')
    partner_tax_number_operator = django_filters.CharFilter(method='noop')

    type = django_filters.CharFilter(method='filter_type')
    type_operator = django_filters.CharFilter(method='noop')

    payment_status = django_filters.CharFilter(method='filter_payment_status')
    payment_status_operator = django_filters.CharFilter(method='noop')

    # Boolean filter with operator support
    cancelled = django_filters.BooleanFilter(method='filter_cancelled')
    cancelled_operator = django_filters.CharFilter(method='noop')

    # Date filters with operator support
    invoice_date = django_filters.DateFilter(method='filter_invoice_date')
    invoice_date_operator = django_filters.CharFilter(method='noop')

    due_date = django_filters.DateFilter(method='filter_due_date')
    due_date_operator = django_filters.CharFilter(method='noop')

    # Numeric filters with operator support
    gross_total = django_filters.NumberFilter(method='filter_gross_total')
    gross_total_operator = django_filters.CharFilter(method='noop')

    net_total = django_filters.NumberFilter(method='filter_net_total')
    net_total_operator = django_filters.CharFilter(method='noop')

    class Meta:
        model = BillingoInvoice
        fields = []  # All filtering is handled by custom methods

    def noop(self, queryset, name, value):
        """No-op filter for operator parameters"""
        return queryset

    def filter_invoice_number(self, queryset, name, value):
        """Filter invoice number with operator support"""
        operator = self.data.get('invoice_number_operator', 'contains')
        return self._apply_string_filter(queryset, 'invoice_number', value, operator)

    def filter_partner_name(self, queryset, name, value):
        """Filter partner name with operator support"""
        operator = self.data.get('partner_name_operator', 'contains')
        return self._apply_string_filter(queryset, 'partner_name', value, operator)

    def filter_partner_tax_number(self, queryset, name, value):
        """Filter partner tax number with operator support"""
        operator = self.data.get('partner_tax_number_operator', 'contains')
        return self._apply_string_filter(queryset, 'partner_tax_number', value, operator)

    def filter_type(self, queryset, name, value):
        """Filter invoice type with operator support"""
        operator = self.data.get('type_operator', 'contains')
        return self._apply_string_filter(queryset, 'type', value, operator)

    def filter_payment_status(self, queryset, name, value):
        """Filter payment status with operator support"""
        operator = self.data.get('payment_status_operator', 'equals')
        return self._apply_string_filter(queryset, 'payment_status', value, operator)

    def filter_cancelled(self, queryset, name, value):
        """Filter cancelled status with operator support"""
        operator = self.data.get('cancelled_operator', 'is')
        return self._apply_boolean_filter(queryset, 'cancelled', value, operator)

    def filter_invoice_date(self, queryset, name, value):
        """Filter invoice date with operator support"""
        operator = self.data.get('invoice_date_operator', 'is')
        return self._apply_date_filter(queryset, 'invoice_date', value, operator)

    def filter_due_date(self, queryset, name, value):
        """Filter due date with operator support"""
        operator = self.data.get('due_date_operator', 'is')
        return self._apply_date_filter(queryset, 'due_date', value, operator)

    def filter_gross_total(self, queryset, name, value):
        """Filter gross total with operator support"""
        operator = self.data.get('gross_total_operator', '=')
        return self._apply_numeric_filter(queryset, 'gross_total', value, operator)

    def filter_net_total(self, queryset, name, value):
        """Filter net total with operator support"""
        operator = self.data.get('net_total_operator', '=')
        return self._apply_numeric_filter(queryset, 'net_total', value, operator)

    # Filter helper methods
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
            bool_value = value if isinstance(value, bool) else (value.lower() == 'true' if isinstance(value, str) else bool(value))
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
        if value is not None:
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
