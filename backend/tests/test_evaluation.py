"""Synthetic measurements only; fixtures confer no Benchmark/Human approval."""

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from evaluation.dataset import load_dataset, validate_dataset
from evaluation.metrics import score_query
from evaluation.runner import measure, repeatability
from evaluation.v1 import build_search

FIXTURE = Path(__file__).parent / "fixtures/evaluation/hand-calculated.json"


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = load_dataset(FIXTURE)

    def run_fixture(self, data=None):
        data = data or self.data
        return measure(data, lambda q, collection, depth: data["fixture_results"][q])

    def test_hand_calculated_metrics_and_full_ground_truth(self):
        rows = self.run_fixture()["per_query"]
        row = rows[0]
        self.assertEqual(row["ranked_chunk_ids"], ["c", "b", "a", "d"])
        self.assertEqual(row["diagnostics"]["duplicates"],
                         [{"chunk_id": "b", "position": 3, "first_position": 2}])
        self.assertEqual(row["metrics"]["1"], {"recall": 0, "rr": 0, "ndcg": 1 / 7})
        expected = (1 + 3 / math.log2(3) + 7 / 2) / (7 + 3 / math.log2(3) + 1 / 2)
        for k in ("3", "5", "10"):
            self.assertEqual(row["metrics"][k]["recall"], 1)
            self.assertEqual(row["metrics"][k]["rr"], 0.5)
            self.assertAlmostEqual(row["metrics"][k]["ndcg"], expected)
        short = score_query({"a": 3, "b": 2, "c": 1}, ["b"])
        self.assertEqual(short["10"]["recall"], 0.5)
        self.assertAlmostEqual(short["10"]["ndcg"], 3 / (7 + 3 / math.log2(3) + 0.5))
        self.assertTrue(all(v == 0 for m in rows[1]["metrics"].values() for v in m.values()))
        self.assertIsNone(rows[2]["metrics"])
        self.assertEqual(rows[3]["exclusion_reason"], "unanswerable_weak_only")
        self.assertTrue(row["matched_judgments"][-1]["implicit_grade_zero"])

    def test_macro_aggregation_splits_categories_and_empty_groups(self):
        additional = copy.deepcopy(self.data["queries"][0])
        additional.update(query_id="second", query_text="second", evidence_family_id="second")
        self.data["queries"].append(additional)
        self.data["fixture_results"]["second"] = []
        groups = self.run_fixture()["aggregates"]
        dev = next(g for g in groups if g["split"] == "Dev" and g["query_category"] is None)
        self.assertEqual((dev["included"], dev["excluded"], dev["denominator"]), (2, 1, 2))
        self.assertEqual(dev["metrics"]["3"]["recall"], 0.5)
        self.assertEqual(dev["metrics"]["3"]["mrr"], 0.25)
        empty = next(g for g in groups if g["split"] == "Test" and g["query_category"] == "Direct Fact")
        self.assertIsNone(empty["metrics"])

    def test_contract_fail_fast_before_any_retrieval(self):
        def mutate(path, value):
            data = copy.deepcopy(self.data)
            target = data
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            return data

        cases = [
            (("queries", 1, "query_id"), "ranked"),
            (("queries", 1, "corpus_version"), ""),
            (("queries", 1, "snapshot_id"), "other"),
            (("queries", 0, "judgments", 0, "chunk_id"), "unknown"),
            (("queries", 0, "judgments", 0, "file_name"), "wrong"),
            (("queries", 0, "judgments", 0, "chunk_index"), True),
            (("queries", 0, "judgments", 0, "human_grade"), 4),
            (("queries", 0, "judgments", 0, "human_grade"), True),
            (("queries", 1, "judgments"), []),
            (("queries", 1, "judgments", 0, "human_grade"), 1),
            (("queries", 1, "coverage_reviewed"), False),
            (("queries", 1, "review_status"), "NEEDS_REVIEW"),
            (("queries", 1, "review", "status"), "PENDING"),
            (("queries", 1, "coverage_review", "no_positive_omissions"), False),
            (("queries", 1, "split"), "train"),
            (("queries", 1, "evidence_family_id"), "ranked"),
            (("provenance", "model_version"), ""),
            (("queries", 1, "query_category"), "Other"),
            (("snapshot", "snapshot_id"), "other"),
            (("queries", 0, "answerable"), False),
            (("queries", 1, "review", "role"), "LLM"),
            (("queries", 1, "review", "date"), "invalid"),
            (("review", "status"), "PENDING"),
            (("purpose",), "benchmark"),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                search = Mock()
                with self.assertRaises(ValueError):
                    measure(mutate(path, value), search)
                search.assert_not_called()
        conflict = copy.deepcopy(self.data["queries"][0]["judgments"][0])
        conflict["human_grade"] = 0
        self.data["queries"][0]["judgments"].append(conflict)
        with self.assertRaisesRegex(ValueError, "conflicting"):
            validate_dataset(self.data)

    def test_invalid_retrieval_is_failure_not_zero(self):
        for results in ([{"chunk_id": "unknown", "final_score": 1}],
                        [{"chunk_id": "a", "final_score": float("nan")}],
                        [{"chunk_id": "a", "final_score": True}],
                        [{"chunk_id": "a", "final_score": 0.5}] * 11):
            with self.subTest(results=results), self.assertRaises(ValueError):
                measure(self.data, lambda *args: results)

    def test_repeatability_exposes_tie_changes_and_metric_changes(self):
        first = self.run_fixture()
        self.data["fixture_results"]["ranked"] = [{"chunk_id": c, "final_score": 0.5} for c in "abc"]
        second = self.run_fixture()
        report = repeatability([first, second])
        self.assertFalse(report["order_stable"])
        self.assertEqual(report["per_query"][0]["affected_positions"], [1, 3, 4])
        self.assertTrue(report["per_query"][0]["metrics_changed"])
        self.assertTrue(repeatability([first, first])["order_stable"])

    def test_cli_fresh_processes_and_persisted_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "report.json"
            cmd = [sys.executable, "-m", "evaluation", "--dataset", str(FIXTURE.resolve()),
                   "--mode", "fixture", "--output", str(output)]
            completed = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["scope"], "SYNTHETIC_FIXTURE")
            self.assertEqual(len({r["process"]["pid"] for r in report["runs"]}), 3)
            self.assertEqual([r["process"]["pythonhashseed"] for r in report["runs"]], ["1", "2", "3"])
            self.assertTrue(report["repeatability"]["order_stable"])
            self.assertIn("backend/app/services/qa.py", report["source_sha256"])
            self.assertEqual(report["protocol"]["latency"], "NOT_MEASURED")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_v1_adapter_public_snapshot_validation_and_depth(self):
        from app.core.vector_store import ChunkRecord
        data = copy.deepcopy(self.data)
        data["purpose"] = "benchmark"

        def human(obj):
            if isinstance(obj, dict):
                if obj.get("role") == "SYNTHETIC_TEST":
                    obj["role"] = "Human project owner"  # Mocked adapter input, never persisted/promoted.
                for value in obj.values():
                    human(value)
            elif isinstance(obj, list):
                for value in obj:
                    human(value)
        human(data)
        chunks = [ChunkRecord(chunk_id=c["chunk_id"], file_id=c["file_id"], file_name=c["file_name"],
                              chunk_index=c["chunk_index"], content=c["chunk_id"], collection_name=data["collection"])
                  for c in data["snapshot"]["chunks"]]
        with patch("app.core.vector_store.ChromaVectorStore") as store, patch("app.services.qa.HybridRetriever") as hybrid:
            store.return_value.list_chunks.return_value = chunks
            hybrid.return_value.hybrid_search.side_effect = lambda q, collection, depth: data["fixture_results"][q]
            search, config = build_search(data)
            measure(data, search)
            self.assertEqual(config["production_default_top_k"], 5)
            self.assertTrue(all(c.args[2] == 10 for c in search.call_args_list))
            chunks[0].content = "changed"
            with self.assertRaisesRegex(ValueError, "content mismatch"):
                build_search(data)

    def test_real_v1_tie_order_across_seeded_processes_with_substituted_store(self):
        script = '''
import json
from unittest.mock import Mock
from app.core.vector_store import ChunkRecord
from app.services.qa import KeywordRetriever, HybridRetriever
store = Mock()
store.list_chunks.return_value = [ChunkRecord(chunk_id=c, file_id=c, file_name=c, chunk_index=0,
    collection_name="synthetic-tie", content="shared") for c in "abcdefgh"]
vector = Mock()
vector.vector_search.return_value = []
print(json.dumps(HybridRetriever(KeywordRetriever(store), vector).hybrid_search("shared", "synthetic-tie", 10)))
'''
        orders = []
        for seed in (1, 2, 3):
            result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                                    env={**os.environ, "PYTHONHASHSEED": str(seed)})
            self.assertEqual(result.returncode, 0, result.stderr)
            orders.append(json.loads(result.stdout))
        # Consume actual V1 order unchanged through the evaluation boundary.
        data = copy.deepcopy(self.data)
        data["snapshot"]["chunks"] = [dict(data["snapshot"]["chunks"][0], chunk_id=c,
            content_sha256=hashlib.sha256(c.encode()).hexdigest()) for c in "abcdefgh"]
        for q in data["queries"]:
            for j in q["judgments"]:
                j["chunk_index"] = 0
        runs = [measure(data, lambda *args, hits=hits: hits) for hits in orders]
        report = repeatability(runs)
        expected = len({tuple(h["chunk_id"] for h in hits) for hits in orders}) == 1
        self.assertEqual(report["order_stable"], expected)
        self.assertFalse(any(q["scores_changed"] for q in report["per_query"]))
        for run, hits in zip(runs, orders):
            self.assertEqual(run["per_query"][0]["ranked_chunk_ids"], [h["chunk_id"] for h in hits])
        print("V1 substituted-store tie evidence: " + json.dumps(report))


if __name__ == "__main__":
    unittest.main()
