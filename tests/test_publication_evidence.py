"""Publication cannot turn raw model responses into unsupported passing reads."""
import copy,json,sys,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,digest
from publication_evidence import validate_bundle,validate_record,validate

class PublicationEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.path=next(p for p in sorted((ROOT/'data/publication-evidence').glob('*.json'))
                 if json.loads(p.read_text())['editorial_decision'] is None)
  self.bundle=json.loads(self.path.read_text())
  self.entry=json.loads((ROOT/'data/entries'/self.path.name).read_text())
  self.packet=self.bundle['packet']
 def test_actual_distinct_readers_and_source_bound_draft_validate(self):
  self.assertTrue(validate(self.entry,self.packet))
 def test_build_owned_badges_and_risk_flag_preserve_raw_evidence_binding(self):
  from core import semantic_hash
  e=copy.deepcopy(self.entry)
  e.update(status='judged',checks={'readers':'2/2','copy':'clear'},released=False,release_versions=[],drafter=e['draft_evidence']['model'],risk=True)
  e['hash']=semantic_hash(e)
  self.assertTrue(validate_bundle(e,self.packet,self.bundle))
 def test_missing_second_reader_cannot_publish(self):
  b=copy.deepcopy(self.bundle);b['records'].pop('reader_b')
  with self.assertRaisesRegex(ValueError,'two reading'):validate_bundle(self.entry,self.packet,b)
  e=copy.deepcopy(self.entry);e['reader_reviews']=e['reader_reviews'][:1]
  with self.assertRaises(ValueError):validate_bundle(e,self.packet,self.bundle)
 def test_changed_definition_or_source_cannot_reuse_receipts(self):
  e=copy.deepcopy(self.entry);e['definition']+=' Unsupported addition.'
  with self.assertRaises(ValueError):validate_bundle(e,self.packet,self.bundle)
  p=copy.deepcopy(self.packet);p['text']+=' Different source.'
  with self.assertRaises(ValueError):validate_bundle(self.entry,p,self.bundle)
 def test_rehashed_raw_pass_without_support_still_rejected(self):
  b=copy.deepcopy(self.bundle);r=b['records']['reader_a']
  parsed=r['saved']['parsed'];parsed['support']=[]
  r['receipt']['response']['choices'][0]['message']['content']=json.dumps(parsed)
  r['saved']['receipt_hash']=digest(r['receipt'])
  with self.assertRaisesRegex(ValueError,'quoted claim support'):
   validate_record(r,'reader_a',b['reviewed_entry'],self.packet)
 def test_corrupt_receipt_and_unbound_model_proof_rejected(self):
  b=copy.deepcopy(self.bundle);b['records']['draft']['receipt']['request_hash']='0'*64
  with self.assertRaisesRegex(ValueError,'receipt changed'):validate_bundle(self.entry,self.packet,b)
  e=copy.deepcopy(self.entry);e['reader_reviews'][0]['model']=e['draft_evidence']['model']
  with self.assertRaises(ValueError):validate_bundle(e,self.packet,self.bundle)
 def test_editorial_scope_read_resolves_missing_keywords_but_not_wrong_sense(self):
  from entry_status import prepare
  e=json.loads((ROOT/'data/entries/hypnotherapy-v2-c8f4a845d0.json').read_text())
  absent={'eligible':False,'rule':'no-psychology-counselling-neural-method-or-historical-context','reason':'Keyword screen found no context.'}
  with patch('entry_status.copy_results',return_value={e['id']:'clear'}),patch('entry_status.independent_records',return_value={}),patch('entry_status.validate_replacements'):
   with patch('entry_status.decide',return_value=absent):
    output,_=prepare([e],history={})
    self.assertEqual(output[0]['status'],'judged')
   with patch('entry_status.decide',return_value={**absent,'rule':'gene-record-sense-mismatch'}):
    output,_=prepare([e],history={})
    self.assertEqual(output[0]['status'],'redraft')
 def test_redundancy_failed_correction_not_promoted(self):
  self.assertFalse((ROOT/'data/entries/redundancy-v3-dfd79156c9.json').exists())
  decisions=json.loads((ROOT/'reports/cleared-redrafts-publication.json').read_text())
  self.assertEqual(decisions['new_entries'],123)
  self.assertNotIn('redundancy',{r['term'] for r in decisions['entries']})

if __name__=='__main__':unittest.main()
