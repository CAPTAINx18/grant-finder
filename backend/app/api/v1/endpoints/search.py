from typing import Any, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db, get_embedding_service
from app.models.user import User
from app.services.ai.base import BaseEmbeddingService
from app.services.grant_search_service import GrantSearchService

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
async def search_grants(
    q: str = Query(..., min_length=1, description="The search query text"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of search results to return"),
    threshold: float = Query(0.3, ge=0.0, le=1.0, description="Minimum cosine similarity threshold for vector search"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service)
) -> Any:
    """Perform hybrid search (combining keyword FTS and semantic vector similarity) for matching grants."""
    search_service = GrantSearchService(db, embedding_service)
    results = await search_service.hybrid_search(
        query_text=q,
        limit=limit,
        threshold=threshold
    )

    output = []
    for grant, rrf_score in results:
        output.append({
            "id": grant.id,
            "name": grant.name,
            "description": grant.description,
            "funding_amount_max": float(grant.funding_amount_max) if grant.funding_amount_max else None,
            "currency": grant.currency,
            "deadline": grant.deadline.isoformat() if grant.deadline else None,
            "score": round(rrf_score, 4)
        })

    return {
        "query": q,
        "results_count": len(output),
        "results": output
    }


from uuid import UUID
from fastapi import HTTPException
from app.models.bookmark import Bookmark
from app.models.grant import Grant

@router.get("/grants/{grant_id}", status_code=status.HTTP_200_OK)
async def get_grant_details(
    grant_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch structured metadata, S3 download links, and eligibility criteria rules for a specific grant."""
    from sqlalchemy.orm import selectinload
    stmt = (
        select(Grant)
        .options(
            selectinload(Grant.provider),
            selectinload(Grant.eligibility_rules)
        )
        .where(Grant.id == grant_id)
    )
    res = await db.execute(stmt)
    grant = res.scalars().first()

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grant with ID '{grant_id}' not found."
        )

    # Check if this user bookmarked it
    bookmark_stmt = select(Bookmark).where(Bookmark.user_id == current_user.id, Bookmark.grant_id == grant_id)
    bookmark_res = await db.execute(bookmark_stmt)
    is_bookmarked = bookmark_res.scalars().first() is not None

    return {
        "id": grant.id,
        "name": grant.name,
        "description": grant.description,
        "funding_amount_min": float(grant.funding_amount_min) if grant.funding_amount_min else None,
        "funding_amount_max": float(grant.funding_amount_max) if grant.funding_amount_max else None,
        "currency": grant.currency,
        "official_source_link": grant.official_source_link,
        "document_url": grant.document_url,
        "click_count": grant.click_count,
        "bookmark_count": grant.bookmark_count,
        "is_bookmarked": is_bookmarked,
        "provider": {
            "id": grant.provider.id,
            "name": grant.provider.name,
            "website": grant.provider.website,
            "provider_type": grant.provider.provider_type
        } if grant.provider else None,
        "eligibility_rules": [
            {
                "id": rule.id,
                "applicant_type": rule.applicant_type,
                "sector": rule.sector,
                "project_stage": rule.project_stage,
                "min_funding_required": float(rule.min_funding_required)
            }
            for rule in grant.eligibility_rules
        ]
    }


@router.post("/grants/{grant_id}/bookmark", status_code=status.HTTP_200_OK)
async def toggle_bookmark_grant(
    grant_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Toggle bookmark state for a specific grant opportunity."""
    grant = await db.get(Grant, grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grant with ID '{grant_id}' not found."
        )

    # Check if user already bookmarked this grant
    stmt = select(Bookmark).where(Bookmark.user_id == current_user.id, Bookmark.grant_id == grant_id)
    res = await db.execute(stmt)
    bookmark = res.scalars().first()

    if bookmark:
        await db.delete(bookmark)
        grant.bookmark_count = max(0, grant.bookmark_count - 1)
        await db.commit()
        return {"bookmarked": False, "bookmark_count": grant.bookmark_count}
    else:
        new_bookmark = Bookmark(user_id=current_user.id, grant_id=grant_id)
        db.add(new_bookmark)
        grant.bookmark_count += 1
        await db.commit()
        return {"bookmarked": True, "bookmark_count": grant.bookmark_count}


@router.get("/bookmarks", status_code=status.HTTP_200_OK)
async def list_bookmarked_grants(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieve all grants bookmarked by the currently authenticated user."""
    stmt = select(Grant).join(Bookmark).where(Bookmark.user_id == current_user.id)
    res = await db.execute(stmt)
    grants = res.scalars().all()

    output = []
    for grant in grants:
        output.append({
            "id": grant.id,
            "name": grant.name,
            "description": grant.description,
            "funding_amount_max": float(grant.funding_amount_max) if grant.funding_amount_max else None,
            "currency": grant.currency,
            "deadline": grant.deadline.isoformat() if grant.deadline else None,
            "bookmark_count": grant.bookmark_count
        })
    return output
