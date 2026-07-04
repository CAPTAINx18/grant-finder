import asyncio
import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.grant_source_registry import GrantSourceRegistry
from app.services.ingestion_service import IngestionService
from app.api.deps import get_embedding_service, get_storage_service
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_ingestion_async(source_id: UUID) -> dict:
    """Helper executing the async ingestion logic within a clean database session context."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    embedding_service = get_embedding_service()
    storage_service = get_storage_service()

    async with async_session() as db:
        service = IngestionService(
            db=db,
            embedding_service=embedding_service,
            storage_service=storage_service
        )
        try:
            result = await service.run_ingestion_for_source(source_id)
            return result
        finally:
            await engine.dispose()


async def _trigger_all_active_crawlers_async() -> int:
    """Query active sources and trigger ingestion tasks via Celery delay execution."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            query = select(GrantSourceRegistry).where(GrantSourceRegistry.is_active == True)
            result = await db.execute(query)
            active_sources = result.scalars().all()
            
            triggered_count = 0
            for source in active_sources:
                logger.info(f"Scheduling automatic crawl for source '{source.name}' (ID: {source.id})")
                # Distribute the task execution asynchronously to Celery worker pool
                run_ingestion_task.delay(str(source.id))
                triggered_count += 1
                
            return triggered_count
        finally:
            await engine.dispose()


@celery_app.task(name="app.workers.tasks.run_ingestion_task")
def run_ingestion_task(source_id: str) -> dict:
    """Celery task running crawler ingestion for a specific source ID."""
    logger.info(f"Executing Celery ingestion task for source ID: {source_id}")
    uuid_id = UUID(source_id)
    return asyncio.run(_run_ingestion_async(uuid_id))


@celery_app.task(name="app.workers.tasks.run_all_active_crawlers_task")
def run_all_active_crawlers_task() -> str:
    """Celery Beat periodic task checking all active crawl sources and queuing jobs."""
    logger.info("Celery Beat trigger: Checking active crawler schedules.")
    count = asyncio.run(_trigger_all_active_crawlers_async())
    return f"Triggered {count} active crawler sources."
