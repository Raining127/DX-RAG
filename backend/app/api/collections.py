"""Knowledge Base Management API — create, list, rename, delete collections
(SPEC F001, Section 6.5).

T0401 + T0402 + T0403 scope:
  - POST /api/collections     — create a knowledge base
  - GET  /api/collections     — list knowledge bases with file_count
  - PUT  /api/collections/{name} — rename with full cascade + compensation
  - DELETE /api/collections/{name} — cascade delete (irreversible)

Create flow (SPEC F001 Detail, 5 steps):
  1. Validate name (canonical regex, 400 INVALID_COLLECTION_NAME)
  2. Check duplicate (409 COLLECTION_ALREADY_EXISTS)
  3. Create ChromaDB collection (VectorStore public interface, F008)
  4. Create uploads/{name}/ directory
  5. Return 201

List flow: query ChromaDB collection names, count files per collection
via VectorStore.get_files (T0107 metadata aggregation).

Rename flow (SPEC F001 Detail, 7 steps):
  1. Validate new_name (400) / old exists (404) / new free (409)
  2. VectorStore.rename_collection — storage-level rename cascade
     (collection rename + metadata cascade, atomic at storage level)
  3. Rename uploads/{old_name}/ → uploads/{new_name}/
  4. Invalidate keyword index seam (old_name, then new_name)
  5. Read-only verification via public read APIs
  Any step failure → compensation (reverse completed steps) → 500
  RENAME_FAILED; observable state is the complete old state (F001).

Delete flow (SPEC F001 Delete, 4 steps; irreversible — SPEC 6.5):
  1. Existence check (404 COLLECTION_NOT_FOUND) — before any
     destructive step
  2. VectorStore.delete_collection (public interface, F008)
  3. Recursive delete of uploads/{name}/ — a missing directory is a
     no-op (delete's goal state is absence; unlike rename it does not
     move a source directory)
  4. Invalidate keyword index seam (T0402)
  Mid-cascade failure → 500 INTERNAL_ERROR + structured log, residual
  state reported honestly; no undo, no compensation.

The name-validation rule below is the SPEC F001 canonical regex as a
shared module-level function — T0404 owns its formal edge-case
verification.
"""

import logging
import re
import shutil
from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings
from app.core.errors import AppError
from app.core.vector_store import ChromaVectorStore
from app.models.schemas import (
    CollectionCreate,
    CollectionItem,
    CollectionListResponse,
    CollectionRename,
    CollectionRenameResponse,
    CollectionResponse,
)
from app.services.keyword_index import invalidate_keyword_index

logger = logging.getLogger(__name__)

router = APIRouter()

# SPEC F001 canonical rule (v1.6 naming-compatibility patch): 3-50 chars,
# letter/digit at both ends, middle may contain letters, digits, _, -.
# No Chinese chars (ChromaDB collection names only accept [a-zA-Z0-9._-]),
# and no "." support by product decision.
_COLLECTION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,48}[A-Za-z0-9]$")


def validate_collection_name(name: str) -> None:
    """SPEC F001 Create step 1: reject names outside the canonical rule.

    Shared by create (T0401) and rename (T0402).  T0404 formalizes the
    edge-case verification of this function.

    Raises:
        AppError: INVALID_COLLECTION_NAME (HTTP 400).
    """
    if not _COLLECTION_NAME_PATTERN.fullmatch(name):
        raise AppError("INVALID_COLLECTION_NAME")


@router.post("/collections", response_model=CollectionResponse, status_code=201)
def create_collection(body: CollectionCreate) -> CollectionResponse:
    """Create a knowledge base (ChromaDB collection + uploads directory)."""
    name = body.name
    validate_collection_name(name)
    store = ChromaVectorStore()
    if name in store.list_collections():
        raise AppError("COLLECTION_ALREADY_EXISTS")
    store.create_collection(name)
    uploads_dir = Path(settings.UPLOAD_DIR) / name
    uploads_dir.mkdir(parents=True, exist_ok=True)
    return CollectionResponse(message="知识库创建成功", name=name)


@router.get("/collections", response_model=CollectionListResponse)
def list_collections() -> CollectionListResponse:
    """List all knowledge bases with per-collection file_count."""
    store = ChromaVectorStore()
    items = [
        CollectionItem(name=name, file_count=len(store.get_files(name)))
        for name in store.list_collections()
    ]
    return CollectionListResponse(collections=items)


# ---------------------------------------------------------------------------
# Rename orchestration (SPEC F001 — business layer steps, T0402)
# ---------------------------------------------------------------------------


@router.put("/collections/{name}", response_model=CollectionRenameResponse)
def rename_collection(name: str, body: CollectionRename) -> CollectionRenameResponse:
    """Rename a knowledge base with full cascade and compensation (F001).

    Orchestration order (SPEC F001 business layer):
      VectorStore atomic rename → uploads dir rename → keyword
      invalidation → read-only verification.

    All 4xx validations run BEFORE any persistent operation, so their
    error codes are never masked by the RENAME_FAILED mapping.

    Compensation (F001 Rename atomicity): if any orchestration step
    fails, completed steps are reversed — uploads dir back to old_name,
    then ``VectorStore.rename_collection(new_name, old_name)`` if the
    forward rename succeeded — and the response is 500 RENAME_FAILED.
    The observable state is then the complete old state.
    """
    old_name = name
    new_name = body.new_name
    validate_collection_name(new_name)

    store = ChromaVectorStore()
    if old_name not in store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")
    if new_name in store.list_collections():
        raise AppError("COLLECTION_ALREADY_EXISTS")

    vector_done = False
    uploads_done = False
    try:
        store.rename_collection(old_name, new_name)  # storage-level cascade
        vector_done = True
        _rename_uploads_dir(old_name, new_name)  # filesystem rename
        uploads_done = True
        invalidate_keyword_index(old_name)  # keyword index seam (D1)
        invalidate_keyword_index(new_name)
        _verify_rename(store, old_name, new_name)  # read-only verification
    except Exception as exc:
        _compensate_rename(store, old_name, new_name, vector_done, uploads_done)
        raise AppError("RENAME_FAILED") from exc

    return CollectionRenameResponse(
        message="知识库重命名成功", old_name=old_name, new_name=new_name
    )


def _rename_uploads_dir(old_name: str, new_name: str) -> None:
    """Rename uploads/{old_name} → uploads/{new_name} (F001 step 4).

    A missing source directory or an occupied target directory makes
    the rename fail — the orchestration compensates and maps it to 500
    RENAME_FAILED.  Each KB owns its uploads directory (F001 create
    flow), so a missing source dir is a genuine inconsistency, not a
    no-op case.
    """
    old_dir = Path(settings.UPLOAD_DIR) / old_name
    new_dir = Path(settings.UPLOAD_DIR) / new_name
    old_dir.rename(new_dir)


def _verify_rename(
    store: ChromaVectorStore, old_name: str, new_name: str
) -> None:
    """Read-only verification of the storage-level cascade (F001 step 5).

    Uses only VectorStore public read APIs (list_collections /
    list_chunks) — never a metadata write path (AC-F008-03).  Raises
    RuntimeError on any mismatch; the orchestration then compensates
    and maps it to RENAME_FAILED.
    """
    if old_name in store.list_collections():
        raise RuntimeError(
            f"rename verification failed: collection {old_name!r} still exists"
        )
    if new_name not in store.list_collections():
        raise RuntimeError(
            f"rename verification failed: collection {new_name!r} missing"
        )
    for record in store.list_chunks(new_name):
        metadata = record.metadata
        if metadata["collection_name"] != new_name:
            raise RuntimeError(
                f"rename verification failed: chunk {record.chunk_id} "
                f"collection_name={metadata['collection_name']!r}"
            )
        expected_source = f"uploads/{new_name}/{metadata['file_name']}"
        if metadata["source_file"] != expected_source:
            raise RuntimeError(
                f"rename verification failed: chunk {record.chunk_id} "
                f"source_file={metadata['source_file']!r}"
            )


def _compensate_rename(
    store: ChromaVectorStore,
    old_name: str,
    new_name: str,
    vector_done: bool,
    uploads_done: bool,
) -> None:
    """Reverse completed rename steps (F001 Rename atomicity).

    Reverse order of the forward cascade: uploads dir back first, then
    the storage-level cascade via ``rename_collection(new, old)`` — only
    if the forward rename succeeded.  Keyword invalidation is NOT rolled
    back to valid (F001: invalidation has no recovery requirement).
    Compensation failures are logged, not masked — the endpoint still
    returns 500 RENAME_FAILED.
    """
    if uploads_done:
        try:
            _rename_uploads_dir(new_name, old_name)
        except Exception:
            logger.exception(
                "rename compensation: uploads dir restore failed (%s → %s)",
                new_name,
                old_name,
            )
    if vector_done:
        try:
            store.rename_collection(new_name, old_name)
        except Exception:
            logger.exception(
                "rename compensation: VectorStore restore failed (%s → %s)",
                new_name,
                old_name,
            )


# ---------------------------------------------------------------------------
# Delete orchestration (SPEC F001 — business layer steps, T0403)
# ---------------------------------------------------------------------------


@router.delete("/collections/{name}", response_model=CollectionResponse)
def delete_collection(name: str) -> CollectionResponse:
    """Delete a knowledge base with cascade cleanup (F001 Delete, 4 steps).

    Order (T0403 D-1): ChromaDB delete → uploads recursive delete →
    keyword invalidation.  Uploads-first is forbidden — a partial
    rmtree failure would leave a live KB with missing files, while a
    Chroma-first failure leaves the state intact and the only residual
    after Chroma succeeds is an orphan uploads directory.

    Irreversible (SPEC 6.5): no compensation, no undo, no confirmation
    token.  Any mid-cascade failure returns 500 INTERNAL_ERROR with the
    residual state logged honestly — never masked, never restored.
    """
    store = ChromaVectorStore()
    if name not in store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    chroma_deleted = False
    try:
        _assert_safe_uploads_target(name)  # validation, no side effect
        store.delete_collection(name)
        chroma_deleted = True
        _delete_uploads_dir(name)
        invalidate_keyword_index(name)
    except AppError:
        raise
    except Exception as exc:
        logger.exception(
            "delete collection %r failed mid-cascade "
            "(chroma_deleted=%s, uploads_dir_exists=%s)",
            name,
            chroma_deleted,
            (Path(settings.UPLOAD_DIR) / name).exists(),
        )
        raise AppError("INTERNAL_ERROR") from exc

    return CollectionResponse(message="知识库删除成功", name=name)


def _assert_safe_uploads_target(name: str) -> None:
    """Refuse a delete whose resolved uploads target escapes the upload root.

    Defense-in-depth (T0403 D-5): API-created names cannot contain path
    separators (v1.6 regex) and the 404 existence check gates this call,
    so a violation indicates a manually polluted collection name.  Raised
    as RuntimeError so the orchestration logs it and maps it to
    INTERNAL_ERROR without touching anything.
    """
    root = Path(settings.UPLOAD_DIR).resolve()
    target = (root / name).resolve()
    if target.parent != root:
        raise RuntimeError(
            f"refusing delete: uploads target {target} escapes upload root {root}"
        )


def _delete_uploads_dir(name: str) -> None:
    """Recursively delete uploads/{name} (F001 Delete step 2; T0403 D-2/D-5).

    A missing directory is a no-op — delete's goal state is absence, so
    an already-absent directory satisfies it.  (Unlike rename, which must
    move the source directory and treats it missing as a genuine
    inconsistency.)
    """
    target = Path(settings.UPLOAD_DIR) / name
    if target.exists():
        shutil.rmtree(target)
