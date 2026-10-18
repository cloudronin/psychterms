"""Build-owned, evidence-derived, forward-only entry status and release counts."""
import argparse,collections,hashlib,json,re,subprocess
from core import ROOT,digest
from overlap_scan import words
from scope_rules import decide,independent_records

RANK={'candidate':0,'reviewed':1,'judged':2,'dropped':3}
BADGES={'candidate':'Candidate: drafted from the sources shown, not yet read by the two reviewers.',
 'reviewed':'Reviewed: passed one reader who did not draft it; copy check clear.',
 'judged':'Judged: passed two readers who did not draft it; copy check clear.',
 'dropped':'Dropped: removed with the reason shown.'}

def windows(text):
    w=words(text)
    for i in range(len(w)-14):yield hashlib.sha256(' '.join(w[i:i+15]).encode()).digest()

def copy_results(entries,packets):
    source=set()
    for p in packets.values():source.update(windows(p['text']))
    hits=set();owners={}
    for e in entries:
        for value in windows(e['definition']):
            if value in source:hits.add(e['id'])
            other=owners.setdefault(value,e['id'])
            if other!=e['id']:hits.update((other,e['id']))
    return {e['id']:'hit' if e['id'] in hits else 'clear' for e in entries}

def drafter(entry):
    if entry.get('draft_evidence'):return entry['draft_evidence']['model']
    if entry.get('model_review'):return entry['model_review']['draft_model']
    if entry.get('fixture'):return 'codex-initial-fixture'
    raise ValueError('Missing drafting identity: '+entry['id'])

def readers(entry,packet):
    records=([entry['model_review']] if entry.get('model_review') else [])+entry.get('reader_reviews',[])
    by_model={};expected=digest({'definition':entry['definition'],'field':entry['field'],'packet_sufficient':True})
    for r in records:
        if r.get('definition_hash')!=expected or r.get('packet_hash')!=packet.get('original_packet_hash',packet['packet_hash']):raise ValueError('Stale reader proof: '+entry['id'])
        if r.get('published_packet_hash',packet['packet_hash'])!=packet['packet_hash']:raise ValueError('Reader packet binding differs')
        if type(r.get('passed')) is not bool or not r.get('receipt_id') or not r.get('model'):raise ValueError('Missing reader receipt or verdict')
        for key in ('request_hash','registration_hash'):
            if not re.fullmatch(r'[a-f0-9]{64}',r.get(key,'')):raise ValueError('Missing reader request binding')
        if r.get('draft_model')!=drafter(entry):raise ValueError('Reader proof names a different drafter')
        if r['model']==drafter(entry):continue
        previous=by_model.get(r['model'])
        if previous is not None and previous['passed']!=r['passed']:raise ValueError('Conflicting reader outcomes for the same definition')
        by_model[r['model']]=r
    return list(by_model.values())

def check_forward(previous,current):
    for ident,old in previous.items():
        new=current.get(ident)
        if not new or RANK[new['status']]<RANK[old['status']]:raise ValueError('Status cannot move backward or disappear: '+ident)
        if old['status']=='dropped' and new['status']!='dropped':raise ValueError('Dropped status is terminal: '+ident)

def check_snapshot(history,current):
    if history!=current:raise ValueError('Committed status history is stale; regenerate it with entry_status.py --write-history')

def prepare(entries,root=ROOT,history=None,scope=True):
    forbidden={'status','checks','released','release_versions'}
    for e in entries:
        if forbidden & e.keys():raise ValueError('Status, checks and released are build-owned')
    packets={e['id']:json.loads((root/'data/packets'/(e['id']+'.json')).read_text()) for e in entries}
    copies=copy_results(entries,packets);independent=independent_records(root) if scope else {}
    drop_path=root/'data/drop-decisions.json';explicit=json.loads(drop_path.read_text())['entries'] if drop_path.exists() else {}
    release_path=root/'data/numbered-releases.json';releases=json.loads(release_path.read_text())['releases'] if release_path.exists() else []
    output=[];snapshot={};model_names=set()
    for e in entries:
        record=packets[e['id']];proofs=readers(e,record);passing=[r for r in proofs if r['passed']];failing=[r for r in proofs if not r['passed']]
        model_names.update(r['model'] for r in proofs)
        eligibility=decide(record,independent) if scope else {'eligible':True}
        reason=explicit.get(e['id'],{}).get('reason')
        if not eligibility['eligible']:reason=eligibility['reason']
        if len(failing)>=2:reason='; '.join(sorted({reason for r in failing for reason in r.get('reasons',[]) if reason})) or 'Both independent readers rejected the definition.'
        status='dropped' if reason else 'judged' if len(passing)>=2 else 'reviewed' if len(passing)==1 else 'candidate'
        if status!='dropped' and copies[e['id']]!='clear':raise ValueError('15-word copy hit requires redraft before publication: '+e['id'])
        versions=[r['version'] for r in releases if r.get('entries',{}).get(e['id'])==e['hash']]
        if versions and status=='dropped':raise ValueError('Dropped entry cannot be released')
        current={**e,'status':status,'checks':{'readers':f'{min(len(passing),2)}/2','copy':copies[e['id']]},'released':bool(versions),'release_versions':versions,'drafter':drafter(e)}
        current.pop('review_status',None)
        if reason:current['drop_reason']=reason
        snapshot[e['id']]={'status':status,'term':e['term'],'version':e['version'],'definition_hash':digest(e['definition'])}
        if reason:snapshot[e['id']]['reason']=reason
        output.append(current)
    if history is None:
        hp=root/'data/status-history.json';history=json.loads(hp.read_text())['entries'] if hp.exists() else {}
    check_forward(history,snapshot)
    counts={s:sum(e['status']==s for e in output) for s in RANK};counts['released']=sum(e['released'] for e in output)
    report={'schema_version':1,'status_counts':counts,'reader_models':sorted(model_names),'copy_threshold_words':15,'copy_scope':'All pinned public source packets and cross-entry definitions','comparison_hash':digest(sorted((k,p['packet_hash']) for k,p in packets.items())),'entries':snapshot}
    return output,report

def release_note(report,version='Public review preview'):
    counts=report['status_counts']
    lines=['# PsychTerms: '+version,'','Status is set by the build from reader evidence and copy checks. The drafter never counts as a reader.','',
      '| Status | Entries |','|---|---:|',*[f'| {s.capitalize()} | {counts[s]} |' for s in ('candidate','reviewed','judged','dropped')],f'| Included in a numbered release | {counts["released"]} |','',
      'Released is an additional marker, not a fifth review status. Candidate entries are public drafts; a citation is not a reader pass.','',
      'Reader models recorded: '+(', '.join(report['reader_models']) or 'none')+'.','',
      'Copy comparison: '+report['copy_scope']+'. Fifteen-word threshold; comparison SHA-256: '+report['comparison_hash']+'.','',
      'Dropped entries are removed from term pages and search; their names and reasons appear on the Dropped page.','']
    return '\n'.join(lines)

if __name__=='__main__':
    from core import load_inputs
    p=argparse.ArgumentParser();p.add_argument('--write-history',action='store_true');p.add_argument('--base');a=p.parse_args()
    entries,report=prepare(load_inputs()[0])
    if a.base:
        previous=subprocess.run(['git','show',a.base+':data/status-history.json'],cwd=ROOT,text=True,capture_output=True)
        if previous.returncode==0:check_forward(json.loads(previous.stdout)['entries'],report['entries'])
        elif subprocess.run(['git','cat-file','-e',a.base+'^{commit}'],cwd=ROOT,capture_output=True).returncode:raise ValueError('Cannot verify previous status history: invalid Git base')
    if not a.write_history:check_snapshot(json.loads((ROOT/'data/status-history.json').read_text())['entries'],report['entries'])
    if a.write_history:(ROOT/'data/status-history.json').write_text(json.dumps({'schema_version':1,'entries':report['entries']},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='entries'},indent=2))
