from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from .models import Article, Category, SubCategory, Tag, Comment
from .serializers import (
    ArticleListSerializer, ArticleDetailSerializer, CategorySerializer,
    SubCategorySerializer, TagSerializer, CommentSerializer
)


@extend_schema(
    summary="List all published articles",
    description="Get a list of all published articles with filtering, search, and pagination support",
    tags=["Blog"]
)
class ArticleListView(generics.ListAPIView):
    """List all published articles with filtering and search"""
    serializer_class = ArticleListSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'tags', 'author', 'is_featured']
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['published_at', 'created_at', 'view_count', 'title']
    ordering = ['-published_at']
    
    def get_queryset(self):
        """Return only published articles"""
        return Article.objects.filter(status='published').select_related(
            'author', 'category', 'subcategory'
        ).prefetch_related('tags')


@extend_schema(
    summary="Get article detail",
    description="Get detailed information about a specific published article by its slug",
    tags=["Blog"]
)
class ArticleDetailView(generics.RetrieveAPIView):
    """Get article detail by slug"""
    serializer_class = ArticleDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Return only published articles"""
        return Article.objects.filter(status='published').select_related(
            'author', 'category', 'subcategory'
        ).prefetch_related('tags')


@extend_schema(
    summary="List blog categories",
    description="Get a list of all active blog categories with article counts",
    tags=["Blog"]
)
class CategoryListView(generics.ListAPIView):
    """List all active categories"""
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None
    
    def get_queryset(self):
        """Return only active categories"""
        return Category.objects.filter(is_active=True)


@extend_schema(
    summary="List blog subcategories", 
    description="Get a list of all active blog subcategories",
    tags=["Blog"]
)
class SubCategoryListView(generics.ListAPIView):
    """List all active subcategories"""
    serializer_class = SubCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None
    
    def get_queryset(self):
        """Return only active subcategories"""
        return SubCategory.objects.filter(is_active=True)


@extend_schema(
    summary="List blog tags",
    description="Get a list of all active blog tags",
    tags=["Blog"]
)
class TagListView(generics.ListAPIView):
    """List all active tags"""
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    
    def get_queryset(self):
        """Return only active tags"""
        return Tag.objects.filter(is_active=True)
