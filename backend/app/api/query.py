"""Knowledge-base question answering API (SPEC Section 6.4)."""

from typing import Any

from fastapi import APIRouter, Body

from app.core.config import settings
from app.core.errors import AppError
from app.core.vector_store import ChromaVectorStore
from app.models.schemas import QueryRequest, QueryResponse
from app.services.qa import QAService, process_history

router = APIRouter()


def _parse_query_request(payload: Any) -> QueryRequest:
    """Validate the query payload and map invalid fields to API errors."""
    if isinstance(payload, QueryRequest):
        payload = payload.model_dump()
    if not isinstance(payload, dict):
        raise AppError("INVALID_QUERY")

    question = payload.get("question")
    collection_name = payload.get("collection_name")
    if not isinstance(question, str) or not question.strip():
        raise AppError("INVALID_QUERY")
    if not isinstance(collection_name, str) or not collection_name.strip():
        raise AppError("INVALID_QUERY")

    top_k = payload.get("top_k", settings.DEFAULT_TOP_K)
    if (
        isinstance(top_k, bool)
        or not isinstance(top_k, int)
        or not settings.TOP_K_MIN <= top_k <= settings.TOP_K_MAX
    ):
        raise AppError("INVALID_TOP_K")

    history = payload.get("history", [])
    if not isinstance(history, list):
        raise AppError("INVALID_HISTORY_FORMAT")
    # Validate at the API boundary; QAService repeats this defense-in-depth
    # check when it formats the history for the LLM prompt.
    process_history(history)

    return QueryRequest(
        question=question,
        collection_name=collection_name,
        top_k=top_k,
        history=history,
    )


@router.post("/query", response_model=QueryResponse)
def query(body: Any = Body(default=None)) -> QueryResponse:
    """Answer a question against one knowledge-base collection."""
    request = _parse_query_request(body)

    vector_store = ChromaVectorStore()
    if request.collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")

    result = QAService(vector_store=vector_store).answer(
        request.question,
        request.collection_name,
        request.top_k,
        [message.model_dump() for message in request.history],
    )
    return QueryResponse.model_validate(result)
