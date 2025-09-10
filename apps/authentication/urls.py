from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, VerifyEmailView,
    ResendVerificationView, ChangePasswordView,
    UserSessionListView, DeactivateSessionView, DeactivateAllSessionsView
)

urlpatterns = [
    # Registration & Email Verification
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    
    # Login & JWT Management
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Password Management
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Session Management
    path('sessions/', UserSessionListView.as_view(), name='user-sessions'),
    path('sessions/<int:session_id>/deactivate/', DeactivateSessionView.as_view(), name='deactivate-session'),
    path('sessions/deactivate-all/', DeactivateAllSessionsView.as_view(), name='deactivate-all-sessions'),
    
    # TODO: Add these routes later
    # path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    # path('reset-password/<uuid:token>/', ResetPasswordView.as_view(), name='reset-password'),
]