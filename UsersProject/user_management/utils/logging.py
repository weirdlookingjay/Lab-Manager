import logging
import os
from datetime import datetime
from django.utils import timezone
from ..models import SystemLog, AuditLog

logger = logging.getLogger('scan_operations')
logger.setLevel(logging.DEBUG)

def log_scan_operation(message, level="info", category="FILE_SCAN", event=None):
    """Log a scan operation to both file and database"""
    # Log to file
    if level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)
    
    # Log to database
    SystemLog.objects.create(
        timestamp=timezone.now(),
        message=message,
        level=level.upper(),
        category=category,
        event=event
    )

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
