from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Wishlist, WishlistItem
from .serializers import WishlistSerializer, AddToWishlistSerializer


@extend_schema(
    summary="Get User's Wishlist",
    description="Retrieve the authenticated user's wishlist with all items. "
                "If the user doesn't have a wishlist yet, an empty one will be created.",
    responses={
        200: WishlistSerializer,
        401: {
            'description': 'Authentication required',
            'examples': {
                'application/json': {
                    'detail': 'Authentication credentials were not provided.'
                }
            }
        }
    },
    tags=['Wishlist']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    """Get or create user's wishlist with all items."""
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    serializer = WishlistSerializer(wishlist, context={'request': request})
    return Response(serializer.data)


@extend_schema(
    summary="Add Product to Wishlist",
    description="Add a product to the authenticated user's wishlist. "
                "If the product is already in the wishlist, it will return an error.",
    request=AddToWishlistSerializer,
    responses={
        201: WishlistSerializer,
        400: {
            'description': 'Validation error or product already in wishlist',
            'examples': {
                'application/json': {
                    'error': 'Product is already in your wishlist'
                }
            }
        },
        401: {
            'description': 'Authentication required',
            'examples': {
                'application/json': {
                    'detail': 'Authentication credentials were not provided.'
                }
            }
        }
    },
    tags=['Wishlist']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    """Add a product to user's wishlist."""
    serializer = AddToWishlistSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    product_id = serializer.validated_data['product']
    
    # Get or create user's wishlist
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    
    try:
        # Try to create the wishlist item
        WishlistItem.objects.create(
            wishlist=wishlist,
            product_id=product_id
        )
        
        # Return updated wishlist
        wishlist_serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(wishlist_serializer.data, status=status.HTTP_201_CREATED)
        
    except IntegrityError:
        # Product is already in wishlist (unique constraint violation)
        return Response(
            {'error': 'Product is already in your wishlist'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    summary="Remove Product from Wishlist",
    description="Remove a product from the authenticated user's wishlist by product ID.",
    parameters=[
        OpenApiParameter(
            name='product_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Product ID to remove from wishlist',
            required=True,
        ),
    ],
    responses={
        200: WishlistSerializer,
        404: {
            'description': 'Product not found in wishlist',
            'examples': {
                'application/json': {
                    'error': 'Product not found in your wishlist'
                }
            }
        },
        401: {
            'description': 'Authentication required',
            'examples': {
                'application/json': {
                    'detail': 'Authentication credentials were not provided.'
                }
            }
        }
    },
    tags=['Wishlist']
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, product_id):
    """Remove a product from user's wishlist."""
    # Get user's wishlist
    try:
        wishlist = Wishlist.objects.get(user=request.user)
    except Wishlist.DoesNotExist:
        return Response(
            {'error': 'Wishlist does not exist'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Find and delete the wishlist item
    try:
        wishlist_item = WishlistItem.objects.get(
            wishlist=wishlist,
            product_id=product_id
        )
        wishlist_item.delete()
        
        # Return updated wishlist
        wishlist_serializer = WishlistSerializer(wishlist, context={'request': request})
        return Response(wishlist_serializer.data)
        
    except WishlistItem.DoesNotExist:
        return Response(
            {'error': 'Product not found in your wishlist'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    summary="Clear Wishlist",
    description="Remove all products from the authenticated user's wishlist.",
    responses={
        200: WishlistSerializer,
        404: {
            'description': 'Wishlist does not exist',
            'examples': {
                'application/json': {
                    'error': 'Wishlist does not exist'
                }
            }
        },
        401: {
            'description': 'Authentication required',
            'examples': {
                'application/json': {
                    'detail': 'Authentication credentials were not provided.'
                }
            }
        }
    },
    tags=['Wishlist']
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_wishlist(request):
    """Clear all items from user's wishlist."""
    # Get user's wishlist
    try:
        wishlist = Wishlist.objects.get(user=request.user)
    except Wishlist.DoesNotExist:
        return Response(
            {'error': 'Wishlist does not exist'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Delete all wishlist items
    wishlist.items.all().delete()
    
    # Return empty wishlist
    wishlist_serializer = WishlistSerializer(wishlist, context={'request': request})
    return Response(wishlist_serializer.data)
