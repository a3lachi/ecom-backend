from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema

from .models import UserProfile, Address
from .serializers import UserMeSerializer, UserUpdateSerializer, AddressSerializer

User = get_user_model()


class UserMeView(APIView):
    """
    Get and update current user's profile information
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get current user profile",
        description="Retrieve the authenticated user's profile information including personal details, loyalty points, membership tier, and address summary.",
        responses={
            200: UserMeSerializer,
            401: {
                "description": "Authentication credentials were not provided or are invalid.",
                "examples": {
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            }
        },
        tags=["Users"]
    )
    def get(self, request):
        """Get current user's profile data"""
        user = request.user
        
        # Create profile if it doesn't exist
        UserProfile.objects.get_or_create(user=user)
        
        serializer = UserMeSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update current user basic information",
        description="Update the authenticated user's basic information (first_name, last_name, phone, locale, timezone). Email and username cannot be updated through this endpoint.",
        request=UserUpdateSerializer,
        responses={
            200: UserMeSerializer,
            400: {
                "description": "Validation errors",
                "examples": {
                    "application/json": {
                        "phone": ["This field is required."]
                    }
                }
            },
            401: {
                "description": "Authentication credentials were not provided or are invalid."
            }
        },
        tags=["Users"]
    )
    def patch(self, request):
        """Update current user's basic information"""
        user = request.user
        
        # Create profile if it doesn't exist
        UserProfile.objects.get_or_create(user=user)
        
        # Update user with provided data
        update_serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if update_serializer.is_valid():
            update_serializer.save()
            
            # Return updated user data
            response_serializer = UserMeSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(update_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAddressListView(APIView):
    """
    List and create addresses for the authenticated user
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List user addresses",
        description="Retrieve all addresses for the authenticated user, ordered by creation date (newest first). Shows default address first if exists.",
        responses={
            200: AddressSerializer(many=True),
            401: {
                "description": "Authentication credentials were not provided or are invalid."
            }
        },
        tags=["Users"]
    )
    def get(self, request):
        """Get all user addresses"""
        # Get addresses ordered by default first, then by creation date
        addresses = Address.objects.filter(user=request.user).order_by(
            '-is_default',  # Default addresses first
            '-created_at'   # Then newest first
        )
        
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create new user address",
        description="Create a new address for the authenticated user. If is_default is True, it will automatically unset any existing default address.",
        request=AddressSerializer,
        responses={
            201: {
                "description": "Address created successfully",
                "content": {
                    "application/json": {
                        "examples": {
                            "success": {
                                "summary": "Address created",
                                "value": {
                                    "id": 1,
                                    "kind": "shipping",
                                    "full_name": "John Doe",
                                    "line1": "123 Main St",
                                    "city": "Casablanca",
                                    "country": "MA",
                                    "is_default": True,
                                    "label": "Home"
                                }
                            }
                        }
                    }
                }
            },
            400: {
                "description": "Validation errors",
                "examples": {
                    "application/json": {
                        "full_name": ["This field is required."],
                        "line1": ["This field is required."],
                        "city": ["This field is required."]
                    }
                }
            },
            401: {
                "description": "Authentication credentials were not provided or are invalid."
            }
        },
        tags=["Users"]
    )
    def post(self, request):
        """Create a new address for the user"""
        serializer = AddressSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Save the address with the authenticated user
            address = serializer.save(user=request.user)
            
            # Return the created address data
            response_serializer = AddressSerializer(address)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
