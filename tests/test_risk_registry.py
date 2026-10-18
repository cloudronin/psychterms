"""Registry flags cannot be erased by entry edits, missing coverage, or stale pins."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,load_inputs,semantic_hash,digest
from risk_registry import load_registry,derive,check_additions,prepare
from export import build
from export_allowlist import public_paths

class RiskTests(unittest.TestCase):
 def setUp(self):
  self.registry,self.pin=load_registry();self.entry=copy.deepcopy(next(e for e in load_inputs()[0] if e['id']=='attention'))
  self.packet=json.loads((ROOT/'data/packets/attention.json').read_text())
 def derive(self,**changes):
  e=copy.deepcopy(self.entry);e.update(changes);e['hash']=semantic_hash(e)
  return derive([e],self.registry,{e['id']:self.packet})[0]
 def repin_packet(self):
  self.packet['packet_hash']=digest({k:v for k,v in self.packet.items() if k!='packet_hash'})
  self.entry['packet_hash']=self.packet['packet_hash'];self.entry['hash']=semantic_hash(self.entry)
 def list_term(self,test=1):
  self.registry['terms'].append({'id':self.entry['id'],'names':[self.entry['term']],'anchors':[],'test':test,'reason':'Synthetic test case'})
 def test_nonrisk_unflagged_and_input_unmodified(self):
  old=copy.deepcopy(self.entry);result=self.derive();self.assertNotIn('risk',result);self.assertEqual(self.entry,old)
 def test_list_membership_generates_true(self):
  self.list_term();result=self.derive();self.assertIs(result['risk'],True);self.assertEqual(result['hash'],semantic_hash(result))
 def test_field_packet_signals_require_list_coverage(self):
  for signal in self.registry['rules']['packet_or_anchor_signals']:
   self.packet['text']='Synthetic '+signal+' marker.';self.repin_packet()
   for field in ('diagnosis','assessment'):
    with self.assertRaisesRegex(ValueError,'coverage missing'):self.derive(field=field)
 def test_unrelated_field_does_not_trigger_test_one(self):
  self.packet['text']='Research mentioning suicide.';self.repin_packet();self.assertNotIn('risk',self.derive(field='research methods'))
 def test_packet_anchor_signals_are_checked(self):
  self.packet['anchors']=['Firearm'];self.repin_packet()
  with self.assertRaisesRegex(ValueError,'coverage missing'):self.derive(field='assessment')
 def test_named_duties_and_safety_practice_any_field(self):
  for name in ('Duty to warn','Duty to protect','Mandated reporting','Involuntary hold','Welfare check','Safety planning'):
   self.assertIs(self.derive(term=name)['risk'],True)
 def test_instrument_and_arcsim_exclusion_need_registry(self):
  for flag in ('risk_instrument','arcsim_no_risk_history_excluded'):
   with self.subTest(flag=flag):
    self.packet[flag]=True;self.repin_packet()
    with self.assertRaisesRegex(ValueError,'coverage missing'):self.derive()
    self.packet.pop(flag);self.repin_packet()
 def test_anchor_membership_carries_existing_exclusion(self):
  self.packet['source_record']='D000081042';self.repin_packet();self.assertIs(self.derive()['risk'],True)
 def test_flag_deletion_does_not_clear_membership(self):
  self.list_term();result=self.derive();result.pop('risk');result['hash']=semantic_hash(result)
  self.assertIs(derive([result],self.registry,{result['id']:self.packet})[0]['risk'],True)
 def test_manual_true_false_and_legacy_flags_rejected(self):
  for key,value in [('risk',False),('risk',True),('risk_term',False)]:
   with self.assertRaisesRegex(ValueError,'build-owned'):self.derive(**{key:value})
 def test_listed_entry_scene_rejected_without_source_flag(self):
  self.list_term()
  with self.assertRaisesRegex(ValueError,'cannot contain a scene'):self.derive(vignette={'text':'Synthetic scene'})
 def test_pin_detects_any_byte_change(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'data').mkdir()
   for name in ('risk_terms.json','risk-terms-pin.json'):(root/'data'/name).write_bytes((ROOT/'data'/name).read_bytes())
   load_registry(root)
   p=root/'data/risk_terms.json';p.write_bytes(p.read_bytes()+b' ')
   with self.assertRaisesRegex(ValueError,'pin is stale'):load_registry(root)
 def test_register_additive_and_versioned(self):
  old=copy.deepcopy(self.registry);new=copy.deepcopy(old);new['terms'].pop()
  with self.assertRaisesRegex(ValueError,'removed or weakened'):check_additions(old,new)
  new=copy.deepcopy(old);new['rules']['packet_or_anchor_signals'].pop()
  with self.assertRaisesRegex(ValueError,'weakened'):check_additions(old,new)
  new=copy.deepcopy(old);new['terms'].append({'id':'test','names':['test'],'anchors':[],'test':3,'reason':'test'})
  with self.assertRaisesRegex(ValueError,'version bump'):check_additions(old,new)
  new['version']+=1;check_additions(old,new)
 def test_modified_packet_and_entry_hash_cannot_be_hidden(self):
  self.packet['text']='Unpinned changes'
  with self.assertRaisesRegex(ValueError,'packet hash'):self.derive()
  e=copy.deepcopy(self.entry);e['definition']='Modified.'
  with self.assertRaisesRegex(ValueError,'Semantic hash'):derive([e],self.registry,{e['id']:self.packet})
 def test_public_scan_allows_risk_ids_and_still_blocks_keys(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'data').mkdir();p=root/'data/risk_terms.json'
   p.write_text('{"id":"risk-assessment-instrument"}')
   with patch('export_allowlist.ROOT',root):
    self.assertEqual(list(public_paths()),['data/risk_terms.json'])
    p.write_text('{"secret":"'+'sk-'+'x'*24+'"}')
    with self.assertRaisesRegex(ValueError,'secret-like'):list(public_paths())
 def test_export_records_registry_pin_and_exact_notice(self):
  self.list_term();e=self.derive()
  with patch('export.prepare',return_value=([e],self.pin)):
   data,md,manifest=build([self.entry],history={})
  self.assertEqual(data['risk_register'],self.pin);self.assertEqual(manifest['risk_register'],self.pin)
  self.assertIs(data['entries'][0]['risk'],True);self.assertEqual(md.count('No scene is provided for this risk term.'),1)

if __name__=='__main__':unittest.main()
