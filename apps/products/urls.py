from django.urls import path
from .views import CategoryListView, ColorListView, SizeListView, TagListView, ProductDetailListView

urlpatterns = [
    # Product endpoints
    path('', ProductDetailListView.as_view(), name='product-detail-list'),
    
    # Category endpoints
    path('categories/', CategoryListView.as_view(), name='category-list'),
    
    # Color endpoints
    path('colors/', ColorListView.as_view(), name='color-list'),
    
    # Size endpoints
    path('sizes/', SizeListView.as_view(), name='size-list'),
    
    # Tag endpoints
    path('tags/', TagListView.as_view(), name='tag-list'),
]
