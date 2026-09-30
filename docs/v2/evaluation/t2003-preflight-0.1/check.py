"""Local readiness evidence only: no query, encode, retrieval or metrics calls."""
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BACKEND=ROOT/'backend'
RELEASE=HERE.parent/'novatech-retrieval-benchmark-1.0.0'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def tree(path):
    return {str(f.relative_to(path)):sha(f) for f in sorted(path.rglob('*')) if f.is_file()}

def main():
    output=HERE/'result.json'
    assert not output.exists(),'Preserve prior evidence; select a new preflight version for a later run'
    os.chdir(BACKEND);sys.path.insert(0,str(BACKEND))
    # These are process-only overrides to prevent any model fetch/telemetry.
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['ANONYMIZED_TELEMETRY']='False'
    report={'started_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'LOCAL_ENVIRONMENT_AND_INDEX_READINESS_ONLY',
            'python':{'executable':sys.executable,'version':sys.version},'working_directory':str(BACKEND),
            'process_overrides':{'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','ANONYMIZED_TELEMETRY':'False'},
            'checks':{},'benchmark_authorized':False,'benchmark_executed':False,'retrieval_executed':False,
            'embedding_encode_executed':False,'index_rebuilt':False}
    def stage(name,fn):
        print('Checking '+name,flush=True)
        try:report['checks'][name]={'status':'PASS','details':fn()}
        except Exception as exc:
            report['checks'][name]={'status':'FAIL','error_type':type(exc).__name__,'error':str(exc)}
        print(name+': '+report['checks'][name]['status'],flush=True)
    snapshot=json.loads((RELEASE/'evidence/snapshot.json').read_text(encoding='utf-8'))
    data=json.loads((RELEASE/'dataset.json').read_text(encoding='utf-8'))
    def release():
        result=runpy.run_path(str(RELEASE/'verify.py'))['verify']()
        from evaluation.dataset import load_dataset
        load_dataset(RELEASE/'dataset.json')
        return {'frozen_release_verifier':result,'current_validator':'PASS'}
    stage('frozen_dataset',release)
    def packages():
        versions={name:metadata.version(name) for name in snapshot['packages']}
        differences={k:{'snapshot':v,'current':versions[k]} for k,v in snapshot['packages'].items() if versions[k]!=v}
        result=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True,encoding='utf-8')
        assert result.returncode==0,result.stdout+result.stderr
        return {'versions':versions,'snapshot_differences':differences,'pip_check':result.stdout.strip()}
    stage('dependencies',packages)
    from app.core.config import settings
    whitelist=['MAX_CHUNK_SIZE','CHUNK_OVERLAP','DEFAULT_TOP_K','MIN_RELEVANCE_SCORE','EMBED_MODEL','CHROMA_PERSIST_DIR','UPLOAD_DIR']
    config={key:getattr(settings,key) for key in whitelist}
    report['effective_configuration']=config
    model_path=Path(settings.EMBED_MODEL).resolve();store_path=Path(settings.CHROMA_PERSIST_DIR).resolve()
    report['resolved_paths']={'model':str(model_path),'store':str(store_path)}
    def configuration():
        differences={k:{'snapshot':snapshot['runtime_confirmed'][k],'current':v} for k,v in config.items() if v!=snapshot['runtime_confirmed'][k]}
        assert not differences,json.dumps(differences)
        assert model_path.is_dir(),'Configured local model directory missing'
        assert store_path.is_dir() and (store_path/'chroma.sqlite3').is_file(),'Existing Chroma database missing; do not create a new store'
        return {'snapshot_configuration_match':True,'expected_production_top_k':5,'min_relevance_score':0.3,
                'only_whitelisted_nonsecret_configuration_exported':True}
    stage('configuration_and_paths',configuration)
    def model_files():
        expected=snapshot['model_files_sha256'];missing=[];mismatch=[]
        for name,digest in expected.items():
            path=model_path/name
            if not path.is_file():missing.append(name)
            elif sha(path)!=digest:mismatch.append(name)
        report['model_file_comparison']={'expected_count':len(expected),'missing':missing,'changed':mismatch}
        assert not missing and not mismatch,'Model file identity differs from snapshot; see model_file_comparison'
        return report['model_file_comparison']
    stage('model_identity',model_files)
    def model_load():
        assert model_path.is_dir(),'Do not resolve a missing model via network'
        from app.services.embedding import get_model
        model=get_model()
        dimension=model.get_sentence_embedding_dimension()
        assert dimension==snapshot['embedding_runtime']['dimension']==512
        assert model.max_seq_length==snapshot['embedding_runtime']['max_seq_length']
        return {'loaded_through':'app.services.embedding.get_model','dimension':dimension,
                'max_seq_length':model.max_seq_length,'device':str(model.device),'encode_called':False}
    stage('offline_model_load',model_load)
    def live_inventory():
        assert store_path.is_dir() and (store_path/'chroma.sqlite3').is_file(),'Do not create missing store'
        before=tree(store_path)
        from app.core.vector_store import ChromaVectorStore
        store=ChromaVectorStore()
        names=store.list_collections()
        assert data['collection'] in names,'Frozen collection not present'
        chunks=store.list_chunks(data['collection'])
        expected={c['chunk_id']:c for c in data['snapshot']['chunks']}
        actual={c.chunk_id:c for c in chunks}
        assert len(chunks)==len(actual)==len(expected)==38
        assert set(actual)==set(expected),'Live chunk IDs differ from frozen dataset'
        for cid,c in actual.items():
            target=expected[cid]
            assert all(getattr(c,k)==target[k] for k in ('file_id','file_name','chunk_index')),(cid,'mapping mismatch')
            assert c.collection_name==data['collection']
            assert hashlib.sha256(c.content.encode('utf-8')).hexdigest()==target['content_sha256'],(cid,'content mismatch')
        assert store.get_chunk_count(data['collection'])==38
        after=tree(store_path)
        changed=[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)]
        return {'collection':data['collection'],'chunks_matched':38,'files_matched':len({c.file_id for c in chunks}),
                'public_api_only':True,'ids_text_and_mapping':'MATCH',
                'persistent_file_hash_changes_during_client_read':changed,
                'stored_embeddings':'NOT_EXPOSED_BY_PUBLIC_INTERFACE; no private collection access or vector search',
                'note':'Client initialization can maintain database files; no mutation API was called.'}
    stage('live_collection_inventory',live_inventory)
    def code():
        git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
        diff=git('diff','v1.0.0','--','backend/app','frontend')
        expected=json.loads((RELEASE/'manifest.json').read_text(encoding='utf-8'))['tool_hashes']
        mismatches=[name for name,digest in expected.items() if sha(ROOT/name)!=digest]
        assert not diff,'Product differs from V1 reference'
        assert not mismatches,'Runner differs from approved release tool hashes: '+str(mismatches)
        return {'head':git('rev-parse','HEAD'),'v1_tag':git('rev-parse','v1.0.0^{commit}'),
                'product_diff_vs_v1':'EMPTY','runner_hashes_match_release':True,
                'working_tree_status':git('status','--short'),
                'runner_sources_sha256':expected,'note':'Workspace contains uncommitted tooling/docs; HEAD alone is insufficient provenance.'}
    stage('implementation_identity',code)
    report['limitations']=['No query execution, embedding encode, vector search, retrieval rankings, metrics, latency or cost measured.',
        'Public VectorStore exposes IDs/text/metadata but not stored vectors; vector integrity/dimensions and search readiness are not independently established.',
        'Evidence is point-in-time; recheck after changes or before authorized baseline run. No concurrent writes should occur during baseline.',
        'Frozen dataset benchmark_authorized=false records original scope. Runtime CLI currently validates data approval but does not enforce that authorization field; user execution authorization remains a separate mandatory workflow gate. Do not alter frozen dataset to grant execution.',
        'Model load is tested offline with process-only overrides; no LLM API call or credential check needed for retrieval-only baseline.',
        'V1 tied-score ordering risk and evaluation depth 10 vs production top_k 5 confounder remain.']
    failed=[k for k,v in report['checks'].items() if v['status']=='FAIL']
    report['status']='BLOCKED' if failed else 'PRECHECK_PASS_WITH_UNTESTED_SEARCH_AND_VECTOR_INTEGRITY'
    report['failed_checks']=failed;report['completed_at_utc']=datetime.now(timezone.utc).isoformat()
    report['script_sha256']=sha(Path(__file__))
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'failed_checks':failed,'report':str(output)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
