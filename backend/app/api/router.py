from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health")
def health_check() -> dict:
    """Basic availability probe (SPEC Section 6.2)."""
    return {"status": "ok"}


# Sub-routers will be included here in future tasks:
# from app.api.collections import router as collections_router
# from app.api.upload import router as upload_router
# from app.api.query import router as query_router
# from app.api.files import router as files_router
