"""Read-only adapter through existing public V1 interfaces; imports are lazy."""

import hashlib

from evaluation.dataset import require, validate_dataset


def build_search(data):
    inventory = validate_dataset(data)
    require(data["purpose"] == "benchmark", "V1 adapter requires reviewed benchmark data")
    from app.core.config import settings
    from app.core.vector_store import ChromaVectorStore
    from app.services.qa import HybridRetriever, KeywordRetriever, VectorRetriever

    require(settings.DEFAULT_TOP_K == 5 and settings.MIN_RELEVANCE_SCORE == 0.30,
            "V1 baseline settings mismatch")
    store = ChromaVectorStore()
    chunks = store.list_chunks(data["collection"])
    require({c.chunk_id for c in chunks} == set(inventory), "live snapshot chunk IDs mismatch")
    for chunk in chunks:
        frozen = inventory[chunk.chunk_id]
        for field in ("file_id", "file_name", "chunk_index"):
            require(getattr(chunk, field) == frozen[field], f"live snapshot {field} mismatch")
        require(hashlib.sha256(chunk.content.encode("utf-8")).hexdigest() == frozen["content_sha256"],
                "live snapshot content mismatch")
    search = HybridRetriever(KeywordRetriever(store), VectorRetriever(store)).hybrid_search
    config = {"embed_model": settings.EMBED_MODEL, "persist_dir": settings.CHROMA_PERSIST_DIR,
              "min_relevance_score": settings.MIN_RELEVANCE_SCORE,
              "production_default_top_k": settings.DEFAULT_TOP_K}
    return search, config
