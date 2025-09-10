from django.db import models
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
        
        # Debug logging (remove in production)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"SessionAware auth - User: {user.email}, JTI: {jti}")
        
        # Strategy: Check both refresh token JTI and access token JTI
        if jti:
            # First check if this JTI matches a refresh token JTI (for refresh token requests)
            session_by_refresh_jti = UserSession.objects.filter(
                user=user,
                jti=jti,
                is_active=True
            ).first()
            
            # Then check if this JTI matches an access token JTI (for API requests)  
            session_by_access_jti = UserSession.objects.filter(
                user=user,
                access_jti=jti,
                is_active=True
            ).first()
            
            session = session_by_refresh_jti or session_by_access_jti
            logger.debug(f"JTI session found: refresh={bool(session_by_refresh_jti)}, access={bool(session_by_access_jti)}")
            
            if session:
                # Session found and active - authentication successful
                return user, validated_token
            else:
                # Check if JTI belongs to an inactive session
                inactive_session = UserSession.objects.filter(
                    models.Q(jti=jti) | models.Q(access_jti=jti),
                    user=user,
                    is_active=False
                ).first()
                
                if inactive_session:
                    raise InvalidToken("Session has been terminated")
                else:
                    # JTI doesn't match any session - fall back to general active session check
                    active_sessions = UserSession.objects.filter(
                        user=user,
                        is_active=True
                    ).count()
                    logger.debug(f"No JTI match - Active sessions for user: {active_sessions}")
                    if active_sessions == 0:
                        raise InvalidToken("No active sessions found")
        else:
            # No JTI in token - check if user has any active sessions
            active_sessions = UserSession.objects.filter(
                user=user,
                is_active=True
            ).count()
            logger.debug(f"No JTI - Active sessions for user: {active_sessions}")
            if active_sessions == 0:
                raise InvalidToken("No active sessions found")
        
        return user, validated_token