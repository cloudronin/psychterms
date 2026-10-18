import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import ROOT,load_inputs,semantic_hash,validate_corpus,validate_entry,digest
from export import build
from import_markdown import audit
from judge_contract import accepted
from seed_terms import parse_mesh,relevant
from check_packets import validate_packet

class PipelineTests(unittest.TestCase):
 def setUp(self):self.entries,self.sources,self.fields=copy.deepcopy(load_inputs());self.entries=[e for e in self.entries if e.get('fixture') is True]
 def resigned(self,e):e['hash']=semantic_hash(e);return e
 def reviewed(self):
  e=copy.deepcopy(self.entries[0]);e['review_status']='accepted'
  e['reviews']=[{'model':model,'passed':True,'entry_hash':e['hash'],'packet_hash':e['packet_hash'],'receipt_id':f'test-{model}','rubric_hash':'a'*64} for model in ['judge-a','judge-b']]
  return e
 def test_preview_valid(self):self.assertEqual(validate_corpus(self.entries,self.sources,self.fields)['entries'],3)
 def test_fixture_parser_excludes_intro_and_footer(self):
  s='# Title\n\nText\n\n## Dictionary\n\n#### One\n<a id="e00001"></a>\n\nOne definition.\n\n## Biographies\n\n#### Person\n<a id="e00002"></a>\n\nA biography.\n\n## Open References\n\nsource'
  self.assertEqual(audit(s),{'parsed_entries':2,'unique_ids':2,'duplicate_ids':0,'sections':{'dictionary':1,'biographies':1},'fixture_only':True,'content_exported':False})
 def test_fixture_audit_never_exports_text_or_terms(self):
  result=json.dumps(audit('#### SECRET HEADWORD\n<a id="e00001"></a>\n\nPRIVATE TEXT.'))
  self.assertNotIn('SECRET',result);self.assertNotIn('PRIVATE',result);self.assertNotIn('e00001',result)
 def test_duplicate_ids_rejected(self):
  with self.assertRaisesRegex(ValueError,'Duplicate IDs'):validate_corpus(self.entries+[self.entries[0]],self.sources,self.fields)
 def test_broken_link_rejected(self):
  self.entries[0]['also_see']=['missing'];self.resigned(self.entries[0])
  with self.assertRaisesRegex(ValueError,'Unresolved'):validate_corpus(self.entries,self.sources,self.fields)
 def test_hash_changes_only_with_semantics(self):
  e=self.entries[0];old=e['hash'];e['version']+=1;self.assertEqual(semantic_hash(e),old);e['definition']+=' Added text.';self.assertNotEqual(semantic_hash(e),old)
 def test_exports_identical_for_reordered_input(self):self.assertEqual(build(self.entries,history={}),build(list(reversed(self.entries)),history={}))
 def test_markdown_and_json_terms_definitions_agree(self):
  data,md,_=build(self.entries,history={})
  for e in data['entries']:self.assertIn('## '+e['term']+'\n',md);self.assertIn(e['definition'],md)
 def test_preview_cannot_release(self):
  with self.assertRaisesRegex(ValueError,'Preview'):validate_corpus(self.entries,self.sources,self.fields,release=True)
 def test_both_distinct_judges_required(self):
  e=self.reviewed();self.assertTrue(accepted(e));e['reviews'][1]['model']='judge-a';self.assertFalse(accepted(e))
 def test_one_judge_no_is_failure(self):
  e=self.reviewed();e['reviews'][1]['passed']=False;self.assertFalse(accepted(e))
 def test_edit_invalidates_both_judges(self):
  e=self.reviewed();e['definition']+=' A change.';self.resigned(e);self.assertFalse(accepted(e))
 def test_packet_change_invalidates_judges(self):
  e=self.reviewed();e['packet_hash']='b'*64;self.assertFalse(accepted(e))
 def test_related_link_is_not_drafting_basis(self):
  e=self.entries[0];e['provenance'][0]['role']='related_topic';self.resigned(e)
  with self.assertRaisesRegex(ValueError,'No permitted drafting basis'):validate_entry(e,self.sources,self.fields)
 def test_disallowed_source_never_becomes_drafting_basis(self):
  e=self.entries[0];e['sources']=['noba'];e['provenance'][0]['source']='noba';self.resigned(e)
  with self.assertRaisesRegex(ValueError,'Unpermitted'):validate_entry(e,self.sources,self.fields)
 def test_dose_prefilter(self):
  e=self.entries[0];e['definition']='Take 5 mg daily.';self.resigned(e)
  with self.assertRaisesRegex(ValueError,'Dose'):validate_entry(e,self.sources,self.fields)
 def test_four_sentences_rejected(self):
  e=self.entries[0];e['definition']='One. Two. Three. Four.';self.resigned(e)
  with self.assertRaisesRegex(ValueError,'three sentences'):validate_entry(e,self.sources,self.fields)
 def test_mesh_equivalence_not_broader_aliases(self):
  record=parse_mesh('*NEWRECORD\nUI = D999999\nMH = Independent example\nMS = A source concept.\nMN = F02.1\nENTRY = True alias|T1|EQV\nENTRY = Broader label|T2|BRD\nENTRY = Inverted, Name|T3|EQV')[0]
  self.assertEqual(record['aliases'],['True alias']);self.assertTrue(relevant(record))
 def test_unrelated_mesh_tree_excluded(self):self.assertFalse(relevant({'tree_numbers':['A01.234']}))
 def test_sources_fail_closed(self):
  for source in self.sources.values():
   if source['decision']=='yes':self.assertTrue(source['licence_confirmed']);self.assertTrue(source['licence_source_url'].startswith('https://'))
 def test_schema_agrees_with_fixture_shape(self):
  schema=json.loads((ROOT/'schema/entry.schema.json').read_text())
  for e in self.entries:self.assertFalse(set(e)-set(schema['properties']));self.assertTrue(set(schema['required'])<=set(e))
 def test_packet_tampering_rejected(self):
  packet=json.loads((ROOT/'data/packets/attention.json').read_text());packet['text']='An unrelated definition.'
  with self.assertRaisesRegex(ValueError,'Packet hash mismatch'):validate_packet(packet,self.sources)
 def test_packet_from_excluded_source_rejected(self):
  packet=json.loads((ROOT/'data/packets/attention.json').read_text());packet['source']='noba'
  with self.assertRaisesRegex(ValueError,'Unpermitted packet'):validate_packet(packet,self.sources)
 def test_single_domain_and_owner(self):
  config=json.loads((ROOT/'data/site-config.json').read_text())
  self.assertEqual(config['name'],'PsychTerms');self.assertEqual(config['domain'],'psychterms.org')
  self.assertEqual(config['owner'],'Vishnu Vettrivel');self.assertTrue(config['custom_domain_active'])
  self.assertFalse((ROOT/'site/public/CNAME').exists())
 def test_risk_classification_is_hash_bound(self):
  e=self.entries[0];before=e['hash'];e['risk']=True
  self.assertNotEqual(semantic_hash(e),before);self.resigned(e)
  validate_entry(e,self.sources,self.fields)
 def test_risk_classification_cannot_be_false(self):
  e=self.entries[0];e['risk']=False;self.resigned(e)
  with self.assertRaisesRegex(ValueError,'removed by hand'):validate_entry(e,self.sources,self.fields)
 def test_unreviewed_scene_cannot_enter_public_data(self):
  e=self.entries[0];e['vignette']={'card_id':'scenario:mockup','text':'Never publish this story.'};self.resigned(e)
  with self.assertRaisesRegex(ValueError,'reviewed unbound-card'):validate_entry(e,self.sources,self.fields)
  e['risk']=True;self.resigned(e)
  with self.assertRaisesRegex(ValueError,'Risk entry cannot'):validate_entry(e,self.sources,self.fields)
 def test_no_count_target_or_deadline(self):
  policy=json.loads((ROOT/'data/release-policy.json').read_text());self.assertIsNone(policy['count_target']);self.assertIsNone(policy['deadline']);self.assertEqual(policy['judges_required'],2)

if __name__=='__main__':unittest.main()
