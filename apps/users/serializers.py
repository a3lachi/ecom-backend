from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Address, UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    age = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        fields = (
            'avatar', 'date_of_birth', 'gender', 'bio', 'website',
            'loyalty_points', 'membership_tier', 'marketing_emails',
            'order_notifications', 'newsletter_subscription',
            'facebook_url', 'twitter_url', 'instagram_url',
            'age', 'full_name', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'loyalty_points', 'membership_tier', 'age', 'full_name',
            'created_at', 'updated_at'
        )


class UserMeSerializer(serializers.ModelSerializer):
    """Serializer for current user's profile information"""
    profile = UserProfileSerializer(read_only=True)
    addresses_count = serializers.SerializerMethodField()
    default_address_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone',
            'email_verified_at', 'locale', 'timezone', 'is_active',
            'date_joined', 'profile', 'addresses_count', 'default_address_id'
        )
        read_only_fields = (
            'id', 'username', 'email_verified_at', 'is_active', 'date_joined'
        )

    def get_addresses_count(self, obj):
        """Get total number of addresses for the user"""
        return obj.addresses.count()

    def get_default_address_id(self, obj):
        """Get the ID of user's default address"""
        default_address = obj.default_address
        return default_address.id if default_address else None


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model"""

    class Meta:
        model = Address
        fields = (
            'id', 'kind', 'full_name', 'line1', 'line2', 'city',
            'region', 'postal_code', 'country', 'phone', 'is_default',
            'label', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, data):
        """Ensure user can only have one default address"""
        user = self.context['request'].user
        
        # If setting as default, check if user already has a default
        if data.get('is_default', False):
            existing_default = Address.objects.filter(
                user=user, is_default=True
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_default.exists():
                # This will be handled by the model's save method
                pass
        
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user basic information"""
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone', 'locale', 'timezone'
        )
        
    def validate_phone(self, value):
        """Validate phone number format"""
        if value and not value.startswith('+'):
            # You could add more comprehensive phone validation here
            pass
        return value


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested use"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name')

    def get_full_name(self, obj):
        """Get user's full name or username as fallback"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username