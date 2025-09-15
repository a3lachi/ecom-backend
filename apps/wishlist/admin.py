from django.contrib import admin
from .models import Wishlist, WishlistItem


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ('added_at',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'items_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'items_count')
    inlines = [WishlistItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'wishlist_user', 'product', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('wishlist__user__username', 'wishlist__user__email', 'product__name')
    readonly_fields = ('added_at',)

    def wishlist_user(self, obj):
        return obj.wishlist.user
    wishlist_user.short_description = 'User'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wishlist__user', 'product')
