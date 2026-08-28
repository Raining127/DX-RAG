"""Tests for the T0601 query tokenizer."""

import unittest
from unittest.mock import Mock

from app.core.vector_store import ChunkRecord, VectorStore
from app.services.keyword_index import invalidate_keyword_index
from app.services.qa import KeywordRetriever, tokenize


def make_chunk(chunk_id: str, content: str) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        file_id=f"file-{chunk_id}",
        file_name=f"{chunk_id}.txt",
        collection_name="test-collection",
        chunk_index=0,
        content=content,
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


if __name__ == "__main__":
    unittest.main()
