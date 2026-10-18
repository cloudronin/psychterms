"""Deterministic exports. Preview content is never a release artifact."""
import argparse,json,shutil
from risk_registry import prepare
from source_citations import references
from entry_status import prepare as prepare_status,release_note,BADGES
from core import ROOT,canonical,digest,load_inputs,validate_corpus

def build(entries,release=False,history=None):
 entries,risk_pin=prepare(entries)
 entries,status_report=prepare_status(entries,history=history)
 dropped=[{'id':e['id'],'term':e['term'],'status':'dropped','reason':e['drop_reason']} for e in entries if e['status']=='dropped']
 ordered=sorted((e for e in entries if e['status']!='dropped'),key=lambda e:e['id'])
 refs=references(ordered)
 release_version='0.0.0-preview'
 if release:
  versions=json.loads((ROOT/'data/numbered-releases.json').read_text())['releases']
  if not versions:raise ValueError('No numbered release is registered')
  release_version=versions[-1]['version']
  ordered=[e for e in ordered if release_version in e['release_versions']]
  if not ordered:raise ValueError('Numbered release has no matching current entry snapshots')
  refs=references(ordered)
  status_report={**status_report,'status_counts':{**{status:sum(e['status']==status for e in ordered) for status in ('candidate','reviewed','judged')},'dropped':len(dropped),'released':sum(e['released'] for e in ordered)}}
 mode='release' if release else 'preview'
 dictionary={'schema_version':1,'release_version':release_version,'status':mode,'risk_register':risk_pin,'entries':ordered,'references':refs,'dropped':dropped,'status_counts':status_report['status_counts'],'reader_models':status_report['reader_models']}
 md=['# PsychTerms', '', 'Public review preview; human review pending, not a finished dictionary release.' if not release else 'PsychTerms, by Vishnu Vettrivel, CC BY 4.0.', '']
 for e in ordered:
  md.extend([f'## {e["term"]}',f'<a id="{e["id"]}"></a>','',e['definition'],'',f'Status: {BADGES[e["status"]]}',f'Field: {e["field"]}',f'Version: {e["version"]} · SHA-256: {e["hash"]}',''])
  if e.get('editorial_note'):md.extend(['Wording review pending: '+e['editorial_note'], ''])
  md.extend(['Sources:', *[f'- {r["role_label"]}: [{r["citation"]}]({r["url"]})' for r in refs[e['id']]], ''])
  if e.get('risk'):md.extend(['No scene is provided for this risk term.', ''])
 md.extend(['## Dropped entries','',*[f'- {e["term"]}: {e["reason"]}' for e in dropped],''])
 return dictionary,'\n'.join(md),{'schema_version':1,'status':mode,'entry_count':len(ordered),'corpus_hash':digest(ordered),'data_hash':digest(dictionary),'risk_register':risk_pin,'status_counts':status_report['status_counts'],'release_note':release_note(status_report,release_version if release else 'Public review preview')}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');a=p.parse_args()
 entries,sources,fields=load_inputs()
 validate_corpus(entries,sources,fields,release=False)
 data,md,manifest=build(entries,release=not a.preview)
 validate_corpus(data['entries'],sources,fields,release=not a.preview,built=True)
 for dest in (ROOT/'dist-data',ROOT/'site/public/downloads'):
  dest.mkdir(parents=True,exist_ok=True)
  (dest/'risk_terms.json').write_bytes((ROOT/'data/risk_terms.json').read_bytes())
  (dest/'dictionary.json').write_bytes(canonical(data)+b'\n')
  (dest/'dictionary.md').write_text(md)
  (dest/'manifest.json').write_bytes(canonical({k:v for k,v in manifest.items() if k!='release_note'})+b'\n')
  (dest/'release-note.md').write_text(manifest['release_note'])
 (ROOT/'reports/release-note.md').write_text(manifest['release_note'])
 print(json.dumps({k:v for k,v in manifest.items() if k!='release_note'},indent=2))
