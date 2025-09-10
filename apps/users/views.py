from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema

from .models import UserProfile
from .serializers import UserMeSerializer

User = get_user_model()


class UserMeView(APIView):
    """
    Get current user's profile information
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
