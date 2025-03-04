from rest_framework import viewsets, mixins
from rest_framework.decorators import action

from .views_base import BaseViewSet
from .serializers import NotificationSerializer

from .models import Notification

class NotificationViewSet(BaseViewSet,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        """Get notifications ordered by timestamp"""
        return Notification.objects.all().order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(read=False).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a notification"""
        notification = self.get_object()
        notification.archived = True
        notification.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchive a notification"""
        notification = self.get_object()
        notification.archived = False
        notification.save()
        return Response({'status': 'success'})
