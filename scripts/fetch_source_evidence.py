"""Download fixed, public source URLs; no model calls or credentials."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
URLS={
 'mesh-d2026.bin':'https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/mesh_browser/d2026.bin',
 'mesh-policy.html':'https://www.nlm.nih.gov/databases/download/terms_and_conditions_mesh.html',
 'nimh-policy.html':'https://www.nimh.nih.gov/site-info/policies',
 'ncit-policy.html':'https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/ThesaurusTermsofUse.htm',
 'nhs-policy.html':'https://www.nhs.uk/our-policies/terms-and-conditions/',
 'aihw-policy.html':'https://www.aihw.gov.au/copyright',
 'wikidata-policy.html':'https://www.wikidata.org/wiki/Wikidata:Copyright',
}
def fetch(pair):
 name,url=pair;dest=ROOT/'.private/source-snapshots'/name;dest.parent.mkdir(parents=True,exist_ok=True)
 result=subprocess.run(['curl','--fail','--silent','--show-error','--location','--max-time','45','--max-filesize','50000000',url,'--output',str(dest)],capture_output=True,text=True)
 if result.returncode:return {'file':name,'url':url,'status':'failed','error':result.stderr.strip()[:180]}
 return {'file':name,'url':url,'status':'downloaded','sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,'retrieved_on':'2026-10-18'}
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(fetch,URLS.items()))
 (ROOT/'reports/source-snapshots.json').write_text(json.dumps({'snapshots':rows},indent=2)+'\n')
 print(json.dumps(rows,indent=2))
