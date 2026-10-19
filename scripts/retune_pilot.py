"""Development-only pilot replay: controls, fixed-packet comparison, then retrieval rescue."""
import argparse,collections,math,concurrent.futures,fcntl,hashlib,json,random,sys,time
from pathlib import Path
from core import ROOT,digest,semantic_hash,load_inputs,validate_entry
from hybrid_redraft import atomic
from retune_api import Client,RunError,LEDGER,ENDPOINT,hashes,audit_saved,OutputError,evidence_manifest
from retune_protocol import MODELS,PRICES,PROMPTS,SCHEMAS,MAX_TOKENS
from retune_controls import controls
from run_candidate_drafts import candidate_entry,window_hashes
from check_packets import validate_packet
from redraft_policy import validate_replacements
DEST=ROOT/'.private/retune-pilot-v8'
ORIGINAL=ROOT/'.private/hybrid-redraft'

def read(path):return json.loads(path.read_text())

def prepare(dest=DEST):
    if (dest/'registration.json').exists():raise ValueError('Never overwrite a registered development run')
    dest.mkdir(parents=True,exist_ok=True)
    old=read(ORIGINAL/'cohort.json');first=[r for r in old['cohort'] if r['wave']==1]
    retrieval={r['headword_key']:r for r in read(ROOT/'.private/local-redraft/retrieval.json')['rows']}
    sources={r['id']:r for r in read(ROOT/'data/sources.json')['sources']}
    previous={s['id']:s for s in read(ROOT/'.private/new-approved-sources/prior-sources.json')['sources']}
    if digest(previous)!=old['source_inventory_hash'] or any(sources.get(k)!=v for k,v in previous.items()):raise ValueError('An original source changed; cannot attribute a fixed-packet comparison')
    from recover_approved_sources import FAMILIES
    if set(sources)-set(previous)!=FAMILIES:raise ValueError('Only the three explicitly added source families are permitted')
    additions=read(ROOT/'.private/new-approved-sources/pilot-packet-options.json')
    if additions['source_inventory_hash']!=digest(sources) or additions['original_cohort_hash']!=digest(old):raise ValueError('New-source options binding changed')
    new_by_key={r['headword_key']:r for r in additions['rows']}
    rows=[]
    for r in first:
        primary=[p['packet'] for p in r['packets']];seen={p['packet_hash'] for p in primary}
        extra=[p for p in retrieval[r['headword_key']]['packets'] if p['packet_hash'] not in seen]
        # Rescue only previously retrieved permitted packets; no web text, paid retrieval or padding.
        extras=sorted(extra,key=lambda p:(p['source_label'].casefold()!=r['term'].casefold(),p['packet_hash']))[:max(0,5-len(primary))]
        for packet in primary+extras:validate_packet(packet,sources)
        rows.append({**r,'packets':primary,'rescue_packets':extras,'new_source_packets':[p['packet'] for p in new_by_key[r['headword_key']]['packets']],'hpo_references':new_by_key[r['headword_key']]['hpo_references']})
    cohort={'schema_version':1,'seed':old['seed'],'original_cohort_hash':digest(old),'source_inventory_hash':digest(sources),'original_source_inventory_hash':old['source_inventory_hash'],'approved_source_manifest_hash':additions['manifest_hash'],'rows':rows}
    atomic(dest/'cohort.json',cohort);atomic(dest/'controls.json',controls())
    original_manifest=read(ORIGINAL/'registration.json')
    # Preserve the original copy comparison verbatim; it already includes every old top-two packet.
    (dest/'comparison.bin').write_bytes((ORIGINAL/'comparison.bin').read_bytes())
    m={'schema_version':1,'line':dest.name,'status':'frozen','development_only':True,
       'evidence_parents':[{'directory':'.private/retune-pilot-v7','registration_hash':read(ROOT/'.private/retune-pilot-v7/registration.json')['registration_hash']}],'calibration_parent':'.private/retune-pilot-v6','control_label_amendment':'The ribosome draft is entailed by its packet (reader yes) but out of dictionary scope (fit no). V6 incorrectly labelled both questions no; original labels and actual responses remain archived. No responses or model prompts changed.',
       'authorization':'Vishnu requested rebuilding/retuning with API models as needed, testing the pilot items first.',
       'total_redraft_cap_usd':200,'shared_budget_ledger':'.private/hybrid-redraft/budget.sqlite',
       'prior_spend_included':True,'source_inventory_file_sha256':hashlib.sha256((ROOT/'data/sources.json').read_bytes()).hexdigest(),'endpoint':ENDPOINT,'models':MODELS,'prices_per_million':PRICES,
       'prompts':PROMPTS,'schemas':SCHEMAS,'max_completion_tokens':MAX_TOKENS,'max_request_bytes':30000,'max_workers':6,
       'transport_schema_retries':1,'uncertain_charge_policy':'Retain every uncertain reservation; a bounded retry reserves separately and all attempts count against the same original $200 ledger.','cohort_hash':digest(cohort),'controls_hash':digest(controls()),
       'original_report_hash':digest(read(ORIGINAL/'wave-001/report.json')),'original_registration_hash':original_manifest['registration_hash'],
       'comparison_sha256':hashlib.sha256((dest/'comparison.bin').read_bytes()).hexdigest(),
       'entry_schema_hash':digest(read(ROOT/'schema/entry.schema.json')),'code_hashes':hashes(),
       'pass_denominator':500,'copy_words':15,'calibration_required':'All fit controls and all reader negative controls must be correct; at least 90% of positive reader controls must pass. Report every false rejection. Controls are developer examples, not an independent accuracy estimate.',
       'comparison':'Same first 500 and original top-two packets first; rescue separately from up to three unused original retrieval candidates. Results are development, not held-out.',
       'continuation':'No automatic wave two; retain the 60% full-headword rule for any future frozen execution.',
       'publication':'Private staging only; field issues recorded separately for review, never silently retagged.'}
    m['registration_hash']=digest(m);atomic(dest/'registration.json',m)
    atomic(ROOT/("data/"+dest.name+"-registration.json"),m)
    print(json.dumps({'registration_hash':m['registration_hash'],'headwords':len(rows),'models':MODELS,'rescue_packets':sum(len(r['rescue_packets']) for r in rows)}),flush=True)

def inputs(dest):
    m=read(dest/'registration.json');c=read(dest/'cohort.json');ctl=read(dest/'controls.json')
    if digest(c)!=m['cohort_hash'] or digest(ctl)!=m['controls_hash'] or len(c['rows'])!=500:raise RunError('Frozen pilot or controls changed')
    if digest(read(ROOT/'schema/entry.schema.json'))!=m['entry_schema_hash']:raise RunError('Entry schema changed')
    if hashlib.sha256((ROOT/'data/sources.json').read_bytes()).hexdigest()!=m['source_inventory_file_sha256']:raise RunError('Source inventory changed during the registered rerun')
    client=Client(m,dest);client.verify();return m,c,ctl,client

def parallel(items,function,workers=6):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(function,item):item for item in items}
        for f in concurrent.futures.as_completed(futures):yield f.result()

def calibrate(dest=DEST):
    m,cohort,ctl,client=inputs(dest);results=[]
    tasks=[(r,role) for r in ctl for role in ('fit','reader_a','reader_b')]
    def check(task):
        row,role=task;saved=client.call(role,row['packet'],row['field'],row['definition'] if role!='fit' else None)
        actual=saved['parsed']['answer']=='yes' if role=='fit' else saved['parsed']['passed']
        return {'control':row['id'],'role':role,'expected':row['expected_fit'] if role=='fit' else row['expected_read'],'actual':actual,'saved':saved}
    for value in parallel(tasks,check):results.append(value)
    fit_controls=[r for r in results if r['role']=='fit'];negative_reads=[r for r in results if r['role']!='fit' and not r['expected']];positive_reads=[r for r in results if r['role']!='fit' and r['expected']]
    qualified=len(results)==3*len(ctl) and all(r['actual']==r['expected'] for r in fit_controls+negative_reads) and sum(r['actual'] for r in positive_reads)>=math.ceil(.9*len(positive_reads))
    result={'registration_hash':m['registration_hash'],'passed':qualified,'false_accepts':sum(r['actual'] for r in negative_reads),'positive_reads_passed':sum(r['actual'] for r in positive_reads),'positive_reads_total':len(positive_reads),'correct':sum(r['actual']==r['expected'] for r in results),'total':len(results),'decisions':sorted(results,key=lambda r:(r['control'],r['role']))}
    atomic(dest/'calibration.json',result);print(json.dumps({k:v for k,v in result.items() if k!='decisions'}),flush=True)
    return result

def index_for(dest,cohort):
    raw=(dest/'comparison.bin').read_bytes();m=read(dest/'registration.json')
    if hashlib.sha256(raw).hexdigest()!=m['comparison_sha256'] or len(raw)%32:raise RunError('Copy comparison changed')
    index={raw[i:i+32] for i in range(0,len(raw),32)}
    # Rescue passages were not all present in the original comparison. Add ALL before drafting.
    for row in cohort['rows']:
        for p in row['rescue_packets']+row['new_source_packets']:index.update(window_hashes(p['text']))
    return index

def process(row,packets,client,sources,fields,index):
    fits=[];attempts=[];accepted=None;errors=[]
    # No old definitions, legacy fixture, judge verdicts or failed drafting prose are passed here.
    yes=[]
    for p in packets:
        validate_packet(p,sources)
        try:fit=client.call('fit',p,row['field'])
        except OutputError as error:errors.append({'role':'fit','packet_hash':p['packet_hash'],'reason':str(error)});continue
        fits.append({'packet_hash':p['packet_hash'],'saved':fit})
        if fit['parsed']['answer']=='yes':yes.append((p,fit))
    for p,fit in yes:
        try:draft=client.call('draft',p,row['field'])
        except OutputError as error:errors.append({'role':'draft','packet_hash':p['packet_hash'],'reason':str(error)});continue
        attempt={'packet_hash':p['packet_hash'],'draft':draft};attempts.append(attempt)
        try:
            e=candidate_entry(p,draft,sources,fields,index);e['version']=2;e['hash']=semantic_hash(e)
        except ValueError as error:attempt['reason']=str(error);continue
        readers=[]
        for role in ('reader_a','reader_b'):
            try:saved=client.call(role,p,row['field'],e['definition'])
            except OutputError as error:errors.append({'role':role,'packet_hash':p['packet_hash'],'reason':str(error)});break
            attempt[role]=saved;readers.append(saved)
        if len(readers)!=2 or not all(r['parsed']['passed'] for r in readers):attempt['reason']='reader rejection';continue
        proofs=[]
        for r in readers:
            proofs.append({**{k:r[k] for k in ('model','receipt_id','request_hash','registration_hash','packet_hash')},'draft_model':draft['model'],
              'definition_hash':digest(draft['parsed']),'published_packet_hash':p['packet_hash'],'passed':True,'reasons':[]})
        e['reader_reviews']=proofs
        if row.get('hpo_references'):
            e['sources'].append('hpo-2026-09-01')
            for reference in row['hpo_references']:
                e['provenance'].append({'source':'hpo-2026-09-01','role':'related_topic','revision':'HPO '+reference['version'],'scope':reference['id']+' '+reference['label']+'; retrieval/reference only, not drafting text','locator':'http://purl.obolibrary.org/obo/'+reference['id'].replace(':','_')})
            e['hash']=semantic_hash(e)
        validate_entry(e,sources,fields)
        accepted={'entry':e,'packet':p,'fit':fit,'draft':draft,'readers':readers,'field_issues':[r['parsed']['field_issue'] for r in readers if r['parsed']['field_issue']],
                  'registration_hash':client.m['registration_hash'],'development_only':True}
        break
    return {'headword_key':row['headword_key'],'term':row['term'],'fits':fits,'attempts':attempts,'accepted':accepted,'output_errors':errors,
            'reason':None if accepted else 'model output could not be verified' if errors and not yes else 'no supporting source found yet' if not yes else 'draft/read/copy failure'}

def run_phase(phase,dest=DEST):
    m,c,ctl,client=inputs(dest);cal=read(dest/'calibration.json')
    if cal['registration_hash']!=m['registration_hash'] or not cal['passed']:raise RunError('Calibration failed; do not replay the pilot')
    entries,sources,fields=load_inputs();index=index_for(dest,c)
    rows=c['rows'];outputs=dest/(phase+'.json');done=read(outputs) if outputs.exists() else {}
    if phase in ('rescue','new-sources'):
        baseline=read(dest/'same-packets.json')
        if len(baseline)!=500:raise RunError('Finish all 500 same-packet comparisons before rescue')
        rows=[r for r in rows if not baseline[r['headword_key']]['accepted']]
        if phase=='new-sources':
            rescued=read(dest/'rescue.json')
            if set(rescued)!={r['headword_key'] for r in rows}:raise RunError('Finish the unused-packet rescue before trying added sources')
            rows=[r for r in rows if not rescued[r['headword_key']]['accepted']]
    def work(row):return process(row,row[{'same-packets':'packets','rescue':'rescue_packets','new-sources':'new_source_packets'}[phase]],client,sources,fields,index)
    pending=[r for r in rows if r['headword_key'] not in done]
    for value in parallel(pending,work):
        done[value['headword_key']]=value;atomic(outputs,done)
        atomic(dest/'progress.json',{'phase':phase,'completed':len(done),'phase_headwords':len(rows),'accepted_before_cross_entry_audit':sum(bool(r['accepted']) for r in done.values()),'total_redraft_budget':client.budget.summary()})
    atomic(outputs,done)
    return done

def audit(accepted,m,dest,index):
    p=accepted['packet'];e=accepted['entry']
    if e['hash']!=semantic_hash(e) or e['version']!=2 or e['packet_hash']!=p['packet_hash'] or accepted['registration_hash']!=m['registration_hash']:raise ValueError('Accepted entry binding changed')
    records=[('fit',accepted['fit'],None),('draft',accepted['draft'],None),('reader_a',accepted['readers'][0],e['definition']),('reader_b',accepted['readers'][1],e['definition'])]
    for role,saved,definition in records:
        receipt=read(dest/'receipts'/(saved['receipt_id']+'.json'));audit_saved(saved,receipt,evidence_manifest(saved,m),role,p,e['field'],definition)
    if accepted['fit']['parsed']['answer']!='yes' or not all(r['parsed']['passed'] for r in accepted['readers']):raise ValueError('Missing fit or reader pass')
    if accepted['draft']['parsed']!={'definition':e['definition'],'field':e['field'],'packet_sufficient':True}:raise ValueError('Draft definition changed')
    if set(window_hashes(e['definition'])) & index:raise ValueError('Source or cross-entry 15-word overlap')
    return e

def report(dest=DEST):
    m,c,ctl,client=inputs(dest);same=read(dest/'same-packets.json');rescue=read(dest/'rescue.json');added=read(dest/'new-sources.json')
    if set(same)!={r['headword_key'] for r in c['rows']}:raise RunError('Incomplete comparison')
    required={k for k,r in same.items() if not r['accepted']}
    if set(rescue)!=required:raise RunError('Incomplete rescue')
    if set(added)!={k for k in required if not rescue[k]['accepted']}:raise RunError('Incomplete added-source phase')
    entries,sources,fields=load_inputs();index=index_for(dest,c);accepted=[];rejected_copy=[];outcomes=[];stages=collections.Counter()
    baseline_accepted=set()
    for row in c['rows']:
        k=row['headword_key'];candidates=[('same-packets',same[k])]+([('rescue',rescue[k])] if k in rescue else [])+([('new-sources',added[k])] if k in added else [])
        stage,choice=next(((stage,value) for stage,value in candidates if value['accepted']),next(((stage,value) for stage,value in reversed(candidates) if value['fits'] or value.get('output_errors')),candidates[0]))
        a=choice['accepted']
        result={'term':row['term'],'headword_key':k,'status':'redraft','stage':stage,'reason':choice['reason'],'field_issues':[]}
        if a:
            try:
                e=audit(a,m,dest,index);validate_entry(e,sources,fields)
                accepted.append(a);stages[stage]+=1;index.update(window_hashes(e['definition']))
                if stage=='same-packets':baseline_accepted.add(k)
                result.update(status='judged',new_entry_id=e['id'],reason=None,field_issues=a['field_issues'])
                atomic(dest/'accepted'/(e['id']+'.json'),a)
            except ValueError as error:result['reason']=str(error);rejected_copy.append({'term':row['term'],'reason':str(error)})
        outcomes.append(result)
    packets={e['id']:read(ROOT/'data/packets'/(e['id']+'.json')) for e in entries};packets.update({a['entry']['id']:a['packet'] for a in accepted})
    history=read(ROOT/'data/status-history.json')['entries']
    validate_replacements([dict(e,status=history[e['id']]['status']) for e in entries]+[dict(a['entry'],status='judged') for a in accepted],packets)
    receipts=[read(p) for p in (dest/'receipts').glob('*.json')];new_receipts=[r for r in receipts if r['registration_hash']==m['registration_hash']];spend=sum(r['paid_usd'] for r in receipts)
    original=read(ORIGINAL/'wave-001/outcomes.json');changed=collections.Counter()
    for out in outcomes:changed[(original[out['headword_key']]['status'],out['status'])]+=1
    summary={'calibration':{k:v for k,v in read(dest/'calibration.json').items() if k!='decisions'},'development_only':True,'registration_hash':m['registration_hash'],'complete':True,'headwords':500,'original_passed':16,
      'same_packet_passed':len(baseline_accepted),'rescue_added':stages['rescue'],'new_source_added':stages['new-sources'],'total_passed':len(accepted),'pass_fraction':len(accepted)/500,
      'field_review_required':sum(bool(a['field_issues']) for a in accepted),'copy_audit_rejections':rejected_copy,
      'transitions':{' -> '.join(k):v for k,v in changed.items()},'phase_counts':{phase:{'headwords':len(values),'no_packets':sum(not v['fits'] for v in values.values()),'no_yes_packet':sum(not any(f['saved']['parsed']['answer']=='yes' for f in v['fits']) for v in values.values()),'fit_yes_packets':sum(f['saved']['parsed']['answer']=='yes' for v in values.values() for f in v['fits']),'draft_attempts':sum(len(v['attempts']) for v in values.values())} for phase,values in (('same-packets',same),('rescue',rescue),('new-sources',added))},'retune_spend_usd':round(spend,6),'incremental_this_registration_usd':round(sum(r['paid_usd'] for r in new_receipts),6),'reused_actual_receipts':len(receipts)-len(new_receipts),'by_role':{role:{'calls':sum(r['role']==role for r in receipts),'usd':round(sum(r['paid_usd'] for r in receipts if r['role']==role),6)} for role in MODELS},
      'total_redraft_budget':client.budget.summary(),'published_entries':0,'next_wave_started':False}
    atomic(dest/'outcomes.json',outcomes);atomic(dest/'report.json',summary)
    atomic(ROOT/('reports/'+dest.name+'.json'),summary)
    sample=random.Random(20261018).sample(outcomes,20)
    lines=['# PsychTerms development rerun of the 500-item pilot','',
      'This corpus and its original failures informed the prompts. These are development results, not an independent validation or a new estimate of population accuracy. The original report and evidence are unchanged.','',
      f'Original: **16/500 (3.2%)**. New API checks and drafts with the same original top-two packets: **{len(baseline_accepted)}/500**. Previously unused permitted retrieval packets add **{stages['rescue']}**, and the added government sources add **{stages['new-sources']}**, for **{len(accepted)}/500 ({len(accepted)/500:.1%})**.','',
      f'Calibration: {summary["calibration"]["correct"]}/{summary["calibration"]["total"]} developer controls matched; false accepts {summary["calibration"]["false_accepts"]}; positive reader controls passed {summary["calibration"]["positive_reads_passed"]}/{summary["calibration"]["positive_reads_total"]}. API spend for this rerun: **${spend:.4f}**. Shared original $200 redraft ledger: **${summary["total_redraft_budget"]["receipted_usd"]:.4f}** receipted.','',
      f'Accepted definitions with a separate field-classification flag: **{summary["field_review_required"]}**. They require field review before publication. No existing fields or statuses were changed.','',
      'Both non-drafter readers and a 15-word source/cross-entry scan are still required. All accepted responses and source evidence were audited before this report. No entries were published and no second wave started.','',
      '## Status changes','', '| Original -> rerun | Headwords |','|---|---:|',*[f'| {k} | {v} |' for k,v in summary['transitions'].items()],
      '', '## Twenty entries sampled with seed 20261018','', '| Headword | Outcome | Stage | Reason / field issue |','|---|---|---|']
    for row in sample:lines.append('| '+' | '.join(str(x or '').replace('|','/').replace('\n',' ') for x in (row['term'],row['status'],row['stage'],row['reason'] or '; '.join(row['field_issues'])))+' |')
    lines+=['','## All outcomes','','| Headword | Outcome | Stage |','|---|---|---|']
    lines +=['| '+' | '.join(str(row[k]).replace('|','/') for k in ('term','status','stage'))+' |' for row in outcomes]
    (ROOT/('reports/'+dest.name+'.md')).write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,indent=2),flush=True);return summary

def execute(dest=DEST):
    lock=(dest/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    atomic(dest/'run-state.json',{'stage':'calibrating'})
    try:
        calibration=calibrate(dest)
        if not calibration['passed']:
            atomic(dest/'run-state.json',{'stage':'calibration_failed','correct':calibration['correct'],'total':calibration['total']});return
        for phase in ('same-packets','rescue','new-sources'):
            atomic(dest/'run-state.json',{'stage':phase});run_phase(phase,dest)
        summary=report(dest);atomic(dest/'run-state.json',{'stage':'complete',**summary})
    except Exception:
        atomic(dest/'run-state.json',{'stage':'paused','reason':'See worker log and actual receipts; no automatic paid retries.'});raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','calibrate','run','report']);p.add_argument('--dest',type=Path,default=DEST);a=p.parse_args()
    if a.command=='prepare':prepare(a.dest)
    elif a.command=='calibrate':calibrate(a.dest)
    elif a.command=='run':execute(a.dest)
    else:report(a.dest)
