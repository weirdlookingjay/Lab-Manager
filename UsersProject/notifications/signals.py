from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Notification
from .email import send_notification_email
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from .tasks import send_automated_notification
from .models import NotificationPreference

User = get_user_model()

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    if created:
        # Send WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.user.id}",
            {
                "type": "notification_message",
                "message": {
                    "id": str(instance.id),
                    "title": instance.title,
                    "message": instance.message,
                    "type": instance.type,
                    "createdAt": instance.created_at.isoformat()
                }
            }
        )
        
        # Check if immediate email notification is enabled
        try:
            preferences = instance.user.notification_preferences
            if preferences.email_enabled and preferences.email_immediate:
                send_notification_email(instance.user, instance)
        except Exception as e:
            print(f"Failed to send immediate email notification: {str(e)}")

@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences for new users"""
    if created:
        NotificationPreference.objects.create(
            user=instance,
            email_enabled=True,  # Enable email notifications by default
            email_digest=False   # Disable digest by default
        )
        
        # Send welcome notification
        send_automated_notification(
            user_ids=[instance.id],
            subject="Welcome to the System",
            message=f"Welcome {instance.username}! Your account has been successfully created.",
            notification_type='success'
        )

# Example of how to add more automated notifications:
"""
@receiver(post_save, sender=YourModel)
def notify_on_model_change(sender, instance, created, **kwargs):
    if created:
        # Notify admins of new items
        admin_ids = User.objects.filter(is_staff=True).values_list('id', flat=True)
        send_automated_notification(
            user_ids=admin_ids,
            subject="New Item Created",
            message=f"A new {instance._meta.verbose_name} has been created.",
            notification_type='info'
        )
"""
