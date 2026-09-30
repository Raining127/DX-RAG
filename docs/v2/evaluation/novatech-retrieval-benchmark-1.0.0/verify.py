"""Read-only frozen release verification. Does not run retrieval or metrics."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def verify():
    manifest=read(HERE/'manifest.json')
    for name,digest in manifest['files_sha256'].items():
        assert sha(HERE/name)==digest,('release file changed',name)
    approval=read(HERE/'approval.json')
    assert sha(HERE/'approval-input/manifest.json')==approval['approved_rc_manifest_sha256']
    assert sha(HERE/'approval-input/dataset.json')==approval['approved_rc_dataset_sha256']
    rc_manifest=read(HERE/'approval-input/manifest.json')
    for name,digest in rc_manifest['files_sha256'].items():
        if name.startswith('evidence/'):
            assert sha(HERE/name)==digest,('approved evidence changed',name)
    rc=read(HERE/'approval-input/dataset.json');data=read(HERE/'dataset.json')
    allowed={'dataset_version','artifact_status','formal_freeze','dataset_promotion','review','provenance'}
    assert {k:v for k,v in data.items() if k not in allowed}=={k:v for k,v in rc.items() if k not in allowed}
    assert {k:v for k,v in data['provenance'].items() if k!='annotation_method'}=={k:v for k,v in rc['provenance'].items() if k!='annotation_method'}
    assert data['provenance']['annotation_method']==rc['provenance']['annotation_method'].replace('Frozen promotion is still pending.', 'Final dataset freeze and promotion approved: '+approval['decision_ref']+'.')
    assert data['dataset_version']=='novatech-retrieval-benchmark-1.0.0'
    assert data['artifact_status']==data['formal_freeze']=='FROZEN'
    assert data['dataset_promotion']=='APPROVED' and data['benchmark_authorized'] is False
    assert data['review']=={'status':'APPROVED','role':'Human project owner','date':approval['date'],'decision_ref':approval['decision_ref']}
    spec=importlib.util.spec_from_file_location('release_validator',HERE/'evidence/dataset-validator.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.load_dataset(HERE/'dataset.json')
    snapshot=read(HERE/'evidence/snapshot.json')
    for source in snapshot['sources']:
        assert sha(HERE/'evidence/corpus'/source['file_name'])==source['sha256']
    actual={c['chunk_id']:c for c in snapshot['chunks']}
    assert len(actual)==len(data['snapshot']['chunks'])==38
    for c in data['snapshot']['chunks']:
        frozen=actual[c['chunk_id']]
        assert all(c[k]==frozen[k] for k in ('file_id','file_name','chunk_index'))
        assert hashlib.sha256(frozen['content'].encode('utf-8')).hexdigest()==c['content_sha256']
    assert len(data['queries'])==40
    assert sum(len(q['judgments']) for q in data['queries'])==1520
    assert {q['query_id'] for q in data['queries']}=={f'BC01-Q{i:03}' for i in range(1,41)}
    counts={side:{'answerable':sum(q['answerable'] for q in data['queries'] if q['split']==side),
                  'unanswerable':sum(not q['answerable'] for q in data['queries'] if q['split']==side)} for side in ('Dev','Test')}
    assert all(v=={'answerable':16,'unanswerable':4} for v in counts.values())
    return {'status':'PASS','dataset_version':data['dataset_version'],
            'dataset_sha256':sha(HERE/'dataset.json'),'manifest_sha256':sha(HERE/'manifest.json'),
            'validator':'Full validate_dataset/load_dataset PASS; pure data validation only',
            'approved_rc_content_comparison':'PASS: release/approval metadata only',
            'query_count':40,'judgment_count':1520,'chunk_count':38,'counts':counts,
            'formal_freeze':'FROZEN','dataset_promotion':'APPROVED',
            'benchmark_authorized':False,'benchmark_executed':False,'live_model_index_store':'NOT_CHECKED'}

if __name__=='__main__':
    result=verify()
    assert read(HERE/'verification.json')==result,'verification record mismatch'
    print(json.dumps(result,ensure_ascii=False))
