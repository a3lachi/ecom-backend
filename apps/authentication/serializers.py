from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import EmailVerificationToken, PasswordResetToken

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = (
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone'
        )
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()
    
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                _("A user with this username already exists.")
            )
        return value.lower()
    
    def create(self, validated_data):
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm', None)
        
        # Create inactive user
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            is_active=False  # User inactive until email verification
        )
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Try to get user by email
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    _('Invalid email or password.'), 
                    code='invalid_credentials'
                )
            
            # Authenticate user
            user = authenticate(username=user.username, password=password)
            
            if not user:
                raise serializers.ValidationError(
                    _('Invalid email or password.'), 
                    code='invalid_credentials'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    _('User account is not active. Please verify your email.'),
                    code='inactive_account'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                _('Must include "email" and "password".'),
                code='required_fields'
            )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 
            'phone', 'is_active', 'email_verified_at', 'date_joined',
            'locale', 'timezone'
        )
        read_only_fields = (
            'id', 'is_active', 'email_verified_at', 'date_joined'
        )

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    
    def validate_token(self, value):
        try:
            verification_token = EmailVerificationToken.objects.get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError(
                _('Invalid verification token.'),
                code='invalid_token'
            )
        
        if not verification_token.is_valid:
            if verification_token.is_used:
                raise serializers.ValidationError(
                    _('This verification token has already been used.'),
                    code='token_used'
                )
            elif verification_token.is_expired:
                raise serializers.ValidationError(
                    _('This verification token has expired. Please request a new one.'),
                    code='token_expired'
                )
        
        return verification_token

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                _('No user found with this email address.'),
                code='user_not_found'
            )
        
        if user.is_active and user.email_verified_at:
            raise serializers.ValidationError(
                _('This email is already verified.'),
                code='already_verified'
            )
        
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value, is_active=True)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        return value.lower()

class PasswordResetSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )
        return attrs
    
    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError(
                _('Invalid reset token.'),
                code='invalid_token'
            )
        
        if not reset_token.is_valid:
            if reset_token.is_used:
                raise serializers.ValidationError(
                    _('This reset token has already been used.'),
                    code='token_used'
                )
            elif reset_token.is_expired:
                raise serializers.ValidationError(
                    _('This reset token has expired. Please request a new one.'),
                    code='token_expired'
                )
        
        return reset_token

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": _("Password fields didn't match.")}
            )
        return attrs
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _('Current password is incorrect.'),
                code='invalid_password'
            )
        return value