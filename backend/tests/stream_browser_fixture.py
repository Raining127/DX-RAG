"""Isolated browser fixture: production query router, in-memory dependencies only.

Only query, collection listing and file listing are exposed. All other project
routers are absent, so browser navigation cannot touch local user data.
"""
import asyncio
import json
import socket
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api.query import router as query_router
from app.core.errors import AppError
from app.services.qa import AsyncDeepSeekClient, QAService


def emit(event, **data):
    print(json.dumps({"event": event, **data}, ensure_ascii=True), flush=True)


def chunk(text=None, reason=None):
    return {"choices": [{"delta": {"content": text}, "finish_reason": reason}]}


async def main():
    gates = {}
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(AppError)
    async def app_error(_request: Request, error: AppError):
        return JSONResponse(status_code=error.http_status, content={
            "error": {"code": error.code, "message": error.message, "details": error.details}
        })

    @app.get("/api/collections")
    async def list_collections():
        return {"collections": [{"name": "kb", "file_count": 1},
                                {"name": "empty-kb", "file_count": 0}]}

    @app.get("/api/files")
    async def list_files(collection_name: str):
        return {"collection_name": collection_name, "files": []}

    app.include_router(query_router, prefix="/api")

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
