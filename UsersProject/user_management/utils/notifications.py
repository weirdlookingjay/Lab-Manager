from ..models import Notification, Computer
from django.contrib.auth import get_user_model

User = get_user_model()

def create_notification(user, title, message, notification_type='info'):
    """
    Create a notification for a specific user
    """
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=notification_type,
        read=False
    )

def notify_all_users(title, message, notification_type='info'):
    """
    Create a notification for all active users
    """
    notifications = []
    for user in User.objects.filter(is_active=True):
        notifications.append(
            Notification(
                user=user,
                title=title,
                message=message,
                type=notification_type,
                read=False
            )
        )
    return Notification.objects.bulk_create(notifications)

# Scan related notifications
def notify_scan_started(user, targets=None):
    target_str = f" for {targets}" if targets else ""
    create_notification(
        user,
        "Scan Started",
        f"A new scan has been initiated{target_str}.",
        'info'
    )

def notify_scan_completed(user, targets=None, issues_found=None):
    target_str = f" for {targets}" if targets else ""
    status = "completed successfully"
    notification_type = 'success'
    
    if issues_found:
        status = f"completed with {len(issues_found)} issues found"
        notification_type = 'error'
    
    create_notification(
        user,
        "Scan Completed",
        f"The scan{target_str} has {status}.",
        notification_type
    )

def notify_scan_error(user, error_message, targets=None):
    target_str = f" for {targets}" if targets else ""
    create_notification(
        user,
        "Scan Error",
        f"An error occurred during the scan{target_str}: {error_message}",
        'error'
    )

def notify_scan_started():
    """Create notification for scan start"""
    Notification.objects.create(
        title="Scan Started",
        message="A new scan has been initiated",
        type="info",
        read=False
    )

def notify_scan_completed():
    """Create notification for scan completion"""
    Notification.objects.create(
        title="Scan Completed",
        message="The scan has completed successfully",
        type="success",
        read=False
    )

def notify_scan_error(error_message):
    """Create notification for scan error"""
    Notification.objects.create(
        title="Scan Error",
        message=error_message,
        type="error",
        read=False
    )

# Device status notifications
def notify_device_status_change(device: Computer, status: str):
    """
    Notify about device status changes (online/offline)
    """
    notification_type = 'error' if status.lower() == 'offline' else 'success'
    notify_all_users(
        f"Device {status.title()}",
        f"Device {device.label} ({device.ip_address}) is now {status}.",
        notification_type
    )

# Backup notifications
def notify_backup_status(user, status: str, details: str = None):
    """
    Notify about backup status changes
    """
    title_map = {
        'started': ('Backup Started', 'info'),
        'completed': ('Backup Completed', 'success'),
        'failed': ('Backup Failed', 'error')
    }
    
    title, notification_type = title_map.get(status.lower(), ('Backup Update', 'info'))
    message = f"Backup {status}"
    if details:
        message += f": {details}"
    
    create_notification(user, title, message, notification_type)

# Security notifications
def notify_security_alert(severity: str, message: str, affected_devices=None):
    """
    Send security alert notifications
    """
    severity_map = {
        'low': 'info',
        'medium': 'warning',
        'high': 'error',
        'critical': 'error'
    }
    
    title = f"{severity.title()} Security Alert"
    
    if affected_devices:
        device_str = ", ".join([f"{d.label} ({d.ip_address})" for d in affected_devices])
        message = f"{message}\nAffected devices: {device_str}"
    
    notify_all_users(title, message, severity_map.get(severity.lower(), 'error'))
