# Backend Testing Documentation

**Project**: Transfer XML Generator Backend
**Last Updated**: 2025-01-15
**Coverage Target**: 80% overall, 95%+ for critical paths
**Framework**: pytest + pytest-django + Django TestCase

---

## Table of Contents

1. [Overview](#overview)
2. [Current Test Coverage](#current-test-coverage)
3. [Test Infrastructure](#test-infrastructure)
4. [Completed Tests](#completed-tests)
5. [Missing Tests](#missing-tests)
6. [Test Execution Guide](#test-execution-guide)
7. [Contributing Tests](#contributing-tests)
8. [Appendix](#appendix)

---

## Overview

### Testing Philosophy

- **Test-Driven Development (TDD)**: Write tests before implementation when possible
- **Fast Feedback**: Unit tests should run in milliseconds
- **Isolation**: Tests should be independent and not affect each other
- **Readability**: Test names should clearly describe what they test
- **Coverage Goals**: 80% minimum overall, 95%+ for critical business logic

### Testing Pyramid

```
           /\
          /E2E\          End-to-End Tests (5%)
         /------\        - Full workflow tests
        /        \       - Bank statement upload → matching → export
       /Integration\     Integration Tests (25%)
      /--------------\   - Service + Model + Database
     /                \  - Multi-component workflows
    /    Unit Tests    \ Unit Tests (70%)
   /--------------------\- Models, Services, Validators
  /______________________\- Serializers, Filters, Utils
```

### Test Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Unit** | Test single function/method in isolation | `test_encrypt_decrypt_credential()` |
| **Integration** | Test component interactions | `test_parse_and_save_bank_statement()` |
| **API** | Test REST API endpoints | `test_create_beneficiary_api()` |
| **Service** | Test service layer business logic | `test_billingo_sync_company()` |
| **Model** | Test Django model validation | `test_beneficiary_vat_validation()` |
| **Filter** | Test FilterSet queryset filtering | `test_filter_invoice_by_amount()` |
| **Permission** | Test access control | `test_only_admin_can_sync()` |

---

## Current Test Coverage

### Overall Statistics (as of 2025-01-15)

```
Total Test Files:     5 files
Total Test Cases:     50+ tests
Total Lines of Test:  2,155+ lines
Fixtures Available:   20+ fixtures
Coverage Target:      80% minimum
Current Coverage:     Not measured yet (run pytest --cov)
```

### Coverage by Module

| Module | Status | Tests Written | Coverage Est. | Priority |
|--------|--------|---------------|---------------|----------|
| **Services** | 🟡 Partial | 13 tests | ~30% | HIGH |
| **Models** | 🟢 Good | 20 tests | ~60% | MEDIUM |
| **Filters** | 🟡 Partial | 8 tests | ~40% | MEDIUM |
| **Views (API)** | 🟡 Partial | 12 tests | ~25% | HIGH |
| **Serializers** | 🔴 None | 0 tests | 0% | HIGH |
| **Permissions** | 🔴 None | 0 tests | 0% | CRITICAL |
| **Validators** | 🔴 None | 0 tests | 0% | HIGH |
| **Utils** | 🔴 None | 0 tests | 0% | MEDIUM |
| **Middleware** | 🔴 None | 0 tests | 0% | LOW |

**Legend**:
🟢 Good (60%+) | 🟡 Partial (20-60%) | 🔴 None (<20%)

---

## Test Infrastructure

### Installed Dependencies

```python
# Core Testing Framework
pytest==7.4.3              # Modern Python test framework
pytest-django==4.7.0       # Django integration
pytest-cov==4.1.0          # Code coverage reporting
pytest-mock==3.12.0        # Advanced mocking

# Test Data Generation
factory-boy==3.3.0         # Model factories
faker==22.0.0              # Fake data generation

# Mocking External Services
responses==0.24.1          # HTTP request mocking
freezegun==1.4.0           # Time/datetime mocking
```

### Configuration Files

```
backend/
├── pytest.ini              # Pytest configuration
├── .coveragerc             # Coverage reporting config
└── bank_transfers/tests/
    ├── conftest.py         # Shared fixtures
    └── ...                 # Test files
```

### Available Fixtures

#### Authentication Fixtures
```python
user                    # Regular test user
admin_user              # Superuser/admin
company                 # Test company
company_user            # Company membership (ADMIN role)
financial_user          # Financial role membership
```

#### Business Model Fixtures
```python
bank_account            # Bank account
beneficiary             # Single beneficiary
multiple_beneficiaries  # 5 beneficiaries for bulk testing
transfer_template       # Transfer template
transfer_batch          # Transfer batch
transfer                # Single transfer
nav_invoice             # NAV invoice
trusted_partner         # Trusted partner (TODO)
billingo_settings       # Billingo API settings
bank_statement          # Parsed bank statement
bank_transaction        # Bank transaction
exchange_rate_usd       # USD exchange rate
exchange_rate_eur       # EUR exchange rate
```

#### API Testing Fixtures
```python
api_client              # Unauthenticated DRF client
authenticated_client    # Authenticated client with JWT + company context
```

#### Mock Data Fixtures
```python
mock_billingo_api_response       # Billingo API JSON response
mock_mnb_exchange_rate_response  # MNB XML response
```

---

## Completed Tests

### ✅ test_services.py (13 tests)

#### BillingoSyncService Tests
```python
✅ test_service_initialization()
✅ test_validate_credentials_success()
✅ test_validate_credentials_invalid_key()
✅ test_validate_credentials_forbidden()
✅ test_validate_credentials_timeout()
✅ test_validate_credentials_connection_error()
✅ test_sync_company_no_settings()
✅ test_sync_company_inactive_settings()
```

**Coverage**: ~40% of BillingoSyncService
**Missing**:
- Full sync_company() workflow test
- Invoice fetching pagination tests
- Error recovery and retry logic
- Incremental vs full sync tests
- Invoice processing and database save

#### CredentialManager Tests
```python
✅ test_encrypt_decrypt_credential()
✅ test_encrypted_credentials_are_different()
✅ test_decrypt_empty_string()
✅ test_decrypt_none()
```

**Coverage**: ~90% of CredentialManager
**Missing**:
- Error handling for corrupted encrypted data
- Key rotation scenarios

### ✅ test_models.py (20+ tests)

#### Model Test Classes
```python
✅ TestCompanyModel (4 tests)
   - Create with valid data
   - __str__ method
   - Tax ID uniqueness

✅ TestBeneficiaryModel (3 tests)
   - Create beneficiary
   - __str__ method
   - Company required constraint

✅ TestBankAccountModel (2 tests)
   - Create bank account
   - __str__ method

✅ TestNAVInvoiceModel (3 tests)
   - Create invoice
   - Payment status choices
   - __str__ method

✅ TestTransferModel (2 tests)
   - Create transfer
   - Currency default

✅ TestBankStatementModel (2 tests)
   - Create statement
   - __str__ method

✅ TestExchangeRateModel (3 tests)
   - Create exchange rate
   - __str__ method
   - Uniqueness constraint
```

**Coverage**: ~60% of models
**Missing**:
- Model validation tests (custom validators)
- Model method tests (business logic)
- Signal tests (post_save, pre_delete)
- Computed properties tests
- Relationship tests (cascade deletes)

### ✅ test_filters.py (8+ tests)

#### BillingoInvoiceFilterSet Tests
```python
✅ test_filter_invoice_number_contains()
✅ test_filter_invoice_number_equals()
✅ test_filter_gross_total_greater_than()
✅ test_filter_invoice_date_on_or_after()
✅ test_filter_cancelled_boolean()
✅ test_filter_multiple_fields()
```

**Coverage**: ~40% of BillingoInvoiceFilterSet
**Missing**:
- All other operators (startsWith, endsWith, isEmpty, etc.)
- Partner name/tax number filtering
- Payment status filtering
- Date range filtering (before, onOrBefore)
- Edge cases (null values, empty strings)

#### Other FilterSet Tests
```python
⚠️ TestBeneficiaryFilterSet (placeholder)
⚠️ TestInvoiceFilterSet (placeholder)
```

**Missing**: Full test coverage for all FilterSets

### ✅ test_views.py (12+ tests)

#### API Endpoint Tests
```python
✅ TestBeneficiaryAPI (6 tests)
   - List authenticated
   - List unauthenticated (401)
   - Create beneficiary
   - Create with invalid data
   - Update beneficiary
   - Delete beneficiary

✅ TestBillingoSettingsAPI (2 tests)
   - Test credentials endpoint exists
   - Test credentials without API key

✅ TestNAVInvoiceAPI (2 tests)
   - List invoices
   - Filter by payment status

✅ TestBankStatementAPI (2 tests)
   - List statements
   - Get statement detail

✅ TestTransferAPI (1 test)
   - Bulk create transfers

✅ TestHealthCheck (1 test)
   - Health check endpoint
```

**Coverage**: ~25% of API endpoints
**Missing**:
- All CRUD operations for most endpoints
- Filtering, pagination, ordering tests
- Permission tests (role-based access)
- Error handling (400, 403, 404, 500)
- Bulk operations tests
- Custom actions tests

---

## Missing Tests

### 🔴 CRITICAL Priority (Security & Data Integrity)

#### 1. Permissions Tests (test_permissions.py) - NOT STARTED
**Priority**: CRITICAL
**Estimated Effort**: 3-4 hours
**Risk**: High - Security vulnerability if permissions are broken

##### Required Test Cases (30+ tests needed):

**Company-Level Permissions**
```python
class TestCompanyPermissions:
    ✗ test_user_can_only_see_own_company_data()
    ✗ test_user_cannot_access_other_company_data()
    ✗ test_company_admin_required_for_settings()
    ✗ test_company_admin_required_for_member_management()
    ✗ test_inactive_company_blocks_access()
```

**Role-Based Access Control (RBAC)**
```python
class TestRolePermissions:
    # ADMIN role (full access)
    ✗ test_admin_can_create_beneficiaries()
    ✗ test_admin_can_delete_transfers()
    ✗ test_admin_can_manage_users()
    ✗ test_admin_can_configure_settings()

    # FINANCIAL role (transfers, invoices)
    ✗ test_financial_can_create_transfers()
    ✗ test_financial_can_generate_xml()
    ✗ test_financial_cannot_delete_users()
    ✗ test_financial_cannot_change_settings()

    # ACCOUNTANT role (read-only for transfers)
    ✗ test_accountant_can_view_transfers()
    ✗ test_accountant_cannot_create_transfers()
    ✗ test_accountant_can_view_invoices()

    # USER role (minimal access)
    ✗ test_user_can_view_beneficiaries()
    ✗ test_user_cannot_create_beneficiaries()
    ✗ test_user_cannot_view_bank_statements()
```

**Feature-Gated Permissions**
```python
class TestFeatureGatePermissions:
    ✗ test_nav_sync_requires_feature_enabled()
    ✗ test_billingo_sync_requires_feature_enabled()
    ✗ test_bank_statement_requires_feature_enabled()
    ✗ test_trusted_partners_requires_feature_enabled()
    ✗ test_disabled_feature_returns_403()
```

**Authentication Tests**
```python
class TestAuthentication:
    ✗ test_unauthenticated_returns_401()
    ✗ test_invalid_jwt_returns_401()
    ✗ test_expired_jwt_returns_401()
    ✗ test_no_company_context_returns_400()
    ✗ test_invalid_company_id_returns_403()
```

---

#### 2. Serializer Tests (test_serializers.py) - NOT STARTED
**Priority**: CRITICAL
**Estimated Effort**: 4-5 hours
**Risk**: High - Data validation failures can corrupt database

##### Required Test Cases (40+ tests needed):

**Beneficiary Serializer**
```python
class TestBeneficiarySerializer:
    ✗ test_serialize_beneficiary_to_json()
    ✗ test_deserialize_valid_data()
    ✗ test_deserialize_invalid_account_number()
    ✗ test_deserialize_invalid_vat_number()
    ✗ test_required_fields_validation()
    ✗ test_default_amount_decimal_validation()
    ✗ test_company_is_set_from_context()
```

**Transfer Serializer**
```python
class TestTransferSerializer:
    ✗ test_serialize_transfer()
    ✗ test_deserialize_valid_transfer()
    ✗ test_amount_must_be_positive()
    ✗ test_execution_date_in_future()
    ✗ test_currency_choices_validation()
    ✗ test_beneficiary_belongs_to_company()
    ✗ test_bank_account_belongs_to_company()
```

**NAV Invoice Serializer**
```python
class TestNAVInvoiceSerializer:
    ✗ test_serialize_invoice_with_all_fields()
    ✗ test_invoice_amounts_calculation()
    ✗ test_payment_status_choices()
    ✗ test_invoice_category_validation()
    ✗ test_read_only_fields_cannot_be_updated()
    ✗ test_xml_data_deserialization()
```

**Bank Statement Serializer**
```python
class TestBankStatementSerializer:
    ✗ test_serialize_statement_with_transactions()
    ✗ test_list_serializer_excludes_transactions()
    ✗ test_detail_serializer_includes_transactions()
    ✗ test_matched_percentage_calculation()
    ✗ test_uploaded_by_name_formatting()
    ✗ test_raw_metadata_json_conversion()
```

**Billingo Serializers**
```python
class TestBillingoSerializers:
    ✗ test_billingo_invoice_serializer()
    ✗ test_billingo_settings_api_key_encryption()
    ✗ test_billingo_settings_has_api_key_flag()
    ✗ test_billingo_sync_log_serializer()
    ✗ test_api_key_input_write_only()
    ✗ test_api_key_never_exposed_in_response()
```

**Nested Serializer Tests**
```python
class TestNestedSerializers:
    ✗ test_transfer_with_beneficiary_details()
    ✗ test_bank_transaction_with_invoice_details()
    ✗ test_batch_invoice_matching_details()
    ✗ test_template_with_template_beneficiaries()
```

---

#### 3. Validator Tests (test_validators.py) - NOT STARTED
**Priority**: HIGH
**Estimated Effort**: 2-3 hours
**Risk**: High - Invalid data can corrupt database

##### Required Test Cases (25+ tests needed):

**Hungarian Account Number Validator**
```python
class TestHungarianAccountValidator:
    ✗ test_valid_account_number_24_digits()
    ✗ test_valid_account_number_with_dashes()
    ✗ test_invalid_account_number_too_short()
    ✗ test_invalid_account_number_too_long()
    ✗ test_invalid_account_number_non_numeric()
    ✗ test_invalid_account_number_wrong_format()
    ✗ test_checksum_validation()
```

**VAT Number Validator**
```python
class TestVATNumberValidator:
    ✗ test_valid_hungarian_vat_number()
    ✗ test_valid_vat_with_dashes()
    ✗ test_invalid_vat_format()
    ✗ test_invalid_vat_checksum()
    ✗ test_vat_empty_allowed_when_optional()
```

**IBAN Validator**
```python
class TestIBANValidator:
    ✗ test_valid_hungarian_iban()
    ✗ test_valid_international_iban()
    ✗ test_invalid_iban_checksum()
    ✗ test_invalid_iban_length()
    ✗ test_invalid_iban_country_code()
```

**Amount Validator**
```python
class TestAmountValidator:
    ✗ test_positive_amount_validation()
    ✗ test_zero_amount_not_allowed()
    ✗ test_negative_amount_not_allowed()
    ✗ test_decimal_precision_max_2_places()
    ✗ test_amount_max_value()
```

---

### 🟡 HIGH Priority (Business Logic)

#### 4. Complete Service Tests (test_services.py expansion)
**Priority**: HIGH
**Estimated Effort**: 6-8 hours
**Current**: 13 tests, need 50+ more

##### BillingoSyncService (30 more tests needed)
```python
class TestBillingoSyncService:
    # Full sync workflow
    ✗ test_full_sync_fetches_all_invoices()
    ✗ test_incremental_sync_uses_last_sync_date()
    ✗ test_sync_with_7_day_safety_buffer()
    ✗ test_pagination_fetches_all_pages()
    ✗ test_deduplication_when_created_and_modified()

    # Invoice processing
    ✗ test_invoice_created_if_not_exists()
    ✗ test_invoice_updated_if_exists()
    ✗ test_invoice_items_created()
    ✗ test_related_documents_created()
    ✗ test_organization_data_extracted()
    ✗ test_partner_data_extracted()

    # Error handling
    ✗ test_sync_continues_after_single_invoice_error()
    ✗ test_sync_log_created_on_start()
    ✗ test_sync_log_updated_on_complete()
    ✗ test_sync_log_marked_failed_on_error()
    ✗ test_partial_status_when_some_errors()

    # Rate limiting
    ✗ test_rate_limit_retry_with_backoff()
    ✗ test_max_retries_then_fail()

    # API call tests
    ✗ test_fetch_documents_page_with_filters()
    ✗ test_api_calls_count_tracked()
```

##### BankStatementParserService (20 tests needed)
```python
class TestBankStatementParserService:
    # Parsing
    ✗ test_parse_granit_pdf()
    ✗ test_parse_revolut_csv()
    ✗ test_parse_magnet_pdf()
    ✗ test_parse_kh_pdf()
    ✗ test_detect_bank_from_pdf()
    ✗ test_parse_unsupported_bank_fails()

    # Validation
    ✗ test_parse_and_save_creates_statement()
    ✗ test_parse_and_save_creates_transactions()
    ✗ test_duplicate_file_hash_rejected()
    ✗ test_parsing_error_sets_error_status()

    # Transaction extraction
    ✗ test_transaction_type_mapping()
    ✗ test_amount_extraction()
    ✗ test_date_extraction()
    ✗ test_payer_beneficiary_extraction()
```

##### TransactionMatchingService (25 tests needed)
```python
class TestTransactionMatchingService:
    # Exact matching
    ✗ test_exact_amount_match()
    ✗ test_exact_amount_and_date_match()
    ✗ test_exact_reference_match()

    # Fuzzy matching
    ✗ test_fuzzy_partner_name_match()
    ✗ test_fuzzy_tax_number_match()
    ✗ test_amount_tolerance_match()

    # Confidence scoring
    ✗ test_high_confidence_exact_match()
    ✗ test_medium_confidence_fuzzy_match()
    ✗ test_low_confidence_partial_match()

    # Batch matching
    ✗ test_match_multiple_invoices_to_transaction()
    ✗ test_batch_total_matches_transaction()
    ✗ test_partial_batch_matching()

    # Auto-matching
    ✗ test_auto_match_on_statement_upload()
    ✗ test_trusted_partner_auto_payment()
    ✗ test_match_method_tracking()
```

##### MNBExchangeRateService (10 tests needed)
```python
class TestMNBExchangeRateService:
    ✗ test_fetch_current_rates_from_mnb()
    ✗ test_parse_xml_response()
    ✗ test_create_or_update_rates()
    ✗ test_convert_amount_to_huf()
    ✗ test_get_rate_for_date()
    ✗ test_handle_mnb_api_errors()
    ✗ test_handle_invalid_xml()
```

---

#### 5. Complete Model Tests (test_models.py expansion)
**Priority**: HIGH
**Estimated Effort**: 4-5 hours
**Current**: 20 tests, need 40+ more

##### Model Validation Tests (20 tests needed)
```python
class TestModelValidation:
    # Beneficiary
    ✗ test_beneficiary_vat_number_validation()
    ✗ test_beneficiary_account_number_validation()
    ✗ test_beneficiary_name_max_length()

    # Transfer
    ✗ test_transfer_amount_must_be_positive()
    ✗ test_transfer_execution_date_validation()
    ✗ test_transfer_currency_choices()

    # BankAccount
    ✗ test_bank_account_iban_validation()
    ✗ test_bank_account_only_one_default_per_company()

    # NAVInvoice
    ✗ test_invoice_amounts_consistency()
    ✗ test_invoice_date_order_validation()
```

##### Model Method Tests (15 tests needed)
```python
class TestModelMethods:
    # BankStatement
    ✗ test_calculate_matched_percentage()
    ✗ test_update_transaction_counts()

    # Transfer
    ✗ test_is_overdue_property()
    ✗ test_can_be_processed_method()

    # TransferBatch
    ✗ test_get_total_amount()
    ✗ test_is_ready_for_export()
```

##### Model Signal Tests (10 tests needed)
```python
class TestModelSignals:
    ✗ test_transfer_updates_batch_count()
    ✗ test_bank_transaction_updates_statement_count()
    ✗ test_company_user_creates_audit_log()
```

---

#### 6. Complete API Tests (test_views.py expansion)
**Priority**: HIGH
**Estimated Effort**: 8-10 hours
**Current**: 12 tests, need 80+ more

##### Full CRUD Coverage (40 tests needed)
```python
# Beneficiaries (expand from 6 to 15 tests)
✗ test_list_with_pagination()
✗ test_list_with_filtering()
✗ test_list_with_ordering()
✗ test_create_with_template_association()
✗ test_partial_update_patch()
✗ test_soft_delete_vs_hard_delete()
✗ test_bulk_import_excel()
✗ test_duplicate_account_number_validation()

# Transfers (2 tests needed, add 15 more)
✗ test_list_transfers()
✗ test_create_transfer()
✗ test_generate_xml_export()
✗ test_generate_csv_export()
✗ test_xml_validation()
✗ test_mark_as_processed()
✗ test_transfer_currency_conversion()

# Templates (0 tests, add 12)
✗ test_create_template()
✗ test_load_template_to_transfers()
✗ test_template_with_beneficiaries()
✗ test_update_template()
✗ test_delete_template_keeps_history()

# NAV Invoices (2 tests, add 15 more)
✗ test_sync_nav_invoices()
✗ test_update_payment_status()
✗ test_bulk_update_payment_status()
✗ test_filter_by_date_range()
✗ test_search_by_invoice_number()

# Bank Statements (2 tests, add 15 more)
✗ test_upload_bank_statement()
✗ test_upload_duplicate_rejected()
✗ test_parse_granit_statement()
✗ test_match_invoice_to_transaction()
✗ test_categorize_transaction()
✗ test_reimbursement_pairing()

# Billingo (2 tests, add 10 more)
✗ test_trigger_manual_sync()
✗ test_trigger_full_sync()
✗ test_list_billingo_invoices()
✗ test_filter_billingo_by_status()
✗ test_billingo_sync_logs()

# Exchange Rates (0 tests, add 8)
✗ test_get_current_rates()
✗ test_convert_currency()
✗ test_sync_from_mnb()
✗ test_get_historical_rate()

# Trusted Partners (0 tests, add 10)
✗ test_list_trusted_partners()
✗ test_create_trusted_partner()
✗ test_get_available_partners()
✗ test_auto_payment_on_match()
```

---

### 🟢 MEDIUM Priority (Utilities & Helpers)

#### 7. Utils Tests (test_utils.py) - NOT STARTED
**Priority**: MEDIUM
**Estimated Effort**: 2-3 hours

```python
class TestXMLGeneration:
    ✗ test_generate_xml_structure()
    ✗ test_xml_utf8_encoding()
    ✗ test_xml_special_character_escaping()
    ✗ test_xml_validates_against_schema()

class TestAccountNumberUtils:
    ✗ test_format_account_number()
    ✗ test_clean_account_number()
    ✗ test_validate_checksum()

class TestAmountUtils:
    ✗ test_format_amount_with_currency()
    ✗ test_round_amount_to_2_decimals()
```

---

#### 8. Filter Tests Completion (test_filters.py expansion)
**Priority**: MEDIUM
**Estimated Effort**: 3-4 hours
**Current**: 8 tests, need 30+ more

```python
# BillingoInvoiceFilterSet (add 15 more tests)
✗ test_filter_startswith_operator()
✗ test_filter_endswith_operator()
✗ test_filter_is_empty_operator()
✗ test_filter_is_not_empty_operator()
✗ test_filter_not_contains_operator()
✗ test_filter_not_equal_operator()
✗ test_filter_date_before_operator()
✗ test_filter_date_not_operator()
✗ test_filter_numeric_less_than_equal()
✗ test_filter_partner_name_contains()
✗ test_filter_partner_tax_number()
✗ test_filter_payment_status()
✗ test_filter_type()

# BankTransactionFilterSet (add 20 tests)
✗ test_filter_by_transaction_type()
✗ test_filter_by_amount_range()
✗ test_filter_by_date_range()
✗ test_filter_by_partner_name()
✗ test_filter_matched_transactions()
✗ test_filter_unmatched_transactions()
✗ test_filter_by_bank_statement()

# InvoiceFilterSet (add 15 tests)
✗ test_filter_by_supplier()
✗ test_filter_by_customer()
✗ test_filter_by_payment_status()
✗ test_filter_by_amount()
✗ test_filter_by_due_date()

# BeneficiaryFilterSet (add 10 tests)
✗ test_filter_by_name()
✗ test_filter_by_vat_number()
✗ test_filter_by_account_number()
✗ test_filter_active_only()
```

---

### 🔵 LOW Priority (Nice to Have)

#### 9. Integration Tests (test_integration.py) - NOT STARTED
**Priority**: LOW
**Estimated Effort**: 6-8 hours

```python
class TestBankStatementWorkflow:
    ✗ test_upload_parse_match_export_workflow()
    ✗ test_auto_matching_on_upload()
    ✗ test_manual_matching_override()

class TestTransferWorkflow:
    ✗ test_create_from_template_workflow()
    ✗ test_bulk_create_and_export_workflow()
    ✗ test_approval_workflow()

class TestNAVSyncWorkflow:
    ✗ test_sync_and_match_workflow()
    ✗ test_trusted_partner_auto_payment()

class TestBillingoSyncWorkflow:
    ✗ test_full_sync_workflow()
    ✗ test_incremental_sync_workflow()
```

---

#### 10. Performance Tests (test_performance.py) - NOT STARTED
**Priority**: LOW
**Estimated Effort**: 4-5 hours

```python
class TestPerformance:
    ✗ test_bulk_insert_1000_transfers()
    ✗ test_filter_10000_invoices()
    ✗ test_match_1000_transactions()
    ✗ test_xml_generation_100_transfers()
```

---

## Test Execution Guide

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Running Tests

#### Basic Execution
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest bank_transfers/tests/test_services.py

# Run specific class
pytest bank_transfers/tests/test_services.py::TestBillingoSyncService

# Run specific test
pytest bank_transfers/tests/test_services.py::TestBillingoSyncService::test_validate_credentials_success
```

#### By Category (Markers)
```bash
# Unit tests only
pytest -m unit

# API tests only
pytest -m api

# Service layer tests
pytest -m service

# Model tests
pytest -m model

# Filter tests
pytest -m filter

# Exclude slow tests
pytest -m "not slow"

# Exclude external API tests
pytest -m "not external"
```

#### Coverage Reports
```bash
# Run with coverage
pytest --cov=bank_transfers

# HTML coverage report
pytest --cov=bank_transfers --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=bank_transfers --cov-report=term-missing

# Fail if coverage below 80%
pytest --cov=bank_transfers --cov-fail-under=80
```

#### Debugging
```bash
# Show print statements
pytest -s

# Show local variables in tracebacks
pytest -l

# Enter debugger on failure
pytest --pdb

# Stop at first failure
pytest -x

# Run failed tests from last run
pytest --lf

# Run failed first, then others
pytest --ff
```

#### Parallel Execution
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run in parallel (all CPUs)
pytest -n auto

# Run with 4 workers
pytest -n 4
```

### Continuous Integration

#### GitHub Actions Example
```yaml
name: Backend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=bank_transfers --cov-report=xml --cov-fail-under=80
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
          SECRET_KEY: test-secret-key
          ENVIRONMENT: test

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
```

---

## Contributing Tests

### Writing New Tests

#### 1. Choose the Right Test File
```
test_models.py      - Model validation, constraints, methods
test_serializers.py - Serializer validation, transformation
test_views.py       - API endpoints, permissions, responses
test_services.py    - Business logic, external API calls
test_filters.py     - Queryset filtering, operators
test_validators.py  - Custom validation logic
test_utils.py       - Utility functions, helpers
```

#### 2. Use Fixtures from conftest.py
```python
def test_my_feature(company, beneficiary, authenticated_client):
    """Test uses shared fixtures automatically."""
    response = authenticated_client.get('/api/beneficiaries/')
    assert response.status_code == 200
```

#### 3. Add Appropriate Markers
```python
@pytest.mark.unit
@pytest.mark.service
@pytest.mark.django_db
class TestMyService:
    def test_feature(self):
        ...
```

#### 4. Follow Naming Conventions
```python
# Test files
test_*.py

# Test classes
class Test<ComponentName>:

# Test methods
def test_<what_it_tests>():
def test_<action>_<expected_result>():
def test_<scenario>_<returns|raises>_<outcome>():
```

#### 5. Structure Tests (Arrange-Act-Assert)
```python
def test_feature():
    # Arrange: Set up test data
    user = User.objects.create(...)

    # Act: Perform the action
    result = service.do_something(user)

    # Assert: Verify the result
    assert result.status == 'success'
    assert result.data is not None
```

#### 6. Use Descriptive Assertions
```python
# ❌ Bad
assert x

# ✅ Good
assert user.is_active is True
assert response.status_code == 200
assert beneficiary.name == 'Expected Name'
```

#### 7. Mock External Dependencies
```python
import responses

@responses.activate
def test_external_api():
    responses.add(
        responses.GET,
        'https://api.example.com/data',
        json={'status': 'ok'},
        status=200
    )

    result = service.fetch_data()
    assert result['status'] == 'ok'
```

### Code Review Checklist

- [ ] Test name clearly describes what it tests
- [ ] Test is independent (doesn't depend on other tests)
- [ ] Test uses fixtures instead of duplicating setup code
- [ ] Test has appropriate markers (@pytest.mark.*)
- [ ] Test mocks external dependencies
- [ ] Test assertions are specific and descriptive
- [ ] Test covers both success and failure cases
- [ ] Test has docstring explaining what it tests

---

## Appendix

### A. Test Markers Reference

```python
@pytest.mark.unit          # Fast, isolated unit tests
@pytest.mark.integration   # Multi-component integration tests
@pytest.mark.api           # API endpoint tests
@pytest.mark.service       # Service layer tests
@pytest.mark.model         # Django model tests
@pytest.mark.serializer    # DRF serializer tests
@pytest.mark.filter        # FilterSet tests
@pytest.mark.validator     # Custom validator tests
@pytest.mark.permission    # Permission and access control tests
@pytest.mark.slow          # Slow running tests (>1 second)
@pytest.mark.external      # Tests requiring external services
@pytest.mark.django_db     # Tests requiring database access
```

### B. Coverage Targets by Component

| Component | Target | Critical Paths Target |
|-----------|--------|----------------------|
| Permissions | 95% | 100% |
| Validators | 90% | 100% |
| Serializers | 85% | 95% |
| Services | 80% | 95% |
| Models | 75% | 90% |
| Views (API) | 80% | 95% |
| Filters | 70% | 85% |
| Utils | 70% | 85% |

### C. Test Execution Time Budget

```
Unit Tests:        < 10 seconds total
Integration Tests: < 30 seconds total
API Tests:         < 20 seconds total
Total Test Suite:  < 60 seconds (1 minute)
```

### D. Common Test Patterns

#### Testing API Endpoints
```python
@pytest.mark.api
@pytest.mark.django_db
def test_create_resource(authenticated_client):
    data = {'name': 'Test'}
    response = authenticated_client.post('/api/resource/', data, format='json')

    assert response.status_code == 201
    assert response.data['name'] == 'Test'
```

#### Testing Permissions
```python
@pytest.mark.permission
@pytest.mark.django_db
def test_admin_required(api_client, user):
    api_client.force_authenticate(user=user)
    response = api_client.post('/api/admin-action/')

    assert response.status_code == 403
```

#### Testing External APIs
```python
@responses.activate
@pytest.mark.external
def test_external_api_call():
    responses.add(
        responses.GET,
        'https://api.example.com/data',
        json={'result': 'ok'},
        status=200
    )

    result = service.call_external_api()
    assert result['result'] == 'ok'
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Maintained By**: Development Team
**Review Cycle**: Bi-weekly or after major feature additions
