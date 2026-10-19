"""Recover NIMH-owned publication prose under the already verified own-text policy."""
import hashlib,json,re,time,urllib.parse,urllib.request
from html.parser import HTMLParser
from pathlib import Path
from core import ROOT,digest
from source_coverage_audit import norm
from recover_article_sources import excluded_paragraph

DEST=ROOT/'.private/source-recovery/government'
POLICY='https://www.nimh.nih.gov/site-info/policies'

class Page(HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.paragraph=None;self.parts=[];self.title_parts=[];self.title=False;self.links=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=='a' and 'href' in values:self.links.append(values['href'])
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append(tag)
        in_main='main' in self.stack and not any(t in self.stack for t in ('script','style','nav','aside','footer','header','figure','table','blockquote'))
        if tag=='h1' and in_main:self.title=True
        if tag=='p' and in_main:self.paragraph=[]
    def handle_endtag(self,tag):
        if tag=='h1':self.title=False
        if tag=='p' and self.paragraph is not None:
            value=' '.join(' '.join(self.paragraph).split());self.paragraph=None
            if value and not excluded_paragraph(value) and not re.search(r'^(?:[“"‘\']?I (?:feel|thought|was|am|have|had)|[“"‘\']?My (?:name|life|anxiety|symptoms))\b',value):self.parts.append(value)
        if tag in self.stack:
            while self.stack:
                if self.stack.pop()==tag:break
    def handle_data(self,value):
        if any(t in self.stack for t in ('script','style','nav','aside','footer','header','figure','table','blockquote')):return
        if self.title:self.title_parts.append(value)
        if self.paragraph is not None:self.paragraph.append(value)

def parse_page(raw):
    page=Page();page.feed(raw.decode('utf-8'));title=' '.join(' '.join(page.title_parts).split())
    if not title or len(page.parts)<2:raise ValueError('No substantive NIMH main-content paragraphs')
    content='\n\n'.join(page.parts)
    if re.search(r'©|all rights reserved|reprinted (?:with|by) permission|used with permission',content,re.I):raise ValueError('Page-specific third-party notice requires manual exclusion review')
    return title,content,page.links

def fetch(url,path):
    if path.exists():raw=path.read_bytes()
    else:
        request=urllib.request.Request(url,headers={'User-Agent':'PsychTermsSourceRecovery/0.1 (https://github.com/cloudronin/psychterms)'})
        with urllib.request.urlopen(request,timeout=35) as response:raw=response.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError('Page exceeds retrieval limit')
        if b'recaptcha' in raw.lower():raise ValueError('Access challenge; source not retrieved')
        path.write_bytes(raw)
    return raw

def run():
    DEST.mkdir(exist_ok=True);records=DEST/'records';records.mkdir(exist_ok=True)
    sources=json.loads((ROOT/'data/sources.json').read_text())['sources'];family=next(s for s in sources if s['id']=='nimh')
    assert family['decision']=='yes' and family['licence_confirmed'] and 'draft_basis' in family['roles']
    index_url='https://www.nimh.nih.gov/health/publications';raw=fetch(index_url,DEST/'nimh-publications-index.html');index=Page();index.feed(raw.decode())
    def publication_urls(links,base=index_url):
        found=set()
        for link in links:
            url=urllib.parse.urljoin(base,link).split('#')[0].split('?')[0];parts=urllib.parse.urlsplit(url)
            if parts.netloc in ('www.nimh.nih.gov','nimh.nih.gov') and parts.path.startswith('/health/publications/') and not any(s in parts.path.lower() for s in ('.pdf','/espanol')):found.add(url)
        return found
    urls=publication_urls(index.links)
    for url in sorted(urls):
        if not url.rstrip('/').endswith('-listing'):continue
        ident='nimh-page-'+hashlib.sha256(url.encode()).hexdigest()[:16]
        try:
            page=Page();page.feed(fetch(url,DEST/(ident+'.html')).decode());urls.update(publication_urls(page.links,url))
        except Exception:continue
    urls.update(['https://www.nimh.nih.gov/health/publications/panic-disorder-when-fear-overwhelms','https://www.nimh.nih.gov/health/publications/bipolar-disorder','https://www.nimh.nih.gov/health/publications/depression','https://www.nimh.nih.gov/health/publications/obsessive-compulsive-disorder-when-unwanted-thoughts-or-repetitive-behaviors-take-over'])
    urls=sorted(urls)
    rows=json.loads((ROOT/'.private/coverage-audit/coverage.json').read_text());existing=set()
    for path in (ROOT/'data/entries').glob('*.json'):
        try:existing.add(norm(json.loads(path.read_text())['term']))
        except json.JSONDecodeError:continue
    terms={r['term'] for r in rows if r['production_scope']=='term' and norm(r['term']) not in existing}
    outcomes=[]
    for position,url in enumerate(urls,1):
        ident='nimh-page-'+hashlib.sha256(url.encode()).hexdigest()[:16];path=DEST/(ident+'.html')
        try:
            if not path.exists():time.sleep(1)
            raw=fetch(url,path);title,content,_=parse_page(raw);sha=hashlib.sha256(raw).hexdigest();normalized=' '+norm(content)+' '
            matches=sorted(term for term in terms if ' '+norm(term)+' ' in normalized)
            reason='Original NIMH-owned publication prose under the verified own-text public-domain policy; images, tables, quotations, external material and identifiable cases excluded. Every requested sense still needs packet support.'
            evidence={'policy_url':POLICY,'reviewed_on':'2026-10-18','finding':reason,'licence_confirmed':True,'policy_snapshot_sha256':family['evidence']['policy_snapshot_sha256']};evidence['sha256']=digest(evidence)
            source={'id':ident,'candidate':'National Institute of Mental Health. '+title,'url':url,'licence':'public-domain-US-government','licence_source_url':POLICY,'licence_confirmed':True,'pinned_version':'HTML publication snapshot 2026-10-18; SHA-256 '+sha,'roles':['draft_basis','supports_definition'],'decision':'yes','reason':reason,'evidence':evidence,'asset_pin_required':True,'content_snapshot_sha256':sha}
            record={'source_id':ident,'record_id':url,'term':title,'aliases':[],'url':url,'text':content,'definition_available':True,'snapshot_sha256':sha,'source_kind':'government_original_publication'}
            row={'status':'admitted','source':source,'record':record,'terms':matches,'asset_filename':path.name};target=records/(ident+'.json');temp=target.with_suffix('.tmp');temp.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');temp.replace(target)
            outcomes.append({'url':url,'status':'admitted','remaining_label_matches':len(matches)})
        except Exception as error:outcomes.append({'url':url,'status':'not_admitted','reason':str(error)[:180]})
        report={'completed':position,'total':len(urls),'admitted':sum(o['status']=='admitted' for o in outcomes),'paid_calls':0,'outcomes':outcomes};(DEST/'nimh-progress.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='outcomes'}),flush=True)
if __name__=='__main__':run()
