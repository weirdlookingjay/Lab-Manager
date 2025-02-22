from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class NotificationType(models.TextChoices):
    INFO = 'info', 'Information'
    WARNING = 'warning', 'Warning'
    ERROR = 'error', 'Error'
    SUCCESS = 'success', 'Success'

class NotificationPriority(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    CRITICAL = 'critical', 'Critical'

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True)
    email_digest = models.BooleanField(default=True)
    email_immediate = models.BooleanField(default=False)
    
    # Error notification preferences
    notify_scan_errors = models.BooleanField(default=True, help_text="Notify when scanning errors occur")
    notify_pdf_errors = models.BooleanField(default=True, help_text="Notify when PDF copy/processing errors occur")
    notify_computer_offline = models.BooleanField(default=True, help_text="Notify when computers go offline")
    computer_offline_threshold = models.IntegerField(default=10, help_text="Minutes before sending offline notification")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"

class PDFAttachment(models.Model):
    file = models.FileField(upload_to='pdfs/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_pdfs')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField()  # Size in bytes
    content_type = models.CharField(max_length=100, default='application/pdf')
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.original_filename
    
    def get_file_url(self):
        if self.file:
            return self.file.url
        return None
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage when the model instance is deleted
        if self.file:
            storage = self.file.storage
            if storage.exists(self.file.name):
                storage.delete(self.file.name)
        super().delete(*args, **kwargs)

class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.LOW
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.type})"

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)
