"""Run each repetition in a fresh process with an explicit Python hash seed."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from importlib import metadata
from datetime import datetime, timezone

from evaluation import RUNNER_VERSION
from evaluation.dataset import fingerprint, load_dataset, require
from evaluation.metrics import KS, REQUEST_DEPTH
from evaluation.runner import measure, repeatability

ROOT = Path(__file__).resolve().parents[2]


def worker(data, mode):
    if mode == "fixture":
        require(data["purpose"] == "synthetic_fixture", "fixture mode requires synthetic_fixture")
        observations = data.get("fixture_results")
        require(isinstance(observations, dict), "missing fixture_results")
        require(set(observations) == {q["query_text"] for q in data["queries"]}, "fixture query keys mismatch")
        search = lambda query, collection, top_k: observations[query]
        config = {"retriever": "synthetic recorded observations; no live retrieval"}
    else:
        from evaluation.v1 import build_search
        search, config = build_search(data)
    result = measure(data, search)
    result["effective_config"] = config
    result["dataset_sha256"] = fingerprint(data)
    result["process"] = {"pid": os.getpid(), "pythonhashseed": os.environ.get("PYTHONHASHSEED")}
    return result


def git_context():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    return {"head": git("rev-parse", "HEAD"), "status": git("status", "--porcelain"),
            "v1_reference": git("rev-parse", "v1.0.0^{commit}"),
            "v1_product_diff": git("diff", "v1.0.0", "--", "backend/app")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mode", required=True, choices=("fixture", "v1"))
    parser.add_argument("--seeds", default="1,2,3", help="fresh-process hash seeds (at least two)")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        data = load_dataset(args.dataset)
        require((args.mode == "fixture") == (data["purpose"] == "synthetic_fixture"), "mode/purpose mismatch")
        if args.worker:
            print(json.dumps(worker(data, args.mode), ensure_ascii=False, allow_nan=False))
            return 0
        require(args.output is not None, "--output required")
        require(not args.output.exists(), "output already exists; choose a new path")
        seeds = [int(value) for value in args.seeds.split(",")]
        require(len(seeds) >= 2 and all(0 <= seed <= 4294967295 for seed in seeds), "invalid seeds")
        runs = []
        for seed in seeds:
            command = [sys.executable, "-m", "evaluation", "--worker", "--dataset",
                       str(args.dataset.resolve()), "--mode", args.mode]
            process = subprocess.run(command, cwd=ROOT / "backend", capture_output=True, text=True,
                                     encoding="utf-8", env={**os.environ, "PYTHONHASHSEED": str(seed),
                                                            "PYTHONIOENCODING": "utf-8"})
            require(process.returncode == 0, f"worker seed {seed} failed: {process.stderr.strip()}")
            result = json.loads(process.stdout)
            require(result["dataset_sha256"] == fingerprint(data), "dataset changed during repetitions")
            result["worker_stderr"] = process.stderr
            runs.append(result)
        sources = list((ROOT / "backend/evaluation").glob("*.py")) + list((ROOT / "backend/app").rglob("*.py"))
        sources.append(ROOT / "docs/v2/evaluation/retrieval-evaluation-dataset-contract.md")
        report = {
            "runner_version": RUNNER_VERSION, "contract_version": "0.3",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset": data, "dataset_sha256": fingerprint(data),
            "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            "git": git_context(),
            "environment": {"python": sys.version, "platform": platform.platform(), "executable": sys.executable,
                            "packages": {d.metadata["Name"]: d.version for d in metadata.distributions() if d.metadata["Name"]}},
            "command": [sys.executable, "-m", "evaluation", *(argv if argv is not None else sys.argv[1:])],
            "scope": "SYNTHETIC_FIXTURE" if args.mode == "fixture" else "V1_HYBRID_RETRIEVAL",
            "protocol": {"ks": KS, "evaluation_request_depth": REQUEST_DEPTH, "production_default_top_k": 5,
                         "weights": {"keyword": 0.3, "vector": 0.7},
                         "candidate_depth_dependency": "Hybrid branches=2*top_k; vector store=4*top_k",
                         "confounder": "depth-10 prefixes may differ from standalone production top_k=5",
                         "at_10": "deeper retrieval diagnostic under evaluation request depth 10",
                         "repeatability_conditions": "fresh processes, declared hash seeds; exact comparison",
                         "hash_seeds": seeds, "latency": "NOT_MEASURED", "cost": "NOT_MEASURED"},
            "runs": runs, "repeatability": repeatability(runs),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        print(f"Saved {args.output}; order_stable={report['repeatability']['order_stable']}")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"evaluation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
