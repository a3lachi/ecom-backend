from django.db import models
from django.core.validators import EmailValidator


class Contact(models.Model):
    """Model for storing contact form submissions"""
    
    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    # Form fields from screenshot
    name = models.CharField(
        max_length=100,
        help_text="Full name of the person contacting us"
    )
    email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Email address for response"
    )
    subject = models.CharField(
        max_length=200,
        help_text="Subject of the inquiry"
    )
    message = models.TextField(
        help_text="Detailed message or inquiry"
    )
    
    # Admin fields for management
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Current status of the inquiry"
    )
    priority = models.CharField(
        max_length=8,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text="Priority level of the inquiry"
    )
    
    # Tracking fields
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the sender"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/device information"
    )
    
    # Admin response
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes for admin use"
    )
    response_sent = models.BooleanField(
        default=False,
        help_text="Whether a response has been sent"
    )
    response_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when response was sent"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['email']),
            models.Index(fields=['response_sent']),
        ]
        verbose_name = 'Contact Inquiry'
        verbose_name_plural = 'Contact Inquiries'
    
    def __str__(self):
        return f"{self.name} - {self.subject[:50]}"
    
    @property
    def is_new(self):
        """Check if inquiry is new"""
        return self.status == self.Status.NEW
    
    @property
    def is_urgent(self):
        """Check if inquiry is urgent"""
        return self.priority == self.Priority.URGENT
    
    def mark_as_responded(self):
        """Mark inquiry as responded"""
        from django.utils import timezone
        self.response_sent = True
        self.response_date = timezone.now()
        if self.status == self.Status.NEW:
            self.status = self.Status.IN_PROGRESS
        self.save(update_fields=['response_sent', 'response_date', 'status'])
