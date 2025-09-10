"""
Session management utility functions that use the SESSION_SECURITY settings
"""
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from .models import UserSession

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


def get_session_security_setting(key, default=None):
    """Get session security setting with fallback to default"""
    session_settings = getattr(settings, 'SESSION_SECURITY', {})
    return session_settings.get(key, default)


def enforce_max_sessions_per_user(user):
    """
    Enforce maximum sessions per user by deactivating oldest sessions
    """
    max_sessions = get_session_security_setting('MAX_SESSIONS_PER_USER', 0)
    
    if max_sessions == 0:  # Unlimited sessions
        return
    
    active_sessions = UserSession.objects.filter(
        user=user,
        is_active=True
    ).order_by('-last_activity')
    
    if active_sessions.count() > max_sessions:
        # Deactivate oldest sessions
        sessions_to_deactivate = active_sessions[max_sessions:]
        deactivated_count = 0
        
        for session in sessions_to_deactivate:
            session.deactivate()
            deactivated_count += 1
        
        if get_session_security_setting('LOG_SESSION_ACTIVITIES', True):
            security_logger.warning(
                f"Enforced max sessions limit for user {user.email}. "
                f"Deactivated {deactivated_count} oldest sessions. "
                f"Limit: {max_sessions}, Active: {active_sessions.count()}"
            )


def cleanup_expired_sessions():
    """
    Clean up sessions that have exceeded the expiry time
    """
    if not get_session_security_setting('AUTO_CLEANUP_SESSIONS', True):
        return
    
    expire_days = get_session_security_setting('SESSION_EXPIRE_DAYS', 30)
    cutoff_date = timezone.now() - timedelta(days=expire_days)
    
    expired_sessions = UserSession.objects.filter(
        last_activity__lt=cutoff_date,
        is_active=True
    )
    
    count = expired_sessions.count()
    if count > 0:
        expired_sessions.update(is_active=False)
        
        if get_session_security_setting('LOG_SESSION_ACTIVITIES', True):
            logger.info(f"Auto-cleanup: Deactivated {count} expired sessions")


def detect_suspicious_session_activity(user, request):
    """
    Detect suspicious session activity and optionally force logout
    """
    if not get_session_security_setting('FORCE_LOGOUT_ON_SUSPICIOUS_ACTIVITY', True):
        return False
    
    from .views import get_client_ip
    
    current_ip = get_client_ip(request)
    
    # Check for sessions from different IPs in the last hour
    recent_sessions = UserSession.objects.filter(
        user=user,
        is_active=True,
        last_activity__gte=timezone.now() - timedelta(hours=1)
    ).exclude(ip_address=current_ip)
    
    if recent_sessions.count() > 2:  # More than 2 different IPs in 1 hour
        security_logger.warning(
            f"Suspicious activity detected for user {user.email}. "
            f"Multiple active sessions from different IPs: {current_ip} and others. "
            f"Consider manual review."
        )
        return True
    
    return False


def log_session_activity(user, activity, request=None, extra_data=None):
    """
    Log session-related activities for security monitoring
    """
    if not get_session_security_setting('LOG_SESSION_ACTIVITIES', True):
        return
    
    log_data = {
        'user': user.email,
        'activity': activity,
        'timestamp': timezone.now().isoformat(),
    }
    
    if request:
        from .views import get_client_ip, get_user_agent
        log_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': get_user_agent(request)[:200],  # Truncate long user agents
        })
    
    if extra_data:
        log_data.update(extra_data)
    
    logger.info(f"Session activity: {log_data}")


def get_session_stats(user):
    """
    Get session statistics for a user
    """
    return {
        'active_sessions': UserSession.objects.filter(user=user, is_active=True).count(),
        'total_sessions': UserSession.objects.filter(user=user).count(),
        'max_allowed': get_session_security_setting('MAX_SESSIONS_PER_USER', 0),
        'expire_days': get_session_security_setting('SESSION_EXPIRE_DAYS', 30),
    }