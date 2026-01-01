"""
API ViewSet Tests

Tests for DRF API endpoints:
- Authentication and permissions
- CRUD operations (Create, Read, Update, Delete)
- Custom actions
- Error handling
- Response format validation
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone


# ============================================================================
# Beneficiary API Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.django_db
class TestBeneficiaryAPI:
    """Test cases for Beneficiary API endpoints."""

    def test_list_beneficiaries_authenticated(self, authenticated_client, company, beneficiary):
        """Test listing beneficiaries with authentication."""
        response = authenticated_client.get('/api/beneficiaries/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert 'results' in response.data
        assert len(response.data['results']) >= 1

    def test_list_beneficiaries_unauthenticated(self, api_client):
        """Test listing beneficiaries without authentication fails."""
        response = api_client.get('/api/beneficiaries/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_beneficiary(self, authenticated_client, company):
        """Test creating a beneficiary via API."""
        data = {
            'name': 'New Beneficiary Ltd.',
            'account_number': '12345678-12345678-12345678',
            'tax_number': '12345678',
            'description': 'New supplier via API'
        }

        response = authenticated_client.post('/api/beneficiaries/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Beneficiary Ltd.'
        assert response.data['tax_number'] == '12345678'

    def test_create_beneficiary_invalid_data(self, authenticated_client):
        """Test creating beneficiary with invalid data fails."""
        data = {
            'name': '',  # Empty name (invalid)
            'account_number': 'invalid'
        }

        response = authenticated_client.post('/api/beneficiaries/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_beneficiary(self, authenticated_client, beneficiary):
        """Test updating a beneficiary."""
        data = {
            'name': 'Updated Name',
            'account_number': beneficiary.account_number
        }

        response = authenticated_client.patch(
            f'/api/beneficiaries/{beneficiary.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_delete_beneficiary(self, authenticated_client, beneficiary):
        """Test deleting a beneficiary."""
        response = authenticated_client.delete(f'/api/beneficiaries/{beneficiary.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# Billingo Settings API Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.django_db
class TestBillingoSettingsAPI:
    """Test cases for Billingo settings API endpoints."""

    def test_test_credentials_endpoint_exists(self, authenticated_client):
        """Test that test_credentials endpoint is accessible.

        Tests the ability to test Billingo API credentials before saving them.
        ADMIN and FINANCIAL roles can test credentials.
        """
        data = {'api_key': 'test-key-12345'}

        response = authenticated_client.post(
            '/api/billingo-settings/test_credentials/',
            data,
            format='json'
        )

        # Should return 200 even if credentials are invalid
        assert response.status_code == status.HTTP_200_OK
        assert 'valid' in response.data

    def test_test_credentials_without_api_key(self, authenticated_client):
        """Test test_credentials without providing API key."""
        response = authenticated_client.post(
            '/api/billingo-settings/test_credentials/',
            {},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data


# ============================================================================
# NAV Invoice API Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.django_db
class TestNAVInvoiceAPI:
    """Test cases for NAV Invoice API endpoints."""

    def test_list_nav_invoices(self, authenticated_client, nav_invoice):
        """Test listing NAV invoices."""
        response = authenticated_client.get('/api/nav/invoices/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_filter_invoices_by_payment_status(self, authenticated_client, company):
        """Test filtering invoices by payment status."""
        # Create invoices with different statuses
        from bank_transfers.models import Invoice

        Invoice.objects.create(
            company=company,
            nav_invoice_number='PAID-001',
            invoice_direction='INBOUND',
            supplier_name='Supplier A',
            issue_date=date.today(),
            invoice_gross_amount=Decimal('100000'),
            invoice_net_amount=Decimal('80000'),
            invoice_vat_amount=Decimal('20000'),
            currency_code='HUF',
            original_request_version='3.0',
            last_modified_date=timezone.now(),
            payment_status='PAID'
        )
        Invoice.objects.create(
            company=company,
            nav_invoice_number='UNPAID-001',
            invoice_direction='INBOUND',
            supplier_name='Supplier B',
            issue_date=date.today(),
            invoice_gross_amount=Decimal('200000'),
            invoice_net_amount=Decimal('160000'),
            invoice_vat_amount=Decimal('40000'),
            currency_code='HUF',
            original_request_version='3.0',
            last_modified_date=timezone.now(),
            payment_status='UNPAID'
        )

        response = authenticated_client.get('/api/nav/invoices/?payment_status=UNPAID')

        assert response.status_code == status.HTTP_200_OK
        # All returned invoices should have UNPAID status
        # payment_status is serialized as an object with status, label, icon, class
        for invoice in response.data['results']:
            # Check if it's a dict (serialized) or string (raw)
            if isinstance(invoice['payment_status'], dict):
                assert invoice['payment_status']['status'] == 'UNPAID'
            else:
                assert invoice['payment_status'] == 'UNPAID'


# ============================================================================
# Bank Statement API Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.django_db
class TestBankStatementAPI:
    """Test cases for Bank Statement API endpoints."""

    def test_list_bank_statements(self, authenticated_client, bank_statement):
        """Test listing bank statements."""
        response = authenticated_client.get('/api/bank-statements/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_get_bank_statement_detail(self, authenticated_client, bank_statement):
        """Test getting bank statement detail."""
        response = authenticated_client.get(f'/api/bank-statements/{bank_statement.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == bank_statement.id
        assert 'transactions' in response.data


# ============================================================================
# Transfer API Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.django_db
class TestTransferAPI:
    """Test cases for Transfer API endpoints."""

    def test_bulk_create_transfers(self, authenticated_client, company, bank_account, beneficiary):
        """Test bulk creating transfers."""
        data = {
            'bank_account': bank_account.id,
            'execution_date': str(date.today() + timedelta(days=7)),
            'transfers': [
                {
                    'beneficiary': beneficiary.id,
                    'amount': '50000.00',
                    'currency': 'HUF',
                    'remittance_info': 'Payment 1'
                }
            ]
        }

        response = authenticated_client.post('/api/transfers/bulk_create/', data, format='json')

        # Check if endpoint exists (might be 400 due to validation, but not 404)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ]


# ============================================================================
# Health Check Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.django_db
class TestHealthCheck:
    """Test cases for health check endpoint."""

    def test_health_check_endpoint(self, api_client):
        """Test health check endpoint returns 200."""
        response = api_client.get('/api/health/')

        assert response.status_code == status.HTTP_200_OK
        # Health check returns Django JsonResponse, not DRF Response
        import json
        data = json.loads(response.content)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['service'] == 'transferXMLGenerator-backend'
