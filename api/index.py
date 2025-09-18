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
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.vercel'

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            import django
            from django.conf import settings
            
            # Initialize Django if not already done
            if not settings.configured:
                django.setup()
            
            # Simple response showing Django is working
            response = {
                'message': 'Django backend is working!',
                'status': 'operational',
                'environment': 'vercel',
                'available_endpoints': [
                    '/api/health - Health check endpoint',
                    '/api/payment_test - PayPal integration test',
                    '/api/hello - Basic test endpoint'
                ],
                'django_version': list(django.VERSION),
                'settings_module': 'config.settings.vercel',
                'apps_loaded': [
                    'core', 'authentication', 'users', 'products',
                    'cart', 'orders', 'payments', 'wishlist', 
                    'comparison', 'blog'
                ]
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            import traceback
            error_response = {
                'error': 'Django initialization failed',
                'details': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())