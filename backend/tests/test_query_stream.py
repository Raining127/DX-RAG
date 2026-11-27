"""Contract tests for the streaming QA route with isolated dependencies.

TestClient exercises the FastAPI route, but may buffer its response.  These
tests do not prove live first-token delivery, disconnect propagation, the
four-minute deadline, or a real model/storage/provider integration.
"""

import asyncio
import json
import threading
import unittest
from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

import anyio
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.requests import ClientDisconnect

from app.core.config import settings
from app.core.errors import AppError
from app.api.query import _stream_query, query_stream
from app.main import app
from app.models.schemas import QueryRequest
from app.services.qa import AsyncDeepSeekClient, QAService, SYSTEM_PROMPT


def parse_events(response):
    """Decode the route's complete response, not arbitrary fragmented SSE."""
    events = []
    for frame in response.text.replace("\r\n", "\n").strip().split("\n\n"):
        if not frame:
            continue
        fields = frame.splitlines()
        event = next(line[6:].strip() for line in fields if line.startswith("event:"))
        data = "\n".join(line[5:].lstrip(" ") for line in fields if line.startswith("data:"))
        events.append((event, json.loads(data)))
    return events


class QueryStreamEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.store = Mock()
        self.store.list_collections.return_value = ["kb"]
        self.store.get_chunk_count.return_value = 2
        self.retriever = Mock()
        self.retriever.hybrid_search.return_value = []
        self.service = QAService(vector_store=self.store, hybrid_retriever=self.retriever)
        self.model = Mock()
        self.events = [{"type": "delta", "text": "回答"}, {"type": "done"}]
        self.model_closed = False
        self.model_emitted = []

        async def stream_answer(*args):
            try:
                for event in self.events:
                    if isinstance(event, Exception):
                        raise event
                    self.model_emitted.append(event)
                    yield event
            finally:
                self.model_closed = True

        self.model.stream_answer.side_effect = stream_answer

    def post(self, payload=None):
        if payload is None:
            payload = {"question": "问题", "collection_name": "kb"}
        return self.client.post("/api/query/stream", json=payload)

    def dependencies(self):
        stack = ExitStack()
        stack.enter_context(patch("app.api.query.ChromaVectorStore", return_value=self.store))
        stack.enter_context(patch("app.api.query.QAService", return_value=self.service))
        stack.enter_context(patch("app.api.query.AsyncDeepSeekClient", return_value=self.model))
        return stack

    def test_invalid_payloads_are_rejected_before_store_or_model(self):
        payloads = [
            ({"question": "", "collection_name": "kb"}, "INVALID_QUERY"),
            ({"question": "问题", "collection_name": "kb", "top_k": 0}, "INVALID_TOP_K"),
            ({"question": "问题", "collection_name": "kb", "top_k": True}, "INVALID_TOP_K"),
            ({"question": "问题", "collection_name": "kb", "history": [{"role": "system", "content": "bad"}]}, "INVALID_HISTORY_FORMAT"),
            ([], "INVALID_QUERY"),
        ]
        for payload, code in payloads:
            with self.subTest(payload=payload), self.dependencies():
                response = self.post(payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["code"], code)
                self.assertTrue(response.headers["content-type"].startswith("application/json"))
                self.store.list_collections.assert_not_called()
                self.retriever.hybrid_search.assert_not_called()
                self.model.stream_answer.assert_not_called()

    def test_missing_collection_and_empty_collection_are_http_errors(self):
        for collection_names, chunk_count, status, code in [
            ([], 2, 404, "COLLECTION_NOT_FOUND"),
            (["kb"], 0, 409, "COLLECTION_EMPTY"),
        ]:
            with self.subTest(code=code):
                self.store.list_collections.return_value = collection_names
                self.store.get_chunk_count.return_value = chunk_count
                with self.dependencies():
                    response = self.post()
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()["error"]["code"], code)
                self.assertTrue(response.headers["content-type"].startswith("application/json"))
                self.retriever.hybrid_search.assert_not_called()
                self.model.stream_answer.assert_not_called()

    def test_injected_preflight_timeout_maps_to_504_not_a_stream(self):
        self.store.get_chunk_count.side_effect = AppError("QUERY_TIMEOUT")
        with self.dependencies():
            response = self.post()
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["error"]["code"], "QUERY_TIMEOUT")
        self.retriever.hybrid_search.assert_not_called()
        self.model.stream_answer.assert_not_called()

    def test_success_stream_encodes_text_and_keeps_all_source_chunks(self):
        filename = '文档"\\\n.md'
        chunks = [
            {"file_id": "file-1", "file_name": filename, "chunk_id": "chunk-1", "content": "第一段", "final_score": 0.9},
            {"file_id": "file-1", "file_name": filename, "chunk_id": "chunk-2", "content": "第二段", "final_score": 0.8},
        ]
        self.retriever.hybrid_search.return_value = chunks
        text = '中文"引号"\n路径\\文件'
        self.events = [{"type": "delta", "text": text}, {"type": "done"}]
        context = f"[来源: {filename}]\n第一段"
        with patch.object(settings, "MAX_CONTEXT_CHARS", len(context)), self.dependencies():
            response = self.post({"question": "问题", "collection_name": "kb", "history": [{"role": "user", "content": "前文"}]})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
        self.assertEqual(parse_events(response), [
            ("status", {"stage": "retrieving"}),
            ("status", {"stage": "generating"}),
            ("delta", {"text": text}),
            ("done", {"sources": [
                {"file_id": "file-1", "file_name": filename, "chunk_id": "chunk-1", "relevance_score": 0.9},
                {"file_id": "file-1", "file_name": filename, "chunk_id": "chunk-2", "relevance_score": 0.8},
            ]}),
        ])
        self.model.stream_answer.assert_called_once_with(SYSTEM_PROMPT, "User: 前文", context, "问题")
        self.assertTrue(self.model_closed)

    def test_no_matching_chunks_still_generate_with_empty_sources(self):
        with self.dependencies():
            response = self.post()
        self.assertEqual(parse_events(response)[-1], ("done", {"sources": []}))
        self.model.stream_answer.assert_called_once_with(SYSTEM_PROMPT, "", "", "问题")
        self.assertTrue(self.model_closed)

    def test_json_frames_preserve_unpaired_surrogates_without_utf8_failure(self):
        # Surrogates are created in memory; the response carries escaped JSON.
        filename = "文档\udfff.md"
        text = "中文\ud800\n引号\""
        self.retriever.hybrid_search.return_value = [
            {"file_id": "file-1", "file_name": filename, "chunk_id": "chunk-1", "content": "内容", "final_score": 0.9}
        ]
        self.events = [{"type": "delta", "text": text}, {"type": "done"}]
        with self.dependencies():
            response = self.post()
        self.assertEqual(response.status_code, 200)
        events = parse_events(response)
        self.assertEqual(events[-2], ("delta", {"text": text}))
        self.assertEqual(events[-1][0], "done")
        self.assertEqual(events[-1][1]["sources"][0]["file_name"], filename)
        self.assertTrue(self.model_closed)

    def test_incomplete_results_never_emit_done_or_sources(self):
        for reason in ("length", "empty", "other"):
            with self.subTest(reason=reason):
                self.events = [{"type": "incomplete", "reason": reason}]
                with self.dependencies():
                    response = self.post()
                self.assertEqual(parse_events(response), [
                    ("status", {"stage": "retrieving"}),
                    ("status", {"stage": "generating"}),
                    ("incomplete", {"reason": reason}),
                ])
                self.assertTrue(self.model_closed)

    def test_retrieval_error_is_stream_error_and_hides_internal_message(self):
        self.retriever.hybrid_search.side_effect = AppError("EMBEDDING_MODEL_ERROR", message="private-retrieval-detail")
        with self.dependencies():
            response = self.post()
        events = parse_events(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(events[0], ("status", {"stage": "retrieving"}))
        self.assertEqual(events[-1][0], "error")
        self.assertEqual(events[-1][1]["code"], "EMBEDDING_MODEL_ERROR")
        self.assertNotIn("private-retrieval-detail", response.text)
        self.assertFalse(any(name == "done" for name, _ in events))
        self.model.stream_answer.assert_not_called()

    def test_model_failure_after_delta_is_stream_error_without_done(self):
        self.events = [
            {"type": "delta", "text": "部分回答"},
            AppError("LLM_UNAVAILABLE", message="private-model-detail"),
        ]
        with self.dependencies():
            response = self.post()
        events = parse_events(response)
        self.assertIn(("delta", {"text": "部分回答"}), events)
        self.assertEqual(events[-1][0], "error")
        self.assertEqual(events[-1][1]["code"], "LLM_UNAVAILABLE")
        self.assertNotIn("重试已耗尽", events[-1][1]["message"])
        self.assertNotIn("private-model-detail", response.text)
        self.assertFalse(any(name == "done" for name, _ in events))
        self.assertTrue(self.model_closed)

    def test_nonstream_unavailable_message_is_unchanged(self):
        self.service.answer = Mock(side_effect=AppError("LLM_UNAVAILABLE"))
        with self.dependencies():
            response = self.client.post(
                "/api/query", json={"question": "问题", "collection_name": "kb"}
            )
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"]["code"], "LLM_UNAVAILABLE")
        self.assertIn("重试已耗尽", response.json()["error"]["message"])

    def test_injected_stream_timeout_maps_to_error_event(self):
        self.retriever.hybrid_search.side_effect = AppError("QUERY_TIMEOUT")
        with self.dependencies():
            response = self.post()
        self.assertEqual(response.status_code, 200)
        events = parse_events(response)
        self.assertEqual(events[-1][0], "error")
        self.assertEqual(events[-1][1]["code"], "QUERY_TIMEOUT")
        self.assertFalse(any(name == "done" for name, _ in events))

    def test_unexpected_error_is_sanitized(self):
        self.events = [{"type": "delta", "text": "部分回答"}, RuntimeError("private-error-detail")]
        with self.dependencies():
            response = self.post()
        events = parse_events(response)
        self.assertEqual(events[-1][0], "error")
        self.assertEqual(events[-1][1]["code"], "INTERNAL_ERROR")
        self.assertNotIn("private-error-detail", response.text)
        self.assertTrue(self.model_closed)

    def test_invalid_sources_cannot_emit_done(self):
        self.retriever.hybrid_search.return_value = [
            {"file_name": "notes.md", "chunk_id": "chunk-1", "content": "text", "final_score": 0.9}
        ]
        with self.dependencies():
            response = self.post()
        events = parse_events(response)
        self.assertEqual(events[-1][0], "error")
        self.assertFalse(any(name == "done" for name, _ in events))
        self.assertTrue(self.model_closed)

    def test_missing_internal_terminal_never_emits_done(self):
        self.events = [{"type": "delta", "text": "部分回答"}]
        with self.dependencies():
            response = self.post()
        events = parse_events(response)
        self.assertEqual(events[-1][0], "error")
        self.assertFalse(any(name == "done" for name, _ in events))
        self.assertTrue(self.model_closed)

    def test_invalid_internal_results_never_emit_done(self):
        cases = [
            [{"type": "done"}],
            [{"type": "delta", "text": " \n"}, {"type": "done"}],
            [{"type": "delta", "text": 123}],
            [{"type": "incomplete", "reason": None}],
            [{"type": "unknown"}],
        ]
        for model_events in cases:
            with self.subTest(model_events=model_events):
                self.events = model_events
                self.model_closed = False
                with self.dependencies():
                    response = self.post()
                events = parse_events(response)
                self.assertEqual(events[-1][0], "error")
                self.assertEqual(events[-1][1]["code"], "LLM_RESPONSE_ERROR")
                self.assertFalse(any(name == "done" for name, _ in events))
                self.assertTrue(self.model_closed)

    def test_first_terminal_closes_model_generator_and_ignores_later_results(self):
        self.events = [
            {"type": "delta", "text": "回答"},
            {"type": "done"},
            {"type": "delta", "text": "迟到内容"},
        ]
        with self.dependencies():
            response = self.post()
        events = parse_events(response)
        self.assertEqual(events[-1], ("done", {"sources": []}))
        self.assertNotIn("迟到内容", response.text)
        self.assertEqual(self.model_emitted, self.events[:2])
        self.assertTrue(self.model_closed)

    def test_collection_becomes_empty_after_preflight_is_stream_error(self):
        self.store.get_chunk_count.side_effect = [1, 0]
        with self.dependencies():
            response = self.post()
        self.assertEqual(response.status_code, 200)
        events = parse_events(response)
        self.assertEqual(events[-1][0], "error")
        self.assertEqual(events[-1][1]["code"], "COLLECTION_EMPTY")
        self.model.stream_answer.assert_not_called()


class StreamGeneratorCleanupTests(unittest.IsolatedAsyncioTestCase):
    async def test_consumer_aclose_closes_model_generator(self):
        """Direct generator closure is not an HTTP-disconnect proof."""
        closed = []

        async def model_stream(*args):
            try:
                yield {"type": "delta", "text": "已收到"}
                yield {"type": "delta", "text": "未消费"}
            finally:
                closed.append(True)

        service = Mock()
        service.prepare.return_value = ([], "", "")
        model = Mock()
        model.stream_answer.side_effect = model_stream
        request = QueryRequest(question="问题", collection_name="kb")
        with patch("app.api.query.AsyncDeepSeekClient", return_value=model):
            stream = _stream_query(service, request)
            self.assertIn("retrieving", await stream.__anext__())
            self.assertIn("generating", await stream.__anext__())
            frame = await stream.__anext__()
            self.assertEqual(json.loads(frame.split("data: ", 1)[1]), {"text": "已收到"})
            await stream.aclose()

        self.assertEqual(closed, [True])

    async def test_cancelled_retrieval_does_not_start_model_after_it_returns(self):
        """Cancellation stops orchestration; the blocking worker is released separately."""
        started = threading.Event()
        release = threading.Event()

        def blocking_prepare(*args):
            started.set()
            if not release.wait(timeout=2):
                raise TimeoutError("test worker was not released")
            return [], "", ""

        service = Mock()
        service.prepare.side_effect = blocking_prepare
        model_factory = Mock()
        request = QueryRequest(question="问题", collection_name="kb")
        with patch("app.api.query.AsyncDeepSeekClient", model_factory):
            stream = _stream_query(service, request)
            self.assertIn("retrieving", await stream.__anext__())
            task = asyncio.create_task(stream.__anext__())
            try:
                self.assertTrue(await asyncio.to_thread(started.wait, 1))
                task.cancel()
                await asyncio.sleep(0)
            finally:
                release.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
            await stream.aclose()

        model_factory.assert_not_called()

    async def test_asgi_send_failure_or_cancellation_closes_model_generator(self):
        """A controlled ASGI send failure is not a real HTTP-disconnect test."""
        for failure in (OSError("send failed"), asyncio.CancelledError()):
            with self.subTest(failure=type(failure).__name__):
                closed = []
                sent = []

                async def model_stream(*args):
                    try:
                        yield {"type": "delta", "text": "已收到"}
                        yield {"type": "done"}
                    finally:
                        closed.append(True)

                async def send(message):
                    if message["type"] == "http.response.body":
                        body = message.get("body", b"")
                        sent.append(body)
                        if b"event: delta" in body:
                            raise failure

                async def receive():
                    await asyncio.Event().wait()

                store = Mock()
                store.list_collections.return_value = ["kb"]
                store.get_chunk_count.return_value = 1
                service = Mock()
                service.prepare.return_value = ([], "", "")
                model = Mock()
                model.stream_answer.side_effect = model_stream
                scope = {"type": "http", "asgi": {"spec_version": "2.4"}}

                with patch("app.api.query.ChromaVectorStore", return_value=store), patch(
                    "app.api.query.QAService", return_value=service
                ), patch("app.api.query.AsyncDeepSeekClient", return_value=model):
                    response = query_stream({"question": "问题", "collection_name": "kb"})
                    expected = (OSError, ClientDisconnect) if isinstance(failure, OSError) else asyncio.CancelledError
                    with self.assertRaises(expected):
                        await response(scope, receive, send)

                self.assertEqual(closed, [True])
                self.assertFalse(any(b"event: done" in frame for frame in sent))

    async def test_asgi_20_disconnect_closes_blocked_model_generator(self):
        """Exercise ASGI task cancellation with a mock disconnect, not real HTTP."""
        closed = []
        sent = []
        waiting = asyncio.Event()

        async def model_stream(*args):
            try:
                yield {"type": "delta", "text": "已收到"}
                waiting.set()
                await asyncio.Event().wait()
            finally:
                closed.append(True)

        async def send(message):
            if message["type"] == "http.response.body":
                sent.append(message.get("body", b""))

        async def receive():
            await waiting.wait()
            return {"type": "http.disconnect"}

        store = Mock()
        store.list_collections.return_value = ["kb"]
        store.get_chunk_count.return_value = 1
        service = Mock()
        service.prepare.return_value = ([], "", "")
        model = Mock()
        model.stream_answer.side_effect = model_stream
        scope = {"type": "http", "asgi": {"spec_version": "2.0"}}

        with patch("app.api.query.ChromaVectorStore", return_value=store), patch(
            "app.api.query.QAService", return_value=service
        ), patch("app.api.query.AsyncDeepSeekClient", return_value=model):
            response = query_stream({"question": "问题", "collection_name": "kb"})
            await asyncio.wait_for(response(scope, receive, send), timeout=3)

        self.assertEqual(closed, [True])
        self.assertTrue(any(b"event: delta" in frame for frame in sent))
        self.assertFalse(any(b"event: done" in frame for frame in sent))

    async def test_asgi_20_disconnect_closes_real_adapter_upstream(self):
        """ASGI mock disconnect exercises real adapter cleanup under AnyIO cancellation."""
        waiting = asyncio.Event()
        closed = []
        client_closed = []
        sent = []

        class Upstream:
            def __init__(self):
                self.first = True

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.first:
                    self.first = False
                    return {"choices": [{"delta": {"content": "内容"}, "finish_reason": None}]}
                waiting.set()
                await asyncio.Event().wait()

            async def close(self):
                await anyio.sleep(0)
                closed.append(True)

        async def send(message):
            if message["type"] == "http.response.body":
                sent.append(message.get("body", b""))

        async def receive():
            await waiting.wait()
            return {"type": "http.disconnect"}

        store = Mock()
        store.list_collections.return_value = ["kb"]
        store.get_chunk_count.return_value = 1
        service = Mock()
        service.prepare.return_value = ([], "", "")
        fake_client = Mock()
        fake_client.chat.completions.create = AsyncMock(return_value=Upstream())
        async def close_client():
            await anyio.sleep(0)
            client_closed.append(True)
        fake_client.close = AsyncMock(side_effect=close_client)
        adapter = AsyncDeepSeekClient()
        scope = {"type": "http", "asgi": {"spec_version": "2.0"}}

        with patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")), patch(
            "app.services.qa.AsyncOpenAI", return_value=fake_client
        ), patch("app.api.query.ChromaVectorStore", return_value=store), patch(
            "app.api.query.QAService", return_value=service
        ), patch("app.api.query.AsyncDeepSeekClient", return_value=adapter):
            response = query_stream({"question": "问题", "collection_name": "kb"})
            await asyncio.wait_for(response(scope, receive, send), timeout=3)

        self.assertEqual(closed, [True])
        self.assertEqual(client_closed, [True])
        fake_client.close.assert_awaited_once()
        self.assertTrue(any(b"event: delta" in frame for frame in sent))
        self.assertFalse(any(b"event: done" in frame for frame in sent))


if __name__ == "__main__":
    unittest.main()
