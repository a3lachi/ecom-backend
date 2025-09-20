from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer


class ReviewListView(generics.ListAPIView):
    """
    List all reviews with optional filtering by product, rating, and user.
    
    Query parameters:
    - product: Filter reviews by product ID
    - rating: Filter reviews by rating (1-5)
    - user: Filter reviews by user ID
    - ordering: Order by fields (e.g., -created_at, rating)
    """
    queryset = Review.objects.filter(is_approved=True, is_verified_purchase=True)
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product', 'rating', 'user']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']  # Default ordering
    permission_classes = []  # Public endpoint
    
    @extend_schema(
        summary="List all reviews",
        description="Retrieve a list of all approved reviews from verified purchases with optional filtering by product, rating, and user.",
        parameters=[
            OpenApiParameter(
                name='product',
                description='Filter reviews by product ID',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='rating',
                description='Filter reviews by rating (1-5)',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='user',
                description='Filter reviews by user ID',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='ordering',
                description='Order by: created_at, -created_at, rating, -rating',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: ReviewSerializer(many=True)},
        tags=['Reviews']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CreateReviewView(generics.CreateAPIView):
    """
    Create a new review for a product.
    
    Requirements:
    - User must be authenticated
    - User must have purchased the product
    - Order must be delivered and paid
    - User can only review each product once
    """
    serializer_class = CreateReviewSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Create a new review",
        description="Create a review for a product. User must have purchased and received the product to review it.",
        request=CreateReviewSerializer,
        responses={
            201: ReviewSerializer,
            400: {"description": "Validation errors"},
            401: {"description": "Authentication required"},
            403: {"description": "User hasn't purchased this product or already reviewed it"}
        },
        tags=['Reviews']
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        # Return the created review using the read serializer
        response_serializer = ReviewSerializer(review)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
