"""
Beneficiary FilterSet - Declarative filtering for beneficiaries

This FilterSet replaces manual filtering logic in BeneficiaryViewSet
with a clean, testable, declarative approach.
"""

import django_filters
from django.db import models
from ..models import Beneficiary


class BeneficiaryFilterSet(django_filters.FilterSet):
    """
    Comprehensive filtering for Beneficiary queryset.

    Supported filters:
    - is_active: Boolean filter for active/inactive beneficiaries
    - is_frequent: Boolean filter for frequent beneficiaries
    - search: Multi-field search (name, account number, VAT number, description)
    - vat_number: Filter by exact VAT number (tax number)
    - has_vat_number: Boolean - beneficiaries with/without VAT number
    - has_account_number: Boolean - beneficiaries with/without account number
    """

    # Active status filter
    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label='Aktív kedvezményezett'
    )

    # Frequent beneficiary filter
    is_frequent = django_filters.BooleanFilter(
        field_name='is_frequent',
        label='Gyakori kedvezményezett'
    )

    # Multi-field search filter
    search = django_filters.CharFilter(
        method='filter_search',
        label='Keresés'
    )

    # VAT number exact filter
    vat_number = django_filters.CharFilter(
        field_name='vat_number',
        lookup_expr='exact',
        label='Adószám'
    )

    # Has VAT number filter
    has_vat_number = django_filters.BooleanFilter(
        method='filter_has_vat_number',
        label='Adószámmal rendelkezik'
    )

    # Has account number filter
    has_account_number = django_filters.BooleanFilter(
        method='filter_has_account_number',
        label='Számlaszámmal rendelkezik'
    )

    def filter_search(self, queryset, name, value):
        """
        Search across multiple beneficiary fields:
        - Name
        - Account number
        - VAT number
        - Description
        - Remittance information
        """
        if not value:
            return queryset

        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(account_number__icontains=value) |
            models.Q(vat_number__icontains=value) |
            models.Q(description__icontains=value) |
            models.Q(remittance_information__icontains=value)
        )

    def filter_has_vat_number(self, queryset, name, value):
        """Filter beneficiaries with or without VAT number"""
        if value is True:
            return queryset.exclude(vat_number__isnull=True).exclude(vat_number='')
        elif value is False:
            return queryset.filter(models.Q(vat_number__isnull=True) | models.Q(vat_number=''))
        return queryset

    def filter_has_account_number(self, queryset, name, value):
        """Filter beneficiaries with or without account number"""
        if value is True:
            return queryset.exclude(account_number__isnull=True).exclude(account_number='')
        elif value is False:
            return queryset.filter(models.Q(account_number__isnull=True) | models.Q(account_number=''))
        return queryset

    class Meta:
        model = Beneficiary
        fields = ['is_active', 'is_frequent', 'search', 'vat_number', 'has_vat_number', 'has_account_number']
