"""
Model Tests

Tests for Django model validation, constraints, and business logic:
- Model field validation
- Custom validators
- Model methods and properties
- Database constraints (unique, foreign keys)
- Model signals
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from bank_transfers.models import (
    Company, Beneficiary, BankAccount, Transfer, TransferBatch,
    NAVInvoice, TrustedPartner, ExchangeRate, BankStatement,
    BankTransaction, CompanyBillingoSettings
)


# ============================================================================
# Company Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.model
@pytest.mark.django_db
class TestCompanyModel:
    """Test cases for Company model."""

    def test_create_company_with_valid_data(self):
        """Test creating a company with all valid fields."""
        company = Company.objects.create(
            name='Test Company Ltd.',
            tax_id='12345678-1-42',
            registration_number='01-09-123456',
            address='1234 Budapest, Test Street 1.',
            is_active=True
        )

        assert company.id is not None
        assert company.name == 'Test Company Ltd.'
        assert company.tax_id == '12345678-1-42'
        assert company.is_active is True

    def test_company_str_method(self):
        """Test Company __str__ method."""
        company = Company.objects.create(
            name='ACME Corporation',
            tax_id='12345678-1-42',
            is_active=True
        )

        assert str(company) == 'ACME Corporation'

    def test_company_tax_id_uniqueness(self):
        """Test that tax_id must be unique."""
        Company.objects.create(
            name='Company A',
            tax_id='12345678-1-42',
            is_active=True
        )

        with pytest.raises(IntegrityError):
            Company.objects.create(
                name='Company B',
                tax_id='12345678-1-42',  # Duplicate
                is_active=True
            )


# ============================================================================
# Beneficiary Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.model
@pytest.mark.django_db
class TestBeneficiaryModel:
    """Test cases for Beneficiary model."""

    def test_create_beneficiary(self, company):
        """Test creating a beneficiary with valid data."""
        beneficiary = Beneficiary.objects.create(
            company=company,
            name='Test Supplier Ltd.',
            account_number='12345678-12345678-12345678',
            vat_number='87654321-2-42',
            default_amount=Decimal('100000.00'),
            is_active=True
        )

        assert beneficiary.id is not None
        assert beneficiary.company == company
        assert beneficiary.name == 'Test Supplier Ltd.'
        assert beneficiary.default_amount == Decimal('100000.00')

    def test_beneficiary_str_method(self, company):
        """Test Beneficiary __str__ method."""
        beneficiary = Beneficiary.objects.create(
            company=company,
            name='Supplier XYZ',
            account_number='12345678-12345678-12345678'
        )

        assert str(beneficiary) == 'Supplier XYZ'

    def test_beneficiary_company_required(self):
        """Test that company is required."""
        with pytest.raises(IntegrityError):
            Beneficiary.objects.create(
                name='No Company Beneficiary',
                account_number='12345678-12345678-12345678'
            )


# ============================================================================
# BankAccount Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.model
@pytest.mark.django_db
class TestBankAccountModel:
    """Test cases for BankAccount model."""

    def test_create_bank_account(self, company):
        """Test creating a bank account."""
        account = BankAccount.objects.create(
            company=company,
            account_number='12345678-90123456-12345678',
            account_iban='HU42123456789012345612345678',
            bank_name='Test Bank',
            bank_bic='TESTHUHU',
            currency='HUF',
            is_default=True
        )

        assert account.id is not None
        assert account.currency == 'HUF'
        assert account.is_default is True

    def test_bank_account_str_method(self, company):
        """Test BankAccount __str__ method."""
        account = BankAccount.objects.create(
            company=company,
            account_number='12345678-90123456',
            bank_name='GRÁNIT Bank'
        )

        assert 'GRÁNIT Bank' in str(account)
        assert '12345678-90123456' in str(account)


# ============================================================================
# NAVInvoice Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.model
@pytest.mark.django_db
class TestNAVInvoiceModel:
    """Test cases for NAV Invoice model."""

    def test_create_nav_invoice(self, company):
        """Test creating a NAV invoice."""
        invoice = NAVInvoice.objects.create(
            company=company,
            nav_invoice_number='TEST-2025-001',
            supplier_name='Supplier Ltd.',
            supplier_tax_number='12345678-1-42',
            customer_name='Customer Ltd.',
            customer_tax_number='87654321-2-42',
            invoice_issue_date=date.today(),
            invoice_delivery_date=date.today(),
            payment_due_date=date.today() + timedelta(days=30),
            invoice_gross_amount=Decimal('121000.00'),
            invoice_vat_amount=Decimal('21000.00'),
            invoice_net_amount=Decimal('100000.00'),
            currency='HUF',
            payment_status='UNPAID',
            invoice_category='NORMAL',
            invoice_operation='CREATE'
        )

        assert invoice.id is not None
        assert invoice.payment_status == 'UNPAID'
        assert invoice.invoice_gross_amount == Decimal('121000.00')

    def test_nav_invoice_payment_status_choices(self, company):
        """Test NAV invoice payment status field."""
        invoice = NAVInvoice.objects.create(
            company=company,
            nav_invoice_number='TEST-2025-002',
            supplier_name='Supplier Ltd.',
            supplier_tax_number='12345678-1-42',
            invoice_issue_date=date.today(),
            invoice_gross_amount=Decimal('100000.00'),
            payment_status='PAID'  # Valid choice
        )

        assert invoice.payment_status == 'PAID'

    def test_nav_invoice_str_method(self, company):
        """Test NAVInvoice __str__ method."""
        invoice = NAVInvoice.objects.create(
            company=company,
            nav_invoice_number='INV-2025-123',
            supplier_name='Supplier XYZ',
            invoice_issue_date=date.today(),
            invoice_gross_amount=Decimal('50000.00')
        )

        assert 'INV-2025-123' in str(invoice)


# ============================================================================
# Transfer Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.model
@pytest.mark.django_db
class TestTransferModel:
    """Test cases for Transfer model."""

    def test_create_transfer(self, company, bank_account, beneficiary):
        """Test creating a transfer."""
        transfer = Transfer.objects.create(
            company=company,
            bank_account=bank_account,
            beneficiary=beneficiary,
            amount=Decimal('50000.00'),
            currency='HUF',
            execution_date=date.today() + timedelta(days=7),
            remittance_info='Test payment',
            is_processed=False
        )

        assert transfer.id is not None
        assert transfer.amount == Decimal('50000.00')
        assert transfer.is_processed is False

    def test_transfer_currency_default(self, company, bank_account, beneficiary):
        """Test transfer currency defaults to HUF."""
        transfer = Transfer.objects.create(
            company=company,
            bank_account=bank_account,
            beneficiary=beneficiary,
            amount=Decimal('10000.00'),
            execution_date=date.today()
        )

        assert transfer.currency == 'HUF'


# ============================================================================
# BankStatement Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.model
@pytest.mark.django_db
class TestBankStatementModel:
    """Test cases for BankStatement model."""

    def test_create_bank_statement(self, company, user):
        """Test creating a bank statement."""
        statement = BankStatement.objects.create(
            company=company,
            bank_code='GRANIT',
            bank_name='GRÁNIT Bank',
            bank_bic='GRNTHUHB',
            account_number='12345678-90123456',
            statement_period_from=date(2025, 1, 1),
            statement_period_to=date(2025, 1, 31),
            opening_balance=Decimal('1000000.00'),
            closing_balance=Decimal('1200000.00'),
            file_name='statement.pdf',
            file_size=123456,
            file_hash='abc123',
            uploaded_by=user,
            status='PARSED'
        )

        assert statement.id is not None
        assert statement.bank_code == 'GRANIT'
        assert statement.status == 'PARSED'

    def test_bank_statement_str_method(self, company, user):
        """Test BankStatement __str__ method."""
        statement = BankStatement.objects.create(
            company=company,
            bank_name='Test Bank',
            account_number='12345678',
            statement_period_from=date(2025, 1, 1),
            statement_period_to=date(2025, 1, 31),
            file_name='test.pdf',
            file_size=100,
            file_hash='hash123',
            uploaded_by=user
        )

        assert 'Test Bank' in str(statement)
        assert '12345678' in str(statement)


# ============================================================================
# ExchangeRate Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.model
@pytest.mark.django_db
class TestExchangeRateModel:
    """Test cases for ExchangeRate model."""

    def test_create_exchange_rate(self):
        """Test creating an exchange rate."""
        rate = ExchangeRate.objects.create(
            currency_code='USD',
            currency_name='US Dollar',
            units=1,
            rate_to_huf=Decimal('360.50'),
            rate_date=date.today(),
            source='MNB'
        )

        assert rate.id is not None
        assert rate.currency_code == 'USD'
        assert rate.rate_to_huf == Decimal('360.50')

    def test_exchange_rate_str_method(self):
        """Test ExchangeRate __str__ method."""
        rate = ExchangeRate.objects.create(
            currency_code='EUR',
            currency_name='Euro',
            units=1,
            rate_to_huf=Decimal('395.25'),
            rate_date=date.today(),
            source='MNB'
        )

        assert 'EUR' in str(rate)
        assert '395.25' in str(rate)

    def test_exchange_rate_uniqueness(self):
        """Test that currency_code + rate_date must be unique."""
        ExchangeRate.objects.create(
            currency_code='USD',
            units=1,
            rate_to_huf=Decimal('360.00'),
            rate_date=date.today(),
            source='MNB'
        )

        with pytest.raises(IntegrityError):
            ExchangeRate.objects.create(
                currency_code='USD',
                units=1,
                rate_to_huf=Decimal('365.00'),  # Different rate
                rate_date=date.today(),  # Same date
                source='MNB'
            )
