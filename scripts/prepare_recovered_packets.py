"""Freeze new private packets from individually cleared article passages."""
import collections,csv,json,re
from pathlib import Path
from core import ROOT,digest,slug,load_inputs
from source_coverage_audit import norm
from prepare_candidate_packets import excerpt
from scope_rules import decide
from check_packets import validate_packet
from recover_article_sources import excluded_paragraph,parse_article
from recover_nimh_sources import parse_page

DEST=ROOT/'.private/source-recovery'

def match_flags(term):
    return 0 if term.isupper() and any(c.isalpha() for c in term) else re.I

def focused_excerpt(text,term,limit=2400,require_explanation=False):
    pattern=r'\b'+r'\W+'.join(re.escape(w) for w in re.findall(r'\w+',term))+r'\b'
    options=[];offset=0
    for paragraph in text.split('\n\n'):
        for match in re.finditer(pattern,paragraph,match_flags(term)):
            following=paragraph[match.end():match.end()+120]
            explanatory=bool(re.match(r'\s*(?:\([^)]{0,60}\)\s*)?(?:,?\s*(?:which\s+)?(?:is|are|refers? to|involves?|describes?|means?|denotes?|can be defined as|is defined as))\b',following,re.I))
            if require_explanation:
                prefix=paragraph[:match.start()]
                starts_sentence=bool(re.search(r'(?:^|[.!?]\s+)(?:[Aa]n?\s+)?$',prefix))
                expanded_acronym=term.isupper() and bool(re.search(r'\(\s*$',prefix)) and bool(re.match(r'\s*\)',following))
                definition_following=bool(re.match(r'\s*(?:\([^)]{0,60}\)\s*)?(?:is|are)\s+(?:a|an|the)\b|\s*(?:refers? to|means?|denotes?|involves?|describes?|is defined as|can be defined as)\b',following,re.I))
                if not (expanded_acronym or (starts_sentence and definition_following)):continue
            options.append((not explanatory,offset+match.start(),offset,paragraph,match.end()))
        offset+=len(paragraph)+2
    if not options:return None,None,None
    _,position,start,paragraph,match_end=min(options,key=lambda row:row[:2])
    if len(paragraph)<=limit:return paragraph,start,start+len(paragraph)
    match_start=position-start;left=max(0,match_start-limit//3);right=min(len(paragraph),left+limit)
    if left:
        boundary=paragraph.find(' ',left)
        if 0<=boundary<match_start:left=boundary+1
    if right<len(paragraph):
        boundary=paragraph.rfind(' ',match_end,right)
        if boundary>=match_end:right=boundary
    if right<match_end:return None,None,None
    return paragraph[left:right],start+left,start+right

def terminal_content_hashes(outcomes,path):
    blocked=set(json.loads(path.read_text())) if path.exists() else set()
    blocked.update(o['source_content_hash'] for o in outcomes.values() if o.get('status')=='not_published' and o.get('source_content_hash'))
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(sorted(blocked),indent=2)+'\n');temp.replace(path)
    return blocked

def prepare():
    entries,sources,_=load_inputs();existing={norm(e['term']) for e in entries};used={e['id'] for e in entries}
    available=collections.defaultdict(list);articles={}
    outcome_path=ROOT/'.private/candidate-drafts/outcomes.json'
    outcomes=json.loads(outcome_path.read_text()) if outcome_path.exists() else {}
    blocked=terminal_content_hashes(outcomes,DEST/'declined-content-hashes.json')
    for path in sorted((DEST/'records').glob('*.json')):
        try:row=json.loads(path.read_text())
        except json.JSONDecodeError:continue  # Retrieval may still be completing this independent record.
        try:
            source,record=parse_article((DEST/'xml'/(row['pmcid']+'.xml')).read_bytes(),row['pmcid'],row['record']['record_id'])
        except (ValueError,FileNotFoundError):continue
        row={**row,'source':source,'record':record}
        for term in row['terms']:
            if norm(term) not in existing:available[term].append(row)
        articles[row['source']['id']]=row
    for path in sorted((DEST/'government/records').glob('*.json')):
        try:row=json.loads(path.read_text())
        except json.JSONDecodeError:continue
        raw=(DEST/'government'/row['asset_filename']).read_bytes()
        if __import__('hashlib').sha256(raw).hexdigest()!=row['record']['snapshot_sha256']:raise ValueError('Government page snapshot changed')
        title,content,_=parse_page(raw)
        if title!=row['record']['term'] or content!=row['record']['text']:raise ValueError('Government prose extraction changed after admission')
        if row['source']['licence']!=sources['nimh']['licence'] or row['source']['evidence']['policy_snapshot_sha256']!=sources['nimh']['evidence']['policy_snapshot_sha256']:raise ValueError('Government own-text permission differs')
        for term in row['terms']:
            if norm(term) not in existing:available[term].append(row)
    packets=[];gaps=[];selected_sources={}
    for term,options in sorted(available.items()):
        candidates=[];pattern=r'\b'+r'\W+'.join(re.escape(w) for w in re.findall(r'\w+',term))+r'\b'
        for row in options:
            record=row['record'];match=re.search(pattern,record['text'],match_flags(term))
            if not match:continue
            passage,start,end=focused_excerpt(record['text'],term,require_explanation=row['source']['id'].startswith('nimh-page-'))
            if not passage or len(passage.split())<12 or excluded_paragraph(passage) or excluded_paragraph(record['term']):continue
            # Prefer explicit explanatory wording; this is retrieval ranking, not semantic acceptance.
            located=re.search(pattern,passage,match_flags(term))
            if located is None:continue
            around=passage[max(0,located.start()-150):located.end()+450]
            explanatory=bool(re.search(r'refers? to|defined as|is (?:a|an|the)\b|characteri[sz]ed|involves?\b|describes?\b',around,re.I))
            try:ident=slug(term)
            except ValueError:ident='term-'+digest({'term':term})[:12]
            packet={'id':ident,'term':term,'source':row['source']['id'],'licence':row['source']['licence'],'source_record':record['record_id'],'revision':row['source']['pinned_version'],'source_snapshot_sha256':record['snapshot_sha256'],'url':record['url'],'text':passage,'source_label':record['term'],'source_kind':record['source_kind'],'source_character_range':[start,end],'support_review_status':'unreviewed'}
            content_hash=digest({key:packet.get(key) for key in ('term','source','source_record','revision','text')})
            if content_hash in blocked:continue
            decision=decide(packet)
            if not decision['eligible']:continue
            packet['planned_field']=decision['field'];packet['scope_decision']=decision
            candidates.append((not explanatory,0 if packet['source'].startswith('nimh-page-') else 1,match.start(),-len(passage),row,packet))
        if not candidates:gaps.append({'term':term,'reason':'No untried eligible definition passage remains in the retrieved sources'});continue
        _,_,_,_,row,packet=min(candidates,key=lambda c:c[:4])
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
    report={'source_recovery':'permitted-publication-passages-v2','prepared_packets':len(packets),'packet_set_hash':digest(packets),'individually_licensed_sources_used':len(selected_sources),'remaining_terms_with_retrieved_candidates':len(available),'no_eligible_passage':len(gaps),'existing_entries_untouched':len(entries),'legacy_definition_text_used':False,'paid_calls':0}
    (DEST/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    # The public inventory contains independent article metadata, never the private audit's term list.
    fields=['id','candidate','licence','licence_source_url','licence_confirmed','pinned_version','roles','decision','reason']
    with (ROOT/'reports/source-inventory.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");writer.writeheader()
        for source in document['sources']:
            out={k:source.get(k,'') for k in fields};out['roles']='; '.join(source['roles']);writer.writerow(out)
    return report

if __name__=='__main__':print(json.dumps(prepare(),indent=2))
