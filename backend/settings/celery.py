import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.base")

app = Celery("settings")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "publish-scheduled-posts-every-minute": {
        "task": "apps.blog.tasks.publish_scheduled_posts",
        "schedule": 60.0,
    },
    "clear-expired-notifications-daily-03-00": {
        "task": "apps.notifications.tasks.clear_expired_notifications",
        "schedule": crontab(hour=3, minute=0),
    },
    "generate-daily-stats-daily-00-00": {
        "task": "apps.blog.tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),
    },
}
