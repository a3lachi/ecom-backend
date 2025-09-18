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
            
            # Simple products endpoint without full Django views
            response = {
                'message': 'Products API endpoint',
                'status': 'working',
                'environment': 'vercel',
                'note': 'This is a simplified test endpoint to verify Django model access',
                'endpoint': '/api/products',
                'methods': ['GET'],
                'description': 'Basic products endpoint for testing Django functionality on Vercel'
            }
            
            # Try to access a Django model if possible
            try:
                from apps.products.models import Product
                product_count = Product.objects.count()
                response['data'] = {
                    'total_products': product_count,
                    'model_access': 'successful'
                }
            except Exception as model_error:
                response['data'] = {
                    'model_access': 'failed',
                    'error': str(model_error)
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            import traceback
            error_response = {
                'error': 'Products endpoint failed',
                'details': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())