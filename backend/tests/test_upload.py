"""Focused contract tests for the Phase 5 upload boundary."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.vector_store import ChunkRecord
from app.services.qa import KeywordRetriever


class UploadContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.store = Mock()
        self.store.list_collections.return_value = ["test-kb"]
        self.store.get_files.return_value = []

    def _post(self, file_name: str, content: bytes):
        return self.client.post(
            "/api/upload",
            files={"file": (file_name, content, "text/plain")},
            data={"collection_name": "test-kb"},
        )

    def test_single_invalid_inputs_remain_side_effect_free(self) -> None:
        cases = [
            ("../doc.pdf", b"payload", "INVALID_FILE_NAME"),
            ("doc.exe", b"payload", "UNSUPPORTED_FILE_TYPE"),
            ("empty.txt", b"", "EMPTY_FILE"),
        ]

        with patch(
            "app.api.upload.ChromaVectorStore", return_value=self.store
        ), patch("pathlib.Path.mkdir") as mkdir, patch(
            "pathlib.Path.write_bytes"
        ) as write_bytes:
            for file_name, content, code in cases:
                response = self._post(file_name, content)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"]["code"], code)

        mkdir.assert_not_called()
        write_bytes.assert_not_called()

    def test_multi_invalid_precedence_is_not_fixed_by_the_contract(self) -> None:
        with patch(
            "app.api.upload.ChromaVectorStore", return_value=self.store
        ), patch("pathlib.Path.write_bytes") as write_bytes:
            response = self._post("../doc.exe", b"payload")

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            response.json()["error"]["code"],
            {"INVALID_FILE_NAME", "UNSUPPORTED_FILE_TYPE"},
        )
        write_bytes.assert_not_called()

    def test_case_variant_is_duplicate_within_one_collection(self) -> None:
        self.store.get_files.return_value = [{"file_name": "doc.pdf"}]

        with patch(
            "app.api.upload.ChromaVectorStore", return_value=self.store
        ):
            response = self._post("DOC.PDF", b"payload")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "FILE_ALREADY_EXISTS")

    def test_failed_warnings_are_preserved_in_error_details(self) -> None:
        warnings = [{"page_number": 3, "error_code": "OCR_PAGE_FAILED"}]
        result = {
            "status": "FAILED",
            "file_id": "failed-file",
            "file_name": "failed.txt",
            "chunks_count": 0,
            "warnings": warnings,
        }

        with patch(
            "app.api.upload.ChromaVectorStore", return_value=self.store
        ), patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"), patch(
            "app.api.upload.IngestService.process", return_value=result
        ), patch("app.api.upload.invalidate_keyword_index") as invalidate:
            response = self._post("failed.txt", b"content")

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["error"]["code"], "FILE_PARSE_ERROR")
        self.assertEqual(body["error"]["details"]["warnings"], warnings)
        invalidate.assert_not_called()

    def test_failed_without_warnings_does_not_fabricate_warning_details(self) -> None:
        result = {
            "status": "FAILED",
            "file_id": "failed-file",
            "file_name": "failed.txt",
            "chunks_count": 0,
            "warnings": [],
        }

        with patch(
            "app.api.upload.ChromaVectorStore", return_value=self.store
        ), patch("pathlib.Path.mkdir"), patch("pathlib.Path.write_bytes"), patch(
            "app.api.upload.IngestService.process", return_value=result
        ):
            response = self._post("failed.txt", b"content")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["details"], {})

    def test_missing_file_uses_unified_validation_envelope(self) -> None:
        response = self.client.post(
            "/api/upload", data={"collection_name": "test-kb"}
        )

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["error"]["code"], "REQUEST_VALIDATION_ERROR")
        self.assertIn("validation_errors", body["error"]["details"])
        self.assertEqual(
            body["error"]["details"]["validation_errors"][0]["loc"],
            ["body", "file"],
        )

    def test_malformed_json_body_uses_unified_validation_envelope(self) -> None:
        response = self.client.post("/api/collections", json=[])

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"], "REQUEST_VALIDATION_ERROR"
        )

    def test_post_commit_invalidation_failure_keeps_upload_committed(self) -> None:
        class CommittedStore:
            def __init__(self) -> None:
                self.committed = False

            def list_collections(self):
                return ["test-kb"]

            def get_files(self, collection):
                if not self.committed:
                    return []
                return [
                    {
                        "file_id": "committed-file",
                        "file_name": "committed.txt",
                        "size": 9,
                        "upload_time": "2026-09-03T00:00:00+00:00",
                        "chunk_count": 1,
                        "status": "SUCCESS",
                    }
                ]

            def list_chunks(self, collection):
                return [
                    ChunkRecord(
                        chunk_id="committed-chunk",
                        file_id="committed-file",
                        file_name="committed.txt",
                        collection_name=collection,
                        chunk_index=0,
                        content="committed content",
                    )
                ]

        store = CommittedStore()
        result = {
            "status": "SUCCESS",
            "file_id": "committed-file",
            "file_name": "committed.txt",
            "chunks_count": 1,
            "warnings": [],
        }

        def process(*args, **kwargs):
            store.committed = True
            return result

        with patch(
            "app.api.upload.ChromaVectorStore", return_value=store
        ), patch("pathlib.Path.mkdir"), patch(
            "pathlib.Path.write_bytes", return_value=None
        ) as write_bytes, patch(
            "app.api.upload.IngestService.process", side_effect=process
        ), patch.object(
            KeywordRetriever,
            "_indexes",
            {"test-kb": {}},
        ), patch.object(
            KeywordRetriever,
            "_chunks",
            {"test-kb": {}},
        ), patch.object(
            KeywordRetriever,
            "_dirty_collections",
            set(),
        ), patch.object(
            KeywordRetriever,
            "invalidate",
            side_effect=RuntimeError("simulated index outage"),
        ) as invalidate:
            response = self._post("committed.txt", b"committed")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "SUCCESS")
            self.assertTrue(store.committed)
            self.assertIn("test-kb", KeywordRetriever._dirty_collections)

            recovered = KeywordRetriever(store).keyword_search(
                "test-kb", "committed", 5
            )

        write_bytes.assert_called_once_with(b"committed")
        invalidate.assert_called_once_with("test-kb")
        self.assertEqual([item["file_name"] for item in recovered], ["committed.txt"])
        self.assertEqual(store.get_files("test-kb")[0]["file_id"], "committed-file")


if __name__ == "__main__":
    unittest.main()
