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
    'bank_transfers',
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

# For development - expose authorization header in responses
CORS_EXPOSE_HEADERS = [
    'authorization',
    'x-company-id',
]

# REST Framework beállítások
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# Swagger beállítások
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        },
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'example'
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
}

# Database Configuration
# Railway provides DATABASE_URL for PostgreSQL, fallback to SQL Server for local development
import dj_database_url

DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Production/Railway PostgreSQL configuration
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # Local development SQL Server configuration
    DATABASES = {
        'default': {
            'ENGINE': 'mssql',
            'NAME': config('DB_NAME', default='administration'),
            'USER': config('DB_USER', default='sa'),
            'PASSWORD': config('DB_PASSWORD', default='Almafa+123'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='1435'),
            'OPTIONS': {
                'driver': 'ODBC Driver 17 for SQL Server',
            },
        }
    }

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Enable WhiteNoise for static file serving in production
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = config('WHITENOISE_USE_FINDERS', default=False, cast=bool)
WHITENOISE_AUTOREFRESH = DEBUG

USE_TZ = True
TIME_ZONE = 'Europe/Budapest'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# NAV API Configuration (Global Settings)
NAV_API_TIMEOUT = config('NAV_API_TIMEOUT', default=30, cast=int)
NAV_SYNC_BATCH_SIZE = config('NAV_SYNC_BATCH_SIZE', default=100, cast=int)

# Master encryption key for application-level encryption
# This is used to encrypt/decrypt company-specific NAV credentials
# IMPORTANT: In production, set MASTER_ENCRYPTION_KEY environment variable
# For development, using a fixed key to avoid decryption issues
MASTER_ENCRYPTION_KEY = config('MASTER_ENCRYPTION_KEY', default='xzHCWpmz42ogX-qf_3gSYR85YU4hlbWxx8t8bSVMgJ8=')
