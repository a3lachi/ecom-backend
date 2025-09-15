from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class Comparison(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="User who owns this comparison (null for guest sessions)"
    )
    session_key = models.CharField(
        max_length=40, 
        null=True, 
        blank=True,
        help_text="Session key for guest users"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comparison_comparisons'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name='comparison_user_or_session_required'
            )
        ]

    def __str__(self):
        if self.user:
            return f"Comparison for {self.user.email}"
        return f"Comparison for session {self.session_key}"
    
    @property
    def items_count(self):
        return self.items.count()


class ComparisonItem(models.Model):
    comparison = models.ForeignKey(
        Comparison,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE
    )
    
    # Product snapshot fields to preserve data even if product changes
    product_name_snapshot = models.CharField(max_length=255, default="")
    sku_snapshot = models.CharField(max_length=100, blank=True, default="")
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    compare_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url_snapshot = models.URLField(blank=True, default="")
    description_snapshot = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comparison_items'
        unique_together = ['comparison', 'product']
        indexes = [
            models.Index(fields=['comparison']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.product_name_snapshot} in comparison"
    
    def sync_from_product(self):
        """Update snapshot data from current product data."""
        if self.product:
            self.product_name_snapshot = self.product.name or ""
            self.sku_snapshot = self.product.sku or ""
            self.unit_price_snapshot = self.product.price or Decimal("0.00")
            self.compare_price_snapshot = self.product.compare_price
            self.description_snapshot = self.product.description or ""
            
            # Update image URL if available
            img = self.product.primary_image
            if img and hasattr(img, 'image') and img.image:
                self.image_url_snapshot = getattr(img.image, "url", "")
            else:
                self.image_url_snapshot = ""
    
    def save(self, *args, **kwargs):
        # Auto-sync from product if this is a new item
        if not self.pk:
            self.sync_from_product()
        super().save(*args, **kwargs)
