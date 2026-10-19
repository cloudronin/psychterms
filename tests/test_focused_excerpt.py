import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_recovered_packets import focused_excerpt

class FocusedExcerptTests(unittest.TestCase):
 def test_definition_paragraph_precedes_an_incidental_abstract_mention(self):
  source='Our study measured working memory during learning.\n\nWorking memory is a system for temporarily holding and using information. It supports ongoing tasks.'
  text,start,end=focused_excerpt(source,'working memory')
  self.assertTrue(text.startswith('Working memory is'));self.assertEqual(source[start:end],text)
 def test_long_paragraph_is_bounded_and_ranges_reproduce_it(self):
  source='Leading background.\n\n'+'background '*300+'Working memory is temporary storage. '+'context '*500
  text,start,end=focused_excerpt(source,'working memory');self.assertIn('Working memory',text);self.assertLessEqual(len(text),2400);self.assertEqual(source[start:end],text)
 def test_absent_term_never_creates_a_packet(self):
  self.assertEqual(focused_excerpt('Unrelated material.','working memory'),(None,None,None))
if __name__=='__main__':unittest.main()
