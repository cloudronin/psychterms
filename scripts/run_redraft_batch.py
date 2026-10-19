"""Registered next-wave drafting with learned editorial checks and private staging."""
import argparse,collections,concurrent.futures,copy,fcntl,hashlib,json,os,re
from pathlib import Path
from core import ROOT,digest,semantic_hash,load_inputs
from hybrid_redraft import atomic
from retune_api import Client,ENDPOINT,hashes
from retune_protocol import MODELS,PRICES,PROMPTS,SCHEMAS,MAX_TOKENS
from retune_pilot import process,audit
from retune_controls import controls
from run_candidate_drafts import window_hashes
from prepare_local_redrafts import corpus
from check_packets import validate_packet
from redraft_policy import headword_exclusions
from source_coverage_audit import norm
from build_also_see import encode
DEST=ROOT/'.private/redraft-wave-002'
def read(path):return json.loads(path.read_text())
def choose_candidates(packets,term,limit=5):
    # Exact source labels and direct government records outrank mere paper mentions.
    ranked=sorted(enumerate(packets),key=lambda x:(norm(x[1]['source_label'])!=norm(term),x[1]['source'] not in {'medlineplus-health-topics','cdc-mental-health-substance-use'},x[0]))
    selected=[];seen=set()
    for _,p in ranked:
        content=digest(' '.join(p['text'].split()))
        if content in seen:continue
        selected.append(p);seen.add(content)
        if len(selected)==limit:break
    return selected

def prepare(dest=DEST,wave=2):
    if (dest/'registration.json').exists():raise ValueError('Never overwrite a registered batch')
    dest.mkdir(parents=True,exist_ok=True)
    original=read(ROOT/'.private/hybrid-redraft/cohort.json');frozen=[r for r in original['cohort'] if r['wave']==wave]
    pilot={r['headword_key'] for r in original['cohort'] if r['wave']<wave}
    if len(frozen)!=500 or len({r['headword_key'] for r in frozen})!=500 or pilot & {r['headword_key'] for r in frozen}:raise ValueError('Next batch must be the next distinct 500 frozen headwords')
    sources,records=corpus();metadata={(r['source_id'],r['record_id']):r for r in records}
    retrieved=read(ROOT/'.private/local-redraft/retrieval.json');retrieval={r['headword_key']:r for r in retrieved['rows']}
    added=read(ROOT/'.private/new-approved-sources/all-packet-options.json')
    if added['source_inventory_hash']!=digest(sources) or added['original_cohort_hash']!=digest(original):raise ValueError('Government options binding changed')
    government={r['headword_key']:r for r in added['rows']};decisions=read(ROOT/'data/pilot-claude-decisions.json')['decisions'];excluded={d['headword_key'] for d in decisions if d['staged_status']=='dropped'}|headword_exclusions()
    rows=[];embeddings=[]
    for old in frozen:
        opts=[]
        if old['headword_key'] not in excluded:
            opts=choose_candidates(copy.deepcopy(retrieval[old['headword_key']]['packets']+[x['packet'] for x in government[old['headword_key']]['packets']]),old['term'])
        indices=[];query=len(embeddings);embeddings.append({'id':'query-'+str(query),'term':old['term'],'definition':'psychology or counselling term, '+old['field']})
        for p in opts:
            record=metadata.get((p['source'],p['source_record']),{})
            p['publisher_aliases']=record.get('aliases',[]);p['packet_hash']=digest({k:v for k,v in p.items() if k!='packet_hash'});validate_packet(p,sources)
            indices.append(len(embeddings));embeddings.append({'id':p['id'],'term':p['source_label'],'definition':p['text']})
        rows.append({**old,'query':query,'indices':indices,'candidate_packets':opts,'hpo_references':government[old['headword_key']]['hpo_references'],'scope_excluded':old['headword_key'] in excluded})
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',HF_HUB_DISABLE_TELEMETRY='1')
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4);device='mps' if torch.backends.mps.is_available() else 'cpu';pin=read(ROOT/'data/also_see_model.json')
    model=SentenceTransformer(str(ROOT/'.cache/models/bge-small-en-v1.5'),device=device,local_files_only=True,trust_remote_code=False)
    def embed(texts):return model.encode(texts,batch_size=32,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)
    vectors,_=encode(embeddings,ROOT/'.cache/models/bge-small-en-v1.5',pin,ROOT/f'.cache/redraft-wave-{wave:03d}',entry_set_hash=digest(embeddings),embed_batch=embed)
    for row in rows:
        q=vectors[row.pop('query')];indices=row.pop('indices')
        ranked=sorted([{'packet':p,'cosine':round(float(q@vectors[i]),8)} for p,i in zip(row['candidate_packets'],indices)],key=lambda x:(-x['cosine'],x['packet']['packet_hash']))
        row['packets']=[r['packet'] for r in ranked[:2]];row['rankings']=[{'packet_hash':r['packet']['packet_hash'],'cosine':r['cosine']} for r in ranked]
    entries,_,_=load_inputs();failed={i for r in frozen for i in r['failed_entry_ids']}
    snapshots={e['id']:digest(e) for e in entries if e['id'] in failed}
    index_path=dest/'comparison.bin';raw=(ROOT/'.private/hybrid-redraft/comparison.bin').read_bytes();index={raw[i:i+32] for i in range(0,len(raw),32)}
    for row in rows:
        for p in row['candidate_packets']:index.update(window_hashes(p['text']))
    for e in entries:index.update(window_hashes(e['definition']))
    for base in (ROOT/'.private/retune-pilot-v8/accepted',ROOT/'.private/pilot-claude-redrafts/accepted'):
        for path in base.glob('*.json'):index.update(window_hashes(read(path)['entry']['definition']))
    raw=b''.join(sorted(index));index_path.write_bytes(raw);atomic(dest/'cohort.json',rows)
    reader_controls=[controls()[i] for i in (0,1,5,19,20,21)];atomic(dest/'controls.json',reader_controls)
    m={'line':f'redraft-wave-{wave:03d}','wave':wave,'headwords':500,'seed':original['seed'],'authorization':'Execution of a further wave requires explicit user instruction; updating the field tagger alone does not start wave three.','total_redraft_cap_usd':200,'prior_spend_included':True,'shared_budget_ledger':'.private/hybrid-redraft/budget.sqlite','models':MODELS,'prices_per_million':PRICES,'endpoint':ENDPOINT,'prompts':PROMPTS,'schemas':SCHEMAS,'max_completion_tokens':MAX_TOKENS,'transport_schema_retries':1,'code_hashes':hashes(),'cohort_hash':digest(rows),'source_inventory_hash':digest(sources),'original_cohort_hash':digest(original),'editorial_decisions_hash':digest(decisions),'failed_entry_snapshots':snapshots,'comparison_sha256':hashlib.sha256(raw).hexdigest(),'embedding_pin':pin,'embedding_device':device,'field_tagging_required':True,'field_guide_hash':digest(read(ROOT/'data/field-definitions.json')),'scope_exclusions_hash':digest(read(ROOT/'data/headword-exclusions.json')),'candidate_limit':5,'ranked_packet_limit':2,'copy_words':15,'workers':12,'controls_hash':digest(reader_controls),'control_requirement':'Both readers reject all three seeded narrowed/finding definitions and accept at least two of three valid definitions. Developer checks, not accuracy validation.','publication':False,'automatic_next_batch':False,'verdicts':'Model-reviewed proposals only; export full packets for Claude. No inherited PASS and no editing previous entries.'}
    m['registration_hash']=digest(m);atomic(dest/'registration.json',m);atomic(ROOT/f'data/redraft-wave-{wave:03d}-registration.json',m)
    print(json.dumps({'registration_hash':m['registration_hash'],'headwords':len(rows),'with_packets':sum(bool(r['packets']) for r in rows),'candidate_packets':sum(len(r['candidate_packets']) for r in rows),'selected_packets':sum(len(r['packets']) for r in rows),'paid_calls':0}),flush=True)

def verify(dest):
    m=read(dest/'registration.json');rows=read(dest/'cohort.json');entries,sources,fields=load_inputs();client=Client(m,dest);client.verify()
    if digest(read(dest/'controls.json'))!=m['controls_hash']:raise ValueError('Reader controls changed')
    if digest(rows)!=m['cohort_hash'] or digest(sources)!=m['source_inventory_hash']:raise ValueError('Frozen batch or sources changed')
    snapshots={e['id']:digest(e) for e in entries if e['id'] in m['failed_entry_snapshots']}
    if snapshots!=m['failed_entry_snapshots']:raise ValueError('Old entry versions changed')
    raw=(dest/'comparison.bin').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=m['comparison_sha256']:raise ValueError('Copy comparison changed')
    return m,rows,sources,fields,client,{raw[i:i+32] for i in range(0,len(raw),32)}

def run(dest=DEST):
    with (dest/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        m,rows,sources,fields,client,index=verify(dest);path=dest/'outcomes.json';done=read(path) if path.exists() else {};atomic(dest/'run-state.json',{'stage':'running'})
        try:
            control_results=[]
            for control in read(dest/'controls.json'):
                for role in ('reader_a','reader_b'):
                    saved=client.call(role,control['packet'],control['field'],control['definition'])
                    control_results.append({'control':control['id'],'role':role,'expected':control['expected_read'],'actual':saved['parsed']['passed'],'saved':saved})
            negative=[r for r in control_results if not r['expected']];positive=[r for r in control_results if r['expected']]
            control_passed=all(not r['actual'] for r in negative) and all(sum(r['actual'] for r in positive if r['role']==role)>=2 for role in ('reader_a','reader_b'))
            atomic(dest/'control-results.json',{'passed':control_passed,'results':control_results})
            if not control_passed:raise ValueError('Seeded reader checks failed; no batch drafting dispatched')
            with concurrent.futures.ThreadPoolExecutor(max_workers=m['workers']) as pool:
                pending=[r for r in rows if r['headword_key'] not in done]
                futures=[pool.submit(process,r,r['packets'],client,sources,fields,index) for r in pending]
                for f in concurrent.futures.as_completed(futures):
                    v=f.result();done[v['headword_key']]=v;atomic(path,done);atomic(dest/'progress.json',{'completed':len(done),'total':len(rows),'provisional_pass':sum(bool(x['accepted']) for x in done.values())})
            accepted=[]
            for row in rows:
                v=done[row['headword_key']];a=v['accepted']
                if not a:continue
                try:audit(a,m,dest,index)
                except ValueError as error:v['accepted']=None;v['reason']='Final audit: '+str(error);continue
                a['review_status']='model-reviewed proposal; pending editorial review';atomic(dest/'accepted'/(a['entry']['id']+'.json'),a);index.update(window_hashes(a['entry']['definition']));accepted.append(a)
            atomic(path,done);verify(dest)
            summary={'wave':m['wave'],'headwords':500,'with_packets':sum(bool(r['packets']) for r in rows),'passed_two_readers_and_copy':len(accepted),'pass_fraction':len(accepted)/500,'field_review_flags':sum(bool(a['field_issues']) for a in accepted),'outcome_counts':dict(collections.Counter('model_pass' if v['accepted'] else 'no_packets' if not next(r for r in rows if r['headword_key']==k)['packets'] else v['reason'] for k,v in done.items())),'total_redraft_budget':client.budget.summary(),'registration_hash':m['registration_hash'],'published':0,'next_batch_started':False}
            atomic(dest/'report.json',summary);atomic(ROOT/('reports/'+dest.name+'.json'),summary);atomic(dest/'run-state.json',{'stage':'complete',**summary});print(json.dumps(summary,indent=2),flush=True)
        except Exception:
            atomic(dest/'run-state.json',{'stage':'paused','reason':'See worker log and receipts; paid retries are bounded.'});raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','verify']);p.add_argument('--wave',type=int,default=3);a=p.parse_args()
    DEST=ROOT/f'.private/redraft-wave-{a.wave:03d}'
    if a.command=='prepare':prepare(DEST,a.wave)
    elif a.command=='run':run(DEST)
    else:print(json.dumps({'frozen_inputs_verified':bool(verify(DEST)),'paid_calls':0}))
