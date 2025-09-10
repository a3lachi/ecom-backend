from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
from datetime import timedelta
import uuid

from .models import EmailVerificationToken, PasswordResetToken, SecurityAttempt, UserSession

User = get_user_model()


class AuthenticationTestSetup(APITestCase):
    """Base test class with common setup for authentication tests"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+1234567890'
        }
        self.user = User.objects.create_user(
            email='existing@example.com',
            username='existinguser',
            password='ExistingPassword123!',
            is_active=True
        )
    
    def get_jwt_tokens(self, user):
        """Helper to get JWT tokens for a user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
    
    def authenticate_user(self, user=None):
        """Helper to authenticate user and set auth header"""
        if user is None:
            user = self.user
        tokens = self.get_jwt_tokens(user)
        
        # Create user session for session-aware authentication
        UserSession.objects.create(
            user=user,
            session_key=f'test-session-{user.id}',
            device_info='Test Device',
            ip_address='127.0.0.1',
            jti=RefreshToken(tokens['refresh'])['jti']
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        return tokens


class RegistrationTestCase(AuthenticationTestSetup):
    """Test cases for user registration"""
    
    def test_successful_registration(self):
        """Test successful user registration"""
        url = reverse('register')
        response = self.client.post(url, self.user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        
        # Verify user was created but inactive
        user = User.objects.get(email=self.user_data['email'])
        self.assertFalse(user.is_active)
        self.assertEqual(user.username, self.user_data['username'])
        
        # Verify email verification token was created
        token = EmailVerificationToken.objects.get(user=user)
        self.assertIsNotNone(token)
        self.assertFalse(token.is_used)
        
        # Verify security attempt was logged
        attempt = SecurityAttempt.objects.get(
            attempt_type=SecurityAttempt.AttemptType.REGISTER,
            email_attempted=self.user_data['email']
        )
        self.assertTrue(attempt.success)


class LoginTestCase(AuthenticationTestSetup):
    """Test cases for user login"""
    
    def test_successful_login(self):
        """Test successful user login"""
        url = reverse('login')
        data = {
            'email': self.user.email,
            'password': 'ExistingPassword123!'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Verify user session was created
        session = UserSession.objects.get(user=self.user)
        self.assertTrue(session.is_active)
        self.assertIsNotNone(session.jti)
        
        # Verify security attempt was logged
        attempt = SecurityAttempt.objects.get(
            user=self.user,
            attempt_type=SecurityAttempt.AttemptType.LOGIN,
            success=True
        )
        self.assertIsNotNone(attempt)


class EmailVerificationTestCase(AuthenticationTestSetup):
    """Test cases for email verification"""
    
    def setUp(self):
        super().setUp()
        self.inactive_user = User.objects.create_user(
            email='unverified@example.com',
            username='unverifieduser', 
            password='UnverifiedPassword123!',
            is_active=False
        )
        self.verification_token = EmailVerificationToken.objects.create(
            user=self.inactive_user
        )
    
    def test_successful_email_verification(self):
        """Test successful email verification"""
        url = reverse('verify-email', kwargs={'token': self.verification_token.token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('verified successfully', response.data['message'])
        
        self.inactive_user.refresh_from_db()
        self.assertTrue(self.inactive_user.is_active)
        self.assertIsNotNone(self.inactive_user.email_verified_at)


class LogoutTestCase(AuthenticationTestSetup):
    """Test cases for user logout"""
    
    def test_successful_logout(self):
        """Test successful logout"""
        tokens = self.authenticate_user()
        
        # Get the session created by authenticate_user
        jti = RefreshToken(tokens['refresh'])['jti']
        session = UserSession.objects.get(
            user=self.user,
            jti=jti
        )
        
        url = reverse('logout')
        data = {'refresh': tokens['refresh']}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Successfully logged out', response.data['message'])
        
        session.refresh_from_db()
        self.assertFalse(session.is_active)


class SessionManagementTestCase(AuthenticationTestSetup):
    """Test cases for session management"""
    
    def setUp(self):
        super().setUp()
        # Clear any existing sessions
        UserSession.objects.all().delete()
        
        self.tokens = self.authenticate_user()
        # Create only one additional test session
        self.session2 = UserSession.objects.create(
            user=self.user,
            session_key='session-2',
            device_info='Safari on iPhone', 
            ip_address='192.168.1.2',
            jti='different-jti'
        )
    
    def test_list_user_sessions(self):
        """Test listing user sessions"""
        url = reverse('user-sessions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 1 from authenticate_user + 1 additional
        
        session_data = response.data[0]
        self.assertIn('id', session_data)
        self.assertIn('device_info', session_data)
        self.assertIn('is_current', session_data)
    
    def test_deactivate_specific_session(self):
        """Test deactivating a specific session"""
        url = reverse('deactivate-session', kwargs={'session_id': self.session2.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('deactivated successfully', response.data['message'])
        
        self.session2.refresh_from_db()
        self.assertFalse(self.session2.is_active)


class PasswordChangeTestCase(AuthenticationTestSetup):
    """Test cases for password change"""
    
    def test_successful_password_change(self):
        """Test successful password change"""
        self.authenticate_user()
        
        url = reverse('change-password')
        data = {
            'current_password': 'ExistingPassword123!',
            'new_password': 'NewPassword456!'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('changed successfully', response.data['message'])
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword456!'))
        self.assertFalse(self.user.check_password('ExistingPassword123!'))
    
    def test_password_change_wrong_current_password(self):
        """Test password change with wrong current password"""
        self.authenticate_user()
        
        url = reverse('change-password')
        data = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword456!'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data)


class SecurityTestCase(AuthenticationTestSetup):
    """Test cases for security features and rate limiting"""
    
    def test_security_attempt_logging(self):
        """Test that security attempts are properly logged"""
        url = reverse('login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify security attempt was logged
        attempt = SecurityAttempt.objects.get(
            email_attempted='nonexistent@example.com',
            attempt_type=SecurityAttempt.AttemptType.LOGIN,
            success=False
        )
        self.assertEqual(attempt.failure_reason, 'invalid_credentials')
        self.assertEqual(attempt.ip_address, '127.0.0.1')
    
    def test_session_aware_authentication(self):
        """Test that deactivated sessions prevent access"""
        tokens = self.authenticate_user()
        
        # Get and deactivate the session
        jti = RefreshToken(tokens['refresh'])['jti']
        session = UserSession.objects.get(
            user=self.user,
            jti=jti
        )
        session.deactivate()
        
        # Try to access protected endpoint - should fail due to deactivated session
        url = reverse('change-password')
        data = {
            'current_password': 'ExistingPassword123!',
            'new_password': 'NewPassword456!'
        }
        response = self.client.post(url, data)
        
        # Should fail due to deactivated session
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)