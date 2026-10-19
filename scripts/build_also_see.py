"""Generate local BGE see-also links. No network clients or language-model calls."""
import argparse,collections,hashlib,json,os,random,time
from pathlib import Path
from core import ROOT,digest
from also_see import PARAMS,assemble,load_context,validate_graph

SEED=20261018

def embedding_text(entry):return entry['term']+': '+entry['definition']

def encode(entries,model_dir,pin,cache,deadline_seconds=1800,entry_set_hash=None,embed_batch=None):
    # Set before loading any model libraries. Only previously downloaded local files load.
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false')
    import numpy as np
    for name,expected in pin['files'].items():
        path=model_dir/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Model asset hash mismatch: '+name)
    texts=[embedding_text(e) for e in entries];keys=[digest(t) for t in texts]
    matrix_path=cache/('embeddings-'+pin['weights_sha256']+'-'+(entry_set_hash or digest([(e['id'],k) for e,k in zip(entries,keys)]))+'.npy')
    cache.mkdir(parents=True,exist_ok=True)
    if matrix_path.exists():
        vectors=np.load(matrix_path,allow_pickle=False)
        if len(vectors)!=len(entries) or not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5):raise ValueError('Invalid embedding matrix cache')
        return vectors,{'embedded':0,'reused':len(entries)}
    row_dir=cache/'embedding-rows'/pin['weights_sha256'];row_dir.mkdir(parents=True,exist_ok=True)
    rows=[None]*len(entries);missing=[]
    for i,key in enumerate(keys):
        path=row_dir/(key+'.npy')
        if path.exists():rows[i]=np.load(path,allow_pickle=False)
        else:missing.append(i)
    start=time.monotonic()
    def save(path,value):
        tmp=path.with_suffix('.tmp')
        with tmp.open('wb') as stream:np.save(stream,value,allow_pickle=False)
        tmp.replace(path)
    if missing:
        if embed_batch is None:
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
            model=SentenceTransformer(str(model_dir),device='cpu',local_files_only=True,trust_remote_code=False)
            embed_batch=lambda texts:model.encode(texts,batch_size=64,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)
        for offset in range(0,len(missing),64):
            if time.monotonic()-start>=deadline_seconds:raise TimeoutError('BGE full-set embedding exceeds 30 minutes; use the registered MiniLM fallback')
            batch=missing[offset:offset+64]
            encoded=embed_batch([texts[i] for i in batch])
            for i,vector in zip(batch,encoded):
                rows[i]=vector.astype(np.float32);save(row_dir/(keys[i]+'.npy'),rows[i])
            print(json.dumps({'embedded':min(offset+64,len(missing)),'to_embed':len(missing),'reused':len(entries)-len(missing)}),flush=True)
    vectors=np.asarray(rows,dtype=np.float32)
    if not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-5):raise ValueError('Embedding vectors must be finite and normalized')
    save(matrix_path,vectors)
    return vectors,{'embedded':len(missing),'reused':len(entries)-len(missing)}

def nearest(entries,vectors,k=20):
    import numpy as np
    # Float64 ranking, self excluded before taking global top 20; field filtering comes later.
    matrix=np.asarray(vectors,dtype=np.float64);matrix=matrix/np.linalg.norm(matrix,axis=1,keepdims=True);result={};ids=[e['id'] for e in entries]
    for start in range(0,len(entries),128):
        scores=matrix[start:start+128]@matrix.T
        for offset,row in enumerate(scores):
            i=start+offset;row[i]=-np.inf
            order=np.argsort(-row,kind='stable')[:min(k,max(0,len(ids)-1))]
            result[ids[i]]=[(ids[int(j)],float(row[j])) for j in order]
    return result

def report(data,entries,stats):
    import numpy as np
    by_id={e['id']:e for e in entries};links=data['links'];sizes=collections.Counter();signals=collections.Counter();scores=[]
    for values in links.values():
        n=len(values);sizes['0' if n==0 else '1–2' if n<=2 else '3–4' if n<=4 else '5']+=1
        for r in values:
            signals[r['signal']]+=1
            if r['signal']=='embedding':scores.append(r['score'])
    quantiles=np.percentile(scores,[0,25,50,75,100]).tolist() if scores else []
    lines=['# PsychTerms: see-also report','', 'Review required before merge. Definitions, entry files, hashes and reader verdicts are unchanged.','',
      '| Measure | Count |','|---|---:|',f'| Entries eligible | {len(entries):,} |',
      *[f'| Entries with {band} links | {sizes[band]:,} |' for band in ('0','1–2','3–4','5')],
      *[f'| Links: {s} | {signals[s]:,} |' for s in ('mention','same_source','embedding')],
      f'| Headword targets appearing in more than 40 definitions | {stats["mention_targets_over_frequency_limit"]:,} |',
      f'| Mention pairs rejected by document frequency | {stats["mention_pairs_frequency_rejected"]:,} |',
      f'| Embedding proposals rejected by field filter | {stats["embedding_field_rejected"]:,} |',
      f'| Unique inbound risk pairs blocked | {stats["inbound_risk_blocked"]:,} |','',
      '## Kept embedding cosine distribution','', '| Min | p25 | Median | p75 | Max |','|---:|---:|---:|---:|---:|',
      '| '+' | '.join(f'{q:.6f}' for q in quantiles)+' |' if quantiles else 'No embedding links retained.','',
      '## Reproduction and interpretation','',
      f'- Model: `{data["model"]}`; revision `{data["model_revision"]}`.',
      f'- Weights SHA-256: `{data["model_hash"]}`.',f'- Entry-set hash: `{data["entry_set_hash"]}`.',
      f'- Input hash (retagged entries, risk, redirects, stop list, parameters): `{data["input_hash"]}`.',
      f'- Parameters: cap {data["params"]["cap"]}; mention cap {data["params"]["mention_cap"]}; headword document frequency ≤ {data["params"]["max_mention_document_frequency"]}; source cap 3; global nearest {data["params"]["neighbours_k"]} excluding self; cosine ≥ {data["params"]["min_cosine"]:.2f}; embedding links require identical fields.',
      f'- Sampling seed: `{SEED}`. Uniform sample without replacement from all eligible IDs, including zero-link and risk entries.',
      '- Risk blocking is applied to all three signals after redirect resolution; risk entries may link out.',
      '- Document frequency counts published definitions containing a canonical headword, case-insensitive whole words with singular/plural matching. Each definition counts once, including the target’s own definition; aliases do not increase this count. Targets above 40 cannot supply mention links, including through aliases. The stop list remains a backstop. Other signals remain eligible.',
      '- Diagnostic counts audit all mention/source proposals and qualifying top-20 embedding proposals even when five slots are already full. Field rejection excludes already-linked and risk targets. Risk count deduplicates the same directed pair across signals after the mention-frequency filter. Frequency rejection counts unique non-self mention pairs after stop-list filtering, before risk filtering.',
      '- Local CPU inference only. Input is exactly `term: definition`, with normalized vectors and no retrieval prefix. No paid calls, no remote embedding service, no LLM-written links.',
      '- Source identity requires an identical nonempty `packet_hash`; shared provenance scope does not qualify. It is a structural candidate signal, not an additional model judgment.',
      '- Singular/plural matching uses English suffix rules and an explicit irregular-noun table; punctuation separates words. Mentions prefer the longest matched phrase globally, then first occurrence, then headword and ID. At most two mention links are retained; after up to three identical-packet links, embeddings fill remaining slots. Cosine ties use ID order.',
      '- Entry `also_see` is hash-covered. Source entries and exported entry hashes remain untouched; the site reads the separate graph in signal order.','',
      '## Twenty random entries','']
    sample=random.Random(SEED).sample(sorted(by_id),min(20,len(by_id)))
    for ident in sample:
        e=by_id[ident];lines.extend([f'### [{e["term"]}](https://psychterms.org/terms/{ident}/)', '',f'Field: {e["field"]}.', '',e['definition'],''])
        if not links[ident]:lines.extend(['No see-also links.',''])
        else:
            for r in links[ident]:
                target=by_id[r['to']];score=f'; cosine {r["score"]:.6f}' if r['score'] is not None else ''
                lines.append(f'- [{target["term"]}](https://psychterms.org/terms/{target["id"]}/): `{r["signal"]}`{score}.')
            lines.append('')
    return '\n'.join(lines)+'\n'

def run(args):
    entries,risk,redirects,stop,fp=load_context()
    pin=json.loads((ROOT/'data/also_see_model.json').read_text())
    vectors,cache_stats=encode(entries,args.model_dir,pin,ROOT/'.cache',entry_set_hash=fp['entry_set_hash'])
    neighbours=nearest(entries,vectors)
    links,stats=assemble(entries,risk,redirects,stop,neighbours)
    output=ROOT/'data/also_see.json';old=json.loads(output.read_text()) if output.exists() else {}
    generated=args.generated or old.get('generated')
    if not generated:raise ValueError('First generation requires --generated YYYY-MM-DD')
    data={'generated':generated,'model':pin['model'],'model_hash':pin['weights_sha256'],'model_revision':pin['revision'],
          'params':PARAMS,**fp,'links':links}
    summary=validate_graph(data,entries,risk,redirects,fp,stop)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'reports/also_see_report.md').write_text(report(data,entries,stats))
    print(json.dumps({**summary,**stats,'cache':cache_stats,'model':pin['model'],'paid_calls':0}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--model-dir',type=Path,default=ROOT/'.cache/models/bge-small-en-v1.5');p.add_argument('--generated');run(p.parse_args())
