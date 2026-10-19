"""Validate local inference provenance without disguising it as hosted API evidence."""
import functools,json,re
from core import ROOT,digest

def identity(name,pin):return 'Ollama '+name+' ('+pin['digest'][:12]+')'

@functools.lru_cache(maxsize=16384)
def read(path,mtime):return json.loads(path.read_text())

def load(path):return read(path,path.stat().st_mtime_ns)

def validate(entry,packet,root=ROOT):
    reference=entry.get('local_run')
    if not reference:return
    batch=reference['batch']
    if not re.fullmatch('[a-z0-9-]+',batch):raise ValueError('Invalid local evidence batch')
    directory=root/'data/local-runs'/batch;manifest=load(directory/'registration.json')
    if digest(manifest)!=reference['manifest_sha256'] or manifest['registration_hash']!=digest({k:v for k,v in manifest.items() if k!='registration_hash'}):raise ValueError('Local registration binding changed')
    receipts={role:load(directory/'receipts'/(sha+'.json')) for role,sha in reference['receipts'].items()}
    validate_records(entry,packet,manifest,receipts,root)

def validate_records(entry,packet,manifest,receipts,root=ROOT):
    reference=entry['local_run']
    if digest(manifest)!=reference['manifest_sha256'] or manifest['registration_hash']!=digest({k:v for k,v in manifest.items() if k!='registration_hash'}):raise ValueError('Local registration binding changed')
    hybrid=manifest.get('line')=='hybrid-redrafts-v1'
    if hybrid:
        if manifest['paid_dispatch_enabled'] is not True or manifest['paid_cap_usd']!=200 or manifest['paid_roles']!=['draft'] or manifest['endpoint']!='http://127.0.0.1:11434/api/':raise ValueError('Hybrid authorization differs')
    elif manifest['paid_dispatch_enabled'] is not False or manifest['paid_cap_usd']!=0 or manifest['endpoint']!='http://127.0.0.1:11434/api/':raise ValueError('Local inference registration permits hosted dispatch')
    if entry['version']!=2 or not entry.get('redraft_of') or packet.get('redraft_of')!=entry['redraft_of']:raise ValueError('Local replacement needs version 2 and packet-bound lineage')
    roles=manifest['roles'];models=manifest['models']
    if len({roles['draft'] if hybrid and r=='draft' else models[roles[r]]['digest'] for r in ('draft','reader_a','reader_b')})!=3:raise ValueError('Local draft and reader weights are not distinct')
    from external_reader import reviewed_field
    field=reviewed_field(entry,root)
    definition={'definition':entry['definition'],'field':field,'packet_sufficient':True}
    proof_by_model={r['model']:r for r in entry['reader_reviews']}
    if len(proof_by_model)!=2:raise ValueError('Two local reader proofs required')
    for role in ('fit','draft','reader_a','reader_b'):
        sha=reference['receipts'][role]
        if not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('Invalid local receipt hash')
        receipt=receipts[role]
        if hybrid and role=='draft':
            from hybrid_draft import validate_receipt
            validate_receipt(receipt,manifest,packet,field,definition,entry['draft_evidence'],sha)
            continue
        model=roles[role];request=receipt['request'];response=receipt['response'];kind='read' if role.startswith('reader') else role
        if digest(receipt)!=sha or receipt['role']!=role or receipt['model']!=model or receipt['model_digest']!=models[model]['digest']:raise ValueError('Local receipt model or role differs')
        if receipt['evidence_kind']!='local Ollama inference' or receipt['paid_usd']!=0:raise ValueError('Local inference origin differs')
        if receipt['registration_hash']!=manifest['registration_hash'] or receipt['packet_hash']!=packet['packet_hash'] or receipt['request_hash']!=digest(request):raise ValueError('Local receipt packet or request differs')
        if request['model']!=model or request['format']!=manifest['schemas'][kind] or request['stream'] is not False:raise ValueError('Local request differs from registered form')
        if request['options']!={**manifest['options'],'num_predict':manifest['max_output_tokens'][kind]}:raise ValueError('Local sampling or context parameters changed')
        if 'thinking' in models[model]['capabilities'] and request.get('think') is not False:raise ValueError('Local thinking mode differs')
        expected_prompt=manifest['prompts'][kind]
        if kind=='fit':expected_prompt=expected_prompt.format(headword=entry['term'])
        expected_input={'headword':entry['term'],'field':field,'source':packet['source'],'source_record':packet['source_record'],'revision':packet['revision'],'text':packet['text']}
        if kind=='read':expected_input['definition']=entry['definition']
        if len(request['messages'])!=2 or request['messages'][0]!={'role':'system','content':expected_prompt} or request['messages'][1]['role']!='user' or json.loads(request['messages'][1]['content'])!=expected_input:raise ValueError('Local inference prompt or input changed')
        if response['model']!=model or not response.get('done') or response.get('done_reason')!='stop':raise ValueError('Incomplete local inference receipt')
        value=json.loads(response['message']['content'])
        if kind=='fit':
            if value.get('answer')!='yes' or not isinstance(value.get('reason'),str) or not value['reason'].strip() or '\n' in value['reason']:raise ValueError('Packet did not pass local fit gate')
            continue
        proof=entry['draft_evidence'] if kind=='draft' else proof_by_model.get(identity(model,models[model]),{})
        if any(proof.get(k)!=receipt[k] for k in ('receipt_id','request_hash','registration_hash','packet_hash')) or proof.get('model')!=identity(model,models[model]):raise ValueError('Local proof differs from its receipt')
        if proof['definition_hash']!=digest(definition):raise ValueError('Local proof definition changed')
        if kind=='draft' and value!=definition:raise ValueError('Local draft differs from actual model response')
        if kind=='read' and (value!={'passed':True,'reasons':[]} or proof.get('passed') is not True or proof.get('reasons')!=[] or proof.get('draft_model')!=entry['draft_evidence']['model'] or proof.get('published_packet_hash')!=packet['packet_hash']):raise ValueError('Local reader did not pass the definition')
