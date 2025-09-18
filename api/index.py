import os
import sys
import json
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Set Django settings module - force vercel settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.vercel'

# Initialize database on startup
def ensure_database():
    """Ensure database is set up for serverless environment"""
    try:
        # Skip database setup for now to debug
        print("Skipping database setup for debugging")
        # from django.core.management import execute_from_command_line
        # from django.db import connection
        
        # # Check if tables exist
        # with connection.cursor() as cursor:
        #     cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        #     if not cursor.fetchone():
        #         # Run migrations if no tables exist
        #         execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    except Exception as e:
        print(f"Database setup warning: {e}")

try:
    import django
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    
    # Initialize Django
    django.setup()
    
    # Ensure database is ready
    ensure_database()
    
    # Create the WSGI application
    application = get_wsgi_application()
    
    # Export for Vercel
    app = application
    
except Exception as e:
    print(f"Django initialization error: {e}")
    import traceback
    traceback.print_exc()
    
    # Fallback error handler
    def app(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'application/json')]
        start_response(status, headers)
        error_response = {
            'error': 'Django initialization failed',
            'details': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        return [json.dumps(error_response).encode('utf-8')]