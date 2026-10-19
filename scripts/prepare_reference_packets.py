"""Scoped government packets, with HPO EXACT aliases as retrieval aids only."""
import argparse,hashlib,json,os,re
from pathlib import Path
from core import ROOT,digest,slug
from hybrid_redraft import atomic
from source_coverage_audit import norm
from prepare_candidate_packets import excerpt
from redraft_policy import packet_rejected,packet_basis_hash
from check_packets import validate_packet
from build_also_see import encode
DEST=ROOT/'.private/new-approved-sources'

def options(row,records,hpo,sources,failed):
    key=norm(row['term']);references=[n for n in hpo['records'] if key in {norm(n['term']),*(norm(a) for a in n['aliases'])}]
    queries={key}
    for n in references:queries.update(norm(a) for a in [n['term'],*n['aliases']])
    choices=[]
    for record in records:
        labels={norm(record['term']),*(norm(a) for a in record.get('aliases',[]))};body=' '+norm(record['text'])+' '
        hit=next(iter(sorted(queries & labels)),None)
        if hit is None:hit=next((q for q in sorted(queries,key=lambda v:(-len(v),v)) if ' '+q+' ' in body),None)
        if hit is None:continue
        choices.append((0 if queries & labels else 1,-len(hit),record['source_id'],record['record_id'],hit,record))
    result=[];seen_texts=set()
    for _,__,___,____,hit,record in sorted(choices,key=lambda x:x[:4]):
        source=sources[record['source_id']]
        text,start,end=excerpt(record['text'],hit,limit=4200)
        if not text or len(text.split())<8:continue
        content_hash=digest(' '.join(text.split()))
        if content_hash in seen_texts:continue
        packet={'term':row['term'],'source':source['id'],'source_record':record['record_id'],'revision':record['revision'],'text':text}
        if any(packet_basis_hash(packet)==packet_basis_hash(old) for old in failed):continue
        if packet_rejected(packet,row):continue
        ident=slug(row['term'])+'-v2-'+digest({'basis':packet_basis_hash(packet),'redraft_of':row['failed_entry_ids']})[:10]
        packet.update(id=ident,source_label=record['term'],licence=source['licence'],source_snapshot_sha256=record['snapshot_sha256'],url=record['url'],
            source_kind=record['source_kind'],source_character_range=[start,end],planned_field=row['field'],redraft_of=row['failed_entry_ids'])
        packet['packet_hash']=digest(packet);validate_packet(packet,sources);result.append(packet);seen_texts.add(content_hash)
        if len(result)==5:break
    return result,[{'source':'hpo-2026-09-01','id':n['id'],'label':n['term'],'version':hpo['version'],'snapshot_sha256':hpo['snapshot_sha256']} for n in references]

def prepare(all_headwords=False):
    sources={s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text())['sources']}
    records=json.loads((DEST/'records.json').read_text());hpo=json.loads((DEST/'hpo-reference-index.json').read_text())
    frozen=json.loads((ROOT/'.private/hybrid-redraft/cohort.json').read_text());rows=[r for r in frozen['cohort'] if all_headwords or r['wave']==1]
    outcomes=json.loads((ROOT/'data/redraft-source-outcomes.json').read_text())['outcomes']
    rows=[{**row,'latest_sourcing':outcomes.get(row['headword_key'],{})} for row in rows]
    embeddings=[];prepared=[]
    for row in rows:
        failed=[json.loads((ROOT/'data/packets'/(i+'.json')).read_text()) for i in row['failed_entry_ids']]
        packets,references=options(row,records,hpo,sources,failed);query_index=len(embeddings)
        embeddings.append({'id':'query-'+str(query_index),'term':row['term'],'definition':'psychology or counselling term, '+row['field']})
        ids=[]
        for p in packets:ids.append(len(embeddings));embeddings.append({'id':p['id'],'term':p['source_label'],'definition':p['text']})
        prepared.append({'headword_key':row['headword_key'],'query_index':query_index,'indices':ids,'packets':packets,'hpo_references':references})
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',HF_HUB_DISABLE_TELEMETRY='1')
    import torch
    from sentence_transformers import SentenceTransformer
    device='mps' if torch.backends.mps.is_available() else 'cpu';torch.set_num_threads(4)
    model=SentenceTransformer(str(ROOT/'.cache/models/bge-small-en-v1.5'),device=device,local_files_only=True,trust_remote_code=False)
    def embed(texts):return model.encode(texts,batch_size=32,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)
    pin=json.loads((ROOT/'data/also_see_model.json').read_text())
    vectors,cache=encode(embeddings,ROOT/'.cache/models/bge-small-en-v1.5',pin,ROOT/('.cache/approved-reference-'+device),entry_set_hash=digest(embeddings),embed_batch=embed)
    for row in prepared:
        q=vectors[row.pop('query_index')];ranked=sorted([{'packet':p,'cosine':round(float(q@vectors[i]),8)} for p,i in zip(row['packets'],row.pop('indices'))],key=lambda v:(-v['cosine'],v['packet']['packet_hash']))
        row['packets']=ranked[:2]
    result={'source_inventory_hash':digest(sources),'manifest_hash':digest(json.loads((DEST/'manifest.json').read_text())),
        'original_cohort_hash':digest(frozen),'embedding_pin':pin,'embedding_device':device,'rows':prepared}
    atomic(DEST/('all-packet-options.json' if all_headwords else 'pilot-packet-options.json'),result)
    print(json.dumps({'headwords':len(rows),'with_packets':sum(bool(r['packets']) for r in prepared),'packets':sum(len(r['packets']) for r in prepared),'hpo_reference_matches':sum(bool(r['hpo_references']) for r in prepared),'cache':cache}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');a=p.parse_args();prepare(a.all)
