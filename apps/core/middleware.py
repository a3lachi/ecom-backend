from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
import threading
import os

# Global flag to track if database is initialized
_db_initialized = threading.Event()

class DatabaseSetupMiddleware:
    """
    Middleware to ensure database is properly initialized for serverless deployments
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only initialize once per serverless instance
        if not _db_initialized.is_set():
            self._ensure_database_setup()
            _db_initialized.set()
        
        response = self.get_response(request)
        return response
    
    def _ensure_database_setup(self):
        """Ensure database tables exist and create superuser if needed"""
        try:
            # Check if database tables exist
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_session';")
                if not cursor.fetchone():
                    # Tables don't exist, run migrations
                    call_command('migrate', verbosity=0, interactive=False)
                    
                    # Create superuser if it doesn't exist
                    User = get_user_model()
                    if not User.objects.filter(is_superuser=True).exists():
                        User.objects.create_superuser(
                            username='admin',
                            email='admin@example.com',
                            password='admin123secure!'
                        )
        except Exception as e:
            # Log error but don't break the application
            print(f"Database setup error: {e}")