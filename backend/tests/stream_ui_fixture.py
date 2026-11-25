"""Loopback-only FastAPI fixture for the frontend stream integration script.

All stores, retrievers and model SDK objects are in memory. This process never
reads ChromaDB, local documents or calls an external model service.
"""
import asyncio
import json
import socket
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app
from app.services.qa import AsyncDeepSeekClient, QAService


def emit(event, **data):
    print(json.dumps({"event": event, **data}, ensure_ascii=True), flush=True)


def chunk(text=None, reason=None):
    return {"choices": [{"delta": {"content": text}, "finish_reason": reason}]}


async def main():
    gates = {}

    class FakeStore:
        def list_collections(self):
            return ["kb", "empty-kb"]

        def get_chunk_count(self, collection):
            return 0 if collection == "empty-kb" else 1

    class FakeRetriever:
        def hybrid_search(self, question, collection, top_k):
            if question == "no-match":
                return []
            return [{"file_id": "fixture-file", "file_name": "fixture.md",
                     "chunk_id": "fixture-chunk", "content": "fixture only", "final_score": 0.9}]

    class FakeStream:
        def __init__(self, question):
            self.question = question
            self.index = 0
            self.gate = gates.setdefault(question, asyncio.Event())

        def __aiter__(self):
            return self

        async def __anext__(self):
            self.index += 1
            if self.index == 1:
                return chunk("  \n" if self.question == "empty" else f"首段:{self.question}")
            if self.index == 2:
                await self.gate.wait()
                if self.question in {"empty", "length"}:
                    return chunk(reason="length" if self.question == "length" else "stop")
                return chunk("末段")
            if self.index == 3 and self.question not in {"empty", "length"}:
                return chunk(reason="stop")
            raise StopAsyncIteration

        async def close(self):
            emit("closed", question=self.question)

    async def create(**kwargs):
        message = kwargs["messages"][-1]["content"]
        question = message.split("## 用户问题\n")[-1]
        emit("model", question=question, message=message)
        return FakeStream(question)

    sdk = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    sock.setblocking(False)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, lifespan="off", log_level="critical", access_log=False))
    with patch("app.api.query.ChromaVectorStore", FakeStore), \
         patch("app.api.query.QAService", side_effect=lambda vector_store:
               QAService(vector_store, FakeRetriever())), \
         patch.object(AsyncDeepSeekClient, "_get_client", return_value=(sdk, False)):
        task = asyncio.create_task(server.serve(sockets=[sock]))
        try:
            for _ in range(300):
                if server.started:
                    break
                await asyncio.sleep(0.01)
            if not server.started:
                raise RuntimeError("fixture server failed to start")
            emit("ready", port=port)
            while True:
                command = await asyncio.to_thread(sys.stdin.readline)
                if not command or command.strip() == "stop":
                    break
                action, _, question = command.strip().partition(" ")
                if action == "release":
                    gates.setdefault(question, asyncio.Event()).set()
        finally:
            for gate in gates.values():
                gate.set()
            server.should_exit = True
            await asyncio.wait_for(task, timeout=5)
            sock.close()


if __name__ == "__main__":
    asyncio.run(main())
