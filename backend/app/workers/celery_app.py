from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "grantfinder",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker settings for stability on Windows if run locally
    worker_prefetch_multiplier=1,
)

# Placeholders for future tasks registration
@celery_app.task(name="app.workers.tasks.ping_task")
def ping_task() -> str:
    return "pong"
