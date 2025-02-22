from rest_framework import serializers
from .models import Ticket, TicketTemplate, TicketComment, TicketAttachment, TicketAuditLog, RoutingRule
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class TicketTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketTemplate
        fields = '__all__'

class TicketCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TicketComment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class TicketAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = TicketAttachment
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at', 'size']

class TicketSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    comments = TicketCommentSerializer(many=True, read_only=True)
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    activity_log = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_activity_log(self, obj):
        audit_logs = TicketAuditLog.objects.filter(ticket=obj).order_by('-created_at')
        return TicketAuditLogSerializer(audit_logs, many=True).data

class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'template', 'custom_fields', 'due_date', 'status', 'assigned_to']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Ensure status is set to 'open' if not provided
        if 'status' not in validated_data:
            validated_data['status'] = 'open'
        return super().create(validated_data)

class TicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'status', 'assigned_to', 
                 'custom_fields', 'tags', 'due_date']

class TicketBulkUpdateSerializer(serializers.Serializer):
    ticket_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.CharField()
    value = serializers.CharField()

class TicketMergeSerializer(serializers.Serializer):
    ticket_ids = serializers.ListField(child=serializers.UUIDField(), min_length=2)
    title = serializers.CharField()

class RoutingRuleSerializer(serializers.ModelSerializer):
    assign_to = UserSerializer(read_only=True)
    assign_to_id = serializers.PrimaryKeyRelatedField(
        source='assign_to',
        queryset=User.objects.all(),
        write_only=True
    )

    class Meta:
        model = RoutingRule
        fields = ['id', 'name', 'conditions', 'actions', 'assign_to', 'assign_to_id', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure assign_to is properly populated
        if instance.assign_to:
            data['assign_to'] = UserSerializer(instance.assign_to).data
        return data

class TicketAuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    formatted_details = serializers.SerializerMethodField()

    class Meta:
        model = TicketAuditLog
        fields = ['id', 'action', 'details', 'formatted_details', 'user', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_formatted_details(self, obj):
        if obj.action == 'status_change':
            return {
                'type': 'status_change',
                'old_value': obj.details.get('old_value'),
                'new_value': obj.details.get('new_value'),
                'note': obj.details.get('note'),
                'timestamp': obj.created_at.isoformat(),
                'user': f"{obj.user.first_name} {obj.user.last_name}"
            }
        elif obj.action == 'assignment':
            old_user = User.objects.filter(id=obj.details.get('old_value')).first()
            new_user = User.objects.filter(id=obj.details.get('new_value')).first()
            return {
                'type': 'assignment',
                'old_value': f"{old_user.first_name} {old_user.last_name}" if old_user else "Unassigned",
                'new_value': f"{new_user.first_name} {new_user.last_name}" if new_user else "Unassigned",
                'timestamp': obj.created_at.isoformat(),
                'user': f"{obj.user.first_name} {obj.user.last_name}"
            }
        elif obj.action == 'priority_change':
            return {
                'type': 'priority_change',
                'old_value': obj.details.get('old_value'),
                'new_value': obj.details.get('new_value'),
                'timestamp': obj.created_at.isoformat(),
                'user': f"{obj.user.first_name} {obj.user.last_name}"
            }
        elif obj.action == 'tag_change':
            change_type = obj.details.get('type')
            tags = obj.details.get('tags', [])
            return {
                'type': 'tag_change',
                'change_type': change_type,
                'tags': tags,
                'timestamp': obj.created_at.isoformat(),
                'user': f"{obj.user.first_name} {obj.user.last_name}"
            }
        return obj.details
