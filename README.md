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

### E-commerce Modules (Coming Soon)
- **Authentication**: User registration, login, JWT token management
- **Users**: Profile management, address handling
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
│   ├── authentication/            # JWT auth for React
│   ├── users/                     # User profile management
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
python manage.py test apps.core
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

4. **Security**
   - Use HTTPS in production
   - Set secure environment variables
   - Configure CORS_ALLOWED_ORIGINS for your React frontend

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

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication:

- **Access Token**: 15-minute expiry for API requests
- **Refresh Token**: 7-day expiry for token renewal
- **Token Blacklisting**: Secure logout functionality

### Usage Example

```javascript
// Login request
const response = await fetch('/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user', password: 'pass' })
});

const { access, refresh } = await response.json();

// API request with token
const apiResponse = await fetch('/api/v1/products/', {
  headers: { 'Authorization': `Bearer ${access}` }
});
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