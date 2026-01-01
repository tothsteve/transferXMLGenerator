"""
Bank Transfers App Test Suite

This package contains all unit tests, integration tests, and API tests for the bank_transfers app.

Test Organization:
- test_models.py: Model validation and business logic tests
- test_serializers.py: Serializer validation and data transformation tests
- test_views.py: API endpoint and ViewSet tests
- test_services.py: Service layer unit tests
- test_permissions.py: Permission and authentication tests
- test_filters.py: FilterSet and queryset filtering tests
- test_validators.py: Custom validator tests

Running Tests:
    # Run all tests
    python manage.py test

    # Run with pytest
    pytest

    # Run with coverage
    pytest --cov=bank_transfers --cov-report=html

    # Run specific test file
    pytest bank_transfers/tests/test_services.py

    # Run specific test class
    pytest bank_transfers/tests/test_services.py::TestBillingoSyncService

    # Run specific test method
    pytest bank_transfers/tests/test_services.py::TestBillingoSyncService::test_validate_credentials
"""
