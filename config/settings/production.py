"""
Production settings for Vercel deployment
"""
import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database for production - using SQLite file for Vercel
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/vercel_db.sqlite3',  # Use /tmp for Vercel
    }
}

# PostgreSQL config (commented out temporarily)
# DATABASE_URL = os.environ.get('DATABASE_URL')
# if DATABASE_URL:
#     import dj_database_url
#     DATABASES = {
#         'default': dj_database_url.parse(DATABASE_URL, conn_max_age=0)
#     }
# else:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': os.environ.get('POSTGRES_DATABASE', 'postgres'),
#             'USER': os.environ.get('POSTGRES_USER', 'postgres'),
#             'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
#             'HOST': os.environ.get('POSTGRES_HOST'),
#             'PORT': os.environ.get('POSTGRES_PORT', '5432'),
#             'OPTIONS': {
#                 'sslmode': 'require',
#                 'connect_timeout': 10,
#                 'application_name': 'django-vercel-app',
#             },
#             'CONN_MAX_AGE': 0,  # No connection pooling for serverless
#         }
#     }

# Static files (using Django defaults since we're not serving static files)

# Enable DEBUG temporarily for debugging Vercel deployment
DEBUG = True  # Set to False after deployment works

# Remove problematic middleware for initial deployment
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Media files (using Django defaults since we're not serving media files)

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS settings - disable for initial deployment
SECURE_SSL_REDIRECT = False  # Disabled for Vercel debugging
SECURE_HSTS_SECONDS = 0  # Disabled for debugging
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Cookie security - relaxed for debugging
SESSION_COOKIE_SECURE = False  # Disabled for debugging
CSRF_COOKIE_SECURE = False  # Disabled for debugging
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Make sure you generate a proper secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'temp-secret-key-for-debugging-change-in-production')
# Note: Set SECRET_KEY environment variable in Vercel dashboard

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.vercel.app",  # Replace with your frontend domain
    "https://your-custom-domain.com",  # Replace with your custom domain if any
]

# Allow all origins for development (remove this in production)
CORS_ALLOW_ALL_ORIGINS = True  # Set to False and configure CORS_ALLOWED_ORIGINS properly

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://your-backend-domain.vercel.app",  # Replace with your backend domain
    "https://your-custom-domain.com",  # Replace with your custom domain if any
]

# Override ALLOWED_HOSTS for production
ALLOWED_HOSTS = [
    '.vercel.app',
    '.now.sh',
    'localhost',
    '127.0.0.1',
]

# Custom domain if you have one
if os.environ.get('CUSTOM_DOMAIN'):
    ALLOWED_HOSTS.append(os.environ.get('CUSTOM_DOMAIN'))

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

# Email backend for production (configure with your email service)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.environ.get('EMAIL_HOST')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# For now, use console backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# PayPal Configuration with defaults for Vercel
PAYPAL_BASE = os.environ.get('PAYPAL_BASE', 'https://api-m.sandbox.paypal.com')
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', 'dummy-client-id')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', 'dummy-client-secret')

# Note: Set these environment variables in Vercel dashboard:
# PAYPAL_BASE=https://api-m.sandbox.paypal.com
# PAYPAL_CLIENT_ID=your_sandbox_client_id  
# PAYPAL_CLIENT_SECRET=your_sandbox_client_secret