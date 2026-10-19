"""Re-source the fixed redraft headwords from pinned permitted text; local BGE only."""
import argparse,collections,json,os,random,re,sqlite3
from pathlib import Path
from core import ROOT,ALLOWED_LICENSES,digest,slug
from redraft_policy import packet_rejected,headword_key,packet_basis_hash
from source_coverage_audit import load_records,norm
from prepare_candidate_packets import excerpt
from check_packets import validate_packet
from build_also_see import encode

SEED=20261018
DEST=ROOT/'.private/local-redraft'

def permitted(source):
    return (source.get('decision')=='yes' and source.get('licence') in ALLOWED_LICENSES
            and 'draft_basis' in source.get('roles',[]) and source.get('licence_confirmed') is True)

def corpus(root=ROOT):
    sources={s['id']:s for s in json.loads((root/'data/sources.json').read_text())['sources']}
    records={}
    def add(row):
        source=sources.get(row.get('source_id'),{})
        text=row.get('text','')
        if not permitted(source) or len(text.split())<8:return
        if not re.fullmatch('[a-f0-9]{64}',row.get('snapshot_sha256','')):return
        if source.get('content_snapshot_sha256') and source['content_snapshot_sha256']!=row['snapshot_sha256']:return
        if re.search(r'dictionary\.apa\.org|APA Dictionary',text,re.I):return
        key=(row['source_id'],row['record_id'],row['snapshot_sha256'])
        if key not in records or len(text)>len(records[key]['text']):records[key]=row
    for row in load_records(root/'.private/coverage-audit'):add(row)
    for path in sorted((root/'.private/source-recovery/records').glob('*.json')):
        row=json.loads(path.read_text())
        if row.get('status')=='admitted':add(row['record'])
    for path in sorted((root/'data/packets').glob('*.json')):
        p=json.loads(path.read_text())
        add({'source_id':p['source'],'record_id':p['source_record'],'term':p.get('source_label',p['term']),
             'aliases':[],'text':p['text'],'snapshot_sha256':p['source_snapshot_sha256'],'url':p['url'],
             'source_kind':p.get('source_kind','pinned_public_packet'),'revision':p['revision']})
    return sources,[records[k] for k in sorted(records)]

def build_index(records,path):
    signature=digest([(r['source_id'],r['record_id'],r['snapshot_sha256'],digest(r['text'])) for r in records])
    db=sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS meta (signature TEXT)')
    previous=db.execute('SELECT signature FROM meta').fetchone()
    if not previous or previous[0]!=signature:
        db.execute('DROP TABLE IF EXISTS texts')
        db.execute("CREATE VIRTUAL TABLE texts USING fts5(position UNINDEXED,label,body,tokenize='unicode61 remove_diacritics 2')")
        db.executemany('INSERT INTO texts VALUES (?,?,?)',((i,' '.join([r['term'],*r.get('aliases',[])]),r['text']) for i,r in enumerate(records)))
        db.execute('DELETE FROM meta');db.execute('INSERT INTO meta VALUES (?)',(signature,));db.commit()
    return db,signature

def candidates(row,field,db,records,sources,failed,limit=5):
    key=norm(row['term'])
    if not key:return []
    query='"'+key.replace('"','""')+'"'
    positions=[int(i) for (i,) in db.execute('SELECT position FROM texts WHERE texts MATCH ? ORDER BY bm25(texts,0,5,1), position LIMIT 100',(query,))]
    result=[];seen=set()
    for i in positions:
        record=records[i];source=sources[record['source_id']];source_key=(record['source_id'],record['record_id'])
        if source_key in seen:continue
        text,start,end=excerpt(record['text'],row['term'],limit=4200)
        if not text or len(text.split())<8:continue
        packet={'term':row['term'],'source':source['id'],'source_record':record['record_id'],
                'revision':record.get('revision',source['pinned_version']),'text':text}
        if any(packet_basis_hash(packet)==packet_basis_hash(old) for old in failed):continue
        if packet_rejected(packet,row):continue
        ident=slug(row['term'])+'-v2-'+digest({'basis':packet_basis_hash(packet),'redraft_of':row['failed_entry_ids']})[:10]
        packet.update(id=ident,source_label=record['term'],licence=source['licence'],
                      source_snapshot_sha256=record['snapshot_sha256'],url=record['url'],
                      source_kind=record.get('source_kind','pinned_permitted_text'),source_character_range=[start,end],
                      planned_field=field,redraft_of=row['failed_entry_ids'])
        packet['packet_hash']=digest(packet);validate_packet(packet,sources)
        result.append(packet);seen.add(source_key)
        if len(result)==limit:break
    return result

def prepare(dest=DEST,root=ROOT):
    if not dest.resolve().is_relative_to((root/'.private').resolve()):raise ValueError('Preparation must remain private')
    dest.mkdir(parents=True,exist_ok=True)
    if (dest/'registration.json').exists():raise ValueError('Registered cohort cannot be regenerated in place')
    pool=json.loads((root/'data/redraft-candidates.json').read_text())['candidates']
    history=json.loads((root/'data/status-history.json').read_text())['entries']
    rows=sorted(pool,key=lambda r:r['headword_key']);random.Random(SEED).shuffle(rows)
    sources,records=corpus(root);db,signature=build_index(records,dest/'sources.sqlite')
    cohort=[];embedding_rows=[]
    for row in rows:
        old=[json.loads((root/'data/entries'/(i+'.json')).read_text()) for i in row['failed_entry_ids']]
        if any(history[e['id']]['status']!='redraft' for e in old):raise ValueError('Cohort includes a non-redraft entry')
        field=old[0]['field'];failed=[json.loads((root/'data/packets'/(e['id']+'.json')).read_text()) for e in old]
        options=candidates(row,field,db,records,sources,failed)
        query_index=len(embedding_rows)
        embedding_rows.append({'id':'query-'+str(query_index),'term':row['term'],'definition':'psychology or counselling term, '+field})
        option_indices=[]
        for p in options:
            option_indices.append(len(embedding_rows));embedding_rows.append({'id':p['id'],'term':p['source_label'],'definition':p['text']})
        cohort.append({'term':row['term'],'headword_key':headword_key(row['term']),'field':field,
                       'failed_entry_ids':row['failed_entry_ids'],'query_index':query_index,'option_indices':option_indices,'packets':options})
    db.close()
    (dest/'retrieval.json').write_text(json.dumps({'source_corpus_hash':signature,'rows':cohort},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'headwords':len(cohort),'candidate_packets':sum(len(r['packets']) for r in cohort),'corpus_records':len(records),'stage':'embedding','paid_calls':0}),flush=True)
    return rank(dest,root)

def rank(dest=DEST,root=ROOT):
    if (dest/'registration.json').exists():raise ValueError('Registered rankings cannot change')
    retrieval=json.loads((dest/'retrieval.json').read_text());cohort=retrieval['rows'];signature=retrieval['source_corpus_hash']
    sources={s['id']:s for s in json.loads((root/'data/sources.json').read_text())['sources']}
    pool=json.loads((root/'data/redraft-candidates.json').read_text())['candidates']
    embedding_rows=[]
    for row in cohort:
        if row['query_index']!=len(embedding_rows):raise ValueError('Retrieval query order changed')
        embedding_rows.append({'id':'query-'+str(len(embedding_rows)),'term':row['term'],'definition':'psychology or counselling term, '+row['field']})
        for i,p in zip(row['option_indices'],row['packets']):
            if i!=len(embedding_rows):raise ValueError('Retrieval packet order changed')
            validate_packet(p,sources)
            embedding_rows.append({'id':p['id'],'term':p['source_label'],'definition':p['text']})
    pin=json.loads((root/'data/also_see_model.json').read_text())
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1',TOKENIZERS_PARALLELISM='false')
    import torch
    device='mps' if torch.backends.mps.is_available() else 'cpu';torch.set_num_threads(4)
    model=None
    def embed(texts):
        nonlocal model
        if model is None:
            from sentence_transformers import SentenceTransformer
            model=SentenceTransformer(str(root/'.cache/models/bge-small-en-v1.5'),device=device,local_files_only=True,trust_remote_code=False)
        return model.encode(texts,batch_size=32,normalize_embeddings=True,convert_to_numpy=True,show_progress_bar=False)
    print(json.dumps({'stage':'embedding','device':device,'rows':len(embedding_rows)}),flush=True)
    vectors,cache=encode(embedding_rows,root/'.cache/models/bge-small-en-v1.5',pin,root/('.cache/local-redraft-'+device),entry_set_hash=digest(embedding_rows),embed_batch=embed)
    for number,row in enumerate(cohort):
        query=vectors[row.pop('query_index')]
        scored=[]
        for index,packet in zip(row.pop('option_indices'),row['packets']):
            scored.append({'packet':packet,'cosine':round(float(query@vectors[index]),8)})
        row['packets']=sorted(scored,key=lambda v:(-v['cosine'],v['packet']['packet_hash']))[:2]
        row['wave']=number//500+1
    payload={'schema_version':1,'seed':SEED,'wave_size':500,'source_corpus_hash':signature,
             'source_inventory_hash':digest(sources),'headword_pool_hash':digest(pool),'embedding_model':pin,'embedding_device':device,'cohort':cohort}
    (dest/'cohort.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    summary={'headwords':len(cohort),'waves':dict(collections.Counter(r['wave'] for r in cohort)),
             'with_ranked_packets':sum(bool(r['packets']) for r in cohort),'ranked_packets':sum(len(r['packets']) for r in cohort),
             'first_wave_headwords':sum(r['wave']==1 for r in cohort),'first_wave_with_packets':sum(r['wave']==1 and bool(r['packets']) for r in cohort),
             'embedding_cache':cache,'paid_calls':0,'source_corpus_hash':signature}
    (dest/'preparation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
    return payload

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dest',type=Path,default=DEST);p.add_argument('--rank-only',action='store_true');a=p.parse_args();rank(a.dest) if a.rank_only else prepare(a.dest)
