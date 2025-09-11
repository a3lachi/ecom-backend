"""
Production settings for Vercel deployment
"""
import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Database for production (you'll need to set this up with your database provider)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DATABASE'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Use SQLite as fallback for testing
if not os.environ.get('POSTGRES_DATABASE'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Static files configuration for Vercel
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_build' / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'staticfiles_build' / 'media'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Make sure you generate a proper secret key
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

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