#!/usr/bin/env python3
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test user
user, created = User.objects.get_or_create(
    username='debuguser',
    email='debug@test.com',
    defaults={'password': 'test123'}
)

# Generate tokens
refresh = RefreshToken.for_user(user)
access = refresh.access_token

print("=== TOKEN ANALYSIS ===")
print(f"Refresh Token JTI: {refresh.get('jti')}")
print(f"Access Token JTI: {access.get('jti')}")
print(f"Refresh Token Type: {refresh.get('token_type')}")
print(f"Access Token Type: {access.get('token_type')}")

print("\n=== ACCESS TOKEN PAYLOAD ===")
for key, value in access.payload.items():
    print(f"{key}: {value}")

print("\n=== REFRESH TOKEN PAYLOAD ===") 
for key, value in refresh.payload.items():
    print(f"{key}: {value}")