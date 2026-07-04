from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class BaseCrawler(ABC):
    """Abstract base class for all grant ingestion crawlers."""

    def __init__(self, source_name: str, config: Dict[str, Any]):
        self.source_name = source_name
        self.config = config

    @abstractmethod
    async def fetch(self) -> Any:
        """Fetch raw data from the external source (e.g. HTTP call, API request, file read)."""
        pass

    @abstractmethod
    async def parse(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parse raw data into a list of standardized dictionary formats for grants."""
        pass

    @abstractmethod
    async def extract_documents(self, parsed_grant: Dict[str, Any]) -> List[Tuple[str, bytes]]:
        """Optionally download and extract documents (filename, file content bytes) attached to the grant."""
        pass

    @abstractmethod
    async def ingest(self) -> Dict[str, Any]:
        """Execute the entire pipeline: fetch -> parse -> save to database."""
        pass
