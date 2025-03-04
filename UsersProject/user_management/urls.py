# user_management/urls.py
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import (    
    AuditLogViewSet,
    LogAggregationViewSet, LogPatternViewSet,
    LogAlertViewSet, LogCorrelationViewSet,
    ScanScheduleViewSet
)

from user_management.views_user import UserViewSet
from user_management.views_computer import ComputerViewSet
from user_management.views_document import DocumentViewSet
from user_management.views_tag import TagViewSet
from user_management.views_notification import NotificationViewSet
from user_management.views_scan import ScanViewSet
from user_management.views_schedule import ScheduleViewSet
from user_management.views_system_log import SystemLogViewSet
from user_management.views_auth import LoginView, LogoutView

# Create a router for our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
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
    
    # Auth URLs
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]