import os
import json

def app(environ, start_response):
    """Simple test handler to check if environment variables are working"""
    status = '200 OK'
    headers = [('Content-type', 'application/json')]
    start_response(status, headers)
    
    response = {
        'status': 'Test endpoint working',
        'django_settings': os.environ.get('DJANGO_SETTINGS_MODULE', 'NOT_SET'),
        'secret_key_set': bool(os.environ.get('SECRET_KEY')),
        'paypal_client_id_set': bool(os.environ.get('PAYPAL_CLIENT_ID')),
        'paypal_client_secret_set': bool(os.environ.get('PAYPAL_CLIENT_SECRET')),
        'environment_vars': list(os.environ.keys())[:10]  # First 10 env vars
    }
    
    return [json.dumps(response, indent=2).encode('utf-8')]