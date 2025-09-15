from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Comparison, ComparisonItem
from .serializers import ComparisonSerializer, AddToComparisonSerializer, RemoveFromComparisonSerializer


def get_or_create_comparison(request):
    """Get or create comparison for authenticated user or guest session."""
    if request.user.is_authenticated:
        comparison, _ = Comparison.objects.get_or_create(
            user=request.user,
        )
    else:
        session_key = request.headers.get('X-Session-Key')
        if not session_key:
            raise ValidationError("Session key required for guest users")
        
        comparison, _ = Comparison.objects.get_or_create(
            session_key=session_key,
            user=None,
        )
    
    return comparison


@extend_schema(
    summary="Get Product Comparison",
    description="Retrieve the current product comparison for authenticated users or guest sessions. "
                "For guest users, include X-Session-Key header with a unique session identifier.",
    parameters=[
        OpenApiParameter(
            name='X-Session-Key',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Session key for guest users (required if not authenticated)',
            required=False,
        ),
    ],
    responses={
        200: ComparisonSerializer,
        400: {
            'description': 'Bad request - missing session key for guest users',
            'examples': {
                'application/json': {
                    'error': 'Session key required for guest users'
                }
            }
        }
    },
    tags=['Comparison']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_comparison(request):
    """Get comparison with all items for current user or session."""
    try:
        comparison = get_or_create_comparison(request)
        serializer = ComparisonSerializer(comparison, context={'request': request})
        return Response(serializer.data)
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    summary="Add Product to Comparison",
    description="Add a product to the comparison list. "
                "If the product already exists, it won't be added again. "
                "For guest users, include X-Session-Key header.",
    parameters=[
        OpenApiParameter(
            name='X-Session-Key',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Session key for guest users (required if not authenticated)',
            required=False,
        ),
    ],
    request=AddToComparisonSerializer,
    responses={
        200: ComparisonSerializer,
        400: {
            'description': 'Validation error',
            'examples': {
                'application/json': {
                    'error': 'Product not found'
                }
            }
        }
    },
    tags=['Comparison']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_comparison(request):
    """Add product to comparison."""
    try:
        comparison = get_or_create_comparison(request)
        serializer = AddToComparisonSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = serializer.validated_data['product']
        
        with transaction.atomic():
            # Check if product already exists in comparison
            existing_item = ComparisonItem.objects.filter(
                comparison=comparison,
                product_id=product_id
            ).first()
            
            if existing_item:
                # Product already in comparison, return current comparison
                pass
            else:
                # Create new comparison item
                ComparisonItem.objects.create(
                    comparison=comparison,
                    product_id=product_id
                )
        
        # Return updated comparison
        comparison_serializer = ComparisonSerializer(comparison, context={'request': request})
        return Response(comparison_serializer.data)
        
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to add product to comparison'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Remove Product from Comparison",
    description="Remove a product from the comparison list. "
                "For guest users, include X-Session-Key header.",
    parameters=[
        OpenApiParameter(
            name='X-Session-Key',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Session key for guest users (required if not authenticated)',
            required=False,
        ),
    ],
    request=RemoveFromComparisonSerializer,
    responses={
        200: ComparisonSerializer,
        400: {
            'description': 'Validation error',
            'examples': {
                'application/json': {
                    'error': 'Product not found in comparison'
                }
            }
        }
    },
    tags=['Comparison']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def remove_from_comparison(request):
    """Remove product from comparison."""
    try:
        comparison = get_or_create_comparison(request)
        serializer = RemoveFromComparisonSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = serializer.validated_data['product']
        
        # Find the comparison item to delete
        try:
            comparison_item = ComparisonItem.objects.get(
                comparison=comparison,
                product_id=product_id
            )
            comparison_item.delete()
            
            # Return updated comparison
            comparison_serializer = ComparisonSerializer(comparison, context={'request': request})
            return Response(comparison_serializer.data)
            
        except ComparisonItem.DoesNotExist:
            return Response(
                {'error': 'Product not found in comparison'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to remove product from comparison'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Clear Comparison",
    description="Remove all products from the comparison list. "
                "For guest users, include X-Session-Key header.",
    parameters=[
        OpenApiParameter(
            name='X-Session-Key',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Session key for guest users (required if not authenticated)',
            required=False,
        ),
    ],
    responses={
        200: ComparisonSerializer,
        400: {
            'description': 'Bad request - missing session key for guest users',
            'examples': {
                'application/json': {
                    'error': 'Session key required for guest users'
                }
            }
        }
    },
    tags=['Comparison']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_comparison(request):
    """Clear all products from comparison."""
    try:
        comparison = get_or_create_comparison(request)
        
        # Delete all comparison items
        comparison.items.all().delete()
        
        # Return empty comparison
        comparison_serializer = ComparisonSerializer(comparison, context={'request': request})
        return Response(comparison_serializer.data)
        
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to clear comparison'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
