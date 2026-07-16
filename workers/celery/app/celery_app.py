"""Celery application."""

import os

from celery import Celery

broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery("hookpress", broker=broker, backend=backend)
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_routes = {
    "studio.*": {"queue": "default"},
    "scoring.*": {"queue": "default"},
    "charts.*": {"queue": "default"},
    "media.*": {"queue": "default"},
}
celery_app.conf.beat_schedule = {
    "charts-refresh-weekly": {
        "task": "charts.refresh_pipeline",
        "schedule": 86400.0,
    },
    "cleanup-stale-media-uploads": {
        "task": "media.cleanup_stale_uploads",
        "schedule": 3600.0,
    },
}
celery_app.autodiscover_tasks(["app.tasks"])


@celery_app.task(name="health.ping")
def ping():
    return "pong"
