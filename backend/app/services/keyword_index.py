"""Keyword index invalidation seam (SPEC F001 Rename step 5 / F009 lifecycle).

T0402 establishes this seam ONLY.  The tokenizer, inverted index,
keyword search, and rebuild are Phase 6 (T0601/T0602) — none of them
may be implemented here.

Contract (single collection scope):
  - ``invalidate_keyword_index(collection_name)`` marks ONE collection's
    keyword index dirty so the next keyword search rebuilds it from
    ``VectorStore.list_chunks`` (full rebuild, SPEC F009).
  - Idempotent: calling it repeatedly has the same effect as one call.
  - No-op when the index/cache for that collection does not exist
    (nothing to invalidate).
  - Raises when a real invalidation fails — the rename orchestration
    catches this, compensates, and maps it to 500 ``RENAME_FAILED``.

Current state (T0402): the Phase 6 keyword index does not exist yet, so
the body is a documented no-op — an absent cache is a no-op by
contract.  T0602 replaces the body with the real dirty-flag
invalidation against its in-memory per-collection index.
Real keyword-index integration acceptance is DEFERRED TO T0602.
"""


def invalidate_keyword_index(collection_name: str) -> None:
    """Invalidate the keyword index of a single collection (F009 lifecycle).

    Idempotent; no-op while the index for ``collection_name`` does not
    exist.  Callers (KB rename T0402, KB delete T0403, upload T0502)
    invoke this after every operation that changes chunk content or the
    collection namespace.

    Args:
        collection_name: Knowledge base (ChromaDB collection) name whose
            index is stale.

    Raises:
        Exception: propagated by the caller if a real index exists and
            its invalidation fails (mapped to RENAME_FAILED by the KB
            rename orchestration).
    """
    # T0602: mark this collection's in-memory index dirty here.  Until
    # the Phase 6 index exists there is no cache to invalidate — no-op.
    return None
