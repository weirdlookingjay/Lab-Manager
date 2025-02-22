import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UsersProject.settings')
django.setup()

from notifications.tasks import test_automated_notification
from django.contrib.auth import get_user_model

User = get_user_model()

# Get all active users and their emails
users = User.objects.filter(is_active=True)
print("\nEmails will be sent to:")
for user in users:
    print(f"- {user.email} ({user.username})")

# Get user IDs for notification
user_ids = list(users.values_list('id', flat=True))

print("\nSending test notification...")
# Send test notification
test_automated_notification(user_ids=user_ids)
