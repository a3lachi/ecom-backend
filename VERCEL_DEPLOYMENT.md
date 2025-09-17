# Vercel Deployment Guide

## Environment Variables Setup

Add these environment variables in your Vercel dashboard:

### Required Environment Variables
```bash
SECRET_KEY=your-long-random-secret-key-here-at-least-50-characters
DJANGO_SETTINGS_MODULE=config.settings.vercel
```

### PayPal Configuration (Optional)
```bash
PAYPAL_BASE=https://api-m.sandbox.paypal.com
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
```

## Files Changed for Vercel

### 1. New Configuration File
- **`config/settings/vercel.py`** - Minimal Vercel-specific settings

### 2. Updated Files
- **`vercel.json`** - Updated to use new settings module
- **`api/index.py`** - Enhanced error handling and database setup
- **`requirements.txt`** - Added `requests` dependency
- **`apps/payments/paypal.py`** - Updated to use `os.environ` instead of `decouple`

## Deployment Steps

1. **Push your changes** to your repository
2. **Set environment variables** in Vercel dashboard
3. **Redeploy** your application

## Testing

Your deployment should now work at: https://a3ecombacken.vercel.app/

Test endpoints:
- `/api/health/` - Health check
- `/api/docs/` - API documentation  
- `/api/v1/auth/` - Authentication endpoints

## Troubleshooting

If you still get errors:
1. Check Vercel function logs
2. Verify environment variables are set
3. Ensure all dependencies are in requirements.txt

## Production Notes

After deployment works:
1. Set `DEBUG = False` in vercel.py
2. Enable HTTPS settings
3. Configure proper SECRET_KEY
4. Set up PostgreSQL database (recommended)