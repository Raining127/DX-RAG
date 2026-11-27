"""Isolated opt-in browser fixture using real retrieval and DeepSeek.

This binds only loopback and creates new temporary storage. It never reads
project documents or the existing knowledge base. The caller must stop this
process, then remove the printed verified temporary directory after exit.
"""
import asyncio
import logging
import os
import socket
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
logging.disable(logging.CRITICAL)

from app.core.config import settings

DOCUMENT = """# 虚构晨星项目的测试资料

本文仅用于软件测试，与真实组织或个人无关。

晨星项目例会固定每周星期二举行，开始时间是上午十点整。参加者需准备进度摘要。
"""


async def main():
    import httpx
    import uvicorn

    parent = Path(tempfile.gettempdir()).resolve(strict=True)
    root = Path(tempfile.mkdtemp(prefix="dx-rag-sqa10-browser-", dir=str(parent))).resolve(strict=True)
    if root.parent != parent or not root.name.startswith("dx-rag-sqa10-browser-"):
        raise RuntimeError("invalid isolated path")
    settings.CHROMA_PERSIST_DIR = str(root / "chroma")
    settings.UPLOAD_DIR = str(root / "uploads")
    settings.LLM_MAX_RETRIES = 0
    from app.main import app

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    sock.setblocking(False)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, lifespan="off", log_level="critical", access_log=False))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    print("TEST_ROOT=" + str(root), flush=True)
    try:
        for _ in range(500):
            if server.started:
                break
            if task.done():
                raise RuntimeError("backend failed to start")
            await asyncio.sleep(0.01)
        if not server.started:
            raise RuntimeError("backend failed to start")
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}", timeout=180, trust_env=False) as client:
            created = await client.post("/api/collections", json={"name": "sqa-live-browser"})
            if created.status_code != 201:
                raise RuntimeError("collection creation failed")
            uploaded = await client.post(
                "/api/upload", data={"collection_name": "sqa-live-browser"},
                files={"file": ("synthetic-notes.md", DOCUMENT.encode("utf-8"), "text/markdown")},
            )
            if uploaded.status_code != 200:
                raise RuntimeError("synthetic ingestion failed")
        print("READY_PORT=" + str(port), flush=True)
        await asyncio.to_thread(sys.stdin.readline)
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=15)
        sock.close()


if __name__ == "__main__":
    try:
        if not settings.get_deepseek_key() or not Path(settings.EMBED_MODEL).is_dir():
            raise RuntimeError("prerequisites missing")
        asyncio.run(main())
    except Exception as exc:
        print("FIXTURE_ERROR=" + type(exc).__name__, flush=True)
        sys.exit(1)
