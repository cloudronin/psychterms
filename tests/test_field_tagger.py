import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from field_tagger import DEFINITIONS,validate
from retune_api import request_for
from retune_pilot import process
from core import digest,ROOT
from redraft_policy import candidate_pool
class FieldTests(unittest.TestCase):
 def value(self,field=None,confident=False,context='other',evidence=''):
  return {'field':field,'confident':confident,'paper_context':context,'context_evidence':evidence,'reason':'Classify the headword meaning.'}
 def test_all_fourteen_fields_have_definitions(self):
  self.assertEqual(set(DEFINITIONS),set(json.loads((ROOT/'data/fields.json').read_text())['fields']))
  self.assertEqual(len(DEFINITIONS),14);self.assertTrue(all('\n' not in s and s.strip() for s in DEFINITIONS.values()))
 def test_uncertainty_cannot_be_dumped_into_biology_or_methods(self):
  for field in ('biological','research methods','cognition'):
   with self.assertRaises(ValueError):validate(self.value(field), 'Source')
  validate(self.value(), 'Source')
  with self.assertRaises(ValueError):validate(self.value('cognition',True,evidence='Source'), 'Source')
  validate(self.value('biological',context='lab',evidence='Laboratory study'), 'Laboratory study of neural mechanisms.')
  validate(self.value('research methods',context='methods',evidence='Methods paper'), 'Methods paper on sampling.')
  with self.assertRaises(ValueError):validate(self.value('biological',context='lab',evidence='Invented laboratory evidence'), 'Source')
 def test_confident_semantic_classification_does_not_require_lab_paper(self):
  validate(self.value('personality',True), 'Temperament concerns enduring individual differences.')
  with self.assertRaises(ValueError):validate(self.value(None,True), 'Source')
 def test_tagger_gets_no_inherited_field_or_claude_answer(self):
  p={'term':'trait','source':'s','source_record':'r','revision':'1','text':'Trait definition.','source_label':'Trait'}
  body=request_for('field',p,'biological');data=json.loads(body['messages'][1]['content'])
  self.assertNotIn('field',data);self.assertNotIn('expected_field',data);self.assertNotIn('definition',data)
  for field,meaning in DEFINITIONS.items():self.assertIn(field+': '+meaning,body['messages'][0]['content'])
 def test_abstention_holds_drafting_and_does_not_claim_missing_source(self):
  p={'term':'term','text':'Packet prose.','packet_hash':'original'}
  class Fake:
   m={'field_tagging_required':True}
   def __init__(self):self.roles=[]
   def call(self,role,*args):self.roles.append(role);return {'parsed':{'field':None,'confident':False}}
  f=Fake();out=process({'headword_key':'term','term':'term','field':'cognition'},[p],f,{},[],set())
  self.assertEqual(f.roles,['field']);self.assertEqual(out['reason'],'field review required');self.assertIsNone(out['accepted'])
 def test_new_field_is_used_for_fit_without_mutating_frozen_packet(self):
  p={'term':'term','text':'Packet prose.','planned_field':'cognition'};p['packet_hash']=digest(p);old=copy.deepcopy(p)
  class Fake:
   m={'field_tagging_required':True}
   def __init__(self):self.calls=[]
   def call(self,role,packet,field,*args):
    self.calls.append((role,copy.deepcopy(packet),field))
    return {'parsed':{'field':'social','confident':True}} if role=='field' else {'parsed':{'answer':'no','reason':'Meaning missing.','evidence':''}}
  f=Fake()
  with patch('retune_pilot.validate_packet'):process({'headword_key':'term','term':'term','field':'cognition'},[p],f,{},[],set())
  self.assertEqual(p,old);self.assertEqual(f.calls[1][2],'social');self.assertEqual(f.calls[1][1]['planned_field'],'social');self.assertNotEqual(f.calls[1][1]['packet_hash'],p['packet_hash'])
 def test_scope_excluded_headword_cannot_reenter_generated_pool(self):
  e={'status':'redraft','term':'Dry eyes','id':'old','packet_hash':'h'}
  self.assertEqual(candidate_pool([e],exclusions={'dry eyes'})['candidates'],[])
if __name__=='__main__':unittest.main()
