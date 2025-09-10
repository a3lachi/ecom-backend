from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, UserProfile

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('kind', 'full_name', 'line1', 'city', 'is_default', 'label')
    readonly_fields = ('created_at', 'updated_at')

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = (
        ('avatar', 'date_of_birth', 'gender'),
        ('bio', 'website'),
        ('loyalty_points', 'membership_tier'),
        ('marketing_emails', 'order_notifications', 'newsletter_subscription'),
        ('facebook_url', 'twitter_url', 'instagram_url'),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_staff', 'email_verified_at', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified_at', 'locale', 'timezone')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    inlines = [UserProfileInline, AddressInline]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extended Profile', {
            'fields': ('phone', 'email_verified_at', 'locale', 'timezone')
        }),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'kind', 'line1', 'city', 'country', 'is_default', 'created_at')
    list_filter = ('kind', 'country', 'city', 'is_default')
    search_fields = ('user__username', 'user__email', 'full_name', 'line1', 'city', 'postal_code')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'kind', 'full_name', 'phone')
        }),
        ('Address Details', {
            'fields': ('line1', 'line2', 'city', 'region', 'postal_code', 'country')
        }),
        ('User Settings', {
            'fields': ('is_default', 'label')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'full_name', 'membership_tier', 'loyalty_points', 
        'marketing_emails', 'created_at'
    )
    list_filter = (
        'membership_tier', 'gender', 'marketing_emails', 
        'order_notifications', 'newsletter_subscription'
    )
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'bio'
    )
    ordering = ('-loyalty_points', '-created_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Details', {
            'fields': ('avatar', 'date_of_birth', 'gender', 'bio', 'website')
        }),
        ('E-commerce Settings', {
            'fields': ('loyalty_points', 'membership_tier')
        }),
        ('Communication Preferences', {
            'fields': ('marketing_emails', 'order_notifications', 'newsletter_subscription')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
