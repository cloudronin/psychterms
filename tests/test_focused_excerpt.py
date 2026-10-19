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
 def test_embedded_substring_cannot_displace_the_requested_whole_word(self):
  source='database '*400+'Data is information collected for analysis. '+'context '*300
  text,start,end=focused_excerpt(source,'data');self.assertRegex(text,r'\bData\b');self.assertEqual(source[start:end],text)
 def test_absent_term_never_creates_a_packet(self):
  self.assertEqual(focused_excerpt('Unrelated material.','working memory'),(None,None,None))
 def test_acronym_never_matches_an_ordinary_lowercase_word(self):
  self.assertEqual(focused_excerpt('People may attend appointments at a clinic and ask who provides care.','AT'),(None,None,None))
 def test_government_packet_requires_a_definition_anchor(self):
  self.assertEqual(focused_excerpt('Find information about mental health. Time with a provider can help.','information',require_explanation=True),(None,None,None))
  source='A panic attack is a sudden episode of intense fear with physical symptoms.'
  self.assertEqual(focused_excerpt(source,'panic attack',require_explanation=True),(source,0,len(source)))
 def test_expanded_acronym_is_a_government_anchor(self):
  source='Attention-deficit/hyperactivity disorder (ADHD) affects attention and activity.'
  self.assertEqual(focused_excerpt(source,'ADHD',require_explanation=True),(source,0,len(source)))
if __name__=='__main__':unittest.main()
