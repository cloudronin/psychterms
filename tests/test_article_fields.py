import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from scope_rules import decide

class ArticleFieldTests(unittest.TestCase):
 def packet(self,term):return {'source':'article-pmc123','source_record':'10.1/test','term':term,'source_label':'Learning and emotion in the brain','text':'Learning and emotion regulation are studied using factor analysis, linear regression and working memory tasks.'}
 def test_requested_concept_takes_precedence_over_broad_article_context(self):
  for term,field in [('factor analysis','research methods'),('linear regression','research methods'),('working memory','cognition'),('anxiety','mental health')]:
   with self.subTest(term=term):self.assertEqual(decide(self.packet(term))['field'],field)
 def test_gene_alias_cannot_stand_in_for_a_psychology_word(self):
  packet=self.packet('WISH');packet['text']='The WISH gene affects neuronal development and learning.'
  self.assertFalse(decide(packet)['eligible'])
 def test_unqualified_regression_not_assumed_statistical(self):
  packet=self.packet('regression');packet['source_label']='Psychotherapy and defence mechanisms';packet['text']='Psychotherapy discusses regression as a defence mechanism.'
  self.assertNotEqual(decide(packet)['field'],'research methods')
if __name__=='__main__':unittest.main()
