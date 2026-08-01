from celery import Celery

from app.core.config import settings


celery = Celery(
    "sportsintel",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery.conf.beat_schedule = {
    "seed-foundation-daily": {
        "task": "app.workers.tasks.seed_foundation",
        "schedule": 86400,
    }
}
