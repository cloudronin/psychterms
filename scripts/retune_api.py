"""All API roles share the ORIGINAL $200 redraft ledger, never a fresh $200 allowance."""
import hashlib,json,math,threading,time,urllib.request,uuid
from pathlib import Path
from core import ROOT,canonical,digest
from budget import Budget
from hybrid_redraft import atomic,NoRedirect
from retune_protocol import MODELS,PRICES,PROMPTS,SCHEMAS,MAX_TOKENS,validate_value
ENDPOINT='https://api.openai.com/v1/chat/completions'
LEDGER=ROOT/'.private/hybrid-redraft/budget.sqlite'
CODE=('retune_protocol.py','retune_api.py','retune_pilot.py','retune_controls.py','core.py','check_packets.py','redraft_policy.py','run_candidate_drafts.py','overlap_scan.py','budget.py','recover_approved_sources.py','prepare_reference_packets.py')
class RunError(RuntimeError):pass
class OutputError(RunError):pass

def evidence_manifest(saved,manifest):
    if saved['registration_hash']==manifest['registration_hash']:return manifest
    for ancestor in manifest.get('evidence_parents',[]):
        parent=json.loads((ROOT/ancestor['directory']/'registration.json').read_text())
        if parent['registration_hash']!=ancestor['registration_hash'] or parent['registration_hash']!=digest({k:v for k,v in parent.items() if k!='registration_hash'}):raise RunError('Parent evidence registration changed')
        if saved['registration_hash']==parent['registration_hash']:return parent
    raise RunError('Receipt registration is not an admitted parent')

def hashes():return {n:hashlib.sha256((ROOT/'scripts'/n).read_bytes()).hexdigest() for n in CODE}

def request_for(role,packet,field,definition=None):
    kind='read' if role.startswith('reader') else role
    data={'headword':packet['term'],'field':field,'source':packet.get('source','control'),'source_record':packet.get('source_record','control'),'revision':packet.get('revision','1'),'text':packet['text'],'source_record_label':packet.get('source_label',''),'publisher_aliases':packet.get('publisher_aliases',[])}
    if kind=='fit':data={'headword':packet['term'],'taxonomy_hint':field,'source_packet':data}
    if kind=='read':data={'headword':packet['term'],'taxonomy_hint':field,'source_packet':data,'draft_to_check':{'definition':definition}}
    return {'model':MODELS[role],'messages':[{'role':'system','content':PROMPTS[kind]},{'role':'user','content':json.dumps(data,ensure_ascii=False)}],
      'response_format':{'type':'json_schema','json_schema':{'name':'dictionary_'+kind,'strict':True,'schema':SCHEMAS[kind]}},
      'max_completion_tokens':MAX_TOKENS[kind],'reasoning_effort':'low','store':False}

def charge(usage,prices):
    cached=usage.get('prompt_tokens_details',{}).get('cached_tokens',0)
    return math.ceil((usage['prompt_tokens']-cached)*prices['input']+cached*prices['cached_input']+usage['completion_tokens']*prices['output'])

class Client:
    def __init__(self,manifest,dest,ledger=LEDGER):
        self.m=manifest;self.dest=dest;self.budget=Budget(ledger,200_000_000);self.stop=threading.Event()
    def verify(self):
        if self.m['registration_hash']!=digest({k:v for k,v in self.m.items() if k!='registration_hash'}) or json.loads((self.dest/'registration.json').read_text())!=self.m:raise RunError('Retune registration changed')
        if hashes()!=self.m['code_hashes']:raise RunError('Registered retune code changed')
        if self.m['models']!=MODELS or self.m['prices_per_million']!=PRICES or self.m['total_redraft_cap_usd']!=200 or self.m['endpoint']!=ENDPOINT:raise RunError('Registered paid roles differ')
    def call(self,role,packet,field,definition=None):
        self.verify();body=request_for(role,packet,field,definition);raw=canonical(body);rh=digest(body)
        if len(raw)>30000:raise RunError('Registered request byte cap exceeded')
        cache=self.dest/'calls'/(role+'-'+rh+'.json')
        if cache.exists():
            saved=json.loads(cache.read_text());r=json.loads((self.dest/'receipts'/(saved['receipt_id']+'.json')).read_text())
            audit_saved(saved,r,evidence_manifest(saved,self.m),role,packet,field,definition);return saved
        if packet.get('source')=='developer-authored-control' and self.m.get('calibration_parent'):
            parent=ROOT/self.m['calibration_parent'];parent_cache=parent/'calls'/(role+'-'+rh+'.json')
            if parent_cache.exists():
                pm=json.loads((parent/'registration.json').read_text())
                if pm['registration_hash']!=digest({k:v for k,v in pm.items() if k!='registration_hash'}):raise RunError('Parent calibration manifest changed')
                saved=json.loads(parent_cache.read_text());receipt=json.loads((parent/'receipts'/(saved['receipt_id']+'.json')).read_text())
                audit_saved(saved,receipt,pm,role,packet,field,definition)
                return {**saved,'reused_from_registration':pm['registration_hash']}
        inherited_errors=[]
        for ancestor in self.m.get('evidence_parents',[]):
            parent=ROOT/ancestor['directory'];parent_cache=parent/'calls'/(role+'-'+rh+'.json')
            if parent_cache.exists():
                saved=json.loads(parent_cache.read_text());receipt=json.loads((parent/'receipts'/(saved['receipt_id']+'.json')).read_text())
                audit_saved(saved,receipt,evidence_manifest(saved,self.m),role,packet,field,definition)
                atomic(self.dest/'receipts'/(saved['receipt_id']+'.json'),receipt);atomic(cache,saved)
                return saved
            inherited_errors.extend(json.loads(p.read_text()) for p in (parent/'errors').glob(rh+'-*.json'))
        if self.stop.is_set():raise RunError('Retune API line paused')
        errors=[json.loads(p.read_text()) for p in (self.dest/'errors').glob(rh+'-*.json')]+inherited_errors
        if len(errors)>self.m['transport_schema_retries']:
            if any(r.get('http_status') in (400,401,403) for r in errors):raise RunError('Provider configuration/authentication error needs attention')
            raise OutputError('Model response or transport unresolved after bounded retry; uncertain charges remain reserved')
        key=Path('/tmp/OPEN_AI_API.txt').read_text().strip()
        if not key:raise RunError('API credential is empty')
        prices=PRICES[MODELS[role]]
        reserve=math.ceil((len(raw)+512)*prices['input']+MAX_TOKENS['read' if role.startswith('reader') else role]*prices['output'])
        for attempt in range(len(errors),self.m['transport_schema_retries']+1):
            self.verify()
            if self.stop.is_set():raise RunError('Retune API line paused')
            rid='retune-'+uuid.uuid4().hex
            self.budget.reserve(rid,'pilot-retune-'+role,reserve)
            request=urllib.request.Request(ENDPOINT,data=raw,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect());start=time.monotonic()
            try:
                with opener.open(request,timeout=150) as response:result=json.load(response)
                receipt={'evidence_kind':'OpenAI API','receipt_id':rid,'registration_hash':self.m['registration_hash'],'role':role,'model':MODELS[role],
                    'request_hash':rh,'packet_hash':packet['packet_hash'],'request':body,'response':result,'elapsed_seconds':round(time.monotonic()-start,3),
                    'paid_usd':charge(result['usage'],prices)/1e6}
                atomic(self.dest/'receipts'/(rid+'.json'),receipt);self.budget.reconcile(rid,round(receipt['paid_usd']*1e6))
                if result.get('model')!=MODELS[role] or not result.get('id') or result['choices'][0]['finish_reason']!='stop':raise OutputError('Incomplete or changed provider model')
                value=validate_value(role,json.loads(result['choices'][0]['message']['content']),packet['text'],definition)
                saved={'parsed':value,'receipt_id':rid,'receipt_hash':digest(receipt),'request_hash':rh,'registration_hash':self.m['registration_hash'],
                       'model':MODELS[role],'packet_hash':packet['packet_hash'],'paid_usd':receipt['paid_usd']}
                atomic(cache,saved);return saved
            except Exception as error:
                atomic(self.dest/'errors'/(rh+'-'+str(attempt)+'.json'),{'receipt_id':rid,'role':role,'request_hash':rh,'error_type':type(error).__name__,'http_status':getattr(error,'code',None)})
                if attempt==self.m['transport_schema_retries'] or getattr(error,'code',None) in (401,403):
                    if getattr(error,'code',None) not in (400,401,403):raise OutputError('Model response or transport unresolved after bounded retry; uncertain charges remain reserved') from error
                    self.stop.set();raise RunError('API line paused after bounded retry; uncertain attempts remain reserved') from error
                time.sleep(1)

def audit_saved(saved,receipt,m,role,packet,field,definition=None):
    body=request_for(role,packet,field,definition)
    if receipt.get('evidence_kind')!='OpenAI API' or digest(receipt)!=saved['receipt_hash'] or receipt['request']!=body or receipt['request_hash']!=digest(body) or receipt['registration_hash']!=m['registration_hash'] or receipt['packet_hash']!=packet['packet_hash'] or receipt['role']!=role or receipt['model']!=MODELS[role]:raise ValueError('API receipt binding differs')
    if any(saved[k]!=receipt[k] for k in ('receipt_id','request_hash','registration_hash','packet_hash','model','paid_usd')):raise ValueError('Saved proof differs from receipt')
    result=receipt['response']
    if result['model']!=MODELS[role] or not result.get('id') or result['choices'][0]['finish_reason']!='stop':raise ValueError('Incomplete provider response')
    value=validate_value(role,json.loads(result['choices'][0]['message']['content']),packet['text'],definition)
    if saved['parsed']!=value or receipt['paid_usd']!=charge(result['usage'],PRICES[MODELS[role]])/1e6:raise ValueError('Actual verdict or spend differs')
