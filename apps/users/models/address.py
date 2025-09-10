# users/models/address.py
from django.db import models
from django.conf import settings

class Address(models.Model):
    class Kind(models.TextChoices):
        SHIPPING = "shipping", "Shipping"
        BILLING  = "billing", "Billing"
        OTHER    = "other", "Other"

    # Owner of this address
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    
    # Address details
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.SHIPPING)
    full_name = models.CharField(max_length=200)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default="MA")
    phone = models.CharField(max_length=30, blank=True)
    
    # User-specific settings
    is_default = models.BooleanField(default=False)
    label = models.CharField(max_length=50, blank=True, help_text="Custom label like 'Home', 'Work', etc.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["city", "country"]),
        ]

    def __str__(self):
        return f"{self.full_name} — {self.line1}, {self.city}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
