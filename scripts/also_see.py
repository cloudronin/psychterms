"""Local, deterministic see-also rules and dependency-free build validation."""
import collections,json,math,re,unicodedata
from core import ROOT,digest
from risk_registry import prepare as prepare_risk

PARAMS={'cap':5,'neighbours_k':20,'min_cosine':0.60}
IRREGULAR={'analysis':'analyses','diagnosis':'diagnoses','hypothesis':'hypotheses','psychosis':'psychoses',
 'neurosis':'neuroses','crisis':'crises','axis':'axes','criterion':'criteria','phenomenon':'phenomena',
 'matrix':'matrices','index':'indices','cortex':'cortices','nucleus':'nuclei','stimulus':'stimuli',
 'locus':'loci','medium':'media','bacterium':'bacteria','child':'children','person':'people',
 'man':'men','woman':'women','foot':'feet','tooth':'teeth','datum':'data','bias':'biases','status':'statuses'}

def tokens(value):return tuple(re.findall(r'\w+',unicodedata.normalize('NFKC',value).casefold()))

def forms(value):
    parts=tokens(value)
    if not parts:return set()
    word=parts[-1];variants={word}
    if word in IRREGULAR:variants.add(IRREGULAR[word])
    elif word in IRREGULAR.values():variants.update(k for k,v in IRREGULAR.items() if v==word)
    elif word.endswith('ies') and len(word)>4:variants.add(word[:-3]+'y')
    elif word.endswith(('ches','shes','xes','zes','sses')):variants.add(word[:-2])
    elif word.endswith('s') and not word.endswith(('ss','us','is','ias')) and word not in ('bias','gas'):
        variants.add(word[:-1])
    elif word.endswith('y') and len(word)>1 and word[-2] not in 'aeiou':variants.add(word[:-1]+'ies')
    elif word.endswith(('s','x','z','ch','sh')):variants.add(word+'es')
    else:variants.add(word+'s')
    return {parts[:-1]+(v,) for v in variants}

def resolve(ident,redirects):
    seen=set()
    while ident in redirects:
        if ident in seen:raise ValueError('Redirect cycle')
        seen.add(ident);ident=redirects[ident]
        if not isinstance(ident,str):raise ValueError('Redirect target must be an ID')
    return ident

def load_context(root=ROOT):
    entries=[json.loads(p.read_text()) for p in sorted((root/'data/entries').glob('*.json'))]
    history=json.loads((root/'data/status-history.json').read_text())['entries']
    drops=json.loads((root/'data/drop-decisions.json').read_text())['entries']
    eligible=[e for e in entries if history[e['id']]['status'] in ('candidate','reviewed','judged') and e['id'] not in drops]
    risk_entries,pin=prepare_risk(eligible,root)
    risk={e['id'] for e in risk_entries if e.get('risk')}
    redirects=json.loads((root/'data/redirects.json').read_text())['redirects']
    stop=json.loads((root/'data/also_see_stoplist.json').read_text())['words']
    eligible=sorted((e for e in eligible if e['id'] not in redirects),key=lambda e:e['id'])
    by_id={e['id']:e for e in eligible}
    for ident in redirects:
        if resolve(ident,redirects) not in by_id:raise ValueError('Redirect target is not published')
    fingerprints=[{k:e.get(k) for k in ('id','term','definition','field','aliases','packet_hash','provenance')} for e in eligible]
    return eligible,risk,redirects,stop,{'entry_set_hash':digest(fingerprints),
        'input_hash':digest({'entries':fingerprints,'risk':sorted(risk),'redirects':redirects,'stoplist':stop,'params':PARAMS}),
        'risk_register':pin}

def mention_index(entries,stoplist):
    stopped=set().union(*(forms(w) for w in stoplist));trie={}
    for e in entries:
        for label in (e['term'],*e.get('aliases',[])):
            if len(''.join(tokens(label)))<=3:continue
            for form in forms(label):
                if form in stopped:continue
                node=trie
                for word in form:node=node.setdefault(word,{})
                node.setdefault(None,set()).add(e['id'])
    return trie

def mentions(definition,trie):
    words=tokens(definition);found={}
    for start in range(len(words)):
        node=trie
        for end in range(start,len(words)):
            node=node.get(words[end])
            if node is None:break
            for ident in node.get(None,()):
                rank=(start,-(end-start+1))
                if ident not in found or rank<found[ident]:found[ident]=rank
    return found

def assemble(entries,risk,redirects,stoplist,neighbours,params=PARAMS):
    by_id={e['id']:e for e in entries};trie=mention_index(entries,stoplist)
    packets=collections.defaultdict(set);scopes=collections.defaultdict(set)
    for e in entries:
        if e.get('packet_hash'):packets[e['packet_hash']].add(e['id'])
        for p in e.get('provenance',[]):
            if p.get('scope'):scopes[p['scope']].add(e['id'])
    result={};blocked=set();field_rejected=set()
    def headword(ident):return (by_id[ident]['term'].casefold(),ident)
    for e in entries:
        ident=e['id'];chosen=[];used=set()
        def permitted(target):
            target=resolve(target,redirects)
            if target==ident or target not in by_id:return None
            if target in risk:blocked.add((ident,target));return None
            return target
        hits=mentions(e['definition'],trie)
        for target in sorted(hits,key=lambda t:(hits[t],headword(t))):
            target=permitted(target)
            if target and target not in used and len(chosen)<params['cap']:
                chosen.append({'to':target,'signal':'mention','score':None});used.add(target)
        packet_group=packets.get(e.get('packet_hash'),set());scope_group=set()
        for p in e.get('provenance',[]):scope_group.update(scopes.get(p.get('scope'),()))
        same=0
        for target in sorted(packet_group|scope_group,key=lambda t:(t not in packet_group,headword(t))):
            target=permitted(target)
            if target and target not in used and same<3 and len(chosen)<params['cap']:
                chosen.append({'to':target,'signal':'same_source','score':None});used.add(target);same+=1
        candidates=neighbours.get(ident,[])[:params['neighbours_k']]
        for raw,score in candidates:
            if score<params['min_cosine']:continue
            target=permitted(raw)
            if not target or target in used:continue
            if e['field']!=by_id[target]['field']:field_rejected.add((ident,target));continue
            if len(chosen)<params['cap']:
                chosen.append({'to':target,'signal':'embedding','score':round(float(score),6)});used.add(target)
        result[ident]=chosen
    return result,{'embedding_field_rejected':len(field_rejected),'inbound_risk_blocked':len(blocked)}

def validate_graph(data,entries,risk,redirects,fingerprint,stoplist=()):
    if data['params']!=PARAMS or data['input_hash']!=fingerprint['input_hash'] or data['entry_set_hash']!=fingerprint['entry_set_hash']:raise ValueError('Stale see-also inputs or parameters; regenerate locally')
    if data['risk_register']!=fingerprint['risk_register']:raise ValueError('Stale see-also risk register')
    by_id={e['id']:e for e in entries}
    trie=mention_index(entries,stoplist)
    if set(data['links'])!=set(by_id):raise ValueError('See-also cohort is not the published corpus')
    if not re.fullmatch(r'[a-f0-9]{64}',data['model_hash']):raise ValueError('Missing model weight hash')
    for ident,links in data['links'].items():
        seen=set();order=[];same=0;scores=[]
        hits=mentions(by_id[ident]['definition'],trie) if any(r['signal']=='mention' for r in links) else {}
        if len(links)>5:raise ValueError('See-also cap exceeded')
        for link in links:
            target=link['to'];signal=link['signal'];score=link['score']
            if target not in by_id or target in risk or target in redirects or target==ident or target in seen:raise ValueError('Invalid, duplicate, self, dropped, redirect or risk target')
            seen.add(target)
            if signal not in ('mention','same_source','embedding'):raise ValueError('Unknown link signal')
            order.append(('mention','same_source','embedding').index(signal))
            if signal=='mention' and target not in hits:raise ValueError('Mention link lacks a headword or alias match')
            if signal=='same_source':
                same+=1
                a,b=by_id[ident],by_id[target]
                scopes_a={p['scope'] for p in a.get('provenance',[]) if p.get('scope')}
                scopes_b={p['scope'] for p in b.get('provenance',[]) if p.get('scope')}
                if not (a.get('packet_hash') and a.get('packet_hash')==b.get('packet_hash')) and not scopes_a.intersection(scopes_b):raise ValueError('Same-source link lacks a shared packet or scope')
            if signal=='embedding':
                if type(score) not in (int,float) or not math.isfinite(score) or not PARAMS['min_cosine']<=score<=1.000001:raise ValueError('Invalid cosine')
                if by_id[ident]['field']!=by_id[target]['field']:raise ValueError('Cross-field embedding')
                scores.append(score)
            elif score is not None:raise ValueError('Only embeddings have scores')
        if order!=sorted(order) or same>3 or scores!=sorted(scores,reverse=True):raise ValueError('Invalid signal ordering or source cap')
    return {'eligible_entries':len(entries),'links':sum(map(len,data['links'].values())),'inbound_risk_links':0}

def check_file(root=ROOT):
    path=root/'data/also_see.json'
    if not path.exists():return None
    entries,risk,redirects,stop,fp=load_context(root)
    data=json.loads(path.read_text());pin=json.loads((root/'data/also_see_model.json').read_text())
    if data['model']!=pin['model'] or data['model_hash']!=pin['weights_sha256'] or data['model_revision']!=pin['revision']:raise ValueError('See-also model pin differs')
    return validate_graph(data,entries,risk,redirects,fp,stop)

if __name__=='__main__':print(json.dumps(check_file(),indent=2))
