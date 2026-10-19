"""Publish article-by-article rights decisions, without the private audit's headwords."""
import csv,hashlib,json,re,xml.etree.ElementTree as ET
from core import ROOT
from recover_article_sources import parse_article

DEST=ROOT/'.private/source-recovery'

def build():
    plan=json.loads((DEST/'article-plan.json').read_text());rows=[]
    for job in plan['article_jobs']:
        path=DEST/'xml'/(job['pmcid']+'.xml');url='https://doi.org/'+job['doi']
        row={'id':'article-'+job['pmcid'].lower(),'candidate':job['doi'],'licence':'unconfirmed','licence_source_url':url,'licence_confirmed':False,'pinned_version':'Not retrieved or verified','roles':'','decision':'no','reason':'Awaiting article-specific permission and content checks'}
        if path.exists():
            raw=path.read_bytes();row['pinned_version']='Article XML SHA-256 '+hashlib.sha256(raw).hexdigest()
            try:
                source,_=parse_article(raw,job['pmcid'],job['doi'])
                row={key:source.get(key,'') for key in row};row['roles']='; '.join(source['roles'])
            except Exception as error:
                row['reason']=str(error)
                try:
                    meta=ET.fromstring(raw).find('./front/article-meta/permissions')
                    notice=ET.tostring(meta,encoding='unicode') if meta is not None else ''
                    versions=re.findall(r'https?://(?:www\.)?creativecommons\.org/licenses/by/(2\.0|2\.5|3\.0|4\.0)/?(?=[\s"<>&)])',notice)
                    if versions and not re.search(r'creativecommons\.org/licenses/by-(?:nc|nd|sa)',notice):row.update(licence='CC-BY-'+versions[0],licence_confirmed=True)
                except ET.ParseError:pass
        rows.append(row)
    fields=['id','candidate','licence','licence_source_url','licence_confirmed','pinned_version','roles','decision','reason']
    with (ROOT/'reports/source-recovery-inventory.csv').open('w',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    return {'candidate_articles':len(rows),'admitted':sum(r['decision']=='yes' for r in rows),'not_admitted_or_pending':sum(r['decision']=='no' for r in rows)}

if __name__=='__main__':print(json.dumps(build(),indent=2))
