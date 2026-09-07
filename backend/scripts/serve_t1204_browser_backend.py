"""Serve an isolated deterministic backend for T1204 browser acceptance.

This is a local verification harness, not application runtime code.  It uses
real FastAPI, ingestion, retrieval, ChromaDB, and filesystem behavior while
substituting only the unavailable embedding model and external LLM boundary.
The temporary persistence tree is removed when the server exits.
"""

from __future__ import annotations

import hashlib
import math
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch


_BACKEND = Path(__file__).resolve().parents[1]


class Matrix:
    def __init__(self, rows: list[list[float]]) -> None:
        self.rows = rows

    def tolist(self) -> list[list[float]]:
        return self.rows


class DeterministicSentenceTransformer:
    """Normalized 512-dimensional replacement for deterministic UI checks."""

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    def encode(self, texts, normalize_embeddings=False):
        rows: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(str(text).encode("utf-8")).digest()
            first = int.from_bytes(digest[:2], "big") % 512
            second = int.from_bytes(digest[2:4], "big") % 512
            vector = [0.0] * 512
            vector[first] += 1.0
            vector[second] += 0.5
            norm = math.sqrt(sum(value * value for value in vector))
            if normalize_embeddings and norm:
                vector = [value / norm for value in vector]
            rows.append(vector)
        return Matrix(rows)


def main() -> int:
    probe_root = Path(tempfile.mkdtemp(prefix="t1204_browser_")).resolve()
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["UPLOAD_DIR"] = str(probe_root / "uploads")
    os.environ["CHROMA_PERSIST_DIR"] = str(probe_root / "chroma")
    os.environ["DEEPSEEK_API_KEY"] = "t1204-test-double"
    sys.path.insert(0, str(_BACKEND))

    fake_sentence_transformers = types.ModuleType("sentence_transformers")
    fake_sentence_transformers.SentenceTransformer = (
        DeterministicSentenceTransformer
    )

    try:
        with patch.dict(
            sys.modules, {"sentence_transformers": fake_sentence_transformers}
        ):
            from fastapi.testclient import TestClient
            import uvicorn

            import app.services.embedding as embedding_mod
            import app.services.qa as qa_mod
            from app.main import app

            embedding_mod._model = None
            embedding_mod.get_model()

            def deterministic_answer(
                self,
                system_prompt: str,
                history_text: str,
                context_text: str,
                question: str,
            ) -> str:
                del self, system_prompt, history_text, context_text
                if question == "trigger500":
                    from app.core.errors import AppError

                    raise AppError("LLM_RESPONSE_ERROR")
                return (
                    "# 验收回答\n\n"
                    "**机器学习**是人工智能的一种方法。\n\n"
                    "- 回答由隔离式 T1204 LLM 边界生成\n"
                    "- 来源仍由真实检索链路组装"
                )

            qa_mod.DeepSeekClient.generate_answer = deterministic_answer

            client = TestClient(app, raise_server_exceptions=False)
            for name in ("browser-kb", "browser-empty"):
                response = client.post("/api/collections", json={"name": name})
                if response.status_code != 201:
                    raise RuntimeError(
                        f"failed to seed {name}: {response.status_code} {response.text}"
                    )

            upload = client.post(
                "/api/upload",
                data={"collection_name": "browser-kb"},
                files={
                    "file": (
                        "machine-learning.txt",
                        (
                            b"machinelearningtoken is a deterministic browser "
                            b"acceptance fact about machine learning."
                        ),
                        "text/plain",
                    )
                },
            )
            if upload.status_code != 200:
                raise RuntimeError(
                    f"failed to seed browser document: {upload.status_code} "
                    f"{upload.text}"
                )

            print(
                "T1204_BROWSER_READY "
                f"uploads={probe_root / 'uploads'} chroma={probe_root / 'chroma'}",
                flush=True,
            )
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
        return 0
    finally:
        shutil.rmtree(probe_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
