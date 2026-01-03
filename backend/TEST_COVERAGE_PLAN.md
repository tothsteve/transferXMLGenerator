# Test Coverage Improvement Plan

**Current Overall Coverage**: 34.79%
**Target Coverage**: 80%
**Gap**: 45.21%

**Last Updated**: 2026-01-03

## Current Status

### ✅ Well-Tested Modules (80%+) - 14 files

| File | Coverage | Lines | Status |
|------|----------|-------|--------|
| `api_urls.py` | 100% | 31 | ✅ Complete |
| `base_models.py` | 100% | 23 | ✅ Complete |
| `middleware.py` | 100% | 6 | ✅ Complete |
| `pagination.py` | 100% | 7 | ✅ Complete |
| `models/billingo.py` | 99.25% | 134 | ✅ Excellent |
| `serializers/exchange_rates.py` | 97.44% | 39 | ✅ Excellent |
| `bank_adapters/revolut_adapter.py` | 84.90% | 189 | ✅ Good |
| `validators/hungarian_validators.py` | 84.62% | 9 | ✅ Good |
| `services/credential_manager.py` | 84.21% | 15 | ✅ Good |
| `bank_adapters/kh_adapter.py` | 83.45% | 198 | ✅ Good |
| `models/bank_statements.py` | 81.38% | 135 | ✅ Good |
| `bank_adapters/magnet_adapter.py` | 80.90% | 262 | ✅ Good |
| `models/exchange_rates.py` | 80.85% | 45 | ✅ Good |
| `schemas/bank_statement.py` | 80.85% | 131 | ✅ Good |

**Total Well-Tested Lines**: ~1,224 lines at 80%+

---

## 🔴 Critical Gaps (Priority 1 - HIGH)

### Core Business Logic Services

| File | Current | Target | Gap | Lines Missed | Priority |
|------|---------|--------|-----|--------------|----------|
| `services/transaction_matching_service.py` | 59.30% ⬆️ | 80% | 20.7% | 172/447 | **IN PROGRESS** |
| `services/invoice_sync_service.py` | 6.86% | 80% | 73.14% | 422/464 | **CRITICAL** |
| `services/nav_client.py` | 7.55% | 80% | 72.45% | 378/418 | **CRITICAL** |
| `services/bank_statement_parser_service.py` | 15.24% | 80% | 64.76% | 117/142 | **HIGH** |
| `services/transfer_service.py` | 14.02% | 80% | 65.98% | 99/122 | **HIGH** |

**Impact**: These services contain core business logic for:
- Bank transaction matching (7 strategies, 5 confidence levels)
- NAV invoice synchronization
- Bank statement parsing (5 different banks)
- Transfer generation and validation

**Estimated Effort**: 3-5 days
**Estimated Tests**: 150-200 test cases

---

## 🟡 Medium Priority (Priority 2)

### Export & Integration Services

| File | Current | Target | Gap | Lines Missed |
|------|---------|--------|-----|--------------|
| `kh_export.py` | 10.09% | 80% | 69.91% | 70/81 |
| `utils.py` (XML generation) | 11.76% | 80% | 68.24% | 26/30 |
| `services/exchange_rate_sync_service.py` | 16.15% | 80% | 63.85% | 129/160 |
| `services/beneficiary_service.py` | 17.98% | 80% | 62.02% | 47/63 |
| `services/excel_import_service.py` | 10.53% | 80% | 69.47% | 48/56 |
| `services/mnb_client.py` | 10.78% | 80% | 69.22% | 140/162 |

**Impact**: Export generation, data import, external API integration

**Estimated Effort**: 2-3 days
**Estimated Tests**: 80-100 test cases

---

## 🟢 Lower Priority (Priority 3)

### Views & API Endpoints (Partially Covered)

| File | Current | Notes |
|------|---------|-------|
| `views/bank_statements.py` | 30.77% | Some coverage via API tests |
| `views/transfers.py` | 28.09% | Some coverage via API tests |
| `views/billingo.py` | 29.70% | Some coverage via API tests |
| `views/invoices.py` | 18.89% | Needs more comprehensive tests |
| `authentication.py` | 31.12% | Critical but complex |
| `permissions.py` | 34.96% | Role-based access control |

**Estimated Effort**: 2-3 days
**Estimated Tests**: 100-120 test cases

---

## 🔵 Lowest Priority (Priority 4)

### Management Commands (0% Coverage)

All management commands have 0% coverage. These can be tested manually or with integration tests.

| Command | Lines | Notes |
|---------|-------|-------|
| `import_base_tables.py` | 264 | CSV import functionality |
| `sync_nav_invoices.py` | 136 | NAV API sync |
| `sync_billingo_invoices.py` | 77 | Billingo sync |
| `sync_billingo_spendings.py` | 147 | Billingo spendings |
| `sync_all_nav_invoices.py` | 131 | Batch NAV sync |
| `import_suppliers.py` | 121 | Supplier import |
| `run_scheduler.py` | 33 | Background scheduler |
| `sync_mnb_rates.py` | 22 | Exchange rate sync |
| Others | ~100 | Utility commands |

**Total**: ~1,031 untested lines

**Estimated Effort**: 3-4 days
**Estimated Tests**: 50-60 test cases

---

## 📋 Implementation Plan

### Phase 1: Critical Services (Week 1)
**Goal**: Raise critical services from 5-15% to 80%+

- [x] **Day 1-2**: Transaction Matching Service ✅ **59.30% coverage** (+53.40%)
  - [x] Test exact amount matching
  - [x] Test fuzzy amount matching (±1%)
  - [x] Test date range matching
  - [x] Test reference number matching (invoice number & tax number)
  - [x] Test beneficiary account matching (IBAN)
  - [x] Test batch invoice matching
  - [x] Test confidence level calculation
  - [x] Test auto-payment threshold (≥0.90)
  - [x] Test duplicate match prevention
  - [x] Test system transaction exclusions (fees, interest)
  - [x] Test edge cases (no candidates, currency mismatch)
  - **Result**: 22 test cases, 100% passing

- [ ] **Day 3-4**: Invoice Sync Service
  - [ ] Test NAV API client integration
  - [ ] Test invoice data extraction
  - [ ] Test XML parsing and validation
  - [ ] Test payment status updates
  - [ ] Test trusted partner auto-payment
  - [ ] Test error handling and retries
  - [ ] Test batch synchronization

- [ ] **Day 5**: NAV Client & Bank Statement Parser
  - [ ] Test NAV authentication
  - [ ] Test invoice query endpoints
  - [ ] Test multi-bank statement detection
  - [ ] Test adapter factory pattern
  - [ ] Test metadata extraction
  - [ ] Test transaction parsing

### Phase 2: Export & Integration (Week 2)
**Goal**: Complete export/import functionality testing

- [ ] **Day 1**: XML/CSV Export
  - [ ] Test SEPA XML generation
  - [ ] Test KH Bank CSV format
  - [ ] Test field mapping and validation
  - [ ] Test batch limits (40 transfers for KH)

- [ ] **Day 2**: Exchange Rate & Beneficiary Services
  - [ ] Test MNB API integration
  - [ ] Test currency conversion
  - [ ] Test daily rate caching
  - [ ] Test beneficiary tax number matching
  - [ ] Test flexible format matching (8-digit, 10-digit)

- [ ] **Day 3**: Excel Import
  - [ ] Test Excel parsing
  - [ ] Test beneficiary creation from rows
  - [ ] Test validation and error handling

### Phase 3: Views & Permissions (Week 3)
**Goal**: Improve API endpoint coverage

- [ ] **Day 1-2**: Critical API Views
  - [ ] Bank statement upload/list/detail
  - [ ] Transfer bulk create/XML generation
  - [ ] Invoice payment status updates

- [ ] **Day 3**: Authentication & Permissions
  - [ ] Multi-company context switching
  - [ ] Role-based access control
  - [ ] Feature flag validation

### Phase 4: Management Commands (Optional)
**Goal**: Add basic integration tests for commands

- [ ] Test import_base_tables command
- [ ] Test sync commands with mocked APIs
- [ ] Test scheduler initialization

---

## 📊 Success Metrics

### Coverage Targets by Phase

| Phase | Target Coverage | Current | Increase |
|-------|----------------|---------|----------|
| **Phase 1 Complete** | 50% | 34.79% | +15.21% |
| **Phase 2 Complete** | 65% | 34.79% | +30.21% |
| **Phase 3 Complete** | 75% | 34.79% | +40.21% |
| **Phase 4 Complete** | 80% | 34.79% | +45.21% |

### Quality Metrics

- **Minimum 80% coverage** for all critical services
- **Zero test failures** - all tests must pass
- **Proper test organization** - group by test classes
- **Comprehensive edge cases** - error handling, validation, boundary conditions
- **Integration tests** - test component interactions
- **Mocked external APIs** - NAV, MNB, Billingo

---

## 🧪 Testing Standards

### Test Structure
```python
class TestTransactionMatchingService:
    """Test transaction matching strategies."""

    def setUp(self):
        """Set up test data and fixtures."""
        pass

    def test_exact_amount_matching(self):
        """Test exact amount matching strategy."""
        pass

    def test_fuzzy_amount_matching(self):
        """Test fuzzy amount matching with ±1% tolerance."""
        pass
```

### Coverage Commands
```bash
# Run tests with coverage
pytest --cov=bank_transfers --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Run specific test file
pytest bank_transfers/tests/test_transaction_matching_service.py -v
```

---

## 📝 Progress Tracking

### Completed
- ✅ Bank adapter tests (111 tests, 100% passing)
  - GRÁNIT, Revolut, MagNet, K&H, Raiffeisen
- ✅ Model tests (26 tests)
- ✅ Filter tests (8 tests)
- ✅ View tests (20 tests)
- ✅ **Transaction Matching Service tests** (22 tests, 100% passing)
  - **Coverage**: 5.90% → 59.30% (+53.40%)
  - All 7 matching strategies tested
  - Auto-payment threshold validation
  - Edge cases and duplicate prevention

### In Progress
- 🔄 Invoice Sync Service tests (NEXT)
- 🔄 NAV Client tests

### Pending
- ⏳ Bank Statement Parser Service tests
- ⏳ Transfer Service tests
- ⏳ Export utilities tests
- ⏳ Exchange Rate Service tests
- ⏳ Beneficiary Service tests
- ⏳ Management command tests

---

## 📈 Coverage by Category

| Category | Files | Current Avg | Target | Status |
|----------|-------|-------------|--------|--------|
| **Bank Adapters** | 6 | 81.24% | 80% | ✅ PASS |
| **Models** | 7 | 68.51% | 80% | ⚠️ NEEDS WORK |
| **Serializers** | 7 | 58.12% | 80% | ⚠️ NEEDS WORK |
| **Services** | 12 | 12.19% | 80% | ❌ CRITICAL |
| **Views** | 10 | 36.84% | 80% | ❌ CRITICAL |
| **Management Commands** | 11 | 0% | 60% | ❌ CRITICAL |
| **Utilities** | 5 | 41.67% | 80% | ⚠️ NEEDS WORK |

---

## 🎯 Weekly Goals

### Week 1 (Starting 2026-01-02)
- **Goal**: Raise Services category from 12.19% → 50%
- **Focus**: Transaction Matching, Invoice Sync, NAV Client
- **Deliverable**: ~100 new test cases, 3 new test files
- **Progress**:
  - ✅ Transaction Matching: 5.90% → 59.30% (+53.40%) - 22 tests
  - ⏳ Invoice Sync: 6.86% (pending)
  - ⏳ NAV Client: 7.55% (pending)

### Week 2
- **Goal**: Raise Services category from 50% → 70%
- **Focus**: Export utilities, Exchange rates, Beneficiary service
- **Deliverable**: ~70 new test cases, 4 new test files

### Week 3
- **Goal**: Raise Views category from 36.84% → 65%
- **Focus**: API endpoint integration tests
- **Deliverable**: ~80 new test cases, enhanced API tests

### Week 4
- **Goal**: Reach overall 80% coverage
- **Focus**: Fill remaining gaps, management commands
- **Deliverable**: Final coverage report, documentation

---

**Next Action**: Start with `test_transaction_matching_service.py`
