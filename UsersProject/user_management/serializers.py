# user_management/serializers.py
import logging
import json
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import Computer, FileTransfer, AuditLog, Notification, Schedule, Tag, SystemLog, LogAggregation, LogPattern, LogAlert, LogCorrelation, ScanSchedule, DocumentTag
from datetime import datetime

User = get_user_model()

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        # Set admin permissions if role is admin (case insensitive)
        if validated_data.get('role', '').lower() == 'admin':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
        return super().create(validated_data)

class ComputerSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    ip = serializers.CharField(source='ip_address', required=False)  # For backward compatibility
    uptime = serializers.CharField(source='format_uptime', read_only=True)
    memory_gb = serializers.CharField(source='format_memory_gb', read_only=True)
    disk_gb = serializers.CharField(source='format_disk_gb', read_only=True)
    cpu_percent = serializers.SerializerMethodField()
    memory_percent = serializers.SerializerMethodField()
    disk_percent = serializers.SerializerMethodField()
    metrics = serializers.JSONField(read_only=True)

    class Meta:
        model = Computer
        fields = [
            # Basic Info
            'id', 'label', 'hostname', 'ip_address', 'ip', 'status',
            'os_version', 'last_seen', 'last_metrics_update', 'manufacturer',
            # System Overview
            'cpu_model', 'cpu_cores', 'cpu_threads', 'cpu_percent',
            'memory_total', 'memory_usage', 'memory_gb', 'memory_percent',
            'total_disk', 'disk_usage', 'disk_gb', 'disk_percent',
            'device_class', 'boot_time', 'system_uptime', 'uptime',
            'logged_in_user', 'metrics'
        ]
        read_only_fields = [
            'status', 'last_seen', 'last_metrics_update', 'uptime',
            'memory_gb', 'disk_gb', 'cpu_percent', 'memory_percent',
            'disk_percent', 'metrics'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Get status before formatting timestamps
        data['status'] = self.get_status(instance)
        
        # Format timestamps
        for field in ['last_seen', 'last_metrics_update', 'boot_time']:
            if data.get(field):
                try:
                    dt = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    data[field] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, AttributeError):
                    pass
        
        return data

    def get_status(self, obj):
        """Get the online/offline status of the computer."""
        thirty_mins_ago = timezone.now() - timezone.timedelta(minutes=30)
        is_online = (
            (obj.last_metrics_update and obj.last_metrics_update >= thirty_mins_ago) or
            (obj.last_seen and obj.last_seen >= thirty_mins_ago)
        )
        return 'online' if is_online else 'offline'

    def get_cpu_percent(self, obj):
        """Get CPU usage percentage."""
        return obj.cpu_percent if obj.cpu_percent is not None else 0

    def get_memory_percent(self, obj):
        """Get memory usage percentage."""
        return obj.memory_percent if obj.memory_percent is not None else 0

    def get_disk_percent(self, obj):
        """Get disk usage percentage."""
        return obj.disk_percent if obj.disk_percent is not None else 0

class FileTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileTransfer
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['timestamp', 'message', 'level']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'read', 'archived', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']

class DocumentTagSerializer(serializers.ModelSerializer):
    tag = TagSerializer(read_only=True)
    
    class Meta:
        model = DocumentTag
        fields = ['id', 'document_path', 'computer', 'tag']

class SystemLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    computer = ComputerSerializer(read_only=True)
    
    class Meta:
        model = SystemLog
        fields = [
            'id', 'timestamp', 'level', 'category', 'event',
            'user', 'computer', 'message', 'details',
            'ip_address', 'user_agent'
        ]
        read_only_fields = fields

class LogAggregationSerializer(serializers.ModelSerializer):
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    
    class Meta:
        model = LogAggregation
        fields = [
            'id', 'period', 'period_display', 'start_time', 'end_time',
            'category', 'event', 'level', 'count', 'error_count',
            'warning_count', 'unique_users', 'unique_computers',
            'most_common_message', 'details'
        ]
        read_only_fields = fields

class LogPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogPattern
        fields = '__all__'

class LogAlertSerializer(serializers.ModelSerializer):
    pattern_name = serializers.CharField(source='pattern.name', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    matched_logs = SystemLogSerializer(many=True, read_only=True)

    class Meta:
        model = LogAlert
        fields = '__all__'

class LogCorrelationSerializer(serializers.ModelSerializer):
    primary_log = SystemLogSerializer(read_only=True)
    related_logs = SystemLogSerializer(many=True, read_only=True)

    class Meta:
        model = LogCorrelation
        fields = '__all__'

class ScanScheduleSerializer(serializers.ModelSerializer):
    computers = ComputerSerializer(many=True, read_only=True)
    computer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = ScanSchedule
        fields = [
            'id', 'type', 'type_display', 'time', 'selected_days', 'monthly_date',
            'email_notification', 'email_addresses', 'computers', 'computer_ids',
            'created_at', 'updated_at', 'enabled', 'last_run', 'next_run'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_run', 'next_run']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['computer_ids'] = [computer.id for computer in instance.computers.all()]
        return data

    def validate(self, data):
        """
        Validate schedule data based on type
        """
        schedule_type = data.get('type')
        selected_days = data.get('selected_days')
        monthly_date = data.get('monthly_date')

        if schedule_type == 'weekly' and not selected_days:
            raise serializers.ValidationError(
                {'selected_days': 'Selected days are required for weekly schedules'}
            )
        elif schedule_type == 'monthly' and not monthly_date:
            raise serializers.ValidationError(
                {'monthly_date': 'Monthly date is required for monthly schedules'}
            )
        
        if monthly_date and (monthly_date < 1 or monthly_date > 31):
            raise serializers.ValidationError(
                {'monthly_date': 'Monthly date must be between 1 and 31'}
            )

        if selected_days:
            if not all(isinstance(day, int) and 0 <= day <= 6 for day in selected_days):
                raise serializers.ValidationError(
                    {'selected_days': 'Selected days must be integers between 0 and 6'}
                )

        if data.get('email_notification') and not data.get('email_addresses'):
            raise serializers.ValidationError(
                {'email_addresses': 'Email addresses are required when email notification is enabled'}
            )

        return data

    def create(self, validated_data):
        computer_ids = validated_data.pop('computer_ids', [])
        schedule = ScanSchedule.objects.create(**validated_data)
        if computer_ids:
            schedule.computers.set(computer_ids)
        return schedule

    def update(self, instance, validated_data):
        computer_ids = validated_data.pop('computer_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if computer_ids is not None:
            instance.computers.set(computer_ids)
        return instance