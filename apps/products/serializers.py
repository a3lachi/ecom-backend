from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Category, Color, Size, Tag, Product, ProductImage, AdditionalInfo
from apps.reviews.serializers import ReviewSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'is_active', 
            'products_count'
        )
        read_only_fields = ('id', 'slug')
    
    @extend_schema_field(serializers.IntegerField)
    def get_products_count(self, obj):
        """Get count of active products in this category"""
        return obj.products.filter(is_active=True).count()


class ColorSerializer(serializers.ModelSerializer):
    """Serializer for Color model"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Color
        fields = ('id', 'name', 'hex_code', 'is_active', 'products_count')
        read_only_fields = ('id',)
    
    @extend_schema_field(serializers.IntegerField)
    def get_products_count(self, obj):
        """Get count of active products with this color"""
        return obj.products.filter(is_active=True).count()


class SizeSerializer(serializers.ModelSerializer):
    """Serializer for Size model"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Size
        fields = ('id', 'name', 'abbreviation', 'sort_order', 'is_active', 'products_count')
        read_only_fields = ('id',)
    
    @extend_schema_field(serializers.IntegerField)
    def get_products_count(self, obj):
        """Get count of active products with this size"""
        return obj.products.filter(is_active=True).count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'is_active', 'products_count')
        read_only_fields = ('id', 'slug')
    
    @extend_schema_field(serializers.IntegerField)
    def get_products_count(self, obj):
        """Get count of active products with this tag"""
        return obj.products.filter(is_active=True).count()
    

class AdditionalInfoSerializer(serializers.ModelSerializer):
    """Serializer for AdditionalInfo model"""
    
    class Meta:
        model = AdditionalInfo
        fields = ("weight", "dimensions", "materials", "other_info")


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model"""
    
    class Meta:
        model = ProductImage
        fields = (
            'id', 'image', 'alt_text', 'is_primary', 'sort_order',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product list view (optimized for performance)"""
    images = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    colors = ColorSerializer(many=True, read_only=True) 
    sizes = SizeSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    # Computed properties
    is_in_stock = serializers.ReadOnlyField()
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'price', 'compare_price',
            'stock_quantity', 'is_featured', 'small_description', 
            'is_active', 'created_at', 'updated_at',
            'primary_image', 'categories', 'colors', 'sizes', 'tags',
            'is_in_stock', 'is_on_sale', 'discount_percentage'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')
    
    
    def get_images(self, obj):
        images = obj.get_all_images()
        return ProductImageSerializer(images, many=True, context=self.context).data


class ProductDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for Product detail view with all information"""
    images = ProductImageSerializer(many=True, read_only=True, source='get_all_images')
    categories = CategorySerializer(many=True, read_only=True)
    colors = ColorSerializer(many=True, read_only=True) 
    sizes = SizeSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    additional_info = AdditionalInfoSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    
    # Computed properties
    is_in_stock = serializers.ReadOnlyField()
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'price', 'compare_price',
            'stock_quantity', 'is_featured', 'small_description', 'large_description',
            'meta_title', 'meta_description', 'is_active', 'created_at', 'updated_at',
            'images', 'primary_image', 'categories', 'colors', 'sizes', 'tags',
            'additional_info', 'reviews', 'is_in_stock', 'is_on_sale', 'discount_percentage'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')
    
    @extend_schema_field(ProductImageSerializer)
    def get_primary_image(self, obj):
        """Get the primary product image"""
        primary_image = obj.primary_image
        if primary_image:
            return ProductImageSerializer(primary_image, context=self.context).data
        return None
    
    @extend_schema_field(ReviewSerializer(many=True))
    def get_reviews(self, obj):
        """Get approved reviews for this product"""
        reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')
        return ReviewSerializer(reviews, many=True, context=self.context).data