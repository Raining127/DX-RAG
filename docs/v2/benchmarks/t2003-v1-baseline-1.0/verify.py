"""Offline verification of captured evidence; never encodes or retrieves."""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RELEASE = ROOT / 'docs/v2/evaluation/novatech-retrieval-benchmark-1.0.0'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify(folder):
    report = read(folder / 'report.json')
    execution = read(folder / 'execution.json')
    data = read(RELEASE / 'dataset.json')
    assert execution['status'] == 'PASS'
    assert execution['collection_script_sha256'] == hashlib.sha256((HERE / 'collect.py').read_bytes()).hexdigest()
    assert report['dataset'] == data
    assert report['scope'] == 'V1_HYBRID_RETRIEVAL'
    assert report['runner_version'] == '0.1.0' and report['contract_version'] == '0.3'
    assert report['protocol']['hash_seeds'] == [1, 2, 3]
    assert report['protocol']['evaluation_request_depth'] == 10
    assert report['protocol']['production_default_top_k'] == 5
    assert report['protocol']['latency'] == report['protocol']['cost'] == 'NOT_MEASURED'
    assert len(report['runs']) == 3
    assert len({run['process']['pid'] for run in report['runs']}) == 3
    assert read(folder / 'inventory-before.json') == read(folder / 'inventory-after.json')
    assert execution['model_before'] == execution['model_after']
    assert execution['release_hashes_before'] == execution['release_hashes_after']
    assert execution['source_before'] == execution['source_after']
    assert not execution['product_diff_after'] and not report['git']['v1_product_diff']
    assert execution['report_sha256'] == hashlib.sha256((folder / 'report.json').read_bytes()).hexdigest()
    manifest = HERE / 'manifest.json'
    if manifest.exists():
        for name, digest in read(manifest)['files_sha256'].items():
            assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    for name, digest in execution['release_hashes_before'].items():
        assert hashlib.sha256((RELEASE / name).read_bytes()).hexdigest() == digest, name
    queries = {q['query_id']: q for q in data['queries']}
    assert len(queries) == 40
    recalculated = 0
    for seed, run in zip((1, 2, 3), report['runs']):
        assert run['process']['pythonhashseed'] == str(seed)
        assert [q['query_id'] for q in run['per_query']] == list(queries)
        for row in run['per_query']:
            query = queries[row['query_id']]
            grades = {j['chunk_id']: j['human_grade'] for j in query['judgments']}
            ids = list(dict.fromkeys(hit['chunk_id'] for hit in row['raw_results']))
            assert ids == row['ranked_chunk_ids']
            assert all(hit['final_score'] >= 0.30 for hit in row['raw_results'])
            assert row['diagnostics']['duplicate_count'] == len(row['raw_results']) - len(ids)
            if not query['answerable']:
                assert row['metrics'] is None and row['exclusion_reason'] is not None
                continue
            relevant = {cid for cid, grade in grades.items() if grade >= 2}
            for k in (1, 3, 5, 10):
                prefix = ids[:k]
                positions = [i for i, cid in enumerate(prefix, 1) if cid in relevant]
                gains = [(2 ** grades[cid] - 1) / math.log2(i + 1) for i, cid in enumerate(prefix, 1)]
                ideal = [(2 ** grade - 1) / math.log2(i + 1)
                         for i, grade in enumerate(sorted(grades.values(), reverse=True)[:k], 1)]
                expected = {'recall': len(set(prefix) & relevant) / len(relevant),
                            'rr': 1 / positions[0] if positions else 0.0,
                            'ndcg': sum(gains) / sum(ideal)}
                for name, value in expected.items():
                    assert abs(row['metrics'][str(k)][name] - value) <= 1e-12
                    recalculated += 1
        assert len(run['aggregates']) == 10
        for group in run['aggregates']:
            members = [q for q in run['per_query'] if q['split'] == group['split'] and
                       (group['query_category'] is None or q['query_category'] == group['query_category'])]
            included = [q for q in members if q['metrics'] is not None]
            assert group['included'] == group['denominator'] == len(included)
            assert group['excluded'] == len(members) - len(included) and group['invalid'] == 0
            if not included:
                assert group['metrics'] is None
                continue
            for k in ('1', '3', '5', '10'):
                for name, source in (('recall', 'recall'), ('mrr', 'rr'), ('ndcg', 'ndcg')):
                    value = sum(q['metrics'][k][source] for q in included) / len(included)
                    assert abs(group['metrics'][k][name] - value) <= 1e-12
        totals = [g for g in run['aggregates'] if g['query_category'] is None]
        assert all(g['included'] == 16 and g['excluded'] == 4 for g in totals)
    changes = []
    for index, diagnostic in enumerate(report['repeatability']['per_query']):
        rows = [run['per_query'][index] for run in report['runs']]
        orders = [row['ranked_chunk_ids'] for row in rows]
        changed = any(order != orders[0] for order in orders[1:])
        metric_changed = any(row['metrics'] != rows[0]['metrics'] for row in rows[1:])
        score_maps = [{hit['chunk_id']: hit['final_score'] for hit in row['raw_results']} for row in rows]
        scores_changed = any(scores != score_maps[0] for scores in score_maps[1:])
        assert diagnostic['query_id'] == rows[0]['query_id']
        assert diagnostic['order_changed'] == changed and diagnostic['metrics_changed'] == metric_changed
        assert diagnostic['scores_changed'] == scores_changed
        if changed or metric_changed or scores_changed:
            changes.append({'query_id': diagnostic['query_id'], 'order_changed': changed,
                            'scores_changed': scores_changed, 'metrics_changed': metric_changed,
                            'positions': diagnostic['affected_positions']})
    assert report['repeatability']['order_stable'] == (not any(c['order_changed'] for c in changes))
    assert report['repeatability']['metric_tolerance'] == 0
    return {'status': 'PASS', 'verification_scope': 'OFFLINE saved evidence; no retrieval/encode',
            'rounds': 3, 'queries_per_round': 40, 'per_query_metric_values_recalculated': recalculated,
            'formula_verification_tolerance': 1e-12, 'repeatability_tolerance': 0,
            'changes': changes, 'persistence_changed_files': execution['persistence_changed_files']}


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'run-01'), ensure_ascii=False, indent=2))
