from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, unique=True, help_text="Color hex code (e.g., #FF5733)")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]
    
    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="Size name (e.g., S, M, L, XL, 32, 10.5)")
    abbreviation = models.CharField(max_length=5, blank=True, help_text="Short form (e.g., S, M, L)")
    sort_order = models.PositiveIntegerField(default=0, help_text="Sort order for sizes (lower numbers first)")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
        indexes = [models.Index(fields=['sort_order'])]
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="Tag name (e.g., case, wireless, car)")
    slug = models.SlugField(max_length=60, unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['slug'])]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Product(models.Model):
    name = models.CharField(max_length=220)
    slug = models.SlugField(max_length=240, unique=True)
    categories = models.ManyToManyField(Category, related_name="products", blank=True)
    colors = models.ManyToManyField(Color, related_name="products", blank=True)
    sizes = models.ManyToManyField(Size, related_name="products", blank=True)
    tags = models.ManyToManyField(Tag, related_name="products", blank=True)
    small_description = models.TextField(blank=True)
    large_description = models.TextField(blank=True)

    sku = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Stock Keeping Unit - unique product identifier"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Product price in the default currency"
    )
    compare_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Original/compare price for showing discounts"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Available stock quantity"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured products for 'new' section"
    )
    

    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]), 
            models.Index(fields=["is_active", "created_at"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["is_featured", "is_active"]),
            models.Index(fields=["price"]),
            models.Index(fields=["stock_quantity"])
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    @property
    def is_on_sale(self):
        """Check if product is on sale (has compare price)"""
        return self.compare_price is not None and self.compare_price > self.price
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if on sale"""
        if not self.is_on_sale:
            return 0
        discount = self.compare_price - self.price
        return int((discount / self.compare_price) * 100)
    
    @property
    def primary_image(self):
        """Get the primary product image"""
        return self.images.filter(is_primary=True).first()
    
    def get_all_images(self):
        """Get all product images ordered by sort_order"""
        return self.images.all().order_by('sort_order', 'id')


class ProductImage(models.Model):
    """Product images with support for multiple images per product"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='products/images/',
        help_text="Product image file"
    )
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alternative text for accessibility"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary image shown in product listings"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'id']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['product', 'sort_order'])
        ]
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Image for {self.product.name} ({'Primary' if self.is_primary else 'Secondary'})"


class AdditionalInfo(models.Model):
    """
    Extra descriptive info for a product, such as weight,
    dimensions, materials, or miscellaneous notes.
    """

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="additional_info"
    )

    weight = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., '400 g'"
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., '10 x 10 x 15 cm'"
    )
    materials = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g., '60% cotton, 40% polyester'"
    )
    other_info = models.TextField(
        blank=True,
        help_text="Any other product information"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product", "id"]
        indexes = [ models.Index(fields=["product"])]

    def __str__(self):
        return f"Additional Info for {self.product.name}"
