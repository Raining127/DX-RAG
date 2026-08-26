from fastapi import APIRouter

from app.api.collections import router as collections_router
from app.api.upload import router as upload_router

api_router = APIRouter()


@api_router.get("/health")
def health_check() -> dict:
    """Basic availability probe (SPEC Section 6.2)."""
    return {"status": "ok"}


api_router.include_router(collections_router)
api_router.include_router(upload_router)

# Sub-routers will be included here in future tasks:
# from app.api.query import router as query_router
# from app.api.files import router as files_router
