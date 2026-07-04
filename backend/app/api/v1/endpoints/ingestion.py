from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.grant_source_registry import GrantSourceRegistry
from app.schemas.ingestion import SourceResponse, TriggerResponse, StatusResponse
from app.workers.tasks import run_ingestion_task

router = APIRouter()


@router.get("/sources", response_model=List[SourceResponse])
async def list_crawler_sources(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve all registered grant ingestion crawler sources. Requires authenticated active login."""
    query = select(GrantSourceRegistry).order_by(GrantSourceRegistry.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/trigger/{source_id}", response_model=TriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_crawling_job(
    source_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Trigger a crawling and parsing ingestion job asynchronously via Celery worker. Requires active login."""
    source = await db.get(GrantSourceRegistry, source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawler source with ID '{source_id}' not found."
        )

    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Crawler source '{source.name}' is inactive. Activate it to trigger crawls."
        )

    # Queue the Celery task asynchronously
    task = run_ingestion_task.delay(str(source_id))

    return {
        "message": f"Ingestion pipeline job triggered successfully for source '{source.name}'.",
        "task_id": task.id
    }


@router.get("/status/{source_id}", response_model=StatusResponse)
async def check_crawling_status(
    source_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Check the status, timestamp, and log results of the last crawl run. Requires active login."""
    source = await db.get(GrantSourceRegistry, source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crawler source with ID '{source_id}' not found."
        )

    return {
        "source_id": source.id,
        "last_run_at": source.last_run_at,
        "last_run_status": source.last_run_status,
        "last_run_error": source.last_run_error
    }
