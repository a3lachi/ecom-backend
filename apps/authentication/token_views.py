from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from .models import UserSession


class SessionAwareTokenRefreshView(TokenRefreshView):
    """
    Token refresh that updates UserSession with new JTI
    and validates session is still active
    """
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        
        if refresh_token:
            try:
                old_token = RefreshToken(refresh_token)
                old_jti = str(old_token['jti'])
                
                # Check if session is still active
                session = UserSession.objects.filter(
                    jti=old_jti,
                    is_active=True
                ).first()
                
                if not session:
                    return Response(
                        {'detail': 'Session has been terminated'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                # Get new tokens from parent class
                response = super().post(request, *args, **kwargs)
                
                if response.status_code == 200:
                    # Update session with new JTI
                    new_refresh_token = response.data.get('refresh')
                    if new_refresh_token:
                        new_token = RefreshToken(new_refresh_token)
                        new_jti = str(new_token['jti'])
                        
                        session.jti = new_jti
                        session.save(update_fields=['jti', 'last_activity'])
                
                return response
                
            except Exception as e:
                return Response(
                    {'detail': 'Invalid token'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        return super().post(request, *args, **kwargs)