"""Keyword index invalidation seam for content-changing operations."""


def invalidate_keyword_index(collection_name: str) -> None:
    """Mark one existing collection index dirty; absent indexes are a no-op."""
    from app.services.qa import KeywordRetriever

    KeywordRetriever.invalidate(collection_name)
