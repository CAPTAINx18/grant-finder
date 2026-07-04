import io
from typing import Any
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_active_user, get_current_admin_user, get_storage_service
from app.models.user import User
from app.services.storage.base import BaseStorageService

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    storage_service: BaseStorageService = Depends(get_storage_service)
) -> Any:
    """Upload a document asset (e.g. grant PDFs, guidelines). Requires active user login."""
    try:
        content = await file.read()
        file_key = await storage_service.upload_file(
            file_name=file.filename,
            file_content=content,
            content_type=file.content_type
        )
        return {
            "message": "File uploaded successfully",
            "file_name": file.filename,
            "file_key": file_key
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {e}"
        )


@router.get("/download/{file_key}")
async def download_document(
    file_key: str,
    current_user: User = Depends(get_current_active_user),
    storage_service: BaseStorageService = Depends(get_storage_service)
) -> Any:
    """Download a document asset by its key. Requires active user login."""
    try:
        content = await storage_service.download_file(file_key)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_key}"}
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {e}"
        )


@router.delete("/{file_key}", status_code=status.HTTP_200_OK)
async def delete_document(
    file_key: str,
    current_user: User = Depends(get_current_admin_user),
    storage_service: BaseStorageService = Depends(get_storage_service)
) -> Any:
    """Delete a document asset from storage. Requires Admin privileges."""
    success = await storage_service.delete_file(file_key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with key '{file_key}' not found or could not be deleted."
        )
    return {"message": "Document deleted successfully."}
