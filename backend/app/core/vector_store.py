"""VectorStore public interface — abstract base class.

SPEC F008 Design Constraints:
  1. One Knowledge Base = one independent ChromaDB Collection
  2. ALL ChromaDB operations MUST go through this public interface
  3. External code MUST NOT access ``_collection`` or any ChromaDB private attribute
  4. Abstraction preserves interface consistency for future Milvus extension

Distance → Similarity Semantic Boundary (F008):
  - ChromaDB raw distance MUST NOT be exposed outside VectorStore
  - ``search()`` converts distance → similarity_score::

      similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)

  - Callers receive similarity_score (higher = more relevant), range [0, 1]
  - External code uses similarity_score as vector_score directly — no
    re-normalization needed
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import chromadb
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.errors import AppError


# ---------------------------------------------------------------------------
# Internal data models used by VectorStore method signatures
# ---------------------------------------------------------------------------


class ChunkRecord(BaseModel):
    """A single chunk record (SPEC Section 7.4).

    Returned by ``list_chunks()`` and ``get_chunks_by_file()``.
    ``embedding`` is NOT included — callers must not receive raw vectors
    through this public interface.
    """

    chunk_id: str = Field(description="UUID, immutable globally unique identifier")
    file_id: str = Field(description="UUID, FK → FileRecord.file_id")
    file_name: str = Field(description="Display-only source filename")
    collection_name: str = Field(description="Parent collection / knowledge base name")
    chunk_index: int = Field(
        description="0-based sequence number within the file (not an ID)"
    )
    content: str = Field(description="Chunk text (≤ max_chunk_size)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full ChromaDB metadata dict (chunk_id, file_id, file_name, "
        "collection_name, chunk_index, source_file, file_size, upload_time, "
        "ingestion_status)",
    )


class VectorSearchResult(BaseModel):
    """A single vector-search hit returned by ``search()``.

    Uses ``similarity_score`` — the result of Distance → Similarity conversion
    (F008 semantic boundary).  Higher = more relevant, range [0, 1].
    """

    chunk_id: str = Field(description="UUID of the chunk")
    file_id: str = Field(description="UUID of the source file")
    file_name: str = Field(description="Display-only source filename")
    content: str = Field(description="Chunk text")
    similarity_score: float = Field(
        description="Converted similarity score [0, 1]; larger = more relevant"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Full ChromaDB metadata dict"
    )


# ---------------------------------------------------------------------------
# VectorStore ABC (SPEC F008 Public Interface table — 11 methods)
# ---------------------------------------------------------------------------


class VectorStore(ABC):
    """Abstract base class for vector storage backends.

    Implementations MUST:
      - Convert ChromaDB raw distance → similarity_score inside ``search()``
      - Never expose ``_collection`` or raw distance to callers
    """

    # --- Collection Lifecycle ---

    @abstractmethod
    def create_collection(self, name: str) -> None:
        """Create a new ChromaDB collection.

        Args:
            name: Collection name (knowledge base name).
        """

    @abstractmethod
    def delete_collection(self, name: str) -> None:
        """Delete a ChromaDB collection and all its data.

        Args:
            name: Collection name to delete.
        """

    @abstractmethod
    def rename_collection(self, old_name: str, new_name: str) -> None:
        """Rename a ChromaDB collection.

        Args:
            old_name: Current collection name.
            new_name: New collection name.
        """

    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all existing ChromaDB collection names.

        Returns:
            List of collection names.
        """

    # --- Data Operations ---

    @abstractmethod
    def add_texts(
        self,
        collection: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> List[str]:
        """Add documents (text + embedding + metadata) to a collection.

        Args:
            collection: Target collection name.
            chunks: List of chunk text strings.
            embeddings: Corresponding embedding vectors (384-dim).
            metadatas: Corresponding metadata dicts (SPEC F008 Metadata Schema).

        Returns:
            List of chunk_ids (UUID strings) in insertion order.
        """

    @abstractmethod
    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int,
    ) -> List[VectorSearchResult]:
        """Vector similarity search — returns similarity_score, NOT raw distance.

        Implements the F008 Distance → Similarity semantic boundary:
        ``similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)``

        Args:
            collection: Collection name to search.
            query_vector: Query embedding vector (384-dim).
            top_k: Maximum number of results to return.

        Returns:
            Results sorted by similarity_score descending.
        """

    @abstractmethod
    def delete_by_file(self, collection: str, file_id: str) -> int:
        """Delete all chunks belonging to a file.

        Args:
            collection: Collection name.
            file_id: UUID of the file whose chunks should be deleted.

        Returns:
            Number of chunks deleted.
        """

    @abstractmethod
    def get_files(self, collection: str) -> List[Dict[str, Any]]:
        """Get file list by aggregating chunk metadata (group/deduplicate by file_id).

        Args:
            collection: Collection name.

        Returns:
            List of dicts with keys: file_id, file_name, size, upload_time,
            chunk_count, status.  No external metadata database required.
        """

    # --- Chunk Metadata Access ---

    @abstractmethod
    def list_chunks(self, collection: str) -> List[ChunkRecord]:
        """List all chunks in a collection (without embedding vectors).

        Used by Keyword Retriever for building the inverted index.

        Args:
            collection: Collection name.

        Returns:
            All ChunkRecords in the collection.
        """

    @abstractmethod
    def get_chunk_count(self, collection: str) -> int:
        """Get the total number of chunks in a collection.

        Args:
            collection: Collection name.

        Returns:
            Total chunk count.
        """

    @abstractmethod
    def get_chunks_by_file(self, collection: str, file_id: str) -> List[ChunkRecord]:
        """Get all chunks for a specific file, ordered by chunk_index ASC.

        Args:
            collection: Collection name.
            file_id: UUID of the file.

        Returns:
            ChunkRecords sorted by chunk_index ascending.
        """


# ---------------------------------------------------------------------------
# ChromaVectorStore — ChromaDB implementation
# ---------------------------------------------------------------------------


class ChromaVectorStore(VectorStore):
    """ChromaDB-backed VectorStore implementation.

    SPEC F008 ChromaDB Configuration:
      - Similarity metric: cosine (``hnsw:space=cosine``)
      - Index type: HNSW (ChromaDB default)
      - Persistence directory: ``settings.CHROMA_PERSIST_DIR``

    The ChromaDB client is stored as a private attribute (``self._client``)
    and never exposed — external code accesses all operations through
    this class's public methods only (SPEC F008 Design Constraint 3).
    """

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )

    # --- Collection Lifecycle (T0102–T0103) ---

    def create_collection(self, name: str) -> None:
        """Create a ChromaDB collection with cosine distance / HNSW index.

        Args:
            name: Collection name (knowledge base name).
        """
        self._client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def delete_collection(self, name: str) -> None:
        """Delete a ChromaDB collection and all contained data.

        Args:
            name: Collection name to delete.
        """
        self._client.delete_collection(name=name)

    def list_collections(self) -> List[str]:
        """List all existing collection names.

        Returns:
            List of collection names.
        """
        return [col.name for col in self._client.list_collections()]

    def rename_collection(self, old_name: str, new_name: str) -> None:
        """Rename a ChromaDB collection (storage-layer operation only).

        Uses ChromaDB's native rename (``Collection.modify(name=...)``).
        Validates ``old_name`` exists first (SPEC F001 error table: rename
        of non-existent KB → 404 COLLECTION_NOT_FOUND).

        Chunk metadata, uploads directory, and keyword index invalidation
        are NOT handled here — the KB Rename endpoint owns that cascade
        (→ T0402).

        Args:
            old_name: Current collection name.
            new_name: New collection name.
        """
        if old_name not in self.list_collections():
            raise AppError("COLLECTION_NOT_FOUND")
        self._client.get_collection(old_name).modify(name=new_name)

    # --- Data Operations ---

    def add_texts(
        self,
        collection: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> List[str]:
        """Persist chunks, embeddings, and metadata into a ChromaDB collection.

        Each chunk is stored with its 384-dim embedding and its 9-field
        metadata dict (SPEC F008 Metadata Schema).  ``chunk_id`` from the
        metadata is used as the ChromaDB document id — chunk_id is the
        immutable chunk identity (SPEC Section 7.1).

        Per T0104 scope: chunk_ids and embeddings are provided by the
        caller; this method does NOT generate or validate them.

        Args:
            collection: Target collection name.
            chunks: List of chunk text strings.
            embeddings: Corresponding embedding vectors (384-dim).
            metadatas: Corresponding metadata dicts (SPEC F008 Metadata Schema).

        Returns:
            List of chunk_ids (UUID strings) in insertion order.
        """
        ids = [meta["chunk_id"] for meta in metadatas]
        self._client.get_collection(collection).add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return ids

    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int,
    ) -> List[VectorSearchResult]:
        """Vector similarity search — returns similarity_score, NOT raw distance.

        Implements the F008 Distance → Similarity semantic boundary:
        ``similarity_score = clamp(1.0 - raw_distance, 0.0, 1.0)``

        Raw ChromaDB distances never leave this method.  Callers receive
        VectorSearchResult with similarity_score (higher = more relevant,
        range [0, 1]) and must NOT re-normalize (F008).

        Args:
            collection: Collection name to search.
            query_vector: Query embedding vector (384-dim).
            top_k: Maximum number of results to return.

        Returns:
            Results sorted by similarity_score descending.
        """
        raw = self._client.get_collection(collection).query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        results = []
        for i in range(len(raw["ids"][0])):
            metadata = raw["metadatas"][0][i]
            distance = raw["distances"][0][i]
            results.append(
                VectorSearchResult(
                    chunk_id=raw["ids"][0][i],
                    file_id=metadata["file_id"],
                    file_name=metadata["file_name"],
                    content=raw["documents"][0][i],
                    similarity_score=max(0.0, min(1.0, 1.0 - distance)),
                    metadata=metadata,
                )
            )
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results

    def delete_by_file(self, collection: str, file_id: str) -> int:
        """Delete all chunks (vectors + metadata) belonging to a file.

        Args:
            collection: Collection name.
            file_id: UUID of the file whose chunks should be deleted.

        Returns:
            Number of chunks deleted.  0 if the file has no chunks.
        """
        col = self._client.get_collection(collection)
        matching = col.get(where={"file_id": file_id}, include=[])
        count = len(matching["ids"])
        if count > 0:
            col.delete(where={"file_id": file_id})
        return count

    def get_files(self, collection: str) -> List[Dict[str, Any]]:
        """Get file list by aggregating chunk metadata (group/deduplicate by file_id).

        Pure ChromaDB aggregation — no external metadata database
        (SPEC Section 7.3 Persistence Strategy).

        Args:
            collection: Collection name.

        Returns:
            List of dicts with keys: file_id, file_name, size, upload_time,
            chunk_count, status.  Empty list for an empty collection.
        """
        col = self._client.get_collection(collection)
        metadatas = col.get(include=["metadatas"])["metadatas"]
        files: Dict[str, Dict[str, Any]] = {}
        for meta in metadatas:
            fid = meta["file_id"]
            if fid not in files:
                # First chunk supplies the denormalized fields
                # (consistent across chunks of the same file_id, SPEC 7.4)
                files[fid] = {
                    "file_id": fid,
                    "file_name": meta["file_name"],
                    "size": meta["file_size"],
                    "upload_time": meta["upload_time"],
                    "chunk_count": 0,
                    "status": meta["ingestion_status"],
                }
            files[fid]["chunk_count"] += 1
        return list(files.values())

    # --- Chunk Metadata Access (T0108) ---

    @staticmethod
    def _to_chunk_records(got: Dict[str, Any]) -> List[ChunkRecord]:
        """Map ChromaDB get() output to ChunkRecord list (no embeddings)."""
        records = []
        for i in range(len(got["ids"])):
            meta = got["metadatas"][i]
            records.append(
                ChunkRecord(
                    chunk_id=got["ids"][i],
                    file_id=meta["file_id"],
                    file_name=meta["file_name"],
                    collection_name=meta["collection_name"],
                    chunk_index=meta["chunk_index"],
                    content=got["documents"][i],
                    metadata=meta,
                )
            )
        return records

    def list_chunks(self, collection: str) -> List[ChunkRecord]:
        """List all chunks in a collection (without embedding vectors).

        Used by Keyword Retriever for building the inverted index.

        Args:
            collection: Collection name.

        Returns:
            All ChunkRecords in the collection.
        """
        col = self._client.get_collection(collection)
        got = col.get(include=["documents", "metadatas"])
        return self._to_chunk_records(got)

    def get_chunk_count(self, collection: str) -> int:
        """Get the total number of chunks in a collection.

        Args:
            collection: Collection name.

        Returns:
            Total chunk count.
        """
        return self._client.get_collection(collection).count()

    def get_chunks_by_file(self, collection: str, file_id: str) -> List[ChunkRecord]:
        """Get all chunks for a specific file, ordered by chunk_index ASC.

        Args:
            collection: Collection name.
            file_id: UUID of the file.

        Returns:
            ChunkRecords sorted by chunk_index ascending.
        """
        col = self._client.get_collection(collection)
        got = col.get(where={"file_id": file_id}, include=["documents", "metadatas"])
        records = self._to_chunk_records(got)
        records.sort(key=lambda r: r.chunk_index)
        return records
