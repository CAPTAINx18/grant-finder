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


from app.models.grant import Grant
from sqlalchemy import func

@router.get("/monitoring", status_code=status.HTTP_200_OK)
async def get_ingestion_monitoring_metrics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve aggregation metrics monitoring all crawler synchronizations. Requires active user login."""
    # 1. Total grants imported
    grants_count_query = select(func.count(Grant.id))
    grants_count_res = await db.execute(grants_count_query)
    total_grants = grants_count_res.scalar() or 0

    # 2. Get all crawler source registries
    sources_query = select(GrantSourceRegistry)
    sources_res = await db.execute(sources_query)
    sources = list(sources_res.scalars().all())

    # Calculate sync details
    last_sync_time = None
    crawler_status = []
    failed_sources = []

    for s in sources:
        if s.last_run_at:
            if last_sync_time is None or s.last_run_at > last_sync_time:
                last_sync_time = s.last_run_at

        status_info = {
            "id": s.id,
            "name": s.name,
            "is_active": s.is_active,
            "last_run_at": s.last_run_at,
            "last_run_status": s.last_run_status or "never",
            "last_run_error": s.last_run_error
        }
        crawler_status.append(status_info)

        if s.last_run_status == "failed":
            failed_sources.append({
                "id": s.id,
                "name": s.name,
                "error": s.last_run_error
            })

    return {
        "total_grants_imported": total_grants,
        "last_sync_time": last_sync_time.isoformat() if last_sync_time else None,
        "crawler_status": crawler_status,
        "failed_sources": failed_sources
    }
