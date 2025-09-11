# Django E-Commerce Backend Deployment on Vercel

This guide will help you deploy your Django e-commerce backend to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Database**: Set up a PostgreSQL database (recommended: Supabase, Railway, or Neon)

## Step-by-Step Deployment

### 1. Database Setup

Choose one of these PostgreSQL providers:

- **Supabase** (Free tier available): [supabase.com](https://supabase.com)
- **Railway** (Free tier available): [railway.app](https://railway.app)
- **Neon** (Free tier available): [neon.tech](https://neon.tech)

After setting up your database, note down:
- Database name
- Username
- Password
- Host
- Port (usually 5432)

### 2. Deploy to Vercel

1. **Connect Repository**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**:
   In the Vercel dashboard, go to your project > Settings > Environment Variables and add:

   ```env
   SECRET_KEY=your-django-secret-key-here
   DEBUG=False
   POSTGRES_DATABASE=your_database_name
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   POSTGRES_HOST=your_host
   POSTGRES_PORT=5432
   DJANGO_SETTINGS_MODULE=config.settings.production
   ```

   **Generate a SECRET_KEY**:
   ```python
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. **Deploy**:
   - Click "Deploy"
   - Vercel will automatically use the `vercel.json` configuration

### 3. Run Database Migrations

After successful deployment, you need to run migrations. You can do this by:

1. **Using Vercel CLI** (Recommended):
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Login to Vercel
   vercel login
   
   # Link your project
   vercel link
   
   # Run migrations
   vercel exec -- python manage.py migrate
   
   # Create superuser
   vercel exec -- python manage.py createsuperuser
   ```

2. **Or using a temporary migration endpoint** (Remove after use):
   Add this to your `urls.py` temporarily:
   ```python
   from django.http import HttpResponse
   from django.core.management import execute_from_command_line
   
   def migrate_view(request):
       execute_from_command_line(['manage.py', 'migrate'])
       return HttpResponse("Migrations completed")
   
   # Add to urlpatterns temporarily
   path('migrate/', migrate_view),
   ```

### 4. Configure CORS and Domains

Update your production settings (`config/settings/production.py`):

```python
# Replace with your actual domains
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.vercel.app",
    "https://your-custom-domain.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://your-backend-domain.vercel.app",
    "https://your-custom-domain.com",
]

ALLOWED_HOSTS = [
    'your-backend-domain.vercel.app',  # Your Vercel domain
    'your-custom-domain.com',          # Your custom domain (if any)
    '.vercel.app',
    '.now.sh',
]
```

### 5. Test Your Deployment

1. **Health Check**: Visit `https://your-domain.vercel.app/api/health/`
2. **API Documentation**: Visit `https://your-domain.vercel.app/api/docs/`
3. **Admin Panel**: Visit `https://your-domain.vercel.app/admin/`
4. **Products API**: Visit `https://your-domain.vercel.app/api/v1/products/`

## Important Notes

### Static Files
- Static files are collected automatically during build
- Media files uploaded by users will not persist on Vercel (use cloud storage for production)

### Database Considerations
- SQLite is used as fallback for testing
- For production, use PostgreSQL with one of the recommended providers
- Run migrations after each deployment with schema changes

### Environment Variables
- Never commit `.env` files to your repository
- Use Vercel's environment variables for sensitive data
- Set `DEBUG=False` in production

### Monitoring and Logs
- View logs in Vercel dashboard: Project > Functions tab
- Monitor performance and errors in the dashboard

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **Database Connection**: Check your database credentials
3. **Static Files**: Ensure `collectstatic` runs successfully
4. **CORS Errors**: Update `CORS_ALLOWED_ORIGINS` with your frontend domain

### Debug Mode
For debugging, temporarily set `DEBUG=True` in environment variables, but remember to set it back to `False` for production.

## Custom Domain Setup

1. Go to Vercel Dashboard > Your Project > Settings > Domains
2. Add your custom domain
3. Update DNS records as instructed by Vercel
4. Update your Django settings with the new domain

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` set
- [ ] Database credentials secure
- [ ] CORS properly configured
- [ ] CSRF trusted origins set
- [ ] HTTPS enforced (automatic on Vercel)

Your Django e-commerce backend should now be live on Vercel!