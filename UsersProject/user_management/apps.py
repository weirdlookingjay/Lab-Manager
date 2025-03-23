from django.apps import AppConfig
import os

class UserManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management'

    def ready(self):
        # Only run in main process
        if os.environ.get('RUN_MAIN') != 'true':
            return

        # Start relay monitoring task
        from .tasks import monitor_relay_server
        monitor_relay_server.delay()
