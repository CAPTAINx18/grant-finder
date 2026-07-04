import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from app.core.config import settings
from app.services.storage.base import BaseStorageService


class LocalFileStorageService(BaseStorageService):
    """Local disk implementation of document storage."""

    def __init__(self, base_path: Optional[str] = None):
        path_str = base_path or settings.STORAGE_LOCAL_PATH
        self.base_path = Path(path_str).resolve()
        # Ensure target storage folder exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None
    ) -> str:
        # Generate a unique key using UUID to prevent collisions
        safe_name = "".join(c for c in file_name if c.isalnum() or c in "._-")
        unique_key = f"{uuid4()}_{safe_name}"
        file_path = self.base_path / unique_key

        # Write binary content
        with open(file_path, "wb") as f:
            f.write(file_content)

        return unique_key

    async def download_file(self, file_key: str) -> bytes:
        file_path = self.base_path / file_key
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File key '{file_key}' not found in storage.")
        
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, file_key: str) -> bool:
        file_path = self.base_path / file_key
        if file_path.exists() and file_path.is_file():
            os.remove(file_path)
            return True
        return False
