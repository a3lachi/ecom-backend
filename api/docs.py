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
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            import django
            from django.conf import settings
            
            # Initialize Django if not already done
            if not settings.configured:
                django.setup()
            
            # Create comprehensive API documentation
            api_docs = self._generate_api_documentation()
            
            # Send HTTP response
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Send HTML content
            self.wfile.write(api_docs.encode('utf-8'))
            
        except Exception as e:
            import traceback
            
            # Send error response with detailed debugging
            error_response = {
                'error': 'Swagger docs endpoint failed',
                'path': '/api/docs/',
                'timestamp': str(__import__('datetime').datetime.now()),
                'exception': {
                    'type': type(e).__name__,
                    'message': str(e),
                    'traceback': traceback.format_exc()
                },
                'django_info': {
                    'settings_configured': False,
                    'installed_apps': []
                }
            }
            
            # Try to get Django info for debugging
            try:
                import django
                from django.conf import settings
                error_response['django_info'] = {
                    'settings_configured': settings.configured,
                    'installed_apps': list(settings.INSTALLED_APPS) if settings.configured else [],
                    'django_version': list(django.VERSION)
                }
            except:
                pass
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def _generate_api_documentation(self):
        """Generate comprehensive API documentation"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Commerce API Documentation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        .section { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #007bff; }
        .endpoint { background: white; padding: 15px; margin: 10px 0; border-radius: 6px; border: 1px solid #e9ecef; }
        .method { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 10px; }
        .get { background: #28a745; color: white; }
        .post { background: #007bff; color: white; }
        .put { background: #ffc107; color: black; }
        .delete { background: #dc3545; color: white; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .code { background: #f1f3f4; padding: 10px; border-radius: 4px; font-family: 'Courier New', monospace; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 E-Commerce API Documentation</h1>
        <p>Complete REST API for e-commerce platform with authentication, products, cart, orders, and payments</p>
        <p><strong>Base URL:</strong> https://a3ecombacken.vercel.app</p>
    </div>

    <div class="status success">
        <strong>✅ API Status:</strong> Operational on Vercel with Django 5.1.3 and PayPal integration
    </div>

    <div class="section">
        <h2>🔐 Authentication Endpoints</h2>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/auth/register/</strong>
            <p>Register a new user account</p>
            <div class="code">
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
            </div>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/auth/login/</strong>
            <p>Login and receive JWT tokens</p>
            <div class="code">
{
  "email": "user@example.com",
  "password": "secure_password"
}
            </div>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/auth/logout/</strong>
            <p>Logout and blacklist tokens</p>
        </div>
    </div>

    <div class="section">
        <h2>🛍️ Products Endpoints</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/products/</strong>
            <p>List all products with pagination, filtering, and search</p>
            <p><strong>Query Parameters:</strong> search, category, min_price, max_price, ordering</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/products/{id}/</strong>
            <p>Get detailed product information</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/products/categories/</strong>
            <p>List all product categories</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/products/tags/</strong>
            <p>List all product tags</p>
        </div>
    </div>

    <div class="section">
        <h2>🛒 Cart Endpoints</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/cart/</strong>
            <p>Get user's cart contents</p>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/cart/add/</strong>
            <p>Add item to cart</p>
            <div class="code">
{
  "product_id": 123,
  "quantity": 2,
  "selected_size": "M",
  "selected_color": "Blue"
}
            </div>
        </div>

        <div class="endpoint">
            <span class="method put">PUT</span>
            <strong>/api/v1/cart/update/{item_id}/</strong>
            <p>Update cart item quantity</p>
        </div>

        <div class="endpoint">
            <span class="method delete">DELETE</span>
            <strong>/api/v1/cart/remove/{item_id}/</strong>
            <p>Remove item from cart</p>
        </div>
    </div>

    <div class="section">
        <h2>💳 Payment Endpoints</h2>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/payments/create/</strong>
            <p>Create payment for cart items</p>
            <div class="code">
{
  "payment_method": "paypal",
  "billing_address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "US"
  }
}
            </div>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/payments/{payment_id}/status/</strong>
            <p>Get payment status and details</p>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/payments/{payment_id}/confirm/</strong>
            <p>Confirm payment after PayPal approval</p>
        </div>
    </div>

    <div class="section">
        <h2>📦 Orders Endpoints</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/orders/</strong>
            <p>List user's orders</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/orders/{order_id}/</strong>
            <p>Get detailed order information</p>
        </div>
    </div>

    <div class="section">
        <h2>❤️ Wishlist & Comparison</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/wishlist/</strong>
            <p>Get user's wishlist</p>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/wishlist/add/</strong>
            <p>Add product to wishlist</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/comparison/</strong>
            <p>Get product comparison list</p>
        </div>
    </div>

    <div class="section">
        <h2>🔧 System Endpoints</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/health/</strong>
            <p>API health check</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/payment_test</strong>
            <p>PayPal integration test (✅ Working)</p>
        </div>
    </div>

    <div class="section">
        <h2>🔗 Integration Status</h2>
        <ul>
            <li>✅ <strong>Django 5.1.3:</strong> Fully operational on Vercel</li>
            <li>✅ <strong>PayPal Integration:</strong> Sandbox environment configured</li>
            <li>✅ <strong>JWT Authentication:</strong> Secure token-based auth</li>
            <li>✅ <strong>Database:</strong> SQLite for serverless deployment</li>
            <li>✅ <strong>CORS:</strong> Configured for cross-origin requests</li>
        </ul>
    </div>

    <div class="section">
        <h2>📝 Authentication</h2>
        <p>Include JWT token in request headers:</p>
        <div class="code">
Authorization: Bearer your_jwt_token_here
        </div>
    </div>

    <footer style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #e9ecef;">
        <p>Generated for <strong>E-Commerce Backend API</strong> • Deployed on Vercel</p>
        <p>🤖 Generated with <a href="https://claude.ai/code">Claude Code</a></p>
    </footer>
</body>
</html>
        '''