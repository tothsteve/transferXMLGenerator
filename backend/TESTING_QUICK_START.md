# Testing Quick Start Guide

**5-Minute Guide to Running and Writing Tests**

---

## 🚀 Quick Start (2 minutes)

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=bank_transfers --cov-report=html
open htmlcov/index.html
```

That's it! 🎉

---

## 📝 Writing Your First Test (3 minutes)

### 1. Pick the Right File
```
test_models.py      → Testing Django models
test_serializers.py → Testing DRF serializers
test_views.py       → Testing API endpoints
test_services.py    → Testing business logic
test_filters.py     → Testing FilterSets
test_validators.py  → Testing custom validators
```

### 2. Copy This Template
```python
import pytest

@pytest.mark.unit
@pytest.mark.django_db
def test_my_feature(company, user):
    """Test description in plain English."""
    # Arrange: Set up test data
    beneficiary = Beneficiary.objects.create(
        company=company,
        name='Test Supplier',
        account_number='12345678-12345678-12345678'
    )

    # Act: Perform the action
    result = beneficiary.validate()

    # Assert: Check the result
    assert result is True
    assert beneficiary.is_active is True
```

### 3. Run Your Test
```bash
pytest bank_transfers/tests/test_models.py::test_my_feature -v
```

---

## 🎯 Common Commands

### Run Specific Tests
```bash
# Run one file
pytest bank_transfers/tests/test_services.py

# Run one class
pytest bank_transfers/tests/test_services.py::TestBillingoSyncService

# Run one test
pytest bank_transfers/tests/test_services.py::TestBillingoSyncService::test_validate_credentials
```

### Run by Category
```bash
pytest -m unit          # Only unit tests
pytest -m api           # Only API tests
pytest -m service       # Only service tests
pytest -m "not slow"    # Skip slow tests
```

### Debugging
```bash
pytest -v               # Verbose output
pytest -s               # Show print statements
pytest -x               # Stop at first failure
pytest --pdb            # Enter debugger on failure
pytest --lf             # Run last failed tests
```

---

## 🔧 Available Fixtures

### Just use them in your test function parameters:

```python
def test_something(company, user, authenticated_client):
    # company, user, authenticated_client are automatically available!
    response = authenticated_client.get('/api/beneficiaries/')
    assert response.status_code == 200
```

### Most Common Fixtures
```python
company                  # Test company
user                     # Regular user
admin_user               # Admin user
company_user             # Company membership
authenticated_client     # API client with auth
beneficiary              # Single beneficiary
bank_account             # Bank account
nav_invoice              # NAV invoice
bank_statement           # Bank statement
bank_transaction         # Bank transaction
```

See `conftest.py` for all 20+ fixtures!

---

## ✅ Test Checklist

Before committing:
- [ ] Test name describes what it tests
- [ ] Test uses fixtures (no manual setup)
- [ ] Test has `@pytest.mark.django_db` if using database
- [ ] Test has descriptive assertions
- [ ] Test passes: `pytest path/to/test.py`
- [ ] Coverage didn't drop: `pytest --cov`

---

## 🐛 Troubleshooting

### "ImportError: No module named pytest"
```bash
pip install -r requirements.txt
```

### "Database access not allowed"
Add `@pytest.mark.django_db` to your test:
```python
@pytest.mark.django_db
def test_my_feature():
    ...
```

### "Fixture 'X' not found"
Check if fixture exists in `conftest.py` or import it:
```python
from bank_transfers.tests.conftest import my_fixture
```

### Tests are slow
```bash
# Run in parallel
pip install pytest-xdist
pytest -n auto
```

---

## 📚 Need More Help?

- **Full Documentation**: `TEST_DOCUMENTATION.md`
- **Test Plan**: `TEST_PLAN.md`
- **Test Guide**: `bank_transfers/tests/README.md`
- **Pytest Docs**: https://docs.pytest.org/
- **Pytest-Django Docs**: https://pytest-django.readthedocs.io/

---

## 🎓 Example Test Patterns

### Testing API Endpoints
```python
@pytest.mark.api
@pytest.mark.django_db
def test_create_beneficiary(authenticated_client, company):
    data = {'name': 'New Supplier', 'account_number': '12345678-12345678-12345678'}
    response = authenticated_client.post('/api/beneficiaries/', data, format='json')

    assert response.status_code == 201
    assert response.data['name'] == 'New Supplier'
```

### Testing Services
```python
@pytest.mark.service
@pytest.mark.django_db
def test_sync_company(company, billingo_settings):
    from bank_transfers.services.billingo_sync_service import BillingoSyncService

    service = BillingoSyncService()
    result = service.sync_company(company)

    assert result['invoices_processed'] > 0
```

### Testing Model Validation
```python
@pytest.mark.model
@pytest.mark.django_db
def test_invalid_vat_number(company):
    from django.core.exceptions import ValidationError

    beneficiary = Beneficiary(
        company=company,
        name='Test',
        vat_number='invalid'
    )

    with pytest.raises(ValidationError):
        beneficiary.full_clean()
```

### Mocking External APIs
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

---

**Happy Testing!** 🧪
