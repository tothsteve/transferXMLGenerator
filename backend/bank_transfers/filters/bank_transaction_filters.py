"""
BankTransaction FilterSet - Declarative filtering for bank transactions

This FilterSet replaces manual filtering logic in BankTransactionViewSet
with a clean, testable, declarative approach.
"""

import django_filters
from ..models import BankTransaction


class BankTransactionFilterSet(django_filters.FilterSet):
    """
    Comprehensive filtering for BankTransaction queryset.

    Supported filters:
    - statement_id: Filter by bank statement
    - transaction_type: Filter by transaction type (AFR_CREDIT, POS_PURCHASE, etc.)
    - matched: Boolean filter - true=matched transactions, false=unmatched
    - Date range: from_date, to_date (booking_date)
    - Amount range: min_amount, max_amount
    """

    # Bank statement filter
    statement_id = django_filters.NumberFilter(
        field_name='bank_statement_id',
        label='Bankszámlakivonat azonosító'
    )

    # Transaction type filter
    transaction_type = django_filters.ChoiceFilter(
        field_name='transaction_type',
        choices=BankTransaction.TRANSACTION_TYPES,
        label='Tranzakció típusa'
    )

    # Matched status filter
    matched = django_filters.BooleanFilter(
        method='filter_matched_status',
        label='Párosított tranzakciók'
    )

    # Booking date range filters
    from_date = django_filters.DateFilter(
        field_name='booking_date',
        lookup_expr='gte',
        label='Könyvelés dátuma (tól)'
    )
    to_date = django_filters.DateFilter(
        field_name='booking_date',
        lookup_expr='lte',
        label='Könyvelés dátuma (ig)'
    )

    # Amount range filters
    min_amount = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='gte',
        label='Összeg (tól)'
    )
    max_amount = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='lte',
        label='Összeg (ig)'
    )

    def filter_matched_status(self, queryset, name, value):
        """
        Filter by matched/unmatched status.

        True: Returns transactions with matched_invoice not null
        False: Returns transactions with matched_invoice null (unmatched)
        """
        if value is True:
            return queryset.filter(matched_invoice__isnull=False)
        elif value is False:
            return queryset.filter(matched_invoice__isnull=True)
        return queryset

    class Meta:
        model = BankTransaction
        fields = [
            'statement_id', 'transaction_type', 'matched',
            'from_date', 'to_date', 'min_amount', 'max_amount'
        ]
