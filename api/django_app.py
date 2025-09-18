import os
import sys
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

def handler(request):
    try:
        import django
        from django.conf import settings
        from django.core.handlers.wsgi import WSGIHandler
        from django.http import HttpRequest, HttpResponse
        from django.test import RequestFactory
        
        # Initialize Django if not already done
        if not settings.configured:
            django.setup()
        
        # Get the requested path from query parameters
        path = request.args.get('path', '/')
        
        # Create a proper Django request
        factory = RequestFactory()
        
        if request.method == 'GET':
            django_request = factory.get(path)
        elif request.method == 'POST':
            django_request = factory.post(path, data=request.get_json() or {})
        elif request.method == 'PUT':
            django_request = factory.put(path, data=request.get_json() or {})
        elif request.method == 'DELETE':
            django_request = factory.delete(path)
        else:
            django_request = factory.generic(request.method, path)
        
        # Copy headers from Vercel request to Django request
        for header, value in request.headers.items():
            header_key = f'HTTP_{header.upper().replace("-", "_")}'
            django_request.META[header_key] = value
        
        # Set additional META data
        django_request.META['REQUEST_METHOD'] = request.method
        django_request.META['PATH_INFO'] = path
        django_request.META['QUERY_STRING'] = request.query_string or ''
        django_request.META['CONTENT_TYPE'] = request.headers.get('content-type', '')
        
        # Create Django WSGI handler
        wsgi_handler = WSGIHandler()
        
        # Process the request through Django
        response = wsgi_handler.get_response(django_request)
        
        # Convert Django response to Vercel response format
        if hasattr(response, 'content'):
            content = response.content.decode('utf-8') if isinstance(response.content, bytes) else response.content
        else:
            content = str(response)
        
        # Return Vercel-compatible response
        return HttpResponse(
            content,
            status=response.status_code,
            content_type=response.get('Content-Type', 'text/html')
        )
        
    except Exception as e:
        import traceback
        
        # Detailed error response for debugging
        error_response = {
            'error': 'Django WSGI handler failed',
            'requested_path': request.args.get('path', '/'),
            'method': request.method,
            'headers': dict(request.headers),
            'exception': {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback.format_exc()
            }
        }
        
        return HttpResponse(
            json.dumps(error_response, indent=2),
            content_type='application/json',
            status=500
        )