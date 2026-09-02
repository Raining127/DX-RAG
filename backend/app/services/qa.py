"""Keyword and vector retrieval services."""

import re
from typing import Callable, Dict, List, Set

from app.core.config import settings
from app.core.vector_store import ChromaVectorStore, ChunkRecord, VectorStore
from app.services.embedding import encode_chunks


_ALPHANUMERIC_PATTERN = re.compile(r"[a-zA-Z0-9]+")
_CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")
_KEYWORD_WEIGHT = 0.3
_VECTOR_WEIGHT = 0.7


def tokenize(text: str) -> List[str]:
    """Tokenize text into unique alphanumeric tokens and Chinese bigrams."""
    tokens = [match.group().lower() for match in _ALPHANUMERIC_PATTERN.finditer(text)]

    for match in _CHINESE_PATTERN.finditer(text):
        segment = match.group()
        tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))

    return list(dict.fromkeys(token for token in tokens if len(token) >= 2))


class KeywordRetriever:
    """Collection-scoped in-memory inverted index and keyword search."""

    _indexes: Dict[str, Dict[str, Set[str]]] = {}
    _chunks: Dict[str, Dict[str, ChunkRecord]] = {}
    _dirty_collections: Set[str] = set()

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    @classmethod
    def invalidate(cls, collection: str) -> None:
        """Mark an existing collection index for full rebuild on next search."""
        if collection in cls._indexes:
            cls._dirty_collections.add(collection)

    def _build_index(self, collection: str) -> None:
        inverted_index: Dict[str, Set[str]] = {}
        chunks: Dict[str, ChunkRecord] = {}

        for chunk in self.vector_store.list_chunks(collection):
            chunks[chunk.chunk_id] = chunk
            for token in tokenize(chunk.content):
                inverted_index.setdefault(token, set()).add(chunk.chunk_id)

        self._indexes[collection] = inverted_index
        self._chunks[collection] = chunks
        self._dirty_collections.discard(collection)

    def keyword_search(
        self, collection: str, query: str, top_k: int
    ) -> List[Dict[str, object]]:
        """Return keyword matches sorted by normalized token coverage."""
        if collection not in self._indexes or collection in self._dirty_collections:
            self._build_index(collection)

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        matched_tokens: Dict[str, int] = {}
        index = self._indexes[collection]
        for token in query_tokens:
            for chunk_id in index.get(token, set()):
                matched_tokens[chunk_id] = matched_tokens.get(chunk_id, 0) + 1

        chunks = self._chunks[collection]
        results = [
            {
                "chunk_id": chunk_id,
                "file_id": chunks[chunk_id].file_id,
                "file_name": chunks[chunk_id].file_name,
                "content": chunks[chunk_id].content,
                "keyword_score": matched_count / len(query_tokens),
            }
            for chunk_id, matched_count in matched_tokens.items()
        ]
        results.sort(key=lambda result: result["keyword_score"], reverse=True)
        return results[:top_k]


class VectorRetriever:
    """Semantic retrieval using query embeddings and VectorStore similarity."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Callable[[List[str]], List[List[float]]] = encode_chunks,
    ) -> None:
        self.vector_store = vector_store
        self.embedder = embedder

    def vector_search(
        self,
        query: str,
        collection: str,
        top_k: int = settings.DEFAULT_TOP_K,
    ) -> List[Dict[str, object]]:
        """Embed a query and return VectorStore similarity as vector_score."""
        query_vector = self.embedder([query])[0]
        search_results = self.vector_store.search(collection, query_vector, top_k * 2)

        return [
            {
                "chunk_id": result.chunk_id,
                "file_id": result.file_id,
                "file_name": result.file_name,
                "content": result.content,
                "vector_score": result.similarity_score,
            }
            for result in search_results[:top_k]
        ]


class HybridRetriever:
    """Merge keyword and vector retrieval results with fixed scoring."""

    def __init__(
        self,
        keyword_retriever: KeywordRetriever,
        vector_retriever: VectorRetriever,
    ) -> None:
        self.keyword_retriever = keyword_retriever
        self.vector_retriever = vector_retriever

    def hybrid_search(
        self,
        query: str,
        collection: str,
        top_k: int = settings.DEFAULT_TOP_K,
    ) -> List[Dict[str, object]]:
        """Fuse both retrieval branches, filter, and return the top results."""
        expanded_top_k = top_k * 2
        keyword_results = self.keyword_retriever.keyword_search(
            collection, query, expanded_top_k
        )
        vector_results = self.vector_retriever.vector_search(
            query, collection, expanded_top_k
        )

        merged: Dict[str, Dict[str, object]] = {}
        for branch_results, score_key in (
            (keyword_results, "keyword_score"),
            (vector_results, "vector_score"),
        ):
            for result in branch_results:
                chunk_id = result["chunk_id"]
                if chunk_id not in merged:
                    merged[chunk_id] = {
                        "chunk_id": chunk_id,
                        "file_id": result.get("file_id"),
                        "file_name": result.get("file_name"),
                        "content": result.get("content"),
                        "metadata": result.get("metadata") or {},
                        "keyword_score": 0.0,
                        "vector_score": 0.0,
                    }

                entry = merged[chunk_id]
                score = float(result.get(score_key) or 0.0)
                entry[score_key] = max(float(entry[score_key]), score)
                if entry["metadata"] == {} and result.get("metadata"):
                    entry["metadata"] = result["metadata"]

                for field in ("file_id", "file_name", "content"):
                    if entry[field] is None and result.get(field) is not None:
                        entry[field] = result[field]

        results = []
        for entry in merged.values():
            final_score = (
                float(entry["keyword_score"]) * _KEYWORD_WEIGHT
                + float(entry["vector_score"]) * _VECTOR_WEIGHT
            )
            results.append(
                {
                    "chunk_id": entry["chunk_id"],
                    "file_id": entry["file_id"],
                    "file_name": entry["file_name"],
                    "content": entry["content"],
                    "final_score": final_score,
                    "metadata": entry["metadata"],
                }
            )

        results.sort(key=lambda result: result["final_score"], reverse=True)
        results = [
            result
            for result in results
            if result["final_score"] >= settings.MIN_RELEVANCE_SCORE
        ]
        return results[:top_k]


def retrieve(
    query: str,
    collection: str,
    top_k: int = settings.DEFAULT_TOP_K,
) -> List[Dict[str, object]]:
    """Run the complete keyword/vector hybrid retrieval pipeline."""
    vector_store = ChromaVectorStore()
    if vector_store.get_chunk_count(collection) == 0:
        return []

    keyword_retriever = KeywordRetriever(vector_store)
    vector_retriever = VectorRetriever(vector_store)
    hybrid_retriever = HybridRetriever(keyword_retriever, vector_retriever)
    return hybrid_retriever.hybrid_search(query, collection, top_k)
