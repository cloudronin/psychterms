"""The only hosted dispatch in the hybrid run: a budget-reserved drafting call."""
import json,math,time,urllib.request,uuid
from pathlib import Path
from core import ROOT,canonical,digest
from budget import Budget

ENDPOINT='https://api.openai.com/v1/chat/completions'
MODEL='gpt-5.4-2026-03-05'

def body_for(m,packet,field):
    api=m['api']
    if api['endpoint']!=ENDPOINT or api['model']!=MODEL or m['paid_roles']!=['draft']:raise ValueError('Only the registered drafting endpoint and snapshot are permitted')
    data={'headword':packet['term'],'field':field,'source':packet['source'],'source_record':packet['source_record'],'revision':packet['revision'],'text':packet['text']}
    return {'model':MODEL,'messages':[{'role':'system','content':m['prompts']['draft']},{'role':'user','content':json.dumps(data,ensure_ascii=False)}],
        'response_format':{'type':'json_schema','json_schema':{'name':'dictionary_result','strict':True,'schema':m['schemas']['draft']}},
        'max_completion_tokens':api['max_completion_tokens'],'reasoning_effort':api['reasoning_effort'],'store':False}

def charge_for(usage,prices):
    cached=usage.get('prompt_tokens_details',{}).get('cached_tokens',0)
    return math.ceil((usage['prompt_tokens']-cached)*prices['input']+cached*prices['cached_input']+usage['completion_tokens']*prices['output'])

def call(m,dest,packet,field):
    from hybrid_redraft import atomic,code_hashes,ProtocolError,validate_result
    if json.loads((dest/'registration.json').read_text())!=m or code_hashes()!=m['code_hashes']:raise ProtocolError('Registered hybrid implementation changed')
    if m['paid_dispatch_enabled'] is not True or m['paid_cap_usd']!=200:raise ProtocolError('Paid drafting registration differs')
    body=body_for(m,packet,field);raw=canonical(body);request_hash=digest(body)
    if len(raw)>24000:raise ProtocolError('Draft request exceeds registered 24,000-byte limit')
    cache=dest/'calls'/('draft-'+request_hash+'.json')
    budget=Budget(dest/'budget.sqlite',int(m['paid_cap_usd']*1e6))
    if cache.exists():
        saved=json.loads(cache.read_text());receipt=json.loads((dest/'receipts'/(saved['receipt_id']+'.json')).read_text())
        if digest(receipt)!=saved['receipt_hash'] or receipt['request']!=body or receipt['registration_hash']!=m['registration_hash'] or receipt['packet_hash']!=packet['packet_hash']:raise ProtocolError('API cached evidence changed')
        if json.loads(receipt['response']['choices'][0]['message']['content'])!=saved['parsed']:raise ProtocolError('Cached draft differs from provider response')
        validate_result('draft',saved['parsed']);return saved
    # Uncertain billable attempts must be reconciled before another dispatch, including after restart.
    if budget.summary()['unresolved_reservations_usd']:raise ProtocolError('Uncertain provider charge remains reserved; reconcile before continuing')
    key=Path('/tmp/OPEN_AI_API.txt').read_text().strip()
    if not key:raise ProtocolError('Drafting API credential is empty')
    prices=m['api']['prices_per_million']
    reserve=math.ceil((len(raw)+512)*prices['input']+m['api']['max_completion_tokens']*prices['output'])
    # One call per packet. No automatic billable retries.
    rid='api-'+uuid.uuid4().hex
    try:budget.reserve(rid,'draft',reserve)
    except RuntimeError as error:raise ProtocolError(str(error)) from error
    request=urllib.request.Request(ENDPOINT,data=raw,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    # No redirects or proxy-based endpoint substitution; credentials never enter receipts.
    from local_redraft import NoRedirect
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    start=time.monotonic()
    try:
        with opener.open(request,timeout=180) as response:result=json.load(response)
        receipt={'evidence_kind':'OpenAI API drafting','receipt_id':rid,'registration_hash':m['registration_hash'],'role':'draft',
                 'model':MODEL,'packet_hash':packet['packet_hash'],'request_hash':request_hash,'request':body,'response':result,
                 'elapsed_seconds':round(time.monotonic()-start,3),'paid_usd':charge_for(result['usage'],prices)/1e6}
        atomic(dest/'receipts'/(rid+'.json'),receipt)
        budget.reconcile(rid,round(receipt['paid_usd']*1e6))
        if result.get('model')!=MODEL or not result.get('id') or result['choices'][0]['finish_reason']!='stop':raise ValueError('Incomplete or changed API model response')
        parsed=validate_result('draft',json.loads(result['choices'][0]['message']['content']))
        saved={'parsed':parsed,'receipt_id':rid,'receipt_hash':digest(receipt),'request_hash':request_hash,'registration_hash':m['registration_hash'],
               'model':MODEL,'packet_hash':packet['packet_hash'],'paid_usd':receipt['paid_usd']}
        atomic(cache,saved);return saved
    except Exception as error:
        atomic(dest/'errors'/(rid+'.json'),{'role':'draft','request_hash':request_hash,'error_type':type(error).__name__,'http_status':getattr(error,'code',None)})
        # Pause rather than silently turn a paid infrastructure failure into a rejected headword.
        raise ProtocolError('API drafting paused; inspect receipt and reserved budget before resuming') from error

def validate_receipt(receipt,manifest,packet,field,definition,proof,sha):
    if digest(receipt)!=sha or receipt['evidence_kind']!='OpenAI API drafting' or receipt['role']!='draft' or receipt['model']!=MODEL:raise ValueError('API drafting origin differs')
    request=body_for(manifest,packet,field);response=receipt['response']
    if receipt['request']!=request or receipt['request_hash']!=digest(request) or receipt['registration_hash']!=manifest['registration_hash'] or receipt['packet_hash']!=packet['packet_hash']:raise ValueError('API draft request binding differs')
    if response['model']!=MODEL or not response.get('id') or response['choices'][0]['finish_reason']!='stop':raise ValueError('Incomplete API drafting receipt')
    if json.loads(response['choices'][0]['message']['content'])!=definition:raise ValueError('Definition differs from API response')
    if receipt['paid_usd']!=charge_for(response['usage'],manifest['api']['prices_per_million'])/1e6:raise ValueError('API usage cost differs')
    if proof['model']!=MODEL or proof['definition_hash']!=digest(definition) or any(proof.get(k)!=receipt[k] for k in ('receipt_id','request_hash','registration_hash','packet_hash')):raise ValueError('API draft evidence differs')
