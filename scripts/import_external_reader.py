"""Import a supplied third-reader CSV after validating the complete split cohort."""
import argparse,csv,hashlib,io,json
from core import ROOT,digest,load_inputs,semantic_hash
from entry_status import readers

MODEL='Claude (version unspecified; user-supplied review)'

def plan(raw,entries,packets,history,fields):
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if not rows or len({r['id'] for r in rows})!=len(rows):raise ValueError('Empty or duplicate external verdicts')
    by_id={e['id']:e for e in entries}
    if {r['id'] for r in rows}!={i for i,e in history.items() if e['status']=='reviewed'}:raise ValueError('CSV must match the complete reviewed cohort')
    bindings={};edits=[]
    for row in rows:
        e=by_id[row['id']];p=packets[e['id']]
        if row['term']!=e['term'] or row['url']!='https://psychterms.org/terms/'+e['id']+'/':raise ValueError('CSV term or URL mismatch')
        if row['verdict'] not in ('PASS','FAIL') or not row['reason'].strip():raise ValueError('Missing verdict or reason')
        if row['headword_fit'] not in ('yes','no') or (row['verdict']=='PASS' and row['headword_fit']!='yes'):raise ValueError('Inconsistent headword-fit decision')
        proofs=readers(e,p)
        if {r['model'] for r in proofs if r['passed']}!={row['passed_by']} or {r['model'] for r in proofs if not r['passed']}!={row['rejected_by']}:raise ValueError('CSV original reader verdicts differ')
        field=row['field'][8:] if row['field'].startswith('suggest:') else e['field']
        if row['field']!='ok' and not row['field'].startswith('suggest:'):raise ValueError('Invalid suggested field')
        if field not in fields:raise ValueError('Unknown suggested field: '+field)
        if e.get('external_review'):raise ValueError('Entry already has an external reader')
        version=e['version']+int(field!=e['field'])
        bindings[e['id']]={'row_sha256':digest(row),'before_entry_hash':e['hash'],'from_field':e['field'],'to_field':field,
            'reviewed_definition_hash':digest({'definition':e['definition'],'field':e['field'],'packet_sufficient':True}),
            'packet_hash':e['packet_hash'],'verdict':row['verdict'],'before_version':e['version'],'after_version':version}
        edits.append((row,dict(e,field=field,version=version)))
    manifest={'schema_version':1,'reader_model':MODEL,'artifact_sha256':hashlib.sha256(raw).hexdigest(),
        'authority':'Vishnu supplied this CSV as Claude third-reader verdicts against the source packets and authorized its application.',
        'evidence_limits':'Model version and API receipts were not supplied. Snapshot hashes bind the current reviewed corpus at import; execution of the external review is human-attested, not independently reproduced.',
        'field_correction_policy':'The third reader approves the suggested field; earlier draft and reader proofs retain their original field binding. Definition, term, sources and packets must remain identical.',
        'entries':bindings}
    return manifest,edits

def run(path,batch):
    raw=path.read_bytes();entries,_,fields=load_inputs()
    fields=list(dict.fromkeys(fields+['personality','emotion and motivation']))
    packets={e['id']:json.loads((ROOT/'data/packets'/(e['id']+'.json')).read_text()) for e in entries}
    history=json.loads((ROOT/'data/status-history.json').read_text())['entries']
    manifest,edits=plan(raw,entries,packets,history,fields)
    folder=ROOT/'data/external-reviews'/batch
    if folder.exists():raise ValueError('Refusing to replace external review evidence')
    # All validation precedes writes. The source CSV is preserved byte-for-byte.
    folder.mkdir(parents=True)
    (folder/'verdicts.csv').write_bytes(raw)
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/fields.json').write_text(json.dumps({'schema_version':1,'fields':fields},ensure_ascii=False,indent=2)+'\n')
    decisions=json.loads((ROOT/'data/drop-decisions.json').read_text())
    pin=digest(manifest)
    for row,e in edits:
        e['external_review']={'batch':batch,'manifest_sha256':pin}
        e['hash']=semantic_hash(e)
        (ROOT/'data/entries'/(e['id']+'.json')).write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n')
        if row['verdict']=='FAIL':decisions['entries'][e['id']]={'reason':row['reason'],'authority':'User-supplied Claude third-reader FAIL','batch':batch}
    (ROOT/'data/drop-decisions.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2)+'\n')
    report={'batch':batch,'artifact_sha256':manifest['artifact_sha256'],'reader_model':MODEL,'entries_covered':len(edits),
        'passed':sum(r['verdict']=='PASS' for r,_ in edits),'dropped':sum(r['verdict']=='FAIL' for r,_ in edits),
        'retagged':sum(manifest['entries'][e['id']]['from_field']!=e['field'] for _,e in edits),'definition_changes':0,'packet_changes':0,
        'out_of_file_entry_changes':0,'new_paid_calls':0}
    (ROOT/'reports/external-reader-import.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv',type=__import__('pathlib').Path);p.add_argument('--batch',required=True);a=p.parse_args()
    print(json.dumps(run(a.csv,a.batch),indent=2))
