from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model (admin view)"""
    
    class Meta:
        model = Contact
        fields = (
            'id', 'name', 'email', 'subject', 'message', 'status', 'priority',
            'ip_address', 'user_agent', 'admin_notes', 'response_sent', 
            'response_date', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'ip_address', 'user_agent', 'created_at', 'updated_at'
        )


class CreateContactSerializer(serializers.ModelSerializer):
    """Serializer for creating new contact form submissions"""
    
    class Meta:
        model = Contact
        fields = ('name', 'email', 'subject', 'message')
    
    def validate_name(self, value):
        """Validate name field"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.strip()
    
    def validate_subject(self, value):
        """Validate subject field"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Subject must be at least 5 characters long.")
        return value.strip()
    
    def validate_message(self, value):
        """Validate message field"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value.strip()
    
    def create(self, validated_data):
        """Create contact with request metadata"""
        request = self.context.get('request')
        
        # Get client IP address
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = ''
        if request:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create contact with metadata
        contact = Contact.objects.create(
            ip_address=ip_address,
            user_agent=user_agent,
            **validated_data
        )
        
        return contact


class PublicContactSerializer(serializers.ModelSerializer):
    """Public serializer for contact inquiries (limited fields)"""
    
    class Meta:
        model = Contact
        fields = ('id', 'name', 'subject', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')