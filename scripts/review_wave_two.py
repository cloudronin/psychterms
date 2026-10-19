"""Apply exact wave-two editorial decisions; test taxonomy and retry two failures."""
import argparse,csv,copy,collections,concurrent.futures,hashlib,json
from pathlib import Path
from core import ROOT,digest,semantic_hash,load_inputs
from hybrid_redraft import atomic
from retune_api import Client,ENDPOINT,hashes,OutputError
from retune_protocol import MODELS,PRICES,PROMPTS,SCHEMAS,MAX_TOKENS
from retune_pilot import process,audit
from run_candidate_drafts import window_hashes
PARENT=ROOT/'.private/redraft-wave-002'
DEST=ROOT/'.private/wave-two-editorial-corrections'
EXCLUDED={'dry eyes','graph theory','henle fiber','shape','superposition'}
REDRAFT={'preparatory response','redundancy'}
def read(p):return json.loads(p.read_text())
def decisions(path,old,fields):
    with path.open(newline='') as f:rows=list(csv.DictReader(f))
    expected={v['accepted']['entry']['id']:v for v in old.values() if v['accepted']}
    if len(rows)!=81 or len({r['entry_id'] for r in rows})!=81 or set(expected)!={r['entry_id'] for r in rows}:raise ValueError('Must match all 81 wave-two proposals exactly')
    result=[]
    for r in rows:
        o=expected[r['entry_id']];e=o['accepted']['entry']
        if r['headword_key']!=o['headword_key'] or r['verdict'] not in ('PASS','FAIL') or not r['reason'].strip() or (r['suggested_field'] and r['suggested_field'] not in fields):raise ValueError('Invalid verdict identity, reason or field')
        if (r['headword_key'] in EXCLUDED|REDRAFT)!=(r['verdict']=='FAIL'):raise ValueError('Failure disposition differs from supplied instructions')
        result.append({**r,'original_field':e['field'],'resolved_field':r['suggested_field'] or e['field'],'staged_status':'judged' if r['verdict']=='PASS' else 'dropped' if r['headword_key'] in EXCLUDED else 'redraft','definition_hash':digest(e['definition']),'packet_hash':o['accepted']['packet']['packet_hash']})
    if collections.Counter(r['verdict'] for r in result)!={'PASS':74,'FAIL':7} or sum(bool(r['suggested_field']) for r in result)!=36:raise ValueError('Unexpected decision totals')
    return result

def prepare(path):
    if (DEST/'registration.json').exists():raise ValueError('Never overwrite a registered review run')
    old=read(PARENT/'outcomes.json');_,sources,fields=load_inputs();ds=decisions(path,old,fields);rows=[];calibration=[]
    for d in ds:
        a=old[d['headword_key']]['accepted'];p=copy.deepcopy(a['packet'])
        if d['verdict']=='PASS':calibration.append({'headword_key':d['headword_key'],'packet':p,'expected_field':d['resolved_field']})
        elif d['headword_key'] in REDRAFT:
            p['id']=p['id'].replace('-v2-','-v3-');p['planned_field']=d['resolved_field'];p['packet_hash']=digest({k:v for k,v in p.items() if k!='packet_hash'})
            rows.append({'headword_key':d['headword_key'],'term':p['term'],'field':d['resolved_field'],'packet':p,'supersedes_proposal':d['entry_id'],'source_text_sha256':hashlib.sha256(p['text'].encode()).hexdigest()})
    DEST.mkdir(parents=True,exist_ok=True);(DEST/'verdicts.csv').write_bytes(path.read_bytes());atomic(DEST/'cohort.json',rows);atomic(DEST/'field-calibration.json',calibration)
    atomic(ROOT/'data/wave-two-claude-decisions.json',{'scope':'Staged proposal decisions and retags, not canonical definition edits or publication.','verdict_file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'decisions':ds})
    raw=(PARENT/'comparison.bin').read_bytes();index={raw[i:i+32] for i in range(0,len(raw),32)}
    for d in ds:
        if d['verdict']=='PASS':index.update(window_hashes(old[d['headword_key']]['accepted']['entry']['definition']))
    raw=b''.join(sorted(index));(DEST/'comparison.bin').write_bytes(raw)
    m={'line':'wave-two-editorial-corrections-v2','authorization':'Vishnu supplied 74 PASS, 7 FAIL and 36 retags; five scope exclusions, two same-packet redrafts, and defined 14-field tagging with constrained uncertainty before wave three.','models':MODELS,'prices_per_million':PRICES,'endpoint':ENDPOINT,'total_redraft_cap_usd':200,'shared_budget_ledger':'.private/hybrid-redraft/budget.sqlite','prior_spend_included':True,'transport_schema_retries':1,'code_hashes':hashes(),'prompts':PROMPTS,'schemas':SCHEMAS,'max_completion_tokens':MAX_TOKENS,'field_tagging_required':True,'cohort_hash':digest(rows),'field_calibration_hash':digest(calibration),'source_inventory_hash':digest(sources),'decisions_hash':digest(ds),'comparison_sha256':hashlib.sha256(raw).hexdigest(),'original_outcomes_hash':digest(old),'publication':False,'wave_three_started':False,'supersedes_registration_hash':'5c9c60f0ddfc843ea42103155d6c5d44c08417d36e233d67c81633115f5ab49e','prior_failure':'V1 incorrectly required literal context evidence for confident classifications and abstentions; quoted formatting rejected 73/74 responses. No classification accuracy claim is made from that run. All costs, receipts, reservations and executed code are retained.','attempt_policy':'One draft per fitting original packet, bounded identical-request schema/transport retries, no iterative repair or invented general meaning.'}
    m['registration_hash']=digest(m);atomic(DEST/'registration.json',m);atomic(ROOT/'data/wave-two-corrections-registration.json',m);print(json.dumps({'pass':74,'scope_dropped':5,'same_packet_redrafts':2,'retags':36,'tagger_comparison_entries':len(calibration),'registration_hash':m['registration_hash']}))

def run():
    m=read(DEST/'registration.json');rows=read(DEST/'cohort.json');cal=read(DEST/'field-calibration.json');_,sources,fields=load_inputs();client=Client(m,DEST);client.verify()
    if digest(rows)!=m['cohort_hash'] or digest(cal)!=m['field_calibration_hash'] or digest(sources)!=m['source_inventory_hash']:raise ValueError('Frozen inputs changed')
    outputs=DEST/'field-results.json';tagged=read(outputs) if outputs.exists() else {}
    def tag(r):
        try:return r['headword_key'],{'saved':client.call('field',r['packet'],''),'expected_field':r['expected_field']}
        except OutputError as error:return r['headword_key'],{'unresolved':str(error),'expected_field':r['expected_field']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for key,v in pool.map(tag,[r for r in cal if r['headword_key'] not in tagged]):tagged[key]=v;atomic(outputs,tagged)
    raw=(DEST/'comparison.bin').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=m['comparison_sha256']:raise ValueError('Copy index changed')
    index={raw[i:i+32] for i in range(0,len(raw),32)};done=read(DEST/'outcomes.json') if (DEST/'outcomes.json').exists() else {};accepted=[]
    for row in rows:
        if row['headword_key'] not in done:done[row['headword_key']]=process(row,[row['packet']],client,sources,fields,index)
        a=done[row['headword_key']]['accepted']
        if a:
            try:audit(a,m,DEST,index)
            except ValueError as error:done[row['headword_key']]['accepted']=None;done[row['headword_key']]['reason']='Final audit: '+str(error);continue
            a['entry']['version']=3;a['entry']['hash']=semantic_hash(a['entry']);a['supersedes_proposal']=row['supersedes_proposal']
            if hashlib.sha256(a['packet']['text'].encode()).hexdigest()!=row['source_text_sha256']:raise ValueError('Same-packet source prose changed')
            atomic(DEST/'accepted'/(a['entry']['id']+'.json'),a);accepted.append(a);index.update(window_hashes(a['entry']['definition']))
        atomic(DEST/'outcomes.json',done)
    values=[v for v in tagged.values() if 'saved' in v];confident=[v for v in values if v['saved']['parsed']['confident']];abstained=[v for v in values if v['saved']['parsed']['field'] is None]
    matches=sum(v['saved']['parsed']['field']==v['expected_field'] for v in values)
    receipt_cost=sum(read(p)['paid_usd'] for p in (DEST/'receipts').glob('*.json'))
    summary={'claude_pass':74,'claude_fail':7,'retags':36,'scope_headwords_excluded':5,'same_packet_redrafts':2,'corrections_passing_two_readers_and_copy':len(accepted),'remaining_redraft':2-len(accepted),'field_tagger':{'comparison_entries':len(cal),'matching_claude':matches,'confident':len(confident),'confident_matching_claude':sum(v['saved']['parsed']['field']==v['expected_field'] for v in confident),'abstained':len(abstained),'unresolved_responses':len(cal)-len(values),'uncertain_routed':len(values)-len(confident)-len(abstained),'development_comparison_not_held_out':True},'run_receipted_usd':round(receipt_cost,6),'shared_budget':client.budget.summary(),'published':0,'wave_three_started':False,'registration_hash':m['registration_hash']}
    atomic(DEST/'report.json',summary);atomic(ROOT/'reports/wave-two-editorial-review.json',summary)
    lines=['# Wave-two editorial decisions and field tagging','', 'Claude verdicts: **74 PASS, 7 FAIL and 36 retags**. Scope exclusions: dry eyes, graph theory, Henle fiber, shape and superposition. They are removed from the active candidate pool and persisted in the headword exclusion registry. The two narrowing failures keep their original source packets for this retry; old failed definitions and earlier verdicts are unchanged.','',f"Same-packet corrections passing both fresh readers and the 15-word scan: **{len(accepted)}/2**. No definitions were published and wave three did not start.",'',f"Field guide: all 14 fields have one-line definitions. The tagger gets source packets and labels, not inherited tags or Claude's answers. On the 74 Claude-passed entries it matches **{matches}/74** fields; **{len(abstained)}** abstentions and **{len(cal)-len(values)}** unverifiable responses. This is an inspected development comparison, not held-out accuracy. Claude's 36 retags remain authoritative in the staged decisions; classifier output does not overwrite them.",'',f"Receipted correction and taxonomy-check usage: **${receipt_cost:.6f}**, within the same original $200 ledger.",'','## Field comparison','','| Term | Claude field | Tagger field | Confident |','|---|---|---|---|']
    for key,v in sorted(tagged.items()):
        p=v.get('saved',{}).get('parsed',{});lines.append('| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in (key,v['expected_field'],p.get('field','unverified'),p.get('confident','unverified')))+' |')
    lines += ['','## Correction outcomes','','| Term | Result | Reason |','|---|---|---|']
    for row in rows:
        v=done[row['headword_key']];lines.append('| '+' | '.join(str(x or '').replace('|','/').replace('\n',' ') for x in (row['term'],'model passes' if v['accepted'] else 'redraft',v['reason']))+' |')
    (ROOT/'reports/wave-two-editorial-review.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);p.add_argument('--verdicts',type=Path);a=p.parse_args();prepare(a.verdicts) if a.command=='prepare' else run()
