"""Deterministic exports. Preview content is never a release artifact."""
import argparse,json,shutil
from risk_registry import prepare
from source_citations import references
from core import ROOT,canonical,digest,load_inputs,validate_corpus

def build(entries,release=False):
 entries,risk_pin=prepare(entries)
 ordered=sorted(entries,key=lambda e:e['id'])
 refs=references(ordered)
 mode='release' if release else 'preview'
 dictionary={'schema_version':1,'release_version':'0.0.0-preview' if not release else '1.0.0','status':mode,'risk_register':risk_pin,'entries':ordered,'references':refs}
 md=['# PsychTerms', '', 'Public review preview; human review pending, not a finished dictionary release.' if not release else 'PsychTerms, by Vishnu Vettrivel, CC BY 4.0.', '']
 for e in ordered:
  md.extend([f'## {e["term"]}',f'<a id="{e["id"]}"></a>','',e['definition'],'',f'Status: {"Candidate · not yet reviewed" if e["review_status"]=="candidate" else e["review_status"]}',f'Field: {e["field"]}',f'Version: {e["version"]} · SHA-256: {e["hash"]}',''])
  if e.get('editorial_note'):md.extend(['Wording review pending: '+e['editorial_note'], ''])
  md.extend(['Sources:', *[f'- {r["role_label"]}: [{r["citation"]}]({r["url"]})' for r in refs[e['id']]], ''])
  if e.get('risk'):md.extend(['No scene is provided for this risk term.', ''])
 return dictionary,'\n'.join(md),{'schema_version':1,'status':mode,'entry_count':len(ordered),'corpus_hash':digest(ordered),'data_hash':digest(dictionary),'risk_register':risk_pin}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args()
 entries,sources,fields=load_inputs()
 validate_corpus(entries,sources,fields,release=False)
 data,md,manifest=build(entries,release=not a.preview)
 validate_corpus(data['entries'],sources,fields,release=not a.preview)
 for dest in (ROOT/'dist-data',ROOT/'site/public/downloads'):
  dest.mkdir(parents=True,exist_ok=True)
  (dest/'risk_terms.json').write_bytes((ROOT/'data/risk_terms.json').read_bytes())
  (dest/'dictionary.json').write_bytes(canonical(data)+b'\n')
  (dest/'dictionary.md').write_text(md)
  (dest/'manifest.json').write_bytes(canonical(manifest)+b'\n')
 print(json.dumps(manifest,indent=2))
