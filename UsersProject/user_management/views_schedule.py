from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .authentication import CookieTokenAuthentication
from .models import Schedule
from .serializers import ScheduleSerializer
from .views_base import BaseViewSet

class ScheduleViewSet(BaseViewSet):
    """ViewSet for managing schedules."""
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieTokenAuthentication, TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Get schedules for the current user."""
        return super().get_queryset().filter(user=self.request.user)
