import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class EmailVerificationToken(models.Model):
    """Token for email verification process"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 24 hours
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    def __str__(self):
        return f"Email verification for {self.user.email}"

class PasswordResetToken(models.Model):
    """Token for password reset process"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 1 hour for security
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    def __str__(self):
        return f"Password reset for {self.user.email}"

class SecurityAttempt(models.Model):
    """Track security attempts (login, registration, etc.) for monitoring"""
    
    class AttemptType(models.TextChoices):
        LOGIN = 'login', 'Login'
        REGISTER = 'register', 'Registration'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        EMAIL_VERIFICATION = 'email_verification', 'Email Verification'
    
    attempt_type = models.CharField(
        max_length=20, 
        choices=AttemptType.choices,
        default=AttemptType.LOGIN
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="User if attempt was successful or user exists"
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    email_attempted = models.EmailField(
        blank=True,
        help_text="Email used in the attempt"
    )
    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        choices=[
            ('invalid_email', 'Invalid Email'),
            ('invalid_password', 'Invalid Password'),
            ('account_locked', 'Account Locked'),
            ('account_inactive', 'Account Inactive'),
            ('too_many_attempts', 'Too Many Attempts'),
            ('validation_error', 'Validation Error'),
            ('invalid_token', 'Invalid Token'),
            ('expired_token', 'Expired Token'),
        ]
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
            models.Index(fields=['attempt_type', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    @classmethod
    def is_ip_blocked(cls, ip_address, attempt_type=None, minutes=15, max_attempts=5):
        """Check if IP should be blocked due to too many failed attempts"""
        since = timezone.now() - timedelta(minutes=minutes)
        query_filter = {
            'ip_address': ip_address,
            'success': False,
            'timestamp__gte': since
        }
        if attempt_type:
            query_filter['attempt_type'] = attempt_type
            
        failed_attempts = cls.objects.filter(**query_filter).count()
        return failed_attempts >= max_attempts
    
    @classmethod
    def is_user_blocked(cls, user, attempt_type=None, minutes=15, max_attempts=3):
        """Check if user should be blocked due to too many failed attempts"""
        since = timezone.now() - timedelta(minutes=minutes)
        query_filter = {
            'user': user,
            'success': False,
            'timestamp__gte': since
        }
        if attempt_type:
            query_filter['attempt_type'] = attempt_type
            
        failed_attempts = cls.objects.filter(**query_filter).count()
        return failed_attempts >= max_attempts
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} {self.get_attempt_type_display()} attempt for {self.email_attempted} from {self.ip_address}"

class UserSession(models.Model):
    """Track active user sessions across devices"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.TextField(help_text="Device/browser information")
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # JWT token information  
    jti = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Refresh token JTI - used for token refresh validation"
    )
    access_jti = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Current access token JTI - updated on token refresh"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['last_activity']),
        ]
        ordering = ['-last_activity']
    
    @property
    def is_expired(self):
        """Check if session is expired (inactive for more than 30 days)"""
        return timezone.now() > self.last_activity + timedelta(days=30)
    
    def deactivate(self):
        """Deactivate this session"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    @classmethod
    def cleanup_expired_sessions(cls):
        """Remove expired sessions"""
        cutoff = timezone.now() - timedelta(days=30)
        return cls.objects.filter(last_activity__lt=cutoff).delete()
    
    def __str__(self):
        return f"{self.user.email} session from {self.ip_address}"
