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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
        
    def do_PUT(self):
        self._handle_request()
        
    def do_DELETE(self):
        self._handle_request()
    
    def _handle_request(self):
        try:
            import django
            from django.conf import settings
            from django.core.handlers.wsgi import WSGIHandler
            from django.http import HttpRequest
            from django.test import RequestFactory
            
            # Initialize Django if not already done
            if not settings.configured:
                django.setup()
            
            # Parse the URL to get the path and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Get the requested Django path from query parameters or use the full path
            if 'path' in query_params:
                django_path = query_params['path'][0]
            else:
                django_path = parsed_url.path
                
            # Remove /api prefix if present to match Django URLs
            if django_path.startswith('/api'):
                django_path = django_path[4:]
            
            if not django_path:
                django_path = '/'
            
            # Create a proper Django request
            factory = RequestFactory()
            
            if self.command == 'GET':
                django_request = factory.get(django_path)
            elif self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length) if content_length > 0 else b''
                django_request = factory.post(django_path, data=post_data)
            else:
                django_request = factory.generic(self.command, django_path)
            
            # Copy headers
            for header, value in self.headers.items():
                header_key = f'HTTP_{header.upper().replace("-", "_")}'
                django_request.META[header_key] = value
            
            # Set additional META data
            django_request.META['REQUEST_METHOD'] = self.command
            django_request.META['PATH_INFO'] = django_path
            django_request.META['QUERY_STRING'] = parsed_url.query or ''
            
            # Create Django WSGI handler and process request
            wsgi_handler = WSGIHandler()
            response = wsgi_handler.get_response(django_request)
            
            # Send response
            self.send_response(response.status_code)
            
            # Send headers
            for header, value in response.items():
                self.send_header(header, value)
            self.end_headers()
            
            # Send content
            if hasattr(response, 'content'):
                self.wfile.write(response.content)
            
        except Exception as e:
            import traceback
            
            # Send error response
            error_response = {
                'error': 'Django WSGI handler failed',
                'requested_path': self.path,
                'method': self.command,
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