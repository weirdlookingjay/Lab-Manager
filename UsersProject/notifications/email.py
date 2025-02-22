from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Notification

def send_notification_email(user, notification):
    """Send a single notification email"""
    subject = notification.title
    html_content = render_to_string('notifications/email/single_notification.html', {
        'notification': notification,
        'user': user
    })
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    return email.send()

def send_notification_digest(user):
    """Send a digest of unread notifications"""
    # Get unread notifications from the last NOTIFICATION_DIGEST_INTERVAL hours
    interval = timezone.now() - timedelta(hours=settings.NOTIFICATION_DIGEST_INTERVAL)
    notifications = Notification.objects.filter(
        user=user,
        is_read=False,
        created_at__gte=interval
    ).order_by('-created_at')
    
    if not notifications.exists():
        return False
        
    subject = f"Notification Digest - {notifications.count()} new notifications"
    html_content = render_to_string('notifications/email/digest.html', {
        'notifications': notifications,
        'user': user,
        'interval': settings.NOTIFICATION_DIGEST_INTERVAL
    })
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    return email.send()
