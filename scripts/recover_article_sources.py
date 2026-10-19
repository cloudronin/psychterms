"""Recover permitted article passages from private bibliographic leads, never legacy prose.

Article XML is obtained from Europe PMC. Only an article's own explicit CC BY
2.0/2.5/3.0/4.0 notice admits its original abstract/introduction/background text. Figures,
tables, references, quoted text, cases and empirical results are excluded.
"""
import collections,concurrent.futures,hashlib,json,re,threading,time,urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from core import ROOT,digest
from source_coverage_audit import norm

DEST=ROOT/'.private/source-recovery'
AUDIT=ROOT/'.private/coverage-audit'
LOCK=threading.Lock()
LAST=0.0
DEFINED_LOCK=threading.Lock()
DEFINED_CACHE=(0.0,set())
NS='{http://www.w3.org/1999/xlink}'

def text(node):
    return ' '.join(' '.join(node.itertext()).split()) if node is not None else ''

def excluded_paragraph(value):
    quoted=re.findall(r'[“\"]([^”\"\n]{20,1500})[”\"]',value)
    return any(len(q.split())>=8 for q in quoted) or bool(re.search(r'dictionary\.apa\.org|APA Dictionary|American Psychological Association.{0,100}(?:defin|describ)',value,re.I))

def parse_article(raw,pmcid,doi):
    root=ET.fromstring(raw)
    if root.get('article-type') in ('case-report','correction','retraction'):raise ValueError('Case, correction or retraction excluded')
    meta=root.find('./front/article-meta')
    if meta is None:raise ValueError('Missing article metadata')
    ids={n.get('pub-id-type'):text(n) for n in meta.findall('article-id')}
    if norm(ids.get('doi',''))!=norm(doi):raise ValueError('Article DOI differs from discovery record')
    title=text(meta.find('title-group/article-title'))
    if re.search(r'case (?:report|study)|case series|retract|correction|corrigendum',title,re.I):raise ValueError('Case, correction or retraction excluded')
    permissions=meta.find('permissions')
    if permissions is None:raise ValueError('No article-specific permission notice')
    licence_xml=ET.tostring(permissions,encoding='unicode')
    versions=re.findall(r'https?://(?:www\.)?creativecommons\.org/licenses/by/(2\.0|2\.5|3\.0|4\.0)/?(?=[\s"<>&)])',licence_xml)
    if not versions or re.search(r'creativecommons\.org/licenses/by-(?:nc|nd|sa)',licence_xml):raise ValueError('No unambiguous permitted versioned CC BY notice')
    version=versions[0];licence='CC-BY-'+version
    authors=[]
    for n in meta.findall('contrib-group/contrib'):
        if n.get('contrib-type', 'author' if any(n in list(g) for g in meta.findall("contrib-group[@content-type='author']")) else '')!='author':continue
        name=n.find('name')
        if name is not None:authors.append(' '.join(filter(None,[text(name.find('surname')),text(name.find('given-names'))])))
        elif n.find('collab') is not None:authors.append(text(n.find('collab')))
    if not authors:raise ValueError('Missing author attribution')
    year=text(meta.find('pub-date/year')) or text(meta.find('permissions/copyright-year'))
    if not year:raise ValueError('Missing publication year')
    paragraphs=[]
    def collect(node):
        parents={child:parent for parent in node.iter() for child in parent}
        for el in node.iter('p'):
            cursor=el;excluded=False
            while cursor in parents:
                if cursor.tag in ('fig','table-wrap','table','disp-quote','ref-list','supplementary-material','boxed-text','fn-group'):excluded=True;break
                if cursor.tag=='sec' and re.match(r'^(?:results?|methods?|participants?|patients?|case presentation)\b',text(cursor.find('title')),re.I):excluded=True;break
                cursor=parents[cursor]
            if excluded:continue
            # Exclude third-party quotations, tables and patient/case narrative.
            if el.find('.//disp-quote') is not None or el.find('.//table-wrap') is not None:continue
            value=text(el)
            if not value or excluded_paragraph(value) or re.search(r'\b(?:patient [A-Z]\b|case report|case presentation|patient was|patient presented|our patient|written informed consent)',value,re.I):continue
            paragraphs.append(value)
    for node in meta.findall('abstract'):collect(node)
    for sec in root.findall('./body/sec'):
        heading=text(sec.find('title')).lower();kind=sec.get('sec-type','').lower()
        if kind in ('intro','introduction','background') or re.search(r'^(?:\d+[. ]*)?(?:introduction|background|theoretical (?:background|framework)|conceptual (?:background|framework))\b',heading):collect(sec)
    if not paragraphs:raise ValueError('No eligible abstract/introduction/background prose')
    sha=hashlib.sha256(raw).hexdigest();ident='article-'+pmcid.lower();url='https://doi.org/'+doi
    finding='The article XML permissions explicitly links CC BY '+version+'. Only original abstract/introduction/background prose is admitted; figures, tables, quotations, cases, results and references are excluded. Each requested sense still requires packet support.'
    evidence={'policy_url':url,'reviewed_on':'2026-10-18','finding':finding,'licence_confirmed':True,'policy_snapshot_sha256':sha,'permission_notice':text(permissions)}
    evidence['sha256']=digest(evidence)
    source={'id':ident,'candidate':'; '.join(authors)+'. '+title,'url':url,'licence':licence,'licence_source_url':url,'licence_confirmed':True,'pinned_version':year+'; DOI '+doi+'; article XML SHA-256 '+sha,'roles':['draft_basis','supports_definition'],'decision':'yes','reason':finding,'evidence':evidence,'asset_pin_required':True,'content_snapshot_sha256':sha}
    record={'source_id':ident,'record_id':doi,'term':title,'aliases':[],'url':url,'text':'\n\n'.join(paragraphs),'definition_available':True,'snapshot_sha256':sha,'source_kind':'article_original_background','authors':authors,'publication_year':year}
    return source,record

def plan():
    existing=set()
    for path in (ROOT/'data/entries').glob('*.json'):
        try:existing.add(norm(json.loads(path.read_text())['term']))
        except json.JSONDecodeError:continue  # A new draft may still be finishing its write.

    terms={norm(r['term']):r['term'] for r in json.loads((AUDIT/'coverage.json').read_text()) if r['production_scope']=='term' and norm(r['term']) not in existing}
    lookup={}
    for directory in (AUDIT/'article-batches',AUDIT/'article-wide-batches',DEST/'search'):
        for path in directory.glob('*.json'):
            try:cached=json.loads(path.read_text())
            except json.JSONDecodeError:continue
            for p in cached.get('resultList',{}).get('result',[]):
                if p.get('doi') and p.get('pmcid'):lookup[p['doi']]=p
    options=collections.defaultdict(dict)
    for path in (AUDIT/'article-records.json',AUDIT/'article-wide-records.json',DEST/'new-article-records.json'):
        if not path.exists():continue
        try:candidates=json.loads(path.read_text())
        except json.JSONDecodeError:continue
        for r in candidates:
            key=norm(r['term']);paper=lookup.get(r['record_id'])
            if key in terms and paper:
                title=norm(paper.get('title',''));abstract=norm(re.sub(r'<[^>]+>',' ',paper.get('abstractText','')))
                rank=(key not in title,not any(s in title for s in ('review','conceptual','definition','theoretical')),abstract.find(key) if key in abstract else 999999,-int(paper.get('pubYear','0') or 0),paper['doi'])
                options[key][paper['doi']]=(rank,paper)
    selected={}
    for key,items in options.items():
        for rank,paper in sorted(items.values(),key=lambda p:p[0])[:3]:
            row=selected.setdefault(paper['pmcid'],{'pmcid':paper['pmcid'],'doi':paper['doi'],'terms':[]})
            row['terms'].append(terms[key])
    jobs=sorted(selected.values(),key=lambda j:(-len(j['terms']),j['pmcid']))
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'article-plan.json').write_text(json.dumps({'eligible_remaining_terms':len(terms),'terms_with_retrievable_articles':len(options),'article_jobs':jobs,'paid_calls':0},ensure_ascii=False,indent=2)+'\n')
    return jobs

def already_defined(terms):
    global DEFINED_CACHE
    with DEFINED_LOCK:
        checked,known=DEFINED_CACHE
        if time.monotonic()-checked>5:
            try:
                history=json.loads((ROOT/'data/status-history.json').read_text())['entries']
                known={norm(e['term']) for e in history.values()};DEFINED_CACHE=(time.monotonic(),known)
            except json.JSONDecodeError:pass
        return all(norm(term) in known for term in terms)

def fetch(job):
    global LAST
    if already_defined(job['terms']):return {'pmcid':job['pmcid'],'status':'already_defined','reason':'An entry already exists; no fallback article required'}
    path=DEST/'xml'/(job['pmcid']+'.xml');error_path=DEST/'errors'/(job['pmcid']+'.json')
    if error_path.exists():
        if path.exists():
            try:
                source,record=parse_article(path.read_bytes(),job['pmcid'],job['doi'])
                error_path.unlink()
                return {'pmcid':job['pmcid'],'status':'admitted','source':source,'record':record,'terms':job['terms']}
            except (ValueError,ET.ParseError):pass
        return {'pmcid':job['pmcid'],'status':'unavailable','reason':json.loads(error_path.read_text())['reason']}
    try:
        if path.exists():raw=path.read_bytes()
        else:
            for attempt in range(2):
                with LOCK:
                    pause=max(0,.21-(time.monotonic()-LAST))
                    if pause:time.sleep(pause)
                    LAST=time.monotonic()
                try:
                    request=urllib.request.Request('https://www.ebi.ac.uk/europepmc/webservices/rest/'+job['pmcid']+'/fullTextXML',headers={'User-Agent':'PsychTermsSourceRecovery/0.1 (https://github.com/cloudronin/psychterms)'})
                    with urllib.request.urlopen(request,timeout=40) as r:raw=r.read(5_000_001)
                    if len(raw)>5_000_000:raise ValueError('Article exceeds retrieval size limit')
                    path.write_bytes(raw);break
                except Exception:
                    if attempt:raise
        source,record=parse_article(raw,job['pmcid'],job['doi'])
        return {'pmcid':job['pmcid'],'status':'admitted','source':source,'record':record,'terms':job['terms']}
    except Exception as error:
        reason=type(error).__name__+': '+str(error)[:180]
        error_path.write_text(json.dumps({'reason':reason})+'\n')
        return {'pmcid':job['pmcid'],'status':'unavailable','reason':reason}

def run(limit=None):
    jobs=plan()
    if limit:jobs=jobs[:limit]
    for name in ('xml','errors','records'):(DEST/name).mkdir(exist_ok=True)
    outcomes=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for outcome in pool.map(fetch,jobs):
            outcomes.append({k:v for k,v in outcome.items() if k not in ('source','record','terms')})
            if outcome['status']=='admitted':
                path=DEST/'records'/(outcome['pmcid']+'.json');temp=path.with_suffix('.tmp');temp.write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
            if len(outcomes)%25==0 or len(outcomes)==len(jobs):
                report={'completed':len(outcomes),'total':len(jobs),'status_counts':dict(collections.Counter(o['status'] for o in outcomes)),'paid_calls':0}
                (DEST/'retrieval-progress.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    return outcomes

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int);a=p.parse_args();run(a.limit)
