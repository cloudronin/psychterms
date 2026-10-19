"""Promote only exact approved definitions; import actual receipts without paid calls."""
import argparse,copy,csv,hashlib,io,json
from pathlib import Path
from core import ROOT,digest,semantic_hash,load_inputs
from hybrid_redraft import atomic
from publication_evidence import validate_record
from risk_registry import load_registry
from run_candidate_drafts import publish_candidate


def read(path):return json.loads(path.read_text())


def selection(root=ROOT):
    private=root/'.private';selected=[]
    pilot={r['headword_key']:r for r in read(private/'retune-pilot-source-context/cohort.json')}
    context=read(private/'retune-pilot-source-context/outcomes.json')
    wave=read(private/'redraft-wave-002/outcomes.json')
    corrections=read(private/'wave-two-editorial-corrections/outcomes.json')
    for filename,batch,lookup in [('pilot-claude-decisions.json','pilot-editorial',pilot),('wave-two-claude-decisions.json','wave-two-editorial',wave),('wave-two-correction-decisions.json','wave-two-corrections',corrections)]:
        for decision in read(root/'data'/filename)['decisions']:
            if decision['verdict']!='PASS':continue
            key=decision['headword_key'];accepted=copy.deepcopy(lookup[key]['accepted']);e=accepted['entry']
            if e['id']!=decision['entry_id'] or digest(e['definition'])!=decision['definition_hash'] or accepted['packet']['packet_hash']!=decision['packet_hash']:
                raise ValueError('Editorial decision does not bind the exact proposal')
            if batch=='pilot-editorial':
                if context[key]['qualified'] is not True:raise ValueError('Missing context-aware two-reader clearance')
                accepted['readers']=[context[key]['reads'][role] for role in ('reader_a','reader_b')]
                accepted['source_record_label']=pilot[key]['source_record_label']
            selected.append({'accepted':accepted,'decision':decision,'batch':batch})
    for outcome in read(private/'pilot-claude-redrafts/outcomes.json').values():
        a=outcome.get('accepted')
        if a and not a['field_issues']:
            selected.append({'accepted':copy.deepcopy(a),'decision':None,'batch':'pilot-model-corrections'})
    ids=[r['accepted']['entry']['id'] for r in selected]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate promotion ID')
    return selected


def prepare(root=ROOT):
    selected=selection(root);private=root/'.private'
    receipts={p.stem:p for p in sorted(private.glob('*/receipts/*.json'))}
    manifests={}
    for p in private.glob('*/registration.json'):
        m=read(p)
        if 'registration_hash' in m:manifests[m['registration_hash']]=m
    planned=[];external={}
    for row in selected:
        a=row['accepted'];e=a['entry'];packet=a['packet'];records={}
        if len(a['readers'])!=2 or len({a['draft']['model'],*(r['model'] for r in a['readers'])})!=3:
            raise ValueError('Missing two distinct non-drafting readers')
        for role,saved in [('draft',a['draft']),*zip(('reader_a','reader_b'),a['readers'])]:
            receipt=read(receipts[saved['receipt_id']]);m=manifests[saved['registration_hash']]
            records[role]={'saved':saved,'receipt':receipt,'registration':m}
            if a.get('source_record_label'):records[role]['source_record_label']=a['source_record_label']
            validate_record(records[role],role,e,packet)
        e['reader_reviews']=[{**{k:s[k] for k in ('model','receipt_id','request_hash','registration_hash','packet_hash')},
            'draft_model':a['draft']['model'],'definition_hash':digest(a['draft']['parsed']),
            'published_packet_hash':packet['packet_hash'],'passed':True,'reasons':[]}
            for s in a['readers']]
        e['hash']=semantic_hash(e)
        bundle={'schema_version':1,'reviewed_entry':copy.deepcopy(e),'packet':packet,'records':records,'editorial_decision':row['decision']}
        decision=row['decision']
        if decision:
            batch=row['batch'];field=decision.get('resolved_field',e['field'])
            external.setdefault(batch,[]).append((e,{'id':e['id'],'term':e['term'],'verdict':'PASS','reason':decision['reason'],
                'field':'ok' if field==e['field'] else 'suggest:'+field},field))
        e['publication_evidence']=digest(bundle)
        planned.append((e,packet,bundle,row['batch']))
    artifacts={}
    for batch,rows in external.items():
        out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=['id','term','verdict','reason','field'],lineterminator='\n');writer.writeheader();writer.writerows(r for e,r,f in rows)
        raw=out.getvalue().encode();m={'schema_version':1,'reader_model':'Claude (version unspecified; user-supplied review)',
            'artifact_sha256':hashlib.sha256(raw).hexdigest(),'entries':{}}
        for e,r,field in rows:
            m['entries'][e['id']]={'row_sha256':digest(r),'from_field':e['field'],'to_field':field,'verdict':'PASS',
                'before_entry_hash':e['hash'],'after_version':e['version'],'reviewed_definition_hash':digest({'definition':e['definition'],'field':e['field'],'packet_sufficient':True}),
                'packet_hash':e['packet_hash']}
        artifacts[batch]=(m,raw)
        for e,r,field in rows:
            e['external_review']={'batch':batch,'manifest_sha256':digest(m)};e['field']=field;e['hash']=semantic_hash(e)
    return planned,artifacts


def run(write=False,root=ROOT):
    planned,artifacts=prepare(root)
    if write:
        # All source and reader records have passed preflight before any entry is written.
        for batch,(m,raw) in artifacts.items():
            folder=root/'data/external-reviews'/batch;folder.mkdir(parents=True,exist_ok=True)
            atomic(folder/'manifest.json',m);(folder/'verdicts.csv').write_bytes(raw)
        registry,_=load_registry(root)
        for e,p,bundle,batch in planned:
            from publication_evidence import validate_bundle
            validate_bundle(e,p,bundle)
            atomic(root/'data/publication-evidence'/(e['id']+'.json'),bundle)
            publish_candidate(e,p,registry)
    report={'new_entries':len(planned),'editorial_and_two_readers':sum(bool(b['editorial_decision']) for e,p,b,batch in planned),
        'two_readers_only':sum(not b['editorial_decision'] for e,p,b,batch in planned),'paid_calls':0,'write':write,
        'entries':[{'id':e['id'],'term':e['term'],'field':e['field'],'version':e['version'],'batch':batch} for e,p,b,batch in planned],
        'excluded':['redundancy'],'prior_failed_entries_changed':0}
    if write:atomic(root/'reports/cleared-redrafts-publication.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='entries'},indent=2))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');run(p.parse_args().write)
