from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "grantfinder",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
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
    # Beat scheduler definitions
    beat_schedule={
        "run-periodic-crawlers-every-5-min": {
            "task": "app.workers.tasks.run_all_active_crawlers_task",
            "schedule": 300.0,  # 5 minutes
        }
    }
)
