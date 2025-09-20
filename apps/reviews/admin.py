from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model"""
    
    list_display = [
        'id', 'user', 'product', 'rating_display', 'title_truncated', 
        'is_verified_purchase', 'is_approved', 'helpful_count', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified_purchase', 'is_approved', 'created_at',
        'product__categories'
    ]
    search_fields = [
        'user__username', 'user__email', 'product__name', 'title', 'comment'
    ]
    readonly_fields = [
        'user', 'product', 'is_verified_purchase', 'helpful_count', 
        'created_at', 'updated_at', 'rating_stars'
    ]
    list_editable = ['is_approved']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('user', 'product', 'rating', 'rating_stars', 'title', 'comment')
        }),
        ('Status & Verification', {
            'fields': ('is_verified_purchase', 'is_approved', 'helpful_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        """Display rating with stars"""
        stars = '⭐' * obj.rating
        return format_html(f'<span title="{obj.rating}/5">{stars}</span>')
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'
    
    def title_truncated(self, obj):
        """Display truncated title"""
        if obj.title:
            return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
        return '-'
    title_truncated.short_description = 'Title'
    title_truncated.admin_order_field = 'title'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'product')
    
    actions = ['approve_reviews', 'unapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        """Bulk approve selected reviews"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'Successfully approved {updated} review(s).')
    approve_reviews.short_description = 'Approve selected reviews'
    
    def unapprove_reviews(self, request, queryset):
        """Bulk unapprove selected reviews"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'Successfully unapproved {updated} review(s).')
    unapprove_reviews.short_description = 'Unapprove selected reviews'
