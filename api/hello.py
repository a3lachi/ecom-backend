from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {
            'message': 'Hello from Vercel!',
            'status': 'working',
            'path': self.path,
            'django_settings': os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT_SET'),
            'environment_vars_count': len(os.environ)
        }
        self.wfile.write(json.dumps(response, indent=2).encode())