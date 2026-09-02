"""Tests for the retrieval services."""

import unittest
from unittest.mock import Mock, patch

from app.core.config import settings
from app.core.vector_store import ChunkRecord, VectorSearchResult, VectorStore
from app.services.keyword_index import invalidate_keyword_index
from app.services.qa import (
    HybridRetriever,
    KeywordRetriever,
    VectorRetriever,
    retrieve,
    tokenize,
)


def make_chunk(chunk_id: str, content: str) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        file_id=f"file-{chunk_id}",
        file_name=f"{chunk_id}.txt",
        collection_name="test-collection",
        chunk_index=0,
        content=content,
    )


def make_vector_result(
    chunk_id: str, content: str, similarity_score: float
) -> VectorSearchResult:
    return VectorSearchResult(
        chunk_id=chunk_id,
        file_id=f"file-{chunk_id}",
        file_name=f"{chunk_id}.txt",
        content=content,
        similarity_score=similarity_score,
    )


class TokenizeTests(unittest.TestCase):
    def test_spec_chinese_examples(self) -> None:
        self.assertEqual(tokenize("机器学习"), ["机器", "器学", "学习"])
        self.assertEqual(
            tokenize("机器学习算法"),
            ["机器", "器学", "学习", "习算", "算法"],
        )

    def test_spec_mixed_language_examples(self) -> None:
        self.assertEqual(
            tokenize("Python机器学习"),
            ["python", "机器", "器学", "学习"],
        )
        self.assertEqual(tokenize("Python编程"), ["python", "编程"])
        self.assertEqual(
            tokenize("NLP 自然语言处理"),
            ["nlp", "自然", "然语", "语言", "言处", "处理"],
        )

    def test_english_and_numbers_are_lowercased_alphanumeric_tokens(self) -> None:
        self.assertEqual(tokenize("PyThOn3 RAG2026"), ["python3", "rag2026"])

    def test_single_character_tokens_are_discarded(self) -> None:
        self.assertEqual(tokenize("A 1 中"), [])

    def test_chinese_bigrams_do_not_cross_segment_boundaries(self) -> None:
        self.assertEqual(tokenize("机器，学习"), ["机器", "学习"])

    def test_duplicate_tokens_are_removed_in_first_seen_order(self) -> None:
        self.assertEqual(tokenize("Python PYTHON 机器机器"), ["python", "机器", "器机"])


class KeywordRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        KeywordRetriever._indexes.clear()
        KeywordRetriever._chunks.clear()
        KeywordRetriever._dirty_collections.clear()
        self.store = Mock(spec=VectorStore)
        self.retriever = KeywordRetriever(self.store)

    def test_index_is_built_lazily_from_list_chunks(self) -> None:
        self.store.list_chunks.return_value = [make_chunk("chunk-1", "机器学习")]

        self.store.list_chunks.assert_not_called()
        results = self.retriever.keyword_search("lazy-collection", "机器学习", 5)

        self.store.list_chunks.assert_called_once_with("lazy-collection")
        self.assertEqual(
            results,
            [
                {
                    "chunk_id": "chunk-1",
                    "file_id": "file-chunk-1",
                    "file_name": "chunk-1.txt",
                    "content": "机器学习",
                    "keyword_score": 1.0,
                }
            ],
        )

    def test_no_matching_tokens_returns_empty_list(self) -> None:
        self.store.list_chunks.return_value = [make_chunk("chunk-1", "机器学习")]

        results = self.retriever.keyword_search("no-match-collection", "量子计算", 5)

        self.assertEqual(results, [])

    def test_partial_match_score_uses_unique_query_token_count(self) -> None:
        self.store.list_chunks.return_value = [make_chunk("chunk-1", "机器学习")]

        results = self.retriever.keyword_search(
            "partial-collection", "机器学习算法", 5
        )

        self.assertEqual(results[0]["keyword_score"], 0.6)

    def test_mixed_language_tokens_can_all_match(self) -> None:
        self.store.list_chunks.return_value = [
            make_chunk("chunk-1", "Python 是流行的编程语言")
        ]

        results = self.retriever.keyword_search(
            "mixed-language-collection", "Python编程", 5
        )

        self.assertEqual(results[0]["keyword_score"], 1.0)

    def test_results_are_sorted_by_score_and_limited_to_top_k(self) -> None:
        self.store.list_chunks.return_value = [
            make_chunk("full-match", "机器学习算法"),
            make_chunk("partial-match", "机器学习"),
        ]

        results = self.retriever.keyword_search("top-k-collection", "机器学习算法", 1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "full-match")
        self.assertEqual(results[0]["keyword_score"], 1.0)

    def test_invalidation_triggers_full_rebuild_on_next_search(self) -> None:
        self.store.list_chunks.return_value = [make_chunk("old", "机器学习")]
        self.retriever.keyword_search("rebuild-collection", "机器学习", 5)
        self.store.list_chunks.return_value = [
            make_chunk("old", "机器学习"),
            make_chunk("new", "量子计算"),
        ]

        invalidate_keyword_index("rebuild-collection")
        results = self.retriever.keyword_search("rebuild-collection", "量子计算", 5)

        self.assertEqual(self.store.list_chunks.call_count, 2)
        self.assertEqual([result["chunk_id"] for result in results], ["new"])

    def test_invalidation_is_no_op_when_index_does_not_exist(self) -> None:
        invalidate_keyword_index("absent-collection")

        self.assertNotIn("absent-collection", KeywordRetriever._dirty_collections)


class VectorRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Mock(spec=VectorStore)
        self.embedder = Mock(return_value=[[0.1, 0.2, 0.3]])
        self.retriever = VectorRetriever(self.store, self.embedder)

    def test_semantic_match_preserves_similarity_as_vector_score(self) -> None:
        self.store.search.return_value = [
            make_vector_result(
                "chunk-1", "机器学习是人工智能的分支", similarity_score=0.82
            )
        ]

        results = self.retriever.vector_search("AI 的子领域", "test-collection", 5)

        self.embedder.assert_called_once_with(["AI 的子领域"])
        self.store.search.assert_called_once_with(
            "test-collection", [0.1, 0.2, 0.3], 10
        )
        self.assertEqual(
            results,
            [
                {
                    "chunk_id": "chunk-1",
                    "file_id": "file-chunk-1",
                    "file_name": "chunk-1.txt",
                    "content": "机器学习是人工智能的分支",
                    "vector_score": 0.82,
                }
            ],
        )

    def test_empty_collection_returns_empty_list(self) -> None:
        self.store.search.return_value = []

        results = self.retriever.vector_search("任意查询", "empty-collection", 5)

        self.assertEqual(results, [])

    def test_expanded_recall_is_truncated_to_top_k(self) -> None:
        self.store.search.return_value = [
            make_vector_result(f"chunk-{index}", f"content-{index}", 1 - index / 10)
            for index in range(6)
        ]

        results = self.retriever.vector_search("query", "test-collection", 3)

        self.store.search.assert_called_once_with(
            "test-collection", [0.1, 0.2, 0.3], 6
        )
        self.assertEqual(
            [result["chunk_id"] for result in results],
            ["chunk-0", "chunk-1", "chunk-2"],
        )

    def test_default_top_k_uses_config(self) -> None:
        self.store.search.return_value = []

        self.retriever.vector_search("query", "test-collection")

        self.store.search.assert_called_once_with(
            "test-collection", [0.1, 0.2, 0.3], settings.DEFAULT_TOP_K * 2
        )


class HybridRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.keyword_retriever = Mock()
        self.vector_retriever = Mock()
        self.retriever = HybridRetriever(
            self.keyword_retriever, self.vector_retriever
        )

    def test_weights_cannot_be_overridden_by_constructor(self) -> None:
        with self.assertRaises(TypeError):
            HybridRetriever(
                self.keyword_retriever,
                self.vector_retriever,
                weights=[1.0, 0.0],
            )

    def test_dual_match_is_fused_once_by_chunk_id(self) -> None:
        self.keyword_retriever.keyword_search.return_value = [
            {
                "chunk_id": "chunk-a",
                "file_id": "file-a",
                "file_name": "a.txt",
                "content": "keyword content",
                "keyword_score": 0.8,
            }
        ]
        self.vector_retriever.vector_search.return_value = [
            {
                "chunk_id": "chunk-a",
                "file_id": "file-a",
                "file_name": "a.txt",
                "content": "vector content",
                "vector_score": 0.9,
                "metadata": {"source": "vector"},
            }
        ]

        results = self.retriever.hybrid_search("query", "collection", 5)

        self.keyword_retriever.keyword_search.assert_called_once_with(
            "collection", "query", 10
        )
        self.vector_retriever.vector_search.assert_called_once_with(
            "query", "collection", 10
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "chunk-a")
        self.assertAlmostEqual(results[0]["final_score"], 0.87)
        self.assertEqual(results[0]["metadata"], {"source": "vector"})

    def test_low_keyword_only_match_is_removed_by_relevance_filter(self) -> None:
        self.keyword_retriever.keyword_search.return_value = [
            {
                "chunk_id": "chunk-a",
                "file_id": "file-a",
                "file_name": "a.txt",
                "content": "keyword content",
                "keyword_score": 0.6,
            }
        ]
        self.vector_retriever.vector_search.return_value = []

        results = self.retriever.hybrid_search("query", "collection", 5)

        self.assertEqual(results, [])

    def test_relevance_filter_runs_before_top_k(self) -> None:
        self.keyword_retriever.keyword_search.return_value = [
            {
                "chunk_id": f"low-{index}",
                "file_id": f"file-low-{index}",
                "file_name": "low.txt",
                "content": "low",
                "keyword_score": 0.0,
            }
            for index in range(2)
        ]
        self.vector_retriever.vector_search.return_value = [
            {
                "chunk_id": f"high-{index}",
                "file_id": f"file-high-{index}",
                "file_name": "high.txt",
                "content": "high",
                "vector_score": 0.5 + index / 20,
            }
            for index in range(5)
        ]

        results = self.retriever.hybrid_search("query", "collection", 3)

        self.assertEqual(
            [result["chunk_id"] for result in results],
            ["high-4", "high-3", "high-2"],
        )

    def test_same_chunk_id_is_deduplicated_even_with_different_content(self) -> None:
        self.keyword_retriever.keyword_search.return_value = [
            {
                "chunk_id": "shared",
                "file_id": "file-a",
                "file_name": "a.txt",
                "content": "first content",
                "keyword_score": 1.0,
            }
        ]
        self.vector_retriever.vector_search.return_value = [
            {
                "chunk_id": "shared",
                "file_id": "file-b",
                "file_name": "b.txt",
                "content": "different content",
                "vector_score": 1.0,
            }
        ]

        results = self.retriever.hybrid_search("query", "collection", 5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "shared")


class RetrievalIntegrationTests(unittest.TestCase):
    def test_retrieve_wires_retrievers_through_one_store(self) -> None:
        store = Mock()
        store.get_chunk_count.return_value = 1
        keyword_retriever = Mock()
        vector_retriever = Mock()
        hybrid_retriever = Mock()
        hybrid_retriever.hybrid_search.return_value = [{"chunk_id": "chunk-a"}]

        with (
            patch("app.services.qa.ChromaVectorStore", return_value=store),
            patch(
                "app.services.qa.KeywordRetriever", return_value=keyword_retriever
            ) as keyword_cls,
            patch(
                "app.services.qa.VectorRetriever", return_value=vector_retriever
            ) as vector_cls,
            patch(
                "app.services.qa.HybridRetriever", return_value=hybrid_retriever
            ) as hybrid_cls,
        ):
            results = retrieve("query", "collection", 5)

        store.get_chunk_count.assert_called_once_with("collection")
        keyword_cls.assert_called_once_with(store)
        vector_cls.assert_called_once_with(store)
        hybrid_cls.assert_called_once_with(keyword_retriever, vector_retriever)
        hybrid_retriever.hybrid_search.assert_called_once_with(
            "query", "collection", 5
        )
        self.assertEqual(results, [{"chunk_id": "chunk-a"}])

    def test_retrieve_empty_collection_returns_empty_list_without_embedding(
        self,
    ) -> None:
        store = Mock()
        store.get_chunk_count.return_value = 0

        with (
            patch("app.services.qa.ChromaVectorStore", return_value=store),
            patch("app.services.qa.KeywordRetriever") as keyword_cls,
            patch("app.services.qa.VectorRetriever") as vector_cls,
            patch("app.services.qa.HybridRetriever") as hybrid_cls,
        ):
            results = retrieve("query", "empty-collection", 5)

        self.assertEqual(results, [])
        keyword_cls.assert_not_called()
        vector_cls.assert_not_called()
        hybrid_cls.assert_not_called()

    def test_retrieve_propagates_missing_collection_error(self) -> None:
        store = Mock()
        store.get_chunk_count.side_effect = RuntimeError("missing collection")

        with patch("app.services.qa.ChromaVectorStore", return_value=store):
            with self.assertRaisesRegex(RuntimeError, "missing collection"):
                retrieve("query", "missing-collection", 5)


if __name__ == "__main__":
    unittest.main()
