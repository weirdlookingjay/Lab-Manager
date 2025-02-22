from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Computer, FileTransfer, AuditLog, Notification, Schedule,
    PasswordPolicy, LoginAttempt, UserSession
)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'failed_login_attempts']
    list_filter = ['role', 'is_active', 'is_verified', 'require_password_change']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    readonly_fields = ['failed_login_attempts', 'locked_until']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'bio', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role')}),
        ('Security', {'fields': ('is_verified', 'failed_login_attempts', 'locked_until', 'require_password_change')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

class PasswordPolicyAdmin(admin.ModelAdmin):
    list_display = ['min_length', 'require_uppercase', 'require_lowercase', 
                   'require_numbers', 'require_special_chars', 'password_expiry_days',
                   'max_login_attempts', 'lockout_duration_minutes']
    
    fieldsets = (
        ('Password Complexity', {
            'fields': ('min_length', 'require_uppercase', 'require_lowercase', 
                      'require_numbers', 'require_special_chars')
        }),
        ('Password Expiry', {
            'fields': ('password_expiry_days', 'prevent_password_reuse')
        }),
        ('Login Security', {
            'fields': ('max_login_attempts', 'lockout_duration_minutes')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one password policy
        return not PasswordPolicy.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the password policy
        return False

class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'timestamp', 'ip_address', 'success', 'failure_reason']
    list_filter = ['success', 'timestamp', 'failure_reason']
    search_fields = ['user__username', 'ip_address', 'user_agent']
    readonly_fields = ['user', 'timestamp', 'ip_address', 'user_agent', 'success', 'failure_reason']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'ip_address', 'is_active', 'created_at', 'last_activity']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'ip_address', 'device_type']
    readonly_fields = ['user', 'session_key', 'ip_address', 'user_agent', 
                      'device_type', 'location', 'created_at', 'last_activity']
    ordering = ['-last_activity']
    
    actions = ['terminate_sessions']

    def has_add_permission(self, request):
        return False

    def terminate_sessions(self, request, queryset):
        queryset.update(is_active=False)
    terminate_sessions.short_description = "Terminate selected sessions"

class ComputerAdmin(admin.ModelAdmin):
    list_display = ['label', 'ip_address', 'is_online', 'last_seen']
    list_filter = ['is_online']
    search_fields = ['label', 'ip_address']

class FileTransferAdmin(admin.ModelAdmin):
    list_display = ['computer', 'timestamp', 'source_file', 'successful']
    list_filter = ['successful', 'timestamp']
    search_fields = ['source_file', 'destination_file']

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'level', 'message']
    list_filter = ['level', 'timestamp']
    search_fields = ['message']
    ordering = ['-timestamp']

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'read', 'timestamp']
    list_filter = ['type', 'read', 'timestamp']
    search_fields = ['title', 'message']

class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'schedule_type', 'enabled']
    list_filter = ['schedule_type', 'enabled']
    search_fields = ['name']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Computer, ComputerAdmin)
admin.site.register(FileTransfer, FileTransferAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(PasswordPolicy, PasswordPolicyAdmin)
admin.site.register(LoginAttempt, LoginAttemptAdmin)
admin.site.register(UserSession, UserSessionAdmin)
