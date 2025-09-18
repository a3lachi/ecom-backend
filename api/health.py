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
            django.setup()
            
            from django.http import HttpRequest
            from apps.core.views import HealthCheckView
            
            # Create a mock request
            request = HttpRequest()
            request.method = 'GET'
            request.path = '/api/health/'
            
            # Get the view response
            view = HealthCheckView()
            response = view.get(request)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Convert Django response to JSON
            if hasattr(response, 'data'):
                self.wfile.write(json.dumps(response.data, indent=2).encode())
            else:
                self.wfile.write(response.content)
            
        except Exception as e:
            import traceback
            error_response = {
                'error': 'Health check failed',
                'details': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())