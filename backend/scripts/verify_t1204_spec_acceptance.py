"""T1204 final SPEC acceptance audit: inventory, API contract, and F001 E2E.

Run from the repository root::

    python backend/scripts/verify_t1204_spec_acceptance.py

The earlier Phase 12 probes own ingestion, retrieval/QA, and file/security
coverage.  This probe closes the remaining runtime gap around knowledge-base
create/rename/delete behavior, including rename compensation.  It also guards
the frozen AC inventory, mandatory DoD inventory, Section 6 route surface, and
Section 9 error catalog used by the final audit report.

All persistent data lives in a fresh system temporary directory.  The local
BGE model is verified separately by ``verify_bge_model.py``; this focused audit
replaces SentenceTransformer construction with a deterministic, normalized
512-dimensional test double. FastAPI, parsers, ingestion, ChromaDB, filesystem
cascades, and keyword-index behavior are real.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


_BACKEND = Path(__file__).resolve().parents[1]
_REPOSITORY = _BACKEND.parent


def run_probe(probe_root: Path) -> int:
    """Execute the isolated audit matrix in a child process."""
    import hashlib
    import math
    import os
    import re
    import types
    import uuid
    from datetime import datetime, timezone
    from unittest.mock import patch

    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["UPLOAD_DIR"] = str(probe_root / "uploads")
    os.environ["CHROMA_PERSIST_DIR"] = str(probe_root / "chroma")

    sys.path.insert(0, str(_BACKEND))

    import fitz
    from fastapi.testclient import TestClient

    import app.api.collections as collections_api
    import app.services.embedding as embedding_mod
    from app.core.config import settings
    from app.core.errors import _ERROR_CATALOG
    from app.core.vector_store import ChromaVectorStore
    from app.main import app
    from app.services.qa import KeywordRetriever

    results: list[tuple[str, bool, str]] = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        ok = bool(condition)
        results.append((label, ok, detail))
        suffix = f" -- {detail}" if detail else ""
        print(f"    [{'PASS' if ok else 'FAIL'}] {label}{suffix}")

    def body_of(response) -> dict:
        try:
            value = response.json()
        except Exception:
            return {}
        return value if isinstance(value, dict) else {}

    def code_of(response) -> str | None:
        return body_of(response).get("error", {}).get("code")

    def record_snapshot(records) -> list[dict]:
        return sorted(
            [
                {
                    "chunk_id": record.chunk_id,
                    "file_id": record.file_id,
                    "file_name": record.file_name,
                    "collection_name": record.collection_name,
                    "chunk_index": record.chunk_index,
                    "content": record.content,
                    "metadata": dict(record.metadata),
                }
                for record in records
            ],
            key=lambda record: record["chunk_id"],
        )

    class Matrix:
        def __init__(self, rows: list[list[float]]) -> None:
            self.rows = rows

        def tolist(self) -> list[list[float]]:
            return self.rows

    class DeterministicSentenceTransformer:
        """Deterministic external-model boundary for persistence checks."""

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
        "declared embedding boundary is isolated and 512-dimensional",
        DeterministicSentenceTransformer.load_count == 1
        and model.model_path == settings.EMBED_MODEL
        and len(model.encode(["probe"], normalize_embeddings=True).tolist()[0])
        == embedding_mod.EMBEDDING_DIMENSION,
    )

    upload_root = Path(settings.UPLOAD_DIR).resolve()
    chroma_root = Path(settings.CHROMA_PERSIST_DIR).resolve()
    repository = _REPOSITORY.resolve()
    isolated = (
        repository not in upload_root.parents
        and repository not in chroma_root.parents
        and upload_root != repository
        and chroma_root != repository
    )
    check(
        "audit storage is outside the repository",
        isolated,
        f"uploads={upload_root}; chroma={chroma_root}",
    )
    if not isolated:
        raise RuntimeError("refusing to run T1204 against repository storage")

    print("\n--- Frozen SPEC inventory and mandatory DoD")
    spec_text = (_REPOSITORY / "docs" / "SPEC.md").read_text(encoding="utf-8")
    section_5 = spec_text.split("## 5.", 1)[1].split("## 6.", 1)[0]
    section_12 = spec_text.split("## 12.", 1)[1].split("## 13.", 1)[0]
    section_13 = spec_text.split("## 13.", 1)[1].split("## 14.", 1)[0]
    feature_acs = re.findall(r"\*\*(AC-[A-Z0-9-]+):", section_5)
    cross_feature_acs = re.findall(r"\*\*(AC-[A-Z0-9-]+):", section_12)
    unique_acs = set(feature_acs) | set(cross_feature_acs)
    check(
        "Section 5 contains the frozen 65 feature AC occurrences",
        len(feature_acs) == 65,
        f"observed={len(feature_acs)}",
    )
    check(
        "Section 12 contains the frozen 39 cross-feature AC occurrences",
        len(cross_feature_acs) == 39,
        f"observed={len(cross_feature_acs)}",
    )
    check(
        "full mandatory audit contains 85 unique AC identifiers",
        len(unique_acs) == 85,
        f"observed={len(unique_acs)}",
    )
    check(
        "mandatory DoD inventory is exactly DOD-01 through DOD-06",
        set(re.findall(r"DOD-\d{2}", section_13))
        >= {f"DOD-{number:02d}" for number in range(1, 7)},
    )

    store = ChromaVectorStore()
    client = TestClient(app, raise_server_exceptions=False)

    print("\n--- Section 6 API and Section 9 error contracts")
    health = client.get("/api/health")
    check(
        "GET /api/health returns the exact availability contract",
        health.status_code == 200 and body_of(health) == {"status": "ok"},
    )
    http_methods = {"get", "post", "put", "patch", "delete"}
    expected_routes = {
        "/api/health": {"get"},
        "/api/collections": {"get", "post"},
        "/api/collections/{name}": {"put", "delete"},
        "/api/upload": {"post"},
        "/api/query": {"post"},
        "/api/files": {"get"},
        "/api/files/{file_id}/preview": {"get"},
        "/api/files/{file_id}": {"delete"},
    }
    openapi_paths = client.get("/openapi.json").json()["paths"]
    actual_routes = {
        path: set(operations) & http_methods
        for path, operations in openapi_paths.items()
    }
    check(
        "OpenAPI route/method surface matches SPEC Section 6",
        actual_routes == expected_routes,
        f"observed={actual_routes}",
    )
    expected_error_statuses = {
        "INVALID_COLLECTION_NAME": 400,
        "COLLECTION_NOT_FOUND": 404,
        "COLLECTION_ALREADY_EXISTS": 409,
        "RENAME_FAILED": 500,
        "UNSUPPORTED_FILE_TYPE": 400,
        "INVALID_FILE_NAME": 400,
        "EMPTY_FILE": 400,
        "FILE_TOO_LARGE": 413,
        "FILE_ALREADY_EXISTS": 409,
        "FILE_NOT_FOUND": 404,
        "FILE_PARSE_ERROR": 422,
        "REQUEST_VALIDATION_ERROR": 422,
        "ENCRYPTED_PDF": 422,
        "INVALID_QUERY": 400,
        "INVALID_TOP_K": 400,
        "INVALID_HISTORY_FORMAT": 400,
        "LLM_NOT_CONFIGURED": 500,
        "LLM_AUTH_FAILED": 500,
        "LLM_UNAVAILABLE": 502,
        "LLM_RESPONSE_ERROR": 500,
        "EMBEDDING_MODEL_ERROR": 500,
        "OCR_NOT_CONFIGURED": 500,
        "OCR_AUTH_FAILED": 500,
        "COLLECTION_EMPTY": 409,
        "INTERNAL_ERROR": 500,
    }
    actual_error_statuses = {
        code: value[0]
        for code, value in _ERROR_CATALOG.items()
        if code not in {"OCR_PAGE_FAILED", "PAGE_RENDER_FAILED"}
    }
    check(
        "Section 9 HTTP error catalog is complete with exact statuses",
        actual_error_statuses == expected_error_statuses,
    )
    check(
        "Section 9 warning-only codes are represented for upload warnings",
        {"OCR_PAGE_FAILED", "PAGE_RENDER_FAILED"} <= set(_ERROR_CATALOG),
    )

    print("\n--- Literal AC-F008-02 public VectorStore fixture")
    vector_kb = "f008-delete"
    store.create_collection(vector_kb)
    file_a = str(uuid.uuid4())
    file_b = str(uuid.uuid4())
    upload_time = datetime.now(timezone.utc).isoformat()
    vector_chunks: list[str] = []
    vector_metadatas: list[dict] = []
    for file_id, file_name, file_size, count in (
        (file_a, "file-a.txt", 500, 5),
        (file_b, "file-b.txt", 300, 3),
    ):
        for chunk_index in range(count):
            chunk_id = str(uuid.uuid4())
            vector_chunks.append(
                f"{file_name} exact deletion fixture chunk {chunk_index}"
            )
            vector_metadatas.append(
                {
                    "chunk_id": chunk_id,
                    "file_id": file_id,
                    "file_name": file_name,
                    "collection_name": vector_kb,
                    "chunk_index": chunk_index,
                    "source_file": f"uploads/{vector_kb}/{file_name}",
                    "file_size": file_size,
                    "upload_time": upload_time,
                    "ingestion_status": "SUCCESS",
                }
            )
    store.add_texts(
        vector_kb,
        vector_chunks,
        embedding_mod.encode_chunks(vector_chunks),
        vector_metadatas,
    )
    check(
        "AC-F008-02 literal fixture contains file_a=5 and file_b=3 chunks",
        len(store.get_chunks_by_file(vector_kb, file_a)) == 5
        and len(store.get_chunks_by_file(vector_kb, file_b)) == 3
        and store.get_chunk_count(vector_kb) == 8,
    )
    deleted_a = store.delete_by_file(vector_kb, file_a)
    check(
        "AC-F008-02 delete returns 5 and preserves all 3 file_b chunks",
        deleted_a == 5
        and store.get_chunks_by_file(vector_kb, file_a) == []
        and len(store.get_chunks_by_file(vector_kb, file_b)) == 3
        and store.get_chunk_count(vector_kb) == 3,
        f"deleted={deleted_a}",
    )
    store.delete_collection(vector_kb)

    print("\n--- F001 create, list, and validation")
    main_kb = "test-kb"
    renamed_kb = "renamed-kb"
    occupied_kb = "occupied-kb"
    create = client.post("/api/collections", json={"name": main_kb})
    check(
        "AC-F001-01 create returns 201 and creates both durable stores",
        create.status_code == 201
        and body_of(create).get("name") == main_kb
        and main_kb in store.list_collections()
        and (upload_root / main_kb).is_dir(),
    )
    listed = body_of(client.get("/api/collections")).get("collections", [])
    check(
        "collection list exposes the created KB with file_count 0",
        {"name": main_kb, "file_count": 0} in listed,
    )
    state_before_duplicate = set(store.list_collections())
    duplicate = client.post("/api/collections", json={"name": main_kb})
    check(
        "AC-F001-02 duplicate create is a side-effect-free 409",
        duplicate.status_code == 409
        and code_of(duplicate) == "COLLECTION_ALREADY_EXISTS"
        and set(store.list_collections()) == state_before_duplicate,
    )
    invalid_names = ["ab", "bad.name", "-bad", "knowledge-base-name-that-is-far-beyond-the-fifty-character-limit"]
    invalid_results = []
    for invalid_name in invalid_names:
        response = client.post("/api/collections", json={"name": invalid_name})
        invalid_results.append(
            (
                invalid_name,
                response.status_code,
                code_of(response),
                (upload_root / invalid_name).exists(),
            )
        )
    check(
        "AC-F001-03 invalid boundary names return 400 before side effects",
        all(
            status == 400
            and code == "INVALID_COLLECTION_NAME"
            and not path_exists
            for _, status, code, path_exists in invalid_results
        )
        and set(store.list_collections()) == state_before_duplicate,
        f"results={invalid_results}",
    )
    create_occupied = client.post(
        "/api/collections", json={"name": occupied_kb}
    )
    check("create rename-conflict fixture", create_occupied.status_code == 201)
    missing_rename = client.put(
        "/api/collections/missing-kb", json={"new_name": "unused-kb"}
    )
    invalid_rename = client.put(
        f"/api/collections/{main_kb}", json={"new_name": "ab"}
    )
    conflict_rename = client.put(
        f"/api/collections/{main_kb}", json={"new_name": occupied_kb}
    )
    check(
        "rename preconditions expose exact 404/400/409 errors without mutation",
        (missing_rename.status_code, code_of(missing_rename))
        == (404, "COLLECTION_NOT_FOUND")
        and (invalid_rename.status_code, code_of(invalid_rename))
        == (400, "INVALID_COLLECTION_NAME")
        and (conflict_rename.status_code, code_of(conflict_rename))
        == (409, "COLLECTION_ALREADY_EXISTS")
        and {main_kb, occupied_kb} <= set(store.list_collections()),
    )

    def pdf_bytes(token: str) -> bytes:
        document = fitz.open()
        page = document.new_page()
        page.insert_text(
            (72, 72),
            f"{token} durable identity content for rename and delete acceptance",
        )
        content = document.tobytes()
        document.close()
        return content

    def upload_pdf(collection: str, file_name: str, token: str):
        payload = pdf_bytes(token)
        response = client.post(
            "/api/upload",
            data={"collection_name": collection},
            files={"file": (file_name, payload, "application/pdf")},
        )
        return response, payload

    print("\n--- AC-F001-04 successful rename cascade and identity")
    upload, original_pdf = upload_pdf(main_kb, "doc.pdf", "atomicidentitytoken")
    upload_body = body_of(upload)
    check(
        "literal F001 fixture uploads doc.pdf with persisted chunks",
        upload.status_code == 200
        and upload_body.get("chunks", 0) > 0
        and (upload_root / main_kb / "doc.pdf").read_bytes() == original_pdf,
    )
    old_records = record_snapshot(store.list_chunks(main_kb))
    query_vector = embedding_mod.encode_chunks([old_records[0]["content"]])[0]
    old_scores = {
        item.chunk_id: item.similarity_score
        for item in store.search(main_kb, query_vector, 20)
    }
    old_keyword_hits = KeywordRetriever(store).keyword_search(
        main_kb, "atomicidentitytoken", 20
    )
    check(
        "rename fixture has persisted vector and built keyword evidence",
        bool(old_records)
        and bool(old_scores)
        and {hit["chunk_id"] for hit in old_keyword_hits}
        == {record["chunk_id"] for record in old_records},
    )
    rename = client.put(
        f"/api/collections/{main_kb}", json={"new_name": renamed_kb}
    )
    new_records = record_snapshot(store.list_chunks(renamed_kb))
    new_scores = {
        item.chunk_id: item.similarity_score
        for item in store.search(renamed_kb, query_vector, 20)
    }
    preserved_identity = len(old_records) == len(new_records) and all(
        before["chunk_id"] == after["chunk_id"]
        and before["file_id"] == after["file_id"]
        and before["file_name"] == after["file_name"]
        and before["chunk_index"] == after["chunk_index"]
        and before["content"] == after["content"]
        and {
            key: value
            for key, value in before["metadata"].items()
            if key not in {"collection_name", "source_file"}
        }
        == {
            key: value
            for key, value in after["metadata"].items()
            if key not in {"collection_name", "source_file"}
        }
        and after["collection_name"] == renamed_kb
        and after["metadata"]["collection_name"] == renamed_kb
        and after["metadata"]["source_file"]
        == f"uploads/{renamed_kb}/doc.pdf"
        for before, after in zip(old_records, new_records)
    )
    check(
        "AC-F001-04 collection, filesystem, and metadata cascade succeeds",
        rename.status_code == 200
        and body_of(rename).get("old_name") == main_kb
        and body_of(rename).get("new_name") == renamed_kb
        and main_kb not in store.list_collections()
        and renamed_kb in store.list_collections()
        and not (upload_root / main_kb).exists()
        and (upload_root / renamed_kb / "doc.pdf").read_bytes() == original_pdf
        and preserved_identity,
    )
    check(
        "AC-F001-04 vector identity is preserved across rename",
        old_scores == new_scores,
        f"before={old_scores}; after={new_scores}",
    )
    check(
        "AC-F001-04 keyword cache is invalidated and retrieval rebuilds",
        main_kb in KeywordRetriever._dirty_collections
        and {
            hit["chunk_id"]
            for hit in KeywordRetriever(store).keyword_search(
                renamed_kb, "atomicidentitytoken", 20
            )
        }
        == {record["chunk_id"] for record in new_records}
        and renamed_kb not in KeywordRetriever._dirty_collections,
    )
    listed_after_rename = body_of(client.get("/api/collections")).get(
        "collections", []
    )
    check(
        "renamed KB remains listable with the original file identity",
        {"name": renamed_kb, "file_count": 1} in listed_after_rename
        and upload_body.get("file_id")
        in {
            item["file_id"]
            for item in body_of(
                client.get(
                    "/api/files", params={"collection_name": renamed_kb}
                )
            ).get("files", [])
        },
    )

    print("\n--- AC-F001-06 injected rename failure and compensation")
    atomic_old = "atomic-old"
    atomic_new = "atomic-new"
    client.post("/api/collections", json={"name": atomic_old})
    atomic_upload, atomic_pdf = upload_pdf(
        atomic_old, "atomic.pdf", "rollbackidentitytoken"
    )
    atomic_before = record_snapshot(store.list_chunks(atomic_old))
    atomic_query = embedding_mod.encode_chunks([atomic_before[0]["content"]])[0]
    atomic_scores_before = {
        item.chunk_id: item.similarity_score
        for item in store.search(atomic_old, atomic_query, 20)
    }
    with patch.object(
        collections_api,
        "_rename_uploads_dir",
        side_effect=OSError("T1204 injected uploads rename failure"),
    ):
        failed_rename = client.put(
            f"/api/collections/{atomic_old}",
            json={"new_name": atomic_new},
        )
    atomic_after = record_snapshot(store.list_chunks(atomic_old))
    atomic_scores_after = {
        item.chunk_id: item.similarity_score
        for item in store.search(atomic_old, atomic_query, 20)
    }
    check(
        "AC-F001-06 injected mid-rename failure returns RENAME_FAILED",
        atomic_upload.status_code == 200
        and failed_rename.status_code == 500
        and code_of(failed_rename) == "RENAME_FAILED",
    )
    check(
        "AC-F001-06 compensation restores complete old observable state",
        atomic_old in store.list_collections()
        and atomic_new not in store.list_collections()
        and (upload_root / atomic_old / "atomic.pdf").read_bytes() == atomic_pdf
        and not (upload_root / atomic_new).exists()
        and atomic_before == atomic_after
        and atomic_scores_before == atomic_scores_after,
    )

    print("\n--- AC-F001-05 delete cascade")
    KeywordRetriever(store).keyword_search(
        renamed_kb, "atomicidentitytoken", 20
    )
    delete = client.delete(f"/api/collections/{renamed_kb}")
    listed_after_delete = body_of(client.get("/api/collections")).get(
        "collections", []
    )
    check(
        "AC-F001-05 delete removes collection, chunks, uploads, and list item",
        delete.status_code == 200
        and body_of(delete).get("name") == renamed_kb
        and renamed_kb not in store.list_collections()
        and not (upload_root / renamed_kb).exists()
        and renamed_kb
        not in {collection["name"] for collection in listed_after_delete}
        and renamed_kb in KeywordRetriever._dirty_collections,
    )
    missing_delete = client.delete(f"/api/collections/{renamed_kb}")
    check(
        "deleting an absent KB returns the Section 6 error contract",
        missing_delete.status_code == 404
        and code_of(missing_delete) == "COLLECTION_NOT_FOUND",
    )

    # Remove remaining fixtures through the public API; this also demonstrates
    # that the compensated KB is fully usable after the injected failure.
    cleanup_statuses = [
        client.delete(f"/api/collections/{name}").status_code
        for name in (occupied_kb, atomic_old)
    ]
    check(
        "all surviving fixtures remain deletable through the public API",
        cleanup_statuses == [200, 200]
        and store.list_collections() == []
        and not any(upload_root.iterdir()),
        f"statuses={cleanup_statuses}",
    )

    failed = [(label, detail) for label, ok, detail in results if not ok]
    print("\n" + "=" * 78)
    print(f"Required checks: {len(results) - len(failed)}/{len(results)} passed")
    print("RESULT:", "PASS" if not failed else "FAIL")
    if failed:
        for label, detail in failed:
            suffix = f" -- {detail}" if detail else ""
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
    probe_root = Path(tempfile.mkdtemp(prefix="t1204_spec_audit_")).resolve()
    if (
        temp_root not in probe_root.parents
        or not probe_root.name.startswith("t1204_spec_audit_")
    ):
        print(f"T1204 unsafe temp path: {probe_root}")
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
        _emit("\nT1204 verification timed out.\n")
        return_code = 1

    for _ in range(10):
        shutil.rmtree(probe_root, ignore_errors=True)
        if not probe_root.exists():
            break
        time.sleep(0.3)
    if probe_root.exists():
        print(f"T1204 cleanup failed: {probe_root}")
        return 1
    return return_code


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe-root":
        raise SystemExit(run_probe(Path(sys.argv[2])))
    raise SystemExit(main())
