"""Execute only the frozen 200-term paid pilot; no full-run mode exists."""
import argparse,collections,concurrent.futures,hashlib,json,math,re,time,uuid,urllib.request,urllib.error
from pathlib import Path
from core import ROOT,canonical,digest
from budget import Budget
from check_packets import validate_packet
from overlap_scan import words


def longest_overlap(text,references,n=15):
 w=words(text)
 for ref in references:
  rw=words(ref)
  windows={tuple(rw[i:i+n]) for i in range(len(rw)-n+1)}
  if any(tuple(w[i:i+n]) in windows for i in range(len(w)-n+1)):return True
 return False

def require_paid_dispatch(root=ROOT):
 policy=json.loads((root/'data/release-policy.json').read_text())
 if (root/'.private/pilot/STOP').exists() or policy.get('paid_dispatch_enabled') is not True:
  raise RuntimeError('Paid dispatch blocked: combined pilot PREREG and pinned ArcSim card inputs required')

class Client:
 def __init__(self,manifest,key,budget,dest):self.m=manifest;self.key=key;self.budget=budget;self.dest=dest
 def call(self,category,ident,model,system,data,schema):
  require_paid_dispatch()
  body={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(data,ensure_ascii=False)}],'response_format':{'type':'json_schema','json_schema':{'name':'dictionary_result','strict':True,'schema':schema}},'max_completion_tokens':self.m['max_completion_tokens'],'reasoning_effort':self.m['reasoning_effort'],'store':False}
  raw=canonical(body);request_hash=hashlib.sha256(raw).hexdigest()
  if len(raw)>self.m['max_request_bytes']:raise ValueError('Request exceeds preregistered byte cap')
  cached=self.dest/'calls'/f'{ident}-{category}.json';cached.parent.mkdir(exist_ok=True)
  if cached.exists():
   saved=json.loads(cached.read_text())
   if saved['request_hash']!=request_hash:raise ValueError('Request changed under frozen pilot')
   return saved['parsed'],saved['receipt_id']
  prices=self.m['prices_per_million'][model]
  reserve=math.ceil((len(raw)+512)*prices['input']+self.m['max_completion_tokens']*prices['output'])
  last=None
  for attempt in range(self.m['transport_schema_retries']+1):
   request_id=uuid.uuid4().hex;cat=category if not attempt else 'transport_schema_retry'
   require_paid_dispatch()
   self.budget.reserve(request_id,cat,reserve)
   req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=raw,headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},method='POST')
   response=None
   try:
    with urllib.request.urlopen(req,timeout=90) as resp:response=json.load(resp)
    receipt=self.dest/'receipts'/f'{request_id}.json';receipt.write_text(json.dumps(response,ensure_ascii=False))
    usage=response.get('usage')
    if not usage:raise ValueError('Missing usage; reservation remains outstanding')
    cost=math.ceil(usage['prompt_tokens']*prices['input']+usage['completion_tokens']*prices['output'])
    self.budget.reconcile(request_id,cost)
    actual_model=response.get('model')
    if actual_model!=model:raise ValueError('Returned model differs from frozen snapshot')
    choice=response['choices'][0]
    if choice['finish_reason']!='stop':raise ValueError('Incomplete completion')
    parsed=json.loads(choice['message']['content'])
    required=set(schema['required'])
    if set(parsed)!=required:raise ValueError('Response schema keys mismatch')
    cached.write_text(json.dumps({'request_hash':request_hash,'parsed':parsed,'receipt_id':request_id},ensure_ascii=False,indent=2)+'\n')
    return parsed,request_id
   except (OSError,urllib.error.URLError,TimeoutError,ValueError,KeyError,json.JSONDecodeError) as error:
    last=type(error).__name__+': '+str(error)[:160]
    # Unreceipted network outcomes conservatively keep their reserved amount.
    (self.dest/'receipts'/f'{request_id}-error.json').write_text(json.dumps({'error':last,'category':category,'attempt':attempt,'request_hash':request_hash}))
    if attempt<self.m['transport_schema_retries']:time.sleep(1)
  raise RuntimeError(last)

def verify_manifest(m,packets):
 if m.get('status')!='frozen' or m.get('count')!=200 or m.get('authorized_cap_usd')!='20.00' or m.get('full_run_authorized') is not False:raise ValueError('Not the authorized frozen pilot')
 if m.get('preregistration_hash')!=digest({k:v for k,v in m.items() if k!='preregistration_hash'}):raise ValueError('Preregistration hash mismatch')
 if m['packet_set_hash']!=digest(packets) or len(packets)!=200:raise ValueError('Packet set changed')
 if len({m['models']['judge_a'],m['models']['judge_b']})!=2:raise ValueError('Distinct judges required')
 if m['executor_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():raise ValueError('Executor changed after preregistration')
 if m['scanner_sha256']!=hashlib.sha256((ROOT/'scripts/overlap_scan.py').read_bytes()).hexdigest():raise ValueError('Scanner changed')
 for row,p in zip(m['sample'],packets):
  if row['id']!=p['id'] or row['packet_hash']!=p['packet_hash']:raise ValueError('Sample changed')
 sources={s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text())['sources']}
 for p in packets:validate_packet(p,sources)

def run(execute,key_file):
 if execute:require_paid_dispatch()
 m=json.loads((ROOT/'data/pilot-preregistration.json').read_text());dest=ROOT/'.private/pilot';packets=json.loads((dest/'packets.json').read_text());verify_manifest(m,packets)
 if not execute:print(json.dumps({'manifest_verified':True,'paid_calls':0,'execute':False},indent=2));return
 key_text=key_file.read_text();match=re.search(r'sk-[A-Za-z0-9_-]+',key_text)
 if not match:raise ValueError('API key not found in supplied file')
 key=match[0]
 # Read-only account availability check; no paid completion and no silent substitution.
 for model in set(m['models'].values()):
  req=urllib.request.Request('https://api.openai.com/v1/models/'+model,headers={'Authorization':'Bearer '+key})
  with urllib.request.urlopen(req,timeout=30) as resp:info=json.load(resp)
  if info.get('id')!=model:raise ValueError('Pinned model is unavailable')
 (dest/'receipts').mkdir(exist_ok=True);budget=Budget(dest/'budget.sqlite',20_000_000);client=Client(m,key,budget,dest)
 references=[p['text'] for p in packets]
 def draft(packet,redraft=None):
  payload={'packet':packet,'fields':m['fields']}
  if redraft:payload['revision_feedback']=redraft
  category='redrafting' if redraft else 'drafting'
  result,receipt=client.call(category,packet['id'],m['models']['draft'],m['draft_prompt'],payload,m['draft_schema'])
  return {'id':packet['id'],'term':packet['term'],'packet_hash':packet['packet_hash'],'draft':result,'draft_receipt':receipt,'overlap_15':longest_overlap(result['definition'],references)}
 def judge(packet,row,label):
  if not row['draft'].get('packet_sufficient') or not row['draft'].get('definition'):
   return {'model':m['models'][label],'passed':False,'reasons':['Draft packet insufficient or no definition'],'receipt_id':None}
  result,receipt=client.call(label,packet['id']+('-redraft' if row.get('redrafted') else ''),m['models'][label],m['judge_prompt'],{'packet':packet,'definition':row['draft']['definition'],'field':row['draft']['field']},m['judge_schema'])
  return dict(result,model=m['models'][label],receipt_id=receipt,packet_hash=packet['packet_hash'],definition_hash=digest(row['draft']))
 def parallel(function,pairs,stage):
  results={}
  with concurrent.futures.ThreadPoolExecutor(max_workers=m['workers']) as pool:
   futures={pool.submit(function,*args):ident for ident,args in pairs}
   for i,future in enumerate(concurrent.futures.as_completed(futures),1):
    results[futures[future]]=future.result()
    if i%20==0 or i==len(futures):print(json.dumps({'stage':stage,'completed':i,'total':len(futures),'budget':budget.summary()['receipted_usd']}),flush=True)
  return results
 initial=parallel(draft,[(p['id'],(p,)) for p in packets],'drafting')
 overlap_count=sum(r['overlap_15'] for r in initial.values())
 initial_path=dest/'initial-drafts.json';initial_path.write_text(json.dumps(initial,ensure_ascii=False,indent=2)+'\n')
 report={'preregistration_hash':m['preregistration_hash'],'attempted_terms':200,'initial_overlap_hits':overlap_count,'source_scope':m['source_scope'],'released_entries':0}
 if overlap_count/200>m['stop_initial_overlap_fraction']:
  report.update(status='stopped_initial_overlap_threshold',budget=budget.summary());(ROOT/'reports/pilot-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return
 judged=parallel(lambda p,row:{'judge_a':judge(p,row,'judge_a'),'judge_b':judge(p,row,'judge_b')},[(p['id'],(p,initial[p['id']])) for p in packets],'two_judges')
 rows={}
 for p in packets:
  row=initial[p['id']];row['judges']=judged[p['id']];row['redrafted']=False
  row['accepted']=all(j['passed'] is True for j in row['judges'].values()) and not row['overlap_15'] and row['draft']['field'] in m['fields']
  rows[p['id']]=row
 failed=[p for p in packets if not rows[p['id']]['accepted']]
 initial_passes=200-len(failed)
 def revise(p):
  old=rows[p['id']]
  feedback={'previous_definition':old['draft']['definition'],'reasons':[reason for j in old['judges'].values() for reason in j['reasons']],'overlap_15':old['overlap_15']}
  row=draft(p,feedback);row['redrafted']=True;row['judges']={'judge_a':judge(p,row,'judge_a'),'judge_b':judge(p,row,'judge_b')};row['accepted']=all(j['passed'] is True for j in row['judges'].values()) and not row['overlap_15'] and row['draft']['field'] in m['fields'];return row
 revised=parallel(revise,[(p['id'],(p,)) for p in failed],'one_redraft_and_two_judges') if failed else {}
 rows.update(revised);(dest/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 final_passes=sum(r['accepted'] for r in rows.values());disagreements=sum(j['judge_a']['passed']!=j['judge_b']['passed'] for j in judged.values())
 summary=budget.summary();report.update(status='stopped_drop_threshold' if (200-final_passes)/200>m['stop_final_drop_fraction'] else 'completed',initial_passes=initial_passes,final_passes=final_passes,redrafted=len(failed),dropped=200-final_passes,initial_judge_disagreements=disagreements,budget=summary,cost_per_attempted_entry_usd=summary['receipted_usd']/200,cost_per_accepted_entry_usd=summary['receipted_usd']/final_passes if final_passes else None,full_run_authorized=False)
 (ROOT/'reports/pilot-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--key-file',type=Path);a=p.parse_args()
 if a.execute and not a.key_file:p.error('--key-file required for authorized pilot execution')
 run(a.execute,a.key_file)
