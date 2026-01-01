# Bank Transfers Test Suite

Comprehensive test suite for the `bank_transfers` Django app with pytest and Django testing framework.

## Test Organization

```
tests/
├── __init__.py              # Test package initialization and documentation
├── conftest.py              # Pytest fixtures (users, companies, models, API clients)
├── test_models.py           # Model validation and business logic tests
├── test_serializers.py      # Serializer validation tests (TODO)
├── test_views.py            # API endpoint and ViewSet tests
├── test_services.py         # Service layer unit tests
├── test_permissions.py      # Permission and authentication tests (TODO)
├── test_filters.py          # FilterSet and queryset filtering tests
├── test_validators.py       # Custom validator tests (TODO)
└── README.md                # This file
```

## Running Tests

### Install Testing Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
# Using pytest (recommended)
pytest

# Using Django test runner
python manage.py test
```

### Run Specific Test Files

```bash
# Run only service tests
pytest bank_transfers/tests/test_services.py

# Run only model tests
pytest bank_transfers/tests/test_models.py

# Run only API tests
pytest bank_transfers/tests/test_views.py
```

### Run Specific Test Classes

```bash
# Run specific test class
pytest bank_transfers/tests/test_services.py::TestBillingoSyncService

# Run specific test method
pytest bank_transfers/tests/test_services.py::TestBillingoSyncService::test_validate_credentials_success
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Run only service layer tests
pytest -m service

# Run only model tests
pytest -m model

# Run only filter tests
pytest -m filter

# Exclude slow tests
pytest -m "not slow"

# Exclude external API tests
pytest -m "not external"
```

### Run Tests with Coverage

```bash
# Run with coverage report
pytest --cov=bank_transfers --cov-report=html

# View coverage report in browser
open htmlcov/index.html

# Run with terminal coverage report
pytest --cov=bank_transfers --cov-report=term-missing

# Fail if coverage is below 80%
pytest --cov=bank_transfers --cov-fail-under=80
```

### Run Tests in Parallel (faster)

```bash
# Install pytest-xdist first
pip install pytest-xdist

# Run tests in parallel using all CPU cores
pytest -n auto

# Run tests using 4 workers
pytest -n 4
```

### Debugging Tests

```bash
# Show print statements (disable output capturing)
pytest -s

# Show local variables in tracebacks
pytest -l

# Enter debugger on failures
pytest --pdb

# Stop at first failure
pytest -x

# Run only failed tests from last run
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Verbose Output

```bash
# Verbose mode
pytest -v

# Very verbose mode
pytest -vv

# Show summary of all test outcomes
pytest -ra
```

## Test Markers

Tests are categorized with markers for easy filtering:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Integration tests (may touch database)
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.model` - Model tests
- `@pytest.mark.serializer` - Serializer tests
- `@pytest.mark.validator` - Validator tests
- `@pytest.mark.filter` - FilterSet tests
- `@pytest.mark.permission` - Permission tests
- `@pytest.mark.external` - Tests requiring external services (MNB, Billingo API)

## Writing New Tests

### 1. Use Existing Fixtures

Fixtures are defined in `conftest.py` and automatically available to all tests:

```python
def test_beneficiary_creation(company, beneficiary):
    """Test uses company and beneficiary fixtures from conftest.py"""
    assert beneficiary.company == company
    assert beneficiary.is_active is True
```

### 2. Add Markers

```python
@pytest.mark.unit
@pytest.mark.service
@pytest.mark.django_db
class TestMyService:
    def test_my_feature(self):
        ...
```

### 3. Use Django Database Mark

Always use `@pytest.mark.django_db` when accessing the database:

```python
@pytest.mark.django_db
def test_create_company():
    company = Company.objects.create(name="Test Co")
    assert company.id is not None
```

### 4. Mock External APIs

Use `responses` library for HTTP mocking:

```python
import responses

@responses.activate
def test_api_call():
    responses.add(
        responses.GET,
        'https://api.example.com/data',
        json={'status': 'ok'},
        status=200
    )
    # Your test code here
```

### 5. Test API Endpoints

Use `authenticated_client` fixture:

```python
@pytest.mark.api
@pytest.mark.django_db
def test_list_beneficiaries(authenticated_client):
    response = authenticated_client.get('/api/beneficiaries/')
    assert response.status_code == 200
```

## Coverage Goals

- **Target**: 80% overall coverage
- **Critical paths**: 95%+ coverage
  - Authentication and permissions
  - Financial calculations
  - Data validation
  - Payment processing
  - Invoice matching

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest --cov=bank_transfers --cov-fail-under=80
```

## Best Practices

1. **Keep tests fast** - Mock external APIs, use minimal data
2. **Test one thing** - Each test should verify a single behavior
3. **Use descriptive names** - Test names should describe what they test
4. **Arrange-Act-Assert** - Structure tests clearly:
   ```python
   def test_feature():
       # Arrange: Set up test data
       user = User.objects.create(...)

       # Act: Perform the action
       result = service.do_something(user)

       # Assert: Verify the result
       assert result.status == 'success'
   ```
5. **Don't test Django** - Test your code, not Django's functionality
6. **Use factories** - Consider factory_boy for complex object creation
7. **Clean up** - Use fixtures and database transactions for isolation

## Troubleshooting

### Test Database Issues

If tests fail due to database issues:

```bash
# Reset test database
python manage.py test --keepdb=False

# Keep test database between runs (faster)
python manage.py test --keepdb
```

### Import Errors

Ensure Django settings are loaded:

```bash
# Set Django settings module
export DJANGO_SETTINGS_MODULE=transferXMLGenerator.settings

# Or run with pytest-django
pytest  # pytest.ini already configures Django settings
```

### Fixture Not Found

Check that:
1. Fixture is defined in `conftest.py`
2. Fixture name matches exactly
3. Test file imports necessary modules

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django documentation](https://pytest-django.readthedocs.io/)
- [Django testing documentation](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [DRF testing guide](https://www.django-rest-framework.org/api-guide/testing/)
