import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,load_inputs,validate_model_review,semantic_hash,digest
from check_packets import validate_packet
class ModelPreviewTests(unittest.TestCase):
 def setUp(self):
  entries,self.sources,_=load_inputs();self.entry=copy.deepcopy(next(e for e in entries if e.get('model_review')))
 def test_designated_model_matches_exact_definition(self):validate_model_review(self.entry)
 def test_edit_or_cherry_picked_other_judge_rejected(self):
  for change in ('definition','model','packet'):
   e=copy.deepcopy(self.entry)
   if change=='definition':e['definition']+=' Extra claim.'
   if change=='model':e['model_review']['model']='different-model'
   if change=='packet':e['model_review']['packet_hash']='a'*64
   with self.assertRaises(ValueError):validate_model_review(e)
 def test_public_packet_retains_original_content_binding(self):
  packet=json.loads((ROOT/'data/packets'/(self.entry['id']+'.json')).read_text());validate_packet(packet,self.sources)
  packet['text']='Unreviewed replacement';packet['packet_hash']=digest({k:v for k,v in packet.items() if k!='packet_hash'})
  with self.assertRaisesRegex(ValueError,'Original judged packet'):validate_packet(packet,self.sources)
 def test_publication_counts_and_holds(self):
  entries,_,_=load_inputs();reviewed=[e for e in entries if e.get('model_review')]
  self.assertEqual(len(reviewed),198);self.assertEqual(sum(e['editorial_status']=='wording_review_pending' for e in reviewed),12)
  self.assertFalse(any('vignette' in e for e in entries))
  self.assertFalse(any(e['term'] in ('Dissent and Disputes','Social Theory') for e in reviewed))
if __name__=='__main__':unittest.main()
