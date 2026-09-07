"""Focused tests for the frozen 512-dimensional embedding contract."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.core.errors import AppError
from app.services import embedding


class _Matrix:
    def __init__(self, rows: list[list[float]]) -> None:
        self._rows = rows

    def tolist(self) -> list[list[float]]:
        return self._rows


class EmbeddingContractTests(unittest.TestCase):
    def test_empty_input_does_not_load_model(self) -> None:
        with patch.object(embedding, "get_model") as get_model:
            self.assertEqual(embedding.encode_chunks([]), [])
        get_model.assert_not_called()

    def test_encode_returns_one_512_dimensional_vector_per_chunk(self) -> None:
        model = Mock()
        model.encode.return_value = _Matrix(
            [[0.0] * embedding.EMBEDDING_DIMENSION for _ in range(3)]
        )

        with patch.object(embedding, "get_model", return_value=model):
            vectors = embedding.encode_chunks(["一", "二", "三"])

        self.assertEqual([len(vector) for vector in vectors], [512, 512, 512])
        model.encode.assert_called_once_with(
            ["一", "二", "三"], normalize_embeddings=True
        )

    def test_dimension_mismatch_uses_embedding_error_contract(self) -> None:
        model = Mock()
        model.encode.return_value = _Matrix([[0.0] * 384])

        with patch.object(embedding, "get_model", return_value=model):
            with self.assertRaises(AppError) as raised:
                embedding.encode_chunks(["错误维度"])

        self.assertEqual(raised.exception.code, "EMBEDDING_MODEL_ERROR")


if __name__ == "__main__":
    unittest.main()
