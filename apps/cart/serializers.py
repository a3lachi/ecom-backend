from decimal import Decimal
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Cart, CartItem, CartAdjustment, Coupon, CartCoupon


class CartItemSerializer(serializers.ModelSerializer):
    line_subtotal = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()
    color_name = serializers.CharField(source='color.name', read_only=True)
    size_name = serializers.CharField(source='size.name', read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'color', 'size', 'quantity',
            'product_name_snapshot', 'sku_snapshot', 'unit_price_snapshot',
            'compare_price_snapshot', 'image_url', 'line_subtotal',
            'color_name', 'size_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'product_name_snapshot', 'sku_snapshot', 'unit_price_snapshot',
            'compare_price_snapshot', 'image_url', 'line_subtotal'
        ]

    def get_image_url(self, obj):
        if obj.image_url_snapshot:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_url_snapshot)
        return obj.image_url_snapshot


class CartAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartAdjustment
        fields = ['id', 'kind', 'label', 'amount', 'meta', 'created_at']


class CartCouponSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    
    class Meta:
        model = CartCoupon
        fields = ['coupon_code', 'amount_applied', 'applied_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    adjustments = CartAdjustmentSerializer(many=True, read_only=True)
    applied_coupon = CartCouponSerializer(read_only=True)
    items_count = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'session_key', 'status', 'currency',
            'items_subtotal', 'discount_total', 'shipping_total',
            'tax_total', 'grand_total', 'items_count', 'subtotal',
            'items', 'adjustments', 'applied_coupon',
            'created_at', 'updated_at', 'checked_out_at'
        ]
        read_only_fields = [
            'user', 'session_key', 'items_subtotal', 'discount_total',
            'shipping_total', 'tax_total', 'grand_total', 'items_count',
            'subtotal', 'created_at', 'updated_at', 'checked_out_at'
        ]


class AddToCartSerializer(serializers.Serializer):
    product = serializers.IntegerField(help_text="Product ID")
    color = serializers.IntegerField(required=False, allow_null=True, help_text="Color ID (optional)")
    size = serializers.IntegerField(required=False, allow_null=True, help_text="Size ID (optional)")
    quantity = serializers.IntegerField(min_value=1, default=1, help_text="Quantity to add")

    def validate_product(self, value):
        from apps.products.models import Product
        try:
            product = Product.objects.get(pk=value)
            if not product.is_active:
                raise serializers.ValidationError("Product is not available")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")

    def validate_color(self, value):
        if value is not None:
            from apps.products.models import Color
            try:
                Color.objects.get(pk=value)
                return value
            except Color.DoesNotExist:
                raise serializers.ValidationError("Color not found")
        return value

    def validate_size(self, value):
        if value is not None:
            from apps.products.models import Size
            try:
                Size.objects.get(pk=value)
                return value
            except Size.DoesNotExist:
                raise serializers.ValidationError("Size not found")
        return value