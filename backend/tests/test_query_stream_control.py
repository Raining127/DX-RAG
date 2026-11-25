"""Controlled retry/deadline tests; no live HTTP, Chroma or model calls."""

import asyncio
import json
import threading
import time
import unittest
from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

from pydantic import SecretStr

from app.core.config import settings
from app.main import app
from app.services.qa import AsyncDeepSeekClient


def chunk(text=None, reason=None):
    return {"choices": [{"delta": {"content": text}, "finish_reason": reason}]}


class FakeUpstream:
    def __init__(self, items, close_error=None):
        self.items = iter(items)
        self.closed = False
        self.close_error = close_error

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            item = next(self.items)
        except StopIteration:
            raise StopAsyncIteration
        if isinstance(item, Exception):
            raise item
        return item

    async def close(self):
        self.closed = True
        if self.close_error:
            raise self.close_error


class StatusError(Exception):
    def __init__(self, code):
        self.status_code = code


def frames(messages):
    data = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    result = []
    for frame in data.decode().split("\n\n"):
        if frame.startswith("event: "):
            lines = frame.splitlines()
            result.append((lines[0][7:], json.loads(lines[1][6:])))
    return result


class ControlledStreamTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.store = Mock()
        self.store.list_collections.return_value = ["kb"]
        self.store.get_chunk_count.return_value = 1
        self.service = Mock()
        self.service.prepare.return_value = ([{
            "file_id": "file-1", "file_name": "文档.md", "chunk_id": "chunk-1",
            "content": "资料", "final_score": 0.9,
        }], "上下文", "历史")
        self.sdk = Mock()
        self.sdk.chat.completions.create = AsyncMock()
        self.sdk.close = AsyncMock()
        self.stack = ExitStack()
        self.stack.enter_context(patch("app.api.query.ChromaVectorStore", return_value=self.store))
        self.stack.enter_context(patch("app.api.query.QAService", return_value=self.service))
        self.sdk_factory = self.stack.enter_context(patch("app.services.qa.AsyncOpenAI", return_value=self.sdk))
        self.stack.enter_context(patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")))
        self.stack.enter_context(patch.object(settings, "LLM_MAX_RETRIES", 2))
        self.addCleanup(self.stack.close)

    async def request(self, receive=None, send=None):
        payload = json.dumps({"question": "问题", "collection_name": "kb"}).encode()
        messages = []
        first = True

        async def default_receive():
            nonlocal first
            if first:
                first = False
                return {"type": "http.request", "body": payload, "more_body": False}
            await asyncio.Event().wait()

        async def default_send(message):
            messages.append(message)

        scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1", "method": "POST", "path": "/api/query/stream",
            "raw_path": b"/api/query/stream", "query_string": b"", "root_path": "",
            "headers": [(b"content-type", b"application/json")], "scheme": "http",
            "server": ("test", 80), "client": ("test", 1),
        }
        await app(scope, receive or default_receive, send or default_send)
        return messages

    async def test_early_errors_retry_with_same_input_and_single_retrieval(self):
        streams = [FakeUpstream([chunk(" \n"), ConnectionError("offline")]),
                   FakeUpstream([TimeoutError("slow")]),
                   FakeUpstream([chunk("\n"), chunk("答案"), chunk(reason="stop")])]
        self.sdk.chat.completions.create.side_effect = streams
        with patch("app.api.query.asyncio.sleep", new_callable=AsyncMock) as sleep:
            messages = await self.request()
        events = frames(messages)
        self.assertEqual([x[0] for x in events], ["status", "status", "status", "status", "delta", "done"])
        self.assertEqual([v["stage"] for k, v in events if k == "status"],
                         ["retrieving", "generating", "retrying", "retrying"])
        self.assertEqual(events[-2], ("delta", {"text": "\n答案"}))
        self.assertEqual(events[-1][1]["sources"], [{"file_id": "file-1", "file_name": "文档.md",
                                                     "chunk_id": "chunk-1", "relevance_score": 0.9}])
        self.assertEqual([call.args[0] for call in sleep.await_args_list], [1, 2])
        self.service.prepare.assert_called_once()
        self.assertEqual(self.sdk.chat.completions.create.await_count, 3)
        self.assertEqual(self.sdk.chat.completions.create.await_args_list[0],
                         self.sdk.chat.completions.create.await_args_list[1])
        self.assertEqual(self.sdk.chat.completions.create.await_args_list[1],
                         self.sdk.chat.completions.create.await_args_list[2])
        self.assertTrue(all(stream.closed for stream in streams))
        self.assertTrue(all(call.kwargs["max_retries"] == 0 for call in self.sdk_factory.call_args_list))

    async def test_retry_exhaustion_is_three_attempts(self):
        self.sdk.chat.completions.create.side_effect = [ConnectionError()] * 3
        with patch("app.api.query.asyncio.sleep", new_callable=AsyncMock) as sleep:
            events = frames(await self.request())
        self.assertEqual(self.sdk.chat.completions.create.await_count, 3)
        self.assertEqual([c.args[0] for c in sleep.await_args_list], [1, 2])
        self.assertEqual(events[-1][1]["code"], "LLM_UNAVAILABLE")

    async def test_configured_retry_count_is_bounded(self):
        for configured, expected in [(0, 1), (5, 3)]:
            with self.subTest(configured=configured):
                self.sdk.chat.completions.create.reset_mock()
                self.sdk.chat.completions.create.side_effect = ConnectionError()
                with patch.object(settings, "LLM_MAX_RETRIES", configured), patch(
                    "app.api.query.asyncio.sleep", new_callable=AsyncMock
                ):
                    events = frames(await self.request())
                self.assertEqual(self.sdk.chat.completions.create.await_count, expected)
                self.assertEqual(events[-1][1]["code"], "LLM_UNAVAILABLE")

    async def test_error_after_first_delta_never_retries(self):
        stream = FakeUpstream([chunk("回答"), ConnectionError()])
        self.sdk.chat.completions.create.return_value = stream
        events = frames(await self.request())
        self.assertEqual(self.sdk.chat.completions.create.await_count, 1)
        self.assertEqual(events[-2], ("delta", {"text": "回答"}))
        self.assertEqual(events[-1][1]["code"], "LLM_UNAVAILABLE")
        self.assertTrue(stream.closed)

    async def test_nonretryable_errors_and_failed_cleanup_never_retry(self):
        for effect, expected in [(StatusError(401), "LLM_AUTH_FAILED"),
                                 (StatusError(400), "LLM_RESPONSE_ERROR"),
                                 (FakeUpstream([ConnectionError()], RuntimeError("close")), "LLM_UNAVAILABLE")]:
            with self.subTest(effect=effect):
                self.sdk.chat.completions.create.reset_mock()
                self.sdk.chat.completions.create.side_effect = effect if isinstance(effect, Exception) else None
                self.sdk.chat.completions.create.return_value = effect
                events = frames(await self.request())
                self.assertEqual(self.sdk.chat.completions.create.await_count, 1)
                self.assertEqual(events[-1][1]["code"], expected)
        with patch("app.services.qa.AsyncOpenAI", None):
            self.sdk.chat.completions.create.reset_mock()
            events = frames(await self.request())
            self.assertEqual(events[-1][1]["code"], "LLM_UNAVAILABLE")
            self.sdk.chat.completions.create.assert_not_awaited()

    async def test_cancel_during_backoff_never_starts_another_attempt(self):
        self.sdk.chat.completions.create.side_effect = ConnectionError()
        sleeping = asyncio.Event()
        async def blocked_sleep(_):
            sleeping.set()
            await asyncio.Event().wait()
        with patch("app.api.query.asyncio.sleep", side_effect=blocked_sleep):
            task = asyncio.create_task(self.request())
            try:
                await asyncio.wait_for(sleeping.wait(), 2)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
            finally:
                if not task.done():
                    task.cancel()
        self.assertEqual(self.sdk.chat.completions.create.await_count, 1)

    async def test_deadline_preflight_blocked_thread_returns_504_before_release(self):
        started, release, ended = threading.Event(), threading.Event(), threading.Event()
        def blocked():
            started.set()
            try:
                release.wait(3)
                return ["kb"]
            finally:
                ended.set()
        self.store.list_collections.side_effect = blocked
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
            task = asyncio.create_task(self.request())
            try:
                self.assertTrue(await asyncio.to_thread(started.wait, 1))
                messages = await asyncio.wait_for(task, 1)
                self.assertFalse(release.is_set())
                self.assertEqual(messages[0]["status"], 504)
                body = json.loads(b"".join(m.get("body", b"") for m in messages))
                self.assertEqual(body["error"]["code"], "QUERY_TIMEOUT")
            finally:
                release.set()
                await asyncio.to_thread(ended.wait, 1)
                await asyncio.sleep(0.02)
            self.service.prepare.assert_not_called()
            self.sdk.chat.completions.create.assert_not_awaited()

    async def test_deadline_retrieval_blocked_thread_never_starts_model(self):
        started, release, ended = threading.Event(), threading.Event(), threading.Event()
        def blocked(*args):
            started.set()
            try:
                release.wait(3)
                return [], "", ""
            finally:
                ended.set()
        self.service.prepare.side_effect = blocked
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
            task = asyncio.create_task(self.request())
            try:
                self.assertTrue(await asyncio.to_thread(started.wait, 1))
                messages = await asyncio.wait_for(task, 1)
                self.assertFalse(release.is_set())
                self.assertEqual(frames(messages)[-1][1]["code"], "QUERY_TIMEOUT")
            finally:
                release.set()
                await asyncio.to_thread(ended.wait, 1)
                await asyncio.sleep(0.02)
            self.sdk.chat.completions.create.assert_not_awaited()

    async def test_asgi_24_disconnect_during_retrieval_stops_orchestration(self):
        started, release, ended = threading.Event(), threading.Event(), threading.Event()
        first = True
        def blocked(*args):
            started.set()
            try:
                release.wait(3)
                return [], "", ""
            finally:
                ended.set()
        self.service.prepare.side_effect = blocked
        async def receive():
            nonlocal first
            if first:
                first = False
                body = json.dumps({"question": "问题", "collection_name": "kb"}).encode()
                return {"type": "http.request", "body": body, "more_body": False}
            if not await asyncio.to_thread(started.wait, 1):
                raise AssertionError("retrieval did not start")
            return {"type": "http.disconnect"}
        task = asyncio.create_task(self.request(receive=receive))
        try:
            messages = await asyncio.wait_for(asyncio.shield(task), 1)
            self.assertFalse(release.is_set())
            self.assertFalse(any(name == "done" for name, _ in frames(messages)))
        finally:
            release.set()
            await asyncio.to_thread(ended.wait, 1)
            if not task.done():
                await asyncio.wait_for(task, 1)
            await asyncio.sleep(0.02)
        self.sdk.chat.completions.create.assert_not_awaited()

    async def test_asgi_24_disconnect_during_model_read_closes_upstream(self):
        started, closed = asyncio.Event(), asyncio.Event()
        first = True
        class Upstream:
            def __aiter__(self):
                return self
            async def __anext__(self):
                started.set()
                await asyncio.Event().wait()
            async def close(self):
                closed.set()
        self.sdk.chat.completions.create.return_value = Upstream()
        async def receive():
            nonlocal first
            if first:
                first = False
                body = json.dumps({"question": "问题", "collection_name": "kb"}).encode()
                return {"type": "http.request", "body": body, "more_body": False}
            await started.wait()
            return {"type": "http.disconnect"}
        messages = await asyncio.wait_for(self.request(receive=receive), 1)
        self.assertTrue(closed.is_set())
        self.assertFalse(any(name == "done" for name, _ in frames(messages)))
        self.assertEqual(self.sdk.chat.completions.create.await_count, 1)

    async def test_asgi_24_disconnect_during_backoff_never_starts_retry(self):
        retrying = asyncio.Event()
        first = True
        self.sdk.chat.completions.create.side_effect = ConnectionError()
        async def receive():
            nonlocal first
            if first:
                first = False
                body = json.dumps({"question": "问题", "collection_name": "kb"}).encode()
                return {"type": "http.request", "body": body, "more_body": False}
            await retrying.wait()
            return {"type": "http.disconnect"}
        async def send(message):
            if b'"retrying"' in message.get("body", b""):
                retrying.set()
        await asyncio.wait_for(self.request(receive=receive, send=send), 1)
        self.assertEqual(self.sdk.chat.completions.create.await_count, 1)

    async def test_deadline_during_model_read_before_and_after_first_delta(self):
        for first in (False, True):
            with self.subTest(first=first):
                started, closed = asyncio.Event(), asyncio.Event()
                class BlockingUpstream:
                    def __init__(self):
                        self.first = first
                    def __aiter__(self):
                        return self
                    async def __anext__(self):
                        if self.first:
                            self.first = False
                            return chunk("部分")
                        started.set()
                        await asyncio.Event().wait()
                    async def close(self):
                        closed.set()
                self.sdk.chat.completions.create.reset_mock()
                self.sdk.chat.completions.create.return_value = BlockingUpstream()
                with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
                    task = asyncio.create_task(self.request())
                    await asyncio.wait_for(started.wait(), 1)
                    events = frames(await asyncio.wait_for(task, 1))
                self.assertEqual(events[-1][1]["code"], "QUERY_TIMEOUT")
                self.assertEqual(any(name == "delta" for name, _ in events), first)
                self.assertTrue(closed.is_set())
                self.assertEqual(self.sdk.chat.completions.create.await_count, 1)

    async def test_deadline_during_retry_wait_does_not_restart(self):
        self.sdk.chat.completions.create.side_effect = ConnectionError()
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
            events = frames(await asyncio.wait_for(self.request(), 1))
        self.assertEqual(events[-1][1]["code"], "QUERY_TIMEOUT")
        self.assertEqual(self.sdk.chat.completions.create.await_count, 1)

    async def test_deadline_checked_after_event_loop_delay_even_if_completion_is_ready(self):
        # Deliberately block the test event loop so both the result and timeout
        # become ready before either callback can resume; monotonic time wins.
        for outcome in ("success", "auth_failure"):
            with self.subTest(outcome=outcome):
                self.sdk.chat.completions.create.reset_mock()
                async def delayed_create(**kwargs):
                    time.sleep(0.25)
                    if outcome == "auth_failure":
                        raise StatusError(401)
                    return FakeUpstream([chunk("迟到"), chunk(reason="stop")])
                self.sdk.chat.completions.create.side_effect = delayed_create
                with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
                    events = frames(await asyncio.wait_for(self.request(), 1))
                self.assertEqual(events[-1][1]["code"], "QUERY_TIMEOUT")
                self.assertFalse(any(name in ("delta", "done") for name, _ in events))
                self.assertEqual(self.sdk.chat.completions.create.await_count, 1)

    async def test_deadline_includes_request_body_read(self):
        started = asyncio.Event()
        async def receive():
            started.set()
            await asyncio.Event().wait()
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
            task = asyncio.create_task(self.request(receive=receive))
            await asyncio.wait_for(started.wait(), 1)
            messages = await asyncio.wait_for(task, 1)
        self.assertEqual(messages[0]["status"], 504)
        self.assertEqual(json.loads(messages[1]["body"])["error"]["code"], "QUERY_TIMEOUT")
        self.store.list_collections.assert_not_called()

    async def test_deadline_bounds_stalled_send_and_closes_model(self):
        closed = asyncio.Event()
        stalled = asyncio.Event()
        class Upstream:
            def __aiter__(self):
                return self
            async def __anext__(self):
                return chunk("内容")
            async def close(self):
                closed.set()
        self.sdk.chat.completions.create.return_value = Upstream()
        async def send(message):
            if b"event: delta" in message.get("body", b""):
                stalled.set()
                await asyncio.Event().wait()
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
            task = asyncio.create_task(self.request(send=send))
            try:
                await asyncio.wait_for(stalled.wait(), 1)
                await asyncio.wait_for(task, 1)
            finally:
                if not task.done():
                    task.cancel()
            self.assertTrue(closed.is_set())

    async def test_blocked_shielded_cleanup_does_not_hold_response_forever(self):
        closed = asyncio.Event()
        closing = asyncio.Event()
        release = asyncio.Event()
        class Upstream:
            def __aiter__(self):
                return self
            async def __anext__(self):
                await asyncio.Event().wait()
            async def close(self):
                closing.set()
                await release.wait()
                closed.set()
        self.sdk.chat.completions.create.return_value = Upstream()
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
            task = asyncio.create_task(self.request())
            try:
                await asyncio.wait_for(closing.wait(), 1)
                messages = await asyncio.wait_for(asyncio.shield(task), 1)
                self.assertEqual(frames(messages)[-1][1]["code"], "QUERY_TIMEOUT")
            finally:
                release.set()
                await asyncio.wait_for(closed.wait(), 1)
                if not task.done():
                    await asyncio.wait_for(task, 1)

    async def test_stalled_send_and_shielded_cleanup_are_both_bounded(self):
        closing, release, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()
        class Upstream:
            def __aiter__(self):
                return self
            async def __anext__(self):
                return chunk("内容")
            async def close(self):
                closing.set()
                await release.wait()
                closed.set()
        self.sdk.chat.completions.create.return_value = Upstream()
        async def send(message):
            if b"event: delta" in message.get("body", b""):
                await asyncio.Event().wait()
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.15):
            task = asyncio.create_task(self.request(send=send))
            try:
                await asyncio.wait_for(closing.wait(), 1)
                await asyncio.wait_for(asyncio.shield(task), 1)
            finally:
                release.set()
                await asyncio.wait_for(closed.wait(), 1)
                if not task.done():
                    await asyncio.wait_for(task, 1)


if __name__ == "__main__":
    unittest.main()
