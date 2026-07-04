from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import documents
from app.api.v1.endpoints import search

api_router = APIRouter()

# Register resource sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
