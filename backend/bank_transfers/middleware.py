from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import Company, CompanyUser, UserProfile


class CompanyContextMiddleware(MiddlewareMixin):
    """
    Middleware a céges kontextus beállításához
    """
    
    def process_request(self, request):
        """
        Company context is now handled by permission classes
        This middleware is kept for potential future use
        """
        return None