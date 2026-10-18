"""Registered, capped drafting only. Candidate publication does not claim judge review."""
import argparse,collections,concurrent.futures,hashlib,json,math,re,threading,urllib.request,uuid
from decimal import Decimal
from pathlib import Path
from core import ROOT,canonical,digest,normalize,semantic_hash,load_inputs,validate_entry
from budget import Budget
from check_packets import validate_packet
from overlap_scan import words
from risk_registry import load_registry,matches,required_tests
from scope_rules import decide

DEST=ROOT/'.private/candidate-drafts'
PINNED_CODE=('core.py','scope_rules.py','check_packets.py','budget.py','risk_registry.py','overlap_scan.py')

def source_content_hash(packet):
    return digest({key:packet.get(key) for key in ('term','source','source_record','revision','text')})

def validate_scope(packet):
    decision=decide(packet)
    if not decision['eligible'] or packet.get('scope_decision')!=decision or packet.get('planned_field')!=decision['field']:
        raise ValueError('Scope and field must be admitted and pinned before paid drafting')

def verify_registration(manifest,packets,execute=False,root=ROOT):
    if manifest.get('line')!='candidate-definitions-v1':raise ValueError('Wrong drafting line')
    if manifest.get('registration_hash')!=digest({k:v for k,v in manifest.items() if k!='registration_hash'}):raise ValueError('Registration hash mismatch')
    if manifest.get('packet_set_hash')!=digest(packets) or manifest.get('source_packet_count')!=len(packets):raise ValueError('Registered packet queue changed')
    if manifest.get('executor_sha256')!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise ValueError('Executor changed after registration')
    if manifest.get('model')!='gpt-5.4-2026-03-05' or manifest.get('copy_threshold_words')!=15:raise ValueError('Registered model or copy threshold changed')
    if execute:
        require_authorization(manifest,root)
        if manifest.get('scope_and_field_required') is not True:raise ValueError('Scope preflight is required')
        expected={name:hashlib.sha256((root/'scripts'/name).read_bytes()).hexdigest() for name in PINNED_CODE}
        if manifest.get('code_hashes')!=expected:raise ValueError('Registered drafting dependencies changed')
        for packet in packets:validate_scope(packet)
    return manifest

def require_authorization(manifest,root=ROOT):
    policy=json.loads((root/'data/release-policy.json').read_text())
    cap=manifest.get('authorized_cap_usd')
    if manifest.get('status')!='frozen' or not manifest.get('human_authorization') or not cap or Decimal(cap)<=0:raise ValueError('Vishnu has not set this drafting cap')
    if policy.get('candidate_paid_dispatch_enabled') is not True or policy.get('candidate_drafting_cap_usd')!=cap:raise ValueError('Candidate drafting line is disabled or its cap differs')
    current=json.loads((root/'.private/candidate-drafts/preregistration.json').read_text())
    if current!=manifest:raise ValueError('Registration changed during execution')


def window_hashes(text,n=15):
    tokens=words(text)
    return (hashlib.sha256(' '.join(tokens[i:i+n]).encode()).digest() for i in range(len(tokens)-n+1))

def copy_index(texts):
    result=set()
    for text in texts:result.update(window_hashes(text))
    return result

def check_draft(draft,fields,index):
    if set(draft)!={'definition','field','packet_sufficient'} or type(draft['packet_sufficient']) is not bool:raise ValueError('Malformed draft')
    if not draft['packet_sufficient']:raise ValueError('Source packet insufficient')
    if not isinstance(draft['definition'],str) or not draft['definition'].strip():raise ValueError('Empty draft')
    if draft['field'] not in fields:raise ValueError('Unknown field')
    if any(h in index for h in window_hashes(draft['definition'])):raise ValueError('15-word overlap')

class Client:
    def __init__(self,manifest,packets,key,budget,dest):
        self.m=manifest;self.packets=packets;self.key=key;self.budget=budget;self.dest=dest;self.stopped=threading.Event();self.attempts=collections.Counter(json.loads(p.read_text())['request_hash'] for p in (dest/'receipts').glob('*-error.json'))
    def call(self,packet,feedback=None):
        require_authorization(self.m)
        if self.m.get('scope_and_field_required'):validate_scope(packet)
        data={'packet':packet,'fields':[packet['planned_field']] if packet.get('planned_field') else self.m['fields']}
        if feedback:data['revision_feedback']=feedback
        body={'model':self.m['model'],'messages':[{'role':'system','content':self.m['draft_prompt']},{'role':'user','content':json.dumps(data,ensure_ascii=False)}],
            'response_format':{'type':'json_schema','json_schema':{'name':'dictionary_result','strict':True,'schema':self.m['draft_schema']}},
            'max_completion_tokens':self.m['max_completion_tokens'],'reasoning_effort':self.m['reasoning_effort'],'store':False}
        raw=canonical(body);request_hash=hashlib.sha256(raw).hexdigest()
        if len(raw)>self.m['max_request_bytes']:raise ValueError('Request exceeds registered size')
        suffix='redraft' if feedback else 'draft';cache=self.dest/'calls'/f'{packet["id"]}-{suffix}-{request_hash}.json'
        legacy=self.dest/'calls'/f'{packet["id"]}-{suffix}.json'
        if not cache.exists() and legacy.exists():
            old=json.loads(legacy.read_text())
            if old.get('request_hash')==request_hash:cache=legacy
        if cache.exists():
            saved=json.loads(cache.read_text())
            if saved['request_hash']!=request_hash or saved.get('packet_hash')!=packet['packet_hash']:raise ValueError('Cached request or source packet changed')
            if saved['registration_hash']!=self.m['registration_hash']:
                archive=self.dest/'registrations'/(saved['registration_hash']+'.json')
                previous=json.loads(archive.read_text())
                if previous.get('registration_hash')!=digest({k:v for k,v in previous.items() if k!='registration_hash'}):raise ValueError('Cached registration archive is invalid')
            return saved
        prices=self.m['prices_per_million'];reserve=math.ceil((len(raw)+512)*prices['input']+self.m['max_completion_tokens']*prices['output'])
        starting=self.attempts[request_hash]
        if starting>self.m['transport_schema_retries']:raise RuntimeError('Registered retry limit exhausted')
        for attempt in range(starting,self.m['transport_schema_retries']+1):
            if self.stopped.is_set():raise RuntimeError('Drafting line stopped')
            require_authorization(self.m)
            rid=uuid.uuid4().hex
            try:self.budget.reserve(rid,suffix if not attempt else 'transport_schema_retry',reserve)
            except RuntimeError:
                self.stopped.set();raise
            request=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=raw,headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},method='POST')
            receipted=False
            try:
                with urllib.request.urlopen(request,timeout=90) as response:result=json.load(response)
                (self.dest/'receipts'/f'{rid}.json').write_text(json.dumps(result,ensure_ascii=False)+'\n')
                usage=result['usage'];cached=usage.get('prompt_tokens_details',{}).get('cached_tokens',0)
                charge=math.ceil((usage['prompt_tokens']-cached)*prices['input']+cached*prices.get('cached_input',prices['input'])+usage['completion_tokens']*prices['output'])
                self.budget.reconcile(rid,charge);receipted=True
                if result.get('model')!=self.m['model']:raise ValueError('Returned model differs from fixed snapshot')
                choice=result['choices'][0]
                if choice.get('finish_reason')!='stop':raise ValueError('Incomplete completion')
                parsed=json.loads(choice['message']['content'])
                if set(parsed)!=set(self.m['draft_schema']['required']):raise ValueError('Response schema differs')
                saved={'parsed':parsed,'receipt_id':rid,'request_hash':request_hash,'registration_hash':self.m['registration_hash'],'model':self.m['model'],'packet_hash':packet['packet_hash']}
                cache.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n');return saved
            except Exception as error:
                (self.dest/'receipts'/f'{rid}-error.json').write_text(json.dumps({'request_hash':request_hash,'error_type':type(error).__name__,'http_status':getattr(error,'code',None),'receipted':receipted})+'\n')
                self.attempts[request_hash]=attempt+1
                if getattr(error,'code',None) in (401,403,429) or 'Provider charge exceeded reservation' in str(error):
                    self.stopped.set();raise RuntimeError('Drafting line stopped for provider or billing reconciliation') from error
                if attempt==self.m['transport_schema_retries']:
                    if not receipted:raise RuntimeError('Registered retry limit exhausted; uncertain charge remains reserved') from error
                    raise

def candidate_entry(packet,saved,sources,fields,index):
    draft=saved['parsed'];check_draft(draft,fields,index);validate_packet(packet,sources)
    if packet.get('planned_field') and draft['field']!=packet['planned_field']:raise ValueError('Draft changed the preregistered field')
    if saved.get('packet_hash')!=packet['packet_hash']:raise ValueError('Draft used a different source packet')
    entry={'id':packet['id'],'term':packet['term'],'definition':draft['definition'],'field':draft['field'],'also_see':[],'aliases':[],
        'sources':[packet['source']],'provenance':[{'role':'draft_basis','source':packet['source'],'revision':packet['revision'],'scope':f'Source record {packet["source_record"]}; pinned source text','locator':packet['url']}],
        'version':1,'packet_hash':packet['packet_hash'],
        'draft_evidence':{'model':saved['model'],'receipt_id':saved['receipt_id'],'request_hash':saved['request_hash'],'registration_hash':saved['registration_hash'],'definition_hash':digest(draft),'packet_hash':packet['packet_hash']}}
    entry['hash']=semantic_hash(entry);validate_entry(entry,sources,fields);return entry

def draft_packet(client,packet,sources,fields,index):
    saved=client.call(packet)
    try:return candidate_entry(packet,saved,sources,fields,index)
    except ValueError as error:
        if str(error) not in ('15-word overlap','More than three sentences'):raise
        reason='A run of at least 15 consecutive words matches the pinned comparison corpus. Rewrite in original wording using only the same packet.' if str(error)=='15-word overlap' else 'The draft exceeds the one-to-three-sentence limit. Rewrite in at most three plain-language sentences, avoiding abbreviations that create extra sentence boundaries, using only the same packet.'
        saved=client.call(packet,{'previous_definition':saved['parsed']['definition'],'reason':reason})
    return candidate_entry(packet,saved,sources,fields,index)

def publish_candidate(entry,packet,registry):
    for folder,value in [('data/entries',entry),('data/packets',packet)]:
        path=ROOT/folder/(entry['id']+'.json')
        if path.exists() and json.loads(path.read_text())!=value:raise ValueError('Refusing to overwrite an existing entry or packet')
    tests=required_tests(entry,packet,registry)
    if tests and not any(matches(entry,packet,row) for row in registry['terms']):
        registry['terms'].append({'id':entry['id'],'names':[entry['term']],'anchors':[packet['source_record']],'test':min(tests),'reason':f'Section 4a test {min(tests)} from pinned candidate source packet or named duty.'})
        registry['version']+=1;path=ROOT/'data/risk_terms.json';path.write_text(json.dumps(registry,indent=2)+'\n')
        (ROOT/'data/risk-terms-pin.json').write_text(json.dumps({'version':registry['version'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2)+'\n')
    (ROOT/'data/packets'/(entry['id']+'.json')).write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/entries'/(entry['id']+'.json')).write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n')

def run(execute,key_file,limit=None):
    manifest=json.loads((DEST/'preregistration.json').read_text());packets=json.loads((DEST/'packets.json').read_text());verify_registration(manifest,packets,execute)
    entries,sources,fields=load_inputs()
    for packet in packets:validate_packet(packet,sources);validate_scope(packet)
    if not execute:return {'registration_valid':True,'status':manifest['status'],'packets':len(packets),'paid_calls':0}
    match=re.search(r'sk-[A-Za-z0-9_-]+',key_file.read_text())
    if not match:raise ValueError('No API key in the supplied file')
    for folder in ('calls','receipts'):(DEST/folder).mkdir(exist_ok=True)
    budget=Budget(DEST/'budget.sqlite',int(Decimal(manifest['authorized_cap_usd'])*1_000_000));client=Client(manifest,packets,match[0],budget,DEST)
    outcome_path=DEST/'outcomes.json'
    outcomes=json.loads(outcome_path.read_text()) if outcome_path.exists() else {}
    existing={e['id'] for e in entries};queue=[p for p in packets if p['id'] not in existing and (outcomes.get(p['id'],{}).get('packet_hash')!=p['packet_hash'] or (outcomes.get(p['id'],{}).get('reason')=='More than three sentences' and not any((DEST/'calls').glob(p['id']+'-redraft*.json')))) and not (outcomes.get(p['id'],{}).get('reason')=='Source packet insufficient' and outcomes.get(p['id'],{}).get('source_content_hash')==source_content_hash(p))]
    if limit:queue=queue[:limit]
    public_packets=[json.loads(p.read_text()) for p in (ROOT/'data/packets').glob('*.json')]
    index=copy_index([p['text'] for p in packets+public_packets]+[e['definition'] for e in entries]);registry,_=load_registry();definitions={normalize(e['definition']) for e in entries}
    results=[]
    def draft(packet):return draft_packet(client,packet,sources,fields,index)
    with concurrent.futures.ThreadPoolExecutor(max_workers=manifest['workers']) as pool:
        futures={pool.submit(draft,p):p for p in queue}
        for future in concurrent.futures.as_completed(futures):
            packet=futures[future]
            try:
                entry=future.result();key=normalize(entry['definition'])
                if key in definitions:raise ValueError('Exact duplicate definition')
                check_draft({'definition':entry['definition'],'field':entry['field'],'packet_sufficient':True},fields,index)
                publish_candidate(entry,packet,registry);definitions.add(key);index.update(window_hashes(entry['definition']));results.append({'id':packet['id'],'status':'candidate'})
            except Exception as error:results.append({'id':packet['id'],'status':'not_published','reason':str(error)[:180]})
            latest=results[-1]
            if not client.stopped.is_set() or latest['status']=='candidate':
                outcomes[packet['id']]=dict(latest,packet_hash=packet['packet_hash'],source_content_hash=source_content_hash(packet),registration_hash=manifest['registration_hash'])
            if len(results)%25==0 or len(results)==len(queue):
                temp=outcome_path.with_suffix('.tmp');temp.write_text(json.dumps(outcomes,ensure_ascii=False,indent=2)+'\n');temp.replace(outcome_path)
                report={'line':manifest['line'],'registration_hash':manifest['registration_hash'],'attempted':len(results),'total':len(queue),'candidate_entries_added':sum(r['status']=='candidate' for r in results),'budget':budget.summary(),'results':results,'judge_calls':0,'vignettes':0}
                (DEST/'run-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
                print(json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)
    return {'candidate_entries_added':sum(r['status']=='candidate' for r in results),'budget':budget.summary(),'judge_calls':0}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--key-file',type=Path);p.add_argument('--limit',type=int);a=p.parse_args()
    if a.execute and not a.key_file:p.error('--key-file is required')
    print(json.dumps(run(a.execute,a.key_file,a.limit),indent=2))
