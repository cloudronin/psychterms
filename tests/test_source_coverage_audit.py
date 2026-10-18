import unittest,sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from source_coverage_audit import norm,audit,passage_candidates,add_article_candidates
class CoverageTests(unittest.TestCase):
 def setUp(self):self.records=[{'source_id':'synthetic-source','record_id':'r1','term':'Working Memory','aliases':['Active memory'],'definition_available':True,'url':'https://example.org/r1'}]
 def test_aliases_are_retrieved_and_gaps_preserved(self):
  rows,r=audit([{'term':'active-memory'},{'term':'unmatched test term'}],self.records)
  self.assertEqual(rows[0]['status'],'exact_label_source_candidate');self.assertEqual(rows[1]['status'],'source_not_yet_found')
  self.assertFalse(rows[0]['meaning_verified']);self.assertEqual(r['headwords_checked'],2)
 def test_sense_qualifier_is_not_an_exact_match(self):
  rows,_=audit([{'term':'Working Memory (different sense)'}],self.records)
  self.assertEqual(rows[0]['status'],'related_candidate_needs_review')
 def test_anchor_without_definition_not_counted_as_drafting_source(self):
  self.records[0]['definition_available']=False
  rows,_=audit([{'term':'Working Memory','section':'biographies'}],self.records)
  self.assertEqual(rows[0]['status'],'exact_label_anchor_only');self.assertEqual(rows[0]['production_scope'],'excluded_biography')
 def test_possessive_variant_is_related_and_never_exact(self):
  self.records[0]['term']='Abney effect';self.records[0]['aliases']=[]
  rows,_=audit([{'term':'Abney’s effect'}],self.records)
  self.assertEqual(rows[0]['status'],'related_candidate_needs_review')
  self.assertFalse(rows[0]['meaning_verified'])
 def test_article_reference_does_not_become_a_definition_source(self):
  rows,_=audit([{'term':'Unmatched test term'}],self.records)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'article-records.json').write_text(json.dumps([{'term':'Unmatched test term','source':'synthetic-source','record_id':'paper-1','url':'https://example.org/paper','definition_available':False}]))
   add_article_candidates(rows,p)
  self.assertEqual(rows[0]['status'],'article_reference_candidate')
  self.assertFalse(rows[0]['meaning_verified']);self.assertFalse(rows[0]['matches'][0]['definition_available'])
 def test_passage_cache_rebuilds_when_record_positions_change(self):
  record=dict(self.records[0],text='A passage about active memory.',snapshot_sha256='one')
  unrelated=dict(record,record_id='unrelated',text='Different passage.',snapshot_sha256='two')
  with tempfile.TemporaryDirectory() as tmp:
   for records in ([record],[unrelated,record]):
    rows,_=audit([{'term':'active memory.'}],[])
    passage_candidates(rows,records,Path(tmp))
    self.assertEqual(rows[0]['matches'][0]['record_id'],'r1')
if __name__=='__main__':unittest.main()
