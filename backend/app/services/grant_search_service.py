import logging
from typing import Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grant import Grant
from app.repositories.grant_repository import GrantRepository
from app.services.ai.base import BaseEmbeddingService

logger = logging.getLogger(__name__)


class GrantSearchService:
    """Service orchestrating semantic search, keyword search, and hybrid fusion search."""

    def __init__(self, db: AsyncSession, embedding_service: BaseEmbeddingService):
        self.repo = GrantRepository(db)
        self.embedding_service = embedding_service

    async def create_grant(self, grant: Grant) -> Grant:
        """Create a grant record and automatically generate its semantic vector embedding."""
        from sqlalchemy import func
        
        # Populate FTS keyword search vector
        grant.search_vector = func.to_tsvector('english', f"{grant.name} {grant.description}")

        # Concatenate name and description to represent the grant context
        context_text = f"Grant Name: {grant.name}. Description: {grant.description}"
        try:
            vector = await self.embedding_service.get_embedding(context_text)
            grant.embedding = vector
        except Exception as e:
            logger.error(f"Failed to generate embedding for grant '{grant.name}': {e}")
            # Save without embedding to maintain system availability
            grant.embedding = None

        return await self.repo.create(grant)

    async def hybrid_search(
        self,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.3
    ) -> List[Tuple[Grant, float]]:
        """Perform Hybrid Search merging FTS and pgvector results using Reciprocal Rank Fusion (RRF)."""
        # 1. Fetch FTS keyword matches
        fts_results = await self.repo.search_by_fts(query_text, limit=limit * 2)

        # 2. Fetch Vector semantic matches
        try:
            query_vector = await self.embedding_service.get_embedding(query_text)
            vector_results = await self.repo.search_by_vector(query_vector, limit=limit * 2, threshold=threshold)
        except Exception as e:
            logger.error(f"Embedding service failed during vector search: {e}")
            vector_results = []

        # 3. Reciprocal Rank Fusion (RRF) Reranking
        # RRF constant (normally set to 60)
        k = 60
        rrf_scores: Dict[Grant, float] = {}

        # Apply FRF scores for FTS results
        for rank, grant in enumerate(fts_results, start=1):
            rrf_scores[grant] = rrf_scores.get(grant, 0.0) + (1.0 / (k + rank))

        # Apply FRF scores for Vector results
        for rank, (grant, similarity) in enumerate(vector_results, start=1):
            rrf_scores[grant] = rrf_scores.get(grant, 0.0) + (1.0 / (k + rank))

        # Apply India-first rank boosting
        for grant in rrf_scores:
            c_elig = (grant.country_eligibility or "").lower()
            c_src = (grant.country or "").lower()
            if "india" in c_elig or "india" in c_src or "global" in c_elig:
                rrf_scores[grant] *= 2.0

        # Sort all grants by their aggregated RRF score descending
        sorted_grants = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)

        # Return the top 'limit' records formatted as (Grant, fusion_score)
        return sorted_grants[:limit]
