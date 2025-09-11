from django.urls import path
from .views import (
    ArticleListView, ArticleDetailView, CategoryListView,
    SubCategoryListView, TagListView
)

urlpatterns = [
    # Articles
    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('articles/<slug:slug>/', ArticleDetailView.as_view(), name='article-detail'),
    
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('subcategories/', SubCategoryListView.as_view(), name='subcategory-list'),
    
    # Tags
    path('tags/', TagListView.as_view(), name='tag-list'),
]