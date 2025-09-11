from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Review(models.Model):
    class Rating(models.IntegerChoices):
        ONE = 1, '⭐'
        TWO = 2, '⭐⭐'
        THREE = 3, '⭐⭐⭐'
        FOUR = 4, '⭐⭐⭐⭐'
        FIVE = 5, '⭐⭐⭐⭐⭐'

    # Foreign keys
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    
    # Review content
    rating = models.PositiveSmallIntegerField(
        choices=Rating.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    
    # Metadata
    is_verified_purchase = models.BooleanField(default=False)  # If user actually bought the product
    is_approved = models.BooleanField(default=True)  # For moderation
    helpful_count = models.PositiveIntegerField(default=0)  # How many found this helpful
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['product', 'rating']),
            models.Index(fields=['user', '-created_at']),
        ]
        # Ensure one review per user per product
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}⭐)"
    
    @property
    def rating_stars(self):
        """Return star representation of rating"""
        return '⭐' * self.rating
