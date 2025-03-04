from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .authentication import CookieTokenAuthentication
from .models import SystemLog
from .serializers import SystemLogSerializer
from .views_base import BaseViewSet

class SystemLogViewSet(BaseViewSet):
    """ViewSet for managing system logs."""
    queryset = SystemLog.objects.all().order_by('-timestamp')
    serializer_class = SystemLogSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Get system logs filtered by user permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset
