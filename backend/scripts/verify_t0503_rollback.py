"""T0503 — Upload ROLLBACK behavior verification (SPEC F002 Upload Failure Atomicity).

Run from the repository root::

    python backend/scripts/verify_t0503_rollback.py

Exit code 0 = every required check passed; 1 = at least one required check failed.

What this verifies
------------------
SPEC F002 "Upload Failure Atomicity" — the FAILED row and its four mandatory
observable behaviors (SPEC Section 12.2 AC-F002-09):

  1. no residual raw file in ``uploads/``
  2. no residual chunk/vector/metadata for that ``file_id`` in ChromaDB
  3. the keyword index does not contain the file
  4. a same-name re-upload is not blocked by the previous failure

plus AC-F002-08 (all pages fail → 422 ``FILE_PARSE_ERROR``) and AC-F002-10
(re-upload after SUCCESS_WITH_WARNINGS → 409 ``FILE_ALREADY_EXISTS``).

Postconditions are asserted through public interfaces only — ``get_files()``,
``get_chunk_count()``, ``get_chunks_by_file()`` and the filesystem.  SPEC
declares the rollback mechanism an implementation detail, so no private
attribute is inspected.  Behavior 2 is asserted as "chunk count unchanged from
baseline AND file absent from ``get_files()``": any surviving chunk carrying
the failed ``file_id`` would raise the count and surface the file.  Behavior 3
is asserted through the same observation — the Phase 6 index is built from
``VectorStore.list_chunks``, so a file absent from the store cannot enter it.

Isolation
---------
``UPLOAD_DIR`` and ``CHROMA_PERSIST_DIR`` are redirected to a throwaway temp
directory before the application is imported, and every scenario runs in its
own collection.  The repository's ``chroma_db/`` and ``uploads/`` are never
touched; the temp tree is removed on exit.

The whole matrix runs in a CHILD PROCESS.  ChromaDB's Rust backend holds open
SQLite/segment file handles for the lifetime of the process — on Windows an
in-process cache clear does not release them, so the parent deletes the temp
tree only after the child has exited and the OS has closed its handles.

Declared substitutions (T0503 Pre-flight decisions D-1/D-2)
-----------------------------------------------------------
* AC-F002-08 is driven by a whitespace-only ``.txt`` rather than SPEC's literal
  "PDF with no effective text on any page".  Both reach the identical FAILED
  branch (cleaned text empty → ``IngestService._fail``).  PyMuPDF is not
  installed in this environment, so the literal PDF fixture is deferred.
* Embeddings are stubbed — ``sentence-transformers`` is not installed, and F007
  is not under test here.  Only the persistence side effects matter.
* SUCCESS_WITH_WARNINGS is produced by injecting an OCR warning through the
  F004 warning channel, not by a real Qwen-VL failure (``dashscope`` absent).

Guards (decision D-4)
---------------------
V11/V12 probe states that are unreachable in the current code but are
documented in the T0503 Pre-flight as findings F-3/F-4.  They are reported,
never enforced, and never repaired here — their owners are T0602 and the
global handler.

Phase 5 Gate remediation (F-1/F-2, 2026-08-25)
----------------------------------------------
V9 and V10 were GUARDs at first delivery (T0104 batching was not yet
implemented).  After the remediation in ``ChromaVectorStore.add_texts``
(safe batching + file_id-scoped compensation) they are upgraded to CHECKs:
V9 verifies that a legal >5461-chunk upload succeeds and persists fully;
V10 injects a batch-2 failure after batch-1 commit and verifies the
file-level all-or-nothing cleanup.
"""

import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))


def run_probe(tmp_root: Path) -> int:
    """Child process body: run the whole matrix against a throwaway root.

    The environment redirect MUST happen before the first import of
    ``app.core.config`` (its Settings singleton reads env vars at import
    time), so every app import lives inside this function.
    """
    import os

    os.environ["UPLOAD_DIR"] = str(tmp_root / "uploads")
    os.environ["CHROMA_PERSIST_DIR"] = str(tmp_root / "chroma")

    from fastapi.testclient import TestClient

    import app.services.embedding as embedding_mod
    import app.services.ingest as ingest_mod
    from app.api import upload as upload_mod
    from app.core.config import settings
    from app.core.errors import AppError
    from app.core.vector_store import ChromaVectorStore
    from app.main import app
    from app.services.ingest import IngestService

    store = ChromaVectorStore()
    # raise_server_exceptions=False so the SPEC 9.4 global handler's 500
    # response is observed as a response instead of propagating into this
    # script.
    client = TestClient(app, raise_server_exceptions=False)

    # (kind, label, ok, detail) — kind "GUARD" is informational and never
    # fails the run.
    results: list = []

    # SPEC F007 vector width; one shared list is reused for every chunk
    # since T0503 never queries — only persistence side effects are under
    # test.
    vector = [0.1] * 384

    def fake_encode(chunks):
        return [vector] * len(chunks)

    @contextmanager
    def patched(target, attr, value):
        """Temporarily replace an attribute on a module or class."""
        is_class = isinstance(target, type)
        missing = object()
        original = target.__dict__.get(attr, missing) if is_class else getattr(target, attr)
        setattr(target, attr, value)
        try:
            yield
        finally:
            if is_class and original is missing:
                delattr(target, attr)
            else:
                setattr(target, attr, original)

    def fake_embeddings():
        """Stub the embedding step (declared substitution, see docstring)."""
        return patched(embedding_mod, "encode_chunks", fake_encode)

    # -----------------------------------------------------------------------
    # Observation & assertion helpers — public interfaces only
    # -----------------------------------------------------------------------

    def observe(collection: str) -> dict:
        """Observable state of one knowledge base."""
        raw_dir = Path(settings.UPLOAD_DIR) / collection
        return {
            "raw": sorted(p.name for p in raw_dir.iterdir()) if raw_dir.is_dir() else [],
            "count": store.get_chunk_count(collection),
            "files": sorted(f["file_name"] for f in store.get_files(collection)),
        }

    def others(exclude: str) -> dict:
        """Chunk counts of every collection except the one under test."""
        return {
            name: store.get_chunk_count(name)
            for name in store.list_collections()
            if name != exclude
        }

    def record(kind: str, label: str, ok: bool, detail: str = "") -> None:
        results.append((kind, label, ok, detail))
        mark = "GUARD" if kind == "GUARD" else ("PASS" if ok else "FAIL")
        print(f"    [{mark}] {label}" + (f" — {detail}" if detail else ""))

    def check(label, ok, detail=""):
        record("CHECK", label, ok, detail)

    def ac(label, ok, detail=""):
        record("AC", label, ok, detail)

    def guard(label, detail=""):
        record("GUARD", label, True, detail)

    def case(title: str, collection: str) -> dict:
        """Start a scenario: fresh collection, captured baseline."""
        print(f"\n--- {title}  [kb={collection}]")
        if collection not in store.list_collections():
            store.create_collection(collection)
        return {"state": observe(collection), "others": others(collection)}

    def post(collection: str, name: str, content: bytes, content_type="text/plain"):
        return client.post(
            "/api/upload",
            files={"file": (name, content, content_type)},
            data={"collection_name": collection},
        )

    def code_of(response) -> str:
        try:
            return response.json().get("error", {}).get("code")
        except Exception:
            return None

    def describe(response) -> str:
        body = response.json() if response.content else {}
        if isinstance(body, dict) and "error" in body:
            return f"HTTP {response.status_code} {body['error'].get('code')}"
        if isinstance(body, dict) and "status" in body:
            return f"HTTP {response.status_code} {body['status']}"
        return f"HTTP {response.status_code}"

    def assert_rolled_back(tag, collection, name, base) -> dict:
        """The four mandatory FAILED observable behaviors (items 1-3 here)."""
        state = observe(collection)
        check(f"{tag}: no raw file residue", name not in state["raw"], f"raw={state['raw']}")
        check(
            f"{tag}: no residual chunk/vector/metadata",
            state["count"] == base["state"]["count"],
            f"chunk_count {base['state']['count']} -> {state['count']}",
        )
        check(
            f"{tag}: file not exposed by get_files()",
            name not in state["files"],
            f"get_files={state['files']}",
        )
        check(
            f"{tag}: no other knowledge base affected",
            others(collection) == base["others"],
            "unrelated collection counts unchanged",
        )
        return state

    # -----------------------------------------------------------------------
    # Scenarios
    # -----------------------------------------------------------------------

    print("=" * 78)
    print("T0503 — Upload ROLLBACK Behavior Verification")
    print("=" * 78)
    print(f"UPLOAD_DIR          : {settings.UPLOAD_DIR}")
    print(f"CHROMA_PERSIST_DIR  : {settings.CHROMA_PERSIST_DIR}")
    repo = str(_BACKEND)
    assert repo not in settings.UPLOAD_DIR, "refusing to run: UPLOAD_DIR inside the repo"
    assert repo not in settings.CHROMA_PERSIST_DIR, "refusing to run: CHROMA dir inside the repo"

    # -- V1/V2: rejection before any filesystem write -----------------------
    kb = "kb-validate"
    case("V1/V2 pre-write rejection is side-effect free", kb)
    rejections = [
        ("../evil.txt", b"payload", 400, "INVALID_FILE_NAME"),
        ("evil.exe", b"payload", 400, "UNSUPPORTED_FILE_TYPE"),
        ("empty.txt", b"", 400, "EMPTY_FILE"),
        ("huge.txt", b"x" * (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1), 413, "FILE_TOO_LARGE"),
    ]
    for name, content, status, expected in rejections:
        response = post(kb, name, content)
        check(
            f"{name} -> {status} {expected}",
            response.status_code == status and code_of(response) == expected,
            describe(response),
        )
    response = post("no-such-kb", "doc.txt", b"content")
    check(
        "unknown collection -> 404 COLLECTION_NOT_FOUND",
        response.status_code == 404 and code_of(response) == "COLLECTION_NOT_FOUND",
        describe(response),
    )
    state = observe(kb)
    check(
        "no validation rejection created any file",
        state["raw"] == [] and state["count"] == 0 and state["files"] == [],
        f"state={state}",
    )

    print("\n--- V15 request-validation rejection (missing file part)")
    response = client.post("/api/upload", data={"collection_name": kb})
    check(
        "missing file part -> 422 with no persistence side effect",
        response.status_code == 422 and observe(kb)["count"] == 0,
        describe(response),
    )
    guard(
        "F-4: request-validation 422 envelope is FastAPI's, not SPEC 6.7",
        f"body keys={sorted(response.json().keys())} (owner: global handler, not T0503)",
    )

    # -- V3/V4/V5: the FAILED contract and re-upload invariant ---------------
    kb = "kb-failed"
    base = case("V3 empty effective content -> FAILED (AC-F002-08/09)", kb)
    response = post(kb, "blank.txt", "   \n\t\n   \n".encode("utf-8"))
    ac(
        "AC-F002-08: all-pages-fail equivalent -> 422 FILE_PARSE_ERROR",
        response.status_code == 422 and code_of(response) == "FILE_PARSE_ERROR",
        describe(response) + "  [D-2: whitespace-only .txt substitution]",
    )
    assert_rolled_back("AC-F002-09", kb, "blank.txt", base)

    print("\n--- V4 immediate same-name retry after FAILED")
    with fake_embeddings():
        response = post(kb, "blank.txt", "retry content after rollback".encode("utf-8"))
    body = response.json()
    ac(
        "AC-F002-09 item 4: retry not blocked by previous FAILED",
        response.status_code == 200 and body.get("status") == "SUCCESS",
        describe(response),
    )
    check("retry commits chunks", body.get("chunks", 0) > 0, f"chunks={body.get('chunks')}")
    state = observe(kb)
    check(
        "retry persists raw file and chunks",
        "blank.txt" in state["raw"] and "blank.txt" in state["files"],
        f"state={state}",
    )

    print("\n--- V5 duplicate after a committed success")
    with fake_embeddings():
        response = post(kb, "blank.txt", b"a third upload")
    check(
        "duplicate name -> 409 FILE_ALREADY_EXISTS",
        response.status_code == 409 and code_of(response) == "FILE_ALREADY_EXISTS",
        describe(response),
    )

    # -- V6/V7/V8: exception paths must roll back like FAILED ----------------
    kb = "kb-parse"
    base = case("V6 parse error (ENCRYPTED_PDF) rolls back", kb)

    def _raise_encrypted(file_path):
        raise AppError("ENCRYPTED_PDF")

    with patched(IngestService, "_parse", _raise_encrypted):
        response = post(kb, "locked.pdf", b"%PDF-1.4 fake")
    check(
        "parse error -> 422 ENCRYPTED_PDF",
        response.status_code == 422 and code_of(response) == "ENCRYPTED_PDF",
        describe(response),
    )
    assert_rolled_back("V6", kb, "locked.pdf", base)

    kb = "kb-embed"
    base = case("V7 embedding failure rolls back", kb)

    def _raise_embedding(chunks):
        raise AppError("EMBEDDING_MODEL_ERROR")

    with patched(embedding_mod, "encode_chunks", _raise_embedding):
        response = post(kb, "embfail.txt", b"content that reaches the embedding step")
    check(
        "embedding failure -> 500 EMBEDDING_MODEL_ERROR",
        response.status_code == 500 and code_of(response) == "EMBEDDING_MODEL_ERROR",
        describe(response),
    )
    assert_rolled_back("V7", kb, "embfail.txt", base)

    kb = "kb-chroma"
    base = case("V8 Chroma persistence failure rolls back", kb)

    def _raise_add(self, **kwargs):
        raise RuntimeError("simulated ChromaDB outage")

    with fake_embeddings(), patched(ChromaVectorStore, "add_texts", _raise_add):
        response = post(kb, "chromafail.txt", b"content that reaches persistence")
    check(
        "persistence failure -> 500 INTERNAL_ERROR",
        response.status_code == 500 and code_of(response) == "INTERNAL_ERROR",
        describe(response),
    )
    assert_rolled_back("V8", kb, "chromafail.txt", base)

    # -- V9: legal file exceeding Chroma's max batch — batching (F-1) --------
    kb = "kb-batch"
    case("V9 legal file above Chroma max batch size (F-1 remediated)", kb)
    paragraph = "这是一段用于批量测试的中文文本内容，需要足够长以便切分器产生大量分块。" * 12 + "\n\n"
    big = (paragraph * 6000).encode("utf-8")
    size_mb = len(big) / 1024 / 1024
    print(f"    fixture: {size_mb:.2f} MB (limit {settings.MAX_UPLOAD_SIZE_MB} MB) — legal upload")
    with fake_embeddings():
        response = post(kb, "big.txt", big)
    body = response.json()
    check(
        "F-1: legal >5461-chunk upload -> 200 SUCCESS",
        response.status_code == 200
        and body.get("status") == "SUCCESS"
        and body.get("chunks", 0) > 5461,
        describe(response) + f" (chunks={body.get('chunks')})",
    )
    state = observe(kb)
    check(
        "F-1: all expected chunks persisted",
        state["count"] == body.get("chunks"),
        f"chunk_count={state['count']} vs chunks={body.get('chunks')}",
    )
    check(
        "F-1: raw file persists on success",
        "big.txt" in state["raw"],
        f"raw={state['raw']}",
    )
    files = {f["file_name"]: f["chunk_count"] for f in store.get_files(kb)}
    check(
        "F-1: get_files exposes the uploaded file with full chunk count",
        files.get("big.txt") == body.get("chunks"),
        f"get_files={files}",
    )
    with fake_embeddings():
        response = post(kb, "big.txt", b"small second attempt")
    check(
        "F-1: same-name re-upload after success -> 409",
        response.status_code == 409 and code_of(response) == "FILE_ALREADY_EXISTS",
        describe(response),
    )

    # -- V10: batch failure after commit — compensation (F-2) -----------------
    kb = "kb-partial"
    base = case("V10 batch-2 failure after batch-1 commit (F-2 remediated)", kb)
    with fake_embeddings():
        seed = post(kb, "good.txt", "# Title\n\nUnrelated pre-existing content.".encode("utf-8"))
    check(
        "V10: pre-seeded unrelated file committed",
        seed.status_code == 200,
        describe(seed),
    )
    base = {"state": observe(kb), "others": others(kb)}

    # Inject the failure INSIDE the real batching loop: the first
    # ChromaDB add() call (batch 1) commits for real, the second raises
    # — exercising VectorStore.add_texts' own compensation path.
    import chromadb.api.models.Collection as chroma_collection_mod

    original_col_add = chroma_collection_mod.Collection.__dict__["add"]
    add_calls = {"count": 0}

    def counting_add(self, **kwargs):
        add_calls["count"] += 1
        if add_calls["count"] > 1:
            raise RuntimeError("simulated batch 2 failure after batch 1 committed")
        return original_col_add(self, **kwargs)

    # Reuse V9's `big` fixture — >5461 chunks so persistence spans two batches.
    with fake_embeddings(), patched(chroma_collection_mod.Collection, "add", counting_add):
        response = post(kb, "partial.txt", big)
    check(
        "F-2: injected batch-2 failure -> 500 INTERNAL_ERROR",
        response.status_code == 500 and code_of(response) == "INTERNAL_ERROR",
        describe(response),
    )
    assert_rolled_back("F-2", kb, "partial.txt", base)
    state = observe(kb)
    check(
        "F-2: unrelated pre-existing file untouched",
        "good.txt" in state["raw"]
        and "good.txt" in state["files"]
        and state["count"] > 0,
        f"state={state}",
    )
    with fake_embeddings():
        retry = post(kb, "partial.txt", b"small retry after compensated failure")
    check(
        "F-2: same-name retry succeeds after compensation",
        retry.status_code == 200,
        describe(retry),
    )

    # -- V11/V12: guards for known findings (never enforced, never fixed)

    kb = "kb-kwidx"
    base = case("V11 GUARD keyword invalidation failure after commit (F-3)", kb)

    def _raise_invalidate(collection_name):
        raise RuntimeError("simulated keyword index outage")

    with fake_embeddings(), patched(upload_mod, "invalidate_keyword_index", _raise_invalidate):
        response = post(kb, "kwfail.txt", b"content whose ingestion succeeds")
    state = observe(kb)
    guard(
        "F-3: post-commit invalidation failure",
        f"{describe(response)}; raw={state['raw']}; chunk_count "
        f"{base['state']['count']} -> {state['count']}; get_files={state['files']}",
    )
    check(
        "V11: raw file and chunks stay mutually consistent",
        ("kwfail.txt" in state["raw"]) == ("kwfail.txt" in state["files"]),
        "no split raw/Chroma state",
    )
    guard(
        "F-3 note: seam is a no-op today and cannot raise unaided",
        "reachable only once T0602 installs a real index",
    )

    kb = "kb-cleanupfail"
    base = case("V12 GUARD cleanup failure must not mask the original error", kb)

    def _raise_unlink(self, missing_ok=False):
        raise OSError("simulated undeletable raw file")

    with patched(embedding_mod, "encode_chunks", _raise_embedding), patched(
        Path, "unlink", _raise_unlink
    ):
        response = post(kb, "stuck.txt", b"content that fails after the raw save")
    check(
        "V12: original error survives a failed cleanup",
        response.status_code == 500 and code_of(response) == "EMBEDDING_MODEL_ERROR",
        describe(response),
    )
    state = observe(kb)
    check(
        "V12: no chunks persisted despite the residual raw file",
        state["count"] == base["state"]["count"] and state["files"] == [],
        f"raw={state['raw']} (residue expected — unlink was forced to fail)",
    )

    # -- V13/V14: committed-success control cases ---------------------------
    kb = "kb-success"
    case("V13 clean SUCCESS control", kb)
    with fake_embeddings():
        response = post(kb, "good.txt", "# Title\n\nSome real content to chunk.".encode("utf-8"))
    body = response.json()
    check(
        "clean upload -> 200 SUCCESS with empty warnings",
        response.status_code == 200
        and body.get("status") == "SUCCESS"
        and body.get("warnings") == [],
        describe(response),
    )
    state = observe(kb)
    check(
        "SUCCESS commits raw file and chunks",
        "good.txt" in state["raw"] and "good.txt" in state["files"] and state["count"] > 0,
        f"state={state}",
    )

    kb = "kb-warn"
    case("V14 SUCCESS_WITH_WARNINGS is a commit, not a rollback (AC-F002-10)", kb)

    def _parse_with_warning(file_path):
        # Mirrors a real PDF whose page 3 OCR failed: the F004 warning channel
        # is populated during parse and the remaining pages still yield text.
        ingest_mod._record_ocr_warning(3, "OCR_PAGE_FAILED")
        return file_path.read_text(encoding="utf-8")

    with fake_embeddings(), patched(IngestService, "_parse", _parse_with_warning):
        response = post(kb, "scanned.pdf", "page 1 text\n\npage 2 text".encode("utf-8"))
    body = response.json()
    check(
        "partial OCR failure -> 200 SUCCESS_WITH_WARNINGS",
        response.status_code == 200 and body.get("status") == "SUCCESS_WITH_WARNINGS",
        describe(response),
    )
    check(
        "warnings carry {page_number, error_code}",
        body.get("warnings") == [{"page_number": 3, "error_code": "OCR_PAGE_FAILED"}],
        f"warnings={body.get('warnings')}",
    )
    state = observe(kb)
    check(
        "SUCCESS_WITH_WARNINGS commits raw file and chunks",
        "scanned.pdf" in state["raw"] and "scanned.pdf" in state["files"] and state["count"] > 0,
        f"chunks={body.get('chunks')}",
    )
    with fake_embeddings():
        response = post(kb, "scanned.pdf", b"second attempt")
    ac(
        "AC-F002-10: re-upload after SUCCESS_WITH_WARNINGS -> 409",
        response.status_code == 409 and code_of(response) == "FILE_ALREADY_EXISTS",
        describe(response),
    )

    # -- Summary -------------------------------------------------------------
    required = [r for r in results if r[0] != "GUARD"]
    failed = [r for r in required if not r[2]]
    guards = [r for r in results if r[0] == "GUARD"]

    print("\n" + "=" * 78)
    print(f"Required checks : {len(required) - len(failed)}/{len(required)} passed")
    print(f"Guards recorded : {len(guards)} (informational — decision D-4)")
    print("=" * 78)
    for _, label, _, detail in guards:
        print(f"  GUARD  {label}\n         {detail}")
    if failed:
        print("\nFAILED:")
        for _, label, _, detail in failed:
            print(f"  - {label} — {detail}")
    print("\nRESULT:", "PASS" if not failed else "FAIL")
    return 1 if failed else 0


def main() -> int:
    """Parent process: run the probe in a child and clean up after it.

    ChromaDB's Rust backend keeps its SQLite/segment file handles open for
    the whole process lifetime; on Windows nothing in-process releases
    them.  Running the matrix in a child means the OS closes every handle
    when the child exits, so the parent can remove the probe tree.
    """
    probe_root = Path(tempfile.mkdtemp(prefix="t0503_"))
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--probe-root", str(probe_root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )

    def emit(text: str) -> None:
        """Write child output to the parent's console without crashing.

        Windows console codecs (e.g. GBK) can reject the replacement
        characters produced by decoding the child's UTF-8 output with
        errors="replace" — re-encode lossily so a display quirk can never
        abort the run or skip cleanup.
        """
        try:
            sys.stdout.write(text)
        except UnicodeEncodeError:
            sys.stdout.write(text.encode(sys.stdout.encoding or "utf-8", errors="replace")
                            .decode(sys.stdout.encoding or "utf-8", errors="replace"))
        sys.stdout.flush()

    emit(completed.stdout)
    if completed.stderr.strip():
        emit("--- child stderr (filtered) ---\n")
        for line in completed.stderr.splitlines():
            # ChromaDB model-download progress spam drowns everything else.
            if any(tag in line for tag in ("it/s", "onnx.tar.gz", "s?iB/s")):
                continue
            emit(line + "\n")
    for attempt in range(10):
        shutil.rmtree(probe_root, ignore_errors=True)
        if not probe_root.exists():
            break
        time.sleep(0.3)
    if probe_root.exists():
        print(f"\nWARNING: probe temp dir not removed (inspect {probe_root})")
        return 1
    return completed.returncode


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe-root":
        sys.exit(run_probe(Path(sys.argv[2])))
    sys.exit(main())
