"""Keyword index invalidation seam for content-changing operations."""

import logging


logger = logging.getLogger(__name__)


def invalidate_keyword_index(collection_name: str) -> None:
    """Invalidate one collection without failing the durable operation.

    The vector store is the durable source of truth.  If the normal invalidation
    seam fails, force the existing lazy full-rebuild path and keep the original
    cache-maintenance failure in the log instead of propagating it to callers.
    """
    from app.services.qa import KeywordRetriever

    try:
        KeywordRetriever.invalidate(collection_name)
    except Exception:
        KeywordRetriever.mark_dirty(collection_name)
        logger.exception(
            "keyword index invalidation failed; collection marked dirty for rebuild: %s",
            collection_name,
        )
