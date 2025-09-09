from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, UserAddress

class UserAddressInline(admin.TabularInline):
    model = UserAddress
    extra = 0
    fields = ('address', 'is_default', 'label')
    readonly_fields = ('created_at',)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'is_staff', 'email_verified_at', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified_at', 'locale', 'timezone')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    inlines = [UserAddressInline]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extended Profile', {
            'fields': ('phone', 'email_verified_at', 'locale', 'timezone')
        }),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'kind', 'line1', 'city', 'country', 'created_at')
    list_filter = ('kind', 'country', 'city')
    search_fields = ('full_name', 'line1', 'city', 'postal_code')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('kind', 'full_name', 'phone')
        }),
        ('Address Details', {
            'fields': ('line1', 'line2', 'city', 'region', 'postal_code', 'country')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'is_default', 'label', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('user__username', 'user__email', 'address__full_name', 'label')
    ordering = ('-created_at',)
