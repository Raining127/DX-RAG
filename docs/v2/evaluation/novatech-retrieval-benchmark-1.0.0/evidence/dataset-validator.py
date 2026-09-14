"""Fail-fast JSON representation of the frozen T2001 contract."""

import hashlib
import json
from datetime import date

CATEGORIES = ("Direct Fact", "Paraphrase", "Distractor", "Multi-chunk")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strings(obj, fields, context):
    require(isinstance(obj, dict), f"{context}: expected object")
    for field in fields:
        require(isinstance(obj.get(field), str) and bool(obj[field].strip()),
                f"{context}: missing/invalid {field}")


def review(obj, context, fixture):
    require(isinstance(obj, dict), f"{context}: missing review")
    strings(obj, ("role", "date", "decision_ref"), context)
    require(obj.get("status") == "APPROVED", f"{context}: review not APPROVED")
    require(obj["role"] == ("SYNTHETIC_TEST" if fixture else "Human project owner"),
            f"{context}: invalid reviewer authority")
    try:
        date.fromisoformat(obj["date"])
    except ValueError as exc:
        raise ValueError(f"{context}: invalid review date") from exc


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode("utf-8")).hexdigest()


def validate_dataset(data):
    strings(data, ("dataset_version", "corpus_version", "snapshot_id", "collection"), "dataset")
    require(data.get("schema_version") == "1", "unsupported schema_version")
    require(data.get("contract_version") == "0.3", "unsupported contract_version")
    require(data.get("purpose") in ("synthetic_fixture", "benchmark"), "invalid purpose")
    fixture = data["purpose"] == "synthetic_fixture"
    provenance = data.get("provenance")
    strings(provenance, ("source", "distribution_basis", "annotation_method", "git_context",
                         "limitations", "ingestion_config", "model_version"), "provenance")
    review(data.get("review"), "dataset promotion", fixture)
    snapshot = data.get("snapshot")
    strings(snapshot, ("corpus_version", "snapshot_id"), "snapshot")
    for field in ("corpus_version", "snapshot_id"):
        require(snapshot[field] == data[field], f"snapshot: incompatible {field}")
    chunks = snapshot.get("chunks")
    require(isinstance(chunks, list) and bool(chunks), "snapshot: nonempty chunks required")
    inventory = {}
    for chunk in chunks:
        strings(chunk, ("chunk_id", "file_id", "file_name", "content_sha256"), "chunk")
        cid = chunk["chunk_id"]
        require(cid not in inventory, f"duplicate snapshot chunk_id: {cid}")
        require(type(chunk.get("chunk_index")) is int and chunk["chunk_index"] >= 0,
                f"{cid}: invalid chunk_index")
        digest = chunk["content_sha256"]
        require(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
                f"{cid}: invalid content_sha256")
        inventory[cid] = chunk
    queries = data.get("queries")
    require(isinstance(queries, list) and bool(queries), "nonempty queries required")
    ids, families = set(), {}
    for query in queries:
        strings(query, ("query_id", "query_text", "evidence_family_id", "corpus_version",
                        "snapshot_id"), "query")
        qid = query["query_id"]
        require(qid not in ids, f"duplicate query_id: {qid}")
        ids.add(qid)
        for field in ("corpus_version", "snapshot_id"):
            require(query[field] == data[field], f"{qid}: incompatible {field}")
        require(query.get("query_category") in CATEGORIES, f"{qid}: invalid category")
        require(type(query.get("answerable")) is bool, f"{qid}: invalid answerable")
        require(query.get("coverage_reviewed") is True, f"{qid}: coverage not reviewed")
        require(query.get("review_status") == "APPROVED", f"{qid}: review not APPROVED")
        review(query.get("review"), qid, fixture)
        review(query.get("coverage_review"), f"{qid} coverage", fixture)
        for flag in ("full_snapshot_screened", "no_positive_omissions"):
            require(query["coverage_review"].get(flag) is True, f"{qid}: missing {flag}")
        require(query.get("split") in ("Dev", "Test"), f"{qid}: invalid split")
        family = query["evidence_family_id"]
        require(families.setdefault(family, query["split"]) == query["split"],
                f"{qid}: evidence family crosses Dev/Test")
        judgments = query.get("judgments")
        require(isinstance(judgments, list), f"{qid}: judgments must be a list")
        grades = {}
        for judgment in judgments:
            strings(judgment, ("chunk_id", "file_name"), f"{qid} judgment")
            cid = judgment["chunk_id"]
            require(cid in inventory, f"{qid}: unknown judgment chunk_id {cid}")
            for field in ("file_name", "chunk_index"):
                require(type(judgment.get(field)) is type(inventory[cid][field]) and
                        judgment.get(field) == inventory[cid][field], f"{qid}/{cid}: mapping mismatch {field}")
            if "file_id" in judgment:
                require(judgment["file_id"] == inventory[cid]["file_id"], f"{qid}/{cid}: file_id mismatch")
            grade = judgment.get("human_grade")
            require(type(grade) is int and grade in range(4), f"{qid}/{cid}: invalid grade")
            require(cid not in grades or grades[cid] == grade, f"{qid}/{cid}: conflicting judgments")
            grades[cid] = grade
            review(judgment.get("review"), f"{qid}/{cid}", fixture)
            if "suggested_grade" in judgment:
                suggested = judgment["suggested_grade"]
                require(type(suggested) is int and suggested in range(4), f"{qid}/{cid}: invalid suggested grade")
                if suggested != grade:
                    strings(judgment, ("rationale",), f"{qid}/{cid}")
        has_relevant = any(g >= 2 for g in grades.values())
        require(has_relevant == query["answerable"], f"{qid}: answerability/ground truth conflict")
    return inventory


def load_dataset(path):
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f"duplicate JSON key: {key}")
            obj[key] = value
        return obj

    with open(path, encoding="utf-8") as handle:
        data = json.load(handle, object_pairs_hook=unique_object)
    validate_dataset(data)
    return data
