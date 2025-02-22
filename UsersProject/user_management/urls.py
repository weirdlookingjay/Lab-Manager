# user_management/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'computers', views.ComputerViewSet, basename='computer')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')
router.register(r'logs', views.LogViewSet, basename='logs')
router.register(r'log-aggregations', views.LogAggregationViewSet, basename='log-aggregation')
router.register(r'log-patterns', views.LogPatternViewSet, basename='log-patterns')
router.register(r'log-alerts', views.LogAlertViewSet, basename='log-alerts')
router.register(r'log-correlations', views.LogCorrelationViewSet, basename='log-correlations')
router.register(r'scan', views.ScanViewSet, basename='scan')
router.register(r'scan-schedules', views.ScanScheduleViewSet, basename='scan-schedule')

# The API URLs are now determined automatically by the router
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Auth URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LoginView.as_view(), name='logout'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Admin URLs
    path('admin/stats/', views.admin_stats, name='admin-stats'),
    path('admin/users/', views.UserViewSet.as_view({'get': 'list'}), name='user_list'),
    path('admin/create-user/', views.RegisterView.as_view({'get': 'list', 'post': 'create'}), name='create_user'),
]