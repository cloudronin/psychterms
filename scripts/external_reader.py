"""Validate human-supplied reader artifacts without inventing API receipts."""
import csv,functools,hashlib,io,json,re
from core import ROOT,digest,semantic_hash

@functools.lru_cache(maxsize=8)
def _load(directory,batch,pin,manifest_mtime,csv_mtime):
    folder=directory/'data/external-reviews'/batch
    manifest=json.loads((folder/'manifest.json').read_text())
    if digest(manifest)!=pin:raise ValueError('External reader manifest hash mismatch')
    raw=(folder/'verdicts.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['artifact_sha256']:raise ValueError('External reader CSV hash mismatch')
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    by_id={r['id']:r for r in rows}
    if len(by_id)!=len(rows) or set(by_id)!=set(manifest['entries']):raise ValueError('External reader cohort differs')
    return manifest,by_id

def evidence(entry,root=ROOT):
    ref=entry.get('external_review')
    if not ref:return None
    batch=ref['batch']
    if not re.fullmatch(r'[a-z0-9-]+',batch):raise ValueError('Invalid external review batch')
    folder=root/'data/external-reviews'/batch
    m,rows=_load(root,batch,ref['manifest_sha256'],(folder/'manifest.json').stat().st_mtime_ns,(folder/'verdicts.csv').stat().st_mtime_ns)
    binding=m['entries'][entry['id']];row=rows[entry['id']]
    if digest(row)!=binding['row_sha256'] or row['term']!=entry['term']:raise ValueError('External reader row differs')
    field=row['field'][8:] if row['field'].startswith('suggest:') else binding['from_field']
    if row['field']!='ok' and not row['field'].startswith('suggest:'):raise ValueError('Invalid external reader field decision')
    if field!=binding['to_field'] or entry['field']!=field:raise ValueError('Unapproved field correction')
    if row['verdict'] not in ('PASS','FAIL') or row['verdict']!=binding['verdict']:raise ValueError('Invalid external verdict')
    # Risk is derived later by the build; the attested snapshot is the raw source entry.
    before={k:v for k,v in entry.items() if k!='risk'};before['field']=binding['from_field']
    if semantic_hash(before)!=binding['before_entry_hash'] or entry['version']!=binding['after_version']:raise ValueError('External reader definition or snapshot changed')
    expected=digest({'definition':entry['definition'],'field':binding['from_field'],'packet_sufficient':True})
    if expected!=binding['reviewed_definition_hash'] or entry['packet_hash']!=binding['packet_hash']:raise ValueError('External reader packet or definition changed')
    return {'model':m['reader_model'],'passed':row['verdict']=='PASS','reasons':[] if row['verdict']=='PASS' else [row['reason']],
        'evidence_kind':'user-supplied CSV','artifact_sha256':m['artifact_sha256'],'row_sha256':binding['row_sha256'],
        'reviewed_field':binding['from_field'],'approved_field':field,'packet_hash':binding['packet_hash']}

def reviewed_field(entry,root=ROOT):
    proof=evidence(entry,root)
    return proof['reviewed_field'] if proof else entry['field']
