from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Comparison, ComparisonItem


class ComparisonItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ComparisonItem
        fields = [
            'id', 'product', 'product_name_snapshot', 'sku_snapshot',
            'unit_price_snapshot', 'compare_price_snapshot', 'image_url',
            'description_snapshot', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'product_name_snapshot', 'sku_snapshot', 'unit_price_snapshot',
            'compare_price_snapshot', 'image_url', 'description_snapshot'
        ]

    def get_image_url(self, obj):
        if obj.image_url_snapshot:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_url_snapshot)
        return obj.image_url_snapshot


class ComparisonSerializer(serializers.ModelSerializer):
    items = ComparisonItemSerializer(many=True, read_only=True)
    items_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Comparison
        fields = [
            'id', 'user', 'session_key', 'items_count',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'session_key', 'items_count',
            'created_at', 'updated_at'
        ]


class AddToComparisonSerializer(serializers.Serializer):
    product = serializers.IntegerField(help_text="Product ID")

    def validate_product(self, value):
        from apps.products.models import Product
        try:
            product = Product.objects.get(pk=value)
            if not product.is_active:
                raise serializers.ValidationError("Product is not available")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")


class RemoveFromComparisonSerializer(serializers.Serializer):
    product = serializers.IntegerField(help_text="Product ID")

    def validate_product(self, value):
        from apps.products.models import Product
        try:
            product = Product.objects.get(pk=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")