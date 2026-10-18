"""Build independent candidates from a freshly downloaded permitted MeSH edition."""
import collections,hashlib,json,re
from core import ROOT,digest,semantic_hash

def parse_mesh(text):
 records=[]
 for block in text.split('*NEWRECORD'):
  fields=collections.defaultdict(list)
  for line in block.splitlines():
   if ' = ' in line:
    k,v=line.split(' = ',1);fields[k].append(v)
  if not fields['UI'] or not fields['MH']:continue
  ident=fields['UI'][0];term=fields['MH'][0]
  records.append({'source_id':'mesh-2026','record_id':ident,'term':term,'scope_note':' '.join(fields['MS']),'tree_numbers':fields['MN'],'aliases':sorted({a.split('|')[0] for a in fields['ENTRY']+fields['PRINT ENTRY'] if 'EQV' in a.split('|') and ',' not in a.split('|')[0]}-{term}), 'url':'https://meshb.nlm.nih.gov/record/ui?ui='+ident})
 return records

def relevant(record):return any(re.match(r'^F0[1-4](?:\.|$)',n) for n in record['tree_numbers'])

if __name__=='__main__':
 source=ROOT/'.private/source-snapshots/mesh-d2026.bin'
 raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest();records=parse_mesh(raw.decode())
 eligible=[dict(r,source_revision='2026',source_snapshot_sha256=sha,classification_status='needs_field_review',eligibility='psychology-tree-candidate-not-release') for r in records if relevant(r) and r['scope_note']]
 payload={'schema_version':1,'origin':'MeSH 2026 F01–F04 tree branches; no legacy term list accessed','source_snapshot_sha256':sha,'count_target':None,'candidates':eligible}
 (ROOT/'data/term-candidates.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 report={'source_records':len(records),'psychology_tree_candidates':len(eligible),'released_entries':0,'classification':'Provisional independent candidates, not accepted dictionary entries','count_target':None,'paid_calls':0}
 (ROOT/'reports/independent-term-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
 byid={r['record_id']:r for r in records}
 examples=[('D001288','attention','cognition','Directing your mental focus toward some parts of an experience while leaving others in the background.'),('D008568','memory','cognition','The ability to keep information from an experience and bring it back later.'),('D011613','psychotherapy','counselling skills','The use of verbal or nonverbal communication to address mental illness or emotional difficulties.')]
 ids=[x[1] for x in examples]
 for record_id,ident,field,definition in examples:
  src=byid[record_id]
  packet={'id':ident,'source':'mesh-2026','source_record':record_id,'revision':'2026','source_snapshot_sha256':sha,'url':src['url'],'text':src['scope_note'],'licence':'public-domain-US-government','term':src['term'],'roles':['term_list','draft_basis','supports_definition'],'status':'preview_source_packet'}
  packet['packet_hash']=digest(packet)
  (ROOT/'data/packets'/f'{ident}.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
  entry={'id':ident,'term':src['term'],'definition':definition,'also_see':[i for i in ids if i!=ident],'field':field,'aliases':src['aliases'],'sources':['mesh-2026'],'provenance':[{'role':'draft_basis','source':'mesh-2026','revision':'2026','scope':'MeSH '+record_id+' scope note; preview only','locator':src['url']}],'version':1,'review_status':'preview_fixture','packet_hash':packet['packet_hash']}
  entry['hash']=semantic_hash(entry)
  (ROOT/'data/entries'/f'{ident}.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 for ident,_,_,_ in examples:
  print(json.dumps({k:byid[ident][k] for k in ('record_id','term','scope_note')},ensure_ascii=False))
