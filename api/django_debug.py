import os
import sys
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        debug_info = {
            'step': 'starting',
            'errors': [],
            'success': [],
            'environment': os.environ.copy()
        }
        
        try:
            # Step 1: Set Django settings
            debug_info['step'] = 'setting_django_settings'
            os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.vercel'
            debug_info['success'].append('Django settings module set')
            
            # Step 2: Import Django
            debug_info['step'] = 'importing_django'
            import django
            debug_info['success'].append(f'Django imported, version: {django.VERSION}')
            
            # Step 3: Try to import settings
            debug_info['step'] = 'importing_settings'
            from django.conf import settings
            debug_info['success'].append('Django settings imported')
            
            # Step 4: Check if Django is configured
            debug_info['step'] = 'checking_configuration'
            if settings.configured:
                debug_info['success'].append('Django already configured')
            else:
                debug_info['success'].append('Django not yet configured')
                
                # Step 5: Setup Django
                debug_info['step'] = 'setting_up_django'
                django.setup()
                debug_info['success'].append('Django setup completed')
            
            # Step 6: Try to import a model
            debug_info['step'] = 'importing_model'
            try:
                from apps.core.models import User
                debug_info['success'].append('Core models imported successfully')
            except Exception as model_error:
                debug_info['errors'].append(f'Model import failed: {str(model_error)}')
            
            debug_info['step'] = 'completed'
            debug_info['final_status'] = 'success'
            
            response = {
                'status': 'Django debug completed',
                'debug_info': debug_info,
                'django_configured': settings.configured,
                'installed_apps': list(settings.INSTALLED_APPS),
                'database_config': settings.DATABASES
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            import traceback
            debug_info['errors'].append(f'Step {debug_info["step"]} failed: {str(e)}')
            debug_info['final_status'] = 'failed'
            
            error_response = {
                'error': 'Django debug failed',
                'debug_info': debug_info,
                'exception_details': {
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