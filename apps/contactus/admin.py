from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin interface for Contact model"""
    
    list_display = [
        'id', 'name', 'email', 'subject_truncated', 'status_badge', 
        'priority_badge', 'response_sent', 'created_at'
    ]
    list_filter = [
        'status', 'priority', 'response_sent', 'created_at'
    ]
    search_fields = [
        'name', 'email', 'subject', 'message', 'ip_address'
    ]
    readonly_fields = [
        'name', 'email', 'subject', 'message', 'ip_address', 
        'user_agent', 'created_at', 'updated_at'
    ]
    # list_editable = ['status', 'priority']  # Removed since badges can't be edited inline
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'subject', 'message')
        }),
        ('Status & Management', {
            'fields': ('status', 'priority', 'response_sent', 'response_date')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('wide',)
        }),
        ('Tracking Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subject_truncated(self, obj):
        """Display truncated subject"""
        if obj.subject:
            return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
        return '-'
    subject_truncated.short_description = 'Subject'
    subject_truncated.admin_order_field = 'subject'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'NEW': '#dc3545',  # Red
            'IN_PROGRESS': '#ffc107',  # Yellow
            'RESOLVED': '#28a745',  # Green
            'CLOSED': '#6c757d',  # Gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        """Display priority with color coding"""
        colors = {
            'LOW': '#28a745',  # Green
            'MEDIUM': '#ffc107',  # Yellow
            'HIGH': '#fd7e14',  # Orange
            'URGENT': '#dc3545',  # Red
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request)
    
    actions = ['mark_as_new', 'mark_as_in_progress', 'mark_as_resolved', 'mark_as_responded']
    
    def mark_as_new(self, request, queryset):
        """Mark selected contacts as new"""
        updated = queryset.update(status=Contact.Status.NEW)
        self.message_user(request, f'Successfully marked {updated} contact(s) as new.')
    mark_as_new.short_description = 'Mark as new'
    
    def mark_as_in_progress(self, request, queryset):
        """Mark selected contacts as in progress"""
        updated = queryset.update(status=Contact.Status.IN_PROGRESS)
        self.message_user(request, f'Successfully marked {updated} contact(s) as in progress.')
    mark_as_in_progress.short_description = 'Mark as in progress'
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected contacts as resolved"""
        updated = queryset.update(status=Contact.Status.RESOLVED)
        self.message_user(request, f'Successfully marked {updated} contact(s) as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def mark_as_responded(self, request, queryset):
        """Mark selected contacts as responded"""
        now = timezone.now()
        updated = 0
        for contact in queryset:
            if not contact.response_sent:
                contact.response_sent = True
                contact.response_date = now
                if contact.status == Contact.Status.NEW:
                    contact.status = Contact.Status.IN_PROGRESS
                contact.save()
                updated += 1
        self.message_user(request, f'Successfully marked {updated} contact(s) as responded.')
    mark_as_responded.short_description = 'Mark as responded'
