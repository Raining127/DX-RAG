"""Pydantic request/response models matching SPEC Section 6 API contracts
and SPEC Section 7 Data Models.

SPEC Section 7.7: v1 SHALL NOT introduce a universal success-response wrapper.
Error models: see app.core.errors (ErrorResponse, ErrorDetail).
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# ChatMessage (SPEC Sections 6.4, 7.6)
# ============================================================================


class ChatMessage(BaseModel):
    """A single conversation turn."""

    role: Literal["user", "assistant"] = Field(
        description="Message role: user or assistant"
    )
    content: str = Field(description="Message content")


# ============================================================================
# Collection Models (SPEC Section 6.5, 7.2)
# ============================================================================


class CollectionCreate(BaseModel):
    """POST /api/collections — request body."""

    name: str = Field(
        description="Collection name (3-50 chars, starts/ends with letter or digit)"
    )


class CollectionRename(BaseModel):
    """PUT /api/collections/{name} — request body."""

    new_name: str = Field(
        description="New collection name (3-50 chars, starts/ends with letter or digit)"
    )


class CollectionItem(BaseModel):
    """A single collection in the list response (SPEC Section 7.2)."""

    name: str = Field(description="Collection name")
    file_count: int = Field(description="Number of files in this collection")


class CollectionResponse(BaseModel):
    """POST /api/collections (201) and DELETE /api/collections/{name} (200) response."""

    message: str = Field(description="Human-readable result message")
    name: str = Field(description="Collection name")


class CollectionRenameResponse(BaseModel):
    """PUT /api/collections/{name} (200) response."""

    message: str = Field(description="Human-readable result message")
    old_name: str = Field(description="Original collection name")
    new_name: str = Field(description="New collection name")


class CollectionListResponse(BaseModel):
    """GET /api/collections (200) response."""

    collections: List[CollectionItem] = Field(
        default_factory=list, description="List of collections"
    )


# ============================================================================
# Upload Models (SPEC Section 6.3)
# ============================================================================


class UploadWarning(BaseModel):
    """A single structured warning from the ingestion pipeline."""

    page_number: int = Field(description="Page number where the warning occurred")
    error_code: Literal["OCR_PAGE_FAILED", "PAGE_RENDER_FAILED"] = Field(
        description="Warning error code"
    )


class UploadResponse(BaseModel):
    """POST /api/upload (200) response — SUCCESS or SUCCESS_WITH_WARNINGS.

    FAILED is not an HTTP 200 status; it is expressed via 4xx/5xx error responses.
    """

    status: Literal["SUCCESS", "SUCCESS_WITH_WARNINGS"] = Field(
        description="Ingestion result status"
    )
    message: str = Field(description="Human-readable result message")
    file_id: str = Field(description="UUID of the uploaded file")
    file_name: str = Field(description="Original filename")
    chunks: int = Field(description="Number of chunks generated")
    collection_name: str = Field(description="Target collection name")
    warnings: List[UploadWarning] = Field(
        default_factory=list, description="List of warnings (empty if SUCCESS)"
    )


# ============================================================================
# QA / Query Models (SPEC Section 6.4)
# ============================================================================


class SourceObject(BaseModel):
    """A single source chunk referenced in the answer."""

    file_id: str = Field(description="UUID of the source file")
    file_name: str = Field(description="Display name of the source file")
    chunk_id: str = Field(description="UUID of the source chunk")
    relevance_score: float = Field(description="Hybrid final_score for this chunk")


class QueryRequest(BaseModel):
    """POST /api/query — request body."""

    question: str = Field(description="User question")
    collection_name: str = Field(description="Target knowledge base name")
    top_k: int = Field(default=5, description="Number of chunks to retrieve (1-20)")
    history: List[ChatMessage] = Field(
        default_factory=list, description="Conversation history (max 20 messages)"
    )


class QueryResponse(BaseModel):
    """POST /api/query (200) response."""

    answer: str = Field(description="LLM-generated answer in Markdown")
    sources: List[SourceObject] = Field(
        default_factory=list, description="Source chunks used in the answer"
    )
    query: str = Field(description="Original user question (echoed)")
    collection_name: str = Field(description="Target collection name")


# ============================================================================
# File Management Models (SPEC Section 6.6)
# ============================================================================


class FileItem(BaseModel):
    """A single file entry in the list response."""

    file_id: str = Field(description="UUID of the file")
    file_name: str = Field(description="Original filename (display only)")
    size: int = Field(description="File size in bytes")
    upload_time: str = Field(description="Upload timestamp (ISO 8601)")
    chunk_count: int = Field(description="Number of chunks generated")
    status: str = Field(description="Ingestion status: SUCCESS or SUCCESS_WITH_WARNINGS")


class FileListResponse(BaseModel):
    """GET /api/files (200) response."""

    collection_name: str = Field(description="Parent collection name")
    files: List[FileItem] = Field(
        default_factory=list, description="List of files in the collection"
    )


class FilePreviewResponse(BaseModel):
    """GET /api/files/{file_id}/preview (200) response."""

    file_id: str = Field(description="UUID of the file")
    file_name: str = Field(description="Display filename")
    collection_name: str = Field(description="Parent collection name")
    content: str = Field(description="Preview text (max 5000 chars)")
    preview_chars: int = Field(description="Actual number of characters returned")
    total_chars: int = Field(description="Total characters across all chunks for this file")


class FileDeleteResponse(BaseModel):
    """DELETE /api/files/{file_id} (200) response."""

    message: str = Field(description="Human-readable result message")
    file_name: str = Field(description="Filename that was deleted")
    collection_name: str = Field(description="Parent collection name")
