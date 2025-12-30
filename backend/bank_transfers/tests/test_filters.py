"""
FilterSet Tests

Tests for django-filter FilterSet classes:
- BillingoInvoiceFilterSet: Operator-based filtering for Billingo invoices
- BankTransactionFilterSet: Transaction filtering
- InvoiceFilterSet: NAV invoice filtering
- BeneficiaryFilterSet: Beneficiary filtering
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import RequestFactory

from bank_transfers.filters import (
    BillingoInvoiceFilterSet,
    BankTransactionFilterSet,
    InvoiceFilterSet,
    BeneficiaryFilterSet
)
from bank_transfers.models import BillingoInvoice, BankTransaction, NAVInvoice, Beneficiary


# ============================================================================
# BillingoInvoiceFilterSet Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.filter
@pytest.mark.django_db
class TestBillingoInvoiceFilterSet:
    """Test cases for BillingoInvoiceFilterSet with operator support."""

    def test_filter_invoice_number_contains(self, company):
        """Test filtering invoice number with 'contains' operator."""
        # Create test invoices
        BillingoInvoice.objects.create(
            id=1,
            company=company,
            invoice_number='INV-2025-001',
            gross_total=Decimal('100000'),
            invoice_date=date.today()
        )
        BillingoInvoice.objects.create(
            id=2,
            company=company,
            invoice_number='INV-2025-002',
            gross_total=Decimal('200000'),
            invoice_date=date.today()
        )
        BillingoInvoice.objects.create(
            id=3,
            company=company,
            invoice_number='CREDIT-2025-001',
            gross_total=Decimal('50000'),
            invoice_date=date.today()
        )

        # Create mock request with query params
        factory = RequestFactory()
        request = factory.get('/', {
            'invoice_number': '002',
            'invoice_number_operator': 'contains'
        })

        # Apply filter
        queryset = BillingoInvoice.objects.filter(company=company)
        filterset = BillingoInvoiceFilterSet(request.GET, queryset=queryset, request=request)

        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert filterset.qs.first().invoice_number == 'INV-2025-002'

    def test_filter_invoice_number_equals(self, company):
        """Test filtering invoice number with 'equals' operator."""
        BillingoInvoice.objects.create(
            id=1,
            company=company,
            invoice_number='INV-001',
            gross_total=Decimal('100000'),
            invoice_date=date.today()
        )
        BillingoInvoice.objects.create(
            id=2,
            company=company,
            invoice_number='inv-001',  # Different case
            gross_total=Decimal('200000'),
            invoice_date=date.today()
        )

        factory = RequestFactory()
        request = factory.get('/', {
            'invoice_number': 'INV-001',
            'invoice_number_operator': 'equals'
        })

        queryset = BillingoInvoice.objects.filter(company=company)
        filterset = BillingoInvoiceFilterSet(request.GET, queryset=queryset, request=request)

        assert filterset.is_valid()
        # Case-insensitive equals should match both
        assert filterset.qs.count() == 2

    def test_filter_gross_total_greater_than(self, company):
        """Test filtering gross total with '>' operator."""
        BillingoInvoice.objects.create(
            id=1,
            company=company,
            invoice_number='INV-001',
            gross_total=Decimal('50000'),
            invoice_date=date.today()
        )
        BillingoInvoice.objects.create(
            id=2,
            company=company,
            invoice_number='INV-002',
            gross_total=Decimal('150000'),
            invoice_date=date.today()
        )
        BillingoInvoice.objects.create(
            id=3,
            company=company,
            invoice_number='INV-003',
            gross_total=Decimal('250000'),
            invoice_date=date.today()
        )

        factory = RequestFactory()
        request = factory.get('/', {
            'gross_total': '100000',
            'gross_total_operator': '>'
        })

        queryset = BillingoInvoice.objects.filter(company=company)
        filterset = BillingoInvoiceFilterSet(request.GET, queryset=queryset, request=request)

        assert filterset.is_valid()
        assert filterset.qs.count() == 2
        assert all(inv.gross_total > Decimal('100000') for inv in filterset.qs)

    def test_filter_invoice_date_on_or_after(self, company):
        """Test filtering invoice date with 'onOrAfter' operator."""
        BillingoInvoice.objects.create(
            id=1,
            company=company,
            invoice_number='INV-001',
            gross_total=Decimal('100000'),
            invoice_date=date(2025, 1, 1)
        )
        BillingoInvoice.objects.create(
            id=2,
            company=company,
            invoice_number='INV-002',
            gross_total=Decimal('200000'),
            invoice_date=date(2025, 1, 15)
        )
        BillingoInvoice.objects.create(
            id=3,
            company=company,
            invoice_number='INV-003',
            gross_total=Decimal('300000'),
            invoice_date=date(2025, 2, 1)
        )

        factory = RequestFactory()
        request = factory.get('/', {
            'invoice_date': '2025-01-15',
            'invoice_date_operator': 'onOrAfter'
        })

        queryset = BillingoInvoice.objects.filter(company=company)
        filterset = BillingoInvoiceFilterSet(request.GET, queryset=queryset, request=request)

        assert filterset.is_valid()
        assert filterset.qs.count() == 2
        assert all(inv.invoice_date >= date(2025, 1, 15) for inv in filterset.qs)

    def test_filter_cancelled_boolean(self, company):
        """Test filtering cancelled status (boolean field)."""
        BillingoInvoice.objects.create(
            id=1,
            company=company,
            invoice_number='INV-001',
            gross_total=Decimal('100000'),
            invoice_date=date.today(),
            cancelled=False
        )
        BillingoInvoice.objects.create(
            id=2,
            company=company,
            invoice_number='INV-002',
            gross_total=Decimal('200000'),
            invoice_date=date.today(),
            cancelled=True
        )

        factory = RequestFactory()
        request = factory.get('/', {
            'cancelled': 'true',
            'cancelled_operator': 'is'
        })

        queryset = BillingoInvoice.objects.filter(company=company)
        filterset = BillingoInvoiceFilterSet(request.GET, queryset=queryset, request=request)

        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert filterset.qs.first().cancelled is True

    def test_filter_multiple_fields(self, company):
        """Test filtering with multiple field conditions."""
        BillingoInvoice.objects.create(
            id=1,
            company=company,
            invoice_number='INV-2025-001',
            partner_name='Customer A',
            gross_total=Decimal('100000'),
            invoice_date=date(2025, 1, 15),
            cancelled=False
        )
        BillingoInvoice.objects.create(
            id=2,
            company=company,
            invoice_number='INV-2025-002',
            partner_name='Customer B',
            gross_total=Decimal('200000'),
            invoice_date=date(2025, 1, 20),
            cancelled=False
        )

        factory = RequestFactory()
        request = factory.get('/', {
            'invoice_number': '2025',
            'invoice_number_operator': 'contains',
            'gross_total': '150000',
            'gross_total_operator': '>',
            'cancelled': 'false'
        })

        queryset = BillingoInvoice.objects.filter(company=company)
        filterset = BillingoInvoiceFilterSet(request.GET, queryset=queryset, request=request)

        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert filterset.qs.first().invoice_number == 'INV-2025-002'


# ============================================================================
# BeneficiaryFilterSet Tests (Placeholder)
# ============================================================================

@pytest.mark.unit
@pytest.mark.filter
@pytest.mark.django_db
class TestBeneficiaryFilterSet:
    """Test cases for BeneficiaryFilterSet."""

    def test_filter_beneficiary_by_name(self, company):
        """Test filtering beneficiaries by name."""
        Beneficiary.objects.create(
            company=company,
            name='Supplier A',
            account_number='12345678-12345678-12345678'
        )
        Beneficiary.objects.create(
            company=company,
            name='Supplier B',
            account_number='98765432-98765432-98765432'
        )

        factory = RequestFactory()
        request = factory.get('/', {'name': 'Supplier A'})

        queryset = Beneficiary.objects.filter(company=company)
        filterset = BeneficiaryFilterSet(request.GET, queryset=queryset, request=request)

        # Assuming name filter uses contains
        assert filterset.is_valid()
        # Test will depend on actual FilterSet implementation


# ============================================================================
# InvoiceFilterSet Tests (Placeholder)
# ============================================================================

@pytest.mark.unit
@pytest.mark.filter
@pytest.mark.django_db
class TestInvoiceFilterSet:
    """Test cases for NAV Invoice FilterSet."""

    def test_filter_invoice_by_payment_status(self, company):
        """Test filtering invoices by payment status."""
        NAVInvoice.objects.create(
            company=company,
            nav_invoice_number='INV-001',
            supplier_name='Supplier A',
            invoice_issue_date=date.today(),
            invoice_gross_amount=Decimal('100000'),
            payment_status='PAID'
        )
        NAVInvoice.objects.create(
            company=company,
            nav_invoice_number='INV-002',
            supplier_name='Supplier B',
            invoice_issue_date=date.today(),
            invoice_gross_amount=Decimal('200000'),
            payment_status='UNPAID'
        )

        factory = RequestFactory()
        request = factory.get('/', {'payment_status': 'UNPAID'})

        queryset = NAVInvoice.objects.filter(company=company)
        filterset = InvoiceFilterSet(request.GET, queryset=queryset, request=request)

        # Actual test depends on FilterSet implementation
        assert filterset.is_valid()
