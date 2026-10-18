import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,load_inputs,digest
from source_citations import packet_citation,references
from export import build
class CitationTests(unittest.TestCase):
 def setUp(self):
  self.entries,self.sources,_=load_inputs();self.entries=[e for e in self.entries if e.get('fixture') is True];self.packet=json.loads((ROOT/'data/packets/attention.json').read_text())
 def test_exact_mesh_author_edition_identifier_and_url(self):
  ref=packet_citation(self.packet,self.sources)
  self.assertIn('U.S. National Library of Medicine.',ref['citation']);self.assertIn('2026',ref['citation'])
  self.assertIn('D001288',ref['citation']);self.assertEqual(ref['url'],self.packet['url'])
  self.assertEqual(ref['packet_hash'],self.packet['packet_hash']);self.assertEqual(ref['role_label'],'Drafting source')
 def test_background_is_not_support(self):
  ref=packet_citation(self.packet,self.sources,'related_topic');self.assertEqual(ref['role_label'],'Background reference only')
 def test_changed_packet_or_revision_rejected(self):
  self.packet['text']='Changed.'
  with self.assertRaisesRegex(ValueError,'Packet hash'):packet_citation(self.packet,self.sources)
  entry=copy.deepcopy(self.entries[0]);entry['provenance'][0]['revision']='different'
  with self.assertRaisesRegex(ValueError,'revision'):references([entry])
 def test_json_markdown_share_source_citation(self):
  data,md,_=build(self.entries,history={})
  for e in data['entries']:
   for ref in data['references'][e['id']]:self.assertIn(ref['citation'],md);self.assertIn(ref['url'],md)
if __name__=='__main__':unittest.main()
