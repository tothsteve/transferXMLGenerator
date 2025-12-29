"""
Bank Transfers Views - Feature-based vertical slices

This package organizes ViewSets by feature/domain instead of having one monolithic api_views.py file.
Each module exports its ViewSets which are then imported by api_urls.py for URL routing.
"""

# Import all ViewSets for easy access from api_urls.py
from .bank_accounts import BankAccountViewSet

__all__ = [
    'BankAccountViewSet',
]
