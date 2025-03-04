from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from datetime import timedelta

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UsersProject.settings')

app = Celery('UsersProject')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure Celery
app.conf.update(
    # Broker settings
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/New_York',
    enable_utc=True,
    
    # Worker settings
    worker_pool_restarts=True,
    worker_max_tasks_per_child=None,  # Disable worker recycling
    worker_prefetch_multiplier=1,  # Process one task at a time
    
    # Beat settings
    beat_max_loop_interval=30,  # Check schedule every 30 seconds
    beat_schedule_filename='celerybeat-schedule',  # Persistent schedule file
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    
    # Task result settings
    task_ignore_result=True,  # Don't store task results
    
    # Security settings
    security_key='my-special-security-key',
    
    # Logging settings
    worker_redirect_stdouts=False,  # Don't redirect stdout/stderr
    worker_log_color=True,  # Enable colored logging
)

# Define the beat schedule
app.conf.beat_schedule = {
    'check-scan-schedules': {
        'task': 'user_management.tasks.check_and_run_scheduled_scans',
        'schedule': crontab(minute='*'),  # Run every minute for more precise scheduling
        'options': {
            'expires': 240,  # Expire after 4 minutes
            'max_retries': 0,  # Don't retry failed tasks
            'task_track_started': True,  # Track when task starts
            'acks_late': True,  # Only acknowledge task after it completes
            'reject_on_worker_lost': True,  # Reject task if worker dies
            'time_limit': 240,  # 4 minute hard timeout
            'soft_time_limit': 180  # 3 minute soft timeout
        }
    },
    'analyze-logs': {
        'task': 'user_management.tasks.analyze_logs',
        'schedule': crontab(minute='*/15'),  # Run every 15 minutes
        'options': {
            'expires': 840,  # Expire after 14 minutes
            'max_retries': 0
        }
    }
}
