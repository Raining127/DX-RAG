"""Query tokenization for keyword retrieval."""

import re
from typing import Dict, List, Set

from app.core.vector_store import ChunkRecord, VectorStore


_ALPHANUMERIC_PATTERN = re.compile(r"[a-zA-Z0-9]+")
_CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")


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
