# E-Commerce Backend API

A modern, scalable Django REST API backend for e-commerce applications built with React frontend in mind. This project provides a complete API-first architecture with comprehensive documentation and production-ready features.

## 🚀 Features

- **RESTful API** - Complete JSON API using Django REST Framework
- **JWT Authentication** - Secure token-based authentication for React frontend
- **PostgreSQL Ready** - Production-ready with PostgreSQL support
- **Auto-generated Documentation** - Swagger UI and ReDoc integration
- **Modular Architecture** - 13+ dedicated Django apps for scalability
- **CORS Configured** - Ready for React frontend integration
- **Environment-specific Settings** - Development, production, and testing configurations
- **API Versioning** - Future-proof API design

## 📋 API Endpoints

### Core Services
- `GET /api/health/` - Health check endpoint
- `GET /api/docs/` - Swagger UI documentation
- `GET /api/redoc/` - ReDoc documentation
- `GET /api/schema/` - OpenAPI 3.0 schema

### E-commerce Modules

#### ✅ Implemented
- **Authentication**: Complete JWT-based auth system with security features
  - Email verification with secure tokens
  - Password reset with IP tracking
  - Login attempt monitoring and rate limiting
  - Multi-device session management
  - Admin dashboard for security monitoring
- **Users**: User management with address system
  - Custom User model with extended fields
  - Multiple address support per user
  - Address types (shipping, billing, other)
  - Default address management

#### 🚧 Coming Soon
- **Products**: Product catalog, categories, search
- **Cart**: Shopping cart management
- **Orders**: Order processing, tracking, history
- **Payments**: Payment gateway integration (Stripe, PayPal)
- **Inventory**: Stock management, warehouse operations
- **Shipping**: Shipping calculations, tracking
- **Reviews**: Product reviews and ratings
- **Coupons**: Discount and promotion system
- **Notifications**: Email/SMS notifications
- **Analytics**: Reporting and analytics

## 🛠️ Technology Stack

- **Backend**: Django 5.2+ with Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT with SimpleJWT
- **API Documentation**: drf-spectacular (Swagger/OpenAPI 3.0)
- **CORS**: django-cors-headers for React integration
- **Environment Management**: python-decouple
- **Testing**: pytest with Django integration

## 🏗️ Project Structure

```
ecom_backend/
├── apps/                          # Django applications
│   ├── authentication/            # 🔐 Complete JWT auth system
│   │   ├── models.py              # Auth models (tokens, sessions, attempts)
│   │   ├── admin.py               # Security monitoring dashboard
│   │   └── migrations/            # Database schema
│   ├── users/                     # 👤 User management system  
│   │   ├── models/                # User models (user, address, relationships)
│   │   │   ├── user.py            # Extended User model
│   │   │   ├── address.py         # Address management
│   │   │   └── user_address.py    # User-address relationships
│   │   ├── admin.py               # User management interface
│   │   ├── tests.py               # Comprehensive test suite
│   │   └── migrations/            # Database schema
│   ├── products/                  # Product catalog API
│   ├── cart/                      # Shopping cart API
│   ├── orders/                    # Order management API
│   ├── payments/                  # Payment processing API
│   ├── inventory/                 # Inventory management API
│   ├── shipping/                  # Shipping calculation API
│   ├── reviews/                   # Product reviews API
│   ├── coupons/                   # Coupon system API
│   ├── notifications/             # Notification system API
│   ├── analytics/                 # Analytics and reporting API
│   └── core/                      # Shared utilities and health check
├── config/                        # Django configuration
│   ├── settings/                  # Environment-specific settings
│   │   ├── base.py               # Base configuration
│   │   ├── development.py        # Development settings
│   │   ├── production.py         # Production settings
│   │   └── testing.py            # Test settings
│   ├── urls.py                   # Main URL configuration
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py                   # ASGI configuration
├── media/                         # User uploaded files
├── docs/                          # API documentation
├── tests/                         # Test files
├── requirements.txt               # Python dependencies
└── manage.py                      # Django management script
```

## 🚦 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ecom-backend.git
   cd ecom-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## 📊 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (Production)
DB_NAME=ecom_backend
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Django Environment
DJANGO_SETTINGS_MODULE=config.settings.development
```

### Settings Environments

- **Development**: Uses SQLite by default, debug enabled
- **Production**: PostgreSQL required, security settings enabled
- **Testing**: In-memory SQLite, optimized for test speed

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run with coverage
pytest --cov=apps

# Run specific app tests
py manage.py test apps.users          # User and address management tests
py manage.py test apps.authentication # Authentication system tests
py manage.py test apps.core           # Core health check tests
```

### Test Coverage
- **Users App**: 8 comprehensive tests covering user-address relationships, default addresses, and edge cases
- **Authentication App**: Security-focused tests for token validation, rate limiting, and session management
- **Integration Tests**: End-to-end authentication flows with proper security validation

### Testing Authentication System

```bash
# Test the complete registration flow
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Get verification token from database (development only)
python manage.py shell -c "
from apps.authentication.models import EmailVerificationToken
token = EmailVerificationToken.objects.last()
print(f'Verification URL: http://localhost:8000/api/v1/auth/verify-email/{token.token}/')
"

# Test login after verification
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

## 🚀 Deployment

### Production Checklist

1. **Environment Variables**
   ```bash
   export DJANGO_SETTINGS_MODULE=config.settings.production
   export SECRET_KEY=your-production-secret-key
   export DEBUG=False
   export ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

2. **Database Setup**
   - Create PostgreSQL database
   - Set database environment variables
   - Run migrations: `python manage.py migrate`

3. **Static Files**
   ```bash
   python manage.py collectstatic
   ```

4. **Security & Authentication**
   - Use HTTPS in production
   - Set secure environment variables
   - Configure CORS_ALLOWED_ORIGINS for your React frontend
   - Set up email service for verification emails (TODO: implement email backend)
   - Configure rate limiting in production (consider Redis for distributed systems)
   - Set up monitoring for failed authentication attempts
   - Configure JWT secret keys securely
   - Set appropriate token expiration times for production

### Docker Support (Coming Soon)

Docker configuration will be added for easy deployment.


## 📝 API Design Principles

- **RESTful**: Standard REST conventions
- **JSON Only**: No HTML template rendering
- **Stateless**: JWT token-based authentication
- **Versioned**: API versioning for backward compatibility
- **Documented**: Auto-generated OpenAPI documentation
- **Paginated**: Consistent pagination across endpoints
- **Filtered**: Comprehensive filtering and search capabilities

## 🔐 Authentication & Security

### JWT Authentication System
- **Access Token**: 15-minute expiry for API requests
- **Refresh Token**: 7-day expiry for token renewal
- **Token Blacklisting**: Secure logout functionality

### Advanced Security Features
- **Email Verification**: Secure token-based email verification (24-hour expiry)
- **Password Reset**: One-time tokens with IP tracking (1-hour expiry)
- **Rate Limiting**: Automatic blocking after failed login attempts
  - IP-based: 5 failed attempts in 15 minutes
  - User-based: 3 failed attempts in 15 minutes
- **Session Management**: Multi-device session tracking with JWT integration
- **Audit Trails**: Complete login attempt logging with failure reasons
- **Admin Security Dashboard**: Monitor and manage security events

### Authentication Models
- **EmailVerificationToken**: Handles email verification workflow
- **PasswordResetToken**: Secure password reset with IP tracking
- **LoginAttempt**: Comprehensive login monitoring and rate limiting
- **UserSession**: Multi-device session management

### Available Authentication Endpoints

#### Registration & Email Verification
- `POST /api/v1/auth/register/` - User registration
- `GET /api/v1/auth/verify-email/{token}/` - Email verification with token
- `POST /api/v1/auth/resend-verification/` - Resend verification email

#### Login & Session Management  
- `POST /api/v1/auth/login/` - User login (returns JWT tokens)
- `POST /api/v1/auth/logout/` - User logout (blacklist refresh token)
- `POST /api/v1/auth/refresh/` - Refresh access token

#### Password Management
- `POST /api/v1/auth/change-password/` - Change password (authenticated users)

### Complete Registration Flow Example

```javascript
// 1. User Registration
const registerResponse = await fetch('/api/v1/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    username: 'johndoe',
    password: 'SecurePassword123',
    password_confirm: 'SecurePassword123',
    first_name: 'John',
    last_name: 'Doe',
    phone: '+212600123456'
  })
});

if (registerResponse.ok) {
  const { message, user } = await registerResponse.json();
  // Show: "Registration successful. Please check your email to verify your account."
  showEmailVerificationMessage();
}

// 2. Email Verification (from email link click)
const verifyResponse = await fetch(`/api/v1/auth/verify-email/${token}/`);
if (verifyResponse.ok) {
  const { access, refresh, user } = await verifyResponse.json();
  // User is now verified and logged in
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  redirectToDashboard();
}

// 3. Login (for verified users)
const loginResponse = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email: 'user@example.com', 
    password: 'SecurePassword123' 
  })
});

const { access, refresh, user } = await loginResponse.json();

// 4. Authenticated API requests
const apiResponse = await fetch('/api/v1/products/', {
  headers: { 'Authorization': `Bearer ${access}` }
});

// 5. Logout
const logoutResponse = await fetch('/api/v1/auth/logout/', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access}`
  },
  body: JSON.stringify({ refresh })
});
```

### Error Handling Examples

```javascript
// Registration validation errors
if (!registerResponse.ok) {
  const errors = await registerResponse.json();
  // Handle field-specific errors
  if (errors.email) console.log('Email error:', errors.email[0]);
  if (errors.username) console.log('Username error:', errors.username[0]);
}

// Rate limiting errors
if (loginResponse.status === 429) {
  const { detail } = await loginResponse.json();
  // "Too many failed login attempts. Please try again later."
  showRateLimitMessage(detail);
}

// Invalid credentials
if (loginResponse.status === 400) {
  const errors = await loginResponse.json();
  if (errors.non_field_errors) {
    // Could be: "Invalid email or password" or "User account is not active"
    showLoginError(errors.non_field_errors[0]);
  }
}
```

## 📈 Performance Features

- **Database Optimization**: Proper indexing and query optimization
- **Caching**: Redis integration ready
- **Pagination**: Efficient large dataset handling
- **Serialization**: Optimized JSON serialization
- **Connection Pooling**: PostgreSQL connection optimization

## 🔍 Health Monitoring

The `/api/health/` endpoint provides:
- API status
- Database connectivity
- System timestamp
- Version information

Perfect for load balancers and monitoring tools.

## 🆘 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Ensure PostgreSQL is running and credentials are correct
# For development, SQLite is used by default
```

**CORS Issues**
```bash
# Add your React app URL to CORS_ALLOWED_ORIGINS in settings
```

**Migration Issues**
```bash
# Reset migrations (development only)
python manage.py migrate --fake-initial
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions or support:
- Create an issue on GitHub
- Check the API documentation at `/api/docs/`
- Review the project wiki

## 🎯 Roadmap

- [ ] Complete all e-commerce endpoints
- [ ] Payment gateway integrations
- [ ] Real-time notifications with WebSockets
- [ ] Advanced search with Elasticsearch
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Performance monitoring
- [ ] Multi-tenant support

---

**Built with ❤️ for modern e-commerce applications**