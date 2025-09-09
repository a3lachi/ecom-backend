# users/models/address.py
from django.db import models

class Address(models.Model):
    class Kind(models.TextChoices):
        SHIPPING = "shipping", "Shipping"
        BILLING  = "billing", "Billing"
        OTHER    = "other", "Other"

    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.SHIPPING)
    full_name = models.CharField(max_length=200)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default="MA")
    phone = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["city", "country"])]

    def __str__(self):
        return f"{self.full_name} — {self.line1}, {self.city}"
