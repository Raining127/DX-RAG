"""Capture the authorized T2003 baseline without changing the frozen runner/product.

Run from the repository root. An existing output directory is never overwritten.
The inventory helper uses only the public VectorStore API in a separate process.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BACKEND = ROOT / 'backend'
RELEASE = ROOT / 'docs/v2/evaluation/novatech-retrieval-benchmark-1.0.0'
OVERRIDES = {'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
             'ANONYMIZED_TELEMETRY': 'False', 'PYTHONIOENCODING': 'utf-8'}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def tree(path):
    return {p.relative_to(path).as_posix(): sha(p)
            for p in sorted(path.rglob('*')) if p.is_file()}


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True,
                                   encoding='utf-8').strip()


def inventory():
    from evaluation.dataset import load_dataset
    from app.core.vector_store import ChromaVectorStore
    data = load_dataset(RELEASE / 'dataset.json')
    expected = {c['chunk_id']: c for c in data['snapshot']['chunks']}
    store = ChromaVectorStore()
    assert data['collection'] in store.list_collections()
    chunks = store.list_chunks(data['collection'])
    assert len(chunks) == len(expected) == 38
    assert {c.chunk_id for c in chunks} == set(expected)
    rows = []
    for chunk in chunks:
        frozen = expected[chunk.chunk_id]
        assert hashlib.sha256(chunk.content.encode('utf-8')).hexdigest() == frozen['content_sha256']
        assert all(getattr(chunk, key) == frozen[key] for key in ('file_id', 'file_name', 'chunk_index'))
        assert chunk.collection_name == data['collection']
        rows.append(chunk.model_dump())
    rows.sort(key=lambda row: row['chunk_id'])
    return {'collection': data['collection'], 'count': len(rows), 'chunks': rows,
            'sha256': hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()}


def main():
    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    os.environ.update(OVERRIDES)
    if sys.argv[1:] == ['--inventory']:
        print(json.dumps(inventory(), ensure_ascii=False))
        return 0
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / 'run-01'
    output.mkdir(parents=True, exist_ok=False)
    record = {'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'authorization': 'H-T2003-BASELINE-2026-09-14; SPEC 1.10',
              'command': [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
              'working_directory': str(BACKEND), 'process_overrides': OVERRIDES,
              'collection_script_sha256': sha(Path(__file__)), 'status': 'IN_PROGRESS',
              'concurrency_boundary': 'No application/python process observed before collection. No OS-wide writer lock; before/after logical checks cannot exclude transient concurrent writes.',
              'latency': 'NOT_MEASURED', 'cost': 'NOT_MEASURED'}
    def command(label, args):
        print(label, flush=True)
        process = subprocess.run(args, cwd=BACKEND, capture_output=True, text=True, encoding='utf-8')
        (output / (label + '.stdout.txt')).write_text(process.stdout, encoding='utf-8')
        (output / (label + '.stderr.txt')).write_text(process.stderr, encoding='utf-8')
        record.setdefault('commands', []).append({'label': label, 'command': args, 'exit_code': process.returncode})
        assert process.returncode == 0, f'{label} failed; see preserved logs'
        return process.stdout
    try:
        record['git_before'] = {'head': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
                                'status': git('status', '--porcelain'), 'v1': git('rev-parse', 'v1.0.0^{commit}')}
        assert record['git_before']['v1'] == 'da8be59a60d7f35a2e3c1ab835624946c53d2a55'
        assert not git('diff', 'v1.0.0', '--', 'backend/app', 'frontend'), 'Product differs from V1'
        record['release_before'] = runpy.run_path(str(RELEASE / 'verify.py'))['verify']()
        snapshot = json.loads((RELEASE / 'evidence/snapshot.json').read_text(encoding='utf-8'))
        from evaluation.dataset import load_dataset
        from app.core.config import settings
        load_dataset(RELEASE / 'dataset.json')
        keys = ['MAX_CHUNK_SIZE', 'CHUNK_OVERLAP', 'DEFAULT_TOP_K', 'MIN_RELEVANCE_SCORE',
                'EMBED_MODEL', 'CHROMA_PERSIST_DIR', 'UPLOAD_DIR']
        record['config'] = {key: getattr(settings, key) for key in keys}
        assert all(record['config'][key] == snapshot['runtime_confirmed'][key] for key in keys)
        model = Path(settings.EMBED_MODEL).resolve()
        store = Path(settings.CHROMA_PERSIST_DIR).resolve()
        assert model.is_dir() and (store / 'chroma.sqlite3').is_file(), 'Missing existing model/store'
        record['paths'] = {'model': str(model), 'store': str(store)}
        record['model_before'] = tree(model)
        assert all(record['model_before'].get(key.replace('\\', '/')) == value
                   for key, value in snapshot['model_files_sha256'].items()), 'Model identity mismatch'
        record['release_hashes_before'] = tree(RELEASE)
        sources = list((BACKEND / 'app').rglob('*.py')) + list((BACKEND / 'evaluation').glob('*.py'))
        record['source_before'] = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
        command('pip-check', [sys.executable, '-m', 'pip', 'check'])
        for pattern in ('test_evaluation.py', 'test_qa.py', 'test_query.py'):
            command(pattern[:-3], [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v'])
        record['persistence_before'] = tree(store)
        before = json.loads(command('inventory-before', [sys.executable, str(Path(__file__)), '--inventory']))
        save(output / 'inventory-before.json', before)
        record['logical_before_sha256'] = before['sha256']
        # Persist preconditions even if an external interruption prevents finalization.
        save(output / 'preconditions.json', record)
        command('benchmark', [sys.executable, '-m', 'evaluation', '--dataset', str(RELEASE / 'dataset.json'),
                              '--mode', 'v1', '--seeds', '1,2,3', '--output', str(output / 'report.json')])
        after = json.loads(command('inventory-after', [sys.executable, str(Path(__file__)), '--inventory']))
        save(output / 'inventory-after.json', after)
        record['logical_after_sha256'] = after['sha256']
        assert before == after, 'Public logical inventory changed'
        record['model_after'] = tree(model)
        assert record['model_after'] == record['model_before'], 'Model changed'
        record['release_hashes_after'] = tree(RELEASE)
        assert record['release_hashes_after'] == record['release_hashes_before'], 'Frozen release changed'
        record['source_after'] = {p.relative_to(ROOT).as_posix(): sha(p) for p in sources}
        assert record['source_after'] == record['source_before'], 'Product/runner sources changed'
        record['persistence_after'] = tree(store)
        record['persistence_changed_files'] = [key for key in sorted(record['persistence_before'].keys() | record['persistence_after'].keys())
                                                if record['persistence_before'].get(key) != record['persistence_after'].get(key)]
        record['product_diff_after'] = git('diff', 'v1.0.0', '--', 'backend/app', 'frontend')
        assert not record['product_diff_after']
        report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
        assert len(report['runs']) == 3 and all(len(run['per_query']) == 40 for run in report['runs'])
        record['report_sha256'] = sha(output / 'report.json')
        record['status'] = 'PASS'
    except Exception as exc:
        record.update(status='FAIL', error_type=type(exc).__name__, error=str(exc))
    record['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
    save(output / 'execution.json', record)
    print(json.dumps({'status': record['status'], 'error': record.get('error'), 'output': str(output)}, ensure_ascii=False), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
