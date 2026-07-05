from uuid import uuid4
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.grant import Grant
from app.models.grant_provider import GrantProvider
from app.models.bookmark import Bookmark
from app.models.eligibility_rule import EligibilityRule
from app.api.v1.endpoints.search import get_grant_details, toggle_bookmark_grant, list_bookmarked_grants


@pytest.mark.asyncio
async def test_bookmarks_and_grant_details_lifecycle() -> None:
    """Integration test validating grant detail retrievals and bookmark toggle operations."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Start transactional block
        await session.begin()

        try:
            # 1. Seed a test User
            user = User(
                email=f"bookmark_tester_{uuid4()}@test.com",
                hashed_password="SecurePasswordHash",
                is_active=True,
                is_admin=False
            )
            session.add(user)
            await session.flush()

            # 2. Seed a test Provider
            provider = GrantProvider(
                name=f"Bookmark Test Agency {uuid4()}",
                website="https://test.bookmark.agency",
                provider_type="Government"
            )
            session.add(provider)
            await session.flush()

            # 3. Seed a test Grant and eligibility criteria
            grant = Grant(
                provider_id=provider.id,
                name="SaaS Bookmark Innovation Grant",
                description="Funding for SaaS platforms integrating hybrid FTS and vector search models.",
                currency="USD",
                funding_amount_max=150000,
                click_count=0,
                bookmark_count=0
            )
            session.add(grant)
            await session.flush()

            rule = EligibilityRule(
                grant_id=grant.id,
                applicant_type="Startup",
                sector="Technology",
                project_stage="Prototype",
                min_funding_required=5000
            )
            session.add(rule)
            await session.flush()

            # 4. Fetch details initially - should return details and is_bookmarked as False
            details_init = await get_grant_details(grant.id, current_user=user, db=session)
            assert details_init["id"] == grant.id
            assert details_init["name"] == "SaaS Bookmark Innovation Grant"
            assert details_init["is_bookmarked"] is False
            assert details_init["bookmark_count"] == 0
            assert details_init["provider"]["name"] == provider.name
            assert len(details_init["eligibility_rules"]) == 1
            assert details_init["eligibility_rules"][0]["applicant_type"] == "Startup"

            # 5. Toggle bookmark - should create bookmark record and increment count
            toggle_res = await toggle_bookmark_grant(grant.id, current_user=user, db=session)
            assert toggle_res["bookmarked"] is True
            assert toggle_res["bookmark_count"] == 1

            # 6. Verify detail state reflects bookmarked: True
            details_bookmarked = await get_grant_details(grant.id, current_user=user, db=session)
            assert details_bookmarked["is_bookmarked"] is True
            assert details_bookmarked["bookmark_count"] == 1

            # 7. Check list bookmarked grants
            list_res = await list_bookmarked_grants(current_user=user, db=session)
            assert len(list_res) == 1
            assert list_res[0]["id"] == grant.id
            assert list_res[0]["name"] == "SaaS Bookmark Innovation Grant"

            # 8. Toggle bookmark again - should remove record and decrement count
            toggle_res_off = await toggle_bookmark_grant(grant.id, current_user=user, db=session)
            assert toggle_res_off["bookmarked"] is False
            assert toggle_res_off["bookmark_count"] == 0

            # 9. Verify details state reflects bookmarked: False
            details_final = await get_grant_details(grant.id, current_user=user, db=session)
            assert details_final["is_bookmarked"] is False
            assert details_final["bookmark_count"] == 0

        finally:
            # Rollback the transaction to keep database clean
            await session.rollback()
            await engine.dispose()
