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