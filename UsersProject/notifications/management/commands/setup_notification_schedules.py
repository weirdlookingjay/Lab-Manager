from django.core.management.base import BaseCommand
from notifications.tasks import schedule_notification_digests

class Command(BaseCommand):
    help = 'Sets up scheduled tasks for notifications'

    def handle(self, *args, **kwargs):
        schedule_notification_digests()
        self.stdout.write(self.style.SUCCESS('Successfully scheduled notification digests'))
