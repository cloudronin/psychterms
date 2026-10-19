"""Import the 70-entry editorial verdicts and redraft only 24 eligible failures."""
import argparse,collections,copy,csv,hashlib,json,concurrent.futures
from pathlib import Path
from core import ROOT,digest,semantic_hash,load_inputs
from hybrid_redraft import atomic
from retune_api import Client,ENDPOINT,hashes
from retune_protocol import MODELS,PRICES,PROMPTS,SCHEMAS,MAX_TOKENS
from retune_pilot import process,audit
from run_candidate_drafts import window_hashes
DEST=ROOT/'.private/pilot-claude-redrafts'
PARENT=ROOT/'.private/retune-pilot-source-context'
EXCLUDED={'superconducting quantum interference device','blank screen'}
def read(p):return json.loads(p.read_text())
def import_verdicts(path,cohort,outcomes,fields):
    with path.open(newline='') as f:rows=list(csv.DictReader(f))
    expected={r['accepted']['entry']['id']:r for r in cohort if outcomes[r['headword_key']]['qualified']}
    if len(rows)!=70 or len({r['entry_id'] for r in rows})!=70 or set(expected)!={r['entry_id'] for r in rows}:raise ValueError('Verdicts must match exactly the 70 qualified proposals')
    decisions=[]
    for v in rows:
        old=expected[v['entry_id']];e=old['accepted']['entry']
        if v['headword_key']!=old['headword_key'] or v['verdict'] not in ('PASS','FAIL') or not v['reason'].strip():raise ValueError('Invalid verdict identity or reason')
        if v['suggested_field'] and v['suggested_field'] not in fields:raise ValueError('Unknown field')
        decisions.append({**v,'original_field':e['field'],'resolved_field':v['suggested_field'] or e['field'],'staged_status':'judged' if v['verdict']=='PASS' else 'dropped' if v['headword_key'] in EXCLUDED else 'redraft','definition_hash':digest(e['definition']),'packet_hash':old['accepted']['packet']['packet_hash']})
    if collections.Counter(d['verdict'] for d in decisions)!={'PASS':44,'FAIL':26} or sum(bool(d['suggested_field']) for d in decisions)!=20:raise ValueError('Unexpected verdict totals')
    if {d['headword_key'] for d in decisions if d['staged_status']=='dropped'}!=EXCLUDED:raise ValueError('The two scope exclusions must fail')
    return decisions

def prepare(path,dest=DEST):
    if (dest/'registration.json').exists():raise ValueError('Do not overwrite a frozen correction run')
    cohort=read(PARENT/'cohort.json');outcomes=read(PARENT/'outcomes.json');_,sources,fields=load_inputs()
    decisions=import_verdicts(path,cohort,outcomes,fields);by_key={r['headword_key']:r for r in cohort};rows=[]
    for d in decisions:
        if d['staged_status']!='redraft':continue
        old=by_key[d['headword_key']];p=copy.deepcopy(old['accepted']['packet'])
        original_hash=p['packet_hash'];p.update(source_label=old['source_record_label'],publisher_aliases=old['publisher_aliases'],planned_field=d['resolved_field'])
        p['id']=old['accepted']['entry']['id'].replace('-v2-','-v3-');p['packet_hash']=digest({k:v for k,v in p.items() if k!='packet_hash'})
        rows.append({'headword_key':d['headword_key'],'term':p['term'],'field':d['resolved_field'],'packet':p,'original_packet_hash':original_hash,'supersedes_proposal':d['entry_id'],'original_source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest()})
    assert len(rows)==24
    dest.mkdir(parents=True,exist_ok=True);atomic(dest/'cohort.json',rows);(dest/'verdicts.csv').write_bytes(path.read_bytes())
    atomic(ROOT/'data/pilot-claude-decisions.json',{'scope':'Private pilot proposal overlay only; not canonical entries or publication. Retags apply to all 20 staged records; failed versions are retained.','verdict_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'decisions':decisions})
    # Freeze the old comparison plus all source passages and the 44 retained definitions.
    raw=(ROOT/'.private/retune-pilot-v8/comparison.bin').read_bytes();index={raw[i:i+32] for i in range(0,len(raw),32)}
    for r in cohort:index.update(window_hashes(r['accepted']['packet']['text']))
    for d in decisions:
        if d['verdict']=='PASS':index.update(window_hashes(by_key[d['headword_key']]['accepted']['entry']['definition']))
    raw=b''.join(sorted(index));(dest/'comparison.bin').write_bytes(raw)
    m={'line':'pilot-claude-same-packet-corrections-v1','development_only':True,'authorization':'Vishnu provided 44 PASS / 26 FAIL and 20 retags, requested draft/reader term-meaning corrections before wave two, and identified 24 same-packet redrafts.','models':MODELS,'prices_per_million':PRICES,'endpoint':ENDPOINT,'total_redraft_cap_usd':200,'shared_budget_ledger':'.private/hybrid-redraft/budget.sqlite','prior_spend_included':True,'transport_schema_retries':1,'code_hashes':hashes(),'prompts':PROMPTS,'schemas':SCHEMAS,'max_completion_tokens':MAX_TOKENS,'cohort_hash':digest(rows),'decision_hash':digest(decisions),'verdict_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'comparison_sha256':hashlib.sha256(raw).hexdigest(),'source_inventory_hash':digest(sources),'parent_cohort_sha256':hashlib.sha256((PARENT/'cohort.json').read_bytes()).hexdigest(),'workers':4,'publication':False,'wave_two':False,'no_new_sources':True,'source_text_unchanged':True,'entry_version':3,'copy_words':15,'attempt_policy':'One new draft per admitted same packet; no iterative content retries or forced generalization. Insufficient packets remain redraft.'}
    m['registration_hash']=digest(m);atomic(dest/'registration.json',m);atomic(ROOT/'data/pilot-claude-redraft-registration.json',m)
    print(json.dumps({'redrafts':len(rows),'retags':20,'retained':44,'dropped':2,'registration_hash':m['registration_hash']}))

def run(dest=DEST):
    m=read(dest/'registration.json');rows=read(dest/'cohort.json');_,sources,fields=load_inputs();client=Client(m,dest);client.verify()
    if digest(rows)!=m['cohort_hash'] or digest(sources)!=m['source_inventory_hash']:raise ValueError('Frozen inputs changed')
    raw=(dest/'comparison.bin').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=m['comparison_sha256']:raise ValueError('Copy index changed')
    index={raw[i:i+32] for i in range(0,len(raw),32)};path=dest/'outcomes.json';done=read(path) if path.exists() else {}
    def one(row):return process(row,[row['packet']],client,sources,fields,index)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(one,r) for r in rows if r['headword_key'] not in done]
        for f in concurrent.futures.as_completed(futures):
            v=f.result();done[v['headword_key']]=v;atomic(path,done);atomic(dest/'progress.json',{'complete':len(done),'total':24,'provisional_pass':sum(bool(v['accepted']) for v in done.values())})
    accepted=[]
    for row in sorted(rows,key=lambda r:r['headword_key']):
        a=done[row['headword_key']]['accepted']
        if a:
            try:audit(a,m,dest,index)
            except ValueError as error:
                done[row['headword_key']]['accepted']=None;done[row['headword_key']]['reason']='Final evidence/copy audit: '+str(error);continue
            a['entry']['version']=3;a['entry']['hash']=semantic_hash(a['entry']);a['supersedes_proposal']=row['supersedes_proposal'];a['original_packet_hash']=row['original_packet_hash']
            if hashlib.sha256(a['packet']['text'].encode()).hexdigest()!=row['original_source_text_sha256']:raise ValueError('Source text changed')
            atomic(dest/'accepted'/(a['entry']['id']+'.json'),a);accepted.append(a);index.update(window_hashes(a['entry']['definition']))
    atomic(path,done)
    summary={'redrafts':24,'passed_two_readers_and_copy':len(accepted),'retained_claude_pass':44,'excluded':2,'remaining_redraft':24-len(accepted),'retags_recorded':20,'field_flags':sum(bool(a['field_issues']) for a in accepted),'total_redraft_budget':client.budget.summary(),'published':0,'wave_two_started':False,'registration_hash':m['registration_hash']}
    atomic(dest/'report.json',summary);atomic(ROOT/'reports/pilot-claude-redrafts.json',summary)
    lines=['# Claude-reviewed pilot corrections','',f'Claude verdicts: 44 PASS, 26 FAIL; 20 retags recorded. Two excluded headwords: superconducting quantum interference device (out of scope), blank screen (not a standalone term).','',f'Of 24 same-packet redrafts, **{len(accepted)}** passed both new independent readers and the 15-word copy scan; **{24-len(accepted)}** remain unresolved. These are fresh model-reviewed proposals, not new Claude verdicts. The 44 earlier Claude passes remain separate. No publication or wave two.','', '| Term | Result | Reason / flags |','|---|---|---|']
    for row in rows:
        v=done[row['headword_key']];a=v['accepted'];reasons=[]
        if a:reasons=a['field_issues']
        else:
            reasons=[f['saved']['parsed']['reason'] for f in v['fits'] if f['saved']['parsed']['answer']=='no']
            for attempt in v['attempts']:
                reasons += [attempt.get('reason','')]+[reason for role in ('reader_a','reader_b') if role in attempt for reason in attempt[role]['parsed']['reasons']]
            reasons += [v['reason']]
        lines.append('| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in (row['term'],'model passes' if a else 'redraft','; '.join(x for x in reasons if x)))+' |')
    (ROOT/'reports/pilot-claude-redrafts.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);p.add_argument('--verdicts',type=Path);a=p.parse_args()
    prepare(a.verdicts) if a.command=='prepare' else run()
