"""Contract 0.3 metrics over validated, first-occurrence-deduplicated IDs."""

import math

KS = (1, 3, 5, 10)
REQUEST_DEPTH = 10


def score_query(grades, ranked_ids):
    relevant = {cid for cid, grade in grades.items() if grade >= 2}
    if not relevant:
        raise ValueError("scoring requires answerable ground truth")
    ideal = sorted(grades.values(), reverse=True)

    def dcg(values):
        return sum((2 ** grade - 1) / math.log2(rank + 1)
                   for rank, grade in enumerate(values, 1))

    result = {}
    for k in KS:
        prefix = ranked_ids[:k]
        rank = next((i for i, cid in enumerate(prefix, 1) if cid in relevant), None)
        result[str(k)] = {
            "recall": len(set(prefix) & relevant) / len(relevant),
            "rr": 1 / rank if rank else 0.0,
            "ndcg": dcg([grades.get(cid, 0) for cid in prefix]) / dcg(ideal[:k]),
        }
    return result
