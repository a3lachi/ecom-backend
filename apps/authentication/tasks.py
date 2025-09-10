from django.core.management import call_command
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_sessions():
    """
    Periodic task to clean up expired user sessions.
    Should be run daily via Celery Beat.
    """
    try:
        call_command('cleanup_sessions', days=30, verbosity=0)
        logger.info("Successfully cleaned up expired user sessions")
    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {str(e)}")
        raise


@shared_task  
def cleanup_old_security_attempts():
    """
    Periodic task to clean up old security attempts.
    Keep only last 90 days of security logs.
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from .models import SecurityAttempt
        
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = SecurityAttempt.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old security attempts")
    except Exception as e:
        logger.error(f"Failed to cleanup old security attempts: {str(e)}")
        raise