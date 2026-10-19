"""No inference: verify old-entry immutability, expose diagnostics and reviewable examples."""
import argparse,collections,csv,hashlib,json,random,time
from pathlib import Path
from core import ROOT,digest
from hybrid_redraft import atomic

def finish(dest,wait=False):
    while True:
        state=json.loads((dest/'run-state.json').read_text())
        if state['stage']=='complete':break
        if state['stage'] in ('paused','calibration_failed'):return state
        if not wait:raise ValueError('Pilot is still running')
        time.sleep(10)
    original=json.loads((ROOT/'.private/hybrid-redraft/registration.json').read_text())
    for ident,sha in original['failed_snapshots'].items():
        if digest(json.loads((ROOT/'data/entries'/(ident+'.json')).read_text()))!=sha:raise ValueError('An original failed entry changed: '+ident)
    report=json.loads((dest/'report.json').read_text());cohort=json.loads((dest/'cohort.json').read_text());outcomes=json.loads((dest/'outcomes.json').read_text())
    if report['headwords']!=500 or len(outcomes)!=500:raise ValueError('Incomplete 500-item development report')
    diagnostics={}
    cohort_by_key={r['headword_key']:r for r in cohort['rows']}
    packet_fields={'same-packets':'packets','rescue':'rescue_packets','new-sources':'new_source_packets'}
    original_summary=dest/'report-dispatch-summary.json'
    if not original_summary.exists():atomic(original_summary,report)
    for phase in ('same-packets','rescue','new-sources'):
        rows=json.loads((dest/(phase+'.json')).read_text())
        actual_missing=sum(not cohort_by_key[k][packet_fields[phase]] for k in rows)
        report['phase_counts'][phase]['no_packets']=actual_missing
        report['phase_counts'][phase]['unresolved_fit_headwords']=sum(any(e['role']=='fit' for e in r.get('output_errors',[])) and not any(f['saved']['parsed']['answer']=='yes' for f in r['fits']) for r in rows.values())
        diagnostics[phase]={'actual_no_packet_headwords':actual_missing,'headwords':len(rows),'proposals_before_cross_entry_audit':sum(bool(r['accepted']) for r in rows.values()),
            'failure_reasons':dict(collections.Counter(r['reason'] for r in rows.values() if not r['accepted'])),
            'unverified_output_events':sum(len(r.get('output_errors',[])) for r in rows.values()),
            'failed_attempt_reasons':dict(collections.Counter(a.get('reason','passed') for r in rows.values() for a in r['attempts']))}
    report['reporting_amendment']='Missing-packet counts use the frozen packet arrays, not the number of completed fit responses; model-output failures are reported separately. Qualification counts and receipts are unchanged.'
    atomic(dest/'report.json',report);atomic(ROOT/('reports/'+dest.name+'.json'),report)
    atomic(dest/'run-state.json',{**state,**report,'stage':'complete'})
    accepted=[]
    for row in outcomes:
        if row['status']=='judged':accepted.append(json.loads((dest/'accepted'/(row['new_entry_id']+'.json')).read_text()))
    if len(accepted)!=report['total_passed']:raise ValueError('Accepted staging count differs from audited report')
    sources={s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text())['sources']}
    csvpath=ROOT/('reports/'+dest.name+'-outcomes.csv')
    with csvpath.open('w') as f:
        w=csv.DictWriter(f,fieldnames=['term','outcome','stage','reason','field_review_required'],lineterminator='\n');w.writeheader()
        for row in outcomes:w.writerow({'term':row['term'],'outcome':row['status'],'stage':row['stage'],'reason':row['reason'] or '', 'field_review_required':bool(row['field_issues'])})
    sample=random.Random(20261018).sample(accepted,min(20,len(accepted)))
    lines=['','## Reviewed development proposals for inspection','',
      'These are staged development proposals, not published term pages. All have actual two-reader passes and clear copy checks; any field flag remains a publication hold. Source facts and model decisions have not received clinician validation. The controls were authored and labelled by the execution agent, not by a clinician.','']
    for a in sample:
        e=a['entry'];p=a['packet'];source=sources[p['source']]
        lines += ['### '+e['term'],'',e['definition'],'',f'Field: {e["field"]}. Source: [{source["candidate"]}]({p["url"]}). {p["licence"]}.',
          source.get('attribution',''),f'Source packet SHA-256: `{p["packet_hash"]}`.','']
        if a['field_issues']:lines+=['Field review: '+'; '.join(a['field_issues']),'']
        for ref in e['provenance']:
            if ref['source']=='hpo-2026-09-01':lines +=[f'HPO reference only: [{ref["scope"]}]({ref["locator"]}); {ref["revision"]}. No HPO prose was used for drafting.','']
    lines += ['## Failure diagnostics','', 'Unverified outputs and exhausted transport attempts remain unresolved; they are not evidence that a term lacks a source.','', '```json',json.dumps(diagnostics,indent=2),'```','']
    md=ROOT/('reports/'+dest.name+'.md');text=md.read_text();marker='\n## Reviewed development proposals for inspection'
    if marker in text:text=text.split(marker)[0]
    md.write_text(text+'\n'.join(lines))
    result={'stage':'review_artifacts_ready','headwords':500,'total_passed':len(accepted),'original_entries_unchanged':len(original['failed_snapshots']),
       'same_packet_passed':report['same_packet_passed'],'rescue_added':report['rescue_added'],'new_source_added':report['new_source_added'],
       'field_review_required':report['field_review_required'],'report':'reports/'+dest.name+'.md','diagnostics':diagnostics,'report_sha256':hashlib.sha256(md.read_bytes()).hexdigest()}
    atomic(dest/'finalization.json',result);print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dest',type=Path,default=ROOT/'.private/retune-pilot-v8');p.add_argument('--wait',action='store_true');a=p.parse_args();finish(a.dest,a.wait)
