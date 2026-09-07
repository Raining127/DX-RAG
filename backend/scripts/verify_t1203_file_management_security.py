"""T1203 — isolated file-management and upload-security E2E verification.

Run from the repository root::

    python backend/scripts/verify_t1203_file_management_security.py

The child-process matrix exercises the real FastAPI collection, upload, file
list, preview, and delete endpoints with a real temporary filesystem and real
ChromaDB persistence. It covers upload -> list -> preview -> delete ->
re-upload, keyword-index invalidation/rebuild, traversal rejection before side
effects, and cross-knowledge-base isolation.

Isolation and declared substitution
-----------------------------------
``UPLOAD_DIR`` and ``CHROMA_PERSIST_DIR`` point to a fresh system temp tree.
The parent removes that tree only after the child exits and releases ChromaDB's
Windows file handles. Repository uploads and Chroma data are never touched.

The repository-local BGE model is verified separately by
``verify_bge_model.py``. This broad deterministic lifecycle matrix substitutes
only ``SentenceTransformer`` construction with a deterministic 512-dimension
normalized model double. The real embedding service, ingestion pipeline, file
APIs, filesystem, and ChromaDB still run.

Exit code 0 means every required check passed; 1 means at least one failed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


_BACKEND = Path(__file__).resolve().parents[1]


def run_probe(probe_root: Path) -> int:
    """Run the verification matrix in an isolated child process."""
    import hashlib
    import math
    import os
    import types
    import uuid
    from datetime import datetime
    from unittest.mock import patch

    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["UPLOAD_DIR"] = str(probe_root / "uploads")
    os.environ["CHROMA_PERSIST_DIR"] = str(probe_root / "chroma")

    sys.path.insert(0, str(_BACKEND))

    import fitz
    from fastapi.testclient import TestClient

    import app.services.embedding as embedding_mod
    import app.services.ingest as ingest_mod
    import app.services.qa as qa_mod
    from app.core.config import settings
    from app.core.vector_store import ChromaVectorStore
    from app.main import app
    from app.services.qa import KeywordRetriever

    results: list[tuple[str, bool, str]] = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        ok = bool(condition)
        results.append((label, ok, detail))
        suffix = f" — {detail}" if detail else ""
        print(f"    [{'PASS' if ok else 'FAIL'}] {label}{suffix}")

    def body_of(response) -> dict:
        try:
            value = response.json()
        except Exception:
            return {}
        return value if isinstance(value, dict) else {}

    def code_of(response) -> str | None:
        return body_of(response).get("error", {}).get("code")

    def is_uuid(value: object) -> bool:
        try:
            uuid.UUID(str(value))
            return True
        except (TypeError, ValueError, AttributeError):
            return False

    class Matrix:
        def __init__(self, rows: list[list[float]]) -> None:
            self.rows = rows

        def tolist(self) -> list[list[float]]:
            return self.rows

    class DeterministicSentenceTransformer:
        """Deterministic external-model boundary for persistence tests."""

        load_count = 0

        def __init__(self, model_path: str) -> None:
            type(self).load_count += 1
            self.model_path = model_path

        def encode(self, texts, normalize_embeddings=False):
            rows: list[list[float]] = []
            for text in texts:
                digest = hashlib.sha256(str(text).encode("utf-8")).digest()
                first = (
                    int.from_bytes(digest[:2], "big")
                    % embedding_mod.EMBEDDING_DIMENSION
                )
                second = (
                    int.from_bytes(digest[2:4], "big")
                    % embedding_mod.EMBEDDING_DIMENSION
                )
                vector = [0.0] * embedding_mod.EMBEDDING_DIMENSION
                vector[first] += 1.0
                vector[second] += 0.5
                norm = math.sqrt(sum(value * value for value in vector))
                if normalize_embeddings and norm:
                    vector = [value / norm for value in vector]
                rows.append(vector)
            return Matrix(rows)

    fake_sentence_transformers = types.ModuleType("sentence_transformers")
    fake_sentence_transformers.SentenceTransformer = (
        DeterministicSentenceTransformer
    )
    embedding_mod._model = None
    with patch.dict(
        sys.modules, {"sentence_transformers": fake_sentence_transformers}
    ):
        model = embedding_mod.get_model()

    check(
        "declared embedding boundary loads once from the configured path",
        DeterministicSentenceTransformer.load_count == 1
        and model.model_path == settings.EMBED_MODEL,
    )

    repo_root = _BACKEND.parent.resolve()
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    chroma_root = Path(settings.CHROMA_PERSIST_DIR).resolve()
    isolated_storage = (
        upload_root != repo_root
        and chroma_root != repo_root
        and repo_root not in upload_root.parents
        and repo_root not in chroma_root.parents
    )
    check(
        "probe storage is outside the repository",
        isolated_storage,
        f"uploads={upload_root}; chroma={chroma_root}",
    )
    if not isolated_storage:
        raise RuntimeError("refusing to run T1203 verification in the repository")

    store = ChromaVectorStore()
    client = TestClient(app, raise_server_exceptions=False)
    kb_a = "t1203-alpha"
    kb_b = "t1203-beta"

    def create_kb(name: str) -> None:
        response = client.post("/api/collections", json={"name": name})
        check(
            f"create isolated knowledge base {name}",
            response.status_code == 201,
            f"HTTP {response.status_code}",
        )

    def upload(
        collection: str,
        file_name: str,
        content: bytes,
        content_type: str = "text/plain",
    ):
        response = client.post(
            "/api/upload",
            files={"file": (file_name, content, content_type)},
            data={"collection_name": collection},
        )
        return response, body_of(response)

    def upload_success(
        collection: str,
        file_name: str,
        content: bytes,
        content_type: str = "text/plain",
    ) -> dict:
        response, body = upload(
            collection, file_name, content, content_type
        )
        check(
            f"upload {file_name} into {collection}",
            response.status_code == 200
            and body.get("status") == "SUCCESS"
            and body.get("file_name") == file_name
            and body.get("collection_name") == collection
            and body.get("chunks", 0) > 0
            and is_uuid(body.get("file_id")),
            f"HTTP {response.status_code}; chunks={body.get('chunks')}",
        )
        return body

    def list_api(collection: str) -> tuple[object, dict]:
        response = client.get(
            "/api/files", params={"collection_name": collection}
        )
        return response, body_of(response)

    def upload_files_snapshot() -> list[str]:
        if not upload_root.exists():
            return []
        return sorted(
            path.relative_to(upload_root).as_posix()
            for path in upload_root.rglob("*")
            if path.is_file()
        )

    def chunk_ids_snapshot() -> dict[str, list[str]]:
        return {
            collection: sorted(
                chunk.chunk_id for chunk in store.list_chunks(collection)
            )
            for collection in (kb_a, kb_b)
        }

    def raw_path(collection: str, file_name: str) -> Path:
        return upload_root / collection / file_name

    def pdf_fixture() -> bytes:
        document = fitz.open()
        try:
            page = document.new_page(width=595, height=842)
            page.insert_text(
                (72, 72),
                "Safe PDF content for T1203 file management verification.",
            )
            return document.tobytes()
        finally:
            document.close()

    create_kb(kb_a)
    create_kb(kb_b)

    print("\n--- Upload filename security and clean-name control")
    valid_pdf = pdf_fixture()
    traversal_names = ("../doc.pdf", "..\\doc.pdf", "subdir/doc.pdf")
    traversal_results = []
    for file_name in traversal_names:
        files_before = upload_files_snapshot()
        chunks_before = chunk_ids_snapshot()
        response, body = upload(
            kb_a, file_name, valid_pdf, "application/pdf"
        )
        traversal_results.append(
            (file_name, response.status_code, code_of(response))
        )
        check(
            f"AC-SEC-01 rejects traversal filename {file_name!r}",
            response.status_code == 400
            and body.get("error", {}).get("code") == "INVALID_FILE_NAME",
            f"HTTP {response.status_code}; code={code_of(response)}",
        )
        check(
            f"AC-SEC-01 rejection for {file_name!r} is side-effect free",
            upload_files_snapshot() == files_before
            and chunk_ids_snapshot() == chunks_before,
        )

    check(
        "AC-SEC-01 covers parent, Windows-parent, and nested path forms",
        traversal_results
        == [
            ("../doc.pdf", 400, "INVALID_FILE_NAME"),
            ("..\\doc.pdf", 400, "INVALID_FILE_NAME"),
            ("subdir/doc.pdf", 400, "INVALID_FILE_NAME"),
        ],
        f"results={traversal_results}",
    )
    check(
        "AC-SEC-01 no escaped or nested doc.pdf exists",
        not (upload_root / "doc.pdf").exists()
        and not (probe_root / "doc.pdf").exists()
        and not raw_path(kb_a, "subdir/doc.pdf").exists(),
    )

    safe_pdf = upload_success(
        kb_a, "safe-document.pdf", valid_pdf, "application/pdf"
    )
    check(
        "AC-SEC-02 a clean supported filename follows normal upload",
        raw_path(kb_a, "safe-document.pdf").read_bytes() == valid_pdf
        and safe_pdf.get("file_name") == "safe-document.pdf"
        and safe_pdf.get("file_id")
        in {
            record["file_id"]
            for record in store.get_files(kb_a)
        },
    )

    print("\n--- Upload, list metadata, and cross-KB isolation")
    preview_bytes = (
        "First persisted paragraph.\nSecond persisted paragraph.\n"
    ).encode("utf-8")
    long_preview_bytes = (
        ("LONG-PREVIEW-BLOCK-0123456789\n" * 240).encode("utf-8")
    )
    delete_a_bytes = b"cascadeuniquekey durable deletion target"
    delete_b_bytes = b"betaisolationkey sibling knowledge base target"

    preview_upload = upload_success(
        kb_a, "preview-source.txt", preview_bytes
    )
    long_upload = upload_success(
        kb_a, "long-preview.txt", long_preview_bytes
    )
    delete_a = upload_success(
        kb_a, "delete-me.txt", delete_a_bytes
    )
    delete_b = upload_success(
        kb_b, "delete-me.txt", delete_b_bytes
    )

    list_a_response, list_a_body = list_api(kb_a)
    list_b_response, list_b_body = list_api(kb_b)
    files_a = list_a_body.get("files", [])
    files_b = list_b_body.get("files", [])
    expected_sizes = {
        "safe-document.pdf": len(valid_pdf),
        "preview-source.txt": len(preview_bytes),
        "long-preview.txt": len(long_preview_bytes),
        "delete-me.txt": len(delete_a_bytes),
    }
    expected_chunk_counts = {
        "safe-document.pdf": safe_pdf.get("chunks"),
        "preview-source.txt": preview_upload.get("chunks"),
        "long-preview.txt": long_upload.get("chunks"),
        "delete-me.txt": delete_a.get("chunks"),
    }
    file_fields = {
        "file_id",
        "file_name",
        "size",
        "upload_time",
        "chunk_count",
        "status",
    }

    check(
        "uploaded files list with the complete metadata contract",
        list_a_response.status_code == 200
        and list_a_body.get("collection_name") == kb_a
        and {record["file_name"] for record in files_a}
        == set(expected_sizes)
        and all(set(record) == file_fields for record in files_a),
        f"HTTP {list_a_response.status_code}; files={len(files_a)}",
    )
    check(
        "file-list size, chunk count, status, and timestamp are accurate",
        all(
            record["size"] == expected_sizes[record["file_name"]]
            and record["chunk_count"]
            == expected_chunk_counts[record["file_name"]]
            and record["status"] == "SUCCESS"
            and datetime.fromisoformat(record["upload_time"]).tzinfo
            is not None
            for record in files_a
        ),
    )
    check(
        "cross-KB file lists expose only their own persisted identities",
        list_b_response.status_code == 200
        and list_b_body.get("collection_name") == kb_b
        and [record["file_id"] for record in files_b]
        == [delete_b.get("file_id")]
        and delete_a.get("file_id")
        not in {record["file_id"] for record in files_b}
        and delete_b.get("file_id")
        not in {record["file_id"] for record in files_a},
    )
    check(
        "same display filename is stored independently in KB-A and KB-B",
        delete_a.get("file_id") != delete_b.get("file_id")
        and raw_path(kb_a, "delete-me.txt").read_bytes()
        == delete_a_bytes
        and raw_path(kb_b, "delete-me.txt").read_bytes()
        == delete_b_bytes,
    )

    print("\n--- Persisted-chunk preview and truncation")
    preview_chunks = store.get_chunks_by_file(
        kb_a, preview_upload.get("file_id", "")
    )
    expected_preview_full = "\n\n".join(
        chunk.content
        for chunk in sorted(
            preview_chunks, key=lambda chunk: chunk.chunk_index
        )
    )
    raw_path(kb_a, "preview-source.txt").write_text(
        "RAW FILE MUTATED AFTER INGESTION",
        encoding="utf-8",
    )

    blocked_message = "preview must not invoke ingestion or model work"
    with (
        patch.object(
            ingest_mod.IngestService,
            "process",
            side_effect=AssertionError(blocked_message),
        ) as ingest,
        patch.object(
            ingest_mod, "parse_text_file", side_effect=AssertionError(blocked_message)
        ) as parse_text,
        patch.object(
            ingest_mod, "parse_pdf_file", side_effect=AssertionError(blocked_message)
        ) as parse_pdf,
        patch.object(
            ingest_mod, "parse_docx_file", side_effect=AssertionError(blocked_message)
        ) as parse_docx,
        patch.object(
            ingest_mod, "parse_excel_file", side_effect=AssertionError(blocked_message)
        ) as parse_excel,
        patch.object(
            ingest_mod, "ocr_page", side_effect=AssertionError(blocked_message)
        ) as ocr,
        patch.object(
            embedding_mod, "encode_chunks", side_effect=AssertionError(blocked_message)
        ) as embed,
        patch.object(
            qa_mod.DeepSeekClient,
            "generate_answer",
            side_effect=AssertionError(blocked_message),
        ) as llm,
    ):
        preview_response = client.get(
            f"/api/files/{preview_upload.get('file_id')}/preview",
            params={"collection_name": kb_a},
        )
    preview_body = body_of(preview_response)
    check(
        "AC-F016-04 preview reconstructs persisted chunks in index order",
        preview_response.status_code == 200
        and preview_body.get("file_id") == preview_upload.get("file_id")
        and preview_body.get("file_name") == "preview-source.txt"
        and preview_body.get("collection_name") == kb_a
        and preview_body.get("content") == expected_preview_full
        and preview_body.get("preview_chars") == len(expected_preview_full)
        and preview_body.get("total_chars") == len(expected_preview_full),
        f"HTTP {preview_response.status_code}",
    )
    check(
        "AC-F016-04 preview ignores mutated raw file and external services",
        "RAW FILE MUTATED" not in preview_body.get("content", "")
        and sum(
            probe.call_count
            for probe in (
                ingest,
                parse_text,
                parse_pdf,
                parse_docx,
                parse_excel,
                ocr,
                embed,
                llm,
            )
        )
        == 0,
    )

    long_chunks = store.get_chunks_by_file(
        kb_a, long_upload.get("file_id", "")
    )
    expected_long_full = "\n\n".join(
        chunk.content
        for chunk in sorted(long_chunks, key=lambda chunk: chunk.chunk_index)
    )
    long_preview_response = client.get(
        f"/api/files/{long_upload.get('file_id')}/preview",
        params={"collection_name": kb_a},
    )
    long_preview_body = body_of(long_preview_response)
    check(
        "AC-F016-05 long preview is truncated to MAX_PREVIEW_CHARS",
        len(expected_long_full) > settings.MAX_PREVIEW_CHARS
        and long_preview_response.status_code == 200
        and long_preview_body.get("content")
        == expected_long_full[: settings.MAX_PREVIEW_CHARS]
        and long_preview_body.get("preview_chars")
        == settings.MAX_PREVIEW_CHARS
        and len(long_preview_body.get("content", ""))
        == settings.MAX_PREVIEW_CHARS,
        f"total={len(expected_long_full)}",
    )
    check(
        "AC-F016-05 total_chars reports the complete pre-truncation length",
        long_preview_body.get("total_chars") == len(expected_long_full)
        and long_preview_body.get("total_chars")
        > long_preview_body.get("preview_chars", 0),
    )

    missing_id = str(uuid.uuid4())
    missing_collection_preview = client.get(
        f"/api/files/{missing_id}/preview",
        params={"collection_name": "t1203-missing"},
    )
    check(
        "AC-F016-06 preview in a missing collection returns 404",
        missing_collection_preview.status_code == 404
        and code_of(missing_collection_preview) == "COLLECTION_NOT_FOUND",
        f"code={code_of(missing_collection_preview)}",
    )

    missing_file_preview = client.get(
        f"/api/files/{missing_id}/preview",
        params={"collection_name": kb_a},
    )
    check(
        "AC-F016-07 missing file preview returns 404 FILE_NOT_FOUND",
        missing_file_preview.status_code == 404
        and code_of(missing_file_preview) == "FILE_NOT_FOUND",
        f"code={code_of(missing_file_preview)}",
    )
    cross_kb_preview = client.get(
        f"/api/files/{delete_a.get('file_id')}/preview",
        params={"collection_name": kb_b},
    )
    check(
        "cross-KB preview cannot resolve a file_id owned by another KB",
        cross_kb_preview.status_code == 404
        and code_of(cross_kb_preview) == "FILE_NOT_FOUND",
    )

    print("\n--- Cascade delete, keyword invalidation, and re-upload")
    delete_file_id = delete_a.get("file_id", "")
    deleted_chunk_ids = {
        chunk.chunk_id
        for chunk in store.get_chunks_by_file(kb_a, delete_file_id)
    }
    delete_chunk_count = len(deleted_chunk_ids)
    keyword = KeywordRetriever(store)
    primed_results = keyword.keyword_search(
        kb_a, "cascadeuniquekey", 5
    )
    check(
        "keyword index is primed with the file before deletion",
        kb_a in KeywordRetriever._indexes
        and any(
            result["chunk_id"] in deleted_chunk_ids
            for result in primed_results
        ),
    )

    beta_before = {
        "raw": raw_path(kb_b, "delete-me.txt").read_bytes(),
        "chunks": {
            chunk.chunk_id
            for chunk in store.get_chunks_by_file(
                kb_b, delete_b.get("file_id", "")
            )
        },
    }
    delete_response = client.delete(
        f"/api/files/{delete_file_id}",
        params={"collection_name": kb_a},
    )
    delete_body = body_of(delete_response)
    remaining_a_chunks = store.list_chunks(kb_a)
    vector_results = store.search(
        kb_a,
        embedding_mod.encode_chunks(["cascadeuniquekey"])[0],
        max(store.get_chunk_count(kb_a), 1),
    )
    check(
        "AC-F016-08 delete endpoint returns the specified confirmation",
        delete_response.status_code == 200
        and delete_body
        == {
            "message": "文件删除成功",
            "file_name": "delete-me.txt",
            "collection_name": kb_a,
        },
        f"HTTP {delete_response.status_code}",
    )
    check(
        "AC-F016-08 raw file and all Chroma records are removed",
        delete_chunk_count > 0
        and not raw_path(kb_a, "delete-me.txt").exists()
        and store.get_chunks_by_file(kb_a, delete_file_id) == []
        and deleted_chunk_ids.isdisjoint(
            {chunk.chunk_id for chunk in remaining_a_chunks}
        )
        and deleted_chunk_ids.isdisjoint(
            {result.chunk_id for result in vector_results}
        )
        and delete_file_id
        not in {record["file_id"] for record in store.get_files(kb_a)},
        f"deleted_chunks={delete_chunk_count}",
    )
    check(
        "AC-F016-08 delete invalidates the collection keyword cache",
        kb_a in KeywordRetriever._dirty_collections,
    )
    check(
        "cross-KB delete preserves same-name raw file and Chroma records",
        raw_path(kb_b, "delete-me.txt").read_bytes() == beta_before["raw"]
        and {
            chunk.chunk_id
            for chunk in store.get_chunks_by_file(
                kb_b, delete_b.get("file_id", "")
            )
        }
        == beta_before["chunks"],
    )

    rebuilt_results = KeywordRetriever(store).keyword_search(
        kb_a, "cascadeuniquekey", 5
    )
    check(
        "invalidated keyword index rebuild removes stale deleted chunks",
        rebuilt_results == []
        and kb_a not in KeywordRetriever._dirty_collections,
    )

    state_before_missing_delete = {
        "uploads": upload_files_snapshot(),
        "chunks": chunk_ids_snapshot(),
    }
    missing_delete = client.delete(
        f"/api/files/{missing_id}",
        params={"collection_name": kb_a},
    )
    check(
        "AC-F016-09 deleting a missing file returns 404 FILE_NOT_FOUND",
        missing_delete.status_code == 404
        and code_of(missing_delete) == "FILE_NOT_FOUND",
        f"code={code_of(missing_delete)}",
    )
    check(
        "AC-F016-09 missing-file delete is side-effect free",
        upload_files_snapshot() == state_before_missing_delete["uploads"]
        and chunk_ids_snapshot() == state_before_missing_delete["chunks"],
    )

    cross_delete = client.delete(
        f"/api/files/{delete_a.get('file_id')}",
        params={"collection_name": kb_b},
    )
    check(
        "cross-KB delete cannot target a file_id from another KB",
        cross_delete.status_code == 404
        and code_of(cross_delete) == "FILE_NOT_FOUND"
        and raw_path(kb_b, "delete-me.txt").exists(),
    )

    reupload_response, reupload_body = upload(
        kb_a, "delete-me.txt", delete_a_bytes
    )
    reuploaded_file_id = reupload_body.get("file_id", "")
    check(
        "re-upload after delete succeeds with a new file identity",
        reupload_response.status_code == 200
        and reupload_body.get("status") == "SUCCESS"
        and is_uuid(reuploaded_file_id)
        and reuploaded_file_id != delete_file_id
        and raw_path(kb_a, "delete-me.txt").read_bytes()
        == delete_a_bytes,
        f"HTTP {reupload_response.status_code}",
    )
    current_delete_records = [
        record
        for record in store.get_files(kb_a)
        if record["file_name"] == "delete-me.txt"
    ]
    check(
        "re-upload leaves no stale file or chunk identity",
        len(current_delete_records) == 1
        and current_delete_records[0]["file_id"] == reuploaded_file_id
        and store.get_chunks_by_file(kb_a, delete_file_id) == []
        and bool(store.get_chunks_by_file(kb_a, reuploaded_file_id)),
    )
    refreshed_keyword = KeywordRetriever(store).keyword_search(
        kb_a, "cascadeuniquekey", 5
    )
    check(
        "re-upload invalidates and rebuilds keyword search with new chunks",
        any(
            result["file_id"] == reuploaded_file_id
            for result in refreshed_keyword
        )
        and all(
            result["chunk_id"] not in deleted_chunk_ids
            for result in refreshed_keyword
        )
        and kb_a not in KeywordRetriever._dirty_collections,
    )

    beta_preview = client.get(
        f"/api/files/{delete_b.get('file_id')}/preview",
        params={"collection_name": kb_b},
    )
    check(
        "KB-B remains independently listable and previewable after KB-A cycle",
        beta_preview.status_code == 200
        and "betaisolationkey" in body_of(beta_preview).get("content", "")
        and delete_b.get("file_id")
        in {
            record["file_id"]
            for record in body_of(list_api(kb_b)[0]).get("files", [])
        },
    )

    print("\n--- Frontend file-management contract wiring")
    frontend_root = _BACKEND.parent / "frontend"
    api_client_source = (frontend_root / "lib" / "api-client.ts").read_text(
        encoding="utf-8"
    )
    file_manager_source = (
        frontend_root / "components" / "FileManager.tsx"
    ).read_text(encoding="utf-8")
    check(
        "FileManager integration uses file_id plus collection for preview/delete",
        "previewFile(file.file_id, resolvedCollection)" in file_manager_source
        and "deleteFile(file.file_id, collectionName)" in file_manager_source
        and "encodeURIComponent(fileId)" in api_client_source
        and "encodeURIComponent(collectionName)" in api_client_source,
    )

    failed = [(label, detail) for label, ok, detail in results if not ok]
    print("\n" + "=" * 78)
    print(f"Required checks: {len(results) - len(failed)}/{len(results)} passed")
    print("RESULT:", "PASS" if not failed else "FAIL")
    if failed:
        for label, detail in failed:
            suffix = f" — {detail}" if detail else ""
            print(f"  - {label}{suffix}")
    print("=" * 78)
    return 1 if failed else 0


def _emit(output: str) -> None:
    """Print child output safely on Windows consoles with legacy codecs."""
    try:
        sys.stdout.write(output)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.write(
            output.encode(encoding, errors="replace").decode(encoding)
        )
    sys.stdout.flush()


def main() -> int:
    """Run the matrix in a child, then remove its isolated temp tree."""
    temp_root = Path(tempfile.gettempdir()).resolve()
    probe_root = Path(
        tempfile.mkdtemp(prefix="t1203_file_management_")
    ).resolve()
    if (
        temp_root not in probe_root.parents
        or not probe_root.name.startswith("t1203_file_management_")
    ):
        print(f"T1203 unsafe temp path: {probe_root}")
        return 1

    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--probe-root",
                str(probe_root),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        _emit(completed.stdout)
        if completed.stderr.strip():
            _emit("--- child stderr ---\n" + completed.stderr)
        return_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        _emit((exc.stdout or "") + (exc.stderr or ""))
        _emit("\nT1203 verification timed out.\n")
        return_code = 1

    for _ in range(10):
        shutil.rmtree(probe_root, ignore_errors=True)
        if not probe_root.exists():
            break
        time.sleep(0.3)
    if probe_root.exists():
        print(f"T1203 cleanup failed: {probe_root}")
        return 1
    return return_code


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe-root":
        raise SystemExit(run_probe(Path(sys.argv[2])))
    raise SystemExit(main())
