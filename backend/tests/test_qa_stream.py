"""Deterministic tests for a single DeepSeek streaming attempt.

The injected upstreams below never access the network or the vector store.
Retry and application-level deadline orchestration belong to SQA-06.
"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from openai import AsyncOpenAI
from pydantic import SecretStr

from app.core.config import settings
from app.core.errors import AppError
from app.services.qa import AsyncDeepSeekClient, RetryableStreamError, SYSTEM_PROMPT


def chunk(content=None, finish_reason=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ]
    )


class StatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class FakeStream:
    def __init__(self, items):
        self.items = iter(items)
        self.closed = False

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


def fake_client(stream=None, error=None):
    create = AsyncMock(return_value=stream, side_effect=error)
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)),
        close=AsyncMock(),
    )


class AsyncDeepSeekClientTests(unittest.IsolatedAsyncioTestCase):
    def answer_stream(self, client):
        return AsyncDeepSeekClient(client=client).stream_answer(
            SYSTEM_PROMPT,
            "User: Earlier question",
            "[来源: policy.md]\nEvidence",
            "Current question",
        )

    async def collect(self, stream):
        return [event async for event in stream]

    async def test_incremental_text_prompt_and_cleanup_before_done(self):
        upstream = FakeStream(
            [chunk(), chunk("  "), chunk("\n"), chunk("首字"), chunk(" "),
             chunk("结尾"), chunk(finish_reason="stop")]
        )
        client = fake_client(upstream)
        stream = self.answer_stream(client)

        self.assertEqual(await stream.__anext__(), {"type": "delta", "text": "  \n首字"})
        self.assertFalse(upstream.closed)
        self.assertEqual(await stream.__anext__(), {"type": "delta", "text": " "})
        self.assertEqual(await stream.__anext__(), {"type": "delta", "text": "结尾"})
        self.assertEqual(await stream.__anext__(), {"type": "done"})
        self.assertTrue(upstream.closed)
        await stream.aclose()
        client.close.assert_not_awaited()  # The injected client is caller-owned.

        client.chat.completions.create.assert_awaited_once()
        request = client.chat.completions.create.await_args.kwargs
        self.assertEqual(request["model"], "deepseek-chat")
        self.assertIs(request["stream"], True)
        self.assertEqual(request["temperature"], settings.LLM_TEMPERATURE)
        self.assertEqual(request["max_tokens"], settings.LLM_MAX_TOKENS)
        self.assertEqual(request["messages"][0], {"role": "system", "content": SYSTEM_PROMPT})
        user = request["messages"][1]
        self.assertEqual(user["role"], "user")
        self.assertIn("## 对话历史\nUser: Earlier question", user["content"])
        self.assertIn("## 参考文档\n[来源: policy.md]\nEvidence", user["content"])
        self.assertIn("## 用户问题\nCurrent question", user["content"])

    async def test_end_reasons_and_empty_results(self):
        cases = [
            ([chunk(" \n"), chunk(finish_reason="stop")],
             [{"type": "incomplete", "reason": "empty"}]),
            ([chunk("last", finish_reason="stop")],
             [{"type": "delta", "text": "last"}, {"type": "done"}]),
            ([chunk("partial"), chunk(finish_reason="length")],
             [{"type": "delta", "text": "partial"}, {"type": "incomplete", "reason": "length"}]),
            ([chunk("last", finish_reason="length")],
             [{"type": "delta", "text": "last"}, {"type": "incomplete", "reason": "length"}]),
            ([chunk(finish_reason="length")],
             [{"type": "incomplete", "reason": "length"}]),
            ([chunk("partial"), chunk(finish_reason="future_reason")],
             [{"type": "delta", "text": "partial"}, {"type": "incomplete", "reason": "other"}]),
        ]
        for chunks, expected in cases:
            with self.subTest(expected=expected):
                upstream = FakeStream(chunks)
                client = fake_client(upstream)
                self.assertEqual(await self.collect(self.answer_stream(client)), expected)
                self.assertTrue(upstream.closed)
                client.chat.completions.create.assert_awaited_once()

    async def test_whitespace_matches_frontend_ecmascript_trim(self):
        cases = [
            ([chunk("\ufeff"), chunk(finish_reason="stop")],
             [{"type": "incomplete", "reason": "empty"}]),
            ([chunk("\ufeff"), chunk("中文"), chunk(finish_reason="stop")],
             [{"type": "delta", "text": "\ufeff中文"}, {"type": "done"}]),
            ([chunk("\u0085"), chunk(finish_reason="stop")],
             [{"type": "delta", "text": "\u0085"}, {"type": "done"}]),
            ([chunk("\u001c"), chunk(finish_reason="stop")],
             [{"type": "delta", "text": "\u001c"}, {"type": "done"}]),
        ]
        for chunks, expected in cases:
            with self.subTest(expected=expected):
                upstream = FakeStream(chunks)
                self.assertEqual(await self.collect(self.answer_stream(fake_client(upstream))), expected)
                self.assertTrue(upstream.closed)

    async def test_empty_choices_do_not_mean_success(self):
        upstream = FakeStream([SimpleNamespace(choices=[]), chunk("ok"), chunk(finish_reason="stop")])
        self.assertEqual(
            await self.collect(self.answer_stream(fake_client(upstream))),
            [{"type": "delta", "text": "ok"}, {"type": "done"}],
        )
        self.assertTrue(upstream.closed)

    async def test_error_payload_with_empty_choices_is_not_ignored(self):
        upstream = FakeStream([
            SimpleNamespace(choices=[], error={"message": "provider failed"})
        ])
        with self.assertRaises(AppError) as raised:
            await self.collect(self.answer_stream(fake_client(upstream)))
        self.assertEqual(raised.exception.code, "LLM_RESPONSE_ERROR")
        self.assertTrue(upstream.closed)

    async def test_missing_finish_and_bad_delta_never_produce_done(self):
        cases = [[chunk("partial")], [chunk(42)], [SimpleNamespace(choices=[])]]
        for chunks in cases:
            with self.subTest(chunks=chunks):
                upstream = FakeStream(chunks)
                seen = []
                with self.assertRaises(AppError) as raised:
                    async for event in self.answer_stream(fake_client(upstream)):
                        seen.append(event)
                self.assertEqual(raised.exception.code, "LLM_RESPONSE_ERROR")
                self.assertNotIsInstance(raised.exception, RetryableStreamError)
                self.assertFalse(any(event["type"] == "done" for event in seen))
                self.assertTrue(upstream.closed)

    async def test_create_and_iteration_errors_are_mapped_once(self):
        for status, code in [(401, "LLM_AUTH_FAILED"), (403, "LLM_AUTH_FAILED"),
                             (400, "LLM_RESPONSE_ERROR"), (429, "LLM_UNAVAILABLE"),
                             (500, "LLM_UNAVAILABLE")]:
            with self.subTest(stage="create", status=status):
                client = fake_client(error=StatusError(status))
                with self.assertRaises(AppError) as raised:
                    await self.collect(self.answer_stream(client))
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(isinstance(raised.exception, RetryableStreamError), status in (429, 500))
                if status in (429, 500):
                    self.assertTrue(raised.exception.retryable)
                client.chat.completions.create.assert_awaited_once()
                client.close.assert_not_awaited()

            with self.subTest(stage="iterate", status=status):
                upstream = FakeStream([StatusError(status)])
                client = fake_client(upstream)
                with self.assertRaises(AppError) as raised:
                    await self.collect(self.answer_stream(client))
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(isinstance(raised.exception, RetryableStreamError), status in (429, 500))
                if status in (429, 500):
                    self.assertTrue(raised.exception.retryable)
                self.assertTrue(upstream.closed)
                client.chat.completions.create.assert_awaited_once()

    async def test_network_errors_marked_retryable_and_preserve_cause(self):
        for error in (ConnectionError("connection"), TimeoutError("timeout")):
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(RetryableStreamError) as raised:
                    await self.collect(self.answer_stream(fake_client(error=error)))
                self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
                self.assertTrue(raised.exception.retryable)
                self.assertIs(raised.exception.__cause__, error)

    async def test_nonretryable_http_status_overrides_network_exception_type(self):
        class BadRequestConnectionError(ConnectionError):
            status_code = 400

        with self.assertRaises(AppError) as raised:
            await self.collect(self.answer_stream(fake_client(error=BadRequestConnectionError())))
        self.assertEqual(raised.exception.code, "LLM_RESPONSE_ERROR")
        self.assertNotIsInstance(raised.exception, RetryableStreamError)

    async def test_failed_cleanup_disables_retry_and_preserves_original_error(self):
        error = ConnectionError("connection")
        upstream = FakeStream([error])
        upstream.close = AsyncMock(side_effect=RuntimeError("close failed"))
        with self.assertRaises(RetryableStreamError) as raised:
            await self.collect(self.answer_stream(fake_client(upstream)))
        self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
        self.assertFalse(raised.exception.retryable)
        self.assertIs(raised.exception.__cause__, error)
        upstream.close.assert_awaited_once()

    async def test_owned_client_close_failure_disables_retry(self):
        error = TimeoutError("timeout")
        client = fake_client(error=error)
        client.close.side_effect = RuntimeError("close failed")
        with patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")), patch(
            "app.services.qa.AsyncOpenAI", return_value=client
        ):
            with self.assertRaises(RetryableStreamError) as raised:
                await self.collect(AsyncDeepSeekClient().stream_answer(
                    SYSTEM_PROMPT, "", "", "question"
                ))
        self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
        self.assertFalse(raised.exception.retryable)
        self.assertIs(raised.exception.__cause__, error)
        client.close.assert_awaited_once()

    async def test_missing_sdk_and_constructor_failure_are_not_retryable(self):
        for sdk in (None, RuntimeError("constructor failed")):
            with self.subTest(sdk=sdk):
                sdk_patch = patch("app.services.qa.AsyncOpenAI", None) if sdk is None else patch(
                    "app.services.qa.AsyncOpenAI", side_effect=sdk
                )
                with patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")), sdk_patch:
                    with self.assertRaises(AppError) as raised:
                        await self.collect(AsyncDeepSeekClient().stream_answer(
                            SYSTEM_PROMPT, "", "", "question"
                        ))
                self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
                self.assertNotIsInstance(raised.exception, RetryableStreamError)

    async def test_error_after_finish_marker_never_produces_done(self):
        upstream = FakeStream([chunk("partial"), chunk(finish_reason="stop"), ConnectionError()])
        seen = []
        with self.assertRaises(AppError) as raised:
            async for event in self.answer_stream(fake_client(upstream)):
                seen.append(event)
        self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
        self.assertEqual(seen, [{"type": "delta", "text": "partial"}])
        self.assertTrue(upstream.closed)

    async def test_failed_attempt_does_not_leak_whitespace_into_next_attempt(self):
        first = FakeStream([chunk(" \n"), ConnectionError()])
        second = FakeStream([chunk("answer"), chunk(finish_reason="stop")])
        client = fake_client()
        client.chat.completions.create.side_effect = [first, second]
        adapter = AsyncDeepSeekClient(client=client)

        seen = []
        with self.assertRaises(AppError) as raised:
            async for event in adapter.stream_answer(SYSTEM_PROMPT, "", "", "question"):
                seen.append(event)
        self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
        self.assertEqual(seen, [])
        self.assertTrue(first.closed)

        events = await self.collect(adapter.stream_answer(SYSTEM_PROMPT, "", "", "question"))
        self.assertEqual(events, [{"type": "delta", "text": "answer"}, {"type": "done"}])
        self.assertTrue(second.closed)
        self.assertEqual(client.chat.completions.create.await_count, 2)

    async def test_consumer_close_releases_upstream(self):
        upstream = FakeStream([chunk("first"), chunk("second"), chunk(finish_reason="stop")])
        client = fake_client(upstream)
        stream = self.answer_stream(client)
        self.assertEqual(await stream.__anext__(), {"type": "delta", "text": "first"})
        await stream.aclose()
        self.assertTrue(upstream.closed)
        client.close.assert_not_awaited()

    async def test_task_cancellation_closes_upstream_and_propagates(self):
        class WaitingStream:
            def __init__(self):
                self.started = asyncio.Event()
                self.closed = False

            def __aiter__(self):
                return self

            async def __anext__(self):
                self.started.set()
                await asyncio.Event().wait()

            async def close(self):
                self.closed = True

        upstream = WaitingStream()
        client = fake_client(upstream)
        stream = self.answer_stream(client)
        task = asyncio.create_task(stream.__anext__())
        await asyncio.wait_for(upstream.started.wait(), timeout=2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertTrue(upstream.closed)
        client.close.assert_not_awaited()

    async def test_cancellation_is_not_hidden_by_stream_close_failure(self):
        class WaitingStream:
            def __init__(self):
                self.started = asyncio.Event()
                self.close = AsyncMock(side_effect=RuntimeError("close failed"))

            def __aiter__(self):
                return self

            async def __anext__(self):
                self.started.set()
                await asyncio.Event().wait()

        upstream = WaitingStream()
        stream = self.answer_stream(fake_client(upstream))
        task = asyncio.create_task(stream.__anext__())
        await asyncio.wait_for(upstream.started.wait(), timeout=2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        upstream.close.assert_awaited_once()

    async def test_legacy_stream_uses_response_aclose(self):
        upstream = FakeStream([chunk("answer"), chunk(finish_reason="stop")])
        upstream.close = None
        upstream.response = SimpleNamespace(aclose=AsyncMock())
        events = await self.collect(self.answer_stream(fake_client(upstream)))
        self.assertEqual(events[-1], {"type": "done"})
        upstream.response.aclose.assert_awaited_once()

    async def test_created_client_is_closed_and_sdk_retry_disabled(self):
        upstream = FakeStream([chunk("answer"), chunk(finish_reason="stop")])
        client = fake_client(upstream)
        with patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")), patch(
            "app.services.qa.AsyncOpenAI", return_value=client
        ) as constructor:
            adapter = AsyncDeepSeekClient()
            constructor.assert_not_called()
            events = await self.collect(
                adapter.stream_answer(SYSTEM_PROMPT, "", "context", "question")
            )

        self.assertEqual(events, [{"type": "delta", "text": "answer"}, {"type": "done"}])
        constructor.assert_called_once_with(
            api_key="test-key", base_url="https://api.deepseek.com",
            timeout=settings.LLM_TIMEOUT, max_retries=0,
        )
        self.assertTrue(upstream.closed)
        client.close.assert_awaited_once()

    async def test_created_client_is_closed_when_create_fails(self):
        client = fake_client(error=TimeoutError())
        with patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")), patch(
            "app.services.qa.AsyncOpenAI", return_value=client
        ):
            with self.assertRaises(AppError) as raised:
                await self.collect(
                    AsyncDeepSeekClient().stream_answer(SYSTEM_PROMPT, "", "", "question")
                )
        self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
        client.close.assert_awaited_once()

    async def test_cancellation_during_stream_close_still_closes_owned_client(self):
        class BlockingCloseStream(FakeStream):
            def __init__(self):
                super().__init__([chunk("answer"), chunk(finish_reason="stop")])
                self.close_started = asyncio.Event()

            async def close(self):
                self.close_started.set()
                await asyncio.Event().wait()

        upstream = BlockingCloseStream()
        client = fake_client(upstream)
        seen = []
        with patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")), patch(
            "app.services.qa.AsyncOpenAI", return_value=client
        ):
            async def consume():
                async for event in AsyncDeepSeekClient().stream_answer(
                    SYSTEM_PROMPT, "", "", "question"
                ):
                    seen.append(event)

            task = asyncio.create_task(consume())
            await asyncio.wait_for(upstream.close_started.wait(), timeout=2)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(task, timeout=2)

        self.assertEqual(seen, [{"type": "delta", "text": "answer"}])
        client.close.assert_awaited_once()

    async def test_close_failure_does_not_emit_done_and_closes_owned_client(self):
        upstream = FakeStream([chunk("answer"), chunk(finish_reason="stop")])
        upstream.close = AsyncMock(side_effect=RuntimeError("close failed"))
        client = fake_client(upstream)
        seen = []
        with patch.object(settings, "DEEPSEEK_API_KEY", SecretStr("test-key")), patch(
            "app.services.qa.AsyncOpenAI", return_value=client
        ):
            with self.assertRaises(AppError) as raised:
                async for event in AsyncDeepSeekClient().stream_answer(
                    SYSTEM_PROMPT, "", "", "question"
                ):
                    seen.append(event)
        self.assertEqual(raised.exception.code, "LLM_UNAVAILABLE")
        self.assertNotIsInstance(raised.exception, RetryableStreamError)
        self.assertEqual(seen, [{"type": "delta", "text": "answer"}])
        upstream.close.assert_awaited_once()
        client.close.assert_awaited_once()

    async def test_real_sdk_decodes_sse_via_in_memory_http_transport(self):
        class BytesStream(httpx.AsyncByteStream):
            def __init__(self):
                self.closed = False

            async def __aiter__(self):
                yield (
                    b'data: {"id":"test","object":"chat.completion.chunk",'
                    b'"created":1,"model":"deepseek-chat","choices":'
                    b'[{"index":0,"delta":{"content":"hel"},"finish_reason":null}]}\n\n'
                )
                yield (
                    b'data: {"id":"test","object":"chat.completion.chunk",'
                    b'"created":1,"model":"deepseek-chat","choices":'
                    b'[{"index":0,"delta":{"content":"lo"},"finish_reason":null}]}\n\n'
                )
                yield (
                    b'data: {"id":"test","object":"chat.completion.chunk",'
                    b'"created":1,"model":"deepseek-chat","choices":'
                    b'[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n'
                    b'data: [DONE]\n\n'
                )

            async def aclose(self):
                self.closed = True

        byte_stream = BytesStream()
        requests = []

        def handle(request):
            requests.append(request)
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"}, stream=byte_stream
            )

        http_client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
        client = AsyncOpenAI(
            api_key="test-key", base_url="https://example.invalid/v1",
            http_client=http_client, max_retries=0,
        )
        try:
            events = await self.collect(self.answer_stream(client))
            self.assertEqual(
                events,
                [{"type": "delta", "text": "hel"},
                 {"type": "delta", "text": "lo"}, {"type": "done"}],
            )
            self.assertEqual(len(requests), 1)
            self.assertTrue(byte_stream.closed)
        finally:
            await client.close()


if __name__ == "__main__":
    unittest.main()
