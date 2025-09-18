import os
import sys
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.vercel'

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # TEMPORARY: Always serve Swagger docs to test functionality  
            # Force function update with comment change
            return self._serve_swagger_docs()
            
            # Test PayPal import without full Django setup
            from apps.payments import paypal
            
            # Test environment variables
            paypal_base = os.environ.get('PAYPAL_BASE', 'NOT_SET')
            paypal_client_id = os.environ.get('PAYPAL_CLIENT_ID', 'NOT_SET')
            paypal_secret = os.environ.get('PAYPAL_CLIENT_SECRET', 'NOT_SET')
            
            response = {
                'message': 'PayPal integration test successful!',
                'status': 'working',
                'paypal_config': {
                    'base_url': paypal_base,
                    'client_id_set': paypal_client_id != 'NOT_SET',
                    'client_secret_set': paypal_secret != 'NOT_SET'
                },
                'paypal_functions': [
                    'create_order',
                    'capture_order', 
                    'get_order_details'
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
                'error': 'PayPal integration test failed',
                'details': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def _serve_swagger_docs(self):
        """Serve Swagger documentation using Django's drf-spectacular"""
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
                self.wfile.write(b'Swagger docs content not available')
                
        except Exception as e:
            import traceback
            
            # Send detailed error response for debugging
            error_response = {
                'error': 'Swagger docs failed in payment_test endpoint',
                'path': self.path,
                'exception': {
                    'type': type(e).__name__,
                    'message': str(e),
                    'traceback': traceback.format_exc()
                }
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())