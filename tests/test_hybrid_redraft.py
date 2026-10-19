"""Hybrid origin, role isolation, usage accounting and budget contracts."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import digest
from budget import Budget
from hybrid_draft import body_for,charge_for,validate_receipt,MODEL,ENDPOINT
from hybrid_redraft import Client,ROLES,SCHEMAS,DRAFT,ProtocolError

class HybridTests(unittest.TestCase):
 def fixture(self):
  m={'registration_hash':'a'*64,'paid_roles':['draft'],'api':{'model':MODEL,'endpoint':ENDPOINT,'max_completion_tokens':1000,'reasoning_effort':'low','prices_per_million':{'input':2.5,'cached_input':.25,'output':15}},'prompts':{'draft':DRAFT},'schemas':SCHEMAS}
  p={'term':'Memory','source':'s','source_record':'r','revision':'1','text':'Memory retains information.','packet_hash':'b'*64}
  return m,p
 def test_only_draft_dispatches_to_hosted_client(self):
  m,p=self.fixture()
  with patch('hybrid_draft.call',return_value='draft') as hosted,patch('hybrid_redraft.LocalClient.call',return_value='local') as local:
   c=Client(m)
   for role in ('fit','reader_a','reader_b'):self.assertEqual(c.call(role,p,'cognition'),'local')
   hosted.assert_not_called();self.assertEqual(local.call_count,3)
   self.assertEqual(c.call('draft',p,'cognition'),'draft');hosted.assert_called_once()
  self.assertNotEqual(ROLES['draft'],ROLES['reader_a']);self.assertNotEqual(ROLES['reader_a'],ROLES['reader_b'])
 def test_request_contains_only_permitted_packet_no_old_prose(self):
  m,p=self.fixture();body=body_for(m,p,'cognition')
  self.assertEqual(body['model'],MODEL);self.assertFalse(body['store'])
  self.assertNotIn('Authorization',json.dumps(body))
  self.assertEqual(set(json.loads(body['messages'][1]['content'])),{'headword','field','source','source_record','revision','text'})
  for bad in ({'endpoint':'http://example.org'},{'model':'other'}):
   with self.assertRaises(ValueError):body_for({**m,'api':{**m['api'],**bad}},p,'cognition')
 def test_actual_provider_response_and_usage_bound_to_proof(self):
  m,p=self.fixture();body=body_for(m,p,'cognition');definition={'definition':'Memory retains information.','field':'cognition','packet_sufficient':True}
  usage={'prompt_tokens':1000,'completion_tokens':100,'prompt_tokens_details':{'cached_tokens':200}}
  receipt={'evidence_kind':'OpenAI API drafting','role':'draft','model':MODEL,'receipt_id':'api-test','registration_hash':m['registration_hash'],'packet_hash':p['packet_hash'],'request_hash':digest(body),'request':body,'response':{'id':'chatcmpl-test','model':MODEL,'choices':[{'finish_reason':'stop','message':{'content':json.dumps(definition)}}],'usage':usage},'paid_usd':.00355}
  proof={k:receipt[k] for k in ('model','receipt_id','registration_hash','packet_hash','request_hash')};proof['definition_hash']=digest(definition)
  self.assertEqual(charge_for(usage,m['api']['prices_per_million']),3550)
  validate_receipt(receipt,m,p,'cognition',definition,proof,digest(receipt))
  for change in ({'paid_usd':0},{'role':'reader_a'},{'evidence_kind':'local Ollama inference'}):
   altered={**receipt,**change}
   with self.assertRaises(ValueError):validate_receipt(altered,m,p,'cognition',definition,proof,digest(altered))
  with self.assertRaises(ValueError):validate_receipt(receipt,m,p,'cognition',{**definition,'definition':'Different.'},proof,digest(receipt))
 def test_cap_counts_unresolved_reservations(self):
  with tempfile.TemporaryDirectory() as tmp:
   b=Budget(Path(tmp)/'budget.sqlite',200_000_000);b.reserve('first','draft',199_999_999)
   with self.assertRaises(RuntimeError):b.reserve('second','draft',2)
   self.assertEqual(b.summary()['calls_reserved'],1)

if __name__=='__main__':unittest.main()
