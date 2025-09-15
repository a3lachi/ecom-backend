from rest_framework import serializers
from .models import Wishlist, WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at']
        read_only_fields = ['added_at']


class AddToWishlistSerializer(serializers.Serializer):
    product = serializers.IntegerField(help_text="Product ID to add to wishlist")

    def validate_product(self, value):
        from apps.products.models import Product
        try:
            product = Product.objects.get(pk=value)
            if not product.is_active:
                raise serializers.ValidationError("Product is not available")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    items_count = serializers.ReadOnlyField()

    class Meta:
        model = Wishlist
        fields = [
            'id', 'user', 'items_count', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']