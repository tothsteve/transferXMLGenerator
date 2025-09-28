# CLAUDE.md

This file provides comprehensive guidance to Claude Code when working with Django REST API code in this Transfer XML Generator repository.

## Core Development Philosophy

### KISS (Keep It Simple, Stupid)

Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible. Simple solutions are easier to understand, maintain, and debug.

### YAGNI (You Aren't Gonna Need It)

Avoid building functionality on speculation. Implement features only when they are needed, not when you anticipate they might be useful in the future.

### Design Principles

- **Dependency Inversion**: High-level modules should not depend on low-level modules. Both should depend on abstractions.
- **Open/Closed Principle**: Software entities should be open for extension but closed for modification.
- **Single Responsibility**: Each function, class, and module should have one clear purpose.
- **Fail Fast**: Check for potential errors early and raise exceptions immediately when issues occur.

## 🧱 Code Structure & Modularity

### File and Function Limits

- **Never create a file longer than 500 lines of code**. If approaching this limit, refactor by splitting into modules.
- **Functions should be under 50 lines** with a single, clear responsibility.
- **Classes should be under 100 lines** and represent a single concept or entity.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Line lenght should be max 100 characters** ruff rule in pyproject.toml

### Project Architecture

Follow Django app-based architecture with clear separation of concerns:

```
transferXMLGenerator/
    ├── backend/
    │   ├── manage.py
    │   ├── transferXMLGenerator/           # Main project settings
    │   │   ├── __init__.py
    │   │   ├── settings.py                # Environment detection
    │   │   ├── settings_local.py          # SQL Server (development)
    │   │   ├── settings_production.py     # PostgreSQL (Railway)
    │   │   ├── urls.py
    │   │   └── wsgi.py
    │   │
    │   └── bank_transfers/                 # Main Django app
    │       ├── __init__.py
    │       ├── models.py                   # Company, Beneficiary, Transfer models
    │       ├── serializers.py             # DRF serializers with validation
    │       ├── api_views.py                # ViewSets and API endpoints
    │       ├── admin.py                    # Django admin configuration
    │       ├── apps.py
    │       ├── services/                   # Business logic services
    │       │   ├── beneficiary_service.py  # Tax number matching logic
    │       │   ├── nav_sync_service.py     # NAV API integration
    │       │   └── export_service.py       # XML/CSV generation
    │       ├── utils/                      # Helper functions
    │       │   ├── generate_xml.py         # SEPA XML generation
    │       │   ├── kh_export.py           # KH Bank CSV export
    │       │   └── validators.py          # Custom field validators
    │       ├── migrations/                 # Database migrations
    │       └── tests/                      # Django test cases
    │           ├── test_models.py
    │           ├── test_serializers.py
    │           ├── test_api_views.py
    │           └── test_services.py
    │
    └── frontend/                          # React TypeScript frontend
```

## 🛠️ Development Environment

### Django + pip/virtualenv Setup

This project uses Django with traditional pip and virtualenv for package management.

```bash
# Create virtual environment (recommended: Python 3.11+)
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if separate file exists)
pip install -r requirements-dev.txt

# Add a new package
# 1. Install the package
pip install new-package
# 2. Update requirements.txt
pip freeze > requirements.txt

# OR manually add to requirements.txt with version
echo "new-package==1.2.3" >> requirements.txt
```

### Development Commands

```bash
# Django development server
python manage.py runserver 8002

# Run all tests
python manage.py test

# Run specific app tests
python manage.py test bank_transfers

# Run specific test class
python manage.py test bank_transfers.tests.test_models.BeneficiaryModelTests

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell for debugging
python manage.py shell

# Collect static files (production)
python manage.py collectstatic

# Check for common issues
python manage.py check

# Show migration status
python manage.py showmigrations

# Load initial data (if fixtures exist)
python manage.py loaddata fixtures/initial_data.json
```

## 📋 Style & Conventions

### Django + Python Style Guide

- **Follow PEP8 and Django coding style** with these specific choices:
  - Line length: 100 characters
  - Use double quotes for strings
  - Use trailing commas in multi-line structures
- **Django-specific conventions**:
  - Use `snake_case` for model fields, methods, and variables
  - Use `PascalCase` for model and class names
  - Use `UPPER_SNAKE_CASE` for constants and settings
- **Type hints recommended** for complex functions and service methods
- **Use Django's built-in validators and forms** for data validation
- **Follow Django REST Framework patterns** for serializers and viewsets

### Docstring Standards

Use Google-style docstrings for all public functions, classes, and modules:

```python
def calculate_discount(
    price: Decimal,
    discount_percent: float,
    min_amount: Decimal = Decimal("0.01")
) -> Decimal:
    """
    Calculate the discounted price for a product.

    Args:
        price: Original price of the product
        discount_percent: Discount percentage (0-100)
        min_amount: Minimum allowed final price

    Returns:
        Final price after applying discount

    Raises:
        ValueError: If discount_percent is not between 0 and 100
        ValueError: If final price would be below min_amount

    Example:
        >>> calculate_discount(Decimal("100"), 20)
        Decimal('80.00')
    """
```

### Naming Conventions

- **Variables and functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes/methods**: `_leading_underscore`
- **Type aliases**: `PascalCase`
- **Enum values**: `UPPER_SNAKE_CASE`

## 🧪 Testing Strategy

### Test-Driven Development (TDD)

1. **Write the test first** - Define expected behavior before implementation
2. **Watch it fail** - Ensure the test actually tests something
3. **Write minimal code** - Just enough to make the test pass
4. **Refactor** - Improve code while keeping tests green
5. **Repeat** - One test at a time

### Django Testing Best Practices

```python
# Use Django's TestCase for database-backed tests
from django.test import TestCase
from django.contrib.auth.models import User
from bank_transfers.models import Company, Beneficiary

class BeneficiaryModelTests(TestCase):
    """Test cases for the Beneficiary model."""

    def setUp(self):
        """Set up test data before each test method."""
        self.company = Company.objects.create(
            name="Test Company",
            tax_id="12345678",
            is_active=True
        )

    def test_beneficiary_creation_with_valid_data(self):
        """Test that beneficiaries can be created with valid data."""
        beneficiary = Beneficiary.objects.create(
            company=self.company,
            name="Test Beneficiary",
            account_number="1234567890123456"
        )
        self.assertEqual(beneficiary.name, "Test Beneficiary")
        self.assertTrue(beneficiary.is_active)

    def test_beneficiary_vat_number_validation(self):
        """Test that VAT number validation works correctly."""
        from django.core.exceptions import ValidationError

        beneficiary = Beneficiary(
            company=self.company,
            name="Test Person",
            vat_number="invalid_vat"
        )

        with self.assertRaises(ValidationError):
            beneficiary.full_clean()

# Use Django's APITestCase for API endpoint testing
from rest_framework.test import APITestCase
from rest_framework import status

class BeneficiaryAPITests(APITestCase):
    """Test cases for Beneficiary API endpoints."""

    def setUp(self):
        """Set up authentication and test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_beneficiary_success(self):
        """Test successful beneficiary creation via API."""
        data = {
            'name': 'New Beneficiary',
            'account_number': '1234567890123456'
        }
        response = self.client.post('/api/beneficiaries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

### Test Organization

- Unit tests: Test individual functions/methods in isolation
- Integration tests: Test component interactions
- End-to-end tests: Test complete user workflows
- Keep test files next to the code they test
- Use `conftest.py` for shared fixtures
- Aim for 80%+ code coverage, but focus on critical paths

## 🚨 Error Handling

### Exception Best Practices

```python
# Create custom exceptions for your domain
class PaymentError(Exception):
    """Base exception for payment-related errors."""
    pass

class InsufficientFundsError(PaymentError):
    """Raised when account has insufficient funds."""
    def __init__(self, required: Decimal, available: Decimal):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient funds: required {required}, available {available}"
        )

# Use specific exception handling
try:
    process_payment(amount)
except InsufficientFundsError as e:
    logger.warning(f"Payment failed: {e}")
    return PaymentResult(success=False, reason="insufficient_funds")
except PaymentError as e:
    logger.error(f"Payment error: {e}")
    return PaymentResult(success=False, reason="payment_error")

# Use context managers for resource management
from contextlib import contextmanager

@contextmanager
def database_transaction():
    """Provide a transactional scope for database operations."""
    conn = get_connection()
    trans = conn.begin_transaction()
    try:
        yield conn
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
```

### Logging Strategy

```python
import logging
from functools import wraps

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log function entry/exit for debugging
def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func.__name__} successfully")
            return result
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {e}")
            raise
    return wrapper
```

## 🔧 Configuration Management

### Environment Variables and Settings

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation."""
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    redis_url: str = "redis://localhost:6379"
    api_key: str
    max_connections: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Usage
settings = get_settings()
```

## 🏗️ Django Models and Serializers

### Django Model Example with Validation

```python
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

class Beneficiary(models.Model):
    """Model for transfer beneficiaries with tax number support."""

    # Company isolation (multi-tenant architecture)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='beneficiaries')

    # Basic beneficiary information
    name = models.CharField(max_length=200, help_text="Full legal name of beneficiary")
    account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\d{16}|\d{8}-\d{8}|\d{8}-\d{8}-\d{8}$',
                                   'Invalid Hungarian account number format')]
    )

    # Tax identification (mutually exclusive)
    vat_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="10-digit personal VAT number"
    )
    tax_number = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        help_text="8-digit company tax number"
    )

    # Status and metadata
    is_active = models.BooleanField(default=True)
    is_frequent = models.BooleanField(default=False)
    description = models.CharField(max_length=200, blank=True)
    remittance_information = models.TextField(blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_transfers_beneficiary'
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['company', 'tax_number']),
            models.Index(fields=['company', 'vat_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'account_number'],
                name='unique_account_per_company',
                condition=models.Q(account_number__isnull=False)
            ),
        ]

    def clean(self):
        """Custom validation for business rules."""
        super().clean()

        # Ensure at least one identifier is provided
        if not any([self.account_number, self.vat_number, self.tax_number]):
            raise ValidationError(
                "At least one of account_number, vat_number, or tax_number must be provided"
            )

        # Ensure mutual exclusivity between VAT and tax numbers
        if self.vat_number and self.tax_number:
            raise ValidationError(
                "Cannot have both VAT number (individuals) and tax number (companies)"
            )

        # Validate VAT number format
        if self.vat_number and len(self.vat_number) != 10:
            raise ValidationError("VAT number must be exactly 10 digits")

        # Validate tax number format
        if self.tax_number and len(self.tax_number) != 8:
            raise ValidationError("Tax number must be exactly 8 digits")

    def __str__(self):
        return f"{self.name} ({self.company.name})"
```

### Django REST Framework Serializer

```python
from rest_framework import serializers
from .models import Beneficiary

class BeneficiarySerializer(serializers.ModelSerializer):
    """Serializer for Beneficiary model with custom validation."""

    class Meta:
        model = Beneficiary
        fields = [
            'id', 'name', 'account_number', 'vat_number', 'tax_number',
            'description', 'is_active', 'is_frequent', 'remittance_information',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Cross-field validation."""
        # Call model's clean method for business rule validation
        instance = Beneficiary(**data)
        instance.clean()
        return data

    def create(self, validated_data):
        """Create beneficiary with company context."""
        # Company is set from request context in the view
        validated_data['company'] = self.context['request'].user.active_company
        return super().create(validated_data)

class BeneficiaryCreateSerializer(BeneficiarySerializer):
    """Serializer for creating beneficiaries."""
    pass

class BeneficiaryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating beneficiaries - all fields optional."""

    class Meta:
        model = Beneficiary
        fields = ['name', 'account_number', 'vat_number', 'tax_number',
                  'description', 'is_active', 'is_frequent', 'remittance_information']
        extra_kwargs = {field: {'required': False} for field in fields}
```

## 🏦 Project-Specific Patterns

### Multi-Company Architecture

This project implements a **multi-tenant architecture** where companies are isolated data containers:

```python
# All business models must include company scoping
class BaseCompanyModel(models.Model):
    """Abstract base model for company-scoped entities."""
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Permission class for company isolation
class CompanyContextPermission(BasePermission):
    """Ensure user has access to the specified company."""

    def has_permission(self, request, view):
        return hasattr(request.user, 'active_company') and request.user.active_company

    def has_object_permission(self, request, view, obj):
        return obj.company == request.user.active_company
```

### NAV Integration Patterns

```python
# Service pattern for complex business logic
class BeneficiaryMatchingService:
    """Service for matching NAV invoices to beneficiaries by tax number."""

    @staticmethod
    def find_beneficiary_by_tax_number(company, supplier_tax_number):
        """
        Find beneficiary by tax number with flexible format matching.

        Supports three levels of matching:
        1. Exact match
        2. Normalized match (remove dashes/spaces)
        3. Base match (first 8 digits)
        """
        # Implementation here...

    @staticmethod
    def _normalize_tax_number(tax_number):
        """Remove dashes and spaces, keeping only digits."""
        return ''.join(filter(str.isdigit, tax_number))
```

### Export Generation Patterns

```python
# Utility functions for XML/CSV generation
def generate_xml(transfers, originator_account):
    """
    Generate SEPA-compatible XML for Hungarian bank transfers.

    Args:
        transfers: List of Transfer objects
        originator_account: BankAccount object for originator

    Returns:
        tuple: (xml_content, batch_object)
    """
    # XML generation logic here...

def generate_kh_export(transfers, originator_account):
    """
    Generate KH Bank CSV export (max 40 transfers per batch).

    Args:
        transfers: List of Transfer objects (max 40)
        originator_account: BankAccount object for originator

    Returns:
        tuple: (csv_content, batch_object)
    """
    # CSV generation logic here...
```

### Database Configuration Patterns

```python
# Environment-specific settings
ENVIRONMENT = config('ENVIRONMENT', default='local')

if ENVIRONMENT == 'production':
    # PostgreSQL for Railway deployment
    DATABASES = {
        'default': dj_database_url.parse(
            config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # SQL Server for local development
    DATABASES = {
        'default': {
            'ENGINE': 'mssql',
            'NAME': 'administration',
            'HOST': 'localhost,1435',
            'USER': config('DB_USER', default='sa'),
            'PASSWORD': config('DB_PASSWORD'),
            'OPTIONS': {
                'driver': 'ODBC Driver 17 for SQL Server',
            },
        }
    }
```

## 🔄 Git Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates
- `refactor/*` - Code refactoring
- `test/*` - Test additions or fixes

### Commit Message Format

Never include claude code, or written by claude code in commit messages

```
<type>(<scope>): <subject>

<body>

<footer>
``
Types: feat, fix, docs, style, refactor, test, chore

Example:
```

feat(auth): add two-factor authentication

- Implement TOTP generation and validation
- Add QR code generation for authenticator apps
- Update user model with 2FA fields

Closes #123

````

## 🗄️ Django Database & Model Standards

### Django Model Conventions
Follow Django's standard conventions with project-specific patterns:

```python
# ✅ DJANGO STANDARD: Auto-incrementing integer primary keys
class Company(models.Model):
    # Django auto-creates: id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_transfers_company'
        verbose_name_plural = 'Companies'
```

### Field Naming Conventions

```sql
-- Primary keys: Auto-incrementing integers (Django default)
id INTEGER PRIMARY KEY AUTO_INCREMENT

-- Foreign keys: {referenced_model}_id
company_id, beneficiary_id, template_id

-- Timestamps: {action}_at
created_at, updated_at, executed_at, expires_at

-- Booleans: is_{state}
is_active, is_frequent, is_processed, is_default

-- Money fields: Use DecimalField for precision
amount DECIMAL(15,2), total_amount DECIMAL(15,2)

-- Text fields: Use appropriate max_length
name VARCHAR(200), description TEXT, notes TEXT

-- Choices: Use CharField with choices
status VARCHAR(20), currency VARCHAR(3), direction VARCHAR(10)
```

### Multi-Company Architecture Pattern

All business models include company isolation:

```python
class Beneficiary(models.Model):
    """Company-scoped beneficiary with tax number support."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    vat_number = models.CharField(max_length=20, blank=True, null=True,
                                  help_text="10-digit personal VAT number")
    tax_number = models.CharField(max_length=8, blank=True, null=True,
                                  help_text="8-digit company tax number")

    class Meta:
        db_table = 'bank_transfers_beneficiary'
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['company', 'tax_number']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['company', 'account_number'],
                                    name='unique_account_per_company'),
        ]
```

### Django REST Framework API Standards

```python
# ✅ DJANGO REST: ViewSet with standard endpoints
class BeneficiaryViewSet(viewsets.ModelViewSet):
    """CRUD operations for beneficiaries with company isolation."""
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated, CompanyContextPermission]

    def get_queryset(self):
        # Always filter by company context
        return Beneficiary.objects.filter(
            company=self.request.user.active_company
        )

# Standard URL patterns
urlpatterns = [
    path('api/beneficiaries/', BeneficiaryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/beneficiaries/<int:pk>/', BeneficiaryViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'delete': 'destroy'
    })),
]
```

### Database Table Naming
Django automatically generates table names: `{app_label}_{model_name}`

```sql
-- Auto-generated table names
bank_transfers_company
bank_transfers_beneficiary
bank_transfers_transfertemplate
bank_transfers_transfer
bank_transfers_transferbatch
```

## 📝 Documentation Standards

### Code Documentation

- Every module should have a docstring explaining its purpose
- Public functions must have complete docstrings
- Complex logic should have inline comments with `# Reason:` prefix
- Keep README.md updated with setup instructions and examples
- Maintain CHANGELOG.md for version history

### Django REST Framework API Documentation

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class BeneficiaryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing beneficiaries with company isolation.

    Provides CRUD operations for beneficiaries within the authenticated
    user's company context. Supports filtering by active status and
    frequent usage patterns.
    """
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated, CompanyContextPermission]

    @swagger_auto_schema(
        operation_summary="List beneficiaries",
        operation_description="Retrieve a paginated list of company beneficiaries",
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description="Search by beneficiary name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'is_frequent', openapi.IN_QUERY,
                description="Filter by frequent beneficiaries",
                type=openapi.TYPE_BOOLEAN
            ),
        ]
    )
    def list(self, request):
        """
        List company beneficiaries with optional filtering.

        - **search**: Filter by beneficiary name (case-insensitive)
        - **is_frequent**: Show only frequently used beneficiaries
        - **is_active**: Show only active beneficiaries (default: true)
        """
        return super().list(request)

    @action(detail=False, methods=['get'])
    def frequent(self, request):
        """Get frequently used beneficiaries for quick selection."""
        frequent_beneficiaries = self.get_queryset().filter(is_frequent=True)
        serializer = self.get_serializer(frequent_beneficiaries, many=True)
        return Response(serializer.data)
```

## 🚀 Performance Considerations

### Optimization Guidelines

- Profile before optimizing - use `cProfile` or `py-spy`
- Use `lru_cache` for expensive computations
- Prefer generators for large datasets
- Use `asyncio` for I/O-bound operations
- Consider `multiprocessing` for CPU-bound tasks
- Cache database queries appropriately

### Example Optimization

```python
from functools import lru_cache
import asyncio
from typing import AsyncIterator

@lru_cache(maxsize=1000)
def expensive_calculation(n: int) -> int:
    """Cache results of expensive calculations."""
    # Complex computation here
    return result

async def process_large_dataset() -> AsyncIterator[dict]:
    """Process large dataset without loading all into memory."""
    async with aiofiles.open('large_file.json', mode='r') as f:
        async for line in f:
            data = json.loads(line)
            # Process and yield each item
            yield process_item(data)
```

## 🛡️ Security Best Practices

### Security Guidelines

- Never commit secrets - use environment variables
- Validate all user input with Pydantic
- Use parameterized queries for database operations
- Implement rate limiting for APIs
- Keep dependencies updated with `uv`
- Use HTTPS for all external communications
- Implement proper authentication and authorization

### Example Security Implementation

```python
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)
```

## 🔍 Debugging Tools

### Debugging Commands

```bash
# Interactive debugging with ipdb
uv add --dev ipdb
# Add breakpoint: import ipdb; ipdb.set_trace()

# Memory profiling
uv add --dev memory-profiler
uv run python -m memory_profiler script.py

# Line profiling
uv add --dev line-profiler
# Add @profile decorator to functions

# Debug with rich traceback
uv add --dev rich
# In code: from rich.traceback import install; install()
```

## 📊 Monitoring and Observability

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "payment_processed",
    user_id=user.id,
    amount=amount,
    currency="USD",
    processing_time=processing_time
)
```

## 📚 Useful Resources

### Essential Tools

- UV Documentation: https://github.com/astral-sh/uv
- Ruff: https://github.com/astral-sh/ruff
- Pytest: https://docs.pytest.org/
- Pydantic: https://docs.pydantic.dev/
- FastAPI: https://fastapi.tiangolo.com/

### Python Best Practices

- PEP 8: https://pep8.org/
- PEP 484 (Type Hints): https://www.python.org/dev/peps/pep-0484/
- The Hitchhiker's Guide to Python: https://docs.python-guide.org/

## ⚠️ Important Notes

- **NEVER ASSUME OR GUESS** - When in doubt, ask for clarification
- **Always verify file paths and module names** before use
- **Keep CLAUDE.md updated** when adding new patterns or dependencies
- **Test your code** - No feature is complete without tests
- **Document your decisions** - Future developers (including yourself) will thank you

## 🔍 Search Command Requirements

**CRITICAL**: Always use `rg` (ripgrep) instead of traditional `grep` and `find` commands:

```bash
# ❌ Don't use grep
grep -r "pattern" .

# ✅ Use rg instead
rg "pattern"

# ❌ Don't use find with name
find . -name "*.py"

# ✅ Use rg with file filtering
rg --files | rg "\.py$"
# or
rg --files -g "*.py"
```

**Enforcement Rules:**

```
(
    r"^grep\b(?!.*\|)",
    "Use 'rg' (ripgrep) instead of 'grep' for better performance and features",
),
(
    r"^find\s+\S+\s+-name\b",
    "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance",
),
```

## 🚀 GitHub Flow Workflow Summary

main (protected) ←── PR ←── feature/your-feature
↓ ↑
deploy development

### Daily Workflow:

1. git checkout main && git pull origin main
2. git checkout -b feature/new-feature
3. Make changes + tests
4. git push origin feature/new-feature
5. Create PR → Review → Merge to main

---

_This document is a living guide. Update it as the project evolves and new patterns emerge._
