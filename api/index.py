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
            from urllib.parse import urlparse, parse_qs
            
            # Parse URL to check for docs parameter
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # If docs parameter, serve Swagger docs
            if 'docs' in query_params:
                docs_value = query_params['docs'][0].lower() if query_params['docs'] else ''
                if docs_value in ['true', 'swagger']:
                    return self._serve_swagger_docs()
            
            # If debug=true parameter, show Django setup diagnostics
            if 'debug' in query_params and query_params['debug'][0].lower() == 'true':
                return self._debug_django_setup()
            
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
                    '/api/hello - Basic test endpoint',
                    '/api/index?docs=true - Swagger documentation'
                ],
                'query_params_received': dict(query_params),
                'parsed_path': parsed_url.path,
                'query_string': parsed_url.query,
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
    
    def _debug_django_setup(self):
        """Debug Django setup process step by step"""
        debug_info = {
            'step': 'starting',
            'errors': [],
            'success': [],
            'current_time': str(__import__('datetime').datetime.now())
        }
        
        try:
            # Step 1: Import Django
            debug_info['step'] = 'importing_django'
            import django
            debug_info['success'].append(f'Django imported, version: {django.VERSION}')
            
            # Step 2: Import settings
            debug_info['step'] = 'importing_settings'
            from django.conf import settings
            debug_info['success'].append('Django settings imported')
            debug_info['settings_configured'] = settings.configured
            
            if settings.configured:
                debug_info['success'].append('Django already configured')
                debug_info['installed_apps'] = list(settings.INSTALLED_APPS)
                debug_info['databases'] = settings.DATABASES
            else:
                # Step 3: Try Django setup
                debug_info['step'] = 'django_setup'
                django.setup()
                debug_info['success'].append('Django setup completed')
                debug_info['installed_apps'] = list(settings.INSTALLED_APPS)
                debug_info['databases'] = settings.DATABASES
            
            # Step 4: Try importing apps
            debug_info['step'] = 'importing_apps'
            try:
                from apps.core.models import User
                debug_info['success'].append('Core models imported')
            except Exception as e:
                debug_info['errors'].append(f'Core models import failed: {str(e)}')
            
            debug_info['step'] = 'completed'
            debug_info['final_status'] = 'success'
            
        except Exception as e:
            import traceback
            debug_info['errors'].append(f'Step {debug_info["step"]} failed: {str(e)}')
            debug_info['final_status'] = 'failed'
            debug_info['exception'] = {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(debug_info, indent=2).encode())
    
    def _serve_swagger_docs(self):
        """Serve Swagger documentation"""
        try:
            import django
            from django.conf import settings
            from django.test import RequestFactory
            
            # Initialize Django if not already done
            if not settings.configured:
                django.setup()
            
            # Try importing the Swagger view
            try:
                from drf_spectacular.views import SpectacularSwaggerView
            except ImportError as e:
                raise Exception(f"drf_spectacular not available: {e}")
            
            # Create Django request factory
            factory = RequestFactory()
            request = factory.get('/api/docs/')
            
            # Create the Swagger view
            view = SpectacularSwaggerView()
            view.setup(request)
            
            # Get the response
            response = view.get(request)
            
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
                self.wfile.write(b'No content in response')
                
        except Exception as e:
            import traceback
            
            # Send detailed error response for debugging
            error_response = {
                'error': 'Swagger docs failed in index endpoint',
                'requested_url': self.path,
                'django_configured': False,
                'installed_apps': [],
                'exception': {
                    'type': type(e).__name__,
                    'message': str(e),
                    'traceback': traceback.format_exc()
                }
            }
            
            # Try to get Django configuration info for debugging
            try:
                import django
                from django.conf import settings
                if settings.configured:
                    error_response['django_configured'] = True
                    error_response['installed_apps'] = list(settings.INSTALLED_APPS)
                    error_response['has_drf_spectacular'] = 'drf_spectacular' in settings.INSTALLED_APPS
            except:
                pass
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def _debug_django_setup(self):
        """Debug Django setup process step by step"""
        debug_info = {
            'step': 'starting',
            'errors': [],
            'success': [],
            'current_time': str(__import__('datetime').datetime.now())
        }
        
        try:
            # Step 1: Import Django
            debug_info['step'] = 'importing_django'
            import django
            debug_info['success'].append(f'Django imported, version: {django.VERSION}')
            
            # Step 2: Import settings
            debug_info['step'] = 'importing_settings'
            from django.conf import settings
            debug_info['success'].append('Django settings imported')
            debug_info['settings_configured'] = settings.configured
            
            if settings.configured:
                debug_info['success'].append('Django already configured')
                debug_info['installed_apps'] = list(settings.INSTALLED_APPS)
                debug_info['databases'] = settings.DATABASES
            else:
                # Step 3: Try Django setup
                debug_info['step'] = 'django_setup'
                django.setup()
                debug_info['success'].append('Django setup completed')
                debug_info['installed_apps'] = list(settings.INSTALLED_APPS)
                debug_info['databases'] = settings.DATABASES
            
            # Step 4: Try importing apps
            debug_info['step'] = 'importing_apps'
            try:
                from apps.core.models import User
                debug_info['success'].append('Core models imported')
            except Exception as e:
                debug_info['errors'].append(f'Core models import failed: {str(e)}')
            
            debug_info['step'] = 'completed'
            debug_info['final_status'] = 'success'
            
        except Exception as e:
            import traceback
            debug_info['errors'].append(f'Step {debug_info["step"]} failed: {str(e)}')
            debug_info['final_status'] = 'failed'
            debug_info['exception'] = {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback.format_exc()
            }
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(debug_info, indent=2).encode())