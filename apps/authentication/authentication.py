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
        # Access tokens don't have JTI by default, so we check by user and active sessions
        jti = validated_token.get('jti')
        
        # Debug: Print token info for testing
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"SessionAware auth - User: {user.email}, JTI: {jti}")
        
        # If there's a JTI, check for exact match (for refresh tokens)
        if jti:
            session_exists = UserSession.objects.filter(
                user=user,
                jti=jti,
                is_active=True
            ).exists()
            logger.debug(f"JTI session exists: {session_exists}")
            if not session_exists:
                raise InvalidToken("Session has been terminated")
        else:
            # For access tokens without JTI, check if user has any active sessions
            active_sessions = UserSession.objects.filter(
                user=user,
                is_active=True
            ).count()
            logger.debug(f"Active sessions for user: {active_sessions}")
            if active_sessions == 0:
                raise InvalidToken("No active sessions found")
            
        return user, validated_token