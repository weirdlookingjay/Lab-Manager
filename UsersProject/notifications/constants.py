"""
Constants for the notification system specifically tailored for the PDF scanning application
"""

# System Health Notifications
SYSTEM_OFFLINE = "system_offline"
SYSTEM_ONLINE = "system_online"
SYSTEM_WARNING = "system_warning"

# Scan Status Notifications
SCAN_STARTED = "scan_started"
SCAN_COMPLETED = "scan_completed"
SCAN_FAILED = "scan_failed"
SCAN_PARTIAL = "scan_partial"

# File Operations Notifications
FILE_COPIED = "file_copied"
FILE_FAILED = "file_failed"
FILE_DUPLICATE = "file_duplicate"
FILE_MODIFIED = "file_modified"

# Storage Notifications
STORAGE_LOW = "storage_low"
STORAGE_CRITICAL = "storage_critical"

# Access Notifications
ACCESS_DENIED = "access_denied"
ACCESS_ERROR = "access_error"

# Notification Templates
NOTIFICATION_TEMPLATES = {
    SYSTEM_OFFLINE: {
        "title": "Computer Offline: {computer_name}",
        "message": "Computer {computer_name} is no longer accessible. Last seen: {last_seen}",
        "type": "error",
        "priority": "high"
    },
    SYSTEM_ONLINE: {
        "title": "Computer Online: {computer_name}",
        "message": "Computer {computer_name} is now online and accessible",
        "type": "success",
        "priority": "low"
    },
    SYSTEM_WARNING: {
        "title": "System Warning: {computer_name}",
        "message": "Performance issues detected on {computer_name}: {details}",
        "type": "warning",
        "priority": "medium"
    },
    SCAN_STARTED: {
        "title": "Scan Started: {computer_name}",
        "message": "Started scanning {computer_name} for PDF files",
        "type": "info",
        "priority": "low"
    },
    SCAN_COMPLETED: {
        "title": "Scan Completed: {computer_name}",
        "message": "Successfully scanned {computer_name}. Found {file_count} PDF files",
        "type": "success",
        "priority": "low"
    },
    SCAN_FAILED: {
        "title": "Scan Failed: {computer_name}",
        "message": "Failed to scan {computer_name}. Error: {error}",
        "type": "error",
        "priority": "high"
    },
    SCAN_PARTIAL: {
        "title": "Partial Scan: {computer_name}",
        "message": "Partial scan completed on {computer_name}. {success_count} successful, {failed_count} failed",
        "type": "warning",
        "priority": "medium"
    },
    FILE_COPIED: {
        "title": "File Copied Successfully",
        "message": "File '{filename}' successfully copied from {source} to {destination}",
        "type": "success",
        "priority": "low"
    },
    FILE_FAILED: {
        "title": "File Copy Failed",
        "message": "Failed to copy '{filename}' from {source}. Error: {error}",
        "type": "error",
        "priority": "high"
    },
    FILE_DUPLICATE: {
        "title": "Duplicate File Detected",
        "message": "File '{filename}' already exists in destination. Action taken: {action}",
        "type": "warning",
        "priority": "medium"
    },
    FILE_MODIFIED: {
        "title": "File Modified",
        "message": "File '{filename}' has been modified since last scan",
        "type": "info",
        "priority": "medium"
    },
    STORAGE_LOW: {
        "title": "Storage Space Low",
        "message": "Available storage space is below {threshold}%. Current: {current}%",
        "type": "warning",
        "priority": "medium"
    },
    STORAGE_CRITICAL: {
        "title": "Storage Space Critical",
        "message": "Critical storage space alert! Only {space_left} remaining",
        "type": "error",
        "priority": "critical"
    },
    ACCESS_DENIED: {
        "title": "Access Denied",
        "message": "Access denied to {path} on {computer_name}. Check permissions",
        "type": "error",
        "priority": "high"
    },
    ACCESS_ERROR: {
        "title": "Access Error",
        "message": "Error accessing {path} on {computer_name}: {error}",
        "type": "error",
        "priority": "high"
    }
}
