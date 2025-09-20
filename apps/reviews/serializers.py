from rest_framework import serializers
from django.db import models
from .models import Review
from apps.orders.models import OrderItem, Order
from apps.products.models import Product


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    rating_stars = serializers.ReadOnlyField()
    
    class Meta:
        model = Review
        fields = (
            'id', 'user_name', 'product', 'rating', 'rating_stars', 'title', 'comment',
            'is_verified_purchase', 'helpful_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user_name', 'rating_stars', 'is_verified_purchase', 'helpful_count', 'created_at', 'updated_at')


class CreateReviewSerializer(serializers.ModelSerializer):
    """Serializer for creating a new review"""
    
    class Meta:
        model = Review
        fields = ('product', 'rating', 'title', 'comment')
        
    def validate_rating(self, value):
        """Ensure rating is between 1 and 5"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_product(self, value):
        """Ensure product exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError("Cannot review inactive product.")
        return value
    
    def validate(self, attrs):
        """Validate that user has purchased and received this product"""
        user = self.context['request'].user
        product = attrs['product']
        
        # Check if user already reviewed this product
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("You have already reviewed this product.")
        
        # Check if user has purchased this product and it's been delivered
        has_delivered_order = OrderItem.objects.filter(
            product=product,
            order__user=user,
            order__status=Order.Status.DELIVERED,
            order__payment_status=Order.PaymentStatus.PAID
        ).exists()
        
        if not has_delivered_order:
            raise serializers.ValidationError(
                "You can only review products that you have purchased and received."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create review with verified purchase status"""
        user = self.context['request'].user
        
        # Create review with verified purchase since validation passed
        review = Review.objects.create(
            user=user,
            is_verified_purchase=True,
            is_approved=False,  # Untill admin review the review
            **validated_data
        )
        
        return review