"""
Health check endpoint for Railway deployment monitoring.
"""

from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """Simple health check endpoint for Railway deployment"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'transferXMLGenerator-backend'
    })
