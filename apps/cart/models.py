from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, UniqueConstraint

class Cart(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CONVERTED = "CONVERTED", "Converted to order"
        ABANDONED = "ABANDONED", "Abandoned"
        EXPIRED = "EXPIRED", "Expired"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="carts"
    )
    # for guests (store in cookie); also handy to merge guest->user after login
    session_key = models.CharField(max_length=64, blank=True, db_index=True)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    # Optional currency if you support multi-currency; otherwise drop it
    currency = models.CharField(max_length=3, default="USD")

    # (Optional cached totals; recompute server-side when items change)
    items_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self):
        who = self.user_id or self.session_key or "guest"
        return f"Cart #{self.pk} ({who})"

    @property
    def items_count(self) -> int:
        return sum(i.quantity for i in self.items.all())

    @property
    def subtotal(self) -> Decimal:
        return sum(i.line_subtotal for i in self.items.all())

    def recompute_totals(self, save=True):
        """Recompute cached totals from items + adjustments."""
        items_subtotal = sum((i.line_subtotal for i in self.items.all()), Decimal("0.00"))
        discount_total = sum((adj.amount for adj in self.adjustments.filter(kind=CartAdjustment.Kind.DISCOUNT)), Decimal("0.00"))
        shipping_total = sum((adj.amount for adj in self.adjustments.filter(kind=CartAdjustment.Kind.SHIPPING)), Decimal("0.00"))
        tax_total = sum((adj.amount for adj in self.adjustments.filter(kind=CartAdjustment.Kind.TAX)), Decimal("0.00"))
        grand_total = items_subtotal + discount_total + shipping_total + tax_total

        self.items_subtotal = items_subtotal
        self.discount_total = discount_total
        self.shipping_total = shipping_total
        self.tax_total = tax_total
        self.grand_total = grand_total
        if save:
            self.save(update_fields=["items_subtotal", "discount_total", "shipping_total", "tax_total", "grand_total", "updated_at"])



# ---- Individual cart lines -------------------------------------------------
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT, related_name="+")
    # Your catalog uses Color/Size as separate models (no variant table)
    color = models.ForeignKey("products.Color", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    size = models.ForeignKey("products.Size", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    # Snapshots (so cart doesn’t change if product data changes tomorrow)
    product_name_snapshot = models.CharField(max_length=255)
    sku_snapshot = models.CharField(max_length=64)
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url_snapshot = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # Prevent duplicate lines for same product+color+size within one cart
            UniqueConstraint(
                fields=["cart", "product", "color", "size"],
                name="uniq_cart_product_color_size"
            ),
        ]
        indexes = [
            models.Index(fields=["cart"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        opt = []
        if self.color_id: opt.append(self.color.name)
        if self.size_id: opt.append(self.size.name)
        suffix = f" ({', '.join(opt)})" if opt else ""
        return f"{self.product_name_snapshot}{suffix} x{self.quantity}"

    @property
    def line_subtotal(self) -> Decimal:
        return self.unit_price_snapshot * self.quantity

    def sync_from_product(self):
        """
        Fill snapshot fields from the current product.
        Call this when creating/updating the line the first time.
        """
        p = self.product
        self.product_name_snapshot = p.name or ""
        self.sku_snapshot = p.sku or ""
        self.unit_price_snapshot = p.price or Decimal("0.00")
        self.compare_price_snapshot = p.compare_price
        # choose primary image if available
        img = p.primary_image
        if img and hasattr(img, 'image') and img.image:
            # If you serve media at a CDN domain, you can build absolute URLs in the serializer instead
            self.image_url_snapshot = getattr(img.image, "url", "")  # storage provides .url
        else:
            self.image_url_snapshot = ""


class CartAdjustment(models.Model):
    """
    A normalized way to represent discounts, shipping, taxes, or manual credits.
    Store positive or negative amounts (e.g., discounts are negative).
    """
    class Kind(models.TextChoices):
        DISCOUNT = "DISCOUNT", "Discount"
        SHIPPING = "SHIPPING", "Shipping"
        TAX = "TAX", "Tax"
        MANUAL = "MANUAL", "Manual Adjustment"

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="adjustments")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    label = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # discounts are negative
    meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["cart", "kind"])]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.kind} {self.label}: {self.amount}"


# ---- Optional coupon model (code-based discount) --------------------------
class Coupon(models.Model):
    class Type(models.TextChoices):
        PERCENT = "PERCENT", "Percent"
        FIXED = "FIXED", "Fixed amount"

    code = models.CharField(max_length=40, unique=True)
    type = models.CharField(max_length=10, choices=Type.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    is_active = models.BooleanField(default=True)

    # validity windows / limits
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)        # global cap
    max_uses_per_user = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class CartCoupon(models.Model):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name="applied_coupon")
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name="applications")
    amount_applied = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["coupon"])]

