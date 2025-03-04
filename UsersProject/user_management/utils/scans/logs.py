import os
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone

from ...models import SystemLog

# Create a logger
logger = logging.getLogger(__name__)

def log_scan_operation(message, level="info", event=None):
    """Log scan operations to both file and database."""
    try:
        # Get current date for log file name
        current_date = datetime.now().strftime('%Y%m%d')
        scan_log_path = os.path.join(settings.BASE_DIR, 'logs', f'scan_operations_{current_date}.log')
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(scan_log_path), exist_ok=True)
        
        # Format the message with timestamp
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        formatted_msg = f"{timestamp} {message}"
        
        # Log to scan operations log file
        with open(scan_log_path, 'a') as f:
            f.write(formatted_msg + '\n')
        
        # Also log to copy_log.txt
        with open(os.path.join(settings.BASE_DIR, 'copy_log.txt'), 'a') as f:
            f.write(formatted_msg + '\n')
            
        # Save to database - ensure event is not None
        if event is None:
            # Set a default event based on the message or level
            if level.upper() == 'ERROR':
                event = 'SCAN_ERROR'
            else:
                event = 'SCAN_INFO'  # Default event for non-error messages
                
        try:
            SystemLog.objects.create(
                timestamp=timezone.now(),
                message=message,
                level=level.upper(),
                category="FILE_SCAN",
                event=event
            )
        except Exception as db_error:
            logger.error(f"Error saving to database: {str(db_error)}")
            raise
            
        # Log the message using the logger
        if level.upper() == 'ERROR':
            logger.error(formatted_msg)
        else:
            logger.info(formatted_msg)
            
        # Print to console for immediate feedback
        print(formatted_msg)
            
    except Exception as e:
        logger.error(f"Error logging: {str(e)}")
        raise  # Re-raise the exception to make sure we don't silently fail