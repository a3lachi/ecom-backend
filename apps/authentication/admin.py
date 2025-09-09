from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import EmailVerificationToken, PasswordResetToken, LoginAttempt, UserSession

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_short', 'created_at', 'expires_at', 'is_used', 'status_display')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('token', 'created_at', 'expires_at', 'status_display')
    ordering = ('-created_at',)
    
    def token_short(self, obj):
        return str(obj.token)[:8] + "..."
    token_short.short_description = "Token"
    
    def status_display(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ Used</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: blue;">◯ Active</span>')
    status_display.short_description = "Status"

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_short', 'created_at', 'expires_at', 'is_used', 'ip_address', 'status_display')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'ip_address')
    readonly_fields = ('token', 'created_at', 'expires_at', 'status_display')
    ordering = ('-created_at',)
    
    def token_short(self, obj):
        return str(obj.token)[:8] + "..."
    token_short.short_description = "Token"
    
    def status_display(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ Used</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: blue;">◯ Active</span>')
    status_display.short_description = "Status"

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email_attempted', 'user', 'success', 'ip_address', 'timestamp', 'failure_reason', 'success_display')
    list_filter = ('success', 'failure_reason', 'timestamp')
    search_fields = ('email_attempted', 'user__email', 'ip_address', 'user_agent')
    readonly_fields = ('timestamp', 'success_display')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def success_display(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    success_display.short_description = "Result"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'device_short', 'created_at', 'last_activity', 'is_active', 'status_display')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__email', 'user__username', 'ip_address', 'device_info')
    readonly_fields = ('session_key', 'created_at', 'last_activity', 'status_display')
    ordering = ('-last_activity',)
    actions = ['deactivate_sessions']
    
    def device_short(self, obj):
        return obj.device_info[:50] + "..." if len(obj.device_info) > 50 else obj.device_info
    device_short.short_description = "Device"
    
    def status_display(self, obj):
        if not obj.is_active:
            return format_html('<span style="color: gray;">◯ Inactive</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: green;">✓ Active</span>')
    status_display.short_description = "Status"
    
    def deactivate_sessions(self, request, queryset):
        count = 0
        for session in queryset:
            session.deactivate()
            count += 1
        self.message_user(request, f"Deactivated {count} sessions.")
    deactivate_sessions.short_description = "Deactivate selected sessions"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
