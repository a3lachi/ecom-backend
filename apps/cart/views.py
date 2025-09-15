from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, DeleteFromCartSerializer, UpdateCartItemSerializer


def get_or_create_cart(request):
    """Get or create cart for authenticated user or guest session."""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            status=Cart.Status.ACTIVE,
            defaults={'currency': 'USD'}
        )
    else:
        session_key = request.headers.get('X-Session-Key')
        if not session_key:
            raise ValidationError("Session key required for guest users")
        
        cart, _ = Cart.objects.get_or_create(
            session_key=session_key,
            status=Cart.Status.ACTIVE,
            user=None,
            defaults={'currency': 'USD'}
        )
    
    return cart


@extend_schema(
    summary="Get Shopping Cart",
    description="Retrieve the current shopping cart for authenticated users or guest sessions. "
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
        200: CartSerializer,
        400: {
            'description': 'Bad request - missing session key for guest users',
            'examples': {
                'application/json': {
                    'error': 'Session key required for guest users'
                }
            }
        }
    },
    tags=['Cart']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart(request):
    """Get cart with all items for current user or session."""
    try:
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )




@extend_schema(
    summary="Add Item to Cart",
    description="Add a product to the shopping cart with specified quantity and variants. "
                "If the item already exists, the quantity will be updated. "
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
    request=AddToCartSerializer,
    responses={
        200: CartSerializer,
        400: {
            'description': 'Validation error',
            'examples': {
                'application/json': {
                    'error': 'Product not found'
                }
            }
        }
    },
    tags=['Cart']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart(request):
    """Add item to cart."""
    try:
        cart = get_or_create_cart(request)
        serializer = AddToCartSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        with transaction.atomic():
            # Get product to prepare defaults with snapshot data
            from apps.products.models import Product
            product = Product.objects.get(pk=data['product'])
            
            # Prepare defaults with snapshot data
            defaults = {
                'quantity': data['quantity'],
                'product_name_snapshot': product.name or "",
                'sku_snapshot': product.sku or "", 
                'unit_price_snapshot': product.price or Decimal("0.00"),
                'compare_price_snapshot': product.compare_price,
                'image_url_snapshot': ""
            }
            
            # Add image URL if available
            img = product.primary_image
            if img and hasattr(img, 'image') and img.image:
                defaults['image_url_snapshot'] = getattr(img.image, "url", "")
            
            # Get or create cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=data['product'],
                color_id=data.get('color'),
                size_id=data.get('size'),
                defaults=defaults
            )
            
            if not created:
                # Update quantity if item already exists
                cart_item.quantity += data['quantity']
                # Also update snapshots in case product data changed
                cart_item.sync_from_product()
                cart_item.save()
            
            # Recompute cart totals
            cart.recompute_totals()
        
        # Return updated cart
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data)
        
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to add item to cart'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Remove Item from Cart",
    description="Remove a product from the shopping cart. "
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
    request=DeleteFromCartSerializer,
    responses={
        200: CartSerializer,
        400: {
            'description': 'Validation error',
            'examples': {
                'application/json': {
                    'error': 'Product not found in cart'
                }
            }
        }
    },
    tags=['Cart']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def delete_from_cart(request):
    """Remove item from cart."""
    try:
        cart = get_or_create_cart(request)
        serializer = DeleteFromCartSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        product_id = serializer.validated_data['product']
        
        # Find the cart item to delete
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product_id=product_id
            )
            cart_item.delete()
            
            # Recompute cart totals
            cart.recompute_totals()
            
            # Return updated cart
            cart_serializer = CartSerializer(cart, context={'request': request})
            return Response(cart_serializer.data)
            
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Product not found in cart'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to remove item from cart'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Clear Cart",
    description="Remove all items from the shopping cart. "
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
        200: CartSerializer,
        404: {
            'description': 'Cart not found',
            'examples': {
                'application/json': {
                    'error': 'Cart not found'
                }
            }
        }
    },
    tags=['Cart']
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_cart(request):
    """Clear all items from cart."""
    try:
        cart = get_or_create_cart(request)
        
        # Delete all cart items
        cart.items.all().delete()
        
        # Recompute cart totals (should be all zeros now)
        cart.recompute_totals()
        
        # Return empty cart
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data)
        
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to clear cart'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Update Cart Item Quantity",
    description="Update the quantity of a specific product in the shopping cart. "
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
    request=UpdateCartItemSerializer,
    responses={
        200: CartSerializer,
        400: {
            'description': 'Validation error',
            'examples': {
                'application/json': {
                    'error': 'Product not found in cart'
                }
            }
        }
    },
    tags=['Cart']
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_cart_item(request):
    """Update quantity of item in cart."""
    try:
        cart = get_or_create_cart(request)
        serializer = UpdateCartItemSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        product_id = data['product']
        new_quantity = data['quantity']
        
        # Find the cart item to update
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product_id=product_id
            )
            
            # Update quantity
            cart_item.quantity = new_quantity
            cart_item.save()
            
            # Recompute cart totals
            cart.recompute_totals()
            
            # Return updated cart
            cart_serializer = CartSerializer(cart, context={'request': request})
            return Response(cart_serializer.data)
            
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Product not found in cart'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except ValidationError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to update cart item'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

