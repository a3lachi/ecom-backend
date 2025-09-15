from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
import uuid


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PROCESSING = "PROCESSING", "Processing"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
        PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially Refunded"

    # Basic order info
    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders"
    )
    
    # Order status
    status = models.CharField(
        max_length=16, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Financial totals
    currency = models.CharField(max_length=3, default="USD")
    items_subtotal = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    discount_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    shipping_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    tax_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    grand_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    
    # Customer notes
    notes = models.TextField(blank=True, help_text="Customer notes for this order")
    
    # Important timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Generate a unique order number."""
        return f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    @property
    def items_count(self):
        """Total number of items in this order."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]
    
    @property
    def is_paid(self):
        """Check if order is fully paid."""
        return self.payment_status == self.PaymentStatus.PAID


class OrderAddress(models.Model):
    class AddressType(models.TextChoices):
        SHIPPING = "SHIPPING", "Shipping"
        BILLING = "BILLING", "Billing"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    address_type = models.CharField(
        max_length=10,
        choices=AddressType.choices
    )
    
    # Address fields
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 country code")
    phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders_addresses'
        unique_together = ['order', 'address_type']
        indexes = [
            models.Index(fields=['order', 'address_type']),
        ]

    def __str__(self):
        return f"{self.get_address_type_display()} for {self.order.order_number}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def formatted_address(self):
        """Return formatted address string."""
        lines = [
            self.full_name,
            self.company if self.company else None,
            self.address_line_1,
            self.address_line_2 if self.address_line_2 else None,
            f"{self.city}, {self.state_province} {self.postal_code}",
            self.country
        ]
        return "\n".join(line for line in lines if line)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        help_text="Product reference (protected to preserve order history)"
    )
    
    # Product variants
    color = models.ForeignKey(
        'products.Color',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    size = models.ForeignKey(
        'products.Size', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Order line details
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    
    # Product snapshot data (preserve pricing/info at time of order)
    product_name_snapshot = models.CharField(max_length=255)
    sku_snapshot = models.CharField(max_length=100, blank=True)
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price_snapshot = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    image_url_snapshot = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders_items'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product_name_snapshot} in {self.order.order_number}"
    
    @property
    def line_total(self):
        """Calculate total for this line item."""
        return self.quantity * self.unit_price_snapshot
    
    def sync_from_product(self):
        """Update snapshot data from current product data."""
        if self.product:
            self.product_name_snapshot = self.product.name or ""
            self.sku_snapshot = self.product.sku or ""
            self.unit_price_snapshot = self.product.price or Decimal("0.00")
            self.compare_price_snapshot = self.product.compare_price
            
            # Update image URL if available
            img = self.product.primary_image
            if img and hasattr(img, 'image') and img.image:
                self.image_url_snapshot = getattr(img.image, "url", "")
            else:
                self.image_url_snapshot = ""
