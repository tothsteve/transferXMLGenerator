"""
Custom pagination classes for bank_transfers app.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination with configurable page size up to 1000 items.
    Supports query parameter 'page_size' to allow frontend to request different page sizes.
    """
    page_size = 50  # Default page size
    page_size_query_param = 'page_size'  # Allow client to override with ?page_size=500
    max_page_size = 1000  # Maximum allowed page size for performance
    
    def get_paginated_response(self, data):
        """
        Return paginated response with metadata for frontend pagination controls.
        """
        return super().get_paginated_response(data)