"""Celery task dispatch helper."""

import os

from celery import Celery

from app.core.config import settings


def get_celery_app() -> Celery:
    broker = os.getenv("CELERY_BROKER_URL", settings.celery_broker_url)
    backend = os.getenv("CELERY_RESULT_BACKEND", broker)
    app = Celery("hookpress", broker=broker, backend=backend)
    app.conf.task_default_queue = "default"
    return app


celery_app = get_celery_app()
