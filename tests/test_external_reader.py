import copy,csv,io,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import digest,semantic_hash
from external_reader import evidence
from import_external_reader import plan

class ExternalReaderTests(unittest.TestCase):
 def setUp(self):
  self.entry={'id':'test','term':'Test','definition':'An original definition.','field':'ethics','version':1,
      'packet_hash':'a'*64,'sources':['source'],'provenance':[],'aliases':[],'also_see':[],
      'draft_evidence':{'model':'drafter'}}
  self.entry['hash']=semantic_hash(self.entry)
  self.packet={'id':'test','term':'Test','packet_hash':'a'*64,'text':'Original source background for the test.'}
  h=digest({'definition':self.entry['definition'],'field':'ethics','packet_sufficient':True})
  self.entry['reader_reviews']=[{'model':model,'draft_model':'drafter','passed':passed,'definition_hash':h,
      'packet_hash':'a'*64,'published_packet_hash':'a'*64,'receipt_id':'actual-'+model,
      'request_hash':'b'*64,'registration_hash':'c'*64,'reasons':[] if passed else ['Rejected.']}
      for model,passed in [('mini',True),('nano',False)]]
  self.row={'id':'test','term':'Test','verdict':'PASS','headword_fit':'yes','field':'suggest:research methods',
      'reason':'Source supports this definition.','passed_by':'mini','rejected_by':'nano','url':'https://psychterms.org/terms/test/'}
 def raw(self,rows=None):
  f=io.StringIO();w=csv.DictWriter(f,fieldnames=list(self.row));w.writeheader();w.writerows(rows or [self.row]);return f.getvalue().encode()
 def planned(self,raw=None):
  return plan(raw or self.raw(),[self.entry],{'test':self.packet},{'test':{'status':'reviewed'}},['ethics','research methods'])
 def fixture(self,root):
  m,edits=self.planned();folder=root/'data/external-reviews/test-batch';folder.mkdir(parents=True)
  (folder/'manifest.json').write_text(json.dumps(m));(folder/'verdicts.csv').write_bytes(self.raw())
  e=edits[0][1];e['external_review']={'batch':'test-batch','manifest_sha256':digest(m)};e['hash']=semantic_hash(e)
  return e
 def test_retag_preserves_actual_api_proofs_and_records_external_origin(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);entry=self.fixture(root);proof=evidence(entry,root)
   self.assertEqual(entry['reader_reviews'],self.entry['reader_reviews'])
   self.assertEqual(entry['version'],2);self.assertEqual(proof['reviewed_field'],'ethics')
   self.assertEqual(proof['approved_field'],'research methods');self.assertTrue(proof['passed'])
   self.assertNotIn('receipt_id',proof)
   built=dict(entry,risk=True);self.assertEqual(evidence(built,root),proof)
 def test_changed_definition_field_source_packet_or_version_cannot_reuse_import(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);entry=self.fixture(root)
   for key,value in [('definition','Changed.'),('field','ethics'),('sources',['other']),('packet_hash','d'*64),('version',3)]:
    changed=copy.deepcopy(entry);changed[key]=value
    with self.assertRaises(ValueError):evidence(changed,root)
 def test_tampered_csv_or_manifest_is_rejected(self):
  for name in ('verdicts.csv','manifest.json'):
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);entry=self.fixture(root);p=root/'data/external-reviews/test-batch'/name
    if name.endswith('.csv'):p.write_bytes(self.raw().replace(b'PASS',b'FAIL'))
    else:
     m=json.loads(p.read_text());m['reader_model']='Changed';p.write_text(json.dumps(m))
    with self.assertRaises(ValueError):evidence(entry,root)
 def test_duplicate_missing_unlisted_and_wrong_original_reader_rejected(self):
  for rows in ([self.row,self.row],[dict(self.row,id='outside')],[dict(self.row,passed_by='drafter')],[dict(self.row,field='suggest:unknown')]):
   with self.assertRaises((ValueError,KeyError)):self.planned(self.raw(rows))
 def test_fail_reason_and_field_are_imported_without_rewriting_definition(self):
  self.row.update(verdict='FAIL',headword_fit='no',reason='Wrong headword sense.')
  manifest,edits=self.planned()
  self.assertEqual(manifest['entries']['test']['verdict'],'FAIL')
  self.assertEqual(edits[0][1]['definition'],self.entry['definition'])
 def test_build_counts_third_reader_pass_and_failure(self):
  from entry_status import prepare
  for verdict,status in [('PASS','judged'),('FAIL','redraft')]:
   self.row.update(verdict=verdict)
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);entry=self.fixture(root);folder=root/'data/packets';folder.mkdir(parents=True)
    (folder/'test.json').write_text(json.dumps(self.packet))
    result,report=prepare([entry],root=root,history={},scope=False)
    self.assertEqual(result[0]['status'],status)
    self.assertIn('Claude (version unspecified; user-supplied review)',report['reader_models'])

if __name__=='__main__':unittest.main()
