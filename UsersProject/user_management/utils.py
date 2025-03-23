import logging
from django.utils import timezone
from .models import AuditLog, Notification, SystemLog, Computer
from typing import Optional, Dict, Any
from django.http import HttpRequest, Http404

logger = logging.getLogger('user_management')

def log_scan_operation(message, level="info"):
    """Log a scan operation to both file and database"""
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

def notify_scan_started(user=None):
    """Create notification for scan start"""
    Notification.objects.create(
        title="Scan Started",
        message="A new scan has been initiated",
        level="info",
        is_read=False,
        user=user
    )

def notify_scan_completed(user=None):
    """Create notification for scan completion"""
    Notification.objects.create(
        title="Scan Completed",
        message="The scan has completed successfully",
        level="success",
        is_read=False,
        user=user
    )

def notify_scan_error(error_message, user=None):
    """Create notification for scan error"""
    Notification.objects.create(
        title="Scan Error",
        message=error_message,
        level="error",
        is_read=False,
        user=user
    )

def process_onet_pdf(file_path):
    """Process a single O*NET PDF file"""
    try:
        # For now, just simulate processing
        # In a real implementation, this would:
        # 1. Extract text from PDF
        # 2. Parse O*NET data
        # 3. Generate new filename
        # 4. Move/rename file
        return True, "processed_file.pdf"
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        return False, None

def log_system_event(
    category: str,
    event: str,
    message: str,
    level: str = 'INFO',
    user = None,
    computer = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[HttpRequest] = None
) -> SystemLog:
    """
    Create a system log entry with the given parameters.
    
    Args:
        category: Log category from SystemLog.CATEGORY_CHOICES
        event: Event type from SystemLog.EVENT_CHOICES
        message: Human-readable message describing the event
        level: Log level from SystemLog.LEVEL_CHOICES (default: 'INFO')
        user: CustomUser instance or None
        computer: Computer instance or None
        details: Additional structured data to store with the log
        request: HttpRequest object to extract IP and user agent
    
    Returns:
        Created SystemLog instance
    """
    log_entry = SystemLog(
        level=level,
        category=category,
        event=event,
        message=message,
        user=user,
        computer=computer,
        details=details or {},
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
    """
    base_details = {
        'file_path': file_path,
        'file_type': file_path.split('.')[-1].lower() if '.' in file_path else 'unknown',
    }
    if details:
        base_details.update(details)
    
    message = f"{event.replace('_', ' ').title()}: {file_path}"
    
    return log_system_event(
        category='FILE_SCAN',
        event=event,
        message=message,
        level=level,
        user=user,
        computer=computer,
        details=base_details,
        request=request
    )

def log_computer_status(
    event: str,
    computer,
    user = None,
    level: str = 'INFO',
    details: Optional[Dict[str, Any]] = None,
    request: Optional[HttpRequest] = None
) -> SystemLog:
    """
    Log a computer status event with standardized message formatting.
    """
    base_details = {
        'computer_name': computer.name,
        'computer_id': str(computer.id),
        'status': computer.status,
    }
    if details:
        base_details.update(details)
    
    message = f"Computer {computer.name}: {event.replace('_', ' ').title()}"
    
    return log_system_event(
        category='COMPUTER_STATUS',
        event=event,
        message=message,
        level=level,
        user=user,
        computer=computer,
        details=base_details,
        request=request
    )

def get_computer_or_404(computer_id):
    """
    Get a computer by ID or raise Http404 if not found.
    Also verifies that the computer is online.
    """
    from django.http import Http404
    from .models import Computer
    
    try:
        computer = Computer.objects.get(id=computer_id)
        if not computer.is_online():
            raise Http404("Computer is offline")
        return computer
    except Computer.DoesNotExist:
        raise Http404("Computer not found")
