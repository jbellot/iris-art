"""Celery task modules."""

# Import tasks so they get auto-discovered by Celery
from app.workers.tasks import email  # noqa: F401
