from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.db import connection
import time

class HealthCheckView(APIView):
    """
    Health check endpoint to verify API status and database connectivity.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Health Check",
        description="Returns the health status of the API and database connection.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "healthy"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "version": {"type": "string", "example": "1.0.0"},
                    "database": {"type": "string", "example": "connected"},
                },
            },
            503: {
                "type": "object", 
                "properties": {
                    "status": {"type": "string", "example": "unhealthy"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "version": {"type": "string", "example": "1.0.0"},
                    "database": {"type": "string", "example": "disconnected"},
                    "error": {"type": "string"},
                },
            }
        },
        tags=["Health Check"]
    )
    def get(self, request):
        """Check API health and database connectivity."""
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            db_status = "connected"
            api_status = "healthy"
            status_code = status.HTTP_200_OK
        
        except Exception as e:
            db_status = "disconnected"
            api_status = "unhealthy"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        response_data = {
            "status": api_status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": "1.0.0",
            "database": db_status,
        }
        
        if api_status == "unhealthy":
            response_data["error"] = str(e)
        
        return Response(response_data, status=status_code)
