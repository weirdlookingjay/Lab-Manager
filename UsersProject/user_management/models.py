# user_management/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import calendar
import logging
from django.contrib.auth import get_user_model
import pytz
from datetime import datetime, timedelta, time as datetime_time

logger = logging.getLogger(__name__)

class PasswordPolicy(models.Model):
    """Global password policy settings"""
    min_length = models.IntegerField(default=8, validators=[MinValueValidator(8), MaxValueValidator(50)])
    require_uppercase = models.BooleanField(default=True)
    require_lowercase = models.BooleanField(default=True)
    require_numbers = models.BooleanField(default=True)
    require_special_chars = models.BooleanField(default=True)
    password_expiry_days = models.IntegerField(default=90, validators=[MinValueValidator(1), MaxValueValidator(365)])
    max_login_attempts = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    lockout_duration_minutes = models.IntegerField(default=30, validators=[MinValueValidator(1), MaxValueValidator(1440)])
    prevent_password_reuse = models.IntegerField(default=3, help_text="Number of previous passwords to prevent reusing")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Password Policy"
        verbose_name_plural = "Password Policies"

    def __str__(self):
        return f"Password Policy (Updated: {self.updated_at.strftime('%Y-%m-%d')})"

    @classmethod
    def get_policy(cls):
        """Get the active password policy, creating default if none exists"""
        policy, created = cls.objects.get_or_create(pk=1)
        return policy

class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='login_attempts')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{'Success' if self.success else 'Failed'} login by {self.user.username} from {self.ip_address}"

class UserSession(models.Model):
    """Track user sessions and devices"""
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=20, default='unknown')
    location = models.CharField(max_length=100, blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_activity']

    def __str__(self):
        return f"Session for {self.user.username} on {self.device_type}"

class CustomUser(AbstractUser):
    """Custom user model that maps to user_management_customer table"""
    password = models.CharField(max_length=128)
    is_superuser = models.BooleanField(default=False)
    username = models.CharField(max_length=150, unique=True)
    is_staff = models.BooleanField(default=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    role = models.CharField(max_length=50, default='user')
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    require_password_change = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_management_customer'
        managed = True

    def __str__(self):
        return self.email

    def is_locked_out(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def record_login_attempt(self, success, ip_address=None, user_agent=None, failure_reason=None):
        if success:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.last_login = timezone.now()
            self.save()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:  # Max attempts before lockout
                self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
            self.save()

class Computer(models.Model):
    ip_address = models.CharField(max_length=15, unique=True)
    label = models.CharField(max_length=100)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    model = models.CharField(max_length=100, null=True, blank=True)
    last_transfer = models.DateTimeField(null=True, blank=True)
    total_transfers = models.IntegerField(default=0)
    successful_transfers = models.IntegerField(default=0)
    failed_transfers = models.IntegerField(default=0)
    total_bytes_transferred = models.BigIntegerField(default=0)
    os_version = models.CharField(max_length=100, null=True, blank=True)
    user_profile = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)  # Added for network authentication
    password = models.CharField(max_length=100, null=True, blank=True)  # Added for network authentication

    class Meta:
        db_table = 'computers'
        managed = False  # Tell Django not to manage this table since it already exists

    def __str__(self):
        return f"{self.label} ({self.ip_address})"

class Schedule(models.Model):
    SCHEDULE_TYPES = [
        ('I', 'Immediate'),
        ('H', 'Hourly'),
        ('D', 'Daily'),
        ('W', 'Weekly'),
        ('M', 'Monthly')
    ]
    
    name = models.CharField(max_length=100)
    schedule_type = models.CharField(max_length=1, choices=SCHEDULE_TYPES)
    func = models.CharField(max_length=255)  # Function to run
    enabled = models.BooleanField(default=True)
    hours = models.IntegerField(null=True, blank=True)
    minutes = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_schedule_type_display()})"

class FileTransfer(models.Model):
    computer = models.ForeignKey(Computer, on_delete=models.CASCADE, related_name='transfers')
    timestamp = models.DateTimeField(default=timezone.now)
    source_file = models.CharField(max_length=255)
    destination_file = models.CharField(max_length=255)
    bytes_transferred = models.BigIntegerField()
    successful = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Transfer {self.source_file} -> {self.destination_file}"

class AuditLog(models.Model):
    """Model for storing audit logs."""
    LEVEL_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} [{self.level}] {self.message}"

class Notification(models.Model):
    LEVEL_CHOICES = (
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    )

    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.title} ({self.type})"

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Default color is blue
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class DocumentTag(models.Model):
    document_path = models.CharField(max_length=255)
    computer = models.CharField(max_length=255)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='document_tags')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document_path', 'computer', 'tag')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.document_path} - {self.tag.name}"

class PasswordHistory(models.Model):
    """Track password history to prevent reuse"""
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='password_history')
    password = models.CharField(max_length=128)  # Hashed password
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Password History"
        verbose_name_plural = "Password Histories"
    
    def __str__(self):
        return f"Password change for {self.user.username} at {self.created_at}"

class SystemLog(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
        ('OVERDUE', 'Overdue'),
    ]

    LEVEL_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('DEBUG', 'Debug'),
    ]

    CATEGORY_CHOICES = [
        ('COMPUTER_STATUS', 'Computer Status'),
        ('FILE_SCAN', 'File Scan'),
        ('FILE_ACCESS', 'File Access'),
        ('SYSTEM', 'System'),
        ('AUTH', 'Authentication'),
    ]

    EVENT_CHOICES = [
        # Computer Status Events
        ('COMPUTER_ONLINE', 'Computer Online'),
        ('COMPUTER_OFFLINE', 'Computer Offline'),
        ('COMPUTER_REGISTERED', 'Computer Registered'),
        ('COMPUTER_UPDATED', 'Computer Updated'),
        
        # File Scan Events
        ('SCAN_STARTED', 'Scan Started'),
        ('SCAN_COMPLETED', 'Scan Completed'),
        ('SCAN_ERROR', 'Scan Error'),
        ('FILE_FOUND', 'File Found'),
        ('FILE_INDEXED', 'File Indexed'),
        ('FILE_MODIFIED', 'File Modified'),
        ('FILE_DELETED', 'File Deleted'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    message = models.TextField()
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # References
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    computer = models.ForeignKey('Computer', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Event Details
    details = models.JSONField(default=dict, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['category', 'event']),
            models.Index(fields=['computer', 'category']),
            models.Index(fields=['timestamp', 'level']),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.level} - {self.event}: {self.message}"

class LogAggregation(models.Model):
    """Model for storing aggregated log data"""
    PERIOD_CHOICES = [
        ('HOUR', 'Hourly'),
        ('DAY', 'Daily'),
        ('WEEK', 'Weekly'),
        ('MONTH', 'Monthly')
    ]

    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    category = models.CharField(max_length=20, choices=SystemLog.CATEGORY_CHOICES)
    event = models.CharField(max_length=50, choices=SystemLog.EVENT_CHOICES)
    level = models.CharField(max_length=10, choices=SystemLog.LEVEL_CHOICES)
    count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    unique_computers = models.IntegerField(default=0)
    most_common_message = models.TextField(blank=True)
    details = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=['period', 'start_time']),
            models.Index(fields=['category', 'event']),
            models.Index(fields=['level']),
        ]
        ordering = ['-start_time', 'category']

    def __str__(self):
        return f"{self.get_period_display()} Aggregation - {self.category} ({self.start_time})"

    @classmethod
    def aggregate_logs(cls, period='DAY', start_time=None, end_time=None):
        """
        Aggregate logs for the specified period
        """
        from django.db.models import Count, F
        from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
        
        try:
            if not start_time:
                start_time = timezone.now() - timezone.timedelta(days=1)
            if not end_time:
                end_time = timezone.now()

            trunc_func = {
                'HOUR': TruncHour,
                'DAY': TruncDay,
                'WEEK': TruncWeek,
                'MONTH': TruncMonth
            }[period]

            # Group logs by period and category
            logs = SystemLog.objects.filter(
                timestamp__gte=start_time,
                timestamp__lt=end_time
            ).annotate(
                period_start=trunc_func('timestamp')
            ).values(
                'period_start', 'category', 'event', 'level'
            ).annotate(
                total_count=Count('id'),
                error_count=Count('id', filter=models.Q(level='ERROR')),
                warning_count=Count('id', filter=models.Q(level='WARNING')),
                unique_users=Count('user', distinct=True),
                unique_computers=Count('computer', distinct=True)
            )

            # Create aggregations
            for log in logs:
                period_end = log['period_start'] + cls.get_period_delta(period)
                
                # Get most common message for this group
                common_message = SystemLog.objects.filter(
                    timestamp__gte=log['period_start'],
                    timestamp__lt=period_end,
                    category=log['category'],
                    event=log['event'],
                    level=log['level']
                ).values('message').annotate(
                    count=Count('id')
                ).order_by('-count').first()

                # Convert any unhashable types to strings in details
                details = {
                    'summary': {
                        'total_count': str(log['total_count']),  # Convert to string
                        'error_count': str(log['error_count']),  # Convert to string
                        'warning_count': str(log['warning_count']),  # Convert to string
                        'unique_users': str(log['unique_users']),  # Convert to string
                        'unique_computers': str(log['unique_computers'])  # Convert to string
                    }
                }

                cls.objects.update_or_create(
                    period=period,
                    start_time=log['period_start'],
                    end_time=period_end,
                    category=str(log['category']),  # Convert to string
                    event=str(log['event']),  # Convert to string
                    level=str(log['level']),  # Convert to string
                    defaults={
                        'count': log['total_count'],
                        'error_count': log['error_count'],
                        'warning_count': log['warning_count'],
                        'unique_users': log['unique_users'],
                        'unique_computers': log['unique_computers'],
                        'most_common_message': common_message['message'] if common_message else '',
                        'details': details
                    }
                )
        except Exception as e:
            logger.error(f"Error aggregating logs: {str(e)}")
            raise
    
        

    @staticmethod
    def get_period_delta(period):
        """Get timedelta for a period"""
        return {
            'HOUR': timezone.timedelta(hours=1),
            'DAY': timezone.timedelta(days=1),
            'WEEK': timezone.timedelta(weeks=1),
            'MONTH': timezone.timedelta(days=30),  # Approximate
        }[period]

class LogPattern(models.Model):
    """Model for defining log patterns to watch for"""
    name = models.CharField(max_length=255)
    description = models.TextField()
    pattern_type = models.CharField(max_length=50, choices=[
        ('SEQUENCE', 'Event Sequence'),
        ('THRESHOLD', 'Threshold Based'),
        ('CORRELATION', 'Event Correlation')
    ])
    conditions = models.JSONField(help_text="JSON defining the pattern conditions")
    alert_threshold = models.IntegerField(default=1)
    cooldown_minutes = models.IntegerField(default=60)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class LogAlert(models.Model):
    """Model for storing triggered log alerts"""
    pattern = models.ForeignKey(LogPattern, on_delete=models.CASCADE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    matched_logs = models.ManyToManyField('SystemLog')
    details = models.JSONField()
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey('CustomUser', null=True, blank=True, on_delete=models.SET_NULL)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Alert for {self.pattern.name} at {self.triggered_at}"

class LogCorrelation(models.Model):
    """Model for storing correlated log events"""
    correlation_id = models.UUIDField(default=uuid.uuid4)
    primary_log = models.ForeignKey('SystemLog', on_delete=models.CASCADE, related_name='primary_correlations')
    related_logs = models.ManyToManyField('SystemLog', related_name='related_correlations')
    correlation_type = models.CharField(max_length=50)
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['correlation_id']),
            models.Index(fields=['correlation_type']),
            models.Index(fields=['created_at'])
        ]

class ScanSchedule(models.Model):
    """Model for managing scan schedules"""
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='scan_schedules',
        null=True,  # Temporary, will remove after migration
        blank=True  # Temporary, will remove after migration
    )
    type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ])
    time = models.TimeField()
    selected_days = models.JSONField(null=True, blank=True)  # For weekly schedules
    monthly_date = models.IntegerField(null=True, blank=True)  # For monthly schedules
    enabled = models.BooleanField(default=True)
    email_notification = models.BooleanField(default=True)
    email_addresses = models.JSONField(null=True, blank=True)
    computers = models.ManyToManyField('Computer', related_name='scan_schedules')
    next_run = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['created_at']
        verbose_name = "Scan Schedule"
        verbose_name_plural = "Scan Schedules"

    def __str__(self):
        return f"{self.get_type_display()} Scan Schedule (Created: {self.created_at.strftime('%Y-%m-%d')})"

    def calculate_next_run(self):
        """Calculate the next run time based on schedule type and current time"""
        est = pytz.timezone('America/New_York')
        current_time = timezone.now().astimezone(est)
        logger.info(f"Calculating next run in EST. Current time: {current_time.strftime('%H:%M:%S')}, Schedule time: {self.time}")

        # Get schedule time as datetime.time object
        if isinstance(self.time, str):
            try:
                schedule_time = datetime.strptime(self.time, '%H:%M:%S').time()
            except ValueError:
                schedule_time = datetime.strptime(self.time, '%H:%M').time()
        else:
            schedule_time = self.time
        logger.info(f"Using time object: {schedule_time}")

        # Create initial next run time for today
        initial_next_run = est.localize(
            datetime.combine(current_time.date(), schedule_time)
        )
        logger.info(f"Initial next_run (EST): {initial_next_run}")

        # If this is a newly created/updated schedule (no last_run)
        if not self.last_run:
            # If the time hasn't passed today, run today
            if current_time.time() < schedule_time:
                logger.info(f"New schedule, time hasn't passed yet, running today (EST): {initial_next_run}")
                return initial_next_run
            # If we just missed it (within 2 minutes), still run today
            grace_period = current_time - timedelta(minutes=2)
            if grace_period.time() <= schedule_time <= current_time.time():
                logger.info(f"New schedule within grace period, running today (EST): {initial_next_run}")
                return initial_next_run
        
        # For all other cases, schedule for the next occurrence
        if self.type == 'daily':
            # For daily, if time has passed today (including grace period), schedule for tomorrow
            grace_period = current_time - timedelta(minutes=2)
            if grace_period.time() > schedule_time:
                initial_next_run += timedelta(days=1)
                logger.info(f"Daily schedule, time passed for today (including grace period), advancing to tomorrow (EST): {initial_next_run}")
            else:
                logger.info(f"Daily schedule, within grace period, running today (EST): {initial_next_run}")
        
        elif self.type == 'weekly' and self.selected_days:
            # For weekly, find the next selected day
            current_weekday = current_time.weekday()
            days_ahead = 7
            
            # Sort days to ensure we check them in order
            selected_days = sorted(self.selected_days)
            
            # First check remaining days this week
            for day in selected_days:
                days_until = (day - current_weekday) % 7
                if days_until == 0:  # Same day
                    if current_time.time() < schedule_time:  # Time hasn't passed
                        days_ahead = 0
                        break
                elif days_until < days_ahead:
                    days_ahead = days_until
                    break
            
            # If no days found this week or time passed today, look at next week
            if days_ahead == 7:
                days_ahead = (selected_days[0] - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7
            
            initial_next_run += timedelta(days=days_ahead)
            logger.info(f"Weekly schedule, advanced to next selected weekday (EST): {initial_next_run}")
        
        elif self.type == 'monthly' and self.monthly_date:
            # For monthly, move to the next month on the same date
            next_date = current_time.date()
            
            # If we haven't passed the day this month and haven't passed the time
            if current_time.day < self.monthly_date or (
                current_time.day == self.monthly_date and current_time.time() < schedule_time
            ):
                # Stay in current month
                next_date = next_date.replace(day=self.monthly_date)
            else:
                # Move to next month
                if current_time.month == 12:
                    next_date = next_date.replace(year=current_time.year + 1, month=1, day=self.monthly_date)
                else:
                    next_date = next_date.replace(month=current_time.month + 1, day=self.monthly_date)
            
            initial_next_run = est.localize(datetime.combine(next_date, schedule_time))
            logger.info(f"Monthly schedule, next run (EST): {initial_next_run}")

        logger.info(f"Final next_run time: {initial_next_run}")
        return initial_next_run

    def save(self, *args, **kwargs):
        """Update next_run time before saving"""
        if not self.pk or self.enabled:
            # Calculate next run in EST
            next_run_local = self.calculate_next_run()
            if next_run_local:
                # Only convert to UTC at the last moment before saving to database
                self.next_run = next_run_local.astimezone(pytz.UTC)
                logger.info(f"Saving schedule - EST: {next_run_local}, UTC: {self.next_run}")
            
        super().save(*args, **kwargs)

# In your settings.py, specify the custom user model
AUTH_USER_MODEL = 'user_management.CustomUser'