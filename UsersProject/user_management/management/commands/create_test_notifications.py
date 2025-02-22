from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_management.models import Notification
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test notifications for development'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='The ID of the user to create notifications for')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} does not exist'))
            return

        # Delete existing notifications for this user
        Notification.objects.filter(user=user).delete()

        # Create sample notifications
        notifications = [
            {
                'title': 'New Scan Complete',
                'message': 'The scheduled scan of your network has completed successfully.',
                'type': 'success',
                'read': False
            },
            {
                'title': 'Security Alert',
                'message': 'Unusual activity detected on Device ABC-123. Please review the security logs.',
                'type': 'error',
                'read': False
            },
            {
                'title': 'System Update Available',
                'message': 'A new system update is available for your devices. Please review and install at your earliest convenience.',
                'type': 'info',
                'read': True
            },
            {
                'title': 'Backup Completed',
                'message': 'Weekly backup of all devices completed successfully.',
                'type': 'success',
                'read': True
            },
            {
                'title': 'Device Offline',
                'message': 'Device XYZ-789 has been offline for more than 30 minutes.',
                'type': 'error',
                'read': False
            }
        ]

        for notif in notifications:
            Notification.objects.create(
                user=user,
                title=notif['title'],
                message=notif['message'],
                type=notif['type'],
                read=notif['read']
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully created test notifications for user {user.username} (ID: {user.id})'))
