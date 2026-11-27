"""Knowledge-base question answering API (SPEC Section 6.4)."""

import asyncio
import json
import sys
import time
from typing import Any, AsyncIterator, Dict, Optional

import anyio
from fastapi import APIRouter, Body, Request
from fastapi.routing import APIRoute
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.errors import AppError, _ERROR_CATALOG
from app.core.vector_store import ChromaVectorStore
from app.models.schemas import QueryRequest, QueryResponse, SourceObject
from app.services.qa import (
    SYSTEM_PROMPT,
    AsyncDeepSeekClient,
    QAService,
    RetryableStreamError,
    _JS_TRIM_WHITESPACE,
    assemble_sources,
    process_history,
)

router = APIRouter()
_background_tasks = set()


def _track_task(task: asyncio.Task) -> None:
    """Keep abandoned cleanup alive and consume its eventual exception."""
    _background_tasks.add(task)

    def finished(completed: asyncio.Task) -> None:
        _background_tasks.discard(completed)
        if not completed.cancelled():
            completed.exception()

    task.add_done_callback(finished)


def _expired(deadline: Optional[float]) -> bool:
    return deadline is not None and time.monotonic() >= deadline


async def _await_deadline(awaitable: Any, deadline: Optional[float], on_abandon: Any = None) -> Any:
    """Wait only until the deadline, even if a cancelled operation shields cleanup."""
    if _expired(deadline):
        # Do not schedule an already-expired operation, especially a new model
        # read or a send. Close the unused coroutine to avoid a warning.
        close = getattr(awaitable, "close", None)
        if close is not None:
            close()
        raise AppError("QUERY_TIMEOUT")
    task = asyncio.ensure_future(awaitable)
    try:
        timeout = None if deadline is None else max(0.0, deadline - time.monotonic())
        done, _ = await asyncio.wait({task}, timeout=timeout)
        if not done or _expired(deadline):
            if task.done() and not task.cancelled():
                task.exception()
            raise AppError("QUERY_TIMEOUT")
        return task.result()
    except BaseException:
        if not task.done():
            task.cancel()
            if on_abandon is not None:
                on_abandon(task)
            else:
                _track_task(task)
        raise


class _StreamingQueryRoute(APIRoute):
    """Start the deadline before FastAPI reads and validates the request body."""

    def get_route_handler(self) -> Any:
        original = super().get_route_handler()

        async def handler(request: Request) -> Any:
            deadline = time.monotonic() + settings.STREAM_QUERY_TIMEOUT
            request.state.stream_query_deadline = deadline
            return await _await_deadline(original(request), deadline)

        return handler


stream_router = APIRouter(route_class=_StreamingQueryRoute)


async def _close_iterator(iterator: Any, interrupted: bool) -> None:
    """Attempt async cleanup without hiding an existing error or cancellation."""
    try:
        with anyio.CancelScope(shield=True):
            await iterator.aclose()
    except Exception:
        if not interrupted:
            raise


async def _finish_model_stream(stream: Any, deadline: Optional[float], interrupted: bool) -> None:
    """Close without letting a shielded provider prevent cancellation or timeout."""
    task = asyncio.create_task(_close_iterator(stream, interrupted))
    _track_task(task)
    timeout = 0.1 if interrupted else (
        None if deadline is None else max(0.0, deadline - time.monotonic())
    )
    try:
        done, _ = await asyncio.wait({task}, timeout=timeout)
    except BaseException:
        with anyio.CancelScope(shield=True):
            await asyncio.wait({task}, timeout=0.1)
        raise
    if interrupted:
        return
    if not done or _expired(deadline):
        raise AppError("QUERY_TIMEOUT")
    task.result()


class _ClosingStreamingResponse(StreamingResponse):
    """Close the response generator when ASGI sending ends or is interrupted."""

    def __init__(self, *args: Any, deadline: Optional[float] = None, **kwargs: Any) -> None:
        self.deadline = deadline
        super().__init__(*args, **kwargs)

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        # Starlette's ASGI 2.4 path relies only on send errors. During a long
        # model read there may be no send, so listen for disconnect as well.
        streaming = asyncio.create_task(self.stream_response(send))
        disconnect = asyncio.create_task(self.listen_for_disconnect(receive))
        try:
            done, _ = await asyncio.wait(
                {streaming, disconnect}, return_when=asyncio.FIRST_COMPLETED
            )
            if streaming in done:
                streaming.result()
            else:
                disconnect.result()
        finally:
            for task in (streaming, disconnect):
                if not task.done():
                    task.cancel()
                    _track_task(task)
            # Normally cleanup is immediate; a provider may shield its close.
            # Do not delay a disconnect indefinitely in that case.
            if not streaming.done():
                with anyio.CancelScope(shield=True):
                    await asyncio.wait({streaming}, timeout=0.2)

        if self.background is not None:
            await self.background()

    async def stream_response(self, send: Any) -> None:
        started = False
        terminal = False
        send_abandoned = False

        async def bounded_send(message: Any) -> None:
            nonlocal started, terminal, send_abandoned
            body = message.get("body", b"")
            is_terminal = body.startswith((b"event: done\n", b"event: incomplete\n", b"event: error\n"))
            # A timeout event gets a short best-effort window: its deadline has
            # necessarily passed, and an unwritable client must not block us.
            is_timeout = body.startswith(b"event: error\n") and b'"QUERY_TIMEOUT"' in body
            limit = time.monotonic() + 0.1 if is_timeout else self.deadline

            async def send_and_record() -> None:
                nonlocal started, terminal
                await send(message)
                if message["type"] == "http.response.start":
                    started = True
                if is_terminal:
                    terminal = True

            def abandon_send(task: asyncio.Task) -> None:
                nonlocal send_abandoned
                send_abandoned = True
                _track_task(task)

            await _await_deadline(send_and_record(), limit, abandon_send)

        try:
            await super().stream_response(bounded_send)
        except AppError as exc:
            if exc.code != "QUERY_TIMEOUT":
                raise
            if started and not terminal and not send_abandoned:
                error = AppError("QUERY_TIMEOUT")
                message = {"type": "http.response.body", "body": _sse_event(
                    "error", {"code": error.code, "message": error.message}
                ).encode("utf-8"), "more_body": False}
                try:
                    await _await_deadline(send(message), time.monotonic() + 0.1)
                except (AppError, OSError):
                    pass
            elif not started and not send_abandoned:
                raise
        finally:
            # Starlette does not close the body iterator on every send failure or
            # disconnect. Shield cleanup from its disconnect cancellation scope.
            await _close_iterator(self.body_iterator, sys.exc_info()[0] is not None)


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


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    """Encode a single event without allowing data to change frame boundaries."""
    # Escaping non-ASCII also keeps malformed lone surrogates encodable by ASGI.
    # Clients recover the original text after parsing the JSON data field.
    payload = json.dumps(data, ensure_ascii=True, allow_nan=False)
    return f"event: {event}\ndata: {payload}\n\n"


async def _stream_query(
    service: QAService, request: QueryRequest, deadline: Optional[float] = None
) -> AsyncIterator[str]:
    """Run one prepared query and translate model results into SSE events."""
    try:
        yield _sse_event("status", {"stage": "retrieving"})
        results, context, history = await _await_deadline(
            run_in_threadpool(
                service.prepare,
                request.question,
                request.collection_name,
                request.top_k,
                [message.model_dump() for message in request.history],
            ),
            deadline,
        )
        yield _sse_event("status", {"stage": "generating"})

        terminal = None
        has_text = False
        emitted_delta = False
        retries = max(0, min(settings.LLM_MAX_RETRIES, 2))
        for attempt in range(retries + 1):
            if _expired(deadline):
                raise AppError("QUERY_TIMEOUT")
            stream = AsyncDeepSeekClient().stream_answer(
                SYSTEM_PROMPT, history, context, request.question
            )
            abandoned = False
            cleanup_task = None

            def abandon_read(task: asyncio.Task) -> None:
                nonlocal abandoned, cleanup_task
                abandoned = True

                async def finish_read_and_close() -> None:
                    try:
                        await task
                    except BaseException:
                        pass
                    await _close_iterator(stream, True)

                cleanup_task = asyncio.create_task(finish_read_and_close())
                _track_task(cleanup_task)

            try:
                while True:
                    try:
                        item = await _await_deadline(stream.__anext__(), deadline, abandon_read)
                    except StopAsyncIteration:
                        break
                    if not isinstance(item, dict):
                        raise AppError("LLM_RESPONSE_ERROR")
                    kind = item.get("type")
                    if kind == "delta":
                        text = item.get("text")
                        if not isinstance(text, str):
                            raise AppError("LLM_RESPONSE_ERROR")
                        if text:
                            has_text = has_text or bool(text.strip(_JS_TRIM_WHITESPACE))
                            emitted_delta = True
                            yield _sse_event("delta", {"text": text})
                    elif kind == "done":
                        if not has_text:
                            raise AppError("LLM_RESPONSE_ERROR")
                        sources = [
                            SourceObject.model_validate(source).model_dump()
                            for source in assemble_sources(results)
                        ]
                        terminal = ("done", {"sources": sources})
                        break
                    elif kind == "incomplete":
                        reason = item.get("reason")
                        if not isinstance(reason, str) or not reason:
                            raise AppError("LLM_RESPONSE_ERROR")
                        terminal = ("incomplete", {"reason": reason})
                        break
                    else:
                        raise AppError("LLM_RESPONSE_ERROR")
            except RetryableStreamError as exc:
                if emitted_delta or not exc.retryable or attempt >= retries:
                    raise
                if _expired(deadline):
                    raise AppError("QUERY_TIMEOUT")
                retry = True
            else:
                retry = False
            finally:
                interrupted = sys.exc_info()[0] in (GeneratorExit, asyncio.CancelledError)
                if abandoned:
                    # Give prompt cleanup a chance even in AnyIO's cancelled
                    # scope, but never wait indefinitely for a shielded SDK.
                    with anyio.CancelScope(shield=True):
                        await asyncio.wait({cleanup_task}, timeout=0.1)
                else:
                    await _finish_model_stream(stream, deadline, interrupted)
            if retry:
                yield _sse_event("status", {"stage": "retrying"})
                await _await_deadline(asyncio.sleep(2 ** attempt), deadline)
                continue
            break
        if terminal is None:
            raise AppError("LLM_RESPONSE_ERROR")
        if _expired(deadline):
            raise AppError("QUERY_TIMEOUT")
        yield _sse_event(*terminal)
    except AppError as exc:
        # Do not expose custom exception messages or details through the stream.
        code = "QUERY_TIMEOUT" if _expired(deadline) else (
            exc.code if exc.code in _ERROR_CATALOG else "INTERNAL_ERROR"
        )
        safe_error = AppError(code)
        message = (
            "问答模型暂时不可用，请稍后重试。"
            if code == "LLM_UNAVAILABLE"
            else safe_error.message
        )
        yield _sse_event("error", {"code": code, "message": message})
    except Exception:
        safe_error = AppError("QUERY_TIMEOUT" if _expired(deadline) else "INTERNAL_ERROR")
        yield _sse_event(
            "error", {"code": safe_error.code, "message": safe_error.message}
        )


@stream_router.post("/query/stream")
def query_stream(body: Any = Body(default=None), request: Request = None) -> StreamingResponse:
    """Validate the request before starting the SSE response."""
    deadline = getattr(request.state, "stream_query_deadline", None) if request else None
    query_request = _parse_query_request(body)
    vector_store = ChromaVectorStore()
    if query_request.collection_name not in vector_store.list_collections():
        raise AppError("COLLECTION_NOT_FOUND")
    if vector_store.get_chunk_count(query_request.collection_name) == 0:
        raise AppError("COLLECTION_EMPTY")

    service = QAService(vector_store=vector_store)
    return _ClosingStreamingResponse(
        _stream_query(service, query_request, deadline),
        media_type="text/event-stream",
        deadline=deadline,
    )


router.include_router(stream_router)
