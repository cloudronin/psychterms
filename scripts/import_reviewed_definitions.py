"""Offline import of explicitly authorized model-reviewed pilot definitions; no scene/cache export."""
import hashlib,json
from core import ROOT,digest,semantic_hash,slug
from source_citations import packet_citation
from risk_registry import load_registry,matches,required_tests
JUDGE='gpt-5.4-mini-2026-03-17'

def import_rows():
 rows=json.loads((ROOT/'.private/pilot/recovered-results.json').read_text())
 packets={p['id']:p for p in json.loads((ROOT/'.private/pilot/packets.json').read_text())}
 sources={s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text())['sources']}
 manifest=json.loads((ROOT/'data/pilot-preregistration.json').read_text())
 triage=json.loads((ROOT/'reports/definition-overlap-triage.json').read_text())
 held={r['term_id']:r['reason'] for r in triage['triage'] if r['action']=='hold_for_wording_revision'}
 blocked=set(triage['summary']['min_15_hit_ids']);added=[];excluded=[]
 registry,pin=load_registry();new_risk=[]
 for row in rows:
  judges=[j for j in row['judges'] if j and j['model']==JUDGE and j['parsed']['passed'] is True]
  if not judges or row['id'] in blocked:
   excluded.append({'source_record':row['id'],'term':row['term'],'reason':'15-word overlap' if row['id'] in blocked else 'Designated mini judge did not pass'})
   continue
  packet=packets[row['id']];packet_citation(packet,sources)
  if row['packet_hash']!=packet['packet_hash'] or row['definition_hash']!=digest({'definition':row['definition'],'field':row['field'],'packet_sufficient':True}):raise ValueError('Definition/packet binding changed')
  ident=slug(row['term'])
  if ident in {'attention','memory','psychotherapy'}:ident+='-mesh-'+row['id'].lower()
  selected=judges[0];label='judge_a';suffix='-redraft' if row['definition_version']==2 else ''
  cached=json.loads((ROOT/'.private/pilot/calls'/f'{row["id"]}{suffix}-{label}.json').read_text())
  if cached['receipt_id']!=selected['receipt_id'] or cached['parsed']!=selected['parsed']:raise ValueError('Selected mini verdict differs from verified recovery')
  entry={'id':ident,'term':row['term'],'definition':row['definition'],'field':row['field'],'also_see':[],'aliases':[],
    'sources':[packet['source']],'provenance':[{'role':'draft_basis','source':packet['source'],'revision':packet['revision'],'scope':f'MeSH {packet["source_record"]} scope note','locator':packet['url']}],
    'version':row['definition_version'],'review_status':'model_passed_preview','packet_hash':packet['packet_hash'],
    'model_review':{'model':JUDGE,'passed':True,'definition_hash':row['definition_hash'],'packet_hash':packet['packet_hash'],'receipt_id':selected['receipt_id'],
                    'request_hash':cached['request_hash'],'draft_model':manifest['models']['draft'],'registration_hash':manifest['preregistration_hash']},
    'editorial_status':'wording_review_pending' if row['id'] in held else 'human_review_pending'}
  if row['id'] in held:entry['editorial_note']=held[row['id']]
  entry['hash']=semantic_hash(entry)
  public_packet=dict(packet,id=ident,original_packet_hash=packet['packet_hash'])
  public_packet['packet_hash']=digest({k:v for k,v in public_packet.items() if k!='packet_hash'})
  # The original model verdict binds to the original packet hash; the import packet adds only a URL-safe ID.
  entry['packet_hash']=public_packet['packet_hash']
  entry['model_review']['published_packet_hash']=public_packet['packet_hash']
  entry['hash']=semantic_hash(entry)
  tests=required_tests(entry,public_packet,registry)
  if tests and not any(matches(entry,public_packet,r) for r in registry['terms']):
   record={'id':ident,'names':[entry['term']],'anchors':[packet['source_record']],'test':min(tests),'reason':f'Section 4a test {min(tests)}: pinned MeSH {packet["source_record"]} packet/anchor or named risk practice.'}
   registry['terms'].append(record);new_risk.append(ident)
  for directory,data in [('data/entries',entry),('data/packets',public_packet)]:
   p=ROOT/directory/(ident+'.json')
   if p.exists() and json.loads(p.read_text())!=data:raise ValueError('Refusing to replace an existing term')
   p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  added.append({'id':ident,'source_record':packet['source_record'],'term':entry['term'],'editorial_status':entry['editorial_status']})
 if new_risk:
  registry['version']+=1;p=ROOT/'data/risk_terms.json';p.write_text(json.dumps(registry,indent=2)+'\n')
  (ROOT/'data/risk-terms-pin.json').write_text(json.dumps({'version':registry['version'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
 report={'status':'model_passed_public_review_preview','judge_model':JUDGE,'imported':len(added),'excluded':excluded,'wording_review_pending':sum(r['editorial_status']=='wording_review_pending' for r in added),
         'vignettes_imported':0,'human_review_completed':False,'new_paid_calls':0,'risk_records_added':len(new_risk),'entries':added}
 (ROOT/'reports/definition-publication.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='entries'},indent=2))
if __name__=='__main__':import_rows()
