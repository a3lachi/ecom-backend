from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    rating_stars = serializers.ReadOnlyField()
    
    class Meta:
        model = Review
        fields = (
            'id', 'user_name', 'rating', 'rating_stars', 'title', 'comment',
            'is_verified_purchase', 'helpful_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user_name', 'rating_stars', 'created_at', 'updated_at')