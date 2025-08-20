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
        print("CustomCORSMiddleware initialized")  # Debug log

    def __call__(self, request):
        # Debug logging
        print(f"CORS Middleware: {request.method} {request.path}")
        if request.method == 'OPTIONS':
            print(f"OPTIONS request - Origin: {request.META.get('HTTP_ORIGIN')}")
            print(f"Requested headers: {request.META.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS')}")
        
        # Handle preflight OPTIONS requests
        if request.method == 'OPTIONS':
            response = HttpResponse()
            origin = request.META.get('HTTP_ORIGIN', '*')
            
            # Set CORS headers explicitly
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = (
                'accept, authorization, content-type, user-agent, x-csrftoken, '
                'x-requested-with, x-company-id, cache-control, pragma, expires, '
                'dnt, origin, accept-encoding'
            )
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            
            print(f"Returning OPTIONS response with headers: {response['Access-Control-Allow-Headers']}")
            return response
        
        # Process the request
        response = self.get_response(request)
        
        # Add CORS headers to actual responses
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response