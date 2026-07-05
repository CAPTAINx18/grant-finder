from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
settings.ENABLE_MOCK_DATA = True
from app.crawlers.mock_crawler import MockCrawler
from app.models.grant import Grant
from app.models.grant_provider import GrantProvider
from app.models.grant_source_registry import GrantSourceRegistry
from app.services.ai.mock import MockEmbeddingService
from app.services.storage.s3 import MockS3StorageService
from app.services.ingestion_service import IngestionService
from app.workers.celery_app import celery_app
import app.workers.tasks


@pytest.mark.asyncio
async def test_mock_crawler_fetching_and_parsing() -> None:
    """Test that MockCrawler returns structured mock grants and files properly."""
    crawler = MockCrawler(source_name="Test Source", config={})
    
    # 1. Fetch raw data
    raw = await crawler.fetch()
    assert len(raw) == 2
    assert raw[0]["title"] == "National Technology Innovation Fund"
    
    # 2. Parse raw data
    parsed = await crawler.parse(raw)
    assert len(parsed) == 2
    first_grant = parsed[0]
    
    assert first_grant["name"] == "National Technology Innovation Fund"
    assert first_grant["funding_amount_min"] == 50000
    assert first_grant["funding_amount_max"] == 250000
    assert first_grant["provider_info"]["name"] == "Bureau of Technology"
    assert len(first_grant["eligibility_rules"]) > 0
    
    # 3. Extract mock documents
    docs = await crawler.extract_documents(first_grant)
    assert len(docs) == 1
    assert docs[0][0] == "guidelines_tech_2026.pdf"
    assert docs[0][1].startswith(b"Mock guidelines")


@pytest.mark.asyncio
async def test_ingestion_pipeline_run() -> None:
    """Integration test validating database ingestion, document uploads, and duplicate checks."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Clean up residual test data from previous runs to prevent duplicate key/link collision
    from sqlalchemy import delete
    async with async_session() as session:
        await session.execute(
            delete(Grant).where(Grant.official_source_link.in_([
                "https://mocksite.gov/tech-fund-2026",
                "https://mocksite.org/clean-oceans"
            ]))
        )
        await session.commit()

    async with async_session() as session:
        # Start transactional block
        await session.begin()

        try:
            # 1. Register a test crawl source
            source = GrantSourceRegistry(
                name=f"Mock Test Ingest Source {uuid4()}",
                url="https://mocksite.gov/api",
                update_method="mock",  # Invokes MockCrawler
                cron_schedule="*/5 * * * *",
                is_active=True
            )
            session.add(source)
            await session.flush()  # Populates source.id

            # 2. Instantiate pipeline service dependencies
            embedding_service = MockEmbeddingService()
            storage_service = MockS3StorageService()
            ingestion_service = IngestionService(session, embedding_service, storage_service)

            # 3. Run the ingestion pipeline
            stats = await ingestion_service.run_ingestion_for_source(source.id)
            assert stats["status"] == "success"
            assert stats["added_items"] == 2
            assert stats["skipped_items"] == 0

            # 4. Verify database records are created
            prov_query = select(GrantProvider).where(GrantProvider.name == "Bureau of Technology")
            prov_res = await session.execute(prov_query)
            provider = prov_res.scalars().first()
            assert provider is not None
            assert provider.provider_type == "Government"

            grant_query = select(Grant).where(Grant.provider_id == provider.id)
            grant_res = await session.execute(grant_query)
            grants = grant_res.scalars().all()
            assert len(grants) == 1
            grant = grants[0]
            assert grant.name == "National Technology Innovation Fund"
            assert grant.document_url is not None
            assert grant.embedding is not None

            # 5. Run ingestion again to verify deduplication
            stats_repeat = await ingestion_service.run_ingestion_for_source(source.id)
            assert stats_repeat["status"] == "success"
            assert stats_repeat["added_items"] == 0
            assert stats_repeat["skipped_items"] == 2

        finally:
            # Rollback all database operations to maintain test isolation
            await session.rollback()
            await engine.dispose()


def test_celery_tasks_registration() -> None:
    """Verify that our asynchronous ingestion tasks are correctly registered in the Celery app."""
    assert "app.workers.tasks.run_ingestion_task" in celery_app.tasks
    assert "app.workers.tasks.run_all_active_crawlers_task" in celery_app.tasks


@pytest.mark.asyncio
async def test_world_bank_crawler_lifecycle() -> None:
    from app.crawlers.world_bank_crawler import WorldBankCrawler
    from app.crawlers.base import APICrawler
    
    crawler = WorldBankCrawler(source_name="World Bank India Test", config={})
    assert isinstance(crawler, APICrawler)
    
    raw = await crawler.fetch()
    assert len(raw) >= 2
    
    parsed = await crawler.parse(raw)
    assert len(parsed) == len(raw)
    assert parsed[0]["currency"] == "USD"
    assert parsed[0]["country_eligibility"] == "India"
    assert parsed[0]["provider_info"]["website"] == "https://www.worldbank.org"
    
    docs = await crawler.extract_documents(parsed[0])
    assert len(docs) == 1
    await crawler.close()


@pytest.mark.asyncio
async def test_horizon_europe_india_crawler_lifecycle() -> None:
    from app.crawlers.horizon_europe_india_crawler import HorizonEuropeIndiaCrawler
    from app.crawlers.base import APICrawler
    
    crawler = HorizonEuropeIndiaCrawler(source_name="EU India Test", config={})
    assert isinstance(crawler, APICrawler)
    
    raw = await crawler.fetch()
    assert len(raw) >= 2
    
    parsed = await crawler.parse(raw)
    assert len(parsed) == len(raw)
    assert parsed[0]["currency"] == "EUR"
    assert parsed[0]["country_eligibility"] == "India / EU"
    
    docs = await crawler.extract_documents(parsed[0])
    assert len(docs) == 1
    await crawler.close()


@pytest.mark.asyncio
async def test_startup_india_crawler_lifecycle() -> None:
    from app.crawlers.startup_india_crawler import StartupIndiaCrawler
    from app.crawlers.base import BeautifulSoupCrawler
    
    crawler = StartupIndiaCrawler(source_name="Startup India Test", config={})
    assert isinstance(crawler, BeautifulSoupCrawler)
    
    raw = await crawler.fetch()
    assert len(raw) >= 2
    
    parsed = await crawler.parse(raw)
    assert len(parsed) == len(raw)
    assert parsed[0]["currency"] == "INR"
    assert parsed[0]["country_eligibility"] == "India"
    
    docs = await crawler.extract_documents(parsed[0])
    assert len(docs) == 1


@pytest.mark.asyncio
async def test_birac_crawler_lifecycle() -> None:
    from app.crawlers.birac_crawler import BiracCrawler
    from app.crawlers.base import BeautifulSoupCrawler
    
    crawler = BiracCrawler(source_name="Birac Test", config={})
    assert isinstance(crawler, BeautifulSoupCrawler)
    
    raw = await crawler.fetch()
    assert len(raw) >= 2
    
    parsed = await crawler.parse(raw)
    assert len(parsed) == len(raw)
    assert parsed[0]["currency"] == "INR"
    assert parsed[0]["country_eligibility"] == "India"
    assert "Biotechnology" in parsed[0]["description"] or "Biotech" in parsed[0]["description"] or "active" in parsed[0]["description"].lower()
    
    docs = await crawler.extract_documents(parsed[0])
    assert len(docs) == 1


@pytest.mark.asyncio
async def test_production_mock_restriction() -> None:
    """Validate that when ENABLE_MOCK_DATA is False, running a mock crawl raises ValueError."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await session.begin()
        try:
            # 1. Register mock source
            source = GrantSourceRegistry(
                name=f"Mock Source Production Test {uuid4()}",
                url="https://mocksite.gov/api",
                update_method="mock",
                cron_schedule="*/5 * * * *",
                is_active=True
            )
            session.add(source)
            await session.flush()

            # Set settings flag to False
            original_val = settings.ENABLE_MOCK_DATA
            settings.ENABLE_MOCK_DATA = False
            
            embedding_service = MockEmbeddingService()
            storage_service = MockS3StorageService()
            ingestion_service = IngestionService(session, embedding_service, storage_service)

            res = await ingestion_service.run_ingestion_for_source(source.id)
            assert res["status"] == "failed"
            assert "disabled in production" in res["error"]
                
            # Restore settings flag
            settings.ENABLE_MOCK_DATA = original_val
        finally:
            await session.rollback()
            await engine.dispose()
