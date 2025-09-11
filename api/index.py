import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Initialize Django
django.setup()

# Create the WSGI application
application = get_wsgi_application()

# Export for Vercel
app = application