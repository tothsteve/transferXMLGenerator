"""
Django settings for transferXMLGenerator project.

This is the base settings file. For specific environments, use:
- settings_local.py for local development (SQL Server)
- settings_production.py for Railway deployment (PostgreSQL)
"""

import os
from pathlib import Path
from decouple import config
from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent.parent

# Auto-detect environment and use appropriate settings
ENVIRONMENT = config('ENVIRONMENT', default='local')

if ENVIRONMENT == 'production':
    # Import production settings
    from .settings_production import *
else:
    # Import local development settings
    from .settings_local import *

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_extensions',
    'drf_yasg',  # ← Swagger hozzáadása
    'bank_transfers.apps.BankTransfersConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'bank_transfers.middleware.CompanyContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'transferXMLGenerator.urls'

# Templates konfigurációja
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# CORS beállítások
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # Django dev server
]

CORS_ALLOW_CREDENTIALS = True

# Custom headers that need to be allowed
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-company-id',  # Custom header for company context
]

# Allow all standard HTTP methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Django REST Framework beállítások
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT beállítások
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# Swagger UI beállítások
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
}

# NAV encryption key (generated automatically if not set)
def get_or_create_nav_key():
    nav_key = config('NAV_ENCRYPTION_KEY', default=None)
    if not nav_key:
        # Generate a new key if none exists
        key = Fernet.generate_key()
        nav_key = key.decode()
        print(f"Generated new NAV encryption key. Add this to your environment: NAV_ENCRYPTION_KEY={nav_key}")
    return nav_key

NAV_ENCRYPTION_KEY = get_or_create_nav_key()

# Master encryption key for NAV credentials (same as NAV_ENCRYPTION_KEY for compatibility)
MASTER_ENCRYPTION_KEY = NAV_ENCRYPTION_KEY

# NAV API timeout settings
NAV_API_TIMEOUT = config('NAV_API_TIMEOUT', default=30, cast=int)  # 30 second timeout
NAV_MAX_RETRIES = config('NAV_MAX_RETRIES', default=3, cast=int)   # 3 retry attempts

# NAV API Configuration
NAV_API_CONFIG = {
    'base_url': config('NAV_BASE_URL', default='https://api.onlineszamla.nav.gov.hu/invoiceService/v3'),
    'test_base_url': config('NAV_TEST_BASE_URL', default='https://api-test.onlineszamla.nav.gov.hu/invoiceService/v3'),
    'software_info': {
        'software_id': config('NAV_SOFTWARE_ID', default='HU12345678901234567890'),
        'software_name': config('NAV_SOFTWARE_NAME', default='Transfer XML Generator'),
        'software_operation': config('NAV_SOFTWARE_OPERATION', default='ONLINE_SERVICE'),
        'software_main_version': config('NAV_SOFTWARE_VERSION', default='1.0'),
        'software_dev_name': config('NAV_SOFTWARE_DEV_NAME', default='ITCardigan'),
        'software_dev_contact': config('NAV_SOFTWARE_DEV_CONTACT', default='info@itcardigan.hu'),
    }
}

# Language and timezone
LANGUAGE_CODE = 'hu-HU'
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'Europe/Budapest'

# Static files configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'