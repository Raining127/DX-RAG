"""Measurement, aggregation, and repeatability without altering retrieval order."""

import math

from evaluation.dataset import CATEGORIES, require, validate_dataset
from evaluation.metrics import KS, REQUEST_DEPTH, score_query


def measure(data, search):
    inventory = validate_dataset(data)  # Entire dataset before the first search.
    output = []
    for query in data["queries"]:
        raw = search(query["query_text"], data["collection"], REQUEST_DEPTH)
        require(isinstance(raw, list) and len(raw) <= REQUEST_DEPTH, "invalid retrieval list/depth")
        ranked, duplicates, seen = [], [], {}
        for position, hit in enumerate(raw, 1):
            require(isinstance(hit, dict), "retrieval hit must be an object")
            cid = hit.get("chunk_id")
            require(isinstance(cid, str) and cid in inventory, f"unknown retrieved chunk_id: {cid}")
            score = hit.get("final_score")
            require(type(score) in (int, float) and math.isfinite(score), f"{cid}: invalid final_score")
            if cid in seen:
                duplicates.append({"chunk_id": cid, "position": position, "first_position": seen[cid]})
            else:
                seen[cid] = position
                ranked.append(cid)
        grades = {j["chunk_id"]: j["human_grade"] for j in query["judgments"]}
        excluded = None
        if not query["answerable"]:
            excluded = "unanswerable_weak_only" if any(grades.values()) else "unanswerable"
        output.append({
            **{key: query[key] for key in ("query_id", "query_text", "query_category", "answerable",
                                           "split", "evidence_family_id", "corpus_version", "snapshot_id")},
            "dataset_version": data["dataset_version"],
            "raw_results": [{"chunk_id": h["chunk_id"], "final_score": h["final_score"]} for h in raw],
            "ranked_chunk_ids": ranked,
            "matched_judgments": [{"chunk_id": cid, "human_grade": grades.get(cid, 0),
                                    "implicit_grade_zero": cid not in grades} for cid in ranked],
            "metrics": score_query(grades, ranked) if query["answerable"] else None,
            "exclusion_reason": excluded,
            "diagnostics": {"validation": "PASS", "duplicates": duplicates,
                            "duplicate_count": len(duplicates), "returned_count": len(raw)},
        })
    return {"per_query": output, "aggregates": aggregate(output)}


def aggregate(rows):
    groups = []
    for split in ("Dev", "Test"):
        for category in (None, *CATEGORIES):
            members = [q for q in rows if q["split"] == split and
                       (category is None or q["query_category"] == category)]
            eligible = [q for q in members if q["metrics"] is not None]
            count = len(eligible)
            metrics = {str(k): {
                name: sum(q["metrics"][str(k)][source] for q in eligible) / count
                for name, source in (("recall", "recall"), ("mrr", "rr"), ("ndcg", "ndcg"))
            } for k in KS} if count else None
            groups.append({"split": split, "query_category": category,
                           "included": count, "excluded": len(members) - count,
                           "invalid": 0, "denominator": count, "metrics": metrics,
                           "excluded_query_ids": [q["query_id"] for q in members if q["metrics"] is None]})
    return groups


def repeatability(runs):
    require(len(runs) >= 2, "repeatability requires at least two runs")
    diagnostics = []
    for index, baseline in enumerate(runs[0]["per_query"]):
        observed = [run["per_query"][index] for run in runs]
        orders = [q["ranked_chunk_ids"] for q in observed]
        positions = [pos + 1 for pos in range(max(map(len, orders), default=0))
                     if len({order[pos] if pos < len(order) else None for order in orders}) > 1]
        diagnostics.append({"query_id": baseline["query_id"], "run_count": len(runs),
                            "order_changed": bool(positions), "affected_positions": positions,
                            "ranked_orders": orders,
                            "scores_changed": any(
                                {h["chunk_id"]: h["final_score"] for h in q["raw_results"]} !=
                                {h["chunk_id"]: h["final_score"] for h in baseline["raw_results"]}
                                for q in observed[1:]),
                            "metrics_changed": any(q["metrics"] != baseline["metrics"] for q in observed[1:]),
                            "metrics_by_run": [q["metrics"] for q in observed]})
    return {"order_stable": not any(d["order_changed"] for d in diagnostics),
            "metric_tolerance": 0, "per_query": diagnostics}
