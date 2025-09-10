"""
Tests specifically for SessionAware JWT Authentication functionality
These tests use the SessionAwareJWTAuthentication to validate session enforcement
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserSession

User = get_user_model()


@override_settings(
    REST_FRAMEWORK={
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'apps.authentication.authentication.SessionAwareJWTAuthentication',
        ),
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
    },
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
)
class SessionAwareAuthenticationTestCase(APITestCase):
    """Test SessionAware JWT Authentication enforcement"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            is_active=True
        )
    
    def create_session_and_authenticate(self):
        """Helper to create session and authenticate user"""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        # Create user session with both JTIs
        session = UserSession.objects.create(
            user=self.user,
            session_key='test-session',
            device_info='Test Device',
            ip_address='127.0.0.1',
            jti=str(refresh['jti']),
            access_jti=str(access['jti'])
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access)}')
        return {
            'session': session,
            'access': str(access),
            'refresh': str(refresh)
        }
    
    def test_active_session_allows_access(self):
        """Test that active session allows API access"""
        auth_data = self.create_session_and_authenticate()
        
        url = reverse('user-sessions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_deactivated_session_blocks_access(self):
        """Test that deactivated session blocks API access"""
        auth_data = self.create_session_and_authenticate()
        
        # Deactivate the session
        session = auth_data['session']
        session.deactivate()
        
        # Try to access protected endpoint
        url = reverse('user-sessions')
        response = self.client.get(url)
        
        # Should be blocked due to deactivated session
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Session has been terminated', response.data.get('detail', ''))
    
    def test_nonexistent_session_blocks_access(self):
        """Test that JWT without matching session blocks access"""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        # Don't create UserSession - JWT exists but no session record
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access)}')
        
        url = reverse('user-sessions')
        response = self.client.get(url)
        
        # Should be blocked due to missing session
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_session_aware_token_refresh(self):
        """Test that token refresh validates and updates session"""
        auth_data = self.create_session_and_authenticate()
        
        # Test refresh with active session
        url = reverse('token-refresh')
        data = {'refresh': auth_data['refresh']}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify session JTI was updated
        session = auth_data['session']
        session.refresh_from_db()
        new_refresh_token = RefreshToken(response.data['refresh'])
        self.assertEqual(session.jti, str(new_refresh_token['jti']))
    
    def test_token_refresh_with_deactivated_session_fails(self):
        """Test that token refresh fails with deactivated session"""
        auth_data = self.create_session_and_authenticate()
        
        # Deactivate session
        session = auth_data['session']
        session.deactivate()
        
        # Try to refresh token
        url = reverse('token-refresh')
        data = {'refresh': auth_data['refresh']}
        response = self.client.post(url, data)
        
        # Should fail due to deactivated session
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Session has been terminated', response.data.get('detail', ''))


@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3', 
            'NAME': ':memory:',
        }
    }
)
class SessionUtilsTestCase(TestCase):
    """Test session utility functions"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!'
        )
    
    def test_session_stats(self):
        """Test session statistics function"""
        from .session_utils import get_session_stats
        
        # Create some sessions
        UserSession.objects.create(
            user=self.user,
            session_key='session-1',
            device_info='Device 1',
            ip_address='127.0.0.1',
            is_active=True
        )
        UserSession.objects.create(
            user=self.user,
            session_key='session-2',
            device_info='Device 2',
            ip_address='127.0.0.2',
            is_active=False  # Inactive
        )
        
        stats = get_session_stats(self.user)
        
        self.assertEqual(stats['active_sessions'], 1)
        self.assertEqual(stats['total_sessions'], 2)
        self.assertIn('max_allowed', stats)
        self.assertIn('expire_days', stats)
    
    def test_max_sessions_enforcement(self):
        """Test max sessions per user enforcement"""
        from .session_utils import enforce_max_sessions_per_user
        from django.conf import settings
        
        # Mock settings for this test
        with override_settings(SESSION_SECURITY={'MAX_SESSIONS_PER_USER': 2}):
            # Create 3 sessions
            sessions = []
            for i in range(3):
                session = UserSession.objects.create(
                    user=self.user,
                    session_key=f'session-{i}',
                    device_info=f'Device {i}',
                    ip_address='127.0.0.1',
                    is_active=True
                )
                sessions.append(session)
            
            # Enforce limit
            enforce_max_sessions_per_user(self.user)
            
            # Check that oldest session was deactivated
            sessions[0].refresh_from_db()
            self.assertFalse(sessions[0].is_active)
            
            # Check that newer sessions are still active
            sessions[1].refresh_from_db()
            sessions[2].refresh_from_db()
            self.assertTrue(sessions[1].is_active)
            self.assertTrue(sessions[2].is_active)