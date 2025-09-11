from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Color, Size, Tag, Product, ProductImage, AdditionalInfo


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'products_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('products_count',)
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products Count'


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code_display', 'is_active', 'products_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'hex_code')
    readonly_fields = ('products_count',)
    
    def hex_code_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; '
            'display: inline-block; margin-right: 10px; border: 1px solid #ccc;"></div>{}',
            obj.hex_code, obj.hex_code
        )
    hex_code_display.short_description = 'Color'
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products Count'


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'sort_order', 'is_active', 'products_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'abbreviation')
    ordering = ('sort_order', 'name')
    readonly_fields = ('products_count',)
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products Count'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'products_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('products_count',)
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products Count'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'sort_order')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


class AdditionalInfoInline(admin.StackedInline):
    model = AdditionalInfo
    extra = 0
    fields = ('weight', 'dimensions', 'materials', 'other_info')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku', 'price', 'compare_price_display', 'stock_quantity', 
        'is_featured', 'is_active', 'discount_display', 'created_at'
    )
    list_filter = (
        'is_active', 'is_featured', 'created_at', 'categories', 'colors', 'sizes'
    )
    search_fields = ('name', 'sku', 'small_description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('categories', 'colors', 'sizes', 'tags')
    readonly_fields = (
        'slug', 'is_in_stock', 'is_on_sale', 'discount_percentage', 
        'primary_image_display', 'created_at', 'updated_at'
    )
    inlines = [ProductImageInline, AdditionalInfoInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'small_description', 'large_description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'discount_percentage')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_in_stock')
        }),
        ('Categorization', {
            'fields': ('categories', 'colors', 'sizes', 'tags')
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured', 'is_on_sale')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('primary_image_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def compare_price_display(self, obj):
        if obj.compare_price:
            return f"${obj.compare_price}"
        return "-"
    compare_price_display.short_description = 'Compare Price'
    
    def discount_display(self, obj):
        if obj.is_on_sale:
            return f"{obj.discount_percentage}%"
        return "-"
    discount_display.short_description = 'Discount'
    
    def primary_image_display(self, obj):
        primary_image = obj.primary_image
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                primary_image.image.url
            )
        return "No Primary Image"
    primary_image_display.short_description = 'Primary Image'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'alt_text', 'is_primary', 'sort_order', 'created_at')
    list_filter = ('is_primary', 'created_at', 'product__categories')
    search_fields = ('product__name', 'alt_text')
    list_editable = ('is_primary', 'sort_order')
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="75" height="75" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(AdditionalInfo)
class AdditionalInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'weight', 'dimensions', 'materials', 'created_at')
    list_filter = ('created_at', 'product__categories')
    search_fields = ('product__name', 'materials', 'other_info')
    readonly_fields = ('created_at', 'updated_at')
