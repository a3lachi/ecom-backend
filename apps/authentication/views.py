from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import EmailVerificationToken, PasswordResetToken, LoginAttempt, UserSession
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    EmailVerificationSerializer, ResendVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetSerializer,
    ChangePasswordSerializer
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

def create_user_session(user, request, jti=None):
    """Create a user session record"""
    import uuid
    return UserSession.objects.create(
        user=user,
        session_key=str(uuid.uuid4()),  # Generate unique session key
        device_info=get_user_agent(request)[:500],  # Truncate if too long
        ip_address=get_client_ip(request),
        jti=jti or ''
    )

def log_login_attempt(request, email=None, user=None, success=False, failure_reason=''):
    """Log login attempt for security monitoring"""
    LoginAttempt.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        success=success,
        email_attempted=email or (user.email if user else ''),
        failure_reason=failure_reason
    )

class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="User Registration",
        description="Register a new user account. User will be inactive until email verification.",
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
            400: OpenApiResponse(description="Validation errors")
        }
    )
    def create(self, request, *args, **kwargs):
        # Check for IP-based rate limiting
        client_ip = get_client_ip(request)
        if LoginAttempt.is_ip_blocked(client_ip, minutes=60, max_attempts=10):
            return Response(
                {"detail": "Too many registration attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create email verification token
            verification_token = EmailVerificationToken.objects.create(user=user)
            
            # TODO: Send verification email (implement email service)
            # send_verification_email(user, verification_token)
            
            # Log registration attempt
            log_login_attempt(
                request, 
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
        log_login_attempt(
            request, 
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
        if LoginAttempt.is_ip_blocked(client_ip):
            log_login_attempt(
                request, email=email, success=False, 
                failure_reason='too_many_attempts'
            )
            return Response(
                {"detail": "Too many failed login attempts. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Check user-based rate limiting
        try:
            user = User.objects.get(email__iexact=email)
            if LoginAttempt.is_user_blocked(user):
                log_login_attempt(
                    request, user=user, success=False, 
                    failure_reason='too_many_attempts'
                )
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
            
            # Create user session
            create_user_session(user, request, jti=str(refresh['jti']))
            
            # Log successful login
            log_login_attempt(request, user=user, success=True)
            
            return Response({
                'access': str(access),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        
        # Log failed login
        log_login_attempt(
            request, email=email, success=False, 
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
            400: OpenApiResponse(description="Invalid or expired token")
        }
    )
    def get(self, request, token):
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
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Create user session
            create_user_session(user, request, jti=str(refresh['jti']))
            
            # Log successful verification
            log_login_attempt(request, user=user, success=True)
            
            return Response({
                'message': 'Email verified successfully. You are now logged in.',
                'access': str(access),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        
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
            400: OpenApiResponse(description="Invalid request")
        }
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['email']
            
            # Invalidate old tokens
            EmailVerificationToken.objects.filter(
                user=user, 
                is_used=False
            ).update(is_used=True)
            
            # Create new token
            verification_token = EmailVerificationToken.objects.create(user=user)
            
            # TODO: Send verification email
            # send_verification_email(user, verification_token)
            
            return Response({
                'message': 'Verification email has been sent.'
            })
        
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
                token = RefreshToken(refresh_token)
                token.blacklist()
                
                # Deactivate user session
                UserSession.objects.filter(
                    user=request.user,
                    jti=str(token['jti']),
                    is_active=True
                ).update(is_active=False)
            
            return Response({
                'message': 'Successfully logged out.'
            })
        except Exception:
            return Response({
                'message': 'Successfully logged out.'
            })

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
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
