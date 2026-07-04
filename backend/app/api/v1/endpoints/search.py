from typing import Any, List
from fastapi import APIRouter, Depends, Query, status
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
