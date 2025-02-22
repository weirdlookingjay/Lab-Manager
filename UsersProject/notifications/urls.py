from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'pdfs', views.PDFAttachmentViewSet, basename='pdf-attachment')

urlpatterns = [
    # Base notification endpoints
    path('', views.get_notifications, name='get_notifications'),
    path('mark_read/<str:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('archive/<str:notification_id>/', views.archive_notification, name='archive_notification'),
    path('unarchive/<str:notification_id>/', views.unarchive_notification, name='unarchive_notification'),
    
    # Preferences endpoints
    path('preferences/', views.notification_preferences, name='notification_preferences'),
    
    # Test notification endpoints
    path('test/', include([
        path('system/', views.test_system_notification, name='test-system-notification'),
        path('scan/', views.test_scan_notification, name='test-scan-notification'),
        path('file/', views.test_file_notification, name='test-file-notification'),
        path('error/', views.test_error_notification, name='test_error_notification'),
        path('send/email/', views.send_admin_email, name='send_admin_email'),
    ])),
    
    # Admin endpoints
    path('admin/', include([
        path('email/send/', views.admin_send_email, name='admin_send_email'),
    ])),
    
    # Email-related endpoints
    path('email/', include([
        path('preferences/', views.get_email_preferences, name='get_email_preferences'),
        path('preferences/update/', views.update_email_preferences, name='update_email_preferences'),
        path('test/', views.test_email_notification, name='test_email_notification'),
        path('test-digest/', views.test_email_digest, name='test_email_digest'),
    ])),

    # File browsing endpoint
    path('files/', views.list_files, name='list_files'),
] + router.urls
