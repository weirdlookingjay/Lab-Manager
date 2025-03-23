import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from django.utils import timezone
from django.http import HttpRequest

from ..models import SystemLog, AuditLog

logger = logging.getLogger('user_management')

def log_scan_operation(message: str, level: str = "info") -> None:
    """Log a scan operation to both file and database."""
    # Log to file
    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)
    
    # Log to database
    AuditLog.objects.create(
        timestamp=timezone.now(),
        message=message,
        level=level.upper()
    )

def log_file_event(
    event: str,
    file_path: str,
    computer,
    user = None,
    level: str = 'INFO',
    details: Optional[Dict[str, Any]] = None,
    request: Optional[HttpRequest] = None
) -> SystemLog:
    """
    Log a file-related event with standardized message formatting.
    
    Args:
        event: Event type (e.g. 'list_files', 'download_file', 'upload_file')
        file_path: Path to the file being operated on
        computer: Computer instance associated with the event
        user: Optional user who triggered the event
        level: Log level (default: 'INFO')
        details: Additional structured data to store with the log
        request: Optional HttpRequest to extract IP and user agent
    
    Returns:
        Created SystemLog instance
    """
    base_details = {
        'file_path': file_path,
        'file_type': file_path.split('.')[-1].lower() if '.' in file_path else 'unknown',
    }
    if details:
        base_details.update(details)
    
    message = f"{event.replace('_', ' ').title()}: {file_path}"
    
    log_entry = SystemLog(
        level=level,
        category='FILE_SYSTEM',
        event=event,
        message=message,
        user=user,
        computer=computer,
        details=base_details
    )
    
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            log_entry.ip_address = x_forwarded_for.split(',')[0]
        else:
            log_entry.ip_address = request.META.get('REMOTE_ADDR')
            
        # Get user agent
        log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    log_entry.save()
    return log_entry

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Create a file handler
log_file = os.path.join(logs_dir, f'scan_operations_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
