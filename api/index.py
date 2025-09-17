import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

try:
    import django
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.http import JsonResponse
    
    # Initialize Django
    if not settings.configured:
        django.setup()
    
    # Create the WSGI application
    application = get_wsgi_application()
    
    # Export for Vercel
    app = application
    
except Exception as e:
    # Fallback error handler
    def app(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'application/json')]
        start_response(status, headers)
        error_response = {
            'error': 'Django initialization failed',
            'details': str(e),
            'type': type(e).__name__
        }
        import json
        return [json.dumps(error_response).encode('utf-8')]