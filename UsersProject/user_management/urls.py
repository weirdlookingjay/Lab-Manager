# user_management/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views_user import UserViewSet
from .views_computer import ComputerViewSet
from .views_document import DocumentViewSet
from .views_tag import TagViewSet
from .views_notification import NotificationViewSet
from .views import AuditLogViewSet, ChangePasswordView, LogViewSet, LogAggregationViewSet, LogPatternViewSet, LogAlertViewSet,LogCorrelationViewSet, LoginView, RegisterView, ScanScheduleViewSet, admin_stats
from .views_scan import ScanViewSet




# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'computers', ComputerViewSet, basename='computer')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'logs', LogViewSet, basename='logs')
router.register(r'log-aggregations', LogAggregationViewSet, basename='log-aggregation')
router.register(r'log-patterns', LogPatternViewSet, basename='log-patterns')
router.register(r'log-alerts', LogAlertViewSet, basename='log-alerts')
router.register(r'log-correlations', LogCorrelationViewSet, basename='log-correlations')
router.register(r'scan', ScanViewSet, basename='scan')
router.register(r'scan-schedules', ScanScheduleViewSet, basename='scan-schedule')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Auth URLs
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LoginView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Admin URLs
    path('admin/stats/', admin_stats, name='admin-stats'),
    path('admin/users/', UserViewSet.as_view({'get': 'list'}), name='user_list'),
    path('admin/create-user/', RegisterView.as_view({'get': 'list', 'post': 'create'}), name='create_user'),
]