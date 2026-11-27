"""Opt-in live streaming check using only a synthetic document and isolated storage.

Run explicitly from backend: ``python -B tests/stream_live_check.py``.
This sends the synthetic document, questions and completed history to DeepSeek
and may incur charges. It never reads project documents or the existing database.
"""

import asyncio
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
# A missing or incomplete local embedding model must never trigger a download.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# App/transport exceptions may contain request details; the report below emits
# only fixed diagnostic codes and explicitly synthetic answer content.
logging.disable(logging.CRITICAL)

from app.core.config import settings


COLLECTION = "sqa-live-fixture"
FILENAME = "synthetic-notes.md"
DOCUMENT = """# 虚构晨星项目的测试资料

本文全部内容仅用于软件测试，与真实组织和个人无关。

## 晨星项目例会
晨星项目的例会固定在每周星期二举行，会议开始时间是上午十点整。
参加者需要准备虚构项目的进度摘要。
"""
QUESTIONS = (
    "虚构晨星项目的例会固定在星期几举行？",
    "晨星项目那次例会通常在几点开始？",
    "请解释虚构晨星项目的例会安排，并列出参加者需要准备什么。",
)


class CheckFailure(Exception):
    """A deliberately sanitized diagnostic for this opt-in check."""


def validate_root(root):
    """Restrict every worker and cleanup to one directly owned temp directory."""
    temp_parent = Path(tempfile.gettempdir()).resolve(strict=True)
    if not root.is_absolute() or root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise CheckFailure("isolated temporary path validation failed")
    resolved = root.resolve(strict=True)
    if resolved != root or resolved.parent != temp_parent or not resolved.name.startswith("dx-rag-sqa10-"):
        raise CheckFailure("isolated temporary path validation failed")
    return resolved


def check_prerequisites():
    """Return the local model path; no network or storage initialization occurs."""
    key = settings.get_deepseek_key()
    if not key or not key.strip():
        print("NOT_RUN: DeepSeek API key is not configured", flush=True)
        return None
    model = Path(settings.EMBED_MODEL).expanduser()
    if not model.is_absolute():
        model = BACKEND / model
    model = model.resolve()
    weights = (model / "model.safetensors", model / "pytorch_model.bin")
    if not model.is_dir() or not (model / "config.json").is_file() or not any(p.is_file() for p in weights):
        print("NOT_RUN: complete local embedding model not found", flush=True)
        return None
    return model


async def frames(response):
    fields = {}
    async for line in response.aiter_lines():
        if not line:
            if fields:
                yield fields.get("event", "message"), json.loads(fields.get("data", "{}"))
                fields = {}
        elif not line.startswith(":"):
            key, _, value = line.partition(":")
            fields[key] = value[1:] if value.startswith(" ") else value


async def main(model, root):
    # The application reads the settings singleton everywhere; override it
    # before any ChromaVectorStore or upload path can be constructed.
    import httpx
    import uvicorn
    from app.main import app
    from app.services.qa import AsyncDeepSeekClient

    root = validate_root(Path(root))
    settings.CHROMA_PERSIST_DIR = str(root / "chroma")
    settings.UPLOAD_DIR = str(root / "uploads")
    settings.EMBED_MODEL = str(model)
    settings.LLM_MAX_RETRIES = 0

    closed = asyncio.Event()
    original_close = AsyncDeepSeekClient._close_stream

    async def observed_close(stream):
        await original_close(stream)
        closed.set()

    # Wrapping cleanup observes the real SDK stream without altering it.
    AsyncDeepSeekClient._close_stream = staticmethod(observed_close)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    sock.setblocking(False)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, lifespan="off", log_level="critical", access_log=False))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(500):
            if server.started:
                break
            if task.done():
                raise CheckFailure("local backend did not start")
            await asyncio.sleep(0.01)
        if not server.started:
            raise CheckFailure("local backend did not start")
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}",
                                     timeout=180, trust_env=False) as client:
            created = await client.post("/api/collections", json={"name": COLLECTION})
            if created.status_code != 201:
                raise CheckFailure("isolated collection creation failed")
            upload = await client.post(
                "/api/upload", data={"collection_name": COLLECTION},
                files={"file": (FILENAME, DOCUMENT.encode("utf-8"), "text/markdown")},
            )
            if upload.status_code != 200:
                raise CheckFailure("synthetic document ingestion failed")
            file_id = upload.json()["file_id"]
            print("PASS: synthetic document ingested into isolated ChromaDB", flush=True)

            history = []
            for index, question in enumerate(QUESTIONS):
                payload = {"question": question, "collection_name": COLLECTION, "history": history}
                if index == 2:
                    closed.clear()
                async with client.stream("POST", "/api/query/stream", json=payload) as response:
                    if response.status_code != 200:
                        raise CheckFailure(f"question {index + 1}: pre-stream HTTP {response.status_code}")
                    answer = ""
                    deltas = 0
                    terminal = None
                    open_at_stop = False
                    async for event, data in frames(response):
                        if event == "delta":
                            answer += data["text"]
                            deltas += 1
                            if index == 2:
                                open_at_stop = not closed.is_set()
                                break
                        elif event in {"done", "incomplete", "error"}:
                            terminal = (event, data)
                            break
                if index == 2:
                    if not deltas:
                        raise CheckFailure("stop check did not receive a text delta")
                    await asyncio.wait_for(closed.wait(), timeout=10)
                    if open_at_stop:
                        print("OBSERVED: upstream was open at stop request and subsequently closed; "
                              "causation and provider billing are not verified", flush=True)
                    else:
                        print("INCONCLUSIVE: upstream was already closed before the stop request; "
                              "cancellation and provider billing are not verified", flush=True)
                    break
                if not terminal or terminal[0] != "done":
                    code = terminal[1].get("code", "") if terminal else ""
                    if code not in {"LLM_AUTH_FAILED", "LLM_NOT_CONFIGURED", "LLM_UNAVAILABLE",
                                    "LLM_RESPONSE_ERROR", "QUERY_TIMEOUT", "EMBEDDING_MODEL_ERROR"}:
                        code = "UNKNOWN"
                    raise CheckFailure(f"question {index + 1}: stream did not complete ({code})")
                sources = terminal[1].get("sources", [])
                if not answer.strip() or not any(source.get("file_id") == file_id for source in sources):
                    raise CheckFailure(f"question {index + 1}: answer or synthetic source missing")
                # Semantic output is reported, not assumed: real models may vary.
                print(f"PASS: question {index + 1}; deltas={deltas}; synthetic source present", flush=True)
                print("ANSWER: " + answer[:500].replace("\r", " ").replace("\n", " "), flush=True)
                history.extend([{"role": "user", "content": question},
                                {"role": "assistant", "content": answer}])
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(task, timeout=15)
        finally:
            sock.close()
            AsyncDeepSeekClient._close_stream = staticmethod(original_close)

def run_isolated(configured_model=None, cleanup_check=False, fail_worker=False):
    """Run the database in a child; clean only after its handles are released."""
    parent = Path(tempfile.gettempdir()).resolve(strict=True)
    root = Path(tempfile.mkdtemp(prefix="dx-rag-sqa10-", dir=str(parent))).resolve(strict=True)
    validate_root(root)
    try:
        if cleanup_check:
            # Simulate SQLite remaining open until process exit. No model, app,
            # network, user database, or credentials are used by this worker.
            code = ("import sqlite3,sys; db=sqlite3.connect(sys.argv[1]); "
                    "db.execute('create table fixture (id integer)'); db.commit()")
            if fail_worker:
                code += "; sys.exit(7)"
            command = [sys.executable, "-B", "-c", code, str(root / "fixture.sqlite")]
        else:
            command = [sys.executable, "-B", str(Path(__file__).resolve()),
                       "--worker", str(root), str(configured_model)]
        result = subprocess.run(command, cwd=str(BACKEND), timeout=900, check=False)
    finally:
        # On Windows, SQLite files can remain locked until the worker exits.
        # Revalidate the exact resolved target immediately before recursive removal.
        verified = validate_root(root)
        shutil.rmtree(verified)
    if cleanup_check:
        expected = 7 if fail_worker else 0
        if result.returncode != expected or root.exists():
            raise CheckFailure("cleanup fixture did not complete as expected")
        outcome = "failed" if fail_worker else "completed"
        print(f"PASS: {outcome} child SQLite process exited and isolated temporary directory removed", flush=True)
        return 0
    return result.returncode


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["--check-cleanup"]:
            sys.exit(run_isolated(cleanup_check=True))
        if sys.argv[1:] == ["--check-cleanup-failure"]:
            sys.exit(run_isolated(cleanup_check=True, fail_worker=True))
        if len(sys.argv) == 4 and sys.argv[1] == "--worker":
            worker_root = validate_root(Path(sys.argv[2]))
            worker_model = Path(sys.argv[3]).resolve(strict=True)
            asyncio.run(main(worker_model, worker_root))
        elif len(sys.argv) == 1:
            configured_model = check_prerequisites()
            if configured_model is None:
                sys.exit(2)
            sys.exit(run_isolated(configured_model))
        else:
            raise CheckFailure("invalid arguments")
    except CheckFailure as exc:
        print(f"NOT_PASSED: {exc}", flush=True)
        sys.exit(1)
    except Exception as exc:
        # No traceback/exception message: provider or transport errors can contain secrets.
        print(f"NOT_PASSED: live check failed ({type(exc).__name__})", flush=True)
        sys.exit(1)
