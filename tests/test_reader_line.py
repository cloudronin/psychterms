import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from io import BytesIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,digest
from budget import Budget
from run_reader_reviews import Client,MODELS,PROMPT,SCHEMA,code_hashes,verify,validate_verdict

class ReaderLineTests(unittest.TestCase):
 def setUp(self):
  self.entry=json.loads((ROOT/'data/entries/attention.json').read_text());packet=json.loads((ROOT/'data/packets/attention.json').read_text())
  self.job={'id':self.entry['id'],'term':self.entry['term'],'definition':self.entry['definition'],'field':self.entry['field'],'definition_hash':digest({'definition':self.entry['definition'],'field':self.entry['field'],'packet_sufficient':True}),'packet':packet,'draft_model':'codex-initial-fixture','model':'gpt-5.4-mini-2026-03-17'}
  self.m={'status':'proposed','authorized_cap_usd':None,'models':MODELS,'prompt':PROMPT,'schema':SCHEMA,'max_completion_tokens':1000,'max_request_bytes':24000,'reasoning_effort':'low','transport_schema_retries':1,'registration_hash':'b'*64}
 def client(self,path,cap=1_000_000):return Client(self.m,'synthetic-key',Budget(path/'budget.sqlite',cap),path)
 def test_reader_line_cannot_charge_to_drafting_cap(self):
  with tempfile.TemporaryDirectory() as tmp,patch('urllib.request.urlopen') as network:
   client=self.client(Path(tmp))
   with self.assertRaisesRegex(ValueError,'own approved cap'):client.call(self.job)
   network.assert_not_called();self.assertEqual(client.budget.summary()['calls_reserved'],0)
 def test_drafter_rejected_before_network(self):
  with tempfile.TemporaryDirectory() as tmp,patch('run_reader_reviews.authorize'),patch('urllib.request.urlopen') as network:
   client=self.client(Path(tmp));self.job['draft_model']=self.job['model']
   with self.assertRaisesRegex(ValueError,'Drafter cannot'):client.call(self.job)
   network.assert_not_called()
 def test_reservation_precedes_network(self):
  with tempfile.TemporaryDirectory() as tmp,patch('run_reader_reviews.authorize'),patch('urllib.request.urlopen') as network:
   client=self.client(Path(tmp),1)
   with self.assertRaisesRegex(RuntimeError,'Budget cap'):client.call(self.job)
   network.assert_not_called()
 def test_receipted_proof_bound_to_definition_packet_and_model_and_cached(self):
  result={'model':self.job['model'],'usage':{'prompt_tokens':40,'completion_tokens':5},'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'passed':True,'reasons':[]})}}]}
  with tempfile.TemporaryDirectory() as tmp,patch('run_reader_reviews.authorize'),patch('urllib.request.urlopen',return_value=BytesIO(json.dumps(result).encode())) as network:
   client=self.client(Path(tmp));proof=client.call(self.job);self.assertEqual(client.call(self.job),proof);network.assert_called_once()
   self.assertEqual(proof['definition_hash'],self.job['definition_hash']);self.assertEqual(proof['published_packet_hash'],self.job['packet']['packet_hash']);self.assertNotEqual(proof['model'],proof['draft_model'])
   self.assertEqual(client.budget.summary()['receipted_usd'],.000053)
 def test_timeout_retains_reserve_and_never_exceeds_retry_limit_on_resume(self):
  with tempfile.TemporaryDirectory() as tmp,patch('run_reader_reviews.authorize'),patch('urllib.request.urlopen',side_effect=TimeoutError):
   client=self.client(Path(tmp))
   with self.assertRaisesRegex(RuntimeError,'retry limit exhausted'):client.call(self.job)
   resumed=self.client(Path(tmp))
   with self.assertRaisesRegex(RuntimeError,'retry limit exhausted'):resumed.call(self.job)
   self.assertEqual(resumed.budget.summary()['calls_reserved'],2);self.assertGreater(resumed.budget.summary()['unresolved_reservations_usd'],0)
 def test_failures_require_reasons_and_passes_cannot_carry_rejection_reasons(self):
  for verdict in [{'passed':False,'reasons':[]},{'passed':True,'reasons':['Unsupported claim.']}]:
   with self.assertRaises(ValueError):validate_verdict(verdict)
  validate_verdict({'passed':False,'reasons':['The packet does not support the requested sense.']})
 def test_mismatched_request_text_cannot_claim_a_valid_definition_hash(self):
  import run_reader_reviews as runner
  self.job['definition']='A different definition.';jobs=[self.job]
  m={**self.m,'line':'independent-readers-v1','job_count':1,'job_set_hash':digest(jobs),'code_hashes':code_hashes(),'executor_sha256':__import__('hashlib').sha256(Path(runner.__file__).read_bytes()).hexdigest()}
  m.pop('registration_hash');m['registration_hash']=digest(m)
  with self.assertRaisesRegex(ValueError,'definition binding'):verify(m,jobs)

if __name__=='__main__':unittest.main()
