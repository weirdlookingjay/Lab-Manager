"""UsersProject URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from user_management.views import (
    ComputerViewSet, 
    DocumentViewSet, 
    NotificationViewSet,
    ScanScheduleViewSet,
    ScanViewSet
)
from rest_framework.routers import DefaultRouter

# Create a router for API endpoints
router = DefaultRouter()
router.register(r'computers', ComputerViewSet, basename='computer')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'scan-schedules', ScanScheduleViewSet, basename='scan-schedule')
router.register(r'scan', ScanViewSet, basename='scan')

print("DEBUG - Main router URLs:", router.urls)

# Debug prints
print("\nDEBUG - Router URLs:")
for url in router.urls:
    print(f"  {url.pattern}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # Include API endpoints at /api/
    path('api/auth/', include('user_management.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)