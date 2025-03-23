# user_management/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth.views import LogoutView

from .views import (    
    AuditLogViewSet,
    LogAggregationViewSet, LogPatternViewSet,
    LogAlertViewSet, LogCorrelationViewSet,
    LoginView  # Import our custom LoginView
)

from .views_notification import (   
    NotificationViewSet
)

from .views_tag import (  
    TagViewSet
)

from .views_system_log import (  
    SystemLogViewSet
)


from .views_schedule import (   
    ScheduleViewSet
)


from .views_scan import (   
    ScanViewSet
)


from .views_document import (  
    DocumentViewSet
)


from .views_computer import (    
    ComputerViewSet,
)

from .views_user import (   
    UserViewSet
)

from .views_file_system import list_local_files, list_remote_files, download_file, upload_file


# Create a router for our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'computers', ComputerViewSet, basename='computer')  
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'schedules', ScheduleViewSet, basename='schedule')
router.register(r'system-logs', SystemLogViewSet, basename='system-log')
router.register(r'log-aggregations', LogAggregationViewSet, basename='log-aggregation')
router.register(r'log-patterns', LogPatternViewSet, basename='log-pattern')
router.register(r'log-alerts', LogAlertViewSet, basename='log-alert')
router.register(r'log-correlations', LogCorrelationViewSet, basename='log-correlation')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # File System routes
    path('api/files/local/', list_local_files, name='list_local_files'),
    path('api/computers/<int:computer_id>/files/', list_remote_files, name='list_remote_files'),
    path('api/computers/<int:computer_id>/files/download/', download_file, name='download_file'),
    path('api/computers/<int:computer_id>/files/upload/', upload_file, name='upload_file'),
    
    # Auth URLs
    path('login/', LoginView.as_view(), name='api-login'),  # Remove api/auth/ prefix since it's already in main urls.py
    path('logout/', LogoutView.as_view(), name='api-logout'),
]