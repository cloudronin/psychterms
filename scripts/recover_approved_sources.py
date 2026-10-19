"""Fetch ONLY Vishnu's three added source families; never imports an OpenMD catalogue."""
import argparse,collections,concurrent.futures,hashlib,html,json,re,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from core import ROOT,digest
from hybrid_redraft import atomic
from source_coverage_audit import norm
DEST=ROOT/'.private/new-approved-sources'
FAMILIES={'medlineplus-health-topics','cdc-mental-health-substance-use','hpo-2026-09-01'}
HPO_VERSION='2026-09-01'
POLICIES={'medlineplus-health-topics':'https://medlineplus.gov/about/using/usingcontent/','cdc-mental-health-substance-use':'https://www.cdc.gov/other/agencymaterials.html','hpo-2026-09-01':'https://human-phenotype-ontology.github.io/license.html'}
CDC_ROOTS={'mental-health','children-mental-health','child-development','adhd','autism','overdose-prevention','alcohol','cannabis','substance-use'}
CDC_SEEDS=['https://www.cdc.gov/mental-health/about/index.html','https://www.cdc.gov/children-mental-health/about/index.html','https://www.cdc.gov/adhd/about/','https://www.cdc.gov/autism/about/index.html','https://www.cdc.gov/overdose-prevention/about/index.html']

def fetch(url,path,max_bytes=4_000_000):
    if path.exists():return path.read_bytes()
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https' or u.hostname not in {'medlineplus.gov','www.cdc.gov','github.com','raw.githubusercontent.com','human-phenotype-ontology.github.io'}:raise ValueError('Outside explicit three-source fetch allowlist')
    if u.hostname=='github.com' and not u.path.startswith('/obophenotype/human-phenotype-ontology/'):raise ValueError('Unapproved GitHub project')
    req=urllib.request.Request(url,headers={'User-Agent':'PsychTermsSourceRecovery/0.2 (https://github.com/cloudronin/psychterms)'})
    with urllib.request.urlopen(req,timeout=45) as response:
        target=urllib.parse.urlsplit(response.geturl()).hostname
        if target not in {u.hostname,'release-assets.githubusercontent.com'}:raise ValueError('Unexpected download host')
        raw=response.read(max_bytes+1)
    if len(raw)>max_bytes:raise ValueError('Source size bound exceeded')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);return raw

class Text(HTMLParser):
    def __init__(self,main=False):super().__init__();self.stack=[];self.parts=[];self.links=[];self.title=[];self.main=main;self.buf=None;self.h1=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag not in {'br','img','input','meta','link','hr','area','wbr','source'}:self.stack.append(tag)
        okay=(not self.main or 'main' in self.stack) and not any(t in self.stack for t in ('script','style','nav','footer','header','aside','table','figure','blockquote'))
        if tag=='h1' and okay:self.h1=True
        if tag in ('p','li') and okay and self.buf is None:self.buf=[]
    def handle_data(self,data):
        if any(t in self.stack for t in ('script','style','nav','footer','header','aside','table','figure','blockquote')):return
        if self.h1:self.title.append(data)
        if self.buf is not None:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=='h1':self.h1=False
        if tag in ('p','li') and self.buf is not None:
            value=' '.join(' '.join(self.buf).split());self.buf=None
            if value:self.parts.append(value)
        if tag in self.stack:
            while self.stack:
                if self.stack.pop()==tag:break

def plain(value):
    p=Text();p.feed(value);return '\n\n'.join(p.parts) or ' '.join(re.sub('<[^>]+>',' ',html.unescape(value)).split())

def in_medline_scope(title,groups):
    return bool({'Mental Health and Behavior','Substance Use and Disorders'} & set(groups) or re.search(r'\b(?:child development|developmental disabilit|developmental delay|intellectual disabilit|learning disabilit|speech and communication disorders)\b',title,re.I))

def medline_records(raw,url):
    root=ET.fromstring(raw);sha=hashlib.sha256(raw).hexdigest();out=[]
    for t in root.findall('health-topic'):
        groups=[g.text or '' for g in t.findall('group')];title=t.attrib['title']
        if t.attrib.get('language')!='English' or not in_medline_scope(title,groups):continue
        # Only the expressly public-domain full-summary. Never site-record/encyclopedia/drug/vendor text.
        summary=t.findtext('full-summary','');text=plain(summary)
        if len(text.split())<8 or re.search(r'©|copyright|all rights reserved|used with permission|reprinted',text,re.I):continue
        aliases=[v.text for tag in ('also-called','see-reference') for v in t.findall(tag) if v.text]
        aliases += [v.text for v in t.findall('mesh-heading/descriptor') if v.text]
        out.append({'source_id':'medlineplus-health-topics','record_id':t.attrib['id'],'term':title,'aliases':sorted(set(aliases)),
            'text':text,'url':t.attrib['url'],'snapshot_sha256':sha,'revision':'MedlinePlus health topic XML '+root.attrib['date-generated'],
            'source_kind':'medlineplus_nlm_owned_health_topic_summary','scope_groups':groups,'definition_available':True})
    return out

def hpo_reference_index(raw):
    nodes={};sha=hashlib.sha256(raw).hexdigest()
    for block in raw.decode().split('\n[Term]\n')[1:]:
        ident=re.search(r'^id: (HP:\d+)$',block,re.M);name=re.search(r'^name: (.+)$',block,re.M)
        if not ident or not name or re.search(r'^is_obsolete: true$',block,re.M):continue
        aliases=[]
        for value in re.findall(r'^synonym: "((?:[^"\\]|\\.)*)" EXACT\b',block,re.M):aliases.append(re.sub(r'\\(.)',r'\1',value))
        nodes[ident.group(1)]={'id':ident.group(1),'term':name.group(1),'aliases':aliases,'parents':re.findall(r'^is_a: (HP:\d+)',block,re.M)}
    # Verified labels in the pinned 2026-09-01 release; traversal is a view, never a rewritten HPO file.
    roots={'HP:0011446':'Abnormality of mental function','HP:0012759':'Neurodevelopmental abnormality'}
    if any(nodes[k]['term']!=v for k,v in roots.items()):raise ValueError('Pinned HPO scope roots changed')
    selected=set(roots)
    while True:
        more={i for i,n in nodes.items() if set(n['parents']) & selected}-selected
        if not more:break
        selected.update(more)
    return {'schema_version':1,'source':'hpo-2026-09-01','version':HPO_VERSION,'snapshot_sha256':sha,'roots':roots,
       'reference_only':True,'original_file_unchanged':True,'records':[nodes[i] for i in sorted(selected)]}

def cdc_url(url):
    p=urllib.parse.urlsplit(url)
    return p.scheme=='https' and p.hostname=='www.cdc.gov' and p.path.strip('/').split('/')[0] in CDC_ROOTS and not re.search(r'\.(?:pdf|jpg|png|js|css|xml)$',p.path,re.I) and '/es/' not in p.path and '/data/' not in p.path

def cdc_record(url,raw):
    if re.search(r'©|all rights reserved|reprinted.{0,30}permission|copyright\s*(?:&copy;|\d{4})',raw.decode('utf-8'),re.I):raise ValueError('Page-level third-party rights notice requires manual review')
    p=Text(main=True);p.feed(raw.decode('utf-8'));title=' '.join(' '.join(p.title).split())
    parts=[v for v in p.parts if len(v.split())>=8 and not re.search(r'©|copyright|all rights reserved|reprinted|used with permission|World Health Organization|realize our abilities, learn well and work well|^Source:|^References?\b',v,re.I)]
    text='\n\n'.join(parts)
    if not title or len(text.split())<30:raise ValueError('No substantive CDC own-text content')
    sha=hashlib.sha256(raw).hexdigest()
    return {'source_id':'cdc-mental-health-substance-use','record_id':url,'term':title,'aliases':[],'url':url,'text':text,
        'snapshot_sha256':sha,'revision':'CDC HTML snapshot 2026-10-19; SHA-256 '+sha,'source_kind':'cdc_original_mental_health_substance_use_page','definition_available':True},p.links

def family(ident,title,url,licence,roles,policy_sha,version,reason,**extra):
    evidence={'policy_url':POLICIES[ident],'reviewed_on':'2026-10-19','policy_snapshot_sha256':policy_sha,'licence_confirmed':True,'finding':reason}
    evidence['sha256']=digest(evidence)
    return {'id':ident,'candidate':title,'url':url,'licence':licence,'licence_source_url':POLICIES[ident],'licence_confirmed':True,
      'pinned_version':version,'roles':roles,'decision':'yes','reason':reason,'evidence':evidence,'asset_pin_required':True,**extra}

def run(cdc_limit=65):
    DEST.mkdir(exist_ok=True);inventory=ROOT/'data/sources.json'
    if not (DEST/'prior-sources.json').exists():(DEST/'prior-sources.json').write_bytes(inventory.read_bytes())
    policies={}
    for ident,url in POLICIES.items():policies[ident]=fetch(url,DEST/(ident+'-policy.html'))
    licence_raw=fetch('https://raw.githubusercontent.com/Human-Phenotype-Ontology/Human-Phenotype-Ontology.github.io/master/license.md',DEST/'hpo-licence-original.md')
    public=ROOT/'data/source-licences';public.mkdir(exist_ok=True);(public/'hpo-licence-original.md').write_bytes(licence_raw)
    # Both originals are retained byte for byte with SHA-256, source URL and dated version.
    hpo_raw=fetch('https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/hp.obo',DEST/'hp-v2026-09-01.obo',20_000_000)
    hpo=hpo_reference_index(hpo_raw);atomic(DEST/'hpo-reference-index.json',hpo)
    index=fetch('https://medlineplus.gov/xml.html',DEST/'medlineplus-xml-index.html')
    urls=re.findall(r'https://medlineplus.gov/xml/mplus_topics_\d{4}-\d{2}-\d{2}\.xml',index.decode())
    xml_url=max(urls);xml_path=DEST/xml_url.rsplit('/',1)[1];xml=fetch(xml_url,xml_path,40_000_000)
    records=medline_records(xml,xml_url);visited=set();queue=set(CDC_SEEDS);cdc_outcomes=[]
    while queue and len(visited)<cdc_limit:
        batch=sorted(queue-visited)[:min(6,cdc_limit-len(visited))]
        if not batch:break
        queue.difference_update(batch)
        def one(url):
            try:
                raw=fetch(url,DEST/('cdc-'+hashlib.sha256(url.encode()).hexdigest()[:16]+'.html'))
                record,links=cdc_record(url,raw);return record,links,None
            except Exception as e:return None,[],type(e).__name__+': '+str(e)[:160]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for url,(record,links,error) in zip(batch,pool.map(one,batch)):
                visited.add(url);cdc_outcomes.append({'url':url,'status':'admitted' if record else 'not_admitted','reason':error})
                if record:records.append(record)
                for link in links:
                    target=urllib.parse.urljoin(url,html.unescape(link)).split('#')[0].split('?')[0]
                    if cdc_url(target) and target not in visited:queue.add(target)
        print(json.dumps({'cdc_pages_processed':len(visited),'admitted_records':len(records)}),flush=True)
    record_dir=ROOT/'.private/source-recovery/records';record_dir.mkdir(exist_ok=True)
    manifest={'checked_on':'2026-10-19','allowed_new_families':sorted(FAMILIES),'scope':['mental health','development','substance use','behavioural phenotype'],
       'medline_xml':{'url':xml_url,'sha256':hashlib.sha256(xml).hexdigest()},'hpo':{'url':'https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/hp.obo','sha256':hashlib.sha256(hpo_raw).hexdigest(),'version':HPO_VERSION,'licence_text_sha256':hashlib.sha256(licence_raw).hexdigest(),'licence_text_path':'data/source-licences/hpo-licence-original.md','drafting_allowed':False,'roles':['aliases','links','related_topic']},
       'records':[{'source':r['source_id'],'record_id':r['record_id'],'sha256':r['snapshot_sha256']} for r in records],
       'cdc_outcomes':cdc_outcomes,'hpo_scoped_reference_records':len(hpo['records']),'other_openmd_sources_admitted':0}
    manifest_sha=digest(manifest)
    sources=[family('medlineplus-health-topics','MedlinePlus, National Library of Medicine: own health-topic summaries','https://medlineplus.gov/healthtopics.html','public-domain-US-government',['draft_basis','supports_definition'],hashlib.sha256(policies['medlineplus-health-topics']).hexdigest(),'Daily XML snapshot '+xml_url.rsplit('/',1)[1]+'; scoped manifest '+manifest_sha,'NLM own full-summary text only, scoped to mental health, development, substance use and behaviour. Exclude licensed encyclopedia, drug monographs, images and external linked text.',attribution='Source: MedlinePlus, National Library of Medicine.'),
      family('cdc-mental-health-substance-use','Centers for Disease Control and Prevention: own mental-health, developmental and substance-use pages','https://www.cdc.gov/mental-health/about/index.html','public-domain-US-government',['draft_basis','supports_definition'],hashlib.sha256(policies['cdc-mental-health-substance-use']).hexdigest(),'HTML snapshots 2026-10-19; scoped manifest '+manifest_sha,'CDC own unmarked prose only within the named scope. Exclude licensed, contractor, grantee and third-party material, logos, images, tables and direct quotations. Preserve substantive meaning; source is available free from CDC.',attribution='Source: CDC. This use does not imply endorsement by CDC, HHS or the United States Government. Original material is available without charge at the source URL.'),
      family('hpo-2026-09-01','Human Phenotype Ontology Consortium: scoped mental-function and neurodevelopment reference','https://github.com/obophenotype/human-phenotype-ontology/releases/tag/v2026-09-01','HPO-attribution-integrity',['aliases','links','related_topic'],hashlib.sha256(policies['hpo-2026-09-01']).hexdigest(),'HPO release 2026-09-01; original OBO SHA-256 '+hashlib.sha256(hpo_raw).hexdigest(),'User-permitted versioned reference. Official terms require acknowledgement, citation, version display and unchanged HPO files/relationships. Preserve original bytes and relationships; labels/EXACT aliases and links only. HPO prose is not a CC BY drafting packet.',licence_text_path='data/source-licences/hpo-licence-original.md',licence_text_sha256=hashlib.sha256(licence_raw).hexdigest(),attribution='This service uses the Human Phenotype Ontology (version 2026-09-01). Human Phenotype Ontology Consortium. See https://human-phenotype-ontology.github.io/license.html.')]
    document=json.loads(inventory.read_text());current={s['id']:s for s in document['sources']}
    for s in sources:current[s['id']]=s
    document['sources']=list(current.values());document['checked_on']='2026-10-19';atomic(inventory,document)
    for r in records:
        target=record_dir/(r['source_id']+'-'+hashlib.sha256(r['record_id'].encode()).hexdigest()[:16]+'.json')
        atomic(target,{'status':'admitted','record':r,'source_family':r['source_id'],'permission_manifest_hash':manifest_sha})
    atomic(DEST/'records.json',records);atomic(DEST/'manifest.json',manifest)
    atomic(ROOT/'reports/approved-source-expansion.json',{'manifest_hash':manifest_sha,'families_added':sorted(FAMILIES),'drafting_records_by_family':dict(collections.Counter(r['source_id'] for r in records)),'hpo_reference_records':len(hpo['records']),'hpo_drafting_records':0,'licence_text':manifest['hpo']['licence_text_path'],'other_openmd_sources_admitted':0})
    print(json.dumps({'records':len(records),'hpo_reference_records':len(hpo['records']),'families':sorted(FAMILIES),'manifest_hash':manifest_sha}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cdc-limit',type=int,default=65);a=p.parse_args();run(a.cdc_limit)
