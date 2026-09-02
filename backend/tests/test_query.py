"""API tests for the knowledge QA endpoint."""

import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.main import app


class QueryEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.store = Mock()
        self.store.list_collections.return_value = ["kb"]
        self.service = Mock()
        self.service.answer.return_value = {
            "answer": "### Python\n\nPython is a language.",
            "sources": [
                {
                    "file_id": "file-1",
                    "file_name": "notes.md",
                    "chunk_id": "chunk-1",
                    "relevance_score": 0.9,
                }
            ],
            "query": "什么是 Python",
            "collection_name": "kb",
        }

    def _post(self, payload: object):
        return self.client.post(
            "/api/query",
            json=payload,
        )

    def _patch_dependencies(self):
        return patch(
            "app.api.query.ChromaVectorStore", return_value=self.store
        ), patch("app.api.query.QAService", return_value=self.service)

    def test_valid_query_returns_exact_response_shape(self) -> None:
        with self._patch_dependencies()[0], self._patch_dependencies()[1]:
            response = self._post(
                {
                    "question": "什么是 Python",
                    "collection_name": "kb",
                    "top_k": 5,
                    "history": [
                        {"role": "user", "content": "你好"},
                        {"role": "assistant", "content": "您好！"},
                    ],
                }
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.service.answer.return_value)
        self.store.list_collections.assert_called_once_with()
        self.service.answer.assert_called_once_with(
            "什么是 Python",
            "kb",
            5,
            [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "您好！"},
            ],
        )

    def test_omitted_optional_fields_use_spec_defaults(self) -> None:
        with self._patch_dependencies()[0], self._patch_dependencies()[1]:
            response = self._post(
                {"question": "问题", "collection_name": "kb"}
            )

        self.assertEqual(response.status_code, 200)
        self.service.answer.assert_called_once_with("问题", "kb", 5, [])

    def test_no_matching_content_returns_200_with_empty_sources(self) -> None:
        self.service.answer.return_value = {
            "answer": "当前知识库中没有足够的信息来回答这个问题",
            "sources": [],
            "query": "量子计算",
            "collection_name": "kb",
        }

        with self._patch_dependencies()[0], self._patch_dependencies()[1]:
            response = self._post(
                {"question": "量子计算", "collection_name": "kb"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sources"], [])

    def test_collection_empty_maps_to_409(self) -> None:
        self.service.answer.side_effect = AppError("COLLECTION_EMPTY")

        with self._patch_dependencies()[0], self._patch_dependencies()[1]:
            response = self._post(
                {"question": "问题", "collection_name": "kb"}
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "COLLECTION_EMPTY")

    def test_llm_and_embedding_errors_use_unified_error_mapping(self) -> None:
        for error_code, status_code in (
            ("LLM_NOT_CONFIGURED", 500),
            ("LLM_AUTH_FAILED", 500),
            ("LLM_UNAVAILABLE", 502),
            ("LLM_RESPONSE_ERROR", 500),
            ("EMBEDDING_MODEL_ERROR", 500),
        ):
            with self.subTest(error_code=error_code):
                self.service.answer.side_effect = AppError(error_code)
                with self._patch_dependencies()[0], self._patch_dependencies()[1]:
                    response = self._post(
                        {"question": "问题", "collection_name": "kb"}
                    )

                self.assertEqual(response.status_code, status_code)
                self.assertEqual(response.json()["error"]["code"], error_code)

    def test_missing_collection_returns_404_without_calling_service(self) -> None:
        self.store.list_collections.return_value = []

        with self._patch_dependencies()[0], self._patch_dependencies()[1]:
            response = self._post(
                {"question": "问题", "collection_name": "missing"}
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"]["code"], "COLLECTION_NOT_FOUND"
        )
        self.service.answer.assert_not_called()

    def test_invalid_top_k_returns_400_without_storage_or_service_work(self) -> None:
        for top_k in (0, 21, -1):
            with self.subTest(top_k=top_k):
                self.store.reset_mock()
                self.service.reset_mock()
                with self._patch_dependencies()[0], self._patch_dependencies()[1]:
                    response = self._post(
                        {
                            "question": "问题",
                            "collection_name": "kb",
                            "top_k": top_k,
                        }
                    )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "INVALID_TOP_K"
                )
                self.store.list_collections.assert_not_called()
                self.service.answer.assert_not_called()

    def test_empty_question_or_collection_returns_invalid_query(self) -> None:
        payloads = [
            {"question": "", "collection_name": "kb"},
            {"question": "   ", "collection_name": "kb"},
            {"question": "问题", "collection_name": ""},
            {"question": "问题", "collection_name": "   "},
            {"collection_name": "kb"},
            {"question": "问题"},
        ]

        for payload in payloads:
            with self.subTest(payload=payload):
                self.store.reset_mock()
                self.service.reset_mock()
                with self._patch_dependencies()[0], self._patch_dependencies()[1]:
                    response = self._post(payload)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "INVALID_QUERY"
                )
                self.store.list_collections.assert_not_called()
                self.service.answer.assert_not_called()

    def test_invalid_history_returns_400_without_storage_or_service_work(self) -> None:
        payloads = [
            {"question": "问题", "collection_name": "kb", "history": None},
            {"question": "问题", "collection_name": "kb", "history": {}},
            {
                "question": "问题",
                "collection_name": "kb",
                "history": [{"content": "missing role"}],
            },
            {
                "question": "问题",
                "collection_name": "kb",
                "history": [{"role": "system", "content": "invalid"}],
            },
            {
                "question": "问题",
                "collection_name": "kb",
                "history": [{"role": "user", "content": 42}],
            },
        ]

        for payload in payloads:
            with self.subTest(payload=payload):
                self.store.reset_mock()
                self.service.reset_mock()
                with self._patch_dependencies()[0], self._patch_dependencies()[1]:
                    response = self._post(payload)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "INVALID_HISTORY_FORMAT"
                )
                self.store.list_collections.assert_not_called()
                self.service.answer.assert_not_called()

    def test_non_object_body_returns_invalid_query(self) -> None:
        for payload in (None, [], "query"):
            with self.subTest(payload=payload):
                self.store.reset_mock()
                self.service.reset_mock()
                with self._patch_dependencies()[0], self._patch_dependencies()[1]:
                    response = self._post(payload)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "INVALID_QUERY"
                )


if __name__ == "__main__":
    unittest.main()
