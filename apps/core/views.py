from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.db import connection
from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
import sys
import os
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
        error_message = None
        
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
            error_message = str(e)
        
        response_data = {
            "status": api_status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": "1.0.0",
            "database": db_status,
        }
        
        if api_status == "unhealthy" and error_message:
            response_data["error"] = error_message
        
        return Response(response_data, status=status_code)


class MigrateView(APIView):
    """
    Run database migrations - for deployment setup only
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Run Database Migrations",
        description="Executes Django database migrations. Should only be used during deployment setup.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "message": {"type": "string", "example": "Migrations completed successfully"},
                },
            },
            500: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "error"},
                    "message": {"type": "string"},
                },
            }
        },
        tags=["Management"]
    )
    def post(self, request):
        """Run Django migrations."""
        try:
            from django.core.management import call_command
            from io import StringIO
            
            # Capture command output
            output = StringIO()
            call_command('migrate', stdout=output)
            
            return Response({
                "status": "success",
                "message": "Migrations completed successfully",
                "output": output.getvalue()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Migration failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateSuperuserView(APIView):
    """
    Create superuser account - for deployment setup only
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Create Superuser Account",
        description="Creates a Django superuser account. Requires username, email, and password in request body.",
        request={
            "type": "object",
            "properties": {
                "username": {"type": "string", "example": "admin"},
                "email": {"type": "string", "example": "admin@example.com"},
                "password": {"type": "string", "example": "securepassword123"},
            },
            "required": ["username", "email", "password"]
        },
        responses={
            201: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "message": {"type": "string", "example": "Superuser created successfully"},
                    "username": {"type": "string", "example": "admin"},
                },
            },
            400: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "error"},
                    "message": {"type": "string"},
                },
            }
        },
        tags=["Management"]
    )
    def post(self, request):
        """Create a Django superuser."""
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not all([username, email, password]):
                return Response({
                    "status": "error",
                    "message": "Username, email, and password are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            User = get_user_model()
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return Response({
                    "status": "error",
                    "message": f"User with username '{username}' already exists"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            return Response({
                "status": "success",
                "message": "Superuser created successfully",
                "username": user.username
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to create superuser: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DatabaseDebugView(APIView):
    """
    Debug database connection - for troubleshooting only
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Debug Database Connection",
        description="Debug database connection with detailed information.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "success"},
                    "database_config": {"type": "object"},
                },
            }
        },
        tags=["Management"]
    )
    def get(self, request):
        """Debug database connection."""
        from django.conf import settings
        import os
        
        db_config = settings.DATABASES['default']
        
        # Get environment variables
        env_vars = {
            'POSTGRES_DATABASE': os.environ.get('POSTGRES_DATABASE', 'NOT SET'),
            'POSTGRES_USER': os.environ.get('POSTGRES_USER', 'NOT SET'),
            'POSTGRES_PASSWORD': '***HIDDEN***' if os.environ.get('POSTGRES_PASSWORD') else 'NOT SET',
            'POSTGRES_HOST': os.environ.get('POSTGRES_HOST', 'NOT SET'),
            'POSTGRES_PORT': os.environ.get('POSTGRES_PORT', 'NOT SET'),
        }
        
        # Test connection
        connection_status = "unknown"
        connection_error = None
        
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                result = cursor.fetchone()
                connection_status = "success"
                db_version = result[0] if result else "unknown"
        except Exception as e:
            connection_status = "failed"
            connection_error = str(e)
            db_version = "unknown"
        
        return Response({
            "status": "debug_info",
            "connection_status": connection_status,
            "connection_error": connection_error,
            "database_config": {
                "ENGINE": db_config.get('ENGINE'),
                "NAME": db_config.get('NAME'),
                "USER": db_config.get('USER'),
                "HOST": db_config.get('HOST'),
                "PORT": db_config.get('PORT'),
                "OPTIONS": db_config.get('OPTIONS', {}),
            },
            "environment_variables": env_vars,
            "database_version": db_version if connection_status == "success" else None,
        }, status=status.HTTP_200_OK)
