"""
Celery configuration for core project.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.development")

app = Celery("core")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery Beat
app.conf.beat_schedule = {
    "health-check-every-minute": {
        "task": "apps.api.tasks.health_check",
        "schedule": 60.0,  # every minute
    },
    "cleanup-old-logs": {
        "task": "apps.api.tasks.cleanup_old_logs",
        "schedule": 3600.0,  # every hour
    },
}

app.conf.timezone = "UTC"


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
