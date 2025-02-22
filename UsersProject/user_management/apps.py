from django.apps import AppConfig

class UserManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management'

    def ready(self):
        """
        Initialize app-specific tasks when Django starts
        """
        try:
            # Import and schedule tasks
            from .tasks import schedule_file_operations
            
            # Schedule any initial file operations if needed
            # schedule_file_operations(hour=0, minute=0)  # Example: Schedule for midnight
            
        except Exception as e:
            # Log any errors but don't prevent app from starting
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing tasks: {str(e)}")
