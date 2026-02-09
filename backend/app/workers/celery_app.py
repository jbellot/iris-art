"""Celery application configuration."""

from celery import Celery
from kombu import Queue

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "iris_art",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery with priority queues
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    # Priority queue configuration
    task_queues=(
        Queue("high_priority", routing_key="high"),
        Queue("default", routing_key="default"),
    ),
    task_routes={
        "app.workers.tasks.processing.process_iris_pipeline": {"queue": "high_priority"},
    },
    task_default_queue="default",
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers.tasks"])
