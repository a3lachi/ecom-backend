#!/usr/bin/env python3
import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.append('/Users/farawa/ecom-backend')
django.setup()

from django.contrib.auth import get_user_model
from apps.cart.models import Cart

User = get_user_model()
user = User.objects.get(email='test@example.com')
cart = Cart.objects.get(user=user, status=Cart.Status.ACTIVE)

print(f"🛒 Cart Debug Info:")
print(f"   Items count: {cart.items_count}")
print(f"   Items subtotal: ${cart.items_subtotal}")
print(f"   Discount total: ${cart.discount_total}")
print(f"   Shipping total: ${cart.shipping_total}")
print(f"   Tax total: ${cart.tax_total}")
print(f"   Grand total: ${cart.grand_total}")
print(f"   Currency: {cart.currency}")

print(f"\n📦 Cart Items:")
for item in cart.items.all():
    print(f"   - {item.product_name_snapshot}: qty={item.quantity}, price=${item.unit_price_snapshot}")
    print(f"     Total: ${item.quantity * item.unit_price_snapshot}")