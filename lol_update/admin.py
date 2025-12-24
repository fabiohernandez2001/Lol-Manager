from django.contrib import admin

# ============================================================================
# Celery Admin Integration
# ============================================================================

# Note: Both django-celery-beat and django-celery-results automatically
# register their models in the Django admin:
#
# - django_celery_beat: PeriodicTask, IntervalSchedule, CrontabSchedule, etc.
# - django_celery_results: TaskResult (with full task history and tracebacks)
#
# No manual registration needed. Access them in Django admin at /admin/
