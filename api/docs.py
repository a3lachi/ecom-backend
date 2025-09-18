import os
import sys
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            import django
            from django.conf import settings
            from django.test import RequestFactory
            
            # Initialize Django if not already done
            if not settings.configured:
                django.setup()
            
            # Import the Swagger view
            from drf_spectacular.views import SpectacularSwaggerView
            
            # Create Django request factory
            factory = RequestFactory()
            request = factory.get('/api/docs/')
            
            # Create the Swagger view and call get method
            view = SpectacularSwaggerView.as_view()
            response = view(request)
            
            # Send HTTP response
            self.send_response(response.status_code)
            
            # Send headers
            for header, value in response.items():
                self.send_header(header, value)
            self.end_headers()
            
            # Send content
            if hasattr(response, 'content'):
                self.wfile.write(response.content)
            else:
                # Fallback content
                self.wfile.write(b'Swagger docs content not available')
            
        except Exception as e:
            import traceback
            
            # Send error response with detailed debugging
            error_response = {
                'error': 'Swagger docs endpoint failed',
                'path': '/api/docs/',
                'timestamp': str(__import__('datetime').datetime.now()),
                'exception': {
                    'type': type(e).__name__,
                    'message': str(e),
                    'traceback': traceback.format_exc()
                },
                'django_info': {
                    'settings_configured': False,
                    'installed_apps': []
                }
            }
            
            # Try to get Django info for debugging
            try:
                import django
                from django.conf import settings
                error_response['django_info'] = {
                    'settings_configured': settings.configured,
                    'installed_apps': list(settings.INSTALLED_APPS) if settings.configured else [],
                    'django_version': list(django.VERSION)
                }
            except:
                pass
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())