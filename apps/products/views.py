from rest_framework import generics
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.db.models import Q

from .models import Category, Color, Size, Tag, Product
from .serializers import CategorySerializer, ColorSerializer, SizeSerializer, TagSerializer, ProductListSerializer


class CategoryListView(generics.ListAPIView):
    """
    Get list of all active categories
    """
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Disable pagination for categories
    
    def get_queryset(self):
        """Return only active categories ordered by name"""
        return Category.objects.filter(is_active=True).order_by('name')
    
    @extend_schema(
        summary="List Categories",
        description="Retrieve all active categories with product counts. No authentication required.",
        responses={
            200: OpenApiResponse(
                description="List of categories",
                response=CategorySerializer(many=True)
            )
        },
        tags=["Products"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ColorListView(generics.ListAPIView):
    """
    Get list of all active colors
    """
    serializer_class = ColorSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Disable pagination for colors
    
    def get_queryset(self):
        """Return only active colors ordered by name"""
        return Color.objects.filter(is_active=True).order_by('name')
    
    @extend_schema(
        summary="List Colors",
        description="Retrieve all active colors with product counts. No authentication required.",
        responses={
            200: OpenApiResponse(
                description="List of colors",
                response=ColorSerializer(many=True)
            )
        },
        tags=["Products"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SizeListView(generics.ListAPIView):
    """
    Get list of all active sizes
    """
    serializer_class = SizeSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Disable pagination for sizes
    
    def get_queryset(self):
        """Return only active sizes ordered by sort_order, then name"""
        return Size.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    @extend_schema(
        summary="List Sizes",
        description="Retrieve all active sizes with product counts, ordered by sort_order. No authentication required.",
        responses={
            200: OpenApiResponse(
                description="List of sizes",
                response=SizeSerializer(many=True)
            )
        },
        tags=["Products"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TagListView(generics.ListAPIView):
    """
    Get list of all active tags
    """
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Disable pagination for tags
    
    def get_queryset(self):
        """Return only active tags ordered by name"""
        return Tag.objects.filter(is_active=True).order_by('name')
    
    @extend_schema(
        summary="List Tags",
        description="Retrieve all active tags with product counts, ordered alphabetically. No authentication required.",
        responses={
            200: OpenApiResponse(
                description="List of tags",
                response=TagSerializer(many=True)
            )
        },
        tags=["Products"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductListView(generics.ListAPIView):
    """
    Get list of products with filtering and search
    """
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Return active products with optional filtering"""
        queryset = Product.objects.filter(is_active=True).prefetch_related(
            'categories', 'colors', 'sizes', 'tags', 'images'
        ).order_by('-created_at')
        
        # # Filter by category slug
        # category = self.request.query_params.get('category', None)
        # if category:
        #     queryset = queryset.filter(categories__slug=category, categories__is_active=True)
        
        # # Filter by color name
        # color = self.request.query_params.get('color', None)
        # if color:
        #     queryset = queryset.filter(colors__name__iexact=color, colors__is_active=True)
        
        # # Filter by size name
        # size = self.request.query_params.get('size', None)
        # if size:
        #     queryset = queryset.filter(sizes__name__iexact=size, sizes__is_active=True)
        
        # # Filter by tag slug
        # tag = self.request.query_params.get('tag', None)
        # if tag:
        #     queryset = queryset.filter(tags__slug=tag, tags__is_active=True)
        
        # # Filter by featured products
        # featured = self.request.query_params.get('featured', None)
        # if featured and featured.lower() == 'true':
        #     queryset = queryset.filter(is_featured=True)
        
        # # Filter by in stock products
        # in_stock = self.request.query_params.get('in_stock', None)
        # if in_stock and in_stock.lower() == 'true':
        #     queryset = queryset.filter(stock_quantity__gt=0)
        
        # # Filter by on sale products
        # on_sale = self.request.query_params.get('on_sale', None)
        # if on_sale and on_sale.lower() == 'true':
        #     queryset = queryset.filter(compare_price__isnull=False, compare_price__gt=models.F('price'))
        
        # # Price range filtering
        # min_price = self.request.query_params.get('min_price', None)
        # if min_price:
        #     try:
        #         queryset = queryset.filter(price__gte=float(min_price))
        #     except ValueError:
        #         pass
        
        # max_price = self.request.query_params.get('max_price', None)
        # if max_price:
        #     try:
        #         queryset = queryset.filter(price__lte=float(max_price))
        #     except ValueError:
        #         pass
        
        # Search by name, description, and tags
        # search = self.request.query_params.get('search', None)
        # if search:
        #     queryset = queryset.filter(
        #         Q(name__icontains=search) | 
        #         Q(small_description__icontains=search) |
        #         Q(tags__name__icontains=search) |
        #         Q(sku__icontains=search)
        #     ).distinct()
        
        return queryset.distinct()
    
    @extend_schema(
        summary="List Products",
        description="Retrieve all active products with comprehensive filtering, search, and sorting options. No authentication required.",
        parameters=[
            OpenApiParameter('category', str, description='Filter by category slug'),
            OpenApiParameter('color', str, description='Filter by color name'),
            OpenApiParameter('size', str, description='Filter by size name'),
            OpenApiParameter('tag', str, description='Filter by tag slug'),
            OpenApiParameter('featured', str, description='Filter featured products (true/false)'),
            OpenApiParameter('in_stock', str, description='Filter in-stock products (true/false)'),
            OpenApiParameter('on_sale', str, description='Filter on-sale products (true/false)'),
            OpenApiParameter('min_price', str, description='Minimum price filter'),
            OpenApiParameter('max_price', str, description='Maximum price filter'),
            OpenApiParameter('search', str, description='Search in name, description, tags, and SKU'),
            OpenApiParameter('ordering', str, description='Sort order: price_asc, price_desc, name_asc, name_desc, newest, oldest'),
        ],
        responses={
            200: OpenApiResponse(
                description="List of products",
                response=ProductListSerializer(many=True)
            )
        },
        tags=["Products"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)