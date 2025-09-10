from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import EmailVerificationToken, SecurityAttempt, UserSession
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    EmailVerificationSerializer, ResendVerificationSerializer,
    ChangePasswordSerializer
)
from .session_utils import (
    enforce_max_sessions_per_user, 
    detect_suspicious_session_activity, 
    log_session_activity,
    get_session_stats
)

User = get_user_model()

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')

def create_user_session(user, request, refresh_jti=None, access_jti=None):
    """Create a user session record with both refresh and access JTIs"""
    import uuid
    session = UserSession.objects.create(
        user=user,
        session_key=str(uuid.uuid4()),  # Generate unique session key
        device_info=get_user_agent(request)[:500],  # Truncate if too long
        ip_address=get_client_ip(request),
        jti=refresh_jti or '',
        access_jti=access_jti or ''
    )
    return session

def log_security_attempt(request, attempt_type, email=None, user=None, success=False, failure_reason=''):
    """Log security attempt for monitoring"""
    SecurityAttempt.objects.create(
        attempt_type=attempt_type,
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=success,
        email_attempted=email or (user.email if user else ''),
        failure_reason=failure_reason
    )

class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="User Registration",
        description="Register a new user account. User will be inactive until email verification.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Registration successful",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "user": {"$ref": "#/components/schemas/User"}
                    }
                }
            ),
            400: OpenApiResponse(description="Validation errors"),
            429: OpenApiResponse(description="Too many attempts")
        }
    )
    def post(self, request):
        # Check for IP-based rate limiting
        client_ip = get_client_ip(request)
        if SecurityAttempt.is_ip_blocked(client_ip, attempt_type=SecurityAttempt.AttemptType.REGISTER, minutes=60, max_attempts=10):
            return Response(
                {"detail": "Too many registration attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create email verification token
            verification_token = EmailVerificationToken.objects.create(user=user)
            
            # TODO: Send verification email (implement email service)
            # send_verification_email(user, verification_token)
            
            # Log registration attempt
            log_security_attempt(
                request, 
                attempt_type=SecurityAttempt.AttemptType.REGISTER,
                email=user.email, 
                user=user, 
                success=True
            )
            
            return Response({
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        # Log failed registration attempt
        email = request.data.get('email', '')
        log_security_attempt(
            request, 
            attempt_type=SecurityAttempt.AttemptType.REGISTER,
            email=email, 
            success=False, 
            failure_reason='validation_error'
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="User Login",
        description="Login with email and password. Returns JWT tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                response={
                    "type": "object",
                    "properties": {
                        "access": {"type": "string"},
                        "refresh": {"type": "string"},
                        "user": {"$ref": "#/components/schemas/User"}
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid credentials"),
            429: OpenApiResponse(description="Too many attempts")
        }
    )
    def post(self, request):
        client_ip = get_client_ip(request)
        email = request.data.get('email', '')
        
        # Check IP-based rate limiting
        if SecurityAttempt.is_ip_blocked(client_ip, attempt_type=SecurityAttempt.AttemptType.LOGIN, minutes=15, max_attempts=5):
            return Response(
                {"detail": "Too many failed login attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Check user-based rate limiting
        try:
            user = User.objects.get(email__iexact=email)
            if SecurityAttempt.is_user_blocked(user, attempt_type=SecurityAttempt.AttemptType.LOGIN):
                return Response(
                    {"detail": "Too many failed login attempts for this account."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
        except User.DoesNotExist:
            pass
        
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Create user session with both JTIs
            session = create_user_session(
                user, 
                request, 
                refresh_jti=str(refresh['jti']),
                access_jti=str(access['jti'])
            )
            
            # Enforce max sessions per user
            enforce_max_sessions_per_user(user)
            
            # Detect suspicious activity
            if detect_suspicious_session_activity(user, request):
                log_session_activity(user, 'suspicious_login_detected', request)
            
            # Log session activity
            log_session_activity(user, 'login_success', request, {
                'session_id': session.id,
                'device_info': session.device_info[:100]  # Truncate for logs
            })
            
            # Log successful login
            log_security_attempt(request, attempt_type=SecurityAttempt.AttemptType.LOGIN, user=user, success=True)
            
            return Response({
                'access': str(access),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        
        # Log failed login
        log_security_attempt(
            request, 
            attempt_type=SecurityAttempt.AttemptType.LOGIN,
            email=email, 
            success=False, 
            failure_reason='invalid_credentials'
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    """Email verification endpoint"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Verify Email",
        description="Verify user email with token and activate account.",
        responses={
            200: OpenApiResponse(
                description="Email verified successfully",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "access": {"type": "string"},
                        "refresh": {"type": "string"},
                        "user": {"$ref": "#/components/schemas/User"}
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid or expired token"),
            429: OpenApiResponse(description="Too many attempts")
        }
    )
    def get(self, request, token):
        # Check for IP-based rate limiting
        client_ip = get_client_ip(request)
        if SecurityAttempt.is_ip_blocked(client_ip, attempt_type=SecurityAttempt.AttemptType.EMAIL_VERIFICATION, minutes=15, max_attempts=10):
            return Response(
                {"detail": "Too many verification attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = EmailVerificationSerializer(data={'token': token})
        if serializer.is_valid():
            verification_token = serializer.validated_data['token']
            user = verification_token.user
            
            # Activate user
            user.is_active = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=['is_active', 'email_verified_at'])
            
            # Mark token as used
            verification_token.mark_as_used()
            
            # Log successful verification
            log_security_attempt(request, attempt_type=SecurityAttempt.AttemptType.EMAIL_VERIFICATION, user=user, success=True)
            
            return Response({
                'message': 'Email verified successfully. You can now log in.'
            }, status=status.HTTP_200_OK)
        
        # Log failed verification attempt
        log_security_attempt(
            request, 
            attempt_type=SecurityAttempt.AttemptType.EMAIL_VERIFICATION,
            success=False, 
            failure_reason='invalid_token'
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationView(APIView):
    """Resend email verification"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Resend Verification Email",
        description="Resend email verification token.",
        request=ResendVerificationSerializer,
        responses={
            200: OpenApiResponse(description="Verification email sent"),
            400: OpenApiResponse(description="Invalid request"),
            429: OpenApiResponse(description="Too many attempts")
        }
    )
    def post(self, request):
        # Check for IP-based rate limiting
        client_ip = get_client_ip(request)
        
        if SecurityAttempt.is_ip_blocked(client_ip, attempt_type=SecurityAttempt.AttemptType.EMAIL_VERIFICATION, minutes=15, max_attempts=5):
            return Response(
                {"detail": "Too many verification requests. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['email']  # Returns user object, not email string
            
            # Invalidate old tokens
            old_tokens = EmailVerificationToken.objects.filter(
                user=user, 
                is_used=False
            )
            for token in old_tokens:
                token.mark_as_used()
            
            # Create new token
            verification_token = EmailVerificationToken.objects.create(user=user)
            
            # TODO: Send verification email
            # send_verification_email(user, verification_token)
            
            # Log successful resend attempt
            log_security_attempt(
                request,
                attempt_type=SecurityAttempt.AttemptType.EMAIL_VERIFICATION,
                user=user,
                success=True
            )
            
            return Response({
                'message': 'Verification email has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Log failed resend attempt
        email = request.data.get('email', '')
        log_security_attempt(
            request,
            attempt_type=SecurityAttempt.AttemptType.EMAIL_VERIFICATION,
            email=email,
            success=False,
            failure_reason='validation_error'
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """Logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Logout",
        description="Logout user and blacklist refresh token.",
        responses={
            200: OpenApiResponse(description="Logged out successfully")
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    
                    # Deactivate user session
                    deactivated_count = UserSession.objects.filter(
                        user=request.user,
                        jti=str(token['jti']),
                        is_active=True
                    ).update(is_active=False)
                    
                except Exception as token_error:
                    # Log the error but still return success for security
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Logout token error for user {request.user.email}: {str(token_error)}")
            
            return Response({
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # Log unexpected errors but still return success
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected logout error for user {getattr(request.user, 'email', 'unknown')}: {str(e)}")
            
            return Response({
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    """Change password for authenticated users"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Change Password",
        description="Change user password (requires current password).",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Invalid current password")
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSessionListView(APIView):
    """List user's active sessions"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="List User Sessions",
        description="Get all active sessions for the authenticated user.",
        responses={
            200: OpenApiResponse(
                description="List of active sessions",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "device_info": {"type": "string"},
                            "ip_address": {"type": "string"},
                            "created_at": {"type": "string"},
                            "last_activity": {"type": "string"},
                            "is_current": {"type": "boolean"}
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        # Get current session JTI from token
        current_jti = None
        if hasattr(request, 'auth') and request.auth:
            current_jti = str(request.auth.get('jti', ''))
        
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-last_activity')
        
        session_data = []
        for session in sessions:
            session_data.append({
                'id': session.id,
                'device_info': session.device_info,
                'ip_address': session.ip_address,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'is_current': session.jti == current_jti
            })
        
        return Response(session_data, status=status.HTTP_200_OK)


class DeactivateSessionView(APIView):
    """Deactivate a specific session"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Deactivate Session",
        description="Deactivate a specific session. This will force re-login for that session.",
        responses={
            200: OpenApiResponse(description="Session deactivated successfully"),
            404: OpenApiResponse(description="Session not found")
        }
    )
    def post(self, request, session_id):
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True
            )
            session.deactivate()
            
            return Response({
                'message': 'Session deactivated successfully.'
            }, status=status.HTTP_200_OK)
        except UserSession.DoesNotExist:
            return Response({
                'error': 'Session not found or already deactivated.'
            }, status=status.HTTP_404_NOT_FOUND)


class DeactivateAllSessionsView(APIView):
    """Deactivate all sessions except current"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Deactivate All Other Sessions",
        description="Deactivate all sessions except the current one. Forces re-login on all other devices.",
        responses={
            200: OpenApiResponse(description="All other sessions deactivated")
        }
    )
    def post(self, request):
        # Get current session JTI
        current_jti = None
        if hasattr(request, 'auth') and request.auth:
            current_jti = str(request.auth.get('jti', ''))
        
        # Deactivate all sessions except current
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        )
        
        if current_jti:
            sessions = sessions.exclude(jti=current_jti)
        
        count = sessions.count()
        sessions.update(is_active=False)
        
        return Response({
            'message': f'Deactivated {count} sessions successfully.'
        }, status=status.HTTP_200_OK)


class UserSessionStatsView(APIView):
    """Get user session statistics"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get Session Statistics",
        description="Get session statistics and security info for the authenticated user.",
        responses={
            200: OpenApiResponse(
                description="Session statistics",
                response={
                    "type": "object",
                    "properties": {
                        "active_sessions": {"type": "integer"},
                        "total_sessions": {"type": "integer"},
                        "max_allowed": {"type": "integer"},
                        "expire_days": {"type": "integer"},
                        "security_settings": {"type": "object"}
                    }
                }
            )
        }
    )
    def get(self, request):
        stats = get_session_stats(request.user)
        
        # Add security settings info
        from django.conf import settings
        session_security = getattr(settings, 'SESSION_SECURITY', {})
        
        stats['security_settings'] = {
            'max_sessions_enforced': session_security.get('MAX_SESSIONS_PER_USER', 0) > 0,
            'auto_cleanup_enabled': session_security.get('AUTO_CLEANUP_SESSIONS', True),
            'activity_logging_enabled': session_security.get('LOG_SESSION_ACTIVITIES', True),
            'suspicious_activity_detection': session_security.get('FORCE_LOGOUT_ON_SUSPICIOUS_ACTIVITY', True),
        }
        
        return Response(stats, status=status.HTTP_200_OK)
