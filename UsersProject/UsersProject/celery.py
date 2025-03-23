from __future__ import absolute_import, unicode_literals
import os

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UsersProject.settings')

from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from datetime import timedelta

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
    task_time_limit=None,  # No time limit for long-running tasks
    task_soft_time_limit=None,  # No soft time limit
    
    # Task result settings
    task_ignore_result=True,  # Don't store task results
    
    # Security settings
    security_key='my-special-security-key',
    
    # Logging settings
    worker_redirect_stdouts=False,  # Don't redirect stdout/stderr
    worker_log_color=True,  # Enable colored logging
    
    # Beat schedule
    beat_schedule={
        'run-relay-client': {
            'task': 'user_management.tasks.run_relay_client',
            'schedule': timedelta(seconds=10),  # Start every 10 seconds if not running
            'options': {
                'expires': 9  # Task expires if not started within 9 seconds
            }
        },
        'monitor-relay-server': {
            'task': 'user_management.tasks.monitor_relay_server',
            'schedule': timedelta(minutes=1)  # Check relay server status every minute
        }
    }
)
