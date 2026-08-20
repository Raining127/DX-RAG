"""Embedding — bge-small-zh-v1.5 lazy singleton + chunk encoding (SPEC F007).

SPEC F007 Model Loading Strategy:
  - Lazy load on FIRST use (never at application startup)
  - Cache the loaded model as a process-level singleton
  - Subsequent calls reuse the cached instance — never reload per request

SPEC F007 Embedding Generation:
  - encode_chunks(chunks) → model.encode(chunks, normalize_embeddings=True).tolist()
  - Empty chunks → empty list (not an error)

Error contract (SPEC F007):
  - Model path missing, corrupt files, OOM, or ANY load failure on first
    use → AppError("EMBEDDING_MODEL_ERROR") → HTTP 500
    (catalog entry: app.core.errors)
"""

from typing import TYPE_CHECKING, List, Optional

from app.core.config import settings
from app.core.errors import AppError

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


# Module-level singleton cache — None until the first successful load.
_model: Optional["SentenceTransformer"] = None


def get_model() -> "SentenceTransformer":
    """Return the process-level bge-small-zh-v1.5 model singleton.

    The first call performs the runtime import and model construction
    (``SentenceTransformer(settings.EMBED_MODEL)``); the loaded instance
    is cached and every later call returns it directly.

    The runtime ``sentence_transformers`` import lives inside this
    function so that importing this module never loads the model and
    never fails when the package is unavailable — the failure surfaces
    on first use, per SPEC F007.

    Raises:
        AppError: EMBEDDING_MODEL_ERROR (HTTP 500) if the import or the
            model construction/loading fails.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(settings.EMBED_MODEL)
        except Exception as exc:
            raise AppError("EMBEDDING_MODEL_ERROR") from exc
    return _model


def encode_chunks(chunks: List[str]) -> List[List[float]]:
    """Convert text chunks to 384-dim L2-normalized vectors (SPEC F007).

    Uses the singleton model from ``get_model()``; the model itself
    performs L2 normalization (``normalize_embeddings=True``) and the
    result is converted to plain Python float lists via ``.tolist()``.

    Args:
        chunks: List of chunk text strings.

    Returns:
        One 384-dim vector per chunk as List[List[float]].  Empty input
        returns an empty list — not an error (SPEC F007 error table).

    Raises:
        AppError: EMBEDDING_MODEL_ERROR (500) if the model fails to load.
    """
    if not chunks:
        return []
    return get_model().encode(chunks, normalize_embeddings=True).tolist()
