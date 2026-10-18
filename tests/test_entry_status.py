import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,load_inputs,digest
from entry_status import prepare,check_forward,check_snapshot,release_note
from scope_rules import decide

class StatusTests(unittest.TestCase):
 def setUp(self):
  self.entry=copy.deepcopy(next(e for e in load_inputs()[0] if e.get('fixture')))
  self.packet=json.loads((ROOT/'data/packets'/(self.entry['id']+'.json')).read_text())
 def reader(self,model='reader-one',passed=True):
  return {'model':model,'draft_model':'codex-initial-fixture','passed':passed,'definition_hash':digest({'definition':self.entry['definition'],'field':self.entry['field'],'packet_sufficient':True}),
   'packet_hash':self.packet.get('original_packet_hash',self.packet['packet_hash']),'published_packet_hash':self.packet['packet_hash'],
   'receipt_id':'test-'+model,'request_hash':'a'*64,'registration_hash':'b'*64,'reasons':[] if passed else ['Meaning is not supported by the packet.']}
 def build(self):return prepare([self.entry],history={},scope=False)
 def test_candidate_reviewed_judged_from_evidence_only(self):
  for count,status in [(0,'candidate'),(1,'reviewed'),(2,'judged')]:
   self.entry['reader_reviews']=[self.reader('reader-'+str(i)) for i in range(count)]
   entries,report=self.build();self.assertEqual(entries[0]['status'],status);self.assertEqual(entries[0]['checks'],{'readers':f'{count}/2','copy':'clear'})
   self.assertEqual(report['status_counts'][status],1);self.assertFalse(entries[0]['released'])
 def test_drafter_and_duplicate_model_never_make_second_reader(self):
  self.entry['reader_reviews']=[self.reader(),self.reader(),self.reader('codex-initial-fixture')]
  entries,report=self.build();self.assertEqual(entries[0]['status'],'reviewed');self.assertEqual(report['reader_models'],['reader-one'])
 def test_stale_packet_or_definition_proof_cannot_promote(self):
  self.entry['reader_reviews']=[self.reader()];self.entry['definition']+=' Edited.'
  with self.assertRaisesRegex(ValueError,'Stale reader'):self.build()
 def test_two_failures_drop_with_reason_even_after_pass(self):
  self.entry['reader_reviews']=[self.reader(),self.reader('no-one',False),self.reader('no-two',False)]
  entries,report=self.build();self.assertEqual(entries[0]['status'],'dropped');self.assertIn('not supported',entries[0]['drop_reason'])
  self.assertIn('| Dropped | 1 |',release_note(report))
 def test_copy_hit_blocks_publication_even_with_readers(self):
  self.entry['definition']=' '.join(self.packet['text'].split()[:20])
  self.entry['reader_reviews']=[self.reader()]
  with self.assertRaisesRegex(ValueError,'15-word copy hit'):self.build()
 def test_manual_status_or_release_rejected(self):
  for key,value in [('status','judged'),('released',True)]:
   self.entry[key]=value
   with self.assertRaisesRegex(ValueError,'build-owned'):self.build()
   del self.entry[key]
 def test_backward_or_disappeared_entries_rejected(self):
  for old,new in [('reviewed','candidate'),('judged','reviewed'),('dropped','judged')]:
   with self.assertRaisesRegex(ValueError,'backward'):check_forward({'x':{'status':old}},{'x':{'status':new}})
  with self.assertRaises(ValueError):check_forward({'x':{'status':'candidate'}},{})
  check_forward({'x':{'status':'reviewed'}},{'x':{'status':'dropped'}})
 def test_committed_history_cannot_omit_new_or_changed_status(self):
  current={'x':{'status':'reviewed'}}
  for history in ({},{'x':{'status':'candidate'}}):
   with self.assertRaisesRegex(ValueError,'stale'):check_snapshot(history,current)
  check_snapshot(current,current)
 def test_numbered_release_is_separate_from_review_status(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data/packets').mkdir(parents=True)
   (root/'data/packets'/(self.entry['id']+'.json')).write_text(json.dumps(self.packet))
   (root/'data/numbered-releases.json').write_text(json.dumps({'releases':[{'version':'1.0.0','entries':{self.entry['id']:self.entry['hash']}}]}))
   entries,report=prepare([self.entry],root=root,scope=False,history={})
   self.assertEqual(entries[0]['status'],'candidate');self.assertTrue(entries[0]['released']);self.assertEqual(report['status_counts']['released'],1)
 def test_release_validation_does_not_change_candidate_to_judged(self):
  from core import validate_entry
  entries,_=self.build();entry=entries[0];entry['released']=True;entry['release_versions']=['1.0.0']
  _,sources,fields=load_inputs();validate_entry(entry,sources,fields,release=True,built=True)
  self.assertEqual(entry['status'],'candidate')
 def test_dropped_definitions_excluded_from_public_exports(self):
  from export import build
  self.entry['reader_reviews']=[self.reader('one',False),self.reader('two',False)]
  data,md,_=build([self.entry],history={})
  self.assertEqual(data['entries'],[]);self.assertEqual(data['dropped'][0]['id'],self.entry['id'])
  self.assertNotIn(self.entry['definition'],md)

class ScopeTests(unittest.TestCase):
 def test_unrelated_gene_is_excluded_before_spend(self):
  self.assertFalse(decide({'term':'AAAS','source':'ncit','source_record':'test','source_label':'AAAS Gene','text':'This gene is involved in nucleocytoplasmic transport.'})['eligible'])
 def test_neural_or_psychology_source_context_sets_field(self):
  for text,field in [('An action potential has a refractory period.','biological'),('Working memory supports reasoning.','cognition')]:
   result=decide({'term':'Test','source':'ncit','source_record':'test','text':text});self.assertTrue(result['eligible']);self.assertEqual(result['field'],field)
 def test_gene_alias_collision_is_not_a_psychology_source_packet(self):
  packet={'term':'wish','source':'ncit','source_record':'test','source_label':'NCKIPSD wt Allele','text':'This gene affects neuronal expression and stress.','semantic_types':['Gene or Genome']}
  self.assertFalse(decide(packet)['eligible'])
 def test_oxidative_stress_and_generic_ability_are_not_psychology_context(self):
  for text in ['This protein has the ability to catalyze lipid metabolism.','This cell responds to oxidative stress.']:
   self.assertFalse(decide({'term':'unrelated','source':'ncit','source_record':'test','source_label':'Protein','text':text})['eligible'])
 def test_registered_field_cannot_be_changed_by_drafter(self):
  from run_candidate_drafts import candidate_entry
  from test_candidate_publication import CandidateTests
  fixture=CandidateTests();fixture.setUp();fixture.packet['planned_field']='ethics'
  fixture.packet['packet_hash']=digest({k:v for k,v in fixture.packet.items() if k!='packet_hash'})
  fixture.saved['packet_hash']=fixture.packet['packet_hash']
  with self.assertRaisesRegex(ValueError,'preregistered field'):candidate_entry(fixture.packet,fixture.saved,fixture.sources,fixture.fields,set())

if __name__=='__main__':unittest.main()
