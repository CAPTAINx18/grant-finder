from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grant import Grant
from app.repositories.base import BaseRepository


class GrantRepository(BaseRepository[Grant]):
    """Repository handling all database operations and specialized searches for Grant models."""

    def __init__(self, db: AsyncSession):
        super().__init__(Grant, db)

    async def search_by_vector(
        self,
        vector: List[float],
        limit: int = 10,
        threshold: float = 0.3
    ) -> List[Tuple[Grant, float]]:
        """Perform semantic cosine distance vector search using pgvector."""
        # Cosine distance operator <=> in pgvector
        distance = Grant.embedding.cosine_distance(vector)
        # Cosine similarity is 1.0 - Cosine Distance
        similarity = (1.0 - distance).label("similarity")

        query = (
            select(Grant, similarity)
            .where(distance <= (1.0 - threshold))
            .order_by(distance.asc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        # Return list of tuples: (Grant, similarity_score)
        return [(row[0], float(row[1])) for row in result.all()]

    async def search_by_fts(
        self,
        query_text: str,
        limit: int = 10
    ) -> List[Grant]:
        """Perform keyword search utilizing PostgreSQL Full-Text Search (FTS)."""
        # Parse query string using websearch syntax (supports quotes, OR, minus)
        ts_query = func.websearch_to_tsquery("english", query_text)
        
        query = (
            select(Grant)
            .where(Grant.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank(Grant.search_vector, ts_query).desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
