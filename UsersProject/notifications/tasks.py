from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging
from .models import NotificationPreference, Notification

User = get_user_model()
logger = logging.getLogger(__name__)

def send_automated_notification(user_ids, subject, message, notification_type='info'):
    """Send automated notifications to specified users"""
    users = User.objects.filter(id__in=user_ids)
    
    for user in users:
        try:
            # Create notification
            notification = Notification.objects.create(
                user=user,
                title=subject,
                message=message,
                type=notification_type,
                priority='normal'
            )
            
            # Check if user wants email notifications
            pref = NotificationPreference.objects.get_or_create(user=user)[0]
            if pref.email_enabled and not pref.email_digest:
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    logger.info(f"Sent automated email to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send automated email to {user.email}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing automated notification for {user.email}: {str(e)}")

def send_notification_digests():
    """Task to send notification digests to users"""
    # Get all users with email digests enabled
    preferences = NotificationPreference.objects.filter(
        email_enabled=True,
        email_digest=True
    ).select_related('user')
    
    for pref in preferences:
        try:
            # Get unread notifications from the last 24 hours
            since = timezone.now() - timedelta(hours=24)
            notifications = Notification.objects.filter(
                user=pref.user,
                created_at__gte=since,
                is_read=False
            )
            
            if notifications.exists():
                # Prepare digest message
                subject = "Your Daily Notification Digest"
                message = "Here are your unread notifications from the last 24 hours:\n\n"
                
                for notif in notifications:
                    message += f"- {notif.title}\n"
                    message += f"  {notif.message}\n"
                    message += f"  Sent: {notif.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                # Send digest email
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[pref.user.email],
                        fail_silently=False,
                    )
                    logger.info(f"Sent digest email to {pref.user.email}")
                except Exception as e:
                    logger.error(f"Failed to send digest to {pref.user.email}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing digest for {pref.user.email}: {str(e)}")

def schedule_notification_digests():
    """Schedule the next digest run"""
    from django_q.tasks import schedule
    from django_q.models import Schedule
    
    # Delete existing schedules
    Schedule.objects.filter(name='send_notification_digests').delete()
    
    # Schedule daily digest
    schedule(
        'notifications.tasks.send_notification_digests',
        name='send_notification_digests',
        schedule_type='D',  # Daily
        next_run=timezone.now().replace(hour=9, minute=0, second=0)  # Run at 9 AM
    )

def test_automated_notification(user_ids=None):
    """Test function to send an automated notification"""
    if user_ids is None:
        # Get all active users if no specific users provided
        user_ids = User.objects.filter(is_active=True).values_list('id', flat=True)
    
    send_automated_notification(
        user_ids=user_ids,
        subject="Test Automated Notification",
        message="This is a test of the automated notification system.",
        notification_type='info'
    )
