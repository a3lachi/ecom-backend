from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
import uuid


class PaymentMethod(models.Model):
    """Configuration for different payment providers."""
    
    class Provider(models.TextChoices):
        PAYPAL = "PAYPAL", "PayPal"
        CAIXA = "CAIXA", "Caixa"
        BIZUM = "BIZUM", "Bizum"
        BINANCE_PAY = "BINANCE_PAY", "Binance Pay"
    
    provider = models.CharField(
        max_length=20,
        choices=Provider.choices,
        unique=True
    )
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    # Provider-specific configuration (stored as JSON)
    configuration = models.JSONField(
        default=dict,
        help_text="Provider-specific settings like API keys, endpoints, etc."
    )
    
    # Display settings
    logo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_methods'
        ordering = ['sort_order', 'display_name']
    
    def __str__(self):
        return f"{self.display_name} ({self.provider})"


class Payment(models.Model):
    """Main payment record linked to an order."""
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"
        PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially Refunded"
    
    class Type(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        REFUND = "REFUND", "Refund"
        PARTIAL_REFUND = "PARTIAL_REFUND", "Partial Refund"
    
    # Basic payment info
    payment_id = models.CharField(max_length=64, unique=True, db_index=True)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.PROTECT,
        related_name='payments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    
    # Payment details
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.PAYMENT
    )
    
    # Financial details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default="USD")
    
    # Provider-specific data
    provider_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Transaction ID from payment provider"
    )
    provider_response = models.JSONField(
        default=dict,
        help_text="Full response from payment provider"
    )
    
    # Payment flow URLs (for redirects)
    success_url = models.URLField(blank=True)
    cancel_url = models.URLField(blank=True)
    webhook_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    failure_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payments_payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_method', 'status']),
            models.Index(fields=['provider_transaction_id']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = self.generate_payment_id()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_payment_id():
        """Generate a unique payment ID."""
        return f"PAY-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:12].upper()}"
    
    @property
    def is_successful(self):
        """Check if payment is successfully completed."""
        return self.status == self.Status.COMPLETED
    
    @property
    def is_refundable(self):
        """Check if payment can be refunded."""
        return self.status == self.Status.COMPLETED and self.payment_type == self.Type.PAYMENT
    
    @property
    def can_be_cancelled(self):
        """Check if payment can be cancelled."""
        return self.status in [self.Status.PENDING, self.Status.PROCESSING]


class PaymentTransaction(models.Model):
    """Individual transaction events for a payment (for audit trail)."""
    
    class Action(models.TextChoices):
        CREATED = "CREATED", "Created"
        AUTHORIZED = "AUTHORIZED", "Authorized"
        CAPTURED = "CAPTURED", "Captured"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"
        WEBHOOK_RECEIVED = "WEBHOOK_RECEIVED", "Webhook Received"
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Provider response data
    provider_transaction_id = models.CharField(max_length=255, blank=True)
    provider_response = models.JSONField(default=dict)
    
    # Status and metadata
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.payment.payment_id}"


class PaymentWebhook(models.Model):
    """Webhook events received from payment providers."""
    
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks'
    )
    
    # Webhook data
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=255, blank=True)
    payload = models.JSONField()
    
    # Processing status
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Request metadata
    headers = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments_webhooks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_method', 'processed']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.event_type} - {self.payment_method.provider}"
