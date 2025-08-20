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
            origin = request.META.get('HTTP_ORIGIN')
            
            # Validate origin for security
            allowed_origins = [
                'https://generous-generosity-production.up.railway.app',
                'https://*.railway.app',
                'https://*.up.railway.app',
                'http://localhost:3000',  # For development
                'http://127.0.0.1:3000',
            ]
            
            # Check if origin is allowed (simplified check)
            origin_allowed = False
            if origin:
                if origin in ['http://localhost:3000', 'http://127.0.0.1:3000']:
                    origin_allowed = True
                elif origin.endswith('.railway.app') or origin.endswith('.up.railway.app'):
                    origin_allowed = True
                elif origin == 'https://generous-generosity-production.up.railway.app':
                    origin_allowed = True
            
            if origin_allowed:
                response['Access-Control-Allow-Origin'] = origin
            else:
                # Fallback for development or unknown origins
                response['Access-Control-Allow-Origin'] = origin or '*'
            
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = (
                'accept, authorization, content-type, user-agent, x-csrftoken, '
                'x-requested-with, x-company-id, cache-control, pragma, expires, '
                'dnt, origin, accept-encoding'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            
            return response
        
        # Process the request
        response = self.get_response(request)
        
        # Add CORS headers to actual responses
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            # Apply same origin validation for actual requests
            if (origin.endswith('.railway.app') or 
                origin.endswith('.up.railway.app') or 
                origin in ['http://localhost:3000', 'http://127.0.0.1:3000']):
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'
        
        return response