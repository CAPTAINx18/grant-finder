import logging
from typing import Any, Optional
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.storage.base import BaseStorageService

logger = logging.getLogger(__name__)


class S3StorageService(BaseStorageService):
    """S3-compatible object storage implementation using boto3 client calls."""

    def __init__(self) -> None:
        self.bucket = settings.S3_BUCKET
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Lazily initialize the boto3 client to allow startup without credentials."""
        if self._client is None:
            if not settings.S3_ACCESS_KEY or not settings.S3_SECRET_KEY:
                logger.error("S3StorageService credentials are not fully configured.")
                raise ValueError("S3 access keys are not configured.")

            self._client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
            )
        return self._client

    async def upload_file(
        self,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None
    ) -> str:
        client = self._get_client()
        safe_name = "".join(c for c in file_name if c.isalnum() or c in "._-")
        unique_key = f"{uuid4()}_{safe_name}"

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            client.put_object(
                Bucket=self.bucket,
                Key=unique_key,
                Body=file_content,
                **extra_args
            )
            logger.info(f"Successfully uploaded {file_name} as {unique_key} to S3 bucket {self.bucket}")
            return unique_key
        except ClientError as e:
            logger.error(f"Failed to upload {file_name} to S3: {e}")
            raise RuntimeError(f"Cloud storage upload error: {e}")

    async def download_file(self, file_key: str) -> bytes:
        client = self._get_client()
        try:
            response = client.get_object(Bucket=self.bucket, Key=file_key)
            return bytes(response["Body"].read())
        except ClientError as e:
            logger.error(f"Failed to download {file_key} from S3: {e}")
            raise FileNotFoundError(f"Cloud storage file {file_key} not found: {e}")

    async def delete_file(self, file_key: str) -> bool:
        client = self._get_client()
        try:
            client.delete_object(Bucket=self.bucket, Key=file_key)
            logger.info(f"Successfully deleted {file_key} from S3 bucket {self.bucket}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {file_key} from S3: {e}")
            return False
class MockS3StorageService(BaseStorageService):
    """Mock implementation of S3 storage for unit testing without credentials."""

    def __init__(self) -> None:
        self.store = {}

    async def upload_file(
        self,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None
    ) -> str:
        key = f"mock-s3-{uuid4()}_{file_name}"
        self.store[key] = file_content
        return key

    async def download_file(self, file_key: str) -> bytes:
        if file_key not in self.store:
            raise FileNotFoundError(f"Mock S3 file {file_key} not found.")
        return self.store[file_key]

    async def delete_file(self, file_key: str) -> bool:
        if file_key in self.store:
            del self.store[file_key]
            return True
        return False
