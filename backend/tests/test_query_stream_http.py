"""Real loopback HTTP integration with in-memory retrieval and model fixtures.

Uvicorn, FastAPI and the stream adapter are real. The store, retrieval and
provider are controlled fakes: no ChromaDB, model files or external calls.
"""

import asyncio
import json
import socket
import threading
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

import httpx
import uvicorn

from app.core.config import settings
from app.main import app
from app.api.query import _ClosingStreamingResponse
from app.services.qa import AsyncDeepSeekClient, QAService


def chunk(text=None, reason=None):
    return {"choices": [{"delta": {"content": text}, "finish_reason": reason}]}


class FakeStream:
    def __init__(self, question, gate, closed):
        self.question = question
        self.gate = gate
        self.closed = closed
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.index += 1
        if self.index == 1:
            if self.question == "empty":
                return chunk(" \n")
            return chunk("首段:" + self.question)
        if self.index == 2:
            await self.gate.wait()
            if self.question in {"empty", "length"}:
                return chunk(reason="length" if self.question == "length" else "stop")
            return chunk("末段")
        if self.index == 3:
            if self.question in {"empty", "length"}:
                raise StopAsyncIteration
            return chunk(reason="stop")
        raise StopAsyncIteration

    async def close(self):
        self.closed.set()


async def read_frame(lines):
    fields = {}
    async for line in lines:
        if not line:
            if fields:
                return fields["event"], json.loads(fields["data"])
        else:
            key, _, value = line.partition(":")
            fields[key] = value.lstrip(" ")
    raise AssertionError("HTTP stream ended before a complete SSE frame")


async def wait_for_frame(lines, event, stage=None):
    while True:
        kind, data = await asyncio.wait_for(read_frame(lines), 2)
        if kind == event and (stage is None or data.get("stage") == stage):
            return data


class LoopbackStreamTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.stack = ExitStack()
        self.gates = {}
        self.closed = {}
        self.model_calls = []
        self.model_messages = {}
        self.legacy_calls = []
        self.prepare_calls = []
        self.retrieval_entered = threading.Event()
        self.retrieval_release = threading.Event()
        self.retrieval_finished = threading.Event()
        self.preflight_entered = threading.Event()
        self.preflight_release = threading.Event()
        self.preflight_finished = threading.Event()
        self.response_finished = asyncio.Event()
        self.block_preflight = False
        self.block_retrieval = False
        self.retry_first = False
        self.fixture_source = {
            "file_id": "fixture-file", "file_name": "fixture.md",
            "chunk_id": "fixture-chunk", "content": "fixture only", "final_score": 0.9,
        }

        owner = self

        class FakeStore:
            def list_collections(self):
                if owner.block_preflight:
                    owner.preflight_entered.set()
                    owner.preflight_release.wait(5)
                    owner.preflight_finished.set()
                return ["kb"]

            def get_chunk_count(self, collection):
                return 1

        class FakeRetriever:
            def hybrid_search(self, question, collection, top_k):
                owner.prepare_calls.append(question)
                if owner.block_retrieval:
                    owner.retrieval_entered.set()
                    owner.retrieval_release.wait(5)
                    owner.retrieval_finished.set()
                return [] if question == "no-match" else [owner.fixture_source]

        class FakeLegacyModel:
            def generate_answer(self, system_prompt, history_text, context_text, question):
                owner.legacy_calls.append((history_text, context_text, question))
                return "legacy fixture"

        async def create(**kwargs):
            question = kwargs["messages"][-1]["content"].split("## 用户问题\n")[-1]
            owner.model_calls.append(question)
            owner.model_messages[question] = kwargs["messages"][-1]["content"]
            if owner.retry_first:
                raise TimeoutError("controlled transient")
            gate = owner.gates.setdefault(question, asyncio.Event())
            closed = owner.closed.setdefault(question, asyncio.Event())
            return FakeStream(question, gate, closed)

        sdk = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        original_response_call = _ClosingStreamingResponse.__call__

        async def observe_response(response, scope, receive, send):
            try:
                await original_response_call(response, scope, receive, send)
            finally:
                owner.response_finished.set()

        self.stack.enter_context(patch("app.api.query.ChromaVectorStore", FakeStore))
        self.stack.enter_context(patch("app.api.query.QAService", side_effect=lambda vector_store:
                                       QAService(vector_store, FakeRetriever(), FakeLegacyModel())))
        self.stack.enter_context(patch.object(AsyncDeepSeekClient, "_get_client", return_value=(sdk, False)))
        self.stack.enter_context(patch.object(_ClosingStreamingResponse, "__call__", observe_response))

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(128)
        self.socket.setblocking(False)
        self.url = f"http://127.0.0.1:{self.socket.getsockname()[1]}"
        config = uvicorn.Config(app, lifespan="off", log_level="critical", access_log=False)
        self.server = uvicorn.Server(config)
        self.server_task = asyncio.create_task(self.server.serve(sockets=[self.socket]))
        for _ in range(200):
            if self.server.started:
                break
            await asyncio.sleep(0.01)
        self.assertTrue(self.server.started, "loopback server did not start")
        self.client = httpx.AsyncClient(base_url=self.url, trust_env=False, timeout=3)

    async def asyncTearDown(self):
        self.retrieval_release.set()
        self.preflight_release.set()
        for gate in self.gates.values():
            gate.set()
        await self.client.aclose()
        self.server.should_exit = True
        await asyncio.wait_for(self.server_task, 5)
        self.socket.close()
        self.stack.close()

    def request(self, question="q"):
        return self.client.build_request("POST", "/api/query/stream", json={
            "question": question, "collection_name": "kb", "history": []})

    async def test_first_delta_arrives_before_upstream_releases_and_done_has_sources(self):
        response = await self.client.send(self.request(), stream=True)
        self.assertEqual(response.status_code, 200)
        lines = response.aiter_lines()
        first = await wait_for_frame(lines, "delta")
        self.assertEqual(first["text"], "首段:q")
        self.assertFalse(self.gates["q"].is_set())
        self.assertFalse(self.closed["q"].is_set())
        self.gates["q"].set()
        self.assertEqual((await wait_for_frame(lines, "delta"))["text"], "末段")
        done = await wait_for_frame(lines, "done")
        self.assertEqual(done["sources"][0]["file_id"], "fixture-file")
        await asyncio.wait_for(self.closed["q"].wait(), 2)
        await response.aclose()

    async def test_disconnect_during_model_read_closes_upstream(self):
        response = await self.client.send(self.request(), stream=True)
        await wait_for_frame(response.aiter_lines(), "delta")
        await response.aclose()
        await asyncio.wait_for(self.closed["q"].wait(), 2)
        self.assertEqual(self.model_calls, ["q"])

    async def test_disconnect_during_blocked_retrieval_never_starts_model(self):
        self.block_retrieval = True
        response = await self.client.send(self.request(), stream=True)
        await wait_for_frame(response.aiter_lines(), "status", "retrieving")
        self.assertTrue(await asyncio.to_thread(self.retrieval_entered.wait, 2))
        await response.aclose()
        await asyncio.wait_for(self.response_finished.wait(), 2)
        self.retrieval_release.set()
        self.assertTrue(await asyncio.to_thread(self.retrieval_finished.wait, 2))
        await asyncio.sleep(0.05)
        self.assertEqual(self.model_calls, [])

    async def test_disconnect_during_retry_wait_does_not_start_next_attempt(self):
        self.retry_first = True
        response = await self.client.send(self.request(), stream=True)
        await wait_for_frame(response.aiter_lines(), "status", "retrying")
        await response.aclose()
        await asyncio.sleep(1.3)
        self.assertEqual(self.model_calls, ["q"])
        self.assertEqual(self.prepare_calls, ["q"])

    async def test_two_streams_are_independent_when_one_disconnects(self):
        first, second = await asyncio.gather(
            self.client.send(self.request("one"), stream=True),
            self.client.send(self.request("two"), stream=True),
        )
        lines1, lines2 = first.aiter_lines(), second.aiter_lines()
        await asyncio.gather(wait_for_frame(lines1, "delta"), wait_for_frame(lines2, "delta"))
        await first.aclose()
        await asyncio.wait_for(self.closed["one"].wait(), 2)
        self.assertFalse(self.closed["two"].is_set())
        self.gates["two"].set()
        await wait_for_frame(lines2, "delta")
        self.assertEqual((await wait_for_frame(lines2, "done"))["sources"][0]["file_id"], "fixture-file")
        await asyncio.wait_for(self.closed["two"].wait(), 2)
        await second.aclose()

    async def test_old_json_endpoint_remains_compatible(self):
        response = await self.client.post("/api/query", json={"question": "old", "collection_name": "kb"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "legacy fixture", "sources": [{
            "file_id": "fixture-file", "file_name": "fixture.md", "chunk_id": "fixture-chunk",
            "relevance_score": 0.9}],
                                          "query": "old", "collection_name": "kb"})
        self.assertEqual(self.legacy_calls, [("", "[来源: fixture.md]\nfixture only", "old")])

    async def test_no_match_calls_model_and_returns_empty_sources(self):
        response = await self.client.send(self.request("no-match"), stream=True)
        lines = response.aiter_lines()
        await wait_for_frame(lines, "delta")
        self.gates["no-match"].set()
        self.assertEqual((await wait_for_frame(lines, "done"))["sources"], [])
        self.assertEqual(self.model_calls, ["no-match"])
        self.assertIn("## 参考文档\n（知识库中暂无相关文档）\n\n## 用户问题\nno-match",
                      self.model_messages["no-match"])
        await response.aclose()

    async def test_length_limit_and_empty_answer_are_not_done(self):
        for question in ("length", "empty"):
            response = await self.client.send(self.request(question), stream=True)
            lines = response.aiter_lines()
            await wait_for_frame(lines, "status", "generating")
            if question == "length":
                await wait_for_frame(lines, "delta")
            # The empty case may still be awaiting the first read.
            while question not in self.gates:
                await asyncio.sleep(0.001)
            self.gates[question].set()
            incomplete = await wait_for_frame(lines, "incomplete")
            self.assertEqual(incomplete["reason"], question)
            await asyncio.wait_for(self.closed[question].wait(), 2)
            await response.aclose()

    async def test_short_overall_timeout_after_delta_sends_error_and_closes(self):
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.4):
            response = await self.client.send(self.request("slow"), stream=True)
            lines = response.aiter_lines()
            await wait_for_frame(lines, "delta")
            error = await wait_for_frame(lines, "error")
            self.assertEqual(error["code"], "QUERY_TIMEOUT")
            await asyncio.wait_for(self.closed["slow"].wait(), 2)
            await response.aclose()

    async def test_short_overall_timeout_before_response_is_http_504(self):
        self.block_preflight = True
        with patch.object(settings, "STREAM_QUERY_TIMEOUT", 0.3):
            response = await self.client.send(self.request(), stream=True)
            self.assertTrue(self.preflight_entered.is_set())
            self.assertFalse(self.preflight_release.is_set())
            self.assertEqual(response.status_code, 504)
            data = json.loads((await response.aread()).decode())
            self.assertEqual(data["error"]["code"], "QUERY_TIMEOUT")
            self.preflight_release.set()
            self.assertTrue(await asyncio.to_thread(self.preflight_finished.wait, 2))
            await asyncio.sleep(0.05)
            self.assertEqual(self.model_calls, [])
            await response.aclose()

    async def test_disconnect_during_preflight_does_not_start_model(self):
        self.block_preflight = True
        pending = asyncio.create_task(self.client.send(self.request(), stream=True))
        self.assertTrue(await asyncio.to_thread(self.preflight_entered.wait, 2))
        pending.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await pending
        await asyncio.sleep(0.1)
        self.preflight_release.set()
        self.assertTrue(await asyncio.to_thread(self.preflight_finished.wait, 2))
        await asyncio.sleep(0.4)
        self.assertEqual(self.model_calls, [])


if __name__ == "__main__":
    unittest.main()
