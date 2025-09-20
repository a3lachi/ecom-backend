from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Contact
from .serializers import ContactSerializer, CreateContactSerializer, PublicContactSerializer


class CreateContactView(generics.CreateAPIView):
    """
    Public endpoint for submitting contact form.
    
    This endpoint allows anyone to submit a contact form without authentication.
    It captures the user's IP address and browser information for tracking.
    """
    serializer_class = CreateContactSerializer
    permission_classes = []  # Public endpoint
    
    @extend_schema(
        summary="Submit contact form",
        description="Submit a contact form inquiry. No authentication required. Form data will be stored and reviewed by admin.",
        request=CreateContactSerializer,
        responses={
            201: PublicContactSerializer,
            400: {"description": "Validation errors"}
        },
        tags=['Contact Us']
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()
        
        # Return limited contact info
        response_serializer = PublicContactSerializer(contact)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ContactListView(generics.ListAPIView):
    """
    Admin-only endpoint to list all contact inquiries.
    
    Supports filtering by status, priority, and response status.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'priority', 'response_sent']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']
    
    @extend_schema(
        summary="List contact inquiries (Admin only)",
        description="Retrieve all contact form submissions. Admin access required.",
        parameters=[
            OpenApiParameter(
                name='status',
                description='Filter by status (NEW, IN_PROGRESS, RESOLVED, CLOSED)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='priority',
                description='Filter by priority (LOW, MEDIUM, HIGH, URGENT)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='response_sent',
                description='Filter by response status',
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='ordering',
                description='Order by: created_at, -created_at, priority, -priority, status, -status',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: ContactSerializer(many=True)},
        tags=['Contact Us']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ContactDetailView(generics.RetrieveUpdateAPIView):
    """
    Admin-only endpoint to view and update specific contact inquiry.
    
    Allows admin to update status, priority, add notes, and mark as responded.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="Retrieve contact inquiry (Admin only)",
        description="Get details of a specific contact inquiry. Admin access required.",
        responses={200: ContactSerializer},
        tags=['Contact Us']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update contact inquiry (Admin only)",
        description="Update status, priority, notes or mark as responded. Admin access required.",
        request=ContactSerializer,
        responses={200: ContactSerializer},
        tags=['Contact Us']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update contact inquiry (Admin only)",
        description="Update contact inquiry fields. Admin access required.",
        request=ContactSerializer,
        responses={200: ContactSerializer},
        tags=['Contact Us']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
