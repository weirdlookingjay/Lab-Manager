# user_management/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import Computer, FileTransfer, AuditLog, Notification, Schedule, Tag, SystemLog, LogAggregation, LogPattern, LogAlert, LogCorrelation, ScanSchedule, DocumentTag

User = get_user_model()

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
    name = serializers.CharField(source='label')
    ip = serializers.CharField(source='ip_address')

    def get_status(self, obj):
        return 'online' if obj.is_online else 'offline'

    class Meta:
        model = Computer
        fields = [
            'id', 'name', 'label', 'ip', 'status', 'last_seen',
            'successful_transfers', 'failed_transfers', 'total_transfers',
            'total_bytes_transferred', 'last_transfer', 'os_version',
            'user_profile', 'username', 'password', 'model'
        ]
        read_only_fields = ['id', 'last_seen', 'last_transfer']
        extra_kwargs = {
            'password': {'write_only': True}  # Ensure password is write-only
        }

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