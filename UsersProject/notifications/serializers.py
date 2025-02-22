from rest_framework import serializers
from .models import Notification, PDFAttachment
import logging

logger = logging.getLogger(__name__)

class NotificationSerializer(serializers.ModelSerializer):
    # Using source mapping to convert snake_case to camelCase
    createdAt = serializers.SerializerMethodField()
    isRead = serializers.BooleanField(source='is_read')
    
    def get_createdAt(self, obj):
        if obj.created_at:
            return obj.created_at.isoformat()
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'priority', 'user', 'isRead', 'createdAt']
        read_only_fields = ['createdAt']

class PDFAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    
    def get_file_url(self, obj):
        if obj.file:
            return obj.get_file_url()
        return None

    class Meta:
        model = PDFAttachment
        fields = ['id', 'file', 'original_filename', 'uploaded_by', 'uploaded_at', 'file_size', 'file_url']
        read_only_fields = ['uploaded_at', 'file_size', 'file_url']
