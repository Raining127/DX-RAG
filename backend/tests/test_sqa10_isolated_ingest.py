"""Real ingestion and hybrid retrieval using isolated synthetic data.

Only embeddings are deterministic stand-ins; no model provider, local embedding
model, existing ChromaDB or uploaded document is accessed. A child process is
used so ChromaDB releases its files before the temporary directory is removed.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def synthetic_vectors(texts):
    """Map synthetic topics to distinct 512-dimensional unit vectors."""
    vectors = []
    for text in texts:
        index = 0 if "星光" in text else 1 if "蓝山" in text else 2
        vector = [0.0] * 512
        vector[index] = 1.0
        vectors.append(vector)
    return vectors


def run_fixture(target):
    from unittest.mock import patch

    from app.core.config import settings
    from app.core.vector_store import ChromaVectorStore
    from app.services.ingest import IngestService
    from app.services.qa import (
        HybridRetriever,
        KeywordRetriever,
        QAService,
        VectorRetriever,
        assemble_sources,
    )

    target = Path(target).resolve()
    assert Path(settings.CHROMA_PERSIST_DIR).resolve() == target / "chroma"
    assert Path(settings.UPLOAD_DIR).resolve() == target / "uploads"
    target.joinpath("uploads").mkdir()
    store = ChromaVectorStore()
    collection = "sqa10-fixture"
    store.create_collection(collection)
    facts = {
        "starlight.md": "星光计划：火星苹果的运输时间为三天。测试资料，仅用于验收。",
        "mountain.md": "蓝山计划：海盐样品的保存温度为四度。测试资料，仅用于验收。",
    }
    with patch("app.services.embedding.encode_chunks", side_effect=synthetic_vectors):
        inserted = {}
        for name, contents in facts.items():
            file_path = target / "uploads" / name
            file_path.write_text(contents, encoding="utf-8")
            result = IngestService.process(file_path, name, collection)
            assert result["status"] == "SUCCESS"
            assert result["chunks_count"] >= 1
            inserted[name] = result["file_id"]

    assert len(store.get_files(collection)) == 2
    assert store.get_chunk_count(collection) >= 2
    keyword = KeywordRetriever(store)
    vector = VectorRetriever(store, embedder=synthetic_vectors)
    hybrid = HybridRetriever(keyword, vector)
    service = QAService(vector_store=store, hybrid_retriever=hybrid)
    question = "星光计划火星苹果的运输时间是多少？"
    keyword_hits = keyword.keyword_search(collection, question, 5)
    vector_hits = vector.vector_search(question, collection, 5)
    assert keyword_hits and keyword_hits[0]["file_name"] == "starlight.md"
    assert vector_hits and vector_hits[0]["file_name"] == "starlight.md"

    results, context, history = service.prepare(question, collection, 5, [])
    sources = assemble_sources(results)
    assert results and sources
    assert sources[0]["file_name"] == "starlight.md"
    assert sources[0]["file_id"] == inserted["starlight.md"]
    assert sources[0]["chunk_id"] in {item.chunk_id for item in store.list_chunks(collection)}
    assert "火星苹果的运输时间为三天" in context
    assert history == ""

    no_match, empty_context, _ = service.prepare("完全无关的银河问题", collection, 5, [])
    assert no_match == [] and empty_context == "" and assemble_sources(no_match) == []
    print("PASS real IngestService and isolated Chroma for two synthetic documents")
    print("PASS real keyword/vector/hybrid retrieval and QAService context/sources")
    print("PASS no-match produces empty context and sources")
    print("LIMIT deterministic 512-dimensional embedding stand-in; no provider call")


class IsolatedIngestAndRetrievalTests(unittest.TestCase):
    def test_real_ingestion_and_retrieval_with_synthetic_vectors(self):
        backend = Path(__file__).resolve().parents[1]
        temporary_root = Path(tempfile.gettempdir()).resolve()
        with tempfile.TemporaryDirectory(prefix="dxrag-sqa10-", dir=str(temporary_root)) as name:
            target = Path(name).resolve()
            if target.parent != temporary_root or not target.name.startswith("dxrag-sqa10-"):
                raise RuntimeError("temporary target outside verified root")
            env = os.environ.copy()
            env.pop("DEEPSEEK_API_KEY", None)
            env.pop("DASHSCOPE_API_KEY", None)
            env.update({
                "PYTHONPATH": str(backend),
                "CHROMA_PERSIST_DIR": str(target / "chroma"),
                "UPLOAD_DIR": str(target / "uploads"),
                "ANONYMIZED_TELEMETRY": "False",
                "HF_HUB_OFFLINE": "1",
            })
            child = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--fixture", str(target)],
                cwd=str(target), env=env, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(child.returncode, 0, child.stderr)
            self.assertIn("PASS real keyword/vector/hybrid retrieval", child.stdout)
            print(child.stdout.strip())


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--fixture":
        run_fixture(sys.argv[2])
    else:
        unittest.main()
