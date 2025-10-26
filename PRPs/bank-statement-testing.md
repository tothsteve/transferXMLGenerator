name: "Bank Statement Testing - Comprehensive Test Coverage"
description: |
  Add comprehensive test coverage for the fully-implemented bank statement import feature,
  including backend pytest tests for ViewSets/services/adapters and frontend React Testing Library
  tests for components/hooks/integration.

---

## Goal

**Feature Goal**: Achieve comprehensive test coverage (80%+) for the bank statement import feature to ensure production reliability, prevent regressions, and document expected behavior.

**Deliverable**: Complete test suite covering backend (pytest-django) and frontend (Jest + React Testing Library) with unit, integration, and E2E tests.

**Success Definition**:
- ✅ All backend ViewSets, services, and adapters have pytest tests
- ✅ All frontend components have React Testing Library tests
- ✅ Integration tests validate full upload-parse-match workflow
- ✅ CI/CD pipeline runs tests automatically
- ✅ Test coverage reports show 80%+ coverage for bank statement code

## User Persona (if applicable)

**Target User**: Developers and QA engineers maintaining the bank statement feature

**Use Case**:
- Run automated tests before deployment
- Validate bug fixes don't break existing functionality
- Document component behavior and API contracts

**User Journey**:
1. Developer makes code changes to bank statement feature
2. Run `pytest` (backend) and `npm test` (frontend)
3. Review test results and coverage reports
4. Fix failing tests or update test assertions
5. Commit with confidence that feature works correctly

**Pain Points Addressed**:
- ❌ **Current**: No automated tests - manual testing is error-prone and time-consuming
- ❌ **Current**: Regressions can slip through code reviews
- ❌ **Current**: New developers don't have test examples to understand expected behavior
- ✅ **After**: Fast, reliable automated testing with clear documentation of behavior

## Why

- **Quality Assurance**: Bank statement matching directly impacts financial accuracy - bugs can cause incorrect payment status updates
- **Regression Prevention**: Current manual testing scripts don't catch edge cases or breaking changes
- **Documentation**: Tests serve as executable documentation of how the feature works
- **Confidence**: Developers can refactor/optimize with confidence that tests will catch issues
- **Compliance**: Financial software typically requires automated testing for audit trails

## What

Implement comprehensive test coverage for the bank statement import feature across backend and frontend.

### Backend Testing (pytest-django)

**ViewSet Tests** (`backend/bank_transfers/tests/test_bank_statement_viewsets.py`):
- BankStatementViewSet: List, detail, upload, delete, permissions
- BankTransactionViewSet: List, detail, filtering, match/unmatch actions
- OtherCostViewSet: CRUD operations

**Service Tests** (`backend/bank_transfers/tests/test_bank_statement_services.py`):
- BankStatementParserService: File validation, duplicate detection, bank detection
- TransactionMatchingService: All 7 matching strategies with confidence scoring
- Direction compatibility checking logic

**Adapter Tests** (`backend/bank_transfers/tests/test_bank_adapters.py`):
- GRANITAdapter: PDF parsing, transaction extraction
- RevolutAdapter: CSV parsing
- MagNetAdapter: XML parsing
- KHAdapter: PDF parsing
- BankAdapterFactory: Auto-detection logic

**Model Tests** (`backend/bank_transfers/tests/test_bank_statement_models.py`):
- BankStatement model validation and constraints
- BankTransaction model validation and computed properties
- OtherCost model validation

### Frontend Testing (Jest + React Testing Library)

**Component Tests** (`frontend/src/components/BankStatements/__tests__/`):
- BankStatements.tsx: Upload button, filtering, pagination, deletion
- BankStatementCard.tsx: Display, status badges, actions
- BankStatementDetails.tsx: Statement summary, transaction table integration
- BankTransactionTable.tsx: Sorting, filtering, row expansion
- UploadDialog.tsx: File validation, drag-and-drop, upload progress
- ManualMatchDialog.tsx: Invoice search, match/unmatch actions

**Hook Tests** (`frontend/src/hooks/__tests__/api.test.ts`):
- useBankStatements: Pagination, filtering, search
- useUploadBankStatement: File upload with progress
- useMatchTransactionToInvoice: Manual matching
- useDeleteBankStatement: Deletion with confirmation

**Integration Tests** (`frontend/src/integration/__tests__/`):
- Full upload-to-match workflow
- Error handling and retry logic
- Permission-based UI rendering

### Success Criteria

- [ ] Backend test coverage ≥ 80% for bank statement code
- [ ] Frontend test coverage ≥ 80% for bank statement components
- [ ] All ViewSet endpoints have test cases (happy path + error cases)
- [ ] All 7 matching strategies have dedicated test cases
- [ ] All 4 bank adapters have parsing tests with sample files
- [ ] File upload validation tests (size limits, file types, corrupt files)
- [ ] Permission tests (ADMIN, FINANCIAL, ACCOUNTANT, USER roles)
- [ ] Integration tests validate full workflow end-to-end
- [ ] CI/CD pipeline configured to run tests on every PR
- [ ] Test coverage reports generated and tracked

## All Needed Context

### Context Completeness Check

_This PRP provides complete context for implementing comprehensive test coverage for an already-implemented bank statement feature. The agent will have access to existing code patterns, test file structures, and documentation to guide test creation._

### Documentation & References

```yaml
# Backend Testing Documentation
- url: https://pytest-django.readthedocs.io/en/latest/
  why: Official pytest-django documentation for Django test setup and fixtures
  critical: Learn about django_db fixture, client fixtures, and settings management

- url: https://www.django-rest-framework.org/api-guide/testing/
  why: DRF testing guide for APIClient and ViewSet testing patterns
  critical: Understand APIClient, force_authenticate, and response assertions

- url: https://factoryboy.readthedocs.io/en/stable/
  why: Factory Boy for creating test data (models) without boilerplate
  critical: Learn factory patterns for Company, User, BankStatement, BankTransaction

- url: https://docs.pytest.org/en/stable/how-to/fixtures.html
  why: pytest fixture patterns for reusable test components
  critical: Understand fixture scope, parametrize, and dependency injection

# Frontend Testing Documentation
- url: https://testing-library.com/docs/react-testing-library/intro/
  why: React Testing Library philosophy and API
  critical: Learn "test the way users interact" approach, avoid implementation details

- url: https://testing-library.com/docs/react-testing-library/api/#render
  why: Render API and query methods (getBy, findBy, queryBy)
  critical: Understand when to use each query variant and async patterns

- url: https://testing-library.com/docs/user-event/intro/
  why: User event library for realistic user interactions
  critical: Use userEvent instead of fireEvent for file uploads, clicks, typing

- url: https://tanstack.com/query/latest/docs/framework/react/guides/testing
  why: React Query testing patterns and mock setup
  critical: Learn QueryClient wrapper, waitFor patterns, and cache manipulation

- url: https://mui.com/material-ui/guides/testing/
  why: Material-UI testing guide
  critical: Understand MUI component testing quirks (findByRole for Select, etc.)

# Existing Test Patterns
- file: backend/test_bank_statement_import.py
  why: Current manual integration test structure shows expected behavior
  pattern: Function-based tests with print statements and boolean returns
  gotcha: These are not pytest tests - they're standalone scripts that import Django

- file: frontend/src/setupTests.ts
  why: Jest setup with react-testing-library/jest-dom matchers
  pattern: Create React App test configuration
  gotcha: No test files exist yet - this is just configuration

# Bank Statement Implementation Files
- file: backend/bank_transfers/api_views.py
  why: ViewSets to test (lines 1848-2167: BankStatementViewSet, BankTransactionViewSet, OtherCostViewSet)
  pattern: ModelViewSet with custom actions, permission classes, company-scoped querysets
  gotcha: Upload endpoint uses MultiPartParser, custom actions require authentication

- file: backend/bank_transfers/services/bank_statement_parser_service.py
  why: Core parsing logic to test - bank detection, file validation, transaction creation
  pattern: Service class with parse_and_save method, calls adapters, handles errors
  gotcha: Uses Django file upload (SimpleUploadedFile in tests)

- file: backend/bank_transfers/services/transaction_matching_service.py
  why: Matching engine with 7 strategies and confidence scoring
  pattern: Strategy pattern with priority cascade, returns match metadata
  gotcha: Direction compatibility checking prevents false positives

- file: backend/bank_transfers/bank_adapters/
  why: Bank-specific parsers (granit_adapter.py, revolut_adapter.py, magnet_adapter.py, kh_adapter.py)
  pattern: Adapter pattern inheriting from BaseBankAdapter, returns NormalizedTransaction list
  gotcha: Each adapter handles different file formats (PDF, CSV, XML)

- file: frontend/src/components/BankStatements/
  why: All frontend components to test (8 files)
  pattern: Functional components with hooks, Material-UI, React Query integration
  gotcha: Components use custom hooks from hooks/api.ts - need to mock React Query

- file: frontend/src/schemas/bankStatement.schemas.ts
  why: Zod schemas defining TypeScript types and validation
  pattern: Branded types for IDs, enums for statuses, full schema validation
  gotcha: Use type inference from Zod schemas in tests

# Current Codebase Test Structure
- file: backend/bank_transfers/tests/ (DOES NOT EXIST YET)
  why: Need to create this directory structure
  pattern: Should follow Django convention: tests/__init__.py, test_*.py files
  gotcha: Must include __init__.py to make it a package

- file: frontend/src/components/BankStatements/__tests__/ (DOES NOT EXIST YET)
  why: Need to create for component tests
  pattern: Create React App convention: __tests__/ folder or *.test.tsx files
  gotcha: Must include proper mocks for React Query and API calls
```

### Current Codebase Tree

```bash
transferXMLGenerator/
├── backend/
│   ├── bank_transfers/
│   │   ├── api_views.py                    # ViewSets to test
│   │   ├── models.py                       # Models (already have validation)
│   │   ├── serializers.py                  # Serializers to test
│   │   ├── permissions.py                  # Custom permissions to test
│   │   ├── services/
│   │   │   ├── bank_statement_parser_service.py
│   │   │   └── transaction_matching_service.py
│   │   ├── bank_adapters/
│   │   │   ├── base.py
│   │   │   ├── factory.py
│   │   │   ├── granit_adapter.py
│   │   │   ├── revolut_adapter.py
│   │   │   ├── magnet_adapter.py
│   │   │   └── kh_adapter.py
│   │   └── tests/                          # ❌ DOES NOT EXIST
│   ├── test_bank_statement_import.py       # Manual integration script
│   ├── test_pdf_import.py                  # Manual integration script
│   ├── test_api_import.py                  # Manual integration script
│   ├── requirements.txt                     # ❌ Missing pytest-django, factory-boy
│   └── pytest.ini                           # ❌ DOES NOT EXIST
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── BankStatements/
    │   │       ├── BankStatements.tsx
    │   │       ├── BankStatementCard.tsx
    │   │       ├── BankStatementDetails.tsx
    │   │       ├── BankTransactionTable.tsx
    │   │       ├── UploadDialog.tsx
    │   │       ├── ManualMatchDialog.tsx
    │   │       └── __tests__/               # ❌ DOES NOT EXIST
    │   ├── hooks/
    │   │   ├── api.ts                       # API hooks to test
    │   │   └── __tests__/                   # ❌ DOES NOT EXIST
    │   ├── schemas/
    │   │   └── bankStatement.schemas.ts     # Zod schemas
    │   └── setupTests.ts                    # ✅ EXISTS (Jest config)
    ├── package.json                         # ✅ Has test command
    └── jest.config.js                       # ❌ DOES NOT EXIST (uses CRA default)
```

### Desired Codebase Tree (After Implementation)

```bash
transferXMLGenerator/
├── backend/
│   ├── bank_transfers/
│   │   └── tests/                           # ✅ NEW
│   │       ├── __init__.py                  # ✅ NEW - Make it a package
│   │       ├── conftest.py                  # ✅ NEW - Shared fixtures
│   │       ├── factories.py                 # ✅ NEW - Factory Boy factories
│   │       ├── test_bank_statement_viewsets.py  # ✅ NEW - ViewSet tests
│   │       ├── test_bank_statement_services.py  # ✅ NEW - Service tests
│   │       ├── test_bank_adapters.py        # ✅ NEW - Adapter tests
│   │       ├── test_transaction_matching.py # ✅ NEW - Matching logic tests
│   │       ├── test_permissions.py          # ✅ NEW - Permission tests
│   │       ├── test_models.py               # ✅ NEW - Model validation tests
│   │       └── fixtures/                    # ✅ NEW - Sample bank files
│   │           ├── granit_sample.pdf
│   │           ├── revolut_sample.csv
│   │           ├── magnet_sample.xml
│   │           └── kh_sample.pdf
│   ├── pytest.ini                           # ✅ NEW - pytest configuration
│   ├── requirements-dev.txt                 # ✅ NEW - Test dependencies
│   └── .github/
│       └── workflows/
│           └── tests.yml                    # ✅ NEW - CI/CD pipeline
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── BankStatements/
    │   │       └── __tests__/               # ✅ NEW
    │   │           ├── BankStatements.test.tsx
    │   │           ├── BankStatementCard.test.tsx
    │   │           ├── BankStatementDetails.test.tsx
    │   │           ├── BankTransactionTable.test.tsx
    │   │           ├── UploadDialog.test.tsx
    │   │           └── ManualMatchDialog.test.tsx
    │   ├── hooks/
    │   │   └── __tests__/                   # ✅ NEW
    │   │       └── api.test.ts
    │   ├── test-utils/                      # ✅ NEW
    │   │   ├── test-utils.tsx               # React Query wrapper
    │   │   └── mocks.ts                     # API mocks
    │   └── integration/
    │       └── __tests__/                   # ✅ NEW
    │           └── bank-statement-workflow.test.tsx
    └── jest.config.js                       # ✅ NEW - Custom Jest config
```

### Known Gotchas & Library Quirks

```python
# BACKEND GOTCHAS

# 1. Django Test Database
# pytest-django creates a test database - don't run tests on production DB!
# pytest.ini must specify DJANGO_SETTINGS_MODULE

# 2. File Uploads in Tests
# Use SimpleUploadedFile, not real file paths
from django.core.files.uploadedfile import SimpleUploadedFile

with open('fixtures/granit_sample.pdf', 'rb') as f:
    uploaded_file = SimpleUploadedFile(
        'test.pdf',
        f.read(),
        content_type='application/pdf'
    )

# 3. Company Context Middleware
# Tests must set request.company manually - it's normally set by middleware
# Use APIClient.force_authenticate(user) and monkeypatch request.company

# 4. Feature Flags
# CompanyFeature must be created for BANK_STATEMENT_IMPORT feature
# Otherwise permission checks fail even with correct role

# 5. Transaction Matching
# Matching requires existing Invoice records to match against
# Use factories to create matching invoices with same amount/date/IBAN

# FRONTEND GOTCHAS

# 1. React Query Must Be Wrapped
# All components using useQuery/useMutation need QueryClientProvider wrapper
# Create reusable wrapper in test-utils.tsx

# 2. Material-UI Select/Autocomplete
# Use findByRole('combobox') not getByRole - MUI components render async
# Use userEvent.click() not fireEvent.click() for realistic behavior

# 3. File Upload Testing
# Create File object: new File(['content'], 'test.pdf', { type: 'application/pdf' })
# Use userEvent.upload(input, file) for drag-and-drop simulation

# 4. Async Queries
# Always use findBy* or waitFor() for async data loading
# Don't use getBy* for elements that appear after API call

# 5. Toast Notifications
# Toasts render outside component tree - use screen.findByText() not container.queryByText()
```

## Implementation Blueprint

### Data Models and Structure

The models already exist and are production-ready. Tests will validate their behavior.

```python
# backend/bank_transfers/tests/factories.py

import factory
from factory.django import DjangoModelFactory
from bank_transfers.models import (
    Company, BankStatement, BankTransaction, OtherCost,
    CompanyUser, BankAccount, Invoice
)
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = 'Test'
    last_name = 'User'

class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: f'Test Company {n}')
    tax_id = factory.Sequence(lambda n: f'{10000000 + n}')
    is_active = True

class BankStatementFactory(DjangoModelFactory):
    class Meta:
        model = BankStatement

    company = factory.SubFactory(CompanyFactory)
    bank_code = 'GRANIT'
    bank_name = 'GRÁNIT Bank Nyrt.'
    bank_bic = 'GNBAHUHB'
    account_number = '12345678-12345678'
    account_iban = 'HU42117730006111110180000000'
    statement_period_from = date(2025, 1, 1)
    statement_period_to = date(2025, 1, 31)
    opening_balance = Decimal('1000000.00')
    closing_balance = Decimal('950000.00')
    file_name = 'test_statement.pdf'
    file_hash = factory.Sequence(lambda n: f'hash{n}' * 16)  # SHA256 length
    file_size = 1024000
    file_path = 'bank_statements/2025/01/test.pdf'
    uploaded_by = factory.SubFactory(UserFactory)
    status = 'PARSED'
    total_transactions = 10

class BankTransactionFactory(DjangoModelFactory):
    class Meta:
        model = BankTransaction

    company = factory.SubFactory(CompanyFactory)
    bank_statement = factory.SubFactory(BankStatementFactory)
    transaction_type = 'TRANSFER_DEBIT'
    booking_date = date(2025, 1, 15)
    value_date = date(2025, 1, 15)
    amount = Decimal('-50000.00')
    currency = 'HUF'
    description = 'Test payment'
    beneficiary_name = 'Test Supplier Ltd.'
    beneficiary_iban = 'HU42117730006111110180000001'
    reference = 'INV-2025-001'
```

### Implementation Tasks (Ordered by Dependencies)

```yaml
Task 1: SETUP - Install test dependencies and configuration
  - CREATE: backend/requirements-dev.txt
  - CONTENT: |
      pytest==7.4.3
      pytest-django==4.7.0
      pytest-cov==4.1.0
      factory-boy==3.3.0
      faker==20.1.0
  - CREATE: backend/pytest.ini
  - CONTENT: |
      [pytest]
      DJANGO_SETTINGS_MODULE = transferXMLGenerator.settings_local
      python_files = test_*.py
      python_classes = Test*
      python_functions = test_*
      addopts = -v --tb=short --strict-markers --cov=bank_transfers --cov-report=html --cov-report=term-missing
      markers =
          unit: Unit tests
          integration: Integration tests
          slow: Slow tests
  - INSTALL: pip install -r backend/requirements-dev.txt
  - PLACEMENT: Backend root directory

Task 2: CREATE - Test directory structure and fixtures
  - CREATE: backend/bank_transfers/tests/__init__.py (empty file to make package)
  - CREATE: backend/bank_transfers/tests/conftest.py (pytest fixtures)
  - CREATE: backend/bank_transfers/tests/factories.py (Factory Boy factories)
  - CREATE: backend/bank_transfers/tests/fixtures/ (directory for sample files)
  - COPY: Sample bank statement files to fixtures/ directory
  - PLACEMENT: Backend bank_transfers app

Task 3: IMPLEMENT - Factory Boy factories for test data
  - CREATE: backend/bank_transfers/tests/factories.py
  - IMPLEMENT: Factories for Company, User, CompanyUser, BankStatement, BankTransaction, Invoice, BankAccount
  - FOLLOW pattern: factory.SubFactory for ForeignKeys, factory.Sequence for unique fields
  - NAMING: {Model}Factory classes
  - DEPENDENCIES: Models from bank_transfers.models
  - PLACEMENT: backend/bank_transfers/tests/

Task 4: IMPLEMENT - Shared pytest fixtures
  - CREATE: backend/bank_transfers/tests/conftest.py
  - IMPLEMENT: Fixtures for api_client, authenticated_user, company_with_features, sample_pdf_file
  - FOLLOW pattern: @pytest.fixture with function scope for fresh data per test
  - NAMING: snake_case fixture names
  - DEPENDENCIES: Factories from Task 3
  - PLACEMENT: backend/bank_transfers/tests/

Task 5: IMPLEMENT - Model tests
  - CREATE: backend/bank_transfers/tests/test_models.py
  - IMPLEMENT: Tests for BankStatement, BankTransaction validation and computed properties
  - TEST: Unique constraints, field validation, is_credit/is_debit properties
  - FOLLOW pattern: @pytest.mark.django_db decorator, factory usage
  - NAMING: test_{model}_{scenario} function naming
  - COVERAGE: All model constraints and business logic
  - PLACEMENT: backend/bank_transfers/tests/

Task 6: IMPLEMENT - Bank adapter tests
  - CREATE: backend/bank_transfers/tests/test_bank_adapters.py
  - IMPLEMENT: Tests for all 4 adapters (GRANIT, Revolut, MagNet, K&H) parsing sample files
  - TEST: Bank detection, transaction extraction, field mapping accuracy
  - FOLLOW pattern: Parametrize tests for multiple sample files
  - NAMING: test_{adapter}_{scenario} function naming
  - COVERAGE: Happy path parsing, malformed file handling, encoding issues
  - PLACEMENT: backend/bank_transfers/tests/

Task 7: IMPLEMENT - Service tests
  - CREATE: backend/bank_transfers/tests/test_bank_statement_services.py
  - IMPLEMENT: Tests for BankStatementParserService (file validation, duplicate detection, parse_and_save)
  - CREATE: backend/bank_transfers/tests/test_transaction_matching.py
  - IMPLEMENT: Tests for TransactionMatchingService (all 7 matching strategies, confidence scoring, direction compatibility)
  - TEST: Each matching strategy independently, edge cases, false positive prevention
  - FOLLOW pattern: Mock Invoice.objects.filter() for matching tests
  - NAMING: test_{service}_{method}_{scenario}
  - COVERAGE: All service methods, error handling, edge cases
  - PLACEMENT: backend/bank_transfers/tests/

Task 8: IMPLEMENT - ViewSet tests
  - CREATE: backend/bank_transfers/tests/test_bank_statement_viewsets.py
  - IMPLEMENT: Tests for BankStatementViewSet (list, detail, upload, delete, permissions)
  - IMPLEMENT: Tests for BankTransactionViewSet (list, detail, filtering, match/unmatch actions)
  - IMPLEMENT: Tests for OtherCostViewSet (CRUD operations)
  - TEST: Authenticated requests, company isolation, feature flag enforcement, role-based permissions
  - FOLLOW pattern: APIClient, force_authenticate, response.status_code assertions
  - NAMING: Test{ViewSet}_{action}_{scenario} class and method naming
  - COVERAGE: All endpoints (happy path + error cases), permission enforcement
  - PLACEMENT: backend/bank_transfers/tests/

Task 9: IMPLEMENT - Permission tests
  - CREATE: backend/bank_transfers/tests/test_permissions.py
  - IMPLEMENT: Tests for all custom permission classes (RequireBankStatementImport, IsCompanyAdmin, etc.)
  - TEST: Permission grant/deny for each role (ADMIN, FINANCIAL, ACCOUNTANT, USER)
  - FOLLOW pattern: Mock request.user and request.company
  - NAMING: test_{permission}_{role}_{expected_result}
  - COVERAGE: All roles × all actions
  - PLACEMENT: backend/bank_transfers/tests/

Task 10: SETUP - Frontend test utilities
  - CREATE: frontend/src/test-utils/test-utils.tsx
  - IMPLEMENT: Custom render function with QueryClientProvider wrapper
  - CREATE: frontend/src/test-utils/mocks.ts
  - IMPLEMENT: MSW (Mock Service Worker) handlers for API endpoints
  - FOLLOW pattern: React Query testing documentation wrapper pattern
  - NAMING: render, createTestQueryClient, server (MSW server)
  - DEPENDENCIES: @testing-library/react, @tanstack/react-query, msw
  - PLACEMENT: frontend/src/test-utils/

Task 11: IMPLEMENT - Component tests (Upload Dialog)
  - CREATE: frontend/src/components/BankStatements/__tests__/UploadDialog.test.tsx
  - IMPLEMENT: Tests for file validation, drag-and-drop, upload progress, error handling
  - TEST: File type validation, size limits, upload mutation, success/error toasts
  - FOLLOW pattern: userEvent for interactions, waitFor for async, findBy* for async elements
  - NAMING: describe('UploadDialog') > it('should ...')
  - COVERAGE: User interactions, validation rules, API integration
  - PLACEMENT: frontend/src/components/BankStatements/__tests__/

Task 12: IMPLEMENT - Component tests (Bank Statements List)
  - CREATE: frontend/src/components/BankStatements/__tests__/BankStatements.test.tsx
  - IMPLEMENT: Tests for filtering, search, pagination, deletion
  - TEST: Filter interactions, pagination clicks, delete confirmation, API refetch
  - FOLLOW pattern: Mock useQuery return values, test user interactions
  - NAMING: describe('BankStatements') > it('should ...')
  - COVERAGE: All user actions, loading/error states, empty states
  - PLACEMENT: frontend/src/components/BankStatements/__tests__/

Task 13: IMPLEMENT - Component tests (Transaction Table)
  - CREATE: frontend/src/components/BankStatements/__tests__/BankTransactionTable.test.tsx
  - IMPLEMENT: Tests for sorting, filtering, row expansion, manual matching
  - TEST: Column sorting toggle, filter dropdowns, expand details, match dialog open
  - FOLLOW pattern: Test user interactions, not implementation details
  - NAMING: describe('BankTransactionTable') > it('should ...')
  - COVERAGE: Sorting logic, filtering logic, user interactions
  - PLACEMENT: frontend/src/components/BankStatements/__tests__/

Task 14: IMPLEMENT - Component tests (Remaining Components)
  - CREATE: frontend/src/components/BankStatements/__tests__/BankStatementCard.test.tsx
  - CREATE: frontend/src/components/BankStatements/__tests__/BankStatementDetails.test.tsx
  - CREATE: frontend/src/components/BankStatements/__tests__/ManualMatchDialog.test.tsx
  - IMPLEMENT: Tests for each component's user-visible behavior
  - TEST: Props rendering, user interactions, conditional rendering
  - FOLLOW pattern: Same as Tasks 11-13
  - NAMING: describe('{Component}') > it('should ...')
  - COVERAGE: All component variations, props, states
  - PLACEMENT: frontend/src/components/BankStatements/__tests__/

Task 15: IMPLEMENT - Hook tests
  - CREATE: frontend/src/hooks/__tests__/api.test.ts
  - IMPLEMENT: Tests for useBankStatements, useUploadBankStatement, useMatchTransactionToInvoice
  - TEST: Query parameter passing, mutation success/error, cache updates
  - FOLLOW pattern: renderHook from @testing-library/react, waitFor for async
  - NAMING: describe('use{Hook}') > it('should ...')
  - COVERAGE: All custom hooks for bank statements
  - PLACEMENT: frontend/src/hooks/__tests__/

Task 16: IMPLEMENT - Integration tests
  - CREATE: frontend/src/integration/__tests__/bank-statement-workflow.test.tsx
  - IMPLEMENT: E2E test for upload → parse → view → match → verify workflow
  - TEST: Full user journey from upload to transaction matching
  - FOLLOW pattern: Multiple step test with waitFor between steps
  - NAMING: describe('Bank Statement Workflow') > it('should complete full workflow')
  - COVERAGE: End-to-end user scenarios
  - PLACEMENT: frontend/src/integration/__tests__/

Task 17: SETUP - CI/CD Pipeline
  - CREATE: .github/workflows/tests.yml
  - IMPLEMENT: GitHub Actions workflow to run backend and frontend tests on PRs
  - CONFIGURE: Separate jobs for backend (pytest) and frontend (npm test)
  - UPLOAD: Coverage reports to Codecov or similar service
  - NAMING: test-backend, test-frontend jobs
  - TRIGGER: on: [push, pull_request] to main branch
  - PLACEMENT: Repository .github/workflows/
```

### Implementation Patterns & Key Details

```python
# BACKEND TEST PATTERNS

# Pattern 1: ViewSet Test with Authentication and Company Context
import pytest
from rest_framework.test import APIClient
from bank_transfers.tests.factories import CompanyFactory, UserFactory, BankStatementFactory

@pytest.mark.django_db
class TestBankStatementViewSet:
    def test_list_statements_authenticated(self):
        # Setup
        company = CompanyFactory()
        user = UserFactory()
        company_user = CompanyUserFactory(company=company, user=user, role='FINANCIAL')
        feature = CompanyFeatureFactory(company=company, feature_code='BANK_STATEMENT_IMPORT')
        statements = BankStatementFactory.create_batch(3, company=company)

        # Create API client
        client = APIClient()
        client.force_authenticate(user=user)

        # Mock company context (normally set by middleware)
        # CRITICAL: Must manually set request.company in tests
        # Use pytest-django's rf.get() + monkeypatch or custom middleware mock

        # Execute
        response = client.get('/api/bank-statements/')

        # Assert
        assert response.status_code == 200
        assert len(response.data['results']) == 3

# Pattern 2: File Upload Test with SimpleUploadedFile
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_upload_statement(api_client, company_with_features, sample_pdf_file):
    # GOTCHA: Use SimpleUploadedFile, not file paths
    # sample_pdf_file is a fixture that reads from fixtures/granit_sample.pdf

    response = api_client.post(
        '/api/bank-statements/upload/',
        {'file': sample_pdf_file},
        format='multipart'
    )

    assert response.status_code == 201
    assert response.data['status'] == 'PARSED'
    assert response.data['total_transactions'] > 0

# Pattern 3: Matching Strategy Test with Mock Invoices
from unittest.mock import patch, MagicMock

@pytest.mark.unit
def test_reference_exact_matching():
    # Setup
    company = CompanyFactory()
    transaction = BankTransactionFactory(
        company=company,
        amount=Decimal('-50000.00'),
        reference='INV-2025-001',
        booking_date=date(2025, 1, 15)
    )
    invoice = InvoiceFactory(
        company=company,
        invoice_number='INV-2025-001',
        invoice_gross_amount=Decimal('50000.00'),
        payment_due_date=date(2025, 1, 15),
        invoice_direction='INBOUND'  # We received invoice, expect DEBIT transaction
    )

    # Execute
    service = TransactionMatchingService(company)
    match = service.match_transaction(transaction)

    # Assert
    assert match is not None
    assert match.matched_invoice == invoice
    assert match.match_confidence == Decimal('1.00')
    assert match.match_method == 'REFERENCE_EXACT'

# FRONTEND TEST PATTERNS

// Pattern 1: Component Test with React Query Wrapper
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithClient } from 'test-utils/test-utils';
import BankStatements from '../BankStatements';

describe('BankStatements', () => {
  it('should display uploaded statements', async () => {
    // CRITICAL: Use custom render with QueryClient wrapper
    renderWithClient(<BankStatements />);

    // Wait for data to load (async query)
    await waitFor(() => {
      expect(screen.getByText(/test bank statement/i)).toBeInTheDocument();
    });
  });
});

// Pattern 2: File Upload Test with userEvent
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should upload file via drag and drop', async () => {
  const user = userEvent.setup();
  renderWithClient(<UploadDialog open={true} onClose={jest.fn()} />);

  // Create file object
  const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

  // Find file input
  const input = screen.getByLabelText(/upload/i);

  // Upload file
  await user.upload(input, file);

  // Wait for validation
  await waitFor(() => {
    expect(screen.getByText(/test.pdf/i)).toBeInTheDocument();
  });

  // Click upload button
  const uploadButton = screen.getByRole('button', { name: /feltöltés/i });
  await user.click(uploadButton);

  // Wait for success toast
  await waitFor(() => {
    expect(screen.getByText(/sikeres feltöltés/i)).toBeInTheDocument();
  });
});

// Pattern 3: Hook Test with renderHook
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBankStatements } from '../api';

describe('useBankStatements', () => {
  it('should fetch bank statements with pagination', async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    const { result } = renderHook(
      () => useBankStatements({ page: 1, page_size: 20 }),
      { wrapper }
    );

    // Wait for query to complete
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Assert
    expect(result.current.data.results).toHaveLength(20);
  });
});
```

### Integration Points

```yaml
BACKEND:
  - dependencies: "Add to requirements-dev.txt: pytest, pytest-django, pytest-cov, factory-boy, faker"
  - configuration: "Create pytest.ini with Django settings module and coverage config"
  - fixtures: "Add sample bank statement files to bank_transfers/tests/fixtures/"
  - commands: "pytest backend/bank_transfers/tests/ -v --cov=bank_transfers --cov-report=html"

FRONTEND:
  - dependencies: "npm install --save-dev @testing-library/user-event msw"
  - configuration: "Create jest.config.js to extend CRA config with coverage thresholds"
  - test-utils: "Create test-utils.tsx with QueryClient wrapper and custom render function"
  - commands: "npm test -- --coverage --watchAll=false"

CI/CD:
  - github-actions: "Create .github/workflows/tests.yml"
  - jobs: |
      - test-backend: Run pytest with coverage upload
      - test-frontend: Run npm test with coverage upload
  - triggers: "On push to main, pull_request to main"
  - artifacts: "Upload coverage reports to Codecov"
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Backend - Run after each test file creation
cd backend
ruff check bank_transfers/tests/ --fix
mypy bank_transfers/tests/
ruff format bank_transfers/tests/

# Frontend - Run after each test file creation
cd frontend
npm run lint:fix

# Expected: Zero errors. Fix linting issues before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Backend - Test each module as created
pytest bank_transfers/tests/test_models.py -v
pytest bank_transfers/tests/test_factories.py -v
pytest bank_transfers/tests/test_bank_adapters.py -v
pytest bank_transfers/tests/test_bank_statement_services.py -v
pytest bank_transfers/tests/test_transaction_matching.py -v
pytest bank_transfers/tests/test_permissions.py -v
pytest bank_transfers/tests/test_bank_statement_viewsets.py -v

# All backend tests
pytest bank_transfers/tests/ -v --cov=bank_transfers --cov-report=term-missing

# Frontend - Test each component as created
npm test -- BankStatements.test.tsx
npm test -- UploadDialog.test.tsx
npm test -- BankTransactionTable.test.tsx
npm test -- ManualMatchDialog.test.tsx

# All frontend tests with coverage
npm test -- --coverage --watchAll=false

# Expected: All tests pass with 80%+ coverage.
```

### Level 3: Integration Testing (System Validation)

```bash
# Backend integration tests
pytest bank_transfers/tests/test_bank_statement_viewsets.py -v -m integration
pytest bank_transfers/tests/ -v -m integration

# Frontend integration tests
npm test -- integration/

# Expected: Full workflow tests pass, API mocks work correctly.
```

### Level 4: Coverage Validation

```bash
# Backend coverage report
pytest bank_transfers/tests/ --cov=bank_transfers --cov-report=html --cov-report=term-missing
open htmlcov/index.html  # View detailed coverage report

# Frontend coverage report
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html  # View detailed coverage report

# Coverage thresholds
# Backend: --cov-fail-under=80 in pytest.ini
# Frontend: coverageThreshold in jest.config.js

# Expected:
# - Backend bank_transfers/models.py: 90%+
# - Backend bank_transfers/services/: 85%+
# - Backend bank_transfers/bank_adapters/: 80%+
# - Backend bank_transfers/api_views.py: 80%+
# - Frontend components/BankStatements/: 80%+
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] Backend: `pytest bank_transfers/tests/ -v --cov=bank_transfers --cov-fail-under=80` passes
- [ ] Frontend: `npm test -- --coverage --watchAll=false` passes with 80%+ coverage
- [ ] No linting errors: `ruff check backend/bank_transfers/` and `npm run lint`
- [ ] No type errors: `mypy backend/bank_transfers/`
- [ ] CI/CD pipeline runs and passes on GitHub Actions

### Feature Validation

- [ ] All ViewSet endpoints have test cases (list, detail, create, update, delete, custom actions)
- [ ] All 7 matching strategies have dedicated test cases with edge cases
- [ ] All 4 bank adapters have parsing tests with sample files
- [ ] File upload validation tests (size, type, corrupt files) pass
- [ ] Permission tests validate all roles (ADMIN, FINANCIAL, ACCOUNTANT, USER)
- [ ] Frontend components have tests for user interactions (clicks, typing, uploads)
- [ ] API integration tests validate request/response contracts
- [ ] Error handling tests validate error messages and recovery

### Code Quality Validation

- [ ] Test file naming follows conventions (test_*.py, *.test.tsx)
- [ ] Test functions have descriptive names (test_{action}_{scenario})
- [ ] Factories used instead of manual model creation
- [ ] Fixtures reused via conftest.py (backend) and test-utils (frontend)
- [ ] Mocks used appropriately (API calls, external services, not business logic)
- [ ] Tests are isolated (no shared state between tests)
- [ ] Tests are deterministic (no random failures)

### Documentation & Deployment

- [ ] README.md updated with testing commands
- [ ] requirements-dev.txt documents all test dependencies
- [ ] pytest.ini and jest.config.js committed to repository
- [ ] Sample bank statement fixtures committed to repository
- [ ] Coverage reports generated and reviewed
- [ ] CI/CD badge added to README showing test status

---

## Anti-Patterns to Avoid

- ❌ Don't test implementation details (internal state, private methods)
- ❌ Don't create brittle tests that break on UI text changes (use test IDs or roles)
- ❌ Don't skip error case testing - test both happy path AND error paths
- ❌ Don't use time.sleep() - use waitFor() for async operations
- ❌ Don't share state between tests - each test should be independent
- ❌ Don't mock what you don't own - mock external APIs, not your own business logic
- ❌ Don't write integration tests without unit tests - bottom-up approach
- ❌ Don't ignore coverage gaps - aim for 80%+ on critical business logic
- ❌ Don't skip CI/CD setup - automated testing is essential for production
