import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recover_nimh_sources import parse_page
from scope_rules import decide

class NimhRecoveryTests(unittest.TestCase):
 def test_only_own_main_paragraphs_are_used(self):
  raw=b'<html><header><p>SECRET HEADER</p></header><main><h1>Panic disorder</h1><p>A panic attack is an abrupt wave of intense fear.</p><figure><p>SECRET CAPTION</p></figure><blockquote><p>SECRET CASE</p></blockquote><p>Other people can experience occasional attacks.</p></main><footer><p>SECRET FOOTER</p></footer></html>'
  title,text,_=parse_page(raw);self.assertEqual(title,'Panic disorder');self.assertNotIn('SECRET',text)
 def test_page_specific_rights_exception_prevents_admission(self):
  with self.assertRaises(ValueError):parse_page(b'<main><h1>Publication</h1><p>Original body.</p><p>All rights reserved.</p></main>')
 def test_clinical_page_context_is_not_lost_in_a_short_definition(self):
  packet={'source':'nimh-page-test','source_record':'https://www.nimh.nih.gov/health/publications/test','source_label':'Panic Disorder','term':'panic attack','text':'A panic attack is an abrupt wave of intense fear.'}
  result=decide(packet);self.assertTrue(result['eligible']);self.assertEqual(result['field'],'mental health')
if __name__=='__main__':unittest.main()
