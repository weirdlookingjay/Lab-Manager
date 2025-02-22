from .models import Notification, NotificationPreference, PDFAttachment
from .constants import NOTIFICATION_TEMPLATES
import psutil
from datetime import datetime
from django.utils import timezone
import logging
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
from django.core.files import File

logger = logging.getLogger(__name__)

User = get_user_model()

def send_notification(user, title, message, notification_type='info', priority='low'):
    """
    Basic notification sender
    """
    # Ensure we have a timestamp
    now = timezone.now()
    logger.info(f"Creating notification with timestamp {now}")
    
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=notification_type,
        priority=priority,
        created_at=now
    )
    
    logger.info(f"Created notification {notification.id} with created_at={notification.created_at}")
    return notification

def send_template_notification(user, template_key, context=None):
    """
    Send a notification using a predefined template
    
    Args:
        user: User object - the recipient of the notification
        template_key: str - key from NOTIFICATION_TEMPLATES
        context: dict - variables to format the template with
    """
    if template_key not in NOTIFICATION_TEMPLATES:
        raise ValueError(f"Unknown notification template: {template_key}")

    template = NOTIFICATION_TEMPLATES[template_key]
    context = context or {}

    title = template["title"].format(**context)
    message = template["message"].format(**context)

    logger.info(f"Sending template notification: {template_key}")
    logger.info(f"Context: {context}")

    notification = send_notification(
        user=user,
        title=title,
        message=message,
        notification_type=template["type"],
        priority=template["priority"]
    )
    
    logger.info(f"Template notification created: {notification.id}, created_at={notification.created_at}")
    return notification

def check_storage_and_notify(user, path, threshold_warning=20, threshold_critical=10):
    """
    Check storage space and send notifications if below thresholds
    """
    try:
        usage = psutil.disk_usage(path)
        free_percent = usage.free / usage.total * 100

        if free_percent <= threshold_critical:
            send_template_notification(user, "STORAGE_CRITICAL", {
                "space_left": f"{usage.free / (1024**3):.2f}GB"
            })
        elif free_percent <= threshold_warning:
            send_template_notification(user, "STORAGE_LOW", {
                "threshold": threshold_warning,
                "current": f"{free_percent:.1f}"
            })
    except Exception as e:
        send_notification(
            user=user,
            title="Storage Check Failed",
            message=f"Failed to check storage space: {str(e)}",
            notification_type="error",
            priority="high"
        )

def notify_system_status(user, computer_name, is_online, last_seen=None):
    """
    Send notification about system status
    """
    if is_online:
        send_template_notification(user, "SYSTEM_ONLINE", {
            "computer_name": computer_name
        })
    else:
        send_template_notification(user, "SYSTEM_OFFLINE", {
            "computer_name": computer_name,
            "last_seen": last_seen or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

def notify_scan_status(user, computer_name, status, **kwargs):
    """
    Send notification about scan status
    """
    send_template_notification(user, f"SCAN_{status.upper()}", {
        "computer_name": computer_name,
        **kwargs
    })

def notify_file_operation(user, operation, filename, **kwargs):
    """
    Send notification about file operations
    """
    send_template_notification(user, f"FILE_{operation.upper()}", {
        "filename": filename,
        **kwargs
    })

def attach_pdf_files(email_message, pdf_files):
    """
    Attach PDF files to an email message.
    
    Args:
        email_message: EmailMessage instance
        pdf_files: List of paths to PDF files
    """
    for pdf_path in pdf_files:
        try:
            if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
                with open(pdf_path, 'rb') as f:
                    content = f.read()
                    email_message.attach(os.path.basename(pdf_path), content, 'application/pdf')
                logger.info(f"Attached PDF file: {pdf_path}")
            else:
                logger.warning(f"PDF file not found or invalid: {pdf_path}")
        except Exception as e:
            logger.error(f"Error attaching PDF file {pdf_path}: {str(e)}")

def attach_files(email_message, attachments):
    """
    Attach uploaded files to an email message.
    
    Args:
        email_message: EmailMessage instance
        attachments: List of UploadedFile objects
    """
    for file in attachments:
        try:
            email_message.attach(file.name, file.read(), file.content_type)
            logger.info(f"Attached file: {file.name}")
        except Exception as e:
            logger.error(f"Error attaching file {file.name}: {str(e)}")

def send_error_notification(error_type, title, message, details=None, attachments=None):
    """
    Send error notifications to admin users based on their preferences.
    
    Args:
        error_type: One of 'scan_error', 'pdf_error', 'computer_offline'
        title: Error title
        message: Error message
        details: Optional dictionary with additional error details
        attachments: Optional list of UploadedFile objects to attach
    """
    logger.info(f"Sending error notification: {error_type} - {title}")
    
    # Get all admin users with appropriate notification preferences
    preference_field = {
        'scan_error': 'notify_scan_errors',
        'pdf_error': 'notify_pdf_errors',
        'computer_offline': 'notify_computer_offline'
    }.get(error_type)
    
    if not preference_field:
        logger.error(f"Invalid error type: {error_type}")
        return
    
    # Get admin users who have enabled this type of notification
    admin_preferences = NotificationPreference.objects.filter(
        user__is_staff=True,
        email_enabled=True,
        **{preference_field: True}
    ).select_related('user')
    
    logger.info(f"Found {admin_preferences.count()} admin users to notify")
    
    # Format details for notification
    detail_text = "\n".join([f"{k}: {v}" for k, v in (details or {}).items()])
    full_message = f"{message}\n\nDetails:\n{detail_text}" if detail_text else message
    
    # Send notifications to each admin
    for pref in admin_preferences:
        try:
            notification = send_notification(
                user=pref.user,
                title=title,
                message=full_message,
                notification_type='error',
                priority='high'
            )
            logger.info(f"Created notification {notification.id} for admin {pref.user.username}")
            
            # Send immediate email if enabled and not using digest
            if pref.email_enabled and (pref.email_immediate or not pref.email_digest):
                logger.info(f"Sending immediate email to {pref.user.email} (email_enabled={pref.email_enabled}, email_immediate={pref.email_immediate}, email_digest={pref.email_digest})")
                try:
                    logger.info(f"Email settings: FROM={settings.DEFAULT_FROM_EMAIL}, TO={pref.user.email}")
                    
                    # Render HTML email template
                    html_message = render_to_string('notifications/email/error_notification.html', {
                        'error_type': error_type,
                        'title': title,
                        'message': message,
                        'details': details or {},
                        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z'),
                        'has_attachments': bool(attachments)
                    })
                    
                    # Create plain text version
                    plain_message = strip_tags(html_message)
                    
                    # Create email message
                    email = EmailMessage(
                        subject=f"Alert: {title}",
                        body=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[pref.user.email]
                    )
                    email.content_subtype = "html"
                    
                    # Attach files if any
                    if attachments:
                        logger.info(f"Attaching {len(attachments)} files")
                        attach_files(email, attachments)
                    
                    # Send email
                    email.send(fail_silently=False)
                    logger.info("Email sent successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to send email: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"Error sending notification to admin {pref.user.username}: {str(e)}")

def store_scanned_pdf(file_path, computer_label, user=None):
    """
    Store a scanned PDF file in the web storage system.
    
    Args:
        file_path: Path to the PDF file
        computer_label: Label of the computer that was scanned
        user: Optional user who initiated the scan
    
    Returns:
        PDFAttachment instance if successful, None if failed
    """
    try:
        # Get the original filename
        original_filename = os.path.basename(file_path)
        
        # Create a new PDFAttachment instance
        with open(file_path, 'rb') as f:
            attachment = PDFAttachment(
                original_filename=f"{computer_label}_{original_filename}",
                uploaded_by=user,
                file_size=os.path.getsize(file_path)
            )
            
            # Save the file to the storage system
            attachment.file.save(
                f"{computer_label}/{original_filename}",
                File(f),
                save=True
            )
            
        return attachment
    except Exception as e:
        logger.error(f"Failed to store PDF {file_path}: {str(e)}")
        return None

# Example usage:
"""
# For scanning errors:
send_error_notification(
    error_type='scan_error',
    title='Scanning Failed',
    message='Failed to scan documents from Computer XYZ',
    details={
        'Computer': 'XYZ',
        'Error': 'Connection timeout',
        'Time': '2025-02-11 15:30:00'
    }
)

# For PDF errors:
send_error_notification(
    error_type='pdf_error',
    title='PDF Processing Failed',
    message='Failed to process PDF file',
    details={
        'File': 'document.pdf',
        'Error': 'Invalid PDF format',
        'Location': os.path.join(settings.DESTINATION_ROOT, 'docs')
    }
)

# For offline computers:
send_error_notification(
    error_type='computer_offline',
    title='Computer Offline',
    message='Computer ABC is not responding',
    details={
        'Computer': 'ABC',
        'Last Seen': '2025-02-11 14:00:00',
        'IP': '192.168.1.100'
    }
)
"""
