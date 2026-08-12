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

from pydantic import BaseModel, Field


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
