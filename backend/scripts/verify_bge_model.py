"""Verify the real local BGE model and an isolated semantic Chroma search.

Run from ``backend/``::

    python scripts/verify_bge_model.py

The child process changes into a fresh system temporary directory before
importing application settings, so ``backend/.env`` and repository business
data are not read. Hugging Face and Transformers offline modes are enabled;
this verification makes no DashScope, DeepSeek, or other network/API calls.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


_BACKEND = Path(__file__).resolve().parents[1]
_MODEL_DIR = _BACKEND / "models" / "bge-small-zh-v1.5"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_probe(probe_root: Path) -> int:
    """Load the real model, enforce its contract, and query temporary Chroma."""
    import math
    import os

    model_dir = _MODEL_DIR.resolve()
    probe_root = probe_root.resolve()
    os.chdir(probe_root)
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["CHROMA_PERSIST_DIR"] = str(probe_root / "chroma")
    os.environ["UPLOAD_DIR"] = str(probe_root / "uploads")
    os.environ["EMBED_MODEL"] = str(model_dir)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    sys.path.insert(0, str(_BACKEND))

    import app.services.embedding as embedding_mod
    from app.core.vector_store import ChromaVectorStore

    results: list[tuple[str, bool, str]] = []

    def check(label: str, condition: bool, detail: str = "") -> None:
        ok = bool(condition)
        results.append((label, ok, detail))
        suffix = f" -- {detail}" if detail else ""
        print(f"    [{'PASS' if ok else 'FAIL'}] {label}{suffix}")

    metadata_path = (
        model_dir
        / ".cache"
        / "huggingface"
        / "download"
        / "modules.json.metadata"
    )
    revision = metadata_path.read_text(encoding="utf-8").splitlines()[0]
    tree_path = (
        model_dir
        / ".cache"
        / "huggingface"
        / "trees"
        / f"{revision}.json"
    )
    tree = json.loads(tree_path.read_text(encoding="utf-8"))["files"]
    missing_or_mismatched = []
    for relative_path, expected in tree.items():
        local_path = model_dir / relative_path
        if not local_path.is_file() or local_path.stat().st_size != expected["size"]:
            missing_or_mismatched.append(relative_path)
            continue
        expected_hash = expected.get("lfs_sha256")
        if expected_hash and _sha256(local_path) != expected_hash:
            missing_or_mismatched.append(relative_path)

    required_sentence_transformers_files = {
        "modules.json",
        "1_Pooling/config.json",
        "config.json",
        "config_sentence_transformers.json",
        "sentence_bert_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
        "model.safetensors",
    }
    check(
        "official Hugging Face snapshot is complete and size/hash verified",
        not missing_or_mismatched
        and required_sentence_transformers_files <= set(tree),
        f"revision={revision}; files={len(tree)}; mismatches={missing_or_mismatched}",
    )

    embedding_mod._model = None
    first_model = embedding_mod.get_model()
    second_model = embedding_mod.get_model()
    if hasattr(first_model, "get_embedding_dimension"):
        model_dimension = first_model.get_embedding_dimension()
    else:
        model_dimension = first_model.get_sentence_embedding_dimension()
    check(
        "real model loads from the configured local path and is a lazy singleton",
        first_model is second_model
        and model_dimension == embedding_mod.EMBEDDING_DIMENSION,
        f"path={model_dir}; dimension={model_dimension}",
    )

    texts = [
        "机器学习是人工智能的一个分支，它让计算机通过数据学习规律。",
        "数据库索引可以加快结构化查询速度。",
        "前端组件负责渲染用户界面和处理交互。",
        "烹饪番茄鸡蛋需要先准备新鲜食材。",
    ]
    vectors = embedding_mod.encode_chunks(texts)
    norms = [math.sqrt(sum(value * value for value in vector)) for vector in vectors]
    check(
        "real encode_chunks returns 512-dimensional L2-normalized vectors",
        len(vectors) == len(texts)
        and all(len(vector) == embedding_mod.EMBEDDING_DIMENSION for vector in vectors)
        and all(math.isclose(norm, 1.0, rel_tol=1e-5, abs_tol=1e-5) for norm in norms),
        f"shape={len(vectors)}x{len(vectors[0])}; norms={[round(norm, 6) for norm in norms]}",
    )

    store = ChromaVectorStore()
    collection = "real-bge-semantic-check"
    store.create_collection(collection)
    upload_time = datetime.now(timezone.utc).isoformat()
    file_names = [
        "machine-learning.txt",
        "database.txt",
        "frontend.txt",
        "cooking.txt",
    ]
    metadatas = []
    for index, file_name in enumerate(file_names):
        file_id = str(uuid.uuid4())
        metadatas.append(
            {
                "chunk_id": str(uuid.uuid4()),
                "file_id": file_id,
                "file_name": file_name,
                "collection_name": collection,
                "chunk_index": 0,
                "source_file": f"uploads/{collection}/{file_name}",
                "file_size": len(texts[index].encode("utf-8")),
                "upload_time": upload_time,
                "ingestion_status": "SUCCESS",
            }
        )
    store.add_texts(collection, texts, vectors, metadatas)

    query = "AI 的子领域是什么？"
    query_vector = embedding_mod.encode_chunks([query])[0]
    ranking = store.search(collection, query_vector, top_k=len(texts))
    ranked_files = [item.file_name for item in ranking]
    ranked_scores = [round(item.similarity_score, 6) for item in ranking]
    check(
        "real BGE plus Chroma ranks the controlled Chinese synonym match first",
        len(ranking) == len(texts)
        and ranking[0].file_name == "machine-learning.txt"
        and ranking[0].similarity_score > ranking[1].similarity_score,
        f"query={query!r}; ranking={list(zip(ranked_files, ranked_scores))}",
    )

    failed = [(label, detail) for label, ok, detail in results if not ok]
    print("\n" + "=" * 78)
    print(f"Required checks: {len(results) - len(failed)}/{len(results)} passed")
    print("RESULT:", "PASS" if not failed else "FAIL")
    print(f"MODEL_REVISION: {revision}")
    if failed:
        for label, detail in failed:
            print(f"  - {label}" + (f" -- {detail}" if detail else ""))
    print("=" * 78)
    return 1 if failed else 0


def _emit(output: str) -> None:
    try:
        sys.stdout.write(output)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.write(output.encode(encoding, errors="replace").decode(encoding))
    sys.stdout.flush()


def main() -> int:
    if not _MODEL_DIR.is_dir():
        print(f"Local model directory is missing: {_MODEL_DIR}")
        return 1

    probe_root = Path(tempfile.mkdtemp(prefix="dx_rag_real_bge_")).resolve()
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--probe-root",
                str(probe_root),
            ],
            cwd=_BACKEND,
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
        _emit("\nReal BGE verification timed out.\n")
        return_code = 1

    for _ in range(10):
        shutil.rmtree(probe_root, ignore_errors=True)
        if not probe_root.exists():
            break
        time.sleep(0.3)
    if probe_root.exists():
        print(f"Real BGE cleanup failed: {probe_root}")
        return 1
    return return_code


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe-root":
        raise SystemExit(run_probe(Path(sys.argv[2])))
    raise SystemExit(main())
