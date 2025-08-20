"""
Custom CORS middleware to ensure x-company-id header is allowed
This is a backup solution if django-cors-headers continues to have issues
"""

from django.http import HttpResponse
from django.conf import settings


class CustomCORSMiddleware:
    """
    Custom CORS middleware that explicitly allows x-company-id header
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = request.META.get('HTTP_ORIGIN', '*')
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = (
                'accept, authorization, content-type, user-agent, x-csrftoken, '
                'x-requested-with, x-company-id, cache-control, pragma, expires'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        
        # Process the request
        response = self.get_response(request)
        
        # Add CORS headers to actual responses
        if hasattr(request, 'META') and 'HTTP_ORIGIN' in request.META:
            response['Access-Control-Allow-Origin'] = request.META['HTTP_ORIGIN']
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response