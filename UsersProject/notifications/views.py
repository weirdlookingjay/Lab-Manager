from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from .models import Notification, NotificationPreference, PDFAttachment
from .serializers import NotificationSerializer, PDFAttachmentSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging
from .email import send_notification_email, send_notification_digest
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import os
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMessage
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

User = get_user_model()

logger = logging.getLogger(__name__)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        # Log the queryset data
        for notification in queryset:
            logger.info(f"Notification {notification.id}: created_at={notification.created_at}, title={notification.title}")
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Log the response data
        logger.info(f"API response data: {response.data}")
        return response

    def perform_create(self, serializer):
        notification = serializer.save(user=self.request.user)
        # Log the created notification
        logger.info(f"Created notification {notification.id}: created_at={notification.created_at}")
        # Send real-time notification
        self._send_notification(notification)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'notifications marked as read'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

    def _send_notification(self, notification):
        channel_layer = get_channel_layer()
        # Log the notification data
        logger.info(f"Sending WebSocket notification {notification.id}: created_at={notification.created_at}")
        
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.user.id}",
            {
                "type": "notification.message",
                "message": {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type,
                    "priority": notification.priority,
                    "createdAt": notification.created_at.isoformat() if notification.created_at else None
                }
            }
        )

class PDFAttachmentViewSet(viewsets.ModelViewSet):
    queryset = PDFAttachment.objects.all()
    serializer_class = PDFAttachmentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get('file')
        if file_obj:
            instance = serializer.save(
                uploaded_by=self.request.user,
                original_filename=file_obj.name,
                file_size=file_obj.size
            )
            return instance
        raise ValidationError("No file was submitted")

    def get_queryset(self):
        # Filter PDFs based on user permissions
        user = self.request.user
        if user.is_superuser:
            return PDFAttachment.objects.all()
        return PDFAttachment.objects.filter(uploaded_by=user)

# Test endpoints to demonstrate notifications
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_system_notification(request):
    """Test endpoint to simulate system notifications"""
    computer_name = request.data.get('computer_name', 'TestPC')
    is_online = request.data.get('is_online', False)
    
    notify_system_status(request.user, computer_name, is_online)
    return Response({'status': 'notification sent'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_scan_notification(request):
    """Test endpoint to simulate scan notifications"""
    computer_name = request.data.get('computer_name', 'TestPC')
    status = request.data.get('status', 'COMPLETED')
    file_count = request.data.get('file_count', 5)
    
    notify_scan_status(
        request.user,
        computer_name,
        status,
        file_count=file_count
    )
    return Response({'status': 'notification sent'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_file_notification(request):
    """Test endpoint to simulate file operation notifications"""
    operation = request.data.get('operation', 'COPIED')
    filename = request.data.get('filename', 'test.pdf')
    
    notify_file_operation(
        request.user,
        operation,
        filename,
        source='TestPC/documents',
        destination='final_directory'
    )
    return Response({'status': 'notification sent'})

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_preferences(request):
    """Get or update notification preferences"""
    try:
        pref, created = NotificationPreference.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            return Response({
                'email_enabled': pref.email_enabled,
                'email_digest': pref.email_digest,
                'email_immediate': pref.email_immediate,
                'notify_scan_errors': pref.notify_scan_errors,
                'notify_pdf_errors': pref.notify_pdf_errors,
                'notify_computer_offline': pref.notify_computer_offline,
                'computer_offline_threshold': pref.computer_offline_threshold,
            })
            
        # PUT request
        pref.email_enabled = request.data.get('email_enabled', pref.email_enabled)
        pref.email_digest = request.data.get('email_digest', pref.email_digest)
        pref.email_immediate = request.data.get('email_immediate', pref.email_immediate)
        pref.notify_scan_errors = request.data.get('notify_scan_errors', pref.notify_scan_errors)
        pref.notify_pdf_errors = request.data.get('notify_pdf_errors', pref.notify_pdf_errors)
        pref.notify_computer_offline = request.data.get('notify_computer_offline', pref.notify_computer_offline)
        pref.computer_offline_threshold = request.data.get('computer_offline_threshold', pref.computer_offline_threshold)
        pref.save()
        
        return Response({
            'message': 'Preferences updated successfully',
            'email_enabled': pref.email_enabled,
            'email_digest': pref.email_digest,
            'email_immediate': pref.email_immediate,
            'notify_scan_errors': pref.notify_scan_errors,
            'notify_pdf_errors': pref.notify_pdf_errors,
            'notify_computer_offline': pref.notify_computer_offline,
            'computer_offline_threshold': pref.computer_offline_threshold,
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_email_preferences(request):
    """Update user's email notification preferences"""
    pref, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if 'email_enabled' in request.data:
        pref.email_enabled = request.data['email_enabled']
    if 'email_digest' in request.data:
        pref.email_digest = request.data['email_digest']
    if 'email_immediate' in request.data:
        pref.email_immediate = request.data['email_immediate']
    
    pref.save()
    
    return Response({
        'email_enabled': pref.email_enabled,
        'email_digest': pref.email_digest,
        'email_immediate': pref.email_immediate
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_email_preferences(request):
    """Get user's email notification preferences"""
    pref, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    return Response({
        'email_enabled': pref.email_enabled,
        'email_digest': pref.email_digest,
        'email_immediate': pref.email_immediate
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Get user's notifications"""
    try:
        # Get query parameters
        show_archived = request.query_params.get('archived', 'false').lower() == 'true'
        
        # Base queryset
        notifications = Notification.objects.filter(user=request.user)
        
        # Filter archived/unarchived
        if not show_archived:
            notifications = notifications.filter(archived=False)
            
        # Order by creation date, newest first
        notifications = notifications.order_by('-created_at')
        
        # Serialize the notifications
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return Response({
            'error': 'Failed to fetch notifications'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_email_notification(request):
    """Test sending an email notification"""
    try:
        # Create a test notification
        notification = request.user.notifications.create(
            title="Test Email Notification",
            message="This is a test email notification to verify the system is working.",
            type='info'
        )
        
        # Send immediate email
        success = send_notification_email(request.user, notification)
        
        return Response({
            'success': success,
            'message': 'Test email sent successfully' if success else 'Failed to send test email'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_email_digest(request):
    """Test sending an email digest"""
    try:
        # Send digest email
        success = send_notification_digest(request.user)
        
        return Response({
            'success': success,
            'message': 'Test digest sent successfully' if success else 'No unread notifications to send'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['POST', 'OPTIONS'])
@permission_classes([IsAdminUser])
def admin_send_email(request):
    # Handle preflight request
    if request.method == 'OPTIONS':
        return Response(status=200)
        
    try:
        data = request.data
        logger.info(f"Received admin email request: {data}")
        
        # Validate required fields
        required_fields = ['subject', 'message', 'user_ids']
        for field in required_fields:
            if not data.get(field):
                logger.error(f"Missing required field: {field}")
                return Response({
                    "error": f"Missing required field: {field}"
                }, status=400)
        
        subject = data['subject']
        message = data['message']
        notification_type = data.get('type', 'info')
        user_ids = data['user_ids']
        attachment_urls = data.get('attachments', [])
        
        logger.info(f"Processing attachments: {attachment_urls}")
        
        # Get users
        users = User.objects.filter(id__in=user_ids)
        if not users.exists():
            logger.error(f"No users found for IDs: {user_ids}")
            return Response({
                "error": "No valid users found"
            }, status=400)
        
        # Get the attachments from our storage
        attachments = []
        for url in attachment_urls:
            try:
                # Extract the relative path from the URL
                logger.info(f"Processing attachment URL: {url}")
                relative_path = url.split(settings.MEDIA_URL)[-1]
                full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                logger.info(f"Full path: {full_path}")
                
                if os.path.exists(full_path):
                    attachments.append(full_path)
                    logger.info(f"Added attachment: {full_path}")
                else:
                    logger.warning(f"Attachment not found: {full_path}")
            except Exception as e:
                logger.error(f"Failed to process attachment {url}: {str(e)}", exc_info=True)
        
        logger.info(f"Found {len(attachments)} valid attachments")
        
        # Send email to each user
        successful_sends = 0
        failed_sends = []
        
        for user in users:
            try:
                # Render email template
                template_name = f'notifications/email/{notification_type}_email.html'
                html_content = render_to_string(template_name, {
                    'subject': subject,
                    'message': message,
                    'user': user,
                    'has_attachments': bool(attachments)
                })
                text_content = strip_tags(html_content)
                
                # Create email message
                email = EmailMessage(
                    subject=subject,
                    body=html_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                )
                email.content_subtype = "html"  # Set content type to HTML
                
                # Attach PDF files
                for attachment_path in attachments:
                    try:
                        with open(attachment_path, 'rb') as f:
                            file_name = os.path.basename(attachment_path)
                            email.attach(file_name, f.read(), 'application/pdf')
                            logger.info(f"Attached {file_name} to email for {user.email}")
                    except Exception as e:
                        logger.error(f"Failed to attach {attachment_path} to email: {str(e)}", exc_info=True)
                
                # Send email
                email.send()
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    title=subject,
                    message=message,
                    type=notification_type
                )
                
                successful_sends += 1
                logger.info(f"Successfully sent email to {user.email}")
                
            except Exception as e:
                error_msg = f"Failed to send email to {user.email}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                failed_sends.append({"email": user.email, "error": str(e)})
        
        # Return appropriate response based on success/failure
        if successful_sends == len(users):
            return Response({
                "message": f"Successfully sent email to {successful_sends} users",
                "successful_sends": successful_sends
            })
        elif successful_sends > 0:
            return Response({
                "message": f"Partially successful: sent {successful_sends} out of {len(users)} emails",
                "successful_sends": successful_sends,
                "failed_sends": failed_sends
            }, status=207)
        else:
            return Response({
                "error": "Failed to send all emails",
                "failed_sends": failed_sends
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in admin_send_email: {str(e)}", exc_info=True)
        return Response({
            "error": str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return Response({'error': 'Failed to mark notification as read'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def archive_notification(request, notification_id):
    """Archive a notification"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.archived = True
        notification.save()
        return Response({'status': 'success'})
    except Exception as e:
        logger.error(f"Error archiving notification: {str(e)}")
        return Response({'error': 'Failed to archive notification'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unarchive_notification(request, notification_id):
    """Unarchive a notification"""
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.archived = False
        notification.save()
        return Response({'status': 'success'})
    except Exception as e:
        logger.error(f"Error unarchiving notification: {str(e)}")
        return Response({'error': 'Failed to unarchive notification'}, status=500)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def test_error_notification(request):
    """Test error notification system"""
    try:
        logger.info(f"Received test error notification request")
        error_type = request.POST.get('error_type', 'scan_error')
        logger.info(f"Testing error type: {error_type}")
        
        # Get attached files
        attachments = request.FILES.getlist('attachments')
        if attachments:
            logger.info(f"Received {len(attachments)} file attachments")
        
        from .utils import send_error_notification
        
        test_messages = {
            'scan_error': {
                'title': 'Test Scanning Error',
                'message': 'This is a test scanning error notification',
                'details': {
                    'Computer': 'TEST-PC',
                    'Error': 'Test scanning error',
                    'Time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Attachments': f"{len(attachments)} files" if attachments else "None"
                }
            },
            'pdf_error': {
                'title': 'Test PDF Error',
                'message': 'This is a test PDF processing error notification',
                'details': {
                    'File': 'test.pdf',
                    'Error': 'Test PDF error',
                    'Location': os.path.join(settings.DESTINATION_ROOT, 'test'),
                    'Attachments': f"{len(attachments)} files" if attachments else "None"
                }
            },
            'computer_offline': {
                'title': 'Test Computer Offline',
                'message': 'This is a test computer offline notification',
                'details': {
                    'Computer': 'TEST-PC',
                    'Last Seen': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'IP': '192.168.1.1'
                }
            }
        }
        
        test_data = test_messages.get(error_type)
        if not test_data:
            logger.error(f"Invalid error type: {error_type}")
            return Response({
                'error': f'Invalid error type: {error_type}'
            }, status=400)
            
        logger.info(f"Sending test notification: {test_data}")
        send_error_notification(
            error_type=error_type,
            title=test_data['title'],
            message=test_data['message'],
            details=test_data['details'],
            attachments=attachments if attachments else None
        )
        
        return Response({
            'message': f'Test {error_type} notification sent successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in test_error_notification: {str(e)}", exc_info=True)
        return Response({
            'error': str(e)
        }, status=400)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_admin_email(request):
    """Send email to selected administrators"""
    try:
        logger.info("Received admin email request")
        
        # Get form data
        email_type = request.POST.get('type', 'info')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        recipients = json.loads(request.POST.get('recipients', '[]'))
        attachments = request.FILES.getlist('attachments')
        
        if not subject or not message or not recipients:
            return Response({
                'error': 'Missing required fields'
            }, status=400)
        
        logger.info(f"Sending admin email: type={email_type}, subject={subject}, recipients={recipients}, attachments={len(attachments)}")
        
        # Select template based on email type
        template_name = {
            'info': 'notifications/email/info_email.html',
            'warning': 'notifications/email/warning_email.html',
            'error': 'notifications/email/error_email.html'
        }.get(email_type, 'notifications/email/info_email.html')
        
        # Create HTML message
        html_message = render_to_string(template_name, {
            'message': message,
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z'),
            'has_attachments': bool(attachments)
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        # Add prefix to subject based on type
        subject_prefix = {
            'info': '[Info]',
            'warning': '[Warning]',
            'error': '[Error]'
        }.get(email_type, '[Info]')
        
        # Create email message
        email = EmailMessage(
            subject=f"{subject_prefix} {subject}",
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients
        )
        email.content_subtype = "html"
        
        # Attach files if any
        if attachments:
            logger.info(f"Attaching {len(attachments)} files")
            for file in attachments:
                try:
                    email.attach(file.name, file.read(), file.content_type)
                    logger.info(f"Attached file: {file.name}")
                except Exception as e:
                    logger.error(f"Error attaching file {file.name}: {str(e)}")
        
        # Send email
        email.send(fail_silently=False)
        logger.info("Email sent successfully")
        
        return Response({
            'message': 'Email sent successfully'
        })
        
    except Exception as e:
        logger.error(f"Error sending admin email: {str(e)}", exc_info=True)
        return Response({
            'error': str(e)
        }, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_files(request):
    """List files and folders in a directory"""
    try:
        path = request.GET.get('path', 'pdfs')  # Default to pdfs folder
        search_query = request.GET.get('search', '').lower()  # Get search query
        recursive = request.GET.get('recursive', 'false').lower() == 'true'  # Get recursive flag
        base_dir = settings.MEDIA_ROOT
        
        # Ensure path starts with pdfs folder
        if not path.startswith('pdfs'):
            path = 'pdfs'
        
        # Create pdfs directory if it doesn't exist
        pdfs_dir = os.path.join(base_dir, 'pdfs')
        if not os.path.exists(pdfs_dir):
            os.makedirs(pdfs_dir)
        
        # Ensure the path is within MEDIA_ROOT and under pdfs folder
        target_dir = os.path.normpath(os.path.join(base_dir, path))
        if not target_dir.startswith(base_dir) or not target_dir.startswith(os.path.join(base_dir, 'pdfs')):
            return Response({
                "error": "Invalid path"
            }, status=400)
            
        # Get folders and PDFs
        folders = []
        pdfs = []
        
        def scan_directory(current_dir, current_relative_path=''):
            """Recursively scan directory for PDFs"""
            items = []
            try:
                items = os.listdir(current_dir)
            except OSError as e:
                logger.error(f"Error accessing directory {current_dir}: {str(e)}")
                return [], []
                
            local_folders = []
            local_pdfs = []
            
            for item in items:
                item_path = os.path.join(current_dir, item)
                relative_path = os.path.relpath(item_path, base_dir)
                
                if os.path.isdir(item_path):
                    local_folders.append({
                        "id": relative_path,
                        "name": item,
                        "path": relative_path
                    })
                    # If recursive and searching, scan subdirectories
                    if recursive and search_query:
                        sub_folders, sub_pdfs = scan_directory(
                            item_path,
                            os.path.join(current_relative_path, item)
                        )
                        local_folders.extend(sub_folders)
                        local_pdfs.extend(sub_pdfs)
                        
                elif item.lower().endswith('.pdf'):
                    if not search_query or search_query in item.lower():
                        # Get PDF attachment if it exists in database
                        pdf_path = os.path.join(settings.MEDIA_URL, relative_path)
                        try:
                            pdf = PDFAttachment.objects.get(file=pdf_path)
                            local_pdfs.append({
                                "id": str(pdf.id),
                                "original_filename": pdf.original_filename,
                                "file_url": pdf.file.url,
                                "uploaded_at": pdf.uploaded_at.isoformat() if pdf.uploaded_at else None,
                                "folder_path": current_relative_path
                            })
                        except PDFAttachment.DoesNotExist:
                            # If not in database, create a basic entry
                            local_pdfs.append({
                                "id": relative_path,
                                "original_filename": item,
                                "file_url": os.path.join(settings.MEDIA_URL, relative_path),
                                "uploaded_at": None,
                                "folder_path": current_relative_path
                            })
            
            return local_folders, local_pdfs
        
        # Scan directory (recursively if searching)
        folders, pdfs = scan_directory(target_dir)
        
        return Response({
            "folders": sorted(folders, key=lambda x: x['name'].lower()),
            "pdfs": sorted(pdfs, key=lambda x: x['original_filename'].lower())
        })
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        return Response({
            "error": str(e)
        }, status=500)
