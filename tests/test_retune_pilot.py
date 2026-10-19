"""Contracts protect source entailment and actual evidence, rather than maximizing yield."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import digest
from retune_protocol import MODELS,validate_value
from retune_api import request_for,audit_saved,charge
from retune_controls import controls
from retune_pilot import process
class RetuneTests(unittest.TestCase):
 def test_fit_yes_needs_exact_source_evidence(self):
  text='Lightness constancy keeps perceived lightness relatively stable.'
  validate_value('fit',{'answer':'yes','evidence':'perceived lightness relatively stable','reason':'Explains the concept.'},text)
  for evidence in ('','An invented source quotation'):
   with self.assertRaises(ValueError):validate_value('fit',{'answer':'yes','evidence':evidence,'reason':'Explains the concept.'},text)
 def test_verdict_cannot_fail_without_reason_or_pass_with_one(self):
  for value in ({'passed':False,'reasons':[],'field_issue':'','support':[]},{'passed':True,'reasons':['It is supported.'],'field_issue':'','support':[]}):
   with self.assertRaises(ValueError):validate_value('reader_a',value,'Source')
  validate_value('reader_b',{'passed':True,'reasons':[],'field_issue':'Taxonomy needs review.','support':[{'claim':'Source','evidence':'Source'}]},'Source')
 def test_roles_are_distinct_and_reader_requests_are_isolated(self):
  p=controls()[0]['packet'];a=request_for('reader_a',p,'cognition','Memory stores information.')
  self.assertEqual(len({MODELS[r] for r in ('draft','reader_a','reader_b')}),3)
  self.assertEqual(set(json.loads(a['messages'][1]['content'])),{'headword','taxonomy_hint','source_packet','draft_to_check'})
  self.assertEqual(json.loads(a['messages'][1]['content'])['draft_to_check'],{'definition':'Memory stores information.'})
  self.assertFalse(a['store'])
 def test_reader_support_requires_literal_source_evidence(self):
  definition='Parenting is marked by warmth.';text='Parenting is characterized by warmth.'
  good={'passed':True,'reasons':[],'field_issue':'','support':[{'claim':definition,'evidence':text}]}
  validate_value('reader_a',good,text,definition)
  for support in ([{'claim':definition,'evidence':'An invented quotation.'}],[]):
   with self.assertRaises(ValueError):validate_value('reader_a',{**good,'support':support},text,definition)
 def test_all_roles_receive_actual_source_labels_and_aliases(self):
  packet={**controls()[0]['packet'],'source_label':'A different source concept','publisher_aliases':['Publisher alias']}
  for role in ('fit','draft','reader_a','reader_b'):
   data=json.loads(request_for(role,packet,'cognition','New definition.' if role.startswith('reader') else None)['messages'][1]['content'])
   source=data.get('source_packet',data)
   self.assertEqual(source['source_record_label'],'A different source concept');self.assertEqual(source['publisher_aliases'],['Publisher alias'])
 def test_controls_include_positive_paraphrases_and_deliberate_unsupported_drafts(self):
  c=controls();self.assertEqual(len(c),19)
  self.assertTrue(any(r['expected_fit'] and not r['expected_read'] for r in c))
  self.assertTrue(any(not r['expected_fit'] for r in c))
  self.assertTrue(next(r for r in c if r['packet']['term']=='authoritative parenting')['expected_read'])
 def test_no_fit_cannot_dispatch_a_draft(self):
  p=controls()[0]['packet'];row={'term':'memory','headword_key':'memory','field':'cognition'}
  class Fake:
   def __init__(self):self.roles=[]
   def call(self,role,*args):
    self.roles.append(role);return {'parsed':{'answer':'no','evidence':'','reason':'Wrong sense.'}}
  f=Fake()
  with patch('retune_pilot.validate_packet'):
   result=process(row,[p],f,{},[],set())
  self.assertEqual(f.roles,['fit']);self.assertFalse(result['attempts']);self.assertIsNone(result['accepted'])
 def test_reused_calibration_retains_actual_parent_registration(self):
  from retune_api import Client
  from hybrid_redraft import atomic
  p=controls()[0]['packet'];body=request_for('fit',p,'cognition');value={'answer':'yes','evidence':'retain','reason':'Meaning explained.'}
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);parent=root/'parent';dest=root/'new'
   pm={'line':'parent'};pm['registration_hash']=digest(pm);atomic(parent/'registration.json',pm)
   r={'evidence_kind':'OpenAI API','receipt_id':'real-parent','registration_hash':pm['registration_hash'],'role':'fit','model':MODELS['fit'],'request_hash':digest(body),'packet_hash':p['packet_hash'],'request':body,'response':{'id':'chatcmpl-parent','model':MODELS['fit'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps(value)}}],'usage':{'prompt_tokens':100,'completion_tokens':10}},'paid_usd':.000315}
   saved={k:r[k] for k in ('model','receipt_id','request_hash','registration_hash','packet_hash','paid_usd')};saved.update(parsed=value,receipt_hash=digest(r))
   atomic(parent/'receipts'/'real-parent.json',r);atomic(parent/'calls'/('fit-'+digest(body)+'.json'),saved)
   m={'registration_hash':'different-child','calibration_parent':'parent'};c=Client(m,dest,root/'test-budget.sqlite')
   with patch.object(c,'verify'),patch('retune_api.ROOT',root),patch('urllib.request.build_opener') as http:
    result=c.call('fit',p,'cognition');http.assert_not_called()
   self.assertEqual(result['registration_hash'],pm['registration_hash']);self.assertEqual(result['receipt_id'],'real-parent');self.assertEqual(c.budget.summary()['calls_reserved'],0)
 def test_control_separates_dictionary_scope_from_semantic_support(self):
  ribosome=next(r for r in controls() if r['packet']['term']=='ribosome')
  self.assertFalse(ribosome['expected_fit']);self.assertTrue(ribosome['expected_read'])
 def test_future_run_cannot_finish_without_context_qualification(self):
  import audit_pilot_source_context as context
  from retune_pilot import execute
  from hybrid_redraft import atomic
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)
   def qualify():atomic(context.DEST/'report.json',{'qualified':1,'pass_fraction':.002,'field_review_required':0})
   with patch('retune_pilot.inputs',return_value=({'source_context_qualification_required':True},None,None,None)),patch('retune_pilot.calibrate',return_value={'passed':True}),patch('retune_pilot.run_phase'),patch('retune_pilot.report',return_value={'total_passed':2,'headwords':500}),patch.object(context,'PARENT',context.PARENT),patch.object(context,'DEST',context.DEST),patch.object(context,'prepare') as prepare_context,patch.object(context,'run',side_effect=qualify) as run_context:
    execute(dest);prepare_context.assert_called_once();run_context.assert_called_once()
   state=json.loads((dest/'run-state.json').read_text());self.assertEqual(state['qualified'],1);self.assertEqual(state['total_passed'],2)
 def test_receipt_audit_detects_changed_verdict_cost_and_source(self):
  p=controls()[0]['packet'];body=request_for('fit',p,'cognition');value={'answer':'yes','evidence':'retain','reason':'Definition present.'}
  m={'registration_hash':'a'*64};usage={'prompt_tokens':100,'completion_tokens':10}
  r={'evidence_kind':'OpenAI API','receipt_id':'r','registration_hash':m['registration_hash'],'role':'fit','model':MODELS['fit'],'request_hash':digest(body),'packet_hash':p['packet_hash'],'request':body,'response':{'id':'chatcmpl-test','model':MODELS['fit'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps(value)}}],'usage':usage},'paid_usd':.000315}
  saved={k:r[k] for k in ('model','receipt_id','request_hash','registration_hash','packet_hash','paid_usd')};saved.update(parsed=value,receipt_hash=digest(r))
  audit_saved(saved,r,m,'fit',p,'cognition')
  for change in ({'parsed':{**value,'answer':'no'}},{'paid_usd':0},{'receipt_hash':'b'*64}):
   with self.assertRaises(ValueError):audit_saved({**saved,**change},r,m,'fit',p,'cognition')
if __name__=='__main__':unittest.main()
