"""Validate and import reported local replacements; default is a private dry run."""
import argparse,json,shutil
from pathlib import Path
from core import ROOT,digest,semantic_hash,load_inputs,validate_entry
from local_redraft import DEST,registration,audit_accepted,summarize,atomic
from local_receipts import validate as validate_local
from entry_status import copy_results
from redraft_policy import validate_replacements
from risk_registry import load_registry
from run_candidate_drafts import publish_candidate

def plan(wave,dest=DEST):
    m,cohort=registration(dest);folder=dest/f'wave-{wave:03d}'
    summary=json.loads((folder/'report.json').read_text());marker=json.loads((folder/'reported.json').read_text())
    if not summary['complete'] or marker['report_hash']!=digest(summary):raise ValueError('A complete emitted wave report is required before import')
    outcomes=json.loads((folder/'outcomes.json').read_text());rows=[r for r in cohort['cohort'] if r['wave']==wave]
    if summarize(wave,rows,outcomes,m)!=summary:raise ValueError('Wave outcomes differ from their report')
    entries,sources,fields=load_inputs();history=json.loads((ROOT/'data/status-history.json').read_text())['entries']
    packets={e['id']:json.loads((ROOT/'data/packets'/(e['id']+'.json')).read_text()) for e in entries}
    batch=f'{"hybrid" if m.get("line")=="hybrid-redrafts-v1" else "local"}-redraft-wave-{wave:03d}';preview=folder/'import-preview';evidence=preview/'data/local-runs'/batch
    atomic(evidence/'registration.json',m);planned=[];existing={e['id']:e for e in entries}
    for row in outcomes.values():
        if row['status']!='judged':continue
        accepted=json.loads((folder/'accepted'/(row['new_entry_id']+'.json')).read_text())
        entry,receipts=audit_accepted(accepted,m,dest);packet=accepted['packet']
        entry['local_run']['batch']=batch;entry['hash']=semantic_hash(entry)
        for role,receipt in receipts.items():atomic(evidence/'receipts'/(entry['local_run']['receipts'][role]+'.json'),receipt)
        validate_local(entry,packet,preview)
        base={k:v for k,v in entry.items() if k!='local_run'};base['hash']=semantic_hash(base);validate_entry(base,sources,fields)
        if entry['id'] in existing:
            if existing[entry['id']]!=entry or packets[entry['id']]!=packet:raise ValueError('Refusing to overwrite an existing entry or packet')
            continue
        planned.append((entry,packet));packets[entry['id']]=packet
    current=[dict(e,status=history[e['id']]['status']) for e in entries]
    proposed=[dict(e,status='judged') for e,p in planned]
    validate_replacements(current+proposed,packets)
    copies=copy_results(entries+[e for e,p in planned],packets)
    if any(v!='clear' for v in copies.values()):raise ValueError('Source/cross-entry copy scan requires review before import')
    return m,batch,evidence,planned

def execute(wave,dest=DEST,write=False):
    m,batch,evidence,planned=plan(wave,dest)
    if write and planned:
        target=ROOT/'data/local-runs'/batch
        for path in evidence.rglob('*.json'):
            relative=path.relative_to(evidence);out=target/relative
            if out.exists() and out.read_bytes()!=path.read_bytes():raise ValueError('Refusing to overwrite local inference evidence')
        for path in evidence.rglob('*.json'):
            out=target/path.relative_to(evidence);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
        registry,_=load_registry()
        for entry,packet in planned:publish_candidate(entry,packet,registry)
    result={'wave':wave,'new_judged_entries':len(planned),'version':2,'write':write,'old_entries_changed':0,'paid_usd':__import__('budget').Budget(dest/'budget.sqlite',int(m['paid_cap_usd']*1e6)).summary()['receipted_usd'] if m.get('line')=='hybrid-redrafts-v1' else 0,
            'next_checks':['entry_status.py --write-history','build_also_see.py','npm run build','check_site.py','check_copy.py']}
    print(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--hybrid',action='store_true');p.add_argument('--wave',type=int,default=1);p.add_argument('--dest',type=Path,default=DEST);p.add_argument('--write',action='store_true');a=p.parse_args()
    if a.hybrid:
        from hybrid_redraft import DEST,registration,audit_accepted,summarize
        a.dest=DEST if a.dest==ROOT/'.private/local-redraft' else a.dest
    execute(a.wave,a.dest,a.write)
