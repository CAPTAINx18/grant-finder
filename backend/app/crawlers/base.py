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


import httpx
import logging

logger = logging.getLogger(__name__)


class APICrawler(BaseCrawler):
    """Specialized crawler designed to interact with REST/JSON APIs via HTTP."""

    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self):
        await self.client.aclose()


class BeautifulSoupCrawler(BaseCrawler):
    """Specialized crawler designed for static HTML scraping using BeautifulSoup."""

    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        try:
            from bs4 import BeautifulSoup
            self.soup_class = BeautifulSoup
        except ImportError:
            logger.warning("beautifulsoup4 is not installed in the current python runtime.")
            self.soup_class = None


class PlaywrightCrawler(BaseCrawler):
    """Specialized crawler designed for dynamic Javascript-heavy scraping using Playwright."""

    def __init__(self, source_name: str, config: Dict[str, Any]):
        super().__init__(source_name, config)
        try:
            from playwright.async_api import async_playwright
            self.playwright_launcher = async_playwright
        except ImportError:
            logger.warning("playwright is not installed in the current python runtime.")
            self.playwright_launcher = None
