import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_pilot_source_context import body,validate,qualified,MODELS
class SourceContextTests(unittest.TestCase):
 def test_real_source_label_is_separate_from_requested_headword(self):
  row={'source_record_label':'Gene Therapy Product','publisher_aliases':['Gene therapy vector'],'accepted':{'packet':{'source':'s','source_record':'r','revision':'1','text':'A functional gene designed for targeted delivery.'},'entry':{'term':'gene therapy','field':'biological','definition':'Gene therapy is a functional gene.'}}}
  request=body('reader_a',row);data=json.loads(request['messages'][1]['content'])
  self.assertEqual(data['headword'],'gene therapy');self.assertEqual(data['source_record_label'],'Gene Therapy Product');self.assertEqual(data['publisher_aliases'],['Gene therapy vector'])
  self.assertNotIn('earlier_verdict',data);self.assertNotEqual(MODELS['reader_a'],MODELS['reader_b'])
 def test_supported_but_out_of_scope_does_not_qualify(self):
  v={'definition_supported':True,'sense_matches':True,'in_scope':False,'reasons':['Unrelated cell biology.'],'field_issue':''}
  validate(v);self.assertFalse(qualified(v))
  bad={**v,'reasons':[]}
  with self.assertRaises(ValueError):validate(bad)
 def test_all_three_questions_must_pass_and_reasons_must_agree(self):
  v={'definition_supported':True,'sense_matches':True,'in_scope':True,'reasons':[],'field_issue':'Review the taxonomy.'}
  validate(v);self.assertTrue(qualified(v))
  for key in ('definition_supported','sense_matches','in_scope'):
   invalid={**v,key:False}
   with self.assertRaises(ValueError):validate(invalid)
if __name__=='__main__':unittest.main()
