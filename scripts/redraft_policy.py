"""Separate immutable failed entries from headwords needing fresh source packets."""
from collections import defaultdict
import unicodedata,json
from pathlib import Path
from core import ROOT
from core import digest

SCOPE_REASON='No psychology or counselling context established'
LEGACY_SCOPE_REASON='The pinned source packet does not establish a psychology, counselling, neural, educational, ethical or research-method context.'
TERMINAL={'dropped','redraft'}

def headword_key(term):
    return ' '.join(unicodedata.normalize('NFKC',term).casefold().split())

def disposition(reason):
    return 'dropped' if reason.strip().rstrip('.') in {SCOPE_REASON,LEGACY_SCOPE_REASON.rstrip('.')} else 'redraft'

def packet_basis_hash(packet):
    # Entry IDs and administrative metadata cannot make an old packet new.
    return digest({'term':headword_key(packet['term']),'source':packet.get('source'),
                   'source_record':packet.get('source_record'),
                   'text':' '.join(unicodedata.normalize('NFKC',packet.get('text','')).casefold().split())})

def packet_rejected(packet,row):
    excluded=set(row.get('excluded_packet_basis_hashes',[]))
    excluded.update(row.get('latest_sourcing',{}).get('excluded_packet_basis_hashes',[]))
    return packet_basis_hash(packet) in excluded

def headword_exclusions(root=ROOT):
    path=root/'data/headword-exclusions.json'
    if not path.exists():return set()
    rows=json.loads(path.read_text())['exclusions']
    return {headword_key(name) for row in rows for name in [row['headword_key'],*row.get('aliases',[])]}

def candidate_pool(entries,outcomes=None,exclusions=None):
    groups=defaultdict(list);active=set();out_of_scope=set(headword_exclusions() if exclusions is None else exclusions)
    for e in entries:
        key=headword_key(e['term'])
        if e['status']=='redraft':groups[key].append(e)
        elif e['status']=='dropped':out_of_scope.add(key)
        else:active.add(key)
    outcomes=outcomes or {};rows=[]
    for key,failed in sorted(groups.items()):
        if key in active or key in out_of_scope:continue
        rows.append({'term':failed[0]['term'],'headword_key':key,'status':'candidate',
            'requirement':outcomes.get(key,{}).get('requirement','new packet required'),'failed_entry_ids':sorted(e['id'] for e in failed),
            'excluded_packet_hashes':sorted({e['packet_hash'] for e in failed}),
            **({'latest_sourcing':outcomes[key]} if key in outcomes else {}),
            **({'excluded_packet_basis_hashes':outcomes[key]['excluded_packet_basis_hashes']}
               if outcomes.get(key,{}).get('excluded_packet_basis_hashes') else {})})
    return {'schema_version':1,'candidates':rows}

def validate_replacements(entries,packets):
    by_id={e['id']:e for e in entries};failed=defaultdict(list);dropped=set()
    for e in entries:
        if e['status']=='redraft':failed[headword_key(e['term'])].append(e)
        elif e['status']=='dropped':dropped.add(headword_key(e['term']))
    for e in entries:
        if e['status'] in TERMINAL:continue
        key=headword_key(e['term']);prior=failed.get(key,[])
        if key in dropped:raise ValueError('Out-of-scope headword cannot be redrafted: '+e['term'])
        if not prior:
            if e.get('redraft_of'):raise ValueError('Replacement lacks a failed entry for this headword')
            continue
        if set(e.get('redraft_of',[]))!={p['id'] for p in prior}:raise ValueError('Replacement must name its failed entries: '+e['id'])
        packet=packets[e['id']]
        if set(packet.get('redraft_of',[]))!=set(e['redraft_of']):raise ValueError('Replacement lineage differs from its packet')
        basis=packet_basis_hash(packet)
        if any(basis==packet_basis_hash(packets[p['id']]) for p in prior):raise ValueError('Replacement needs a new source packet: '+e['id'])
        if any(e['packet_hash']==p['packet_hash'] or e['provenance']==p['provenance'] for p in prior):raise ValueError('Replacement needs new provenance: '+e['id'])
        def receipts(row):
            return {r['receipt_id'] for r in [row.get('draft_evidence',{}),row.get('model_review',{}),*row.get('reader_reviews',[])] if r.get('receipt_id')}
        if any(receipts(e)&receipts(p) for p in prior):raise ValueError('Replacement cannot inherit drafting or reader receipts: '+e['id'])
