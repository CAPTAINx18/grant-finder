from datetime import datetime, timezone
import logging
from typing import Any, Dict
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawlers.registry import get_crawler
from app.models.grant import Grant
from app.models.grant_provider import GrantProvider
from app.models.eligibility_rule import EligibilityRule
from app.models.grant_source_registry import GrantSourceRegistry
from app.services.ai.base import BaseEmbeddingService
from app.services.storage.base import BaseStorageService

logger = logging.getLogger(__name__)


class IngestionService:
    """Service orchestrating crawler execution, document uploads, embedding generation, and database ingestion."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: BaseEmbeddingService,
        storage_service: BaseStorageService
    ):
        self.db = db
        self.embedding_service = embedding_service
        self.storage_service = storage_service

    async def run_ingestion_for_source(self, source_id: UUID) -> Dict[str, Any]:
        """Trigger and execute the ingestion pipeline for a registered Crawler source registry entry."""
        # 1. Fetch crawler source registry entry
        source = await self.db.get(GrantSourceRegistry, source_id)
        if not source:
            raise ValueError(f"Ingestion source with ID '{source_id}' not found.")

        if not source.is_active:
            logger.info(f"Ingestion source '{source.name}' is inactive. Skipping run.")
            return {"status": "skipped", "message": "Source is inactive."}

        # Update last run metadata to in-progress
        source.last_run_at = datetime.now(timezone.utc)
        source.last_run_status = "running"
        await self.db.commit()

        added_count = 0
        skipped_count = 0
        error_msg = None

        try:
            # 2. Instantiate registered crawler class dynamically
            crawler_config = source.metadata_json or {}
            
            from app.core.config import settings
            if source.update_method == "mock" and not settings.ENABLE_MOCK_DATA:
                logger.warning(f"[{source.name}] Mock ingestion requested but ENABLE_MOCK_DATA is False. Aborting.")
                source.last_run_status = "failed"
                source.last_run_error = "Mock data ingestion is disabled in production."
                await self.db.commit()
                return {
                    "status": "failed",
                    "fetched_items": 0,
                    "added_items": 0,
                    "skipped_items": 0,
                    "error": "Mock data ingestion is disabled in production."
                }

            # We map update_method (e.g. 'mock') directly to the crawler registry key
            crawler = get_crawler(
                name=source.update_method,
                source_name=source.name,
                config=crawler_config
            )

            # 3. Fetch and parse raw data
            raw_data = await crawler.fetch()
            parsed_grants = await crawler.parse(raw_data)

            # 4. Ingest parsed grants
            for item in parsed_grants:
                # Extract and upload attached documents first
                document_url = None
                docs = await crawler.extract_documents(item)
                if docs:
                    filename, content = docs[0]  # Take primary guidelines document
                    try:
                        document_url = await self.storage_service.upload_file(
                            file_name=filename,
                            file_content=content,
                            content_type="application/octet-stream"
                        )
                    except Exception as upload_err:
                        logger.error(f"Failed to upload document '{filename}': {upload_err}")

                link = item.get("official_source_link")
                
                # Check for duplicates based on official source URL link
                if link:
                    dup_query = select(Grant).where(Grant.official_source_link == link)
                    dup_result = await self.db.execute(dup_query)
                    existing_grant = dup_result.scalars().first()
                    if existing_grant:
                        logger.info(f"Duplicate grant found for link: {link}. Updating existing record.")
                        existing_grant.name = item["name"]
                        existing_grant.description = item["description"]
                        existing_grant.funding_amount_min = item.get("funding_amount_min")
                        existing_grant.funding_amount_max = item.get("funding_amount_max")
                        existing_grant.currency = item.get("currency", "USD")
                        if document_url:
                            existing_grant.document_url = document_url
                        
                        # Populate India-first Metadata
                        existing_grant.country = item.get("country") or item.get("provider_info", {}).get("country", "India")
                        existing_grant.funding_currency = item.get("funding_currency") or item.get("currency", "INR")
                        existing_grant.eligibility_country = item.get("eligibility_country") or item.get("country_eligibility", "India")
                        existing_grant.source_type = item.get("source_type") or item.get("provider_info", {}).get("provider_type", "Government")
                        
                        from sqlalchemy import func
                        existing_grant.search_vector = func.to_tsvector('english', f"{item['name']} {item['description']}")
                        
                        # Regenerate embedding
                        context_text = f"Grant Name: {existing_grant.name}. Description: {existing_grant.description}"
                        try:
                            existing_grant.embedding = await self.embedding_service.get_embedding(context_text)
                        except Exception as emb_err:
                            logger.error(f"Failed to generate embedding on update: {emb_err}")
                        
                        # Update eligibility rules
                        delete_rules_stmt = select(EligibilityRule).where(EligibilityRule.grant_id == existing_grant.id)
                        delete_rules_res = await self.db.execute(delete_rules_stmt)
                        old_rules = delete_rules_res.scalars().all()
                        for rule in old_rules:
                            await self.db.delete(rule)
                        
                        for rule_data in item.get("eligibility_rules", []):
                            rule = EligibilityRule(
                                grant_id=existing_grant.id,
                                applicant_type=rule_data.get("applicant_type"),
                                sector=rule_data.get("sector"),
                                project_stage=rule_data.get("project_stage"),
                                min_funding_required=rule_data.get("min_funding_required", 0.0)
                            )
                            self.db.add(rule)
                        
                        skipped_count += 1
                        continue

                # Retrieve or create provider
                prov_info = item["provider_info"]
                prov_name = prov_info["name"]
                
                prov_query = select(GrantProvider).where(GrantProvider.name == prov_name)
                prov_result = await self.db.execute(prov_query)
                provider = prov_result.scalars().first()
                
                if not provider:
                    provider = GrantProvider(
                        name=prov_name,
                        website=prov_info.get("website"),
                        provider_type=prov_info.get("provider_type")
                    )
                    self.db.add(provider)
                    await self.db.flush()  # Populates provider.id

                # Populate Grant details
                from sqlalchemy import func
                grant = Grant(
                    provider_id=provider.id,
                    name=item["name"],
                    description=item["description"],
                    funding_amount_min=item.get("funding_amount_min"),
                    funding_amount_max=item.get("funding_amount_max"),
                    currency=item.get("currency", "USD"),
                    official_source_link=link,
                    document_url=document_url,
                    click_count=0,
                    bookmark_count=0,
                    search_vector=func.to_tsvector('english', f"{item['name']} {item['description']}"),
                    country=item.get("country") or item.get("provider_info", {}).get("country", "India"),
                    funding_currency=item.get("funding_currency") or item.get("currency", "INR"),
                    eligibility_country=item.get("eligibility_country") or item.get("country_eligibility", "India"),
                    source_type=item.get("source_type") or item.get("provider_info", {}).get("provider_type", "Government")
                )

                # Generate vector embedding for semantic searches
                context_text = f"Grant Name: {grant.name}. Description: {grant.description}"
                try:
                    grant.embedding = await self.embedding_service.get_embedding(context_text)
                except Exception as emb_err:
                    logger.error(f"Failed to generate embedding: {emb_err}")
                    grant.embedding = None

                self.db.add(grant)
                await self.db.flush()  # Populates grant.id

                # Populate eligibility rules
                for rule_data in item.get("eligibility_rules", []):
                    rule = EligibilityRule(
                        grant_id=grant.id,
                        applicant_type=rule_data.get("applicant_type"),
                        sector=rule_data.get("sector"),
                        project_stage=rule_data.get("project_stage"),
                        min_funding_required=rule_data.get("min_funding_required", 0.0)
                    )
                    self.db.add(rule)

                added_count += 1

            source.last_run_status = "success"
            await self.db.commit()
            logger.info(f"Ingestion run completed for source '{source.name}': Added {added_count}, Skipped {skipped_count}.")

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Ingestion run failed for source '{source.name}': {e}")
            source.last_run_status = "failed"
            source.last_run_error = error_msg
            await self.db.commit()

        return {
            "status": source.last_run_status,
            "fetched_items": added_count + skipped_count,
            "added_items": added_count,
            "skipped_items": skipped_count,
            "error": error_msg
        }
