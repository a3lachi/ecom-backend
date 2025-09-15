from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import Order
from .serializers import OrderListSerializer


@extend_schema(
    summary="List User Orders",
    description="Retrieve all orders for the authenticated user. "
                "Orders are sorted by creation date (newest first).",
    responses={
        200: OrderListSerializer(many=True),
        401: {
            'description': 'Authentication required',
            'examples': {
                'application/json': {
                    'detail': 'Authentication credentials were not provided.'
                }
            }
        }
    },
    tags=['Orders']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_orders(request):
    """List all orders for the authenticated user."""
    try:
        # Get all orders for the current user, ordered by newest first
        queryset = Order.objects.filter(user=request.user).order_by('-created_at')
        
        # Serialize and return all orders
        serializer = OrderListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
        
    except Exception:
        return Response(
            {'error': 'Failed to retrieve orders'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
