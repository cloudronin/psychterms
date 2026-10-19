import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,digest,semantic_hash,load_inputs,validate_entry
from run_candidate_drafts import candidate_entry,copy_index,check_draft,verify_registration,Client
from prepare_candidate_packets import excerpt,prepare
from budget import Budget

class CandidateTests(unittest.TestCase):
 def setUp(self):
  entries,self.sources,self.fields=load_inputs()
  self.base=copy.deepcopy(next(e for e in entries if e.get('fixture') is True))
  self.packet=json.loads((ROOT/'data/packets'/(self.base['id']+'.json')).read_text())
  self.saved={'parsed':{'definition':'A synthetic definition for testing the unreviewed publication state.','field':self.base['field'],'packet_sufficient':True},
    'model':'fixed-draft-model','receipt_id':'synthetic-receipt','request_hash':'a'*64,'registration_hash':'b'*64,'packet_hash':self.packet['packet_hash']}
 def entry(self):return candidate_entry(self.packet,self.saved,self.sources,self.fields,set())
 def test_replacement_is_new_entry_with_lineage_and_no_inherited_reads(self):
  self.packet['id']='new-test-entry';self.packet['redraft_of']=[self.base['id']]
  self.packet.pop('original_packet_hash',None)
  self.packet['packet_hash']=digest({k:v for k,v in self.packet.items() if k!='packet_hash'})
  self.saved['packet_hash']=self.packet['packet_hash']
  replacement=self.entry()
  self.assertEqual(replacement['id'],'new-test-entry')
  self.assertEqual(replacement['redraft_of'],[self.base['id']])
  self.assertNotIn('reader_reviews',replacement);self.assertNotIn('model_review',replacement)
  self.assertIn(self.packet['packet_hash'],replacement['provenance'][0]['scope'])
  self.assertEqual(replacement['hash'],semantic_hash(replacement))
 def test_candidate_can_preview_without_any_judge_claim(self):
  e=self.entry();validate_entry(e,self.sources,self.fields)
  self.assertNotIn('status',e);self.assertNotIn('model_review',e)
  self.assertEqual(e['packet_hash'],self.packet['packet_hash'])
 def test_candidate_cannot_release_or_self_promote(self):
  e=self.entry()
  with self.assertRaisesRegex(ValueError,'Preview'):validate_entry(e,self.sources,self.fields,release=True)
  e['status']='judged'
  with self.assertRaisesRegex(ValueError,'build-owned'):validate_entry(e,self.sources,self.fields)
 def test_edited_definition_invalidates_drafting_evidence(self):
  e=self.entry();e['definition']='An altered unsupported assertion.';e['hash']=semantic_hash(e)
  with self.assertRaisesRegex(ValueError,'Draft evidence'):validate_entry(e,self.sources,self.fields)
 def test_candidate_cannot_claim_a_passed_review(self):
  e=self.entry();e['model_review']={'passed':True}
  from entry_status import prepare as statuses
  with self.assertRaisesRegex(ValueError,'Stale reader proof'):statuses([e],history={})
 def test_insufficient_packet_and_15_word_copy_do_not_publish(self):
  self.saved['parsed']['packet_sufficient']=False
  with self.assertRaisesRegex(ValueError,'insufficient'):self.entry()
  draft={'definition':' '.join('word'+str(i) for i in range(20))+'.','field':self.base['field'],'packet_sufficient':True}
  with self.assertRaisesRegex(ValueError,'15-word overlap'):check_draft(draft,self.fields,copy_index([draft['definition']]))
 def test_wrong_source_binding_rejected(self):
  self.saved['packet_hash']='c'*64
  with self.assertRaisesRegex(ValueError,'different source packet'):self.entry()
 def test_context_window_contains_the_requested_term(self):
  text='prefix '*1000+'requested term '+'suffix '*1000
  result,start,end=excerpt(text,'requested term',limit=600)
  self.assertIn('requested term',result);self.assertEqual(result,text[start:end]);self.assertLessEqual(len(result),600)
 def test_exact_source_label_precedes_broader_descriptor_alias(self):
  records=[{'source_id':'mesh-2026','record_id':'broader','term':'Broader concept','aliases':['Synthetic topic'],'text':'A description of a broader concept that is not specific to the requested topic.','snapshot_sha256':self.packet['source_snapshot_sha256'],'url':'https://example.org/broader'},
   {'source_id':'ncit','record_id':'exact','term':'Synthetic topic','aliases':[],'text':'A cognitive source description specific to the requested synthetic topic and its intended meaning.','snapshot_sha256':'b'*64,'url':'https://example.org/exact'}]
  row={'term':'Synthetic topic','production_scope':'term','status':'exact_label_source_candidate','matches':[{'source':r['source_id'],'record_id':r['record_id']} for r in records]}
  (ROOT/'.private').mkdir(exist_ok=True)
  with tempfile.TemporaryDirectory(dir=ROOT/'.private') as tmp,patch('prepare_candidate_packets.load_records',return_value=records):
   directory=Path(tmp);(directory/'coverage.json').write_text(json.dumps([row]));prepare(directory,directory/'out')
   packets=json.loads((directory/'out/packets.json').read_text())
   self.assertEqual(packets[0]['source'],'ncit');self.assertEqual(packets[0]['source_record'],'exact')
 def test_no_cap_prevents_any_paid_execution(self):
  import run_candidate_drafts as runner
  packets=[self.packet]
  m={'line':'candidate-definitions-v1','packet_set_hash':digest(packets),'source_packet_count':1,'model':'gpt-5.4-2026-03-05','copy_threshold_words':15,
    'executor_sha256':hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest(),'status':'proposed','authorized_cap_usd':None}
  m['registration_hash']=digest(m)
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir();(root/'data/release-policy.json').write_text('{}')
   with patch('urllib.request.urlopen') as network:
    with self.assertRaisesRegex(ValueError,'has not set'):verify_registration(m,packets,execute=True,root=root)
    network.assert_not_called()
 def test_candidate_schema_has_receipt_binding(self):
  import jsonschema
  schema=json.loads((ROOT/'schema/entry.schema.json').read_text());jsonschema.validate(self.entry(),schema)
 def test_citation_names_the_actual_source_record(self):
  from source_citations import packet_citation
  packet=copy.deepcopy(self.packet);packet['source_label']='Actual source record title';packet['packet_hash']=digest({k:v for k,v in packet.items() if k!='packet_hash'})
  self.assertIn('Actual source record title',packet_citation(packet,self.sources)['citation'])
 def test_candidate_status_and_source_citations_survive_export(self):
  from export import build
  data,md,_=build([self.entry()],history={})
  self.assertEqual(data['entries'][0]['status'],'candidate')
  self.assertIn('Candidate: drafted from the sources shown, not yet read by the two reviewers.',md)
  self.assertIn(self.packet['url'],md)
  self.assertEqual(data['references'][self.packet['id']][0]['packet_hash'],self.packet['packet_hash'])
 def test_sentence_contract_gets_one_redraft_and_insufficient_sources_are_not_forced(self):
  from run_candidate_drafts import draft_packet
  from unittest.mock import Mock
  first=copy.deepcopy(self.saved);first['parsed']['definition']='One. Two. Three. Four.'
  client=Mock();client.call.side_effect=[first,self.saved]
  entry=draft_packet(client,self.packet,self.sources,self.fields,set());self.assertEqual(entry['definition'],self.saved['parsed']['definition']);self.assertEqual(client.call.call_count,2)
  client=Mock();client.call.side_effect=[first,first]
  with self.assertRaisesRegex(ValueError,'three sentences'):draft_packet(client,self.packet,self.sources,self.fields,set())
  self.assertEqual(client.call.call_count,2)
  first['parsed']['packet_sufficient']=False;client=Mock();client.call.return_value=first
  with self.assertRaisesRegex(ValueError,'insufficient'):draft_packet(client,self.packet,self.sources,self.fields,set())
  self.assertEqual(client.call.call_count,1)
 def client(self,path,cap):
  for folder in ('calls','receipts'):(path/folder).mkdir()
  m={'model':'gpt-5.4-2026-03-05','fields':self.fields,'draft_prompt':'Synthetic test prompt','draft_schema':{'required':['definition','field','packet_sufficient']},
    'max_completion_tokens':1000,'reasoning_effort':'low','max_request_bytes':24000,'registration_hash':'b'*64,'prices_per_million':{'input':2.5,'output':15,'cached_input':.25},'transport_schema_retries':1}
  budget=Budget(path/'budget.sqlite',cap)
  return Client(m,[self.packet],'synthetic-key',budget,path)
 def test_client_reserves_before_network_dispatch(self):
  with tempfile.TemporaryDirectory() as tmp,patch('run_candidate_drafts.require_authorization'),patch('urllib.request.urlopen') as network:
   client=self.client(Path(tmp),1)
   with self.assertRaisesRegex(RuntimeError,'Budget cap'):client.call(self.packet)
   network.assert_not_called()
 def test_uncertain_network_charges_retain_reservations_and_obey_retry_limit(self):
  with tempfile.TemporaryDirectory() as tmp,patch('run_candidate_drafts.require_authorization'),patch('urllib.request.urlopen',side_effect=TimeoutError):
   client=self.client(Path(tmp),1_000_000)
   with self.assertRaisesRegex(RuntimeError,'retry limit exhausted'):client.call(self.packet)
   self.assertEqual(client.budget.summary()['calls_reserved'],2);self.assertGreater(client.budget.summary()['unresolved_reservations_usd'],0)
   with self.assertRaisesRegex(RuntimeError,'retry limit exhausted'):client.call(self.packet)
   self.assertEqual(client.budget.summary()['calls_reserved'],2)
 def test_scope_rejection_precedes_any_network_or_reservation(self):
  with tempfile.TemporaryDirectory() as tmp,patch('run_candidate_drafts.require_authorization'),patch('urllib.request.urlopen') as network:
   client=self.client(Path(tmp),1_000_000);client.m['scope_and_field_required']=True
   with self.assertRaisesRegex(ValueError,'Scope and field'):client.call(self.packet)
   network.assert_not_called();self.assertEqual(client.budget.summary()['calls_reserved'],0)
 def test_changed_requests_get_separate_caches_and_old_receipts_are_preserved(self):
  from io import BytesIO
  result={'model':'gpt-5.4-2026-03-05','usage':{'prompt_tokens':40,'completion_tokens':5},'choices':[{'finish_reason':'stop','message':{'content':json.dumps(self.saved['parsed'])}}]}
  with tempfile.TemporaryDirectory() as tmp,patch('run_candidate_drafts.require_authorization'),patch('urllib.request.urlopen',side_effect=lambda *a,**k:BytesIO(json.dumps(result).encode())) as network:
   client=self.client(Path(tmp),1_000_000);original=client.call(self.packet)
   client.m['draft_prompt']+=' Changed instruction.';client.m['registration_hash']='c'*64
   changed=client.call(self.packet);self.assertNotEqual(original['request_hash'],changed['request_hash'])
   self.assertEqual(len(list((Path(tmp)/'calls').glob('*.json'))),2)
   self.assertEqual(client.call(self.packet),changed);self.assertEqual(network.call_count,2)
 def test_receipted_request_reconciles_and_is_not_rebilled_on_resume(self):
  from io import BytesIO
  result={'model':'gpt-5.4-2026-03-05','usage':{'prompt_tokens':40,'completion_tokens':5,'prompt_tokens_details':{'cached_tokens':10}},
    'choices':[{'finish_reason':'stop','message':{'content':json.dumps(self.saved['parsed'])}}]}
  with tempfile.TemporaryDirectory() as tmp,patch('run_candidate_drafts.require_authorization'),patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(result).encode())) as network:
   client=self.client(Path(tmp),1_000_000);first=client.call(self.packet);second=client.call(self.packet)
   self.assertEqual(first,second);network.assert_called_once()
   self.assertEqual(client.budget.summary()['receipted_usd'],.000153)

if __name__=='__main__':unittest.main()
