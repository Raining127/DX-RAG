"""File management API (SPEC F016, Section 6.6)."""

from pathlib import Path, PureWindowsPath

from fastapi import APIRouter, Query

from app.core.config import settings
from app.core.errors import AppError
from app.core.vector_store import ChromaVectorStore
from app.models.schemas import (
    FileDeleteResponse,
    FileItem,
    FileListResponse,
    FilePreviewResponse,
)
from app.services.keyword_index import invalidate_keyword_index

router = APIRouter()


@router.get("/files", response_model=FileListResponse)
def list_files(
    collection_name: str = Query(..., description="Target knowledge base name"),
) -> FileListResponse:
    """Return the persisted file records for one knowledge base."""
    vector_store = ChromaVectorStore()
    if collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    files = [
        FileItem.model_validate(file_record)
        for file_record in vector_store.get_files(collection_name)
    ]
    return FileListResponse(collection_name=collection_name, files=files)


@router.get(
    "/files/{file_id}/preview", response_model=FilePreviewResponse
)
def preview_file(
    file_id: str,
    collection_name: str = Query(..., description="Target knowledge base name"),
) -> FilePreviewResponse:
    """Reconstruct a persisted file preview from its stored chunks."""
    vector_store = ChromaVectorStore()
    if collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    chunks = vector_store.get_chunks_by_file(collection_name, file_id)
    if not chunks:
        raise AppError("FILE_NOT_FOUND")

    ordered_chunks = sorted(chunks, key=lambda chunk: chunk.chunk_index)
    full_content = "\n\n".join(chunk.content for chunk in ordered_chunks)
    preview_content = full_content[: settings.MAX_PREVIEW_CHARS]

    return FilePreviewResponse(
        file_id=file_id,
        file_name=ordered_chunks[0].file_name,
        collection_name=collection_name,
        content=preview_content,
        preview_chars=len(preview_content),
        total_chars=len(full_content),
    )


def _delete_raw_file(collection_name: str, file_name: str) -> None:
    """Delete an uploaded file after verifying its path stays in the KB root."""
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    collection_dir = (upload_root / collection_name).resolve()
    target = (collection_dir / file_name).resolve()
    if (
        PureWindowsPath(file_name).name != file_name
        or collection_dir.parent != upload_root
        or target.parent != collection_dir
    ):
        raise AppError("INTERNAL_ERROR")

    target.unlink(missing_ok=True)


@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
def delete_file(
    file_id: str,
    collection_name: str = Query(..., description="Target knowledge base name"),
) -> FileDeleteResponse:
    """Irreversibly delete one file and its persisted chunks."""
    vector_store = ChromaVectorStore()
    if collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    file_record = next(
        (
            record
            for record in vector_store.get_files(collection_name)
            if record["file_id"] == file_id
        ),
        None,
    )
    if file_record is None:
        raise AppError("FILE_NOT_FOUND")

    file_name = file_record["file_name"]
    _delete_raw_file(collection_name, file_name)
    vector_store.delete_by_file(collection_name, file_id)
    invalidate_keyword_index(collection_name)

    return FileDeleteResponse(
        message="文件删除成功",
        file_name=file_name,
        collection_name=collection_name,
    )
