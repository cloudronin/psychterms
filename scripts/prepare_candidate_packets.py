"""Prepare private source-backed drafting packets; no model calls or legacy prose."""
import collections,json,re
from pathlib import Path
from core import ROOT,digest,slug,load_inputs
from check_packets import validate_packet
from source_coverage_audit import load_records,norm
from scope_rules import decide
from redraft_policy import packet_basis_hash,headword_key

def excerpt(text,term,limit=4200):
    if len(text)<=limit:return text,0,len(text)
    pattern=r'\W+'.join(re.escape(w) for w in re.findall(r'\w+',term))
    match=re.search(pattern,text,re.I) if pattern else None
    if not match:return None,None,None
    start=max(0,match.start()-limit//3);end=min(len(text),start+limit)
    if start:
        boundary=text.find(' ',start)
        if 0<=boundary<match.start():start=boundary+1
    if end<len(text):end=text.rfind(' ',match.end(),end)
    if end<=match.end():return None,None,None
    return text[start:end],start,end

def prepare(directory,out):
    if '.private' not in out.resolve().relative_to(ROOT).parts:raise ValueError('Queue must remain private')
    entries,sources,_=load_inputs()
    pool_path=ROOT/'data/redraft-candidates.json'
    pool=json.loads(pool_path.read_text())['candidates'] if pool_path.exists() else []
    redrafts={headword_key(row['term']):row for row in pool}
    existing={headword_key(e['term']) for e in entries}-set(redrafts)
    failed_packets={ident:json.loads((ROOT/'data/packets'/(ident+'.json')).read_text())
                    for row in pool for ident in row['failed_entry_ids']}
    records=load_records(directory);index={(r['source_id'],r['record_id']):r for r in records}
    rows=json.loads((directory/'coverage.json').read_text());packets=[];pending=[];seen=set();used={e['id'] for e in entries}
    priority={'mesh-2026':0,'ncit':1,'onlinestatbook-v2':2}
    for row in rows:
        if row['production_scope']=='excluded_biography':continue
        term=row['term'];key=norm(term);word_key=headword_key(term)
        if word_key in existing or word_key in seen:continue
        if row['status'] not in ('exact_label_source_candidate','source_passage_candidate'):
            pending.append({'term':term,'reason':'No admitted source-text packet yet','retrieval_status':row['status']});continue
        selected=None;scope_rejected=False
        def rank(match):
            record=index.get((match['source'],match['record_id']),{})
            preferred=norm(record.get('term',''))==key
            alias=key in {norm(a) for a in record.get('aliases',[])}
            position=norm(record.get('text','')).find(key)
            return (0 if preferred else 1 if alias else 2,position if position>=0 and not (preferred or alias) else 0,priority.get(match['source'],10))
        for match in sorted(row['matches'],key=rank):
            source=sources.get(match['source']);record=index.get((match['source'],match['record_id']))
            if not source or source['decision']!='yes' or 'draft_basis' not in source['roles'] or not record or not record.get('text'):continue
            # Require either the exact source label/alias, or the actual located passage.
            if row['status']=='exact_label_source_candidate' and key not in {norm(record['term']),*(norm(a) for a in record.get('aliases',[]))}:continue
            text,start,end=excerpt(record['text'],term)
            if not text or len(text.split())<8:continue
            decision=decide({'source':source['id'],'source_record':record['record_id'],'term':term,'source_label':record['term'],'text':text,'tree_numbers':record.get('tree_numbers',[]),'semantic_types':record.get('semantic_types',[])})
            if not decision['eligible']:scope_rejected=True;continue
            basis={'term':term,'source':source['id'],'source_record':record['record_id'],
                   'revision':'Flat export snapshot 2026-10-18' if source['id']=='ncit' else source['pinned_version'],'text':text}
            if word_key in redrafts and any(packet_basis_hash(basis)==packet_basis_hash(failed_packets[i]) for i in redrafts[word_key]['failed_entry_ids']):continue
            selected=(source,record,text,start,end);break
        if not selected:
            pending.append({'term':term,'reason':'No sufficiently contextual, admitted source-text packet','retrieval_status':'scope_excluded_before_spend' if scope_rejected else row['status']});continue
        source,record,text,start,end=selected
        ident=slug(term)
        if ident in used:ident+='-'+digest({'term':term,'source':record['source_id'],'record':record['record_id'],'text':text,'revision':source['pinned_version'],'redraft_of':redrafts.get(word_key,{}).get('failed_entry_ids',[])})[:10]
        if ident in used:raise ValueError('Replacement entry ID collision')
        used.add(ident);seen.add(word_key)
        packet={'id':ident,'term':term,'source':source['id'],'licence':source['licence'],'source_record':record['record_id'],
            'revision':'Flat export snapshot 2026-10-18' if source['id']=='ncit' else source['pinned_version'],'source_snapshot_sha256':record['snapshot_sha256'],'url':record['url'],'text':text,
            'source_label':record['term'],'tree_numbers':record.get('tree_numbers',[]),'semantic_types':record.get('semantic_types',[]),'source_kind':record.get('source_kind','descriptor_record_candidate'),
            'source_character_range':[start,end],'support_review_status':'unreviewed'}
        decision=decide(packet)
        if not decision['eligible']:
            pending.append({'term':term,'reason':decision['reason'],'retrieval_status':'scope_excluded_before_spend'});continue
        if word_key in redrafts:packet['redraft_of']=redrafts[word_key]['failed_entry_ids']
        packet['planned_field']=decision['field'];packet['scope_decision']=decision
        packet['packet_hash']=digest(packet);validate_packet(packet,sources);packets.append(packet)
    out.mkdir(parents=True,exist_ok=True)
    (out/'packets.json').write_text(json.dumps(packets,ensure_ascii=False,indent=2)+'\n')
    (out/'pending-sources.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2)+'\n')
    report={'packet_count':len(packets),'packet_set_hash':digest(packets),'pending_source_rows':len(pending),'existing_entries':len(entries),
        'sources':dict(collections.Counter(p['source'] for p in packets)),'legacy_definition_text_used':False,'paid_calls':0,
        'median_packet_characters':sorted(len(p['text']) for p in packets)[len(packets)//2] if packets else 0}
    (out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,default=ROOT/'.private/coverage-audit');p.add_argument('--out',type=Path,default=ROOT/'.private/candidate-drafts');a=p.parse_args()
    print(json.dumps(prepare(a.audit,a.out),indent=2))
