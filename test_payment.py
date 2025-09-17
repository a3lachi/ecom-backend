#!/usr/bin/env python3
"""
Test script for PayPal payment system using ngrok tunnel.
"""

import os
import django
import sys
import requests
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.append('/Users/farawa/ecom-backend')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from apps.cart.models import Cart, CartItem
from apps.products.models import Product
from apps.authentication.models import UserSession

User = get_user_model()

# ngrok URL
NGROK_URL = "https://248c50000662.ngrok-free.app"

def create_test_user_and_token():
    """Create or get test user and get JWT token via API."""
    try:
        user = User.objects.get(email='test@example.com')
        print(f"Using existing user: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        print(f"Created new user: {user.email}")
    
    # Get JWT token via authentication API
    auth_url = f"{NGROK_URL}/api/v1/auth/login/"
    auth_data = {
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    
    print(f"Getting token from: {auth_url}")
    response = requests.post(auth_url, json=auth_data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access')
        print(f"✅ Got access token successfully")
        return user, access_token
    else:
        print(f"❌ Failed to get token: {response.status_code} - {response.text}")
        # Fallback: Generate token directly and create session
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Create user session for authentication
        session = UserSession.objects.create(
            user=user,
            jti=refresh['jti'],
            access_jti=refresh.access_token['jti'],
            session_key='test_session',
            ip_address='127.0.0.1',
            device_info='test_script',
            is_active=True
        )
        print(f"✅ Created user session: {session.id}")
        
        print(f"Using fallback token generation")
        return user, access_token

def create_test_cart(user):
    """Create a test cart with items."""
    # Get or create a product
    try:
        product = Product.objects.first()
        if not product:
            print("No products found. Please create a product first.")
            return None
    except:
        print("Could not access products. Make sure products app is set up.")
        return None
    
    # Create cart
    cart, created = Cart.objects.get_or_create(
        user=user,
        status=Cart.Status.ACTIVE,
        defaults={
            'currency': 'USD'
        }
    )
    
    if created or cart.items.count() == 0:
        # Add item to cart
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=2,
            product_name_snapshot=product.name,
            sku_snapshot=getattr(product, 'sku', 'TEST-SKU'),
            unit_price_snapshot=Decimal('29.99'),
        )
        cart.refresh_from_db()
        print(f"Created test cart with {cart.items_count} items")
    else:
        print(f"Using existing cart with {cart.items_count} items")
    
    return cart

def test_payment_methods(token):
    """Test the payment methods endpoint."""
    url = f"{NGROK_URL}/api/v1/payments/methods/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n=== Testing Payment Methods Endpoint ===")
    print(f"URL: {url}")
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.status_code == 200

def test_create_payment(token):
    """Test the create payment endpoint."""
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
    
    print(f"\n=== Testing Create Payment Endpoint ===")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 201:
        response_data = response.json()
        approval_url = response_data.get('approval_url')
        if approval_url:
            print(f"\n🎉 SUCCESS! PayPal payment created successfully!")
            print(f"📋 Payment ID: {response_data.get('payment_id')}")
            print(f"💰 Amount: {response_data.get('amount')} {response_data.get('currency')}")
            print(f"🔗 Approval URL: {approval_url}")
            print(f"\n📱 To complete the payment, open this URL in your browser:")
            print(f"   {approval_url}")
            print(f"\n✅ This URL will redirect back to:")
            print(f"   Success: {NGROK_URL}/api/v1/payments/paypal/success/")
            print(f"   Cancel:  {NGROK_URL}/api/v1/payments/paypal/cancel/")
    
    return response.status_code == 201

def main():
    print("🚀 Starting PayPal Payment System Test")
    print(f"🌐 Using ngrok URL: {NGROK_URL}")
    
    # Create test user and get token
    print("\n📝 Setting up test user...")
    user, token = create_test_user_and_token()
    
    # Create test cart
    print("\n🛒 Setting up test cart...")
    cart = create_test_cart(user)
    if not cart:
        print("❌ Could not create test cart. Exiting.")
        return
    
    # Test payment methods
    print("\n🔍 Testing payment methods endpoint...")
    if not test_payment_methods(token):
        print("❌ Payment methods test failed. Exiting.")
        return
    
    # Test create payment
    print("\n💳 Testing create payment endpoint...")
    success = test_create_payment(token)
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("🎯 Next steps:")
        print("   1. Click the PayPal approval URL above")
        print("   2. Complete the payment in PayPal sandbox")
        print("   3. You'll be redirected back to the success callback")
    else:
        print("\n❌ Payment creation test failed.")

if __name__ == '__main__':
    main()