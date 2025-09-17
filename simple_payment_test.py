#!/usr/bin/env python3
import requests
import json

# Get a valid token
import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.append('/Users/farawa/ecom-backend')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from apps.authentication.models import UserSession

User = get_user_model()
user = User.objects.get(email='test@example.com')
refresh = RefreshToken.for_user(user)

# Create session
session, _ = UserSession.objects.get_or_create(
    user=user,
    session_key='test_session_3',
    defaults={
        'jti': refresh['jti'],
        'access_jti': refresh.access_token['jti'],
        'ip_address': '127.0.0.1',
        'device_info': 'test_script',
        'is_active': True
    }
)

token = str(refresh.access_token)
NGROK_URL = "https://248c50000662.ngrok-free.app"

# Test create payment
url = f"{NGROK_URL}/api/v1/payments/create/"
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

data = {
    'payment_method': 'PAYPAL',
    'shipping_address': {
        'first_name': 'John',
        'last_name': 'Doe',
        'address_line_1': '123 Test Street',
        'city': 'Test City',
        'state_province': 'Test State',
        'postal_code': '12345',
        'country': 'US',
        'phone': '+1234567890'
    }
}

print("🔥 Creating PayPal payment...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")

response = requests.post(url, headers=headers, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")