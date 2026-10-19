import csv,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from term_meaning_rule import source_relative_fault,TERM_MEANING_CHECK
from retune_protocol import DRAFT,READ,validate_value
from audit_pilot_source_context import PROMPT
from retune_api import request_for
from retune_controls import controls
from revise_pilot_after_claude import import_verdicts,EXCLUDED
class TermMeaningTests(unittest.TestCase):
 def test_drafter_and_both_reader_paths_have_the_named_rule(self):
  self.assertIn('in this article',DRAFT)
  self.assertIn(TERM_MEANING_CHECK,READ);self.assertIn(TERM_MEANING_CHECK,PROMPT)
  for role in ('reader_a','reader_b'):
   self.assertIn(TERM_MEANING_CHECK,request_for(role,controls()[0]['packet'],'cognition','A definition.')['messages'][0]['content'])
 def test_source_relative_language_cannot_draft_or_get_a_pass(self):
  for phrase in ('In this article','In this study','In this source','In this packet','Here refers to','As used in','In the source packet','The study found'):
   definition=phrase+' memory means recall.'
   self.assertTrue(source_relative_fault(definition))
   with self.assertRaises(ValueError):validate_value('draft',{'definition':definition,'field':'cognition','packet_sufficient':True},'recall')
   with self.assertRaises(ValueError):validate_value('reader_b',{'passed':True,'reasons':[],'field_issue':'','support':[{'claim':'recall','evidence':'recall'}]},'recall',definition)
  self.assertFalse(source_relative_fault('Memory is the ability to retain and retrieve information.'))
 def test_semantic_controls_include_narrowing_without_banned_phrases(self):
  narrow=[r for r in controls() if r['definition']=='Memory is recall of a 20-word list after five minutes.']
  self.assertEqual(len(narrow),1);self.assertFalse(narrow[0]['expected_read']);self.assertFalse(source_relative_fault(narrow[0]['definition']))
 def test_verdict_import_exact_identity_and_all_retags(self):
  keys=['term'+str(i) for i in range(68)]+sorted(EXCLUDED);cohort=[];outcomes={};verdicts=[]
  for i,k in enumerate(keys):
   cohort.append({'headword_key':k,'accepted':{'entry':{'id':'id'+str(i),'field':'cognition','definition':'Exact draft'},'packet':{'packet_hash':'packet'+str(i)}}});outcomes[k]={'qualified':True}
   verdicts.append({'entry_id':'id'+str(i),'headword_key':k,'verdict':'PASS' if i<44 else 'FAIL','reason':'Editorial reason','suggested_field':'social' if i<20 else ''})
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'verdicts.csv'
   def save():
    with p.open('w',newline='') as f:
     w=csv.DictWriter(f,fieldnames=list(verdicts[0]));w.writeheader();w.writerows(verdicts)
   save();d=import_verdicts(p,cohort,outcomes,['social','cognition'])
   self.assertEqual(sum(r['staged_status']=='redraft' for r in d),24);self.assertEqual(sum(r['staged_status']=='dropped' for r in d),2);self.assertEqual(sum(r['resolved_field']=='social' for r in d),20)
   verdicts[0]['headword_key']='another term';save()
   with self.assertRaises(ValueError):import_verdicts(p,cohort,outcomes,['social','cognition'])
if __name__=='__main__':unittest.main()
