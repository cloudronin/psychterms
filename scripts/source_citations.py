"""Citations are derived from the pinned source packet, never invented by a writer."""
import json
from core import ROOT
from check_packets import validate_packet
ROLE_LABELS={'draft_basis':'Drafting source','supports_definition':'Supporting source','related_topic':'Background reference only'}
def packet_citation(packet,sources,role='draft_basis'):
 validate_packet(packet,sources)
 source=sources[packet['source']]
 if role not in ROLE_LABELS:raise ValueError('Unknown citation role')
 if packet['source']=='mesh-2026':
  citation=f'U.S. National Library of Medicine. Medical Subject Headings (MeSH), {packet["revision"]}. “{packet["term"]}” ({packet["source_record"]}).'
 else:
  citation=f'{source["candidate"]}. {packet["revision"]}. “{packet["term"]}” ({packet["source_record"]}).'
 return {'source':packet['source'],'record_id':packet['source_record'],'revision':packet['revision'],'role':role,'role_label':ROLE_LABELS[role],
         'citation':citation,'url':packet['url'],'licence':packet['licence'],'packet_hash':packet['packet_hash'],'source_snapshot_sha256':packet['source_snapshot_sha256']}

def references(entries,root=ROOT):
 sources={s['id']:s for s in json.loads((root/'data/sources.json').read_text())['sources']}
 result={}
 for entry in entries:
  packet=json.loads((root/'data/packets'/(entry['id']+'.json')).read_text())
  if packet['packet_hash']!=entry['packet_hash']:raise ValueError('Citation packet does not match entry')
  rows=[]
  for p in entry['provenance']:
   if p['source']==packet['source']:
    if p['revision']!=packet['revision']:raise ValueError('Citation revision does not match packet')
    rows.append(packet_citation(packet,sources,p['role']))
   else:
    source=sources[p['source']]
    rows.append({'source':p['source'],'revision':p['revision'],'role':p['role'],'role_label':ROLE_LABELS[p['role']],
                 'citation':f'{source["candidate"]}. {p["revision"]}. {p["scope"]}.','url':p.get('locator',source['url']),'licence':source['licence']})
  result[entry['id']]=rows
 return result
