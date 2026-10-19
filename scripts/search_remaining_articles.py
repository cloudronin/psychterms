"""Anonymous, cached bibliographic discovery for remaining private headwords.

A discovery match is never admitted text or a supported citation. No model calls.
"""
import collections,concurrent.futures,hashlib,json,re,threading,time,urllib.parse,urllib.request
from pathlib import Path
from core import ROOT
from source_coverage_audit import norm

DEST=ROOT/'.private/source-recovery';AUDIT=ROOT/'.private/coverage-audit'
LOCK=threading.Lock();LAST=0.0

def run():
    global LAST
    known={norm(e['term']) for e in (json.loads(p.read_text()) for p in (ROOT/'data/entries').glob('*.json'))}
    discovered={norm(r['term']) for filename in ('article-records.json','article-wide-records.json') for r in json.loads((AUDIT/filename).read_text())}
    terms=sorted({r['term'] for r in json.loads((AUDIT/'coverage.json').read_text()) if r['production_scope']=='term' and norm(r['term']) not in known and norm(r['term']) not in discovered},key=lambda t:(-len(t.split()),t))
    batches=[terms[i:i+10] for i in range(0,len(terms),10)];cache=DEST/'search';cache.mkdir(exist_ok=True)
    journals='(ISSN:1932-6203 OR ISSN:1664-1078 OR ISSN:1664-0640 OR ISSN:1662-5161 OR ISSN:1471-244X OR ISSN:1471-2202 OR ISSN:1471-2288 OR ISSN:2050-7283 OR ISSN:1744-9081)'
    def fetch(pair):
        global LAST
        index,batch=pair
        query='('+ ' OR '.join('TITLE_ABS:'+json.dumps(t,ensure_ascii=False) for t in batch)+') AND OPEN_ACCESS:Y AND '+journals
        url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':query,'format':'json','pageSize':100,'resultType':'core'})
        path=cache/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        try:
            if path.exists():result=json.loads(path.read_text())
            else:
                with LOCK:
                    pause=max(0,.8-(time.monotonic()-LAST))
                    if pause:time.sleep(pause)
                    LAST=time.monotonic()
                req=urllib.request.Request(url,headers={'User-Agent':'PsychTermsSourceDiscovery/0.1 (https://github.com/cloudronin/psychterms)'})
                with urllib.request.urlopen(req,timeout=45) as response:result=json.load(response)
                if 'resultList' not in result:raise ValueError('Missing bibliographic results')
                path.write_text(json.dumps(result,ensure_ascii=False)+'\n')
            sha=hashlib.sha256(path.read_bytes()).hexdigest();rows=[]
            for paper in result['resultList'].get('result',[]):
                licence=paper.get('license','').lower().replace('-',' ')
                if not licence.startswith('cc by') or any(x in licence.split() for x in ('nc','nd','sa')):continue
                doi=paper.get('doi','');pmcid=paper.get('pmcid')
                if not doi or not pmcid:continue
                name=paper.get('journalInfo',{}).get('journal',{}).get('title','').lower()
                source='plos' if doi.startswith('10.1371/') else 'frontiers' if doi.startswith('10.3389/') else 'bmc' if doi.startswith('10.1186/') else None
                if not source:continue
                content=' '+norm(paper.get('title','')+' '+re.sub(r'<[^>]+>',' ',paper.get('abstractText','')))+' '
                for term in batch:
                    if ' '+norm(term)+' ' not in content:continue
                    rows.append({'term':term,'source':source,'record_id':doi,'pmcid':pmcid,'source_term':paper.get('title',''),'url':'https://doi.org/'+doi,'authors':paper.get('authorString',''),'publication_date':paper.get('firstPublicationDate',paper.get('pubYear','')),'definition_available':False,'source_kind':'open_article_reference_candidate','licence_observed_in_article_metadata':paper['license'],'meaning_verified':False,'snapshot_sha256':sha})
            return index,rows,None,result.get('hitCount',0)>100
        except Exception as error:return index,[],str(error)[:150],False
    rows=[];errors=[];truncated=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(fetch,pair) for pair in enumerate(batches)]
        for done,future in enumerate(concurrent.futures.as_completed(futures),1):
            index,found,error,limited=future.result();rows.extend(found)
            if error:errors.append({'batch':index,'error':error})
            if limited:truncated.append(index)
            if done%25==0 or done==len(batches):
                report={'terms_queried':len(terms),'completed_batches':done,'total_batches':len(batches),'candidate_terms':len({r['term'] for r in rows}),'article_candidates':len(rows),'failed_batches':errors,'truncated_batches':truncated,'paid_calls':0}
                (DEST/'new-article-records.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
                (DEST/'search-progress.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('failed_batches','truncated_batches')},ensure_ascii=False),flush=True)
if __name__=='__main__':run()
