from rest_framework import serializers
from .models import Order, OrderItem, OrderAddress


class OrderAddressSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderAddress
        fields = [
            'address_type', 'first_name', 'last_name', 'full_name',
            'company', 'address_line_1', 'address_line_2', 
            'city', 'state_province', 'postal_code', 'country', 'phone'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.ReadOnlyField()
    color_name = serializers.CharField(source='color.name', read_only=True)
    size_name = serializers.CharField(source='size.name', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'color', 'size', 'color_name', 'size_name',
            'quantity', 'product_name_snapshot', 'sku_snapshot',
            'unit_price_snapshot', 'compare_price_snapshot', 'image_url',
            'line_total', 'created_at'
        ]
    
    def get_image_url(self, obj):
        if obj.image_url_snapshot:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_url_snapshot)
        return obj.image_url_snapshot


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list view - minimal data for performance."""
    items_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'order_number', 'status', 'payment_status', 'currency',
            'grand_total', 'items_count', 'created_at', 'updated_at'
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed order view."""
    items = OrderItemSerializer(many=True, read_only=True)
    addresses = OrderAddressSerializer(many=True, read_only=True)
    items_count = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    is_paid = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'order_number', 'user', 'status', 'payment_status', 'currency',
            'items_subtotal', 'discount_total', 'shipping_total', 
            'tax_total', 'grand_total', 'notes', 'items_count',
            'can_be_cancelled', 'is_paid', 'items', 'addresses',
            'created_at', 'updated_at', 'confirmed_at', 
            'shipped_at', 'delivered_at'
        ]
        read_only_fields = [
            'order_number', 'user', 'status', 'payment_status',
            'items_subtotal', 'discount_total', 'shipping_total',
            'tax_total', 'grand_total', 'created_at', 'updated_at',
            'confirmed_at', 'shipped_at', 'delivered_at'
        ]