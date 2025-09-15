from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint


class Wishlist(models.Model):
    """
    User's wishlist containing liked products.
    Each user has one wishlist that contains multiple wishlist items.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Wishlist for {self.user.email if hasattr(self.user, 'email') else self.user.username}"

    @property
    def items_count(self) -> int:
        """Return total number of items in wishlist."""
        return self.items.count()


class WishlistItem(models.Model):
    """
    Individual product in a user's wishlist.
    Tracks when the product was added to wishlist.
    """
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )
    
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Prevent duplicate products in same wishlist
            UniqueConstraint(
                fields=["wishlist", "product"],
                name="unique_wishlist_product"
            ),
        ]
        indexes = [
            models.Index(fields=["wishlist"]),
            models.Index(fields=["product"]),
            models.Index(fields=["added_at"]),
        ]
        ordering = ["-added_at"]  # Most recently added first

    def __str__(self):
        return f"{self.product.name}"

