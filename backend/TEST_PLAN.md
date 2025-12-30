# Backend Test Implementation Plan

**Project**: Transfer XML Generator Backend
**Plan Created**: 2025-01-15
**Target Completion**: 4 weeks
**Coverage Goal**: 80% overall, 95%+ critical paths

---

## Executive Summary

### Current State
- ✅ Test infrastructure complete (pytest, fixtures, config)
- ✅ 50+ tests written across 4 test files
- ✅ ~30-40% estimated coverage
- ❌ Critical gaps: Permissions, Serializers, Validators

### Missing Tests
- **Total Tests Needed**: ~250 additional tests
- **Estimated Effort**: 40-50 hours
- **Priority Distribution**: 40% CRITICAL, 35% HIGH, 25% MEDIUM/LOW

### Implementation Schedule
```
Week 1: CRITICAL - Permissions & Serializers (20 hours)
Week 2: HIGH - Validators & Service completion (15 hours)
Week 3: HIGH - API & Model completion (12 hours)
Week 4: MEDIUM - Filters, Utils, Integration (8 hours)
```

---

## Priority Matrix

### 🔴 CRITICAL (Must Have - Week 1-2)

| Test Suite | Tests Needed | Effort | Risk | Deadline |
|------------|--------------|--------|------|----------|
| **Permissions** | 30 tests | 4h | HIGH | Week 1 |
| **Serializers** | 40 tests | 5h | HIGH | Week 1 |
| **Validators** | 25 tests | 3h | HIGH | Week 2 |
| **Service (Billingo)** | 20 tests | 4h | MEDIUM | Week 2 |

**Total**: 115 tests, 16 hours

### 🟡 HIGH (Should Have - Week 2-3)

| Test Suite | Tests Needed | Effort | Risk | Deadline |
|------------|--------------|--------|------|----------|
| **Service (Bank Parser)** | 20 tests | 4h | MEDIUM | Week 2 |
| **Service (Matching)** | 25 tests | 5h | MEDIUM | Week 2 |
| **API Views (Full CRUD)** | 40 tests | 8h | MEDIUM | Week 3 |
| **Models (Validation)** | 20 tests | 3h | LOW | Week 3 |

**Total**: 105 tests, 20 hours

### 🟢 MEDIUM (Nice to Have - Week 3-4)

| Test Suite | Tests Needed | Effort | Risk | Deadline |
|------------|--------------|--------|------|----------|
| **Filters (Complete)** | 30 tests | 4h | LOW | Week 3 |
| **Utils** | 10 tests | 2h | LOW | Week 4 |
| **Integration** | 15 tests | 6h | LOW | Week 4 |

**Total**: 55 tests, 12 hours

---

## Week 1: CRITICAL Priority (Days 1-5)

### Day 1-2: Permissions Tests (test_permissions.py)
**Goal**: Complete all security and access control tests
**Effort**: 4 hours
**Tests**: 30

#### Checklist
```python
# Company-Level Permissions (5 tests - 30 min)
[ ] test_user_can_only_see_own_company_data
[ ] test_user_cannot_access_other_company_data
[ ] test_company_admin_required_for_settings
[ ] test_inactive_company_blocks_access
[ ] test_company_context_required

# Role-Based Access Control (15 tests - 2 hours)
[ ] test_admin_full_access
[ ] test_admin_can_manage_users
[ ] test_financial_can_create_transfers
[ ] test_financial_can_generate_xml
[ ] test_financial_cannot_delete_users
[ ] test_accountant_read_only_transfers
[ ] test_accountant_cannot_create_transfers
[ ] test_user_minimal_access
[ ] test_user_cannot_create_beneficiaries
[ ] test_user_cannot_view_bank_statements
[ ] test_role_inheritance
[ ] test_permission_caching
[ ] test_role_change_updates_permissions
[ ] test_inactive_user_blocked
[ ] test_multiple_company_context_switching

# Feature-Gated Permissions (6 tests - 1 hour)
[ ] test_nav_sync_requires_feature
[ ] test_billingo_sync_requires_feature
[ ] test_bank_statement_requires_feature
[ ] test_trusted_partners_requires_feature
[ ] test_disabled_feature_returns_403
[ ] test_feature_check_performance

# Authentication (4 tests - 30 min)
[ ] test_unauthenticated_returns_401
[ ] test_invalid_jwt_returns_401
[ ] test_expired_jwt_returns_401
[ ] test_no_company_context_returns_400
```

**Deliverable**: `bank_transfers/tests/test_permissions.py` (400+ lines)

---

### Day 3-4: Serializer Tests (test_serializers.py)
**Goal**: Complete all data validation tests
**Effort**: 5 hours
**Tests**: 40

#### Checklist
```python
# Beneficiary Serializer (7 tests - 45 min)
[ ] test_serialize_beneficiary_to_json
[ ] test_deserialize_valid_data
[ ] test_deserialize_invalid_account_number
[ ] test_deserialize_invalid_vat_number
[ ] test_required_fields_validation
[ ] test_default_amount_decimal_validation
[ ] test_company_set_from_context

# Transfer Serializer (7 tests - 45 min)
[ ] test_serialize_transfer
[ ] test_deserialize_valid_transfer
[ ] test_amount_must_be_positive
[ ] test_execution_date_in_future
[ ] test_currency_choices_validation
[ ] test_beneficiary_belongs_to_company
[ ] test_bank_account_belongs_to_company

# NAV Invoice Serializer (6 tests - 45 min)
[ ] test_serialize_invoice_with_all_fields
[ ] test_invoice_amounts_calculation
[ ] test_payment_status_choices
[ ] test_invoice_category_validation
[ ] test_read_only_fields
[ ] test_xml_data_deserialization

# Bank Statement Serializer (6 tests - 45 min)
[ ] test_serialize_statement_with_transactions
[ ] test_list_vs_detail_serializer
[ ] test_matched_percentage_calculation
[ ] test_uploaded_by_name_formatting
[ ] test_raw_metadata_json_conversion
[ ] test_transaction_nesting

# Billingo Serializers (8 tests - 1 hour)
[ ] test_billingo_invoice_serializer
[ ] test_billingo_settings_api_key_encryption
[ ] test_billingo_settings_has_api_key_flag
[ ] test_billingo_sync_log_serializer
[ ] test_api_key_input_write_only
[ ] test_api_key_never_exposed
[ ] test_encrypted_key_stored_correctly
[ ] test_decrypt_on_sync

# Nested Serializers (6 tests - 45 min)
[ ] test_transfer_with_beneficiary_details
[ ] test_bank_transaction_with_invoice_details
[ ] test_batch_invoice_matching_details
[ ] test_template_with_template_beneficiaries
[ ] test_deep_nesting_performance
[ ] test_circular_reference_handling
```

**Deliverable**: `bank_transfers/tests/test_serializers.py` (500+ lines)

---

### Day 5: Validator Tests (test_validators.py)
**Goal**: Complete all custom validation tests
**Effort**: 3 hours
**Tests**: 25

#### Checklist
```python
# Hungarian Account Validator (7 tests - 45 min)
[ ] test_valid_account_24_digits
[ ] test_valid_account_with_dashes
[ ] test_invalid_too_short
[ ] test_invalid_too_long
[ ] test_invalid_non_numeric
[ ] test_invalid_wrong_format
[ ] test_checksum_validation

# VAT Number Validator (5 tests - 30 min)
[ ] test_valid_hungarian_vat
[ ] test_valid_vat_with_dashes
[ ] test_invalid_vat_format
[ ] test_invalid_vat_checksum
[ ] test_vat_optional_when_allowed

# IBAN Validator (5 tests - 30 min)
[ ] test_valid_hungarian_iban
[ ] test_valid_international_iban
[ ] test_invalid_iban_checksum
[ ] test_invalid_iban_length
[ ] test_invalid_country_code

# Amount Validator (5 tests - 30 min)
[ ] test_positive_amount_required
[ ] test_zero_not_allowed
[ ] test_negative_not_allowed
[ ] test_decimal_precision_max_2
[ ] test_amount_max_value

# Date Validators (3 tests - 30 min)
[ ] test_execution_date_not_in_past
[ ] test_payment_due_date_validation
[ ] test_date_range_validation
```

**Deliverable**: `bank_transfers/tests/test_validators.py` (350+ lines)

---

## Week 2: HIGH Priority - Services (Days 6-10)

### Day 6-7: BillingoSyncService Tests (expansion)
**Goal**: Complete Billingo sync service tests
**Effort**: 4 hours
**Tests**: 20

#### Checklist
```python
# Full Sync Workflow (5 tests - 1 hour)
[ ] test_full_sync_fetches_all_invoices
[ ] test_incremental_sync_uses_last_sync_date
[ ] test_sync_with_7_day_safety_buffer
[ ] test_pagination_fetches_all_pages
[ ] test_deduplication_created_and_modified

# Invoice Processing (6 tests - 1.5 hours)
[ ] test_invoice_created_if_not_exists
[ ] test_invoice_updated_if_exists
[ ] test_invoice_items_created
[ ] test_related_documents_created
[ ] test_organization_data_extracted
[ ] test_partner_data_extracted

# Error Handling (5 tests - 1 hour)
[ ] test_sync_continues_after_error
[ ] test_sync_log_created_on_start
[ ] test_sync_log_updated_on_complete
[ ] test_sync_log_marked_failed
[ ] test_partial_status_some_errors

# Rate Limiting (4 tests - 30 min)
[ ] test_rate_limit_retry_with_backoff
[ ] test_max_retries_then_fail
[ ] test_api_calls_count_tracked
[ ] test_concurrent_sync_prevention
```

**Deliverable**: Update `test_services.py` (+250 lines)

---

### Day 8: BankStatementParserService Tests
**Goal**: Complete bank statement parsing tests
**Effort**: 4 hours
**Tests**: 20

#### Checklist
```python
# Bank Adapters (6 tests - 1.5 hours)
[ ] test_parse_granit_pdf
[ ] test_parse_revolut_csv
[ ] test_parse_magnet_pdf
[ ] test_parse_kh_pdf
[ ] test_detect_bank_from_pdf
[ ] test_unsupported_bank_fails

# Validation (4 tests - 1 hour)
[ ] test_parse_and_save_creates_statement
[ ] test_parse_and_save_creates_transactions
[ ] test_duplicate_file_hash_rejected
[ ] test_parsing_error_sets_status

# Transaction Extraction (6 tests - 1 hour)
[ ] test_transaction_type_mapping
[ ] test_amount_extraction_credit
[ ] test_amount_extraction_debit
[ ] test_date_extraction_formats
[ ] test_payer_beneficiary_extraction
[ ] test_metadata_extraction

# Edge Cases (4 tests - 30 min)
[ ] test_empty_statement
[ ] test_corrupted_pdf
[ ] test_missing_required_fields
[ ] test_special_characters_handling
```

**Deliverable**: Update `test_services.py` (+300 lines)

---

### Day 9-10: TransactionMatchingService Tests
**Goal**: Complete invoice matching tests
**Effort**: 5 hours
**Tests**: 25

#### Checklist
```python
# Exact Matching (3 tests - 45 min)
[ ] test_exact_amount_match
[ ] test_exact_amount_and_date_match
[ ] test_exact_reference_match

# Fuzzy Matching (6 tests - 1.5 hours)
[ ] test_fuzzy_partner_name_match
[ ] test_fuzzy_tax_number_match
[ ] test_amount_tolerance_match
[ ] test_levenshtein_distance_matching
[ ] test_phonetic_matching
[ ] test_abbreviation_matching

# Confidence Scoring (5 tests - 1 hour)
[ ] test_high_confidence_exact_match
[ ] test_medium_confidence_fuzzy_match
[ ] test_low_confidence_partial_match
[ ] test_confidence_threshold
[ ] test_multiple_matches_sorted_by_confidence

# Batch Matching (6 tests - 1.5 hours)
[ ] test_match_multiple_invoices_to_transaction
[ ] test_batch_total_matches_transaction
[ ] test_partial_batch_matching
[ ] test_batch_matching_optimization
[ ] test_batch_unmatching
[ ] test_batch_rematch

# Auto-Matching (5 tests - 30 min)
[ ] test_auto_match_on_upload
[ ] test_trusted_partner_auto_payment
[ ] test_match_method_tracking
[ ] test_auto_match_disabled
[ ] test_manual_override_auto_match
```

**Deliverable**: Update `test_services.py` (+350 lines)

---

## Week 3: HIGH Priority - APIs & Models (Days 11-15)

### Day 11-13: Complete API Tests
**Goal**: Full CRUD coverage for all endpoints
**Effort**: 8 hours
**Tests**: 40

#### Endpoint Coverage Checklist

**Beneficiaries** (9 more tests - 1.5 hours)
```python
[ ] test_list_with_pagination
[ ] test_list_with_filtering
[ ] test_list_with_ordering
[ ] test_create_with_template
[ ] test_partial_update_patch
[ ] test_soft_delete
[ ] test_bulk_import_excel
[ ] test_duplicate_validation
[ ] test_export_to_excel
```

**Transfers** (13 tests - 2.5 hours)
```python
[ ] test_list_transfers
[ ] test_create_transfer
[ ] test_bulk_create_transfers
[ ] test_generate_xml_export
[ ] test_generate_csv_export
[ ] test_xml_validation
[ ] test_mark_as_processed
[ ] test_currency_conversion
[ ] test_filter_by_status
[ ] test_filter_by_date_range
[ ] test_update_transfer
[ ] test_delete_transfer
[ ] test_transfer_batch_operations
```

**Templates** (8 tests - 1.5 hours)
```python
[ ] test_create_template
[ ] test_load_template_to_transfers
[ ] test_template_with_beneficiaries
[ ] test_update_template
[ ] test_delete_template
[ ] test_copy_template
[ ] test_template_validation
[ ] test_template_preview
```

**NAV Invoices** (10 tests - 2.5 hours)
```python
[ ] test_sync_nav_invoices
[ ] test_update_payment_status
[ ] test_bulk_update_payment_status
[ ] test_filter_by_date_range
[ ] test_search_invoice_number
[ ] test_filter_by_supplier
[ ] test_filter_by_customer
[ ] test_filter_by_amount
[ ] test_export_invoices
[ ] test_invoice_statistics
```

**Deliverable**: Update `test_views.py` (+500 lines)

---

### Day 14-15: Complete Model Tests
**Goal**: Model validation, methods, signals
**Effort**: 3 hours
**Tests**: 20

#### Checklist
```python
# Model Validation (10 tests - 1.5 hours)
[ ] test_beneficiary_vat_validation
[ ] test_beneficiary_account_validation
[ ] test_transfer_amount_positive
[ ] test_transfer_date_validation
[ ] test_bank_account_iban_valid
[ ] test_only_one_default_account
[ ] test_invoice_amounts_consistent
[ ] test_invoice_date_order
[ ] test_statement_balance_calculation
[ ] test_transaction_amount_signs

# Model Methods (6 tests - 1 hour)
[ ] test_bank_statement_matched_percentage
[ ] test_transfer_is_overdue
[ ] test_transfer_can_be_processed
[ ] test_batch_total_amount
[ ] test_batch_ready_for_export
[ ] test_invoice_is_paid_property

# Model Signals (4 tests - 30 min)
[ ] test_transfer_updates_batch_count
[ ] test_transaction_updates_statement_count
[ ] test_company_user_audit_log
[ ] test_soft_delete_cascade
```

**Deliverable**: Update `test_models.py` (+250 lines)

---

## Week 4: MEDIUM Priority - Polish (Days 16-20)

### Day 16-17: Complete Filter Tests
**Goal**: Comprehensive FilterSet coverage
**Effort**: 4 hours
**Tests**: 30

#### Checklist
```python
# BillingoInvoiceFilterSet (15 tests - 2 hours)
[ ] test_all_string_operators (8 operators × 2 fields)
[ ] test_all_date_operators (6 operators × 2 fields)
[ ] test_all_numeric_operators (6 operators × 2 fields)

# BankTransactionFilterSet (10 tests - 1.5 hours)
[ ] test_filter_by_type
[ ] test_filter_by_amount_range
[ ] test_filter_by_date_range
[ ] test_filter_matched_status
[ ] test_complex_query

# Other FilterSets (5 tests - 30 min)
[ ] test_invoice_filter
[ ] test_beneficiary_filter
[ ] test_transfer_filter
[ ] test_statement_filter
[ ] test_filter_performance
```

**Deliverable**: Update `test_filters.py` (+400 lines)

---

### Day 18: Utils Tests
**Goal**: Test utility functions
**Effort**: 2 hours
**Tests**: 10

#### Checklist
```python
# XML Generation (4 tests - 45 min)
[ ] test_generate_xml_structure
[ ] test_xml_utf8_encoding
[ ] test_xml_special_characters
[ ] test_xml_schema_validation

# Account Utils (3 tests - 45 min)
[ ] test_format_account_number
[ ] test_clean_account_number
[ ] test_validate_checksum

# Amount Utils (3 tests - 30 min)
[ ] test_format_amount
[ ] test_round_amount
[ ] test_currency_conversion
```

**Deliverable**: `bank_transfers/tests/test_utils.py` (200 lines)

---

### Day 19-20: Integration Tests
**Goal**: End-to-end workflow tests
**Effort**: 6 hours
**Tests**: 15

#### Checklist
```python
# Bank Statement Workflow (5 tests - 2 hours)
[ ] test_upload_parse_match_export
[ ] test_auto_matching_on_upload
[ ] test_manual_matching_override
[ ] test_categorize_and_export
[ ] test_reimbursement_pairing

# Transfer Workflow (5 tests - 2 hours)
[ ] test_template_to_export
[ ] test_bulk_create_export
[ ] test_approval_workflow
[ ] test_multi_currency_transfer
[ ] test_batch_processing

# Sync Workflows (5 tests - 2 hours)
[ ] test_nav_sync_and_match
[ ] test_billingo_full_sync
[ ] test_trusted_partner_payment
[ ] test_exchange_rate_sync
[ ] test_concurrent_operations
```

**Deliverable**: `bank_transfers/tests/test_integration.py` (400 lines)

---

## Daily Testing Routine

### Morning (Start of Day)
```bash
# Run all tests to ensure nothing broke
pytest

# Check coverage
pytest --cov=bank_transfers --cov-report=term-missing

# Review coverage gaps
open htmlcov/index.html
```

### During Development
```bash
# Run specific test file you're working on
pytest bank_transfers/tests/test_permissions.py -v

# Run in watch mode (requires pytest-watch)
ptw -- bank_transfers/tests/test_permissions.py
```

### End of Day
```bash
# Run full test suite
pytest --cov=bank_transfers --cov-fail-under=80

# Commit if tests pass
git add bank_transfers/tests/
git commit -m "test: Add <component> tests"
```

---

## Success Criteria

### Week 1 Success
- ✅ All CRITICAL tests complete (115 tests)
- ✅ Permissions fully covered (100%)
- ✅ Serializers fully covered (95%+)
- ✅ Validators fully covered (95%+)
- ✅ Overall coverage > 50%

### Week 2 Success
- ✅ All service tests complete
- ✅ BillingoSyncService fully covered (90%+)
- ✅ BankStatementParserService covered (85%+)
- ✅ TransactionMatchingService covered (85%+)
- ✅ Overall coverage > 65%

### Week 3 Success
- ✅ API endpoints fully tested
- ✅ All CRUD operations covered
- ✅ Model validation complete
- ✅ Overall coverage > 75%

### Week 4 Success
- ✅ All filters tested
- ✅ Utils tested
- ✅ Integration tests complete
- ✅ **Overall coverage ≥ 80%**
- ✅ **Critical paths ≥ 95%**

---

## Risk Mitigation

### Potential Blockers

| Risk | Impact | Mitigation |
|------|--------|------------|
| External API dependencies | HIGH | Use `responses` library for mocking |
| Database setup complexity | MEDIUM | Use pytest fixtures and transactions |
| Test data creation overhead | MEDIUM | Use factory_boy for model factories |
| Slow test execution | MEDIUM | Run tests in parallel with pytest-xdist |
| Flaky tests | MEDIUM | Ensure test isolation, use freezegun for time |

### Contingency Plans

1. **If behind schedule after Week 1**:
   - Reduce Week 4 tasks (filters, utils)
   - Focus on maintaining 80% overall coverage
   - Defer integration tests to next sprint

2. **If coverage not meeting target**:
   - Run coverage report to identify gaps
   - Prioritize untested critical paths
   - Add targeted tests for low-coverage modules

3. **If tests are too slow**:
   - Profile with `pytest --durations=10`
   - Optimize slow tests
   - Use parallel execution
   - Mock more external dependencies

---

## Tracking Progress

### Weekly Checklist

**Week 1**
- [ ] Day 1-2: Permissions tests complete
- [ ] Day 3-4: Serializer tests complete
- [ ] Day 5: Validator tests complete
- [ ] Coverage > 50%

**Week 2**
- [ ] Day 6-7: Billingo service tests complete
- [ ] Day 8: Bank parser tests complete
- [ ] Day 9-10: Matching service tests complete
- [ ] Coverage > 65%

**Week 3**
- [ ] Day 11-13: API tests complete
- [ ] Day 14-15: Model tests complete
- [ ] Coverage > 75%

**Week 4**
- [ ] Day 16-17: Filter tests complete
- [ ] Day 18: Utils tests complete
- [ ] Day 19-20: Integration tests complete
- [ ] Coverage ≥ 80%

---

## Reporting

### Daily Report Template
```markdown
## Test Progress - Day X

**Tests Added**: X tests
**Tests Passing**: X/X (100%)
**Coverage**: X% (+X% from yesterday)
**Time Spent**: X hours

**Completed**:
- Component A: X tests

**In Progress**:
- Component B: X/Y tests

**Blockers**:
- None / [describe blocker]

**Tomorrow**:
- Complete Component B
- Start Component C
```

### Weekly Summary Template
```markdown
## Week X Test Summary

**Total Tests**: X tests (+X from last week)
**Coverage**: X% (+X% from last week)
**Time Spent**: X hours

**Highlights**:
- Completed all CRITICAL tests
- Fixed X failing tests
- Improved performance by Xs

**Next Week**:
- Focus on [component]
- Target X% coverage
```

---

**Plan Version**: 1.0
**Created**: 2025-01-15
**Updated**: 2025-01-15
**Owner**: Development Team
