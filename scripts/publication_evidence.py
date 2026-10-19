"""Offline verification of the actual provider receipts used for promoted redrafts."""
import json,re
from core import ROOT,digest,semantic_hash
from jsonschema import validate as validate_schema


def validate_record(record,role,entry,packet):
    saved=record['saved'];receipt=record['receipt'];m=record['registration']
    if m['registration_hash']!=digest({k:v for k,v in m.items() if k!='registration_hash'}):
        raise ValueError('Publication registration changed')
    if digest(receipt)!=saved['receipt_hash'] or receipt.get('evidence_kind')!='OpenAI API':
        raise ValueError('Publication receipt changed')
    for key in ('receipt_id','request_hash','registration_hash','packet_hash','model','paid_usd'):
        if saved[key]!=receipt[key]:raise ValueError('Publication saved proof differs')
    if receipt['role']!=role or receipt['registration_hash']!=m['registration_hash'] or receipt['packet_hash']!=packet['packet_hash']:
        raise ValueError('Publication role or packet differs')
    request=receipt['request'];model=receipt['model'];kind='read' if role.startswith('reader') else role
    if request['model']!=model or model!=m['models'][role] or digest(request)!=receipt['request_hash']:
        raise ValueError('Publication request differs')
    prompt=m['prompts'][kind] if 'prompts' in m else m['prompt']
    schema=m['schemas'][kind] if 'schemas' in m else m['schema']
    if request['messages'][0]!={'role':'system','content':prompt} or len(request['messages'])!=2 or request['messages'][1]['role']!='user':
        raise ValueError('Publication prompt differs')
    if request['response_format']['json_schema']['schema']!=schema:raise ValueError('Publication schema differs')
    data=json.loads(request['messages'][1]['content']);source=data.get('source_packet',data)
    if data['headword']!=entry['term'] or data.get('taxonomy_hint',data.get('field'))!=entry['field']:
        raise ValueError('Publication headword or reviewed field differs')
    if any(source.get(k)!=packet[k] for k in ('source','source_record','revision','text')):
        raise ValueError('Publication source differs')
    for holder in (source,data):
        if 'source_record_label' in holder and holder['source_record_label']!=record.get('source_record_label',packet.get('source_label','')):
            raise ValueError('Publication source label differs')
    response=receipt['response'];choice=response['choices'][0]
    if response['model']!=model or not response.get('id') or choice['finish_reason']!='stop':
        raise ValueError('Incomplete publication response')
    parsed=json.loads(choice['message']['content']);validate_schema(parsed,schema)
    if parsed!=saved['parsed']:raise ValueError('Publication response differs')
    if role=='draft':
        if parsed!={'definition':entry['definition'],'field':entry['field'],'packet_sufficient':True}:
            raise ValueError('Publication draft differs')
    else:
        if data.get('draft_to_check')!={'definition':entry['definition']}:raise ValueError('Reader saw a different definition')
        if 'passed' in parsed:
            from retune_protocol import validate_value
            validate_value(role,parsed,packet['text'],entry['definition'])
            if parsed['passed'] is not True:raise ValueError('Publication reader failed')
        elif not all(parsed.get(k) is True for k in ('definition_supported','sense_matches','in_scope')) or parsed.get('reasons')!=[]:
            raise ValueError('Publication context reader failed')
    return saved


def validate_bundle(entry,packet,bundle):
    reviewed=bundle['reviewed_entry']
    from external_reader import reviewed_field
    before={k:v for k,v in entry.items() if k not in ('risk','external_review','publication_evidence','status','checks','released','release_versions','drafter','drop_reason','new_packet_required','scope_review','latest_sourcing')}
    before['field']=reviewed_field(entry)
    before['hash']=semantic_hash(before)
    if before!=reviewed or semantic_hash(before)!=reviewed['hash'] or packet!=bundle['packet']:
        raise ValueError('Publication snapshot differs')
    roles=bundle['records']
    if set(roles)!={'draft','reader_a','reader_b'}:raise ValueError('Publication needs drafting and two reading receipts')
    saved={role:validate_record(value,role,reviewed,packet) for role,value in roles.items()}
    if len({v['model'] for v in saved.values()})!=3:raise ValueError('Publication readers must differ from drafter and each other')
    definition_hash=digest({'definition':reviewed['definition'],'field':reviewed['field'],'packet_sufficient':True})
    if len(entry.get('reader_reviews',[]))!=2:raise ValueError('Publication needs exactly two reader proofs')
    for role,proof in [('draft',entry['draft_evidence']),*zip(('reader_a','reader_b'),entry['reader_reviews'])]:
        s=saved[role]
        if any(proof.get(k)!=s[k] for k in ('receipt_id','model','request_hash','registration_hash','packet_hash')) or proof.get('definition_hash')!=definition_hash:
            raise ValueError('Publication entry proof differs from provider receipt')
        if role!='draft' and (proof.get('passed') is not True or proof.get('draft_model')!=saved['draft']['model']):
            raise ValueError('Publication reader proof is not a pass')
    return True


def validate(entry,packet,root=ROOT):
    pin=entry.get('publication_evidence')
    if not pin:return
    if not re.fullmatch('[a-f0-9]{64}',pin):raise ValueError('Invalid publication evidence hash')
    path=root/'data/publication-evidence'/(entry['id']+'.json')
    bundle=json.loads(path.read_text())
    if digest(bundle)!=pin:raise ValueError('Publication evidence hash differs')
    # External field evidence uses the same root in normal builds.
    return validate_bundle(entry,packet,bundle)
