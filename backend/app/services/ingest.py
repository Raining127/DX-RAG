"""Document parsing — text file parser + DOCX parser (SPEC F003).

Text files (SPEC F003 3.1):
  v1 rule: .txt / .md / .csv / .json / .log are ALL read as plain text —
  no CSV/JSON structured parsing (SPEC F003 Define / Detail 3.1).

  Encoding cascade (SPEC F003 3.1):
    UTF-8 (strict) → UTF-16 (strict) → GBK (errors="ignore")
    UTF-8/UTF-16 are strict so a wrong guess FAILS and falls through to
    the next encoding instead of silently returning mojibake.

DOCX (SPEC F003 3.3):
  Paragraphs joined by "\n", then table text (cells joined by " " per
  row, rows by "\n"), all joined by "\n".  v1 adds NO synthetic table
  markers ([表格] etc.).

Excel (SPEC F003 3.4):
  openpyxl with data_only=True; per row cells joined by " " (None cells
  skipped), all-empty rows and all-empty sheets skipped, non-empty
  sheets joined by "\n".

PDF (SPEC F003 3.2):
  Per-page loop with PyMuPDF (fitz): native text via page.get_text();
  empty page → OCR fallback callback ocr_page(pdf_path, page_number)
  with 1-based page_number, or empty text; pages joined in order by
  "\n\n".  Encrypted PDF → ENCRYPTED_PDF.

OCR fallback (SPEC F004):
  Qwen-VL-Plus via DashScope MultiModalConversation; page rendered to
  JPEG, Base64 data-URI; retry on timeout/network/429/5xx (initial + 2
  retries, ~1s/~2s backoff per SPEC 9.3); 401/403 raise immediately;
  per-page failure → empty text + structured warning
  {page_number, error_code} in the module warning list.

Cleaning (SPEC F005):
  5 steps in order: splitlines → per-line strip → drop lines empty
  after strip → join with "\\n" → empty result returns "".  An empty
  cleaned text is rejected by the ingest pipeline (a later task).
  v1 does NOT: HTML tag removal, special-char filtering, language
  detection, encoding conversion (handled in parsing).

Chunking & IDs (SPEC F006):
  Markdown header splitting (# → ## → ### → ####) for every file (F006
  Step 1 for .md, Step 2.1 for others), header path prefix
  "{path}\\n\\n{content}", oversized candidates re-split with
  RecursiveCharacterTextSplitter using the frozen separator list, short
  candidates pass through.  IDs (SPEC 7.1): file_id UUID4 per call,
  chunk_id UUID4 per chunk, chunk_index 0-based.

Ingest pipeline (SPEC F002/F004 — IngestService.process):
  parse (by extension, PDF with OCR fallback) → clean → chunk → embed
  → store, file_id generated at start.  Status model: SUCCESS /
  SUCCESS_WITH_WARNINGS / FAILED (0 chunks → FAILED with rollback:
  raw file deleted, delete_by_file; keyword index is the caller's
  concern).  Parse/OCR/embedding AppErrors propagate unchanged.

Error contract (SPEC F003 error table):
  - File missing/unreadable/corrupt → AppError("FILE_PARSE_ERROR") → 422
  - All encoding attempts fail → AppError("FILE_PARSE_ERROR") with
    details.encoding_attempts → HTTP 422

Extension-based dispatch to these parsers is owned by the ingest
pipeline (a later task) — this module only provides the parsing
functions.
"""

import base64
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.config import settings
from app.core.errors import AppError


def parse_text_file(file_path: Path) -> str:
    """Parse a text-format file (.txt/.md/.csv/.json/.log) to plain text.

    Reads the file as bytes and decodes with the UTF-8 → UTF-16 → GBK
    cascade.  GBK is the final fallback with ``errors="ignore"`` per
    SPEC F003 3.1 — invalid bytes are dropped, never an error.

    Args:
        file_path: Path to the text file.

    Returns:
        Decoded text content.  Empty file → empty string.

    Raises:
        AppError: FILE_PARSE_ERROR (422) if the file cannot be read or
            every encoding attempt fails.
    """
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        raise AppError("FILE_PARSE_ERROR") from exc

    attempts: List[Dict[str, str]] = []
    for encoding in ("utf-8", "utf-16", "gbk"):
        # GBK is the last resort: ignore undecodable bytes (SPEC F003 3.1)
        errors = "ignore" if encoding == "gbk" else "strict"
        try:
            return raw.decode(encoding, errors=errors)
        except UnicodeDecodeError as exc:
            attempts.append({"encoding": encoding, "error": str(exc)})
    raise AppError("FILE_PARSE_ERROR", details={"encoding_attempts": attempts})


def parse_docx_file(file_path: Path) -> str:
    """Parse a .docx file to plain text (SPEC F003 3.3).

    Paragraphs and table cells are extracted as plain text:
    - Paragraphs: ``"\\n".join(p.text for p in doc.paragraphs)``
    - Tables: cells joined by ``" "`` within a row, rows by ``"\\n"``
    - Paragraphs and tables joined by ``"\\n"``
    - v1 adds NO synthetic table markers (SPEC F003 3.3 step 5)

    The ``python-docx`` import lives inside this function so that
    importing this module never fails when the package is unavailable —
    the failure surfaces on first use as FILE_PARSE_ERROR.

    Args:
        file_path: Path to the .docx file.

    Returns:
        Plain text of paragraphs and tables.  Empty DOCX → empty string
        (later rejected by cleaning, see F005).

    Raises:
        AppError: FILE_PARSE_ERROR (422) if the file cannot be opened or
            parsed (corrupt file, missing package, etc.).
    """
    try:
        from docx import Document

        doc = Document(str(file_path))
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc

    paragraphs = [p.text for p in doc.paragraphs]
    tables: List[str] = []
    for table in doc.tables:
        rows = [" ".join(cell.text for cell in row.cells) for row in table.rows]
        tables.append("\n".join(rows))
    return "\n".join(paragraphs + tables)


def parse_excel_file(file_path: Path) -> str:
    """Parse an Excel file (.xlsx/.xlsm/.xltx/.xltm) to plain text.

    SPEC F003 3.4:
    - openpyxl opened with ``data_only=True``
    - Iterate all sheets; per row cells joined by ``" "`` with ``None``
      cells skipped; all-empty rows skipped; all-empty sheets skipped
    - Non-empty sheet texts joined by ``"\\n"``

    The ``openpyxl`` import lives inside this function so that
    importing this module never fails when the package is unavailable —
    the failure surfaces on first use as FILE_PARSE_ERROR.

    Args:
        file_path: Path to the Excel file.

    Returns:
        Plain text of all non-empty sheets.  Workbook with no content
        → empty string.

    Raises:
        AppError: FILE_PARSE_ERROR (422) if the file cannot be opened or
            parsed (corrupt file, missing package, etc.).
    """
    try:
        from openpyxl import load_workbook

        wb = load_workbook(file_path, data_only=True)
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc

    sheet_texts: List[str] = []
    for ws in wb.worksheets:
        rows = []
        for row in ws.iter_rows(values_only=True):
            # SPEC 3.4: " ".join(str(cell) for cell in row if cell is not None)
            line = " ".join(str(cell) for cell in row if cell is not None)
            if line:  # skip entirely empty rows
                rows.append(line)
        if rows:  # skip entirely empty sheets
            sheet_texts.append("\n".join(rows))
    return "\n".join(sheet_texts)


def parse_pdf_file(
    file_path: Path,
    ocr_page: Optional[Callable[[Path, int], str]] = None,
) -> str:
    """Parse a .pdf file to plain text, page by page (SPEC F003 3.2).

    Per-page orchestration loop with PyMuPDF (fitz):
    - ``page.get_text()`` extracts native text; non-empty (``strip()``
      is True) → native text used for that page
    - Empty native text → OCR fallback: ``ocr_page(file_path,
      page_number)`` if a callback is provided (the Qwen-VL call itself
      is implemented in T0305), otherwise the page contributes empty
      text
    - Page texts joined in original page order with ``"\\n\\n"``
    - v1: no enhanced OCR on pages that already have native text

    The ``fitz`` import lives inside this function so that importing
    this module never fails when the package is unavailable — the
    failure surfaces on first use as FILE_PARSE_ERROR.

    Args:
        file_path: Path to the .pdf file.
        ocr_page: Optional per-page OCR fallback callback with the
            frozen T0305 contract ``ocr_page(pdf_path, page_number) ->
            str`` — called with the PDF path and the 1-based page
            number of a page whose native text is empty.

    Returns:
        Page texts (native or OCR) joined in page order by ``"\\n\\n"``.

    Raises:
        AppError: ENCRYPTED_PDF (422) if the PDF is encrypted/protected.
        AppError: FILE_PARSE_ERROR (422) if the file cannot be opened or
            parsed (corrupt file, missing package, etc.).
    """
    try:
        import fitz

        # A failed PyMuPDF filename-open can retain a Windows file handle in
        # its exception traceback, preventing the upload layer's rollback.
        # Own the file read here so even malformed PDFs leave no open handle.
        doc = fitz.open(stream=file_path.read_bytes(), filetype="pdf")
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc

    try:
        if doc.needs_pass:
            raise AppError("ENCRYPTED_PDF")
        page_texts: List[str] = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                page_texts.append(text)
            elif ocr_page is not None:
                page_texts.append(ocr_page(file_path, page.number + 1))
            else:
                page_texts.append("")
        return "\n\n".join(page_texts)
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# OCR fallback (SPEC F004 — Qwen-VL-Plus via DashScope)
# ---------------------------------------------------------------------------

_OCR_PROMPT = "请提取图片中的所有文字，保持格式"

# SPEC 9.3: initial request + max 2 retries = max 3 total attempts,
# exponential backoff (~1s, ~2s)
_MAX_TOTAL_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = (1.0, 2.0)

# Structured warnings {page_number, error_code} recorded by ocr_page.
# Lifecycle (clear per file) is owned by the ingest pipeline (T0308).
_OCR_WARNINGS: List[Dict[str, Any]] = []


def get_ocr_warnings() -> List[Dict[str, Any]]:
    """Return the warnings recorded by ``ocr_page`` since the last clear."""
    return list(_OCR_WARNINGS)


def clear_ocr_warnings() -> None:
    """Reset the OCR warning list."""
    _OCR_WARNINGS.clear()


def _record_ocr_warning(page_number: int, error_code: str) -> None:
    """Append a SPEC F004 structured warning."""
    _OCR_WARNINGS.append({"page_number": page_number, "error_code": error_code})


def ocr_page(pdf_path: Path, page_number: int) -> str:
    """OCR a single PDF page with Qwen-VL-Plus (SPEC F004).

    Page ``page_number`` (1-based) is rendered to JPEG via
    ``page.get_pixmap()``, Base64-encoded as a data-URI, and sent to
    DashScope MultiModalConversation (model ``qwen-vl-plus``).

    Retry policy (SPEC 9.3): timeout/network/429/5xx → exponential
    backoff (~1s, ~2s), initial + 2 retries = 3 total attempts.
    401/403 → raise immediately (no retry).  Other non-200 → page
    failure (no retry).

    Per-page failure tolerance (SPEC F004): render failure or retries
    exhausted → return empty string and record a structured warning
    {page_number, error_code} — the page is skipped, not the file.

    Fatal errors (raise, terminate the whole file):
    - ``DASHSCOPE_API_KEY`` missing → AppError("OCR_NOT_CONFIGURED")
    - 401/403 → AppError("OCR_AUTH_FAILED")
    - PDF cannot be opened (or packages missing) → FILE_PARSE_ERROR

    Args:
        pdf_path: Path to the .pdf file.
        page_number: 1-based page number to OCR.

    Returns:
        The page's OCR text, or empty string if the page failed.

    Raises:
        AppError: OCR_NOT_CONFIGURED (500) if the DashScope key is unset.
        AppError: OCR_AUTH_FAILED (500) on 401/403, no retry.
        AppError: FILE_PARSE_ERROR (422) if the PDF cannot be opened.
    """
    if settings.get_dashscope_key() is None:
        raise AppError("OCR_NOT_CONFIGURED")

    try:
        import dashscope
        import fitz
        from dashscope import MultiModalConversation

        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise AppError("FILE_PARSE_ERROR") from exc

    try:
        try:
            page = doc.load_page(page_number - 1)
            pix = page.get_pixmap()
            img_b64 = base64.b64encode(pix.tobytes("jpg")).decode("ascii")
        except Exception:
            _record_ocr_warning(page_number, "PAGE_RENDER_FAILED")
            return ""

        dashscope.api_key = settings.get_dashscope_key()
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": "data:image/jpeg;base64," + img_b64},
                    {"text": _OCR_PROMPT},
                ],
            }
        ]

        for attempt in range(1, _MAX_TOTAL_ATTEMPTS + 1):
            try:
                response = MultiModalConversation.call(
                    model="qwen-vl-plus", messages=messages
                )
            except Exception:
                retriable = True  # timeout / network error (SPEC 9.3)
            else:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    return "".join(
                        item["text"]
                        for item in content
                        if isinstance(item, dict) and "text" in item
                    )
                if response.status_code in (401, 403):
                    # Auth failure: terminate the whole file, no retry (F004)
                    raise AppError("OCR_AUTH_FAILED")
                # Retry only timeout/network/429/5xx; anything else fails
                # the page on this attempt.
                retriable = response.status_code == 429 or response.status_code >= 500
            if attempt < _MAX_TOTAL_ATTEMPTS and retriable:
                time.sleep(_RETRY_BACKOFF_SECONDS[attempt - 1])
                continue
            break

        _record_ocr_warning(page_number, "OCR_PAGE_FAILED")
        return ""
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Cleaning (SPEC F005)
# ---------------------------------------------------------------------------


def clean_text(text: str) -> str:
    """Clean parsed raw text before chunking (SPEC F005).

    The 5 cleaning steps (SPEC F005 Detail, in order):
    1. ``text.splitlines()``
    2. per-line ``line.strip()``
    3. drop lines that are empty after stripping
    4. ``"\\n".join(cleaned_lines)``
    5. empty result → return "" (the ingest pipeline rejects the file)

    Dropping empty lines collapses consecutive blank lines (Define:
    合并连续空白行); line-internal whitespace is preserved — only line
    ends are stripped.

    v1 does NOT (SPEC F005 不做): encoding conversion (done in parsing),
    HTML tag removal, special-char filtering, sensitive-data masking,
    language detection.

    Args:
        text: Raw parsed text.

    Returns:
        Cleaned text, or "" if nothing remains after cleaning.
    """
    lines = text.splitlines()  # Step 1: split by line boundaries
    lines = [line.strip() for line in lines]  # Step 2: strip line ends
    lines = [line for line in lines if line]  # Step 3: drop empty lines
    return "\n".join(lines)  # Step 4; empty → "" (Step 5)


# ---------------------------------------------------------------------------
# Chunking & ID generation (SPEC F006)
# ---------------------------------------------------------------------------

# SPEC F006 Detail: header levels # → ## → ### → #### (metadata keys are
# the LangChain convention for MarkdownHeaderTextSplitter)
_MD_HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ("####", "Header 4"),
]

# SPEC F006 Detail: separator priority from high to low
_CHUNK_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]


def chunk_text(
    text: str,
    source_file: str,
    file_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Chunk cleaned text and assign chunk/file IDs (SPEC F006).

    Pipeline (SPEC F006 Detail):
    1. Markdown header splitting via ``MarkdownHeaderTextSplitter``
       (headers # → ## → ### → ####).  SPEC Step 1 applies it to .md
       files and Step 2.1 to other files ("先尝试 Markdown 标题切分"),
       so every file goes through it.  Each section is a chunk
       candidate; a candidate under headers gets the header path
       prefix ``"{path}\\n\\n{content}"`` where path = non-empty header
       values joined by ``" > "``.
    2. Any candidate longer than ``settings.MAX_CHUNK_SIZE`` is
       re-split with ``RecursiveCharacterTextSplitter`` using the
       frozen separator priority list and ``settings.CHUNK_OVERLAP``.
    3. Candidates ≤ max_chunk_size pass through unchanged; short
       chunks are never merged.

    IDs (SPEC F006 / 7.1): one ``file_id`` (UUID4) per call, shared by
    every chunk of that call; one ``chunk_id`` (UUID4) per chunk;
    ``chunk_index`` 0-based in emission order.  The caller may supply
    ``file_id`` (the ingest pipeline generates it once per file, T0308);
    when omitted a UUID4 is generated here.

    The ``langchain_text_splitters`` import lives inside this function
    so that importing this module never fails when the package is
    unavailable — the failure surfaces on first use as ImportError
    (→ 500 INTERNAL_ERROR via the global handler, SPEC 9.4; chunking
    has no catalog error code).

    Args:
        text: Cleaned text (output of ``clean_text``).
        source_file: Source file name.  Kept for the frozen signature;
            SPEC F006 Step 2.1 applies header splitting to every file,
            so the extension does not gate behavior in v1.
        file_id: Optional caller-supplied file UUID (SPEC 7.1: one per
            upload).  Defaults to a generated UUID4.

    Returns:
        List of chunk dicts, each with keys chunk_id, content,
        chunk_index, file_id.  Empty text → empty list (the ingest
        pipeline rejects the file upstream per F005).
    """
    if not text.strip():
        return []

    from langchain_text_splitters import (
        MarkdownHeaderTextSplitter,
        RecursiveCharacterTextSplitter,
    )

    if file_id is None:
        file_id = str(uuid.uuid4())
    max_chunk_size = settings.MAX_CHUNK_SIZE
    chunk_overlap = settings.CHUNK_OVERLAP

    # Step 1 — Markdown header splitting (every file, see docstring)
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_MD_HEADERS_TO_SPLIT_ON
    )
    candidates: List[str] = []
    for doc in header_splitter.split_text(text):
        content = doc.page_content
        if not content.strip():
            continue  # degenerate empty section — nothing to chunk
        header_values = [
            doc.metadata.get(key)
            for key in ("Header 1", "Header 2", "Header 3", "Header 4")
        ]
        header_path = " > ".join(value for value in header_values if value)
        if header_path:
            content = header_path + "\n\n" + content
        candidates.append(content)

    # Step 2/3 — oversized candidates re-split, short ones pass through
    recursive_splitter = RecursiveCharacterTextSplitter(
        separators=_CHUNK_SEPARATORS,
        chunk_size=max_chunk_size,
        chunk_overlap=chunk_overlap,
    )
    pieces: List[str] = []
    for candidate in candidates:
        if len(candidate) <= max_chunk_size:
            pieces.append(candidate)
        else:
            pieces.extend(recursive_splitter.split_text(candidate))

    return [
        {
            "chunk_id": str(uuid.uuid4()),
            "content": piece,
            "chunk_index": index,
            "file_id": file_id,
        }
        for index, piece in enumerate(pieces)
    ]


# ---------------------------------------------------------------------------
# Ingest pipeline orchestration (SPEC F002 step 8, F004 status model)
# ---------------------------------------------------------------------------

_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}
_EXCEL_EXTENSIONS = {".xlsx", ".xlsm", ".xltx", ".xltm"}


class IngestService:
    """Ingest pipeline orchestration (SPEC F002 / F004).

    ``process()`` runs parse → clean → chunk → embed → store for one
    file and returns the F004 ingestion status model:
      - SUCCESS             — no warnings, chunks > 0
      - SUCCESS_WITH_WARNINGS — OCR per-page warnings, chunks > 0
      - FAILED              — 0 chunks (cleaned text empty); rollback
        deletes the raw file and all its chunks via delete_by_file

    The keyword index is NOT touched here — invalidation is the upload
    layer's responsibility (T0502/T0308 scope split).

    Error boundaries: parse errors (FILE_PARSE_ERROR / ENCRYPTED_PDF),
    OCR fatal errors (OCR_NOT_CONFIGURED / OCR_AUTH_FAILED) and
    embedding errors (EMBEDDING_MODEL_ERROR) propagate unchanged — the
    API layer maps them to their HTTP codes (F003/F004/F007).  FAILED
    is returned as a status, not raised (F004).
    """

    @classmethod
    def process(
        cls,
        file_path: Path,
        file_name: str,
        collection_name: str,
    ) -> Dict[str, Any]:
        """Run the full ingestion pipeline for one uploaded file.

        Args:
            file_path: Path to the saved raw file (saved by the upload
                layer before this call; this method deletes it on
                FAILED).
            file_name: Display-only original file name.
            collection_name: Knowledge base (ChromaDB collection) name.

        Returns:
            Dict with keys status, file_id, file_name, chunks_count,
            warnings.

        Raises:
            AppError: UNSUPPORTED_FILE_TYPE, FILE_PARSE_ERROR,
                ENCRYPTED_PDF, OCR_NOT_CONFIGURED, OCR_AUTH_FAILED,
                EMBEDDING_MODEL_ERROR — propagate unchanged (see class
                docstring).
        """
        from app.core.vector_store import ChromaVectorStore
        from app.services.embedding import encode_chunks

        # Per-file lifecycle: one file_id for all chunks of this upload
        # (SPEC 7.1), one upload timestamp (denormalized, SPEC 7.4),
        # fresh OCR warning list (T0305 channel).
        file_id = str(uuid.uuid4())
        upload_time = datetime.now(timezone.utc).isoformat()
        clear_ocr_warnings()

        raw_text = cls._parse(file_path)
        cleaned = clean_text(raw_text)
        if not cleaned:
            return cls._fail(file_path, file_id, file_name, collection_name)

        chunks = chunk_text(cleaned, file_name, file_id=file_id)
        if not chunks:
            return cls._fail(file_path, file_id, file_name, collection_name)

        warnings = get_ocr_warnings()
        status = "SUCCESS_WITH_WARNINGS" if warnings else "SUCCESS"

        # SPEC F008 Metadata Schema — 9 fields, denormalized file-level
        # fields identical across all chunks of this file_id.
        metadatas = [
            {
                "chunk_id": chunk["chunk_id"],
                "file_id": file_id,
                "file_name": file_name,
                "collection_name": collection_name,
                "chunk_index": chunk["chunk_index"],
                "source_file": f"uploads/{collection_name}/{file_name}",
                "file_size": file_path.stat().st_size,
                "upload_time": upload_time,
                "ingestion_status": status,
            }
            for chunk in chunks
        ]

        embeddings = encode_chunks([chunk["content"] for chunk in chunks])
        store = ChromaVectorStore()
        store.add_texts(
            collection=collection_name,
            chunks=[chunk["content"] for chunk in chunks],
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return {
            "status": status,
            "file_id": file_id,
            "file_name": file_name,
            "chunks_count": len(chunks),
            "warnings": warnings,
        }

    @staticmethod
    def _parse(file_path: Path) -> str:
        """Dispatch to the per-extension parser (SPEC F003)."""
        suffix = file_path.suffix.lower()
        if suffix in _TEXT_EXTENSIONS:
            return parse_text_file(file_path)
        if suffix == ".pdf":
            return parse_pdf_file(file_path, ocr_page=ocr_page)
        if suffix == ".docx":
            return parse_docx_file(file_path)
        if suffix in _EXCEL_EXTENSIONS:
            return parse_excel_file(file_path)
        raise AppError("UNSUPPORTED_FILE_TYPE")

    @classmethod
    def _fail(
        cls,
        file_path: Path,
        file_id: str,
        file_name: str,
        collection_name: str,
    ) -> Dict[str, Any]:
        """FAILED rollback + result dict (SPEC F002 failure atomicity).

        Mandatory: no residual raw file, no residual chunk/vector/
        metadata in ChromaDB (delete_by_file), and the result exposes
        the structured warnings.  The keyword index is not touched —
        the upload layer invalidates it (caller's responsibility).
        """
        from app.core.vector_store import ChromaVectorStore

        file_path.unlink(missing_ok=True)
        ChromaVectorStore().delete_by_file(collection_name, file_id)
        return {
            "status": "FAILED",
            "file_id": file_id,
            "file_name": file_name,
            "chunks_count": 0,
            "warnings": get_ocr_warnings(),
        }



