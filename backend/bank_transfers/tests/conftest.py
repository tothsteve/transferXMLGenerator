"""
Pytest Configuration and Shared Fixtures

This module provides shared test fixtures for the bank_transfers test suite.
Fixtures are available to all tests automatically via pytest's fixture discovery.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from bank_transfers.models import (
    Company, CompanyUser, BankAccount, Beneficiary, TransferTemplate,
    Transfer, TransferBatch, Invoice, TrustedPartner, ExchangeRate,
    BankStatement, BankTransaction, CompanyBillingoSettings
)

User = get_user_model()


# ============================================================================
# User and Authentication Fixtures
# ============================================================================

@pytest.fixture
def user(db):
    """Create a regular test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin test user."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )


# ============================================================================
# Company and Membership Fixtures
# ============================================================================

@pytest.fixture
def company(db):
    """Create a test company."""
    return Company.objects.create(
        name='Test Company Ltd.',
        tax_id='12345678-1-42'
    )


@pytest.fixture
def company_user(db, company, user):
    """Create a company user membership with ADMIN role."""
    return CompanyUser.objects.create(
        company=company,
        user=user,
        role='ADMIN',
        is_active=True
    )


@pytest.fixture
def enable_all_features(db, company):
    """Enable all features for testing."""
    from bank_transfers.models import FeatureTemplate, CompanyFeature

    # Get or create all feature templates
    feature_codes = [
        'NAV_SYNC',
        'BILLINGO_SYNC',
        'BANK_STATEMENT_IMPORT',
        'BENEFICIARY_MANAGEMENT',
        'TRANSFER_MANAGEMENT',
        'BATCH_MANAGEMENT',
    ]

    for feature_code in feature_codes:
        # Create feature template if doesn't exist
        feature_template, _ = FeatureTemplate.objects.get_or_create(
            feature_code=feature_code,
            defaults={
                'feature_name': feature_code.replace('_', ' ').title(),
                'description': f'Test feature: {feature_code}',
                'is_system_critical': False,
            }
        )

        # Enable feature for company
        CompanyFeature.objects.get_or_create(
            company=company,
            feature_template=feature_template,
            defaults={'is_enabled': True}
        )


@pytest.fixture
def financial_user(db, company, user):
    """Create a company user with FINANCIAL role."""
    financial = User.objects.create_user(
        username='financial',
        email='financial@example.com',
        password='financialpass123'
    )
    return CompanyUser.objects.create(
        company=company,
        user=financial,
        role='FINANCIAL',
        is_active=True
    )


# ============================================================================
# Bank Account Fixtures
# ============================================================================

@pytest.fixture
def bank_account(db, company):
    """Create a test bank account."""
    return BankAccount.objects.create(
        company=company,
        name='Test Bank Account',
        account_number='12345678-90123456-12345678',
        bank_name='Test Bank',
        is_default=True
    )


# ============================================================================
# Beneficiary Fixtures
# ============================================================================

@pytest.fixture
def beneficiary(db, company):
    """Create a test beneficiary."""
    return Beneficiary.objects.create(
        company=company,
        name='Test Beneficiary Ltd.',
        account_number='98765432-10987654-32109876',
        tax_number='87654321',  # First 8 digits of tax number
        description='Test supplier for unit tests'
    )


@pytest.fixture
def multiple_beneficiaries(db, company):
    """Create multiple beneficiaries for bulk testing."""
    beneficiaries = []
    for i in range(5):
        beneficiaries.append(
            Beneficiary.objects.create(
                company=company,
                name=f'Beneficiary {i+1}',
                account_number=f'1234567{i}-1234567{i}-1234567{i}',
                tax_number=f'1234567{i}',
                description=f'Test beneficiary #{i+1}'
            )
        )
    return beneficiaries


# ============================================================================
# Transfer and Template Fixtures
# ============================================================================

@pytest.fixture
def transfer_template(db, company):
    """Create a transfer template."""
    return TransferTemplate.objects.create(
        company=company,
        name='Monthly Payroll',
        description='Standard monthly payroll template',
        is_active=True
    )


@pytest.fixture
def transfer_batch(db, company, bank_account):
    """Create a transfer batch."""
    return TransferBatch.objects.create(
        company=company,
        batch_name='Test Batch',
        bank_account=bank_account,
        execution_date=date.today() + timedelta(days=7),
        status='PENDING'
    )


@pytest.fixture
def transfer(db, bank_account, beneficiary):
    """Create a single transfer."""
    return Transfer.objects.create(
        originator_account=bank_account,
        beneficiary=beneficiary,
        amount=Decimal('50000.00'),
        currency='HUF',
        execution_date=date.today() + timedelta(days=7),
        remittance_info='Test payment',
        is_processed=False
    )


# ============================================================================
# NAV Invoice Fixtures
# ============================================================================

@pytest.fixture
def nav_invoice(db, company):
    """Create a NAV invoice."""
    return Invoice.objects.create(
        company=company,
        nav_invoice_number='TESZT-2025-001',
        invoice_direction='INBOUND',
        supplier_name='Test Supplier Ltd.',
        supplier_tax_number='12345678-1-42',
        customer_name='Test Company Ltd.',
        customer_tax_number='87654321-2-42',
        issue_date=date.today(),
        fulfillment_date=date.today(),
        payment_due_date=date.today() + timedelta(days=30),
        invoice_gross_amount=Decimal('121000.00'),
        invoice_vat_amount=Decimal('21000.00'),
        invoice_net_amount=Decimal('100000.00'),
        currency_code='HUF',
        original_request_version='3.0',
        last_modified_date=timezone.now(),
        payment_status='UNPAID',
        invoice_category='NORMAL',
        invoice_operation='CREATE'
    )


# ============================================================================
# Billingo Fixtures
# ============================================================================

@pytest.fixture
def billingo_settings(db, company):
    """Create Billingo settings (without API key for security)."""
    from bank_transfers.services.credential_manager import CredentialManager

    credential_manager = CredentialManager()
    encrypted_key = credential_manager.encrypt_credential('test-api-key-12345')

    return CompanyBillingoSettings.objects.create(
        company=company,
        api_key=encrypted_key,
        is_active=True
    )


# ============================================================================
# Bank Statement Fixtures
# ============================================================================

@pytest.fixture
def bank_statement(db, company, user):
    """Create a bank statement."""
    return BankStatement.objects.create(
        company=company,
        bank_code='GRANIT',
        bank_name='GRÁNIT Bank',
        bank_bic='GRNTHUHB',
        account_number='12345678-90123456',
        account_iban='HU42123456789012345612345678',
        statement_period_from=date(2025, 1, 1),
        statement_period_to=date(2025, 1, 31),
        statement_number='2025/01',
        opening_balance=Decimal('1000000.00'),
        closing_balance=Decimal('1500000.00'),
        file_name='statement_2025_01.pdf',
        file_size=123456,
        file_hash='abc123def456',
        uploaded_by=user,
        status='PARSED',
        total_transactions=10,
        credit_count=5,
        debit_count=5,
        total_credits=Decimal('600000.00'),
        total_debits=Decimal('100000.00'),
        matched_count=0
    )


@pytest.fixture
def bank_transaction(db, bank_statement):
    """Create a bank transaction."""
    return BankTransaction.objects.create(
        company=bank_statement.company,
        bank_statement=bank_statement,
        transaction_type='TRANSFER',
        booking_date=date(2025, 1, 15),
        value_date=date(2025, 1, 15),
        amount=Decimal('-50000.00'),
        currency='HUF',
        description='Test transfer payment',
        payer_name='Test Company Ltd.',
        beneficiary_name='Test Supplier Ltd.',
        beneficiary_account_number='98765432-10987654'
    )


# ============================================================================
# Exchange Rate Fixtures
# ============================================================================

@pytest.fixture
def exchange_rate_usd(db):
    """Create a USD exchange rate."""
    return ExchangeRate.objects.create(
        currency='USD',
        unit=1,
        rate=Decimal('360.50'),
        rate_date=date.today(),
        source='MNB'
    )


@pytest.fixture
def exchange_rate_eur(db):
    """Create a EUR exchange rate."""
    return ExchangeRate.objects.create(
        currency='EUR',
        unit=1,
        rate=Decimal('395.25'),
        rate_date=date.today(),
        source='MNB'
    )


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def api_client():
    """Create a DRF API test client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user, company, company_user, enable_all_features):
    """Create an authenticated API client with company context and all features enabled."""
    from rest_framework_simplejwt.tokens import RefreshToken

    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    # Set authentication header
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    # Set company header
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {access_token}',
        HTTP_X_COMPANY_ID=str(company.id)
    )

    return api_client


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def mock_billingo_api_response():
    """Mock Billingo API response data."""
    return {
        'data': [
            {
                'id': 123456,
                'invoice_number': 'TEST-2025-001',
                'type': 'invoice',
                'cancelled': False,
                'payment_status': 'paid',
                'payment_method': 'bank_transfer',
                'gross_total': 121000,
                'total': 100000,
                'currency': 'HUF',
                'invoice_date': '2025-01-15',
                'due_date': '2025-02-14',
                'paid_date': '2025-01-20',
                'organization': {
                    'name': 'Test Company Ltd.',
                    'tax_number': '12345678-1-42',
                    'bank_account': {
                        'account_number': '12345678-90123456',
                        'iban': 'HU42123456789012345612345678',
                        'swift': 'TESTHUHU'
                    }
                },
                'partner': {
                    'id': 789,
                    'name': 'Test Customer Ltd.',
                    'tax_number': '87654321-2-42'
                },
                'items': [
                    {
                        'product_id': 1,
                        'name': 'Consulting services',
                        'quantity': 10,
                        'unit': 'hour',
                        'net_unit_price': 10000,
                        'net_amount': 100000,
                        'gross_amount': 121000,
                        'vat': '27%',
                        'entitlement': 'AAM'
                    }
                ]
            }
        ],
        'page': 1,
        'per_page': 100,
        'total': 1,
        'last_page': 1
    }


@pytest.fixture
def mock_mnb_exchange_rate_response():
    """Mock MNB exchange rate API response."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<MNBCurrentExchangeRates>
    <Day date="2025-01-15">
        <Rate curr="USD" unit="1">360.50</Rate>
        <Rate curr="EUR" unit="1">395.25</Rate>
        <Rate curr="GBP" unit="1">450.75</Rate>
    </Day>
</MNBCurrentExchangeRates>
"""
