"""
Celery configuration for ChallengerBrain project.

This module initializes the Celery application and configures it for Django integration.
It automatically discovers tasks from all installed Django apps.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChallengerBrain.settings')

# Create the Celery application instance
app = Celery('ChallengerBrain')

# Load configuration from Django settings
# All celery-related configuration options should have a `CELERY_` prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks from all registered Django apps
# This looks for tasks.py in each app directory
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Debug task to verify Celery is working correctly.

    Usage:
        from ChallengerBrain.celery import debug_task
        debug_task.delay()
    """
    print(f'Request: {self.request!r}')
