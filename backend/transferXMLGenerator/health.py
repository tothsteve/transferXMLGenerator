"""
Health check endpoint for Railway deployment monitoring.

This module provides a simple health check endpoint that can be used by:
- Railway deployment platform for uptime monitoring
- Load balancers for service availability checks
- Kubernetes health probes
- External monitoring services

The health check endpoint returns:
- HTTP 200 status code
- JSON response with service status, timestamp, and service name
"""

from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """
    Simple health check endpoint for deployment platform monitoring.

    Returns:
        JsonResponse: Health status with structure:
            {
                'status': 'healthy',
                'timestamp': ISO-formatted current timestamp,
                'service': 'transferXMLGenerator-backend'
            }
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'transferXMLGenerator-backend'
    })
