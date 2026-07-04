import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.grant import Grant
from app.models.grant_provider import GrantProvider
from app.services.ai.mock import MockEmbeddingService
from app.services.grant_search_service import GrantSearchService


@pytest.mark.asyncio
async def test_postgres_pgvector_hybrid_search() -> None:
    """Integration test validating that pgvector stores, queries, and ranks embeddings correctly in PostgreSQL."""
    # 1. Establish async connection to the active Postgres instance
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Start transactional block
        await session.begin()

        try:
            # 2. Seed a test provider
            from uuid import uuid4
            provider = GrantProvider(
                name=f"Vector Search Test Agency LLC {uuid4()}",
                website="https://test.vector.agency",
                provider_type="Government"
            )
            session.add(provider)
            await session.flush()

            # 3. Initialize search service with MockEmbeddingService
            embedding_service = MockEmbeddingService()
            search_service = GrantSearchService(session, embedding_service)

            g1 = Grant(
                provider_id=provider.id,
                name="AI Research and Deep Learning Grant",
                description="Funding for advanced machine learning, neural networks, and generative AI research projects.",
                currency="USD",
                click_count=0,
                bookmark_count=0
            )
            g2 = Grant(
                provider_id=provider.id,
                name="Clean Energy Climate Solution Grant",
                description="Financial support for solar panels, wind turbine engineering, and renewable energy storage.",
                currency="USD",
                click_count=0,
                bookmark_count=0
            )

            # create_grant generates 1536-dimensional embeddings and inserts them into PostgreSQL
            await search_service.create_grant(g1)
            await search_service.create_grant(g2)
            await session.flush()

            # 4. Search for "deep learning" - should rank AI Grant first
            results_ai = await search_service.hybrid_search("deep learning", limit=5, threshold=-1.0)
            assert len(results_ai) >= 1
            best_match_ai = results_ai[0][0]
            assert best_match_ai.name == "AI Research and Deep Learning Grant"

            # 5. Search for "wind turbine" - should rank Clean Energy Grant first
            results_energy = await search_service.hybrid_search("wind turbine", limit=5, threshold=-1.0)
            assert len(results_energy) >= 1
            best_match_energy = results_energy[0][0]
            assert best_match_energy.name == "Clean Energy Climate Solution Grant"

        finally:
            # Rollback the transaction to maintain database cleanliness
            await session.rollback()
            await engine.dispose()
