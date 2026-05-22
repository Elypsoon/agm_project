"""
URL configuration for MS-Periodos project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings

def health_check(request):
    """Health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': settings.SERVICE_NAME,
        'version': settings.SERVICE_VERSION,
        'environment': settings.ENVIRONMENT,
    })

def root_view(request):
    """Root endpoint."""
    return JsonResponse({
        'message': f'Welcome to {settings.SERVICE_NAME}',
        'version': settings.SERVICE_VERSION,
        'docs': '/admin/',
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', require_http_methods(["GET"])(health_check)),
    path('', require_http_methods(["GET"])(root_view)),
    path('api/', include('api.urls')),
]
