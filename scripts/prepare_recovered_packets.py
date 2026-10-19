"""Freeze new private packets from individually cleared article passages."""
import collections,csv,json,re
from pathlib import Path
from core import ROOT,digest,slug,load_inputs
from source_coverage_audit import norm
from prepare_candidate_packets import excerpt
from scope_rules import decide
from check_packets import validate_packet
from recover_article_sources import excluded_paragraph

DEST=ROOT/'.private/source-recovery'

def prepare():
    entries,sources,_=load_inputs();existing={norm(e['term']) for e in entries};used={e['id'] for e in entries}
    available=collections.defaultdict(list);articles={}
    outcome_path=ROOT/'.private/candidate-drafts/outcomes.json'
    outcomes=json.loads(outcome_path.read_text()) if outcome_path.exists() else {}
    blocked={o.get('source_content_hash') for o in outcomes.values() if o.get('status')=='not_published'}
    for path in sorted((DEST/'records').glob('*.json')):
        try:row=json.loads(path.read_text())
        except json.JSONDecodeError:continue  # Retrieval may still be atomically completing this independent record.
        for term in row['terms']:
            if norm(term) not in existing:available[term].append(row)
        articles[row['source']['id']]=row
    packets=[];gaps=[];selected_sources={}
    for term,options in sorted(available.items()):
        candidates=[];pattern=r'\b'+r'\W+'.join(re.escape(w) for w in re.findall(r'\w+',term))+r'\b'
        for row in options:
            record=row['record'];match=re.search(pattern,record['text'],re.I)
            if not match:continue
            passage,start,end=excerpt(record['text'],term)
            if not passage or len(passage.split())<12 or excluded_paragraph(passage) or excluded_paragraph(record['term']):continue
            # Prefer explicit explanatory wording; this is retrieval ranking, not semantic acceptance.
            around=record['text'][max(0,match.start()-150):match.end()+450]
            explanatory=bool(re.search(r'refers? to|defined as|is (?:a|an|the)\b|characteri[sz]ed|involves?\b|describes?\b',around,re.I))
            packet={'id':slug(term),'term':term,'source':row['source']['id'],'licence':row['source']['licence'],'source_record':record['record_id'],'revision':row['source']['pinned_version'],'source_snapshot_sha256':record['snapshot_sha256'],'url':record['url'],'text':passage,'source_label':record['term'],'source_kind':record['source_kind'],'source_character_range':[start,end],'support_review_status':'unreviewed'}
            content_hash=digest({key:packet.get(key) for key in ('term','source','source_record','revision','text')})
            if content_hash in blocked:continue
            decision=decide(packet)
            if not decision['eligible']:continue
            packet['planned_field']=decision['field'];packet['scope_decision']=decision
            candidates.append((not explanatory,match.start(),-len(passage),row,packet))
        if not candidates:gaps.append({'term':term,'reason':'No eligible passage mentions the exact requested term'});continue
        _,_,_,row,packet=min(candidates,key=lambda c:c[:3])
        if packet['id'] in used:packet['id']+='-'+digest({'term':term,'source':packet['source'],'record':packet['source_record']})[:10]
        used.add(packet['id']);packet['packet_hash']=digest(packet)
        validate_packet(packet,{packet['source']:row['source']});packets.append(packet);selected_sources[packet['source']]=row['source']
    srcpath=ROOT/'data/sources.json';document=json.loads(srcpath.read_text());known={s['id']:s for s in document['sources']}
    for ident,source in selected_sources.items():
        if ident in known and known[ident]!=source:raise ValueError('Previously pinned article source changed')
        if ident not in known:document['sources'].append(source)
    temp=srcpath.with_suffix('.tmp');temp.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n');temp.replace(srcpath)
    (DEST/'packets.json').write_text(json.dumps(packets,ensure_ascii=False,indent=2)+'\n')
    (DEST/'passage-gaps.json').write_text(json.dumps(gaps,ensure_ascii=False,indent=2)+'\n')
    report={'source_recovery':'article-background-v1','prepared_packets':len(packets),'packet_set_hash':digest(packets),'individually_licensed_sources_used':len(selected_sources),'remaining_terms_with_retrieved_candidates':len(available),'no_eligible_passage':len(gaps),'existing_entries_untouched':len(entries),'legacy_definition_text_used':False,'paid_calls':0}
    (DEST/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    # The public inventory contains independent article metadata, never the private audit's term list.
    fields=['id','candidate','licence','licence_source_url','licence_confirmed','pinned_version','roles','decision','reason']
    with (ROOT/'reports/source-inventory.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");writer.writeheader()
        for source in document['sources']:
            out={k:source.get(k,'') for k in fields};out['roles']='; '.join(source['roles']);writer.writerow(out)
    return report

if __name__=='__main__':print(json.dumps(prepare(),indent=2))
