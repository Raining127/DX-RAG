"""File Upload API — POST /api/upload (SPEC F002, Sections 6.3 and 10.2).

Endpoint flow (SPEC F002 Detail normal flow, T0502):
  1-6.  ``validate_upload`` — the pre-ingestion checks below (T0501)
  7.    save the raw bytes to ``uploads/{collection_name}/{file_name}``
  8.    ``IngestService.process`` — parse → clean → chunk → embed → store
  9.    invalidate this collection's keyword index cache
  10.   return the Section 6.3 response

Validation order (SPEC F002 Detail normal flow steps 2-6 + Section 10.2):
  1. file name safety     — 400 `INVALID_FILE_NAME`
  2. extension whitelist  — 400 `UNSUPPORTED_FILE_TYPE`
  3. size limit           — 413 `FILE_TOO_LARGE`
  4. empty file           — 400 `EMPTY_FILE`
  5. knowledge base exists— 404 `COLLECTION_NOT_FOUND`
  6. duplicate file name  — 409 `FILE_ALREADY_EXISTS`

File name safety runs first: SPEC Section 10.2 requires the check to
happen before any filesystem operation, and putting it ahead of the
whole pipeline means no later step ever handles an unvalidated path.

Every check is side-effect free — a rejected upload leaves no file in
``uploads/`` and no data in ChromaDB (AC-SEC-01).
"""

import logging
from pathlib import Path, PureWindowsPath
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import settings
from app.core.errors import AppError
from app.core.vector_store import ChromaVectorStore
from app.models.schemas import UploadResponse
from app.services.ingest import IngestService
from app.services.keyword_index import invalidate_keyword_index

logger = logging.getLogger(__name__)

router = APIRouter()

# SPEC Section 6.3 response examples — one message per 200 outcome.
_STATUS_MESSAGES = {
    "SUCCESS": "上传并入库成功",
    "SUCCESS_WITH_WARNINGS": "上传并入库成功（部分页面 OCR 失败）",
}

# SPEC Section 10.2 upload whitelist — the 11 formats F003 can parse.
_ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".log",
    ".pdf",
    ".docx",
    ".xlsx",
    ".xlsm",
    ".xltx",
    ".xltm",
}


def validate_file_name(file_name: str) -> None:
    """Reject file names carrying path components (SPEC Section 10.2).

    ``PureWindowsPath`` is used on every platform so that ``\\`` counts
    as a separator regardless of the host OS — a backslash name must not
    pass validation on Linux and then resolve to a directory on Windows.
    A name is safe only when it equals its own basename; ``""``, ``"."``
    and ``".."`` are checked explicitly because they are not rewritten by
    the basename comparison alone.

    Sanitization is forbidden — a dangerous name is rejected, never
    silently rewritten into a different one (SPEC Section 10.2).

    Raises:
        AppError: INVALID_FILE_NAME (HTTP 400).
    """
    if not file_name or file_name in {".", ".."}:
        raise AppError("INVALID_FILE_NAME")
    if PureWindowsPath(file_name).name != file_name:
        raise AppError("INVALID_FILE_NAME")


def validate_extension(file_name: str) -> None:
    """Check the final suffix against the whitelist, case-insensitively.

    SPEC F002 Detail: 扩展名校验不区分大小写.  Only the final suffix
    counts, so ``archive.tar.gz`` is judged by ``.gz``.

    Raises:
        AppError: UNSUPPORTED_FILE_TYPE (HTTP 400).
    """
    if PureWindowsPath(file_name).suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise AppError("UNSUPPORTED_FILE_TYPE")


def validate_content(content: bytes) -> None:
    """Check upload size and emptiness (SPEC F002 边界条件).

    ``MAX_UPLOAD_SIZE_MB`` itself is allowed — only a strictly larger
    file is rejected.  A 0-byte file is rejected as EMPTY_FILE.

    Raises:
        AppError: FILE_TOO_LARGE (HTTP 413) or EMPTY_FILE (HTTP 400).
    """
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise AppError("FILE_TOO_LARGE")
    if len(content) == 0:
        raise AppError("EMPTY_FILE")


def validate_upload(
    file_name: str,
    content: bytes,
    collection_name: Optional[str] = None,
) -> str:
    """Run the full pre-ingestion validation pipeline (SPEC F002 steps 2-6).

    Args:
        file_name: Original upload file name (display identity, SPEC 7.1).
        content: Raw upload bytes, used for the size / empty checks only —
            never written to disk here (that is T0502).
        collection_name: Target knowledge base; empty or missing falls
            back to ``settings.CHROMA_COLLECTION`` (SPEC F002 step 4).

    Returns:
        The resolved collection name, for the caller to use downstream.

    Raises:
        AppError: INVALID_FILE_NAME, UNSUPPORTED_FILE_TYPE, FILE_TOO_LARGE,
            EMPTY_FILE, COLLECTION_NOT_FOUND, FILE_ALREADY_EXISTS.
    """
    validate_file_name(file_name)
    validate_extension(file_name)
    validate_content(content)

    collection = collection_name or settings.CHROMA_COLLECTION
    store = ChromaVectorStore()
    if collection not in store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    # Duplicate scope is one knowledge base (SPEC F002 step 6 / AC-F002-03):
    # the same name in another collection is a different file.  Compared
    # case-insensitively because uploads/ lives on case-insensitive
    # filesystems, where "Doc.pdf" would overwrite "doc.pdf".
    existing = {file["file_name"].lower() for file in store.get_files(collection)}
    if file_name.lower() in existing:
        raise AppError("FILE_ALREADY_EXISTS")

    return collection


# ---------------------------------------------------------------------------
# Upload endpoint (SPEC F002 normal flow steps 7-10, Section 6.3; T0502)
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    collection_name: Optional[str] = Form(default=None),
) -> UploadResponse:
    """Upload one file into a knowledge base and run the ingest pipeline.

    Validation runs to completion before the first byte is written, so a
    rejected upload never creates a file (SPEC Section 10.2, AC-SEC-01).

    Failure atomicity (SPEC F002 Upload Failure Atomicity): the saved raw
    file must not survive a failed ingestion.  ``IngestService`` removes
    it on the FAILED result path, and this endpoint removes it when the
    pipeline raises instead (FILE_PARSE_ERROR, ENCRYPTED_PDF, OCR and
    embedding errors) — the save is this layer's side effect, so undoing
    it is this layer's duty.  FAILED is never a 200: it is reported as
    422 FILE_PARSE_ERROR (SPEC Section 6.3).

    The keyword index is invalidated only on the 200 outcomes (F002 step
    9).  A failed upload adds no chunk, so its index is already correct.

    Returns:
        UploadResponse with status SUCCESS or SUCCESS_WITH_WARNINGS.

    Raises:
        AppError: INVALID_FILE_NAME, UNSUPPORTED_FILE_TYPE, FILE_TOO_LARGE,
            EMPTY_FILE, COLLECTION_NOT_FOUND, FILE_ALREADY_EXISTS (from
            validation) or FILE_PARSE_ERROR plus the ingest error codes.
    """
    file_name = file.filename or ""
    content = file.file.read()
    collection = validate_upload(file_name, content, collection_name)

    target = Path(settings.UPLOAD_DIR) / collection / file_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    try:
        result = IngestService.process(target, file_name, collection)
    except Exception:
        _discard_saved_file(target)
        raise

    if result["status"] == "FAILED":
        raise AppError("FILE_PARSE_ERROR")

    invalidate_keyword_index(collection)

    return UploadResponse(
        status=result["status"],
        message=_STATUS_MESSAGES[result["status"]],
        file_id=result["file_id"],
        file_name=result["file_name"],
        chunks=result["chunks_count"],
        collection_name=collection,
        warnings=result["warnings"],
    )


def _discard_saved_file(target: Path) -> None:
    """Delete the raw file saved for an upload that then failed.

    Never raises: a cleanup failure is logged with the residual path so
    it cannot mask the ingestion error the caller is re-raising.
    """
    try:
        target.unlink(missing_ok=True)
    except OSError:
        logger.exception("upload rollback: failed to delete %s", target)
