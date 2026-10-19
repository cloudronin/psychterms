import sys,json,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_recovered_packets import terminal_content_hashes

class RecoveryAttemptTests(unittest.TestCase):
 def test_alternate_declines_do_not_recycle_prior_source(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'declined.json'
   first=terminal_content_hashes({'term':{'status':'not_published','source_content_hash':'a'*64}},path)
   self.assertEqual(first,{'a'*64})
   second=terminal_content_hashes({'term':{'status':'not_published','source_content_hash':'b'*64}},path)
   self.assertEqual(second,{'a'*64,'b'*64})
   self.assertEqual(set(json.loads(path.read_text())),second)
 def test_success_is_not_a_failed_packet(self):
  with tempfile.TemporaryDirectory() as folder:
   self.assertEqual(terminal_content_hashes({'term':{'status':'candidate','source_content_hash':'a'*64}},Path(folder)/'declined.json'),set())
if __name__=='__main__':unittest.main()
