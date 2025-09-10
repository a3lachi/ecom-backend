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
│   ├── __init__.py                # Apps package initializer
│   ├── authentication/            # 🔐 Complete JWT auth system with session management
│   │   ├── models.py              # Auth models (EmailVerificationToken, SecurityAttempt, UserSession)
│   │   ├── serializers.py         # Auth serializers (RegisterSerializer, LoginSerializer, UserSerializer, etc.)
│   │   ├── views.py               # Auth views (RegisterView, LoginView, VerifyEmailView, SessionManagement, etc.)
│   │   ├── authentication.py      # SessionAwareJWTAuthentication - custom JWT auth with session validation
│   │   ├── token_views.py         # SessionAwareTokenRefreshView - session-aware token refresh
│   │   ├── session_utils.py       # Session management utilities (enforce limits, cleanup, security monitoring)
│   │   ├── tasks.py               # Background tasks for session cleanup and maintenance
│   │   ├── urls.py                # Auth URL patterns (/register/, /login/, /verify-email/, /sessions/, etc.)
│   │   ├── admin.py               # Security monitoring dashboard with visual indicators
│   │   ├── tests.py               # Core auth tests (registration, login, logout, security)
│   │   ├── test_session_aware.py  # Session-aware authentication tests
│   │   ├── test_settings.py       # Test-specific settings configuration
│   │   ├── SESSION_INTEGRATION_GUIDE.md # Integration guide for session management
│   │   ├── management/            # Django management commands
│   │   │   ├── __init__.py
│   │   │   └── commands/
│   │   │       ├── __init__.py
│   │   │       └── cleanup_sessions.py # Command for cleaning up expired sessions
│   │   └── migrations/            # Database schema migrations
│   │       ├── 0001_initial.py
│   │       ├── 0002_securityattempt_delete_loginattempt_and_more.py
│   │       └── 0003_usersession_access_jti_alter_usersession_jti.py
│   ├── users/                     # 👤 User management system with addresses
│   │   ├── models/                # User models package
│   │   │   ├── __init__.py        # Models package exports
│   │   │   ├── user.py            # Extended User model with profile relationship
│   │   │   ├── address.py         # Address model with types (shipping/billing/other)
│   │   │   └── user_profile.py    # UserProfile model for extended user data
│   │   ├── serializers.py         # User serializers for API responses
│   │   ├── views.py               # User management views
│   │   ├── admin.py               # User admin interface with address inlines
│   │   ├── tests.py               # User system tests (relationships, addresses, profiles)
│   │   ├── urls.py                # User URL patterns
│   │   └── migrations/            # User model migrations
│   │       ├── 0001_initial.py
│   │       ├── 0002_address_useraddress_user_addresses_and_more.py
│   │       ├── 0003_refactor_user_address_relationship.py
│   │       └── 0004_userprofile_and_more.py
│   ├── products/                  # Product catalog API (structured app ready for implementation)
│   │   ├── models.py              # Product models (placeholder)
│   │   ├── views.py               # Product API views (placeholder)
│   │   ├── admin.py               # Product admin interface (placeholder)
│   │   ├── tests.py               # Product tests (placeholder)
│   │   └── urls.py                # Product URL patterns (placeholder)
│   ├── cart/                      # Shopping cart API (structured app ready for implementation)
│   ├── orders/                    # Order management API (structured app ready for implementation)
│   ├── payments/                  # Payment processing API (structured app ready for implementation)
│   ├── inventory/                 # Inventory management API (structured app ready for implementation)
│   ├── shipping/                  # Shipping calculation API (structured app ready for implementation)
│   ├── reviews/                   # Product reviews API (structured app ready for implementation)
│   ├── coupons/                   # Coupon system API (structured app ready for implementation)
│   ├── notifications/             # Notification system API (structured app ready for implementation)
│   ├── analytics/                 # Analytics and reporting API (structured app ready for implementation)
│   └── core/                      # Shared utilities and health check
│       ├── models.py              # Core shared models
│       ├── views.py               # HealthCheckView with database connectivity check
│       ├── admin.py               # Core admin utilities
│       ├── tests.py               # Core functionality tests
│       └── urls.py                # Health check and core URL patterns
├── config/                        # Django configuration
│   ├── settings/                  # Environment-specific settings
│   │   ├── __init__.py           # Settings package
│   │   ├── base.py               # Base configuration with AUTH_USER_MODEL
│   │   ├── development.py        # Development settings (SQLite, CORS_ALLOW_ALL_ORIGINS)
│   │   ├── production.py         # Production settings (PostgreSQL)
│   │   └── testing.py            # Test settings
│   ├── urls.py                   # Main URL configuration with /api/v1/auth/ routes
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py                   # ASGI configuration
├── media/                         # User uploaded files
├── docs/                          # API documentation  
├── tests/                         # Global test files
├── fixtures/                      # Test data fixtures
├── email_templates/               # Email templates (for verification emails)
├── logs/                          # Application logs
├── scripts/                       # Utility scripts
├── requirements.txt               # Python dependencies (Django 5.2+, DRF, JWT, etc.)
├── pytest.ini                    # Pytest configuration
├── .env                          # Environment variables (not in git)
├── .env.example                  # Environment template
├── db.sqlite3                    # Development database
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

#### Running Authentication Tests

The authentication system has comprehensive test coverage:

```bash
# Run all authentication tests (17 tests)
python manage.py test apps.authentication -v 2

# Run specific test modules
python manage.py test apps.authentication.tests -v 2              # Main auth tests
python manage.py test apps.authentication.test_session_aware -v 2  # Session-aware tests

# Expected test output:
# test_active_session_allows_access ... ok
# test_deactivated_session_blocks_access ... ok  
# test_session_aware_token_refresh ... ok
# test_token_refresh_with_deactivated_session_fails ... ok
# test_successful_registration ... ok
# test_successful_login ... ok
# test_successful_email_verification ... ok
# test_successful_logout ... ok
# test_session_management ... ok
# ... and 8 more tests
# Ran 17 tests in ~10s - OK
```

#### Test Coverage Areas

**Core Authentication Tests** (`apps/authentication/tests.py`):
- ✅ User registration with validation
- ✅ Email verification flow
- ✅ Login with JWT token generation
- ✅ Logout with token blacklisting
- ✅ Password change functionality
- ✅ Session management (list, deactivate)
- ✅ Security attempt logging
- ✅ Rate limiting enforcement

**Session-Aware Authentication Tests** (`apps/authentication/test_session_aware.py`):
- ✅ Active session allows API access
- ✅ Deactivated session blocks API access
- ✅ JWT without session blocks access
- ✅ Session-aware token refresh
- ✅ Token refresh fails with deactivated session
- ✅ Session utilities (stats, enforcement)

#### Manual API Testing

```bash
# 1. Test Registration Flow
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+1234567890"
  }'
# Expected: 201 Created with success message

# 2. Get verification token (development only)
python manage.py shell -c "
from apps.authentication.models import EmailVerificationToken
token = EmailVerificationToken.objects.filter(user__email='test@example.com').last()
print(f'Verification URL: http://localhost:8000/api/v1/auth/verify-email/{token.token}/')
"

# 3. Verify email
curl -X GET "http://localhost:8000/api/v1/auth/verify-email/{TOKEN_FROM_ABOVE}/"
# Expected: 200 OK with verification success message

# 4. Test Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
# Expected: 200 OK with access/refresh tokens

# 5. Test Authenticated Endpoint (save access token from login)
ACCESS_TOKEN="your_access_token_here"
curl -X GET http://localhost:8000/api/v1/auth/sessions/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
# Expected: 200 OK with sessions list

# 6. Test Token Refresh (save refresh token from login)
REFRESH_TOKEN="your_refresh_token_here"
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH_TOKEN\"}"
# Expected: 200 OK with new tokens

# 7. Test Session Management
curl -X POST http://localhost:8000/api/v1/auth/sessions/deactivate-all/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
# Expected: 200 OK with deactivation count

# 8. Test Logout
curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"refresh\": \"$REFRESH_TOKEN\"}"
# Expected: 200 OK with logout success
```

#### Security Testing

```bash
# Test rate limiting (run multiple times quickly)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email": "wrong@example.com", "password": "wrongpass"}'
  echo "Attempt $i"
done
# Expected: First 5 attempts return 400, 6th returns 429 (rate limited)

# Test session enforcement (deactivate session then try API call)
# 1. Login and get tokens
# 2. Get session ID from /api/v1/auth/sessions/
# 3. Deactivate session: POST /api/v1/auth/sessions/{id}/deactivate/
# 4. Try API call with old access token - should return 401

# Test duplicate registration
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser2",
    "password": "SecurePass123!"
  }'
# Expected: 400 Bad Request with email validation error
```

#### Database Verification

```bash
# Check database state after tests
python manage.py shell -c "
from apps.authentication.models import *
from django.contrib.auth import get_user_model

User = get_user_model()
print(f'Users: {User.objects.count()}')
print(f'Sessions: {UserSession.objects.count()}')
print(f'Security Attempts: {SecurityAttempt.objects.count()}')
print(f'Email Tokens: {EmailVerificationToken.objects.count()}')

# Show recent security attempts
for attempt in SecurityAttempt.objects.all()[:5]:
    print(f'{attempt.timestamp}: {attempt.attempt_type} - {attempt.success}')
"
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

### JWT Authentication System with Session Management

Our authentication system combines JWT tokens with sophisticated session management for enhanced security:

- **Access Token**: 15-minute expiry for API requests
- **Refresh Token**: 7-day expiry for token renewal  
- **Session-Aware Authentication**: Custom authentication class that validates both JWT tokens AND active sessions
- **Token Blacklisting**: Secure logout functionality with session deactivation

### Advanced Security Features

#### Multi-Layer Security Protection
- **Email Verification**: Secure UUID-based tokens with 24-hour expiry
- **Rate Limiting**: Progressive blocking system
  - **IP-based**: 5 failed login attempts in 15 minutes
  - **User-based**: 3 failed attempts in 15 minutes
  - **Registration**: 10 attempts per hour per IP
  - **Email Verification**: 10 attempts per 15 minutes per IP

#### Session Management & Device Tracking
- **Multi-Device Sessions**: Track active sessions across devices
- **Session Enforcement**: Force logout by deactivating sessions
- **Device Information**: Store browser/device info and IP addresses  
- **Suspicious Activity Detection**: Monitor logins from multiple IPs
- **Session Limits**: Configurable maximum sessions per user (auto-deactivates oldest)
- **Automatic Cleanup**: Remove expired sessions (30-day default)

#### Security Monitoring & Audit Trails
- **Security Attempt Logging**: Complete audit trail of all authentication attempts
- **Failure Reason Tracking**: Detailed logging of why authentication failed
- **Admin Security Dashboard**: Visual monitoring interface
- **Configurable Security Settings**: Fine-tune security parameters

### Authentication Models

#### Core Models
- **`EmailVerificationToken`**: UUID-based email verification with expiry tracking
- **`SecurityAttempt`**: Comprehensive logging of all security events with failure reasons
- **`UserSession`**: Advanced session management with JWT integration

#### Model Features
```python
# UserSession tracks both refresh and access token JTIs
class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.TextField()  # Browser/device information
    ip_address = models.GenericIPAddressField()
    jti = models.CharField(max_length=255)  # Refresh token JTI
    access_jti = models.CharField(max_length=255)  # Access token JTI
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
```

### Available Authentication Endpoints

#### Registration & Email Verification
- **`POST /api/v1/auth/register/`** - User registration (creates inactive user)
  - Requires: email, username, password, first_name, last_name, phone (optional)
  - Returns: Registration success message and user data
  - Creates EmailVerificationToken automatically
  
- **`GET /api/v1/auth/verify-email/{token}/`** - Email verification with UUID token
  - Activates user account and sets `email_verified_at`
  - Returns: Success message and auto-login tokens (optional)
  
- **`POST /api/v1/auth/resend-verification/`** - Resend verification email
  - Invalidates old tokens and creates new one
  - Rate limited to prevent abuse

#### Login & Session Management  
- **`POST /api/v1/auth/login/`** - User login with session creation
  - Creates UserSession with device tracking
  - Enforces maximum sessions per user
  - Detects suspicious activity (multiple IPs)
  - Returns JWT tokens + user data
  
- **`POST /api/v1/auth/logout/`** - Secure logout
  - Blacklists refresh token
  - Deactivates associated UserSession
  - Graceful error handling
  
- **`POST /api/v1/auth/refresh/`** - Session-aware token refresh  
  - Validates session is still active before refresh
  - Updates session with new JTIs
  - Blocks refresh if session deactivated

#### Advanced Session Management
- **`GET /api/v1/auth/sessions/`** - List all active user sessions
  - Shows device info, IP, creation date, last activity
  - Identifies current session
  
- **`POST /api/v1/auth/sessions/{session_id}/deactivate/`** - Deactivate specific session
  - Force logout on specific device
  - Useful for "logout everywhere except here"
  
- **`POST /api/v1/auth/sessions/deactivate-all/`** - Deactivate all other sessions
  - Keep current session, logout all others
  - Security feature for account compromise
  
- **`GET /api/v1/auth/sessions/stats/`** - Session statistics and security info
  - Active/total session counts
  - Security settings status
  - Session limits and expiry info

#### Password Management
- **`POST /api/v1/auth/change-password/`** - Change password (authenticated users)
  - Requires current password verification
  - Django password validation applied

### Security Configuration

#### Session Security Settings
Configure session behavior in your settings:

```python
# config/settings/base.py
SESSION_SECURITY = {
    'MAX_SESSIONS_PER_USER': 5,          # 0 for unlimited
    'SESSION_EXPIRE_DAYS': 30,           # Auto-cleanup after N days
    'AUTO_CLEANUP_SESSIONS': True,        # Enable automatic cleanup
    'LOG_SESSION_ACTIVITIES': True,       # Enable session activity logging
    'FORCE_LOGOUT_ON_SUSPICIOUS_ACTIVITY': True,  # Security feature
}

# Rate limiting settings (built into models)
SECURITY_ATTEMPT_LIMITS = {
    'LOGIN_IP_MAX_ATTEMPTS': 5,          # Per IP in 15 minutes
    'LOGIN_USER_MAX_ATTEMPTS': 3,        # Per user in 15 minutes
    'REGISTER_IP_MAX_ATTEMPTS': 10,      # Per IP in 60 minutes
    'EMAIL_VERIFICATION_MAX_ATTEMPTS': 10, # Per IP in 15 minutes
}
```

#### Custom Authentication Setup
The system uses `SessionAwareJWTAuthentication` which must be configured:

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.authentication.authentication.SessionAwareJWTAuthentication',
    ),
    # ... other settings
}

# Token refresh uses custom view
# config/urls.py
from apps.authentication.token_views import SessionAwareTokenRefreshView

urlpatterns = [
    path('api/v1/auth/refresh/', SessionAwareTokenRefreshView.as_view(), name='token-refresh'),
    # ... other URLs
]
```

### Complete Authentication Flow Examples

#### 1. Registration & Email Verification Flow

```javascript
// User Registration
const registerResponse = await fetch('/api/v1/auth/register/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    username: 'johndoe',
    password: 'SecurePassword123',
    first_name: 'John',
    last_name: 'Doe',
    phone: '+1234567890'  // Optional
  })
});

if (registerResponse.ok) {
  const { message, user } = await registerResponse.json();
  // Response: "Registration successful. Please check your email to verify your account."
  showEmailVerificationMessage(user.email);
}

// Email Verification (user clicks link in email)
const verifyResponse = await fetch(`/api/v1/auth/verify-email/${token}/`);
if (verifyResponse.ok) {
  const { message } = await verifyResponse.json();
  // Response: "Email verified successfully. You can now log in."
  redirectToLogin();
}

// Resend Verification (if needed)
const resendResponse = await fetch('/api/v1/auth/resend-verification/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' })
});
```

#### 2. Login & Session Management

```javascript
// Login with session tracking
const loginResponse = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email: 'user@example.com', 
    password: 'SecurePassword123' 
  })
});

const { access, refresh, user } = await loginResponse.json();
// System automatically creates UserSession with device info and IP

// Store tokens securely
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);

// Make authenticated requests
const apiResponse = await fetch('/api/v1/some-endpoint/', {
  headers: { 'Authorization': `Bearer ${access}` }
});

// Token refresh (session-aware)
const refreshResponse = await fetch('/api/v1/auth/refresh/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh })
});

if (refreshResponse.ok) {
  const { access: newAccess, refresh: newRefresh } = await refreshResponse.json();
  localStorage.setItem('access_token', newAccess);
  localStorage.setItem('refresh_token', newRefresh);
}
```

#### 3. Advanced Session Management

```javascript
// List all user sessions
const sessionsResponse = await fetch('/api/v1/auth/sessions/', {
  headers: { 'Authorization': `Bearer ${access}` }
});
const sessions = await sessionsResponse.json();
// Returns array with: id, device_info, ip_address, created_at, last_activity, is_current

sessions.forEach(session => {
  console.log(`${session.device_info} from ${session.ip_address} - ${session.is_current ? 'Current' : 'Other'}`);
});

// Deactivate specific session (logout specific device)
const deactivateResponse = await fetch(`/api/v1/auth/sessions/${sessionId}/deactivate/`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access}` }
});

// Logout from all other devices (keep current session)
const logoutAllResponse = await fetch('/api/v1/auth/sessions/deactivate-all/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access}` }
});

// Get session statistics
const statsResponse = await fetch('/api/v1/auth/sessions/stats/', {
  headers: { 'Authorization': `Bearer ${access}` }
});
const stats = await statsResponse.json();
// Returns: active_sessions, total_sessions, max_allowed, expire_days, security_settings

// Secure logout (current session)
const logoutResponse = await fetch('/api/v1/auth/logout/', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access}`
  },
  body: JSON.stringify({ refresh })
});
```

### Comprehensive Error Handling

The authentication system provides detailed error messages for all scenarios:

```javascript
// Registration validation errors
if (!registerResponse.ok) {
  const errors = await registerResponse.json();
  
  // Handle field-specific validation errors
  if (errors.email) {
    // "A user with this email already exists."
    showFieldError('email', errors.email[0]);
  }
  if (errors.username) {
    // "A user with this username already exists."
    showFieldError('username', errors.username[0]);
  }
  if (errors.password) {
    // Django password validation messages
    showFieldError('password', errors.password[0]);
  }
}

// Rate limiting errors (429 Too Many Requests)
if (loginResponse.status === 429) {
  const { detail } = await loginResponse.json();
  const messages = {
    login: "Too many failed login attempts. Please try again later.",
    register: "Too many registration attempts. Please try again later.",
    email_verification: "Too many verification attempts. Please try again later."
  };
  showRateLimitMessage(detail);
}

// Authentication errors (400 Bad Request)
if (loginResponse.status === 400) {
  const errors = await loginResponse.json();
  if (errors.non_field_errors) {
    const errorMessages = {
      'invalid_credentials': 'Invalid email or password.',
      'inactive_account': 'User account is not active. Please verify your email.',
      'required_fields': 'Must include email and password.'
    };
    showLoginError(errors.non_field_errors[0]);
  }
}

// Session-related errors (401 Unauthorized)
if (apiResponse.status === 401) {
  const error = await apiResponse.json();
  
  if (error.detail === 'Session has been terminated') {
    // Session was deactivated - force re-login
    clearTokens();
    redirectToLogin('Your session has been terminated. Please log in again.');
  } else if (error.detail === 'No active sessions found') {
    // No active sessions - re-authentication required
    clearTokens();
    redirectToLogin('Please log in to continue.');
  } else {
    // Token expired or invalid - try refresh
    await attemptTokenRefresh();
  }
}

// Email verification errors
if (verifyResponse.status === 400) {
  const error = await verifyResponse.json();
  const errorMessages = {
    'invalid_token': 'Invalid verification token.',
    'token_used': 'This verification token has already been used.',
    'token_expired': 'This verification token has expired. Please request a new one.'
  };
  showVerificationError(errorMessages[error.code] || error.detail);
}

// Password change errors
if (changePasswordResponse.status === 400) {
  const errors = await changePasswordResponse.json();
  if (errors.current_password) {
    showFieldError('current_password', 'Current password is incorrect.');
  }
  if (errors.new_password) {
    showFieldError('new_password', errors.new_password[0]);
  }
}
```

### Session Management Utilities

```javascript
// Token refresh with session validation
async function attemptTokenRefresh() {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) {
    redirectToLogin();
    return false;
  }

  try {
    const response = await fetch('/api/v1/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    });

    if (response.ok) {
      const { access, refresh: newRefresh } = await response.json();
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', newRefresh);
      return true;
    } else if (response.status === 401) {
      // Session terminated or refresh token invalid
      clearTokens();
      redirectToLogin('Your session has expired. Please log in again.');
      return false;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
    clearTokens();
    redirectToLogin();
    return false;
  }
}

// Session monitoring for security
async function checkActiveSessions() {
  try {
    const response = await fetch('/api/v1/auth/sessions/', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
    });
    
    if (response.ok) {
      const sessions = await response.json();
      const activeSessions = sessions.length;
      const currentSession = sessions.find(s => s.is_current);
      
      // Show session management UI
      updateSessionsUI({
        total: activeSessions,
        current: currentSession,
        others: sessions.filter(s => !s.is_current)
      });
    }
  } catch (error) {
    console.error('Failed to check sessions:', error);
  }
}

// Secure logout with session cleanup
async function secureLogout() {
  const tokens = {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token')
  };

  // Always clear local tokens first
  clearTokens();

  if (tokens.refresh) {
    try {
      await fetch('/api/v1/auth/logout/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${tokens.access}`
        },
        body: JSON.stringify({ refresh: tokens.refresh })
      });
    } catch (error) {
      // Logout endpoint handles errors gracefully
      console.log('Logout cleanup completed');
    }
  }

  redirectToLogin();
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
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