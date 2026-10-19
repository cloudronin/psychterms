import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_redraft_batch import choose_candidates
class BatchTests(unittest.TestCase):
 def packet(self,text,label='Paper title',source='article'):
  return {'text':text,'source_label':label,'source':source}
 def test_duplicate_passages_do_not_consume_two_slots(self):
  p=self.packet('A passage');q=self.packet('A   passage')
  chosen=choose_candidates([p,q,self.packet('Another passage')],'memory')
  self.assertEqual(len(chosen),2)
 def test_exact_label_wins_over_incidental_paper_mention(self):
  paper=self.packet('Paper passage');exact=self.packet('Definition','Memory','glossary')
  chosen=choose_candidates([paper,exact],'memory',1)
  self.assertEqual(chosen,[exact])
 def test_direct_government_material_precedes_incidental_paper(self):
  government=self.packet('Government passage','Health topic','medlineplus-health-topics')
  chosen=choose_candidates([self.packet('Paper passage'),government],'memory',1)
  self.assertEqual(chosen,[government])
 def test_candidate_cap_is_five(self):
  self.assertEqual(len(choose_candidates([self.packet(str(i)) for i in range(9)],'memory')),5)
if __name__=='__main__':unittest.main()
