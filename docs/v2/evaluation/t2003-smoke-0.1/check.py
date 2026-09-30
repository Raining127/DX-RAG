"""One explicitly authorized non-Benchmark encode + public vector search."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RELEASE=HERE.parent/'novatech-retrieval-benchmark-1.0.0'
QUERY='这是一条用于验证系统连通性的测试文本。'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def tree(path):
    return {p.relative_to(path).as_posix():sha(p) for p in sorted(path.rglob('*')) if p.is_file()}

def main():
    output=HERE/'result.json'
    assert not output.exists(),'Do not overwrite smoke evidence or repeat query automatically'
    os.chdir(ROOT/'backend');sys.path.insert(0,str(ROOT/'backend'))
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['ANONYMIZED_TELEMETRY']='False'
    report={'started_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'ONE_NON_BENCHMARK_EMBEDDING_AND_VECTOR_SEARCH',
        'authorization':'Human: 授权最小 embedding 与向量检索冒烟检查，使用非 Benchmark 查询；不修改语料、不重建索引、不运行完整 Benchmark。',
        'query_text':QUERY,'requested_top_k':1,'encode_calls':0,'vector_search_calls':0,
        'benchmark_executed':False,'benchmark_metrics_computed':False,'hybrid_retrieval_executed':False,
        'index_rebuild_requested':False,'python':sys.version,'executable':sys.executable,
        'process_overrides':{'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','ANONYMIZED_TELEMETRY':'False'}}
    try:
        release_report=runpy.run_path(str(RELEASE/'verify.py'))['verify']()
        report['release_before']=release_report
        data=json.loads((RELEASE/'dataset.json').read_text(encoding='utf-8'))
        assert QUERY not in {q['query_text'] for q in data['queries']}
        assert QUERY not in (HERE.parent/'pilot-snapshot-01-annotation-packet-draft.md').read_text(encoding='utf-8')
        report['query_is_not_benchmark_or_pilot_question']=True
        from app.core.config import settings
        from app.core.vector_store import ChromaVectorStore
        from app.services.embedding import encode_chunks
        model_path=Path(settings.EMBED_MODEL).resolve();store_path=Path(settings.CHROMA_PERSIST_DIR).resolve()
        assert model_path.is_dir() and (store_path/'chroma.sqlite3').is_file(),'Do not create missing model/store'
        report['effective_paths']={'model':str(model_path),'store':str(store_path)}
        model_before=tree(model_path);persist_before=tree(store_path)
        store=ChromaVectorStore()
        expected={c['chunk_id']:c for c in data['snapshot']['chunks']}
        def inventory():
            chunks=store.list_chunks(data['collection'])
            assert len(chunks)==len(expected)==38 and {c.chunk_id for c in chunks}==set(expected)
            rows=[]
            for c in chunks:
                frozen=expected[c.chunk_id]
                digest=hashlib.sha256(c.content.encode('utf-8')).hexdigest()
                assert digest==frozen['content_sha256']
                assert all(getattr(c,k)==frozen[k] for k in ('file_id','file_name','chunk_index'))
                assert c.collection_name==data['collection']
                rows.append(c.model_dump())
            return hashlib.sha256(json.dumps(sorted(rows,key=lambda x:x['chunk_id']),sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
        before=inventory();report['logical_inventory_before_sha256']=before
        print('Frozen inventory matched; encoding one neutral text offline.',flush=True)
        report['encode_calls']+=1
        vectors=encode_chunks([QUERY])
        assert len(vectors)==1 and len(vectors[0])==512
        vector=vectors[0]
        assert all(isinstance(v,(float,int)) and math.isfinite(v) for v in vector)
        norm=math.sqrt(sum(v*v for v in vector));assert abs(norm-1.0)<1e-4
        report['embedding']={'count':1,'dimension':512,'all_finite':True,'l2_norm':norm,
            'norm_tolerance':1e-4,'vector_sha256':hashlib.sha256(json.dumps(vector).encode('utf-8')).hexdigest()}
        print('Embedding valid; issuing exactly one public vector search, top_k=1.',flush=True)
        report['vector_search_calls']+=1
        results=store.search(data['collection'],vector,top_k=1)
        assert len(results)==1,'Expected a nonempty one-result vector response from 38 chunks'
        for hit in results:
            assert hit.chunk_id in expected
            frozen=expected[hit.chunk_id]
            assert hit.file_id==frozen['file_id'] and hit.file_name==frozen['file_name']
            assert hashlib.sha256(hit.content.encode('utf-8')).hexdigest()==frozen['content_sha256']
            assert math.isfinite(hit.similarity_score) and 0<=hit.similarity_score<=1
        report['vector_response']=[{'chunk_id':h.chunk_id,'file_id':h.file_id,'file_name':h.file_name,
             'similarity_score':h.similarity_score,'matches_frozen_text':True} for h in results]
        after=inventory();report['logical_inventory_after_sha256']=after
        assert after==before,'Logical inventory (including metadata) changed'
        persist_after=tree(store_path);model_after=tree(model_path)
        report['persistent_file_hash_changes']=[n for n in sorted(persist_before.keys()|persist_after.keys()) if persist_before.get(n)!=persist_after.get(n)]
        report['model_file_hash_changes']=[n for n in sorted(model_before.keys()|model_after.keys()) if model_before.get(n)!=model_after.get(n)]
        assert not report['model_file_hash_changes'],'Model files changed during smoke'
        report['release_after']=runpy.run_path(str(RELEASE/'verify.py'))['verify']()
        assert report['release_after']==release_report
        report['status']='PASS'
    except Exception as exc:
        report.update(status='FAIL',error_type=type(exc).__name__,error=str(exc))
    report['limitations']=['Single neutral query validates basic encode/vector-search execution, not relevance quality or a Benchmark.',
        'No full stored-vector audit, hybrid path, repeatability, latency or cost validation.',
        'Client read/search may change persistence files internally; file-level changes do not alone identify a cause. No mutation API invoked.',
        'Authorization is smoke-only; complete T2003 Benchmark still requires separate authorization.']
    report['completed_at_utc']=datetime.now(timezone.utc).isoformat();report['script_sha256']=sha(Path(__file__))
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'encode_calls':report['encode_calls'],
         'vector_search_calls':report['vector_search_calls'],'error':report.get('error'),
         'persistent_file_hash_changes':report.get('persistent_file_hash_changes')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
