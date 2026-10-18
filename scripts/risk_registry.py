"""Build-owned risk classification from a versioned, byte-pinned, additive register."""
import copy
import hashlib
import json
import re
import subprocess
from core import ROOT, normalize, semantic_hash


def load_registry(root=ROOT):
    path=root/'data/risk_terms.json'
    raw=path.read_bytes(); registry=json.loads(raw)
    pin=json.loads((root/'data/risk-terms-pin.json').read_text())
    if pin != {'version':registry['version'],'sha256':hashlib.sha256(raw).hexdigest()}:
        raise ValueError('Risk register pin is stale')
    if type(registry['version']) is not int or registry['version']<1:raise ValueError('Invalid risk register version')
    ids=[r['id'] for r in registry['terms']]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate risk register IDs')
    for row in registry['terms']:
        if not row.get('reason') or row.get('test') not in (1,2,3):raise ValueError('Risk term needs a rule and reason')
        if not row.get('names') and not row.get('anchors'):raise ValueError('Risk term needs a name or anchor')
    return registry,pin


def matches(entry,packet,row):
    names={normalize(entry['term']),*(normalize(n) for n in entry.get('aliases',[]))}
    anchors={str(packet.get('source_record','')),*(str(a) for a in packet.get('anchors',[]))}
    return entry['id']==row['id'] or bool(names & {normalize(n) for n in row.get('names',[])}) or bool(anchors & set(row.get('anchors',[])))


def required_tests(entry,packet,registry):
    """Mechanical coverage guard. Explicit instrument/history decisions live in the register."""
    rules=registry['rules']; tests=set()
    text=normalize(json.dumps(packet,ensure_ascii=False))
    if entry['field'] in ('diagnosis','assessment'):
        if any(re.search(r'\b'+re.escape(normalize(term))+r'\b',text) for term in rules['packet_or_anchor_signals']):tests.add(1)
    names=' '.join(normalize(n) for n in [entry['term'],*entry.get('aliases',[])])
    if any(re.search(r'\b'+re.escape(normalize(term))+r'\b',names) for term in rules['named_practices_and_duties']):tests.add(2)
    if packet.get('risk_instrument') is True or re.search(r'\brisk assessment instrument\b|\bsuicide (?:risk )?(?:scale|screen|questionnaire|assessment)\b',text):tests.add(2)
    if packet.get('arcsim_no_risk_history_excluded') is True:tests.add(3)
    return tests


def derive(entries,registry,packets):
    result=[]
    for source in entries:
        if 'risk' in source or 'risk_term' in source:raise ValueError('Risk flags are build-owned; edit risk_terms.json, never an entry flag')
        if source.get('hash')!=semantic_hash(source):raise ValueError('Semantic hash mismatch before risk derivation')
        packet=packets.get(source['id'])
        if not packet or packet.get('packet_hash')!=source.get('packet_hash'):raise ValueError('Risk classification needs the matching pinned packet')
        # Packet hash and anchor contents are checked before deriving any flag.
        from core import digest
        if packet['packet_hash']!=digest({k:v for k,v in packet.items() if k!='packet_hash'}):raise ValueError('Risk packet hash mismatch')
        listed=any(matches(source,packet,row) for row in registry['terms'])
        if required_tests(source,packet,registry) and not listed:
            raise ValueError('Risk coverage missing: add '+source['id']+' to risk_terms.json by pull request')
        entry=copy.deepcopy(source)
        if listed:
            if 'vignette' in entry:raise ValueError('Risk entry cannot contain a scene: '+entry['id'])
            entry['risk']=True
            entry['hash']=semantic_hash(entry)
        result.append(entry)
    return result


def prepare(entries,root=ROOT):
    registry,pin=load_registry(root)
    packets={e['id']:json.loads((root/'data/packets'/(e['id']+'.json')).read_text()) for e in entries}
    return derive(entries,registry,packets),pin


def check_additions(previous,current):
    old={r['id']:r for r in previous['terms']};new={r['id']:r for r in current['terms']}
    if any(new.get(key)!=row for key,row in old.items()):raise ValueError('Risk register entries cannot be removed or weakened')
    for key,values in previous['rules'].items():
        if not set(values)<=set(current['rules'].get(key,[])):raise ValueError('Risk rules cannot be weakened')
    if previous!=current and current['version']<=previous['version']:raise ValueError('Risk register changes require a version bump')


if __name__=='__main__':
    import argparse
    from core import load_inputs
    p=argparse.ArgumentParser();p.add_argument('--base');args=p.parse_args()
    registry,pin=load_registry()
    if args.base:
        subprocess.run(['git','cat-file','-e',args.base+'^{commit}'],cwd=ROOT,check=True,capture_output=True)
        result=subprocess.run(['git','show',args.base+':data/risk_terms.json'],cwd=ROOT,capture_output=True,text=True)
        if result.returncode==0:check_additions(json.loads(result.stdout),registry)
        elif subprocess.run(['git','cat-file','-e',args.base+':data/risk_terms.json'],cwd=ROOT,capture_output=True).returncode==0:raise ValueError('Cannot read baseline risk register')
        # Initial introduction has no predecessor; later PRs must preserve it.
    entries,_=prepare(load_inputs()[0]);print(json.dumps({'entries':len(entries),'risk_entries':sum(e.get('risk',False) for e in entries),'risk_terms':len(registry['terms']),'pin':pin},indent=2))
