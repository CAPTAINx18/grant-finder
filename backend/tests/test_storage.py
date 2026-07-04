import shutil
from pathlib import Path
import pytest

from app.services.storage.local import LocalFileStorageService
from app.services.storage.s3 import MockS3StorageService


@pytest.fixture
def temp_storage_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary directory path for storage tests."""
    return tmp_path / "test_uploads"


@pytest.mark.asyncio
async def test_local_file_storage(temp_storage_dir: Path) -> None:
    """Test LocalFileStorageService uploads, downloads, and deletions."""
    service = LocalFileStorageService(base_path=str(temp_storage_dir))
    
    file_name = "test_document.txt"
    file_content = b"This is a test document content for GrantFinder storage."
    
    # 1. Test upload
    key = await service.upload_file(file_name, file_content, "text/plain")
    assert key is not None
    assert key.endswith(file_name)
    assert (temp_storage_dir / key).exists()

    # 2. Test download
    downloaded = await service.download_file(key)
    assert downloaded == file_content

    # 3. Test delete
    deleted = await service.delete_file(key)
    assert deleted is True
    assert not (temp_storage_dir / key).exists()

    # 4. Test download non-existent raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        await service.download_file("non-existent-key")


@pytest.mark.asyncio
async def test_mock_s3_storage() -> None:
    """Test MockS3StorageService uploads, downloads, and deletions in memory."""
    service = MockS3StorageService()
    
    file_name = "grant_proposal.pdf"
    file_content = b"PDF binary stream simulator mock content"
    
    # 1. Test upload
    key = await service.upload_file(file_name, file_content, "application/pdf")
    assert key is not None
    assert file_name in key
    
    # 2. Test download
    downloaded = await service.download_file(key)
    assert downloaded == file_content
    
    # 3. Test delete
    deleted = await service.delete_file(key)
    assert deleted is True
    
    # 4. Test double deletion / deleting missing file
    deleted_again = await service.delete_file(key)
    assert deleted_again is False
