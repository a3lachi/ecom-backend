from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from .models import UserSession


class SessionAwareJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that also checks if the user session is still active.
    This allows forcing re-login by deactivating sessions.
    """
    
    def authenticate(self, request):
        # First perform normal JWT authentication
        result = super().authenticate(request)
        if result is None:
            return None
            
        user, validated_token = result
        
        # Check if the session associated with this token is still active
        jti = validated_token.get('jti')
        if jti and not UserSession.objects.filter(
            user=user,
            jti=jti,
            is_active=True
        ).exists():
            # Session has been deactivated, force re-authentication
            raise InvalidToken("Session has been terminated")
            
        return user, validated_token