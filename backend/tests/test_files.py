"""API tests for the file-list endpoint."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.vector_store import ChunkRecord
from app.main import app


class FileListEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.store = Mock()
        self.store.list_collections.return_value = ["test-kb"]

    def _get(self, collection_name: str):
        return self.client.get(
            "/api/files", params={"collection_name": collection_name}
        )

    @staticmethod
    def _chunk(
        chunk_id: str,
        chunk_index: int,
        content: str,
        file_id: str = "file-1",
        file_name: str = "doc.md",
    ) -> ChunkRecord:
        return ChunkRecord(
            chunk_id=chunk_id,
            file_id=file_id,
            file_name=file_name,
            collection_name="test-kb",
            chunk_index=chunk_index,
            content=content,
        )

    def test_populated_collection_returns_file_records(self) -> None:
        self.store.get_files.return_value = [
            {
                "file_id": "file-1",
                "file_name": "one.md",
                "size": 100,
                "upload_time": "2026-08-10T14:30:00",
                "chunk_count": 2,
                "status": "SUCCESS",
            },
            {
                "file_id": "file-2",
                "file_name": "two.pdf",
                "size": 200,
                "upload_time": "2026-08-11T14:30:00",
                "chunk_count": 3,
                "status": "SUCCESS_WITH_WARNINGS",
            },
            {
                "file_id": "file-3",
                "file_name": "three.txt",
                "size": 300,
                "upload_time": "2026-08-12T14:30:00",
                "chunk_count": 1,
                "status": "SUCCESS",
            },
        ]

        with patch(
            "app.api.files.ChromaVectorStore", return_value=self.store
        ):
            response = self._get("test-kb")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "collection_name": "test-kb",
                "files": self.store.get_files.return_value,
            },
        )
        self.store.list_collections.assert_called_once_with()
        self.store.get_files.assert_called_once_with("test-kb")

    def test_empty_collection_returns_empty_files(self) -> None:
        self.store.get_files.return_value = []

        with patch(
            "app.api.files.ChromaVectorStore", return_value=self.store
        ):
            response = self._get("test-kb")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"collection_name": "test-kb", "files": []}
        )
        self.store.get_files.assert_called_once_with("test-kb")

    def test_missing_collection_returns_404_without_getting_files(self) -> None:
        self.store.list_collections.return_value = []

        with patch(
            "app.api.files.ChromaVectorStore", return_value=self.store
        ):
            response = self._get("missing-kb")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "COLLECTION_NOT_FOUND"
        )
        self.store.get_files.assert_not_called()

    def test_preview_reconstructs_chunks_in_chunk_index_order(self) -> None:
        self.store.get_chunks_by_file.return_value = [
            self._chunk("chunk-2", 2, "last"),
            self._chunk("chunk-0", 0, "first"),
            self._chunk("chunk-1", 1, "middle"),
        ]

        with patch(
            "app.api.files.ChromaVectorStore", return_value=self.store
        ):
            response = self.client.get(
                "/api/files/file-1/preview",
                params={"collection_name": "test-kb"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "file_id": "file-1",
                "file_name": "doc.md",
                "collection_name": "test-kb",
                "content": "first\n\nmiddle\n\nlast",
                "preview_chars": len("first\n\nmiddle\n\nlast"),
                "total_chars": len("first\n\nmiddle\n\nlast"),
            },
        )
        self.store.get_chunks_by_file.assert_called_once_with(
            "test-kb", "file-1"
        )

    def test_preview_truncates_content_and_keeps_full_total(self) -> None:
        first = "a" * 3000
        second = "b" * 3000
        self.store.get_chunks_by_file.return_value = [
            self._chunk("chunk-0", 0, first),
            self._chunk("chunk-1", 1, second),
        ]

        with patch(
            "app.api.files.ChromaVectorStore", return_value=self.store
        ):
            response = self.client.get(
                "/api/files/file-1/preview",
                params={"collection_name": "test-kb"},
            )

        body = response.json()
        full_content = f"{first}\n\n{second}"
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["content"], full_content[:5000])
        self.assertEqual(body["preview_chars"], 5000)
        self.assertEqual(body["total_chars"], len(full_content))

    def test_preview_missing_collection_returns_404_without_chunk_lookup(
        self,
    ) -> None:
        self.store.list_collections.return_value = []

        with patch(
            "app.api.files.ChromaVectorStore", return_value=self.store
        ):
            response = self.client.get(
                "/api/files/file-1/preview",
                params={"collection_name": "missing-kb"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "COLLECTION_NOT_FOUND"
        )
        self.store.get_chunks_by_file.assert_not_called()

    def test_preview_missing_file_returns_404(self) -> None:
        self.store.get_chunks_by_file.return_value = []

        with patch(
            "app.api.files.ChromaVectorStore", return_value=self.store
        ):
            response = self.client.get(
                "/api/files/missing-file/preview",
                params={"collection_name": "test-kb"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "FILE_NOT_FOUND"
        )
        self.store.get_chunks_by_file.assert_called_once_with(
            "test-kb", "missing-file"
        )

    def test_delete_file_removes_disk_and_storage_in_order(self) -> None:
        self.store.get_files.return_value = [
            {"file_id": "file-1", "file_name": "doc.md"}
        ]
        events = []
        self.store.delete_by_file.side_effect = (
            lambda collection, file_id: events.append("chroma") or 15
        )

        with (
            patch(
                "app.api.files.ChromaVectorStore", return_value=self.store
            ),
            patch(
                "app.api.files.Path.unlink",
                side_effect=lambda **kwargs: events.append("disk"),
            ) as unlink,
            patch(
                "app.api.files.invalidate_keyword_index",
                side_effect=lambda collection: events.append("index"),
            ),
        ):
            response = self.client.delete(
                "/api/files/file-1",
                params={"collection_name": "test-kb"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "message": "文件删除成功",
                "file_name": "doc.md",
                "collection_name": "test-kb",
            },
        )
        self.assertEqual(events, ["disk", "chroma", "index"])
        unlink.assert_called_once_with(missing_ok=True)
        self.store.get_files.assert_called_once_with("test-kb")
        self.store.delete_by_file.assert_called_once_with("test-kb", "file-1")

    def test_delete_missing_collection_returns_404_without_cascade(self) -> None:
        self.store.list_collections.return_value = []

        with (
            patch(
                "app.api.files.ChromaVectorStore", return_value=self.store
            ),
            patch("app.api.files.invalidate_keyword_index") as invalidate,
        ):
            response = self.client.delete(
                "/api/files/file-1",
                params={"collection_name": "missing-kb"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "COLLECTION_NOT_FOUND"
        )
        self.store.get_files.assert_not_called()
        self.store.delete_by_file.assert_not_called()
        invalidate.assert_not_called()

    def test_delete_missing_file_returns_404_without_cascade(self) -> None:
        self.store.get_files.return_value = [
            {"file_id": "other-file", "file_name": "other.md"}
        ]

        with (
            patch(
                "app.api.files.ChromaVectorStore", return_value=self.store
            ),
            patch("app.api.files.invalidate_keyword_index") as invalidate,
            patch("app.api.files._delete_raw_file") as delete_raw,
        ):
            response = self.client.delete(
                "/api/files/missing-file",
                params={"collection_name": "test-kb"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "FILE_NOT_FOUND")
        self.store.get_files.assert_called_once_with("test-kb")
        self.store.delete_by_file.assert_not_called()
        delete_raw.assert_not_called()
        invalidate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
