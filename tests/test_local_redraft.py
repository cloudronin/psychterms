import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,digest,semantic_hash
from local_redraft import (Client,ROLES,FIT,DRAFT,READ,SCHEMAS,NoRedirect,ProtocolError,
    atomic,identity,local_http,prior_wave_guard,summarize,validate_result,run,audit_accepted)
from local_receipts import validate_records
from prepare_local_redrafts import permitted,build_index,candidates

def packet(ident='new',record='fresh',text='Term is a synthetic process of retaining and retrieving information.'):
 p={'id':ident,'term':'Term','source':'s','source_record':record,'revision':'1','text':text,
    'source_label':'Term','source_snapshot_sha256':'a'*64,'licence':'CC0-1.0','url':'https://example.org/'+record,
    'redraft_of':['old'],'planned_field':'cognition'}
 p['packet_hash']=digest(p);return p

def manifest():
 m={'registration_hash':'','endpoint':'http://127.0.0.1:11434/api/','paid_dispatch_enabled':False,'paid_cap_usd':0,
    'roles':ROLES,'models':{name:{'digest':str(i)*64,'capabilities':[]} for i,name in enumerate(sorted(set(ROLES.values())),1)},
    'prompts':{'fit':FIT,'draft':DRAFT,'read':READ},'schemas':SCHEMAS,'options':{'temperature':0,'seed':20261018,'num_ctx':8192},
    'max_output_tokens':{'fit':256,'draft':512,'read':512},'transport_or_schema_retries':1,'min_wave_pass_fraction':.60}
 m['registration_hash']=digest({k:v for k,v in m.items() if k!='registration_hash'});return m

class LocalRedraftTests(unittest.TestCase):
 def setup_client(self,dest):
  m=manifest();atomic(dest/'registration.json',m);return m,Client(m,dest)
 def responder(self,m):
  def response(endpoint,payload=None,**kwargs):
   if endpoint=='tags':return {'models':[{'name':name,'digest':p['digest']} for name,p in m['models'].items()]}
   assert endpoint=='chat'
   required=payload['format']['required']
   value=({'answer':'yes','reason':'The packet explicitly explains the term.'} if 'answer' in required else
     {'definition':'A synthetic process of retaining and retrieving information.','field':'cognition','packet_sufficient':True} if 'definition' in required else {'passed':True,'reasons':[]})
   return {'model':payload['model'],'done':True,'done_reason':'stop','message':{'content':json.dumps(value)}}
  return response
 def accepted(self,dest):
  m,client=self.setup_client(dest);p=packet()
  with patch('local_redraft.local_http',side_effect=self.responder(m)):
   saved={r:client.call(r,p,'cognition','A synthetic process of retaining and retrieving information.' if r.startswith('reader') else None) for r in ('fit','draft','reader_a','reader_b')}
  draft=saved['draft'];dh=digest(draft['parsed'])
  e={'id':'new','term':'Term','field':'cognition','definition':draft['parsed']['definition'],'version':2,'redraft_of':['old'],
     'draft_evidence':{k:draft[k] for k in ('model','receipt_id','request_hash','registration_hash','packet_hash')},'reader_reviews':[]}
  e['draft_evidence']['definition_hash']=dh
  for role in ('reader_a','reader_b'):
   value=saved[role];e['reader_reviews'].append({**{k:value[k] for k in ('model','receipt_id','request_hash','registration_hash','packet_hash')},
     'definition_hash':dh,'draft_model':draft['model'],'published_packet_hash':p['packet_hash'],'passed':True,'reasons':[]})
  e['hash']=semantic_hash(e)
  a={'entry':e,'packet':p,'fit':saved['fit'],'draft':saved['draft'],'readers':[saved['reader_a'],saved['reader_b']],'registration_hash':m['registration_hash']}
  return m,a
 def test_sources_require_admitted_license_and_original_drafting_role(self):
  yes={'decision':'yes','licence':'CC-BY-4.0','roles':['draft_basis'],'licence_confirmed':True}
  self.assertTrue(permitted(yes))
  for change in ({'licence':'CC-BY-SA-4.0'},{'licence':'CC-BY-NC-SA-4.0'},{'licence_confirmed':False},{'roles':['related_topic']},{'decision':'no'}):
   self.assertFalse(permitted(dict(yes,**change)))
 def test_retrieval_excludes_failed_basis_caps_five_and_builds_new_lineage(self):
  source={'id':'s','decision':'yes','licence':'CC0-1.0','roles':['draft_basis'],'licence_confirmed':True,'pinned_version':'1'}
  old=packet('old','r0')
  records=[{'source_id':'s','record_id':'r'+str(i),'term':'Term','aliases':[],
    'text':old['text'] if i==0 else 'Term is a synthetic psychology process with source-specific detail number '+str(i)+'.',
    'snapshot_sha256':'a'*64,'url':'https://example.org/'+str(i)} for i in range(9)]
  with tempfile.TemporaryDirectory() as tmp:
   db,_=build_index(records,Path(tmp)/'sources.sqlite')
   rows=candidates({'term':'Term','failed_entry_ids':['old']},'cognition',db,records,{'s':source},[old]);db.close()
  self.assertEqual(len(rows),5);self.assertNotIn('r0',[p['source_record'] for p in rows])
  self.assertTrue(all(p['id'].startswith('term-v2-') and p['redraft_of']==['old'] for p in rows))
 def test_local_transport_refuses_unknown_endpoints_and_redirects(self):
  with patch('urllib.request.build_opener') as transport:
   with self.assertRaises(ValueError):local_http('https://api.openai.com/v1/chat/completions')
   transport.assert_not_called()
  with self.assertRaises(ProtocolError):NoRedirect().redirect_request(None,None,None,None,None,None)
 def test_reader_and_fit_outputs_must_be_decisive_and_well_formed(self):
  validate_result('fit',{'answer':'no','reason':'Only a mention.'})
  for role,value in [('fit',{'answer':'maybe','reason':'Uncertain.'}),('fit',{'answer':'yes','reason':'Two\nlines'}),
   ('reader_a',{'passed':True,'reasons':['Unsupported.']}),('reader_b',{'passed':False,'reasons':[]})]:
   with self.assertRaises(ValueError):validate_result(role,value)
 def test_primary_denominator_includes_all_headwords(self):
  rows=[{}]*500;m=manifest()
  outcomes={str(i):{'status':'judged' if i<300 else 'redraft','reason':None if i<300 else 'no supporting source found yet'} for i in range(500)}
  report=summarize(1,rows,outcomes,m)
  self.assertEqual(report['pass_fraction'],.60);self.assertTrue(report['continue_allowed']);self.assertEqual(report['no_supporting_source'],200)
  outcomes['299']['status']='redraft';self.assertFalse(summarize(1,rows,outcomes,m)['continue_allowed'])
 def test_wave_two_requires_emitted_complete_report_and_sixty_percent(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m=manifest()
   with self.assertRaises(ValueError):prior_wave_guard(2,dest,m)
   for fraction,complete in [(.599,True),(.9,False),(.6,True)]:
    report={'registration_hash':m['registration_hash'],'complete':complete,'pass_fraction':fraction}
    atomic(dest/'wave-001/report.json',report);atomic(dest/'wave-001/reported.json',{'report_hash':digest(report)})
    if fraction>=.6 and complete:prior_wave_guard(2,dest,m)
    else:
     with self.assertRaises(ValueError):prior_wave_guard(2,dest,m)
 def test_cached_verdict_cannot_differ_from_actual_response(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m,client=self.setup_client(dest)
   with patch('local_redraft.local_http',side_effect=self.responder(m)):saved=client.call('fit',packet(),'cognition')
   path=next((dest/'calls').glob('fit-*.json'));forged=json.loads(path.read_text());forged['parsed']['answer']='no';atomic(path,forged)
   with patch('local_redraft.local_http') as transport:
    with self.assertRaisesRegex(ValueError,'actual local response'):client.call('fit',packet(),'cognition')
    transport.assert_not_called()
 def test_swapped_model_stops_before_dispatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m,client=self.setup_client(dest)
   with patch('local_redraft.local_http',return_value={'models':[]}) as transport:
    with self.assertRaises(ProtocolError):client.call('fit',packet(),'cognition')
    self.assertEqual([c.args[0] for c in transport.call_args_list],['tags'])
 def test_actual_local_receipts_bind_fit_draft_and_both_readers(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m,a=self.accepted(dest)
   proposal,receipts=audit_accepted(a,m,dest)
   self.assertEqual(len(receipts),4);validate_records(proposal,a['packet'],m,receipts)
   for changed in [dict(a['packet'],text='Changed source text.'),dict(a['packet'],redraft_of=['other'])]:
    with self.assertRaises(ValueError):validate_records(proposal,changed,m,receipts)
 def test_receipts_cannot_include_extra_context_even_with_recomputed_hash(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m,a=self.accepted(dest);e,receipts=audit_accepted(a,m,dest)
   receipt=copy.deepcopy(receipts['reader_a']);receipt['request']['messages'].append({'role':'user','content':'Another reader passed it.'})
   receipt['request_hash']=digest(receipt['request']);receipts['reader_a']=receipt
   e['local_run']['receipts']['reader_a']=digest(receipt)
   with self.assertRaisesRegex(ValueError,'prompt or input'):validate_records(e,a['packet'],m,receipts)
 def test_reader_proof_cannot_invert_the_actual_verdict(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m,a=self.accepted(dest);e,receipts=audit_accepted(a,m,dest)
   e['reader_reviews'][0]['passed']=False
   with self.assertRaisesRegex(ValueError,'did not pass'):validate_records(e,a['packet'],m,receipts)
 def test_drafter_weights_cannot_count_as_an_independent_reader(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m,a=self.accepted(dest);e,receipts=audit_accepted(a,m,dest)
   m['models'][m['roles']['reader_a']]['digest']=m['models'][m['roles']['draft']]['digest']
   m['registration_hash']=digest({k:v for k,v in m.items() if k!='registration_hash'});e['local_run']['manifest_sha256']=digest(m)
   with self.assertRaisesRegex(ValueError,'not distinct'):validate_records(e,a['packet'],m,receipts)
 def test_new_sourcing_reason_does_not_rewrite_terminal_entry_history(self):
  from entry_status import prepare
  p=packet('old');e={'id':'old','term':'Term','field':'cognition','definition':'A rejected synthetic definition.',
     'version':1,'packet_hash':p['packet_hash'],'draft_evidence':{'model':'synthetic-drafter'}}
  e['hash']=semantic_hash(e);dh=digest({'definition':e['definition'],'field':e['field'],'packet_sufficient':True})
  e['reader_reviews']=[{'model':name,'draft_model':'synthetic-drafter','passed':False,'definition_hash':dh,
   'packet_hash':p['packet_hash'],'receipt_id':name,'request_hash':'a'*64,'registration_hash':'b'*64,'reasons':['Unsupported.']} for name in ('reader-a','reader-b')]
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);atomic(root/'data/packets/old.json',p)
   before,history=prepare([e],root=root,history={},scope=False)
   attempt={'status':'redraft','reason':'no supporting source found yet','failed_entry_ids':['old']}
   atomic(root/'data/redraft-source-outcomes.json',{'outcomes':{'term':attempt}})
   after,current=prepare([e],root=root,history=history['entries'],scope=False)
   self.assertEqual(history['entries'],current['entries']);self.assertEqual(before[0]['drop_reason'],after[0]['drop_reason'])
   self.assertEqual(after[0]['latest_sourcing'],attempt)
   self.assertEqual(current['redraft_candidates']['candidates'][0]['latest_sourcing'],attempt)
 def test_no_fit_packet_never_reaches_drafter_and_keeps_redraft_reason(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp);m=manifest();m.update(comparison_sha256=__import__('hashlib').sha256(b'').hexdigest(),comparison_windows=0,failed_snapshots={})
   (dest/'comparison.bin').write_bytes(b'')
   row={'term':'Term','headword_key':'term','field':'cognition','failed_entry_ids':['old'],'wave':1,'packets':[{'packet':packet()}]}
   source={'s':{'decision':'yes','roles':['draft_basis'],'licence':'CC0-1.0'}}
   with patch('local_redraft.registration',return_value=(m,{'cohort':[row]})),patch('local_redraft.load_inputs',return_value=([],source,['cognition'])),patch.object(Client,'call',return_value={'parsed':{'answer':'no','reason':'Only a mention.'}}) as calls:
    report=run(1,dest)
   self.assertEqual([c.args[0] for c in calls.call_args_list],['fit']);self.assertEqual(report['no_supporting_source'],1)
   outcome=json.loads((dest/'wave-001/outcomes.json').read_text())['term']
   self.assertEqual(outcome['reason'],'no supporting source found yet');self.assertEqual(outcome['status'],'redraft')

if __name__=='__main__':unittest.main()
