from abc import ABC, abstractmethod
from typing import Optional


class BaseStorageService(ABC):
    """Abstract base class for document storage systems."""

    @abstractmethod
    async def upload_file(
        self,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None
    ) -> str:
        """Upload file content and return the file identifier/key/URL."""
        pass

    @abstractmethod
    async def download_file(self, file_key: str) -> bytes:
        """Download and return the file binary contents."""
        pass

    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        """Delete the file from storage. Returns True if deleted successfully."""
        pass
