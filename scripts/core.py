"""Offline content contract. There are no paid API clients in this scaffold."""
from pathlib import Path
import hashlib
import json
import re
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
SEMANTIC=('id','term','definition','also_see','field','aliases','sources','provenance','exam_layer_id','risk','redraft_of')
ALLOWED_LICENSES={'public-domain-US-government','public-domain-US','CC0-1.0','CC-BY-2.0','CC-BY-2.5','CC-BY-3.0','CC-BY-4.0','OGL-UK-3.0'}

def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def semantic_hash(entry): return digest({k:entry[k] for k in SEMANTIC if k in entry})
def normalize(text): return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',text).casefold()))
def slug(term):
    value=re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',term).encode('ascii','ignore').decode().lower()).strip('-')
    if not value: raise ValueError('Term requires an explicitly assigned stable ID')
    return value

def validate_entry(entry, sources, fields, release=False, built=False):
    required={'id','term','definition','also_see','field','aliases','sources','provenance','version','hash'}
    if not required <= entry.keys(): raise ValueError('Missing entry fields')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',entry['id']): raise ValueError('Invalid ID')
    if not isinstance(entry['term'],str) or not entry['term'].strip(): raise ValueError('Empty term')
    if entry['field'] not in fields: raise ValueError('Unknown field')
    if 'risk_term' in entry: raise ValueError('Legacy risk flag is forbidden; risk is build-owned')
    if 'risk' in entry and entry['risk'] is not True: raise ValueError('Risk flags cannot be removed by hand')
    if entry.get('risk') and 'vignette' in entry: raise ValueError('Risk entry cannot contain a scene')
    if 'vignette' in entry: raise ValueError('Scene publication requires a reviewed unbound-card import; pilot scenes are private')
    if entry['hash']!=semantic_hash(entry): raise ValueError('Semantic hash mismatch')
    if type(entry['version']) is not int or entry['version']<1: raise ValueError('Invalid version')
    for name in ('also_see','aliases','sources'):
        if not isinstance(entry[name],list) or any(not isinstance(v,str) for v in entry[name]):raise ValueError('Invalid '+name)
        if len(entry[name])!=len(set(entry[name])):raise ValueError('Repeated '+name)
    if not isinstance(entry['definition'],str) or not entry['definition'].strip():raise ValueError('Empty definition')
    if '\n' in entry['definition']:raise ValueError('Definition must be one paragraph')
    # Conservative mechanical prefilter; both judges assess sentence structure semantically.
    if len(re.findall(r'[.!?](?:\s|$)',entry['definition']))>3:raise ValueError('More than three sentences')
    if re.search(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|µg|ml)\b',entry['definition'],re.I):raise ValueError('Dose-like content')
    basis=False
    for source_id in entry['sources']:
        if source_id not in sources:raise ValueError('Unknown source')
    for item in entry['provenance']:
        if item['source'] not in entry['sources']:raise ValueError('Provenance source absent from sources')
        if item['role'] not in {'draft_basis','supports_definition','related_topic'}:raise ValueError('Unknown provenance role')
        source=sources[item['source']]
        if not item.get('revision') or not item.get('scope'):raise ValueError('Unpinned provenance')
        if item['role'] in {'draft_basis','supports_definition'}:
            if source['decision']!='yes' or source['licence'] not in ALLOWED_LICENSES:raise ValueError('Unpermitted source')
            if item['role'] not in source['roles']:raise ValueError('Source role not allowed')
        if item['role']=='draft_basis':basis=True
    if not basis:raise ValueError('No permitted drafting basis')
    computed={'status','checks','released','release_versions','drafter','drop_reason','new_packet_required','scope_review'}
    if 'review_status' in entry:raise ValueError('Legacy review_status is forbidden; status is build-owned')
    if not built and computed & entry.keys():raise ValueError('Status and release markers are build-owned')
    if built:
        if entry.get('status') not in {'candidate','reviewed','judged','dropped','redraft'} or type(entry.get('released')) is not bool or 'checks' not in entry:raise ValueError('Missing build-owned review state')
    if 'redraft_of' in entry:
        if not isinstance(entry['redraft_of'],list) or not entry['redraft_of'] or any(not isinstance(i,str) or i==entry['id'] for i in entry['redraft_of']) or len(set(entry['redraft_of']))!=len(entry['redraft_of']):raise ValueError('Invalid redraft lineage')
    if entry.get('draft_evidence'):validate_draft_evidence(entry)
    elif entry.get('model_review'):validate_model_review(entry)
    elif entry.get('fixture') is not True or entry['id'] not in {'attention','memory','psychotherapy'}:raise ValueError('Missing drafting evidence')
    if release and (not built or entry.get('released') is not True or entry.get('status') in {'dropped','redraft'}):
        raise ValueError('Preview entry needs a build-assigned numbered-release marker')



def validate_draft_evidence(entry):
    evidence=entry.get('draft_evidence',{})
    from external_reader import reviewed_field
    expected=digest({'definition':entry['definition'],'field':reviewed_field(entry),'packet_sufficient':True})
    if evidence.get('definition_hash')!=expected or evidence.get('packet_hash')!=entry.get('packet_hash'):raise ValueError('Draft evidence no longer matches definition or packet')
    for key in ('request_hash','registration_hash'):
        if not re.fullmatch(r'[a-f0-9]{64}',evidence.get(key,'')):raise ValueError('Missing draft binding')
    if not evidence.get('receipt_id') or not evidence.get('model'):raise ValueError('Missing draft receipt')


def validate_model_review(entry):
    review=entry.get('model_review',{})
    if review.get('model')!='gpt-5.4-mini-2026-03-17' or review.get('passed') is not True:raise ValueError('Designated mini judge must pass')
    if review.get('draft_model')==review.get('model'):raise ValueError('Judge must differ from drafter')
    from external_reader import reviewed_field
    expected=digest({'definition':entry['definition'],'field':reviewed_field(entry),'packet_sufficient':True})
    if review.get('definition_hash')!=expected or review.get('published_packet_hash')!=entry.get('packet_hash'):raise ValueError('Model verdict no longer matches definition or packet')
    for key in ('request_hash','registration_hash','packet_hash'):
        if not re.fullmatch(r'[a-f0-9]{64}',review.get(key,'')):raise ValueError('Missing model review binding')
    if not review.get('receipt_id'):raise ValueError('Missing model review receipt')
    packet=json.loads((ROOT/'data/packets'/(entry['id']+'.json')).read_text())
    reviewed_packet=packet.get('original_packet_hash',packet.get('packet_hash'))
    if reviewed_packet!=review['packet_hash']:raise ValueError('Judge reviewed a different source packet')
    from check_packets import validate_packet
    sources={s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text())['sources']}
    validate_packet(packet,sources)

def validate_reviews(entry):
    if 'model_review' in entry:
        validate_model_review(entry)
        return
    reviews=entry.get('reviews',[])
    if len(reviews)!=2 or len({r.get('model') for r in reviews})!=2:raise ValueError('Two distinct judge models required')
    packet=entry.get('packet_hash')
    if not packet or not re.fullmatch(r'[a-f0-9]{64}',packet):raise ValueError('Missing packet hash')
    for r in reviews:
        if r.get('passed') is not True or r.get('entry_hash')!=entry['hash'] or r.get('packet_hash')!=packet:raise ValueError('Judge result is failed or stale')
        if not r.get('receipt_id') or not r.get('rubric_hash'):raise ValueError('Unrecorded judge evidence')

def validate_corpus(entries,sources,fields,release=False,built=False):
    ids=[e['id'] for e in entries]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate IDs')
    seen={}
    for e in entries:
        validate_entry(e,sources,fields,release,built)
        if set(e['also_see'])-set(ids):raise ValueError('Unresolved also_see')
        if e['id'] in e['also_see']:raise ValueError('Self link')
        normalized=normalize(e['definition'])
        if normalized in seen:raise ValueError('Exact duplicate definitions: '+seen[normalized]+' / '+e['id'])
        seen[normalized]=e['id']
    return {'entries':len(entries),'release':release,'corpus_hash':digest(sorted(entries,key=lambda e:e['id']))}

def load_inputs():
    entries=[json.loads(p.read_text()) for p in sorted((ROOT/'data/entries').glob('*.json'))]
    sources={s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text())['sources']}
    fields=json.loads((ROOT/'data/fields.json').read_text())['fields']
    return entries,sources,fields
