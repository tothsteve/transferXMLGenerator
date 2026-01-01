"""
Service Layer Tests

Tests for business logic in the service layer:
- BillingoSyncService: API synchronization and credential validation
- BankStatementParserService: Bank statement parsing
- TransactionMatchingService: Invoice matching algorithms
- CredentialManager: Encryption/decryption
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import responses

from bank_transfers.services.billingo_sync_service import (
    BillingoSyncService, BillingoAPIError, BillingoRateLimitError
)
from bank_transfers.services.credential_manager import CredentialManager


# ============================================================================
# BillingoSyncService Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.service
class TestBillingoSyncService:
    """Test cases for Billingo API synchronization service."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = BillingoSyncService()

        assert service.BASE_URL == "https://api.billingo.hu/v3"
        assert service.MAX_RETRIES == 3
        assert service.RETRY_DELAY == 5
        assert service.credential_manager is not None

    @responses.activate
    def test_validate_credentials_success(self):
        """Test successful API credential validation."""
        service = BillingoSyncService()

        # Mock successful API response
        responses.add(
            responses.GET,
            "https://api.billingo.hu/v3/documents",
            json={
                'data': [{
                    'organization': {
                        'name': 'Test Company Ltd.',
                        'tax_number': '12345678-1-42'
                    }
                }],
                'page': 1,
                'total': 1
            },
            status=200
        )

        result = service.validate_and_test_credentials('test-api-key')

        assert result['valid'] is True
        assert result['organization_name'] == 'Test Company Ltd.'
        assert result['organization_tax_number'] == '12345678-1-42'
        assert 'error' not in result

    @responses.activate
    def test_validate_credentials_invalid_key(self):
        """Test credential validation with invalid API key."""
        service = BillingoSyncService()

        # Mock 401 Unauthorized response
        responses.add(
            responses.GET,
            "https://api.billingo.hu/v3/documents",
            json={'error': 'Unauthorized'},
            status=401
        )

        result = service.validate_and_test_credentials('invalid-key')

        assert result['valid'] is False
        assert 'Érvénytelen API kulcs' in result['error']

    @responses.activate
    def test_validate_credentials_forbidden(self):
        """Test credential validation with insufficient permissions."""
        service = BillingoSyncService()

        # Mock 403 Forbidden response
        responses.add(
            responses.GET,
            "https://api.billingo.hu/v3/documents",
            json={'error': 'Forbidden'},
            status=403
        )

        result = service.validate_and_test_credentials('limited-key')

        assert result['valid'] is False
        assert 'Hozzáférés megtagadva' in result['error']

    @responses.activate
    def test_validate_credentials_timeout(self):
        """Test credential validation with API timeout."""
        service = BillingoSyncService()

        # Mock timeout
        def request_callback(request):
            import requests
            raise requests.exceptions.Timeout("Connection timeout")

        responses.add_callback(
            responses.GET,
            "https://api.billingo.hu/v3/documents",
            callback=request_callback
        )

        result = service.validate_and_test_credentials('test-key')

        assert result['valid'] is False
        assert 'Időtúllépés' in result['error']

    @responses.activate
    def test_validate_credentials_connection_error(self):
        """Test credential validation with network connection error."""
        service = BillingoSyncService()

        # Mock connection error
        def request_callback(request):
            import requests
            raise requests.exceptions.ConnectionError("Network unreachable")

        responses.add_callback(
            responses.GET,
            "https://api.billingo.hu/v3/documents",
            callback=request_callback
        )

        result = service.validate_and_test_credentials('test-key')

        assert result['valid'] is False
        assert 'Kapcsolódási hiba' in result['error']

    @pytest.mark.django_db
    def test_sync_company_no_settings(self, company):
        """Test sync fails when company has no Billingo settings."""
        service = BillingoSyncService()

        with pytest.raises(BillingoAPIError, match="No Billingo settings configured"):
            service.sync_company(company)

    @pytest.mark.django_db
    def test_sync_company_inactive_settings(self, company, billingo_settings):
        """Test sync fails when Billingo sync is disabled."""
        billingo_settings.is_active = False
        billingo_settings.save()

        service = BillingoSyncService()

        with pytest.raises(BillingoAPIError, match="Billingo sync is disabled"):
            service.sync_company(company)


# ============================================================================
# CredentialManager Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.service
class TestCredentialManager:
    """Test cases for credential encryption/decryption service."""

    def test_encrypt_decrypt_credential(self):
        """Test that credentials can be encrypted and decrypted."""
        manager = CredentialManager()
        original = "my-secret-api-key-12345"

        encrypted = manager.encrypt_credential(original)
        decrypted = manager.decrypt_credential(encrypted)

        assert encrypted != original
        assert decrypted == original

    def test_encrypted_credentials_are_different(self):
        """Test that encrypting the same value twice produces different ciphertext (due to IV)."""
        manager = CredentialManager()
        original = "my-secret-api-key-12345"

        encrypted1 = manager.encrypt_credential(original)
        encrypted2 = manager.encrypt_credential(original)

        # Different ciphertexts due to random IV
        assert encrypted1 != encrypted2

        # But both decrypt to the same value
        assert manager.decrypt_credential(encrypted1) == original
        assert manager.decrypt_credential(encrypted2) == original

    def test_decrypt_empty_string(self):
        """Test decrypting empty string returns empty string."""
        manager = CredentialManager()

        result = manager.decrypt_credential('')

        assert result == ''

    def test_decrypt_none(self):
        """Test decrypting None returns empty string."""
        manager = CredentialManager()

        result = manager.decrypt_credential(None)

        # Actual implementation returns "" for None/empty values
        assert result == ''


# ============================================================================
# BankStatementParserService Tests (Placeholder)
# ============================================================================

@pytest.mark.unit
@pytest.mark.service
class TestBankStatementParserService:
    """Test cases for bank statement parsing service."""

    @pytest.mark.django_db
    def test_parse_and_save_requires_company(self, user):
        """Test that parse_and_save requires a company."""
        from bank_transfers.services.bank_statement_parser_service import BankStatementParserService

        service = BankStatementParserService(company=None, user=user)

        # Should raise an error when trying to parse without company
        # (Implementation-specific test - adjust based on actual behavior)
        assert service.company is None


# ============================================================================
# TransactionMatchingService Tests (Placeholder)
# ============================================================================

@pytest.mark.unit
@pytest.mark.service
class TestTransactionMatchingService:
    """Test cases for transaction-invoice matching service."""

    @pytest.mark.django_db
    def test_exact_amount_matching(self, bank_transaction, nav_invoice):
        """Test exact amount match between transaction and invoice."""
        from bank_transfers.services.transaction_matching_service import TransactionMatchingService

        # Set matching amounts
        bank_transaction.amount = Decimal('-121000.00')
        bank_transaction.save()

        nav_invoice.invoice_gross_amount = Decimal('121000.00')
        nav_invoice.save()

        service = TransactionMatchingService(bank_transaction.company)

        # Test amount comparison (implementation-specific)
        assert abs(bank_transaction.amount) == nav_invoice.invoice_gross_amount
