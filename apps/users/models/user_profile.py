from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class UserProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
        PREFER_NOT_TO_SAY = 'P', 'Prefer not to say'

    class MembershipTier(models.TextChoices):
        BRONZE = 'bronze', 'Bronze'
        SILVER = 'silver', 'Silver'
        GOLD = 'gold', 'Gold'
        PLATINUM = 'platinum', 'Platinum'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )

    # Personal Information
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=1, 
        choices=Gender.choices, 
        blank=True
    )
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(blank=True)

    # E-commerce Specific Fields
    loyalty_points = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    membership_tier = models.CharField(
        max_length=10,
        choices=MembershipTier.choices,
        default=MembershipTier.BRONZE
    )
    
    # Communication Preferences
    marketing_emails = models.BooleanField(
        default=True,
        help_text="Receive promotional emails and special offers"
    )
    order_notifications = models.BooleanField(
        default=True,
        help_text="Receive notifications about order updates"
    )
    newsletter_subscription = models.BooleanField(
        default=False,
        help_text="Subscribe to weekly newsletter"
    )

    # Social Media Links (optional)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['membership_tier']),
            models.Index(fields=['loyalty_points']),
        ]

    def save(self, *args, **kwargs):
        """Override save to update membership tier based on loyalty points"""
        self._update_membership_tier()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def full_name(self):
        """Get user's full name"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

    @property
    def age(self):
        """Calculate user's age from date of birth"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def can_receive_marketing(self):
        """Check if user can receive marketing communications"""
        return self.marketing_emails and self.user.is_active

    def add_loyalty_points(self, points):
        """Add loyalty points and update membership tier if needed"""
        if points > 0:
            self.loyalty_points += points
            self._update_membership_tier()
            self.save(update_fields=['loyalty_points', 'membership_tier'])

    def deduct_loyalty_points(self, points):
        """Deduct loyalty points (for redemption)"""
        if points > 0 and self.loyalty_points >= points:
            self.loyalty_points -= points
            self._update_membership_tier()
            self.save(update_fields=['loyalty_points', 'membership_tier'])
            return True
        return False

    def _update_membership_tier(self):
        """Update membership tier based on loyalty points"""
        if self.loyalty_points >= 10000:
            self.membership_tier = self.MembershipTier.PLATINUM
        elif self.loyalty_points >= 5000:
            self.membership_tier = self.MembershipTier.GOLD
        elif self.loyalty_points >= 1000:
            self.membership_tier = self.MembershipTier.SILVER
        else:
            self.membership_tier = self.MembershipTier.BRONZE

    def get_loyalty_discount_percentage(self):
        """Get discount percentage based on membership tier"""
        discount_map = {
            self.MembershipTier.BRONZE: 0,
            self.MembershipTier.SILVER: 5,
            self.MembershipTier.GOLD: 10,
            self.MembershipTier.PLATINUM: 15,
        }
        return discount_map.get(self.membership_tier, 0)