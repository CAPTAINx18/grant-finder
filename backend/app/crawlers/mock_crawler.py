import logging
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from app.crawlers.base import BaseCrawler
from app.crawlers.registry import register_crawler

logger = logging.getLogger(__name__)


@register_crawler("mock")
class MockCrawler(BaseCrawler):
    """Mock crawler that returns simulated grant opportunities for pipeline testing."""

    async def fetch(self) -> Any:
        logger.info(f"[{self.source_name}] Mock fetch invoked.")
        # Return a list of raw mock grant payloads
        return [
            {
                "id": "raw-mock-1",
                "title": "National Technology Innovation Fund",
                "desc": "Funding for startups developing cutting edge software, blockchain, or machine learning applications.",
                "amount_range": [50000, 250000],
                "source_url": "https://mocksite.gov/tech-fund-2026",
                "agency": "Bureau of Technology",
                "eligibility": {
                    "applicant_types": ["Startup", "Small Business"],
                    "sectors": ["Technology", "Software"],
                    "stages": ["R&D", "Prototype"]
                },
                "doc_name": "guidelines_tech_2026.pdf",
                "doc_content": b"Mock guidelines PDF byte contents for tech innovation grant."
            },
            {
                "id": "raw-mock-2",
                "title": "Clean Oceans Initiative Grant",
                "desc": "Support for nonprofit initiatives dedicated to plastic removal, marine biology research, and shoreline cleanup.",
                "amount_range": [10000, 75000],
                "source_url": "https://mocksite.org/clean-oceans",
                "agency": "Global Ecology Foundation",
                "eligibility": {
                    "applicant_types": ["Non-Profit", "University"],
                    "sectors": ["Environment", "Conservation"],
                    "stages": ["Implementation", "Community Action"]
                },
                "doc_name": "ocean_cleanup_details.docx",
                "doc_content": b"Mock Word document contents containing ocean cleanup criteria."
            }
        ]

    async def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        logger.info(f"[{self.source_name}] Mock parse invoked on {len(raw_data)} items.")
        parsed_grants = []
        
        for item in raw_data:
            # Map raw fields to the standardized database grant structure schema
            parsed = {
                "name": item["title"],
                "description": item["desc"],
                "funding_amount_min": item["amount_range"][0],
                "funding_amount_max": item["amount_range"][1],
                "currency": "USD",
                "official_source_link": item["source_url"],
                "provider_info": {
                    "name": item["agency"],
                    "website": "https://mocksite.gov",
                    "provider_type": "NGO" if "Foundation" in item["agency"] else "Government"
                },
                "eligibility_rules": [
                    {
                        "applicant_type": app_type,
                        "sector": sector,
                        "project_stage": stage,
                        "min_funding_required": 0.0
                    }
                    for app_type in item["eligibility"]["applicant_types"]
                    for sector in item["eligibility"]["sectors"]
                    for stage in item["eligibility"]["stages"]
                ],
                "temp_doc": {
                    "filename": item["doc_name"],
                    "content": item["doc_content"]
                }
            }
            parsed_grants.append(parsed)
            
        return parsed_grants

    async def extract_documents(self, parsed_grant: Dict[str, Any]) -> List[Tuple[str, bytes]]:
        # Retrieve the simulated guideline document from our temp storage dict
        doc_info = parsed_grant.get("temp_doc")
        if doc_info:
            return [(doc_info["filename"], doc_info["content"])]
        return []

    async def ingest(self) -> Dict[str, Any]:
        """Runs the mock pipeline and returns the result count."""
        # Note: Ingestion service coordinates the database saving. 
        # This method is implemented but the general orchestration is run in IngestionService.
        raw = await self.fetch()
        parsed = await self.parse(raw)
        return {
            "source": self.source_name,
            "fetched_count": len(raw),
            "parsed_count": len(parsed)
        }
