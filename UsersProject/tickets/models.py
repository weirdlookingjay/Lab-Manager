from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class TicketPriority(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'

class TicketStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PENDING = 'pending', 'Pending'
    RESOLVED = 'resolved', 'Resolved'
    CLOSED = 'closed', 'Closed'

class TicketTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    default_priority = models.CharField(max_length=20, choices=TicketPriority.choices)
    default_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_ticket_templates'
    )
    custom_fields = models.JSONField(default=dict)
    sla_minutes = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=TicketPriority.choices)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tickets'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    
    template = models.ForeignKey(
        TicketTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets'
    )
    
    custom_fields = models.JSONField(default=dict)
    tags = models.JSONField(default=list)
    linked_tickets = models.ManyToManyField('self', blank=True, symmetrical=False)
    parent_ticket = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_tickets'
    )
    
    sla_breach_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.id})"

    def save(self, *args, **kwargs):
        # Set SLA breach time based on priority if not already set
        if not self.sla_breach_at and self.priority:
            sla_hours = {
                TicketPriority.URGENT: 4,
                TicketPriority.HIGH: 8,
                TicketPriority.MEDIUM: 24,
                TicketPriority.LOW: 48,
            }
            hours = sla_hours.get(self.priority)
            if hours:
                self.sla_breach_at = timezone.now() + timezone.timedelta(hours=hours)
        
        super().save(*args, **kwargs)

class RoutingRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    conditions = models.JSONField(default=dict)
    actions = models.JSONField(default=dict)
    assign_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='routing_rules'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.name

class TicketComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    content = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.ticket.id} by {self.author}"

class TicketAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='ticket_attachments/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

class TicketAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)
    details = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on {self.ticket.id} by {self.user}"
