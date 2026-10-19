import hashlib,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recover_approved_sources import FAMILIES,medline_records,hpo_reference_index,cdc_url,in_medline_scope,cdc_record
from prepare_reference_packets import options
from prepare_local_redrafts import permitted
class ApprovedSourceTests(unittest.TestCase):
 def test_only_three_new_families_and_cdc_roots(self):
  self.assertEqual(FAMILIES,{'medlineplus-health-topics','cdc-mental-health-substance-use','hpo-2026-09-01'})
  for url in ('https://www.cdc.gov/mental-health/about/index.html','https://www.cdc.gov/overdose-prevention/about/index.html'):self.assertTrue(cdc_url(url))
  for url in ('https://openmd.com/dictionaries','https://www.cdc.gov/cancer/about/index.html','https://www.cdc.gov.evil.example/mental-health/','https://other.example/mental-health/'):self.assertFalse(cdc_url(url))
 def test_medline_only_scoped_english_full_summary_no_licensed_external_text(self):
  xml=b'''<health-topics date-generated="2026-10-17"><health-topic id="1" title="Anxiety" language="English" url="https://medlineplus.gov/anxiety.html"><full-summary>&lt;p&gt;Anxiety involves apprehension or fear in anticipation of a possible threat.&lt;/p&gt;</full-summary><group>Mental Health and Behavior</group><also-called>Apprehension</also-called><site-record><information-category>Medical Encyclopedia</information-category><text>Licensed vendor prose must never be imported.</text></site-record></health-topic><health-topic id="2" title="Kidney Disease" language="English"><full-summary>Kidney disease is a condition that affects renal function.</full-summary><group>Kidney Diseases</group></health-topic></health-topics>'''
  rows=medline_records(xml,'https://medlineplus.gov/xml/file.xml');self.assertEqual(len(rows),1);self.assertIn('Apprehension',rows[0]['aliases']);self.assertNotIn('Licensed',rows[0]['text']);self.assertFalse(in_medline_scope('Kidney Disease',['Kidney Diseases']))
 def test_hpo_is_reference_only_scoped_view_preserving_original_parent_ids(self):
  raw=b'''format-version: 1.2\n[Term]\nid: HP:0011446\nname: Abnormality of mental function\n\n[Term]\nid: HP:0012759\nname: Neurodevelopmental abnormality\n\n[Term]\nid: HP:9999991\nname: Abnormal behavior\nsynonym: "Behavioural anomaly" EXACT []\nis_a: HP:0011446 ! Abnormality of mental function\n\n[Term]\nid: HP:9999992\nname: Renal anomaly\n'''
  index=hpo_reference_index(raw);self.assertTrue(index['reference_only']);self.assertEqual(len(index['records']),3);record=next(r for r in index['records'] if r['id']=='HP:9999991');self.assertEqual(record['parents'],['HP:0011446']);self.assertEqual(record['aliases'],['Behavioural anomaly']);self.assertFalse(any('definition' in r for r in index['records']))
 def test_page_level_copyright_mark_blocks_entire_cdc_page(self):
  raw=b'<main><h1>Topic</h1><p>A substantive paragraph describing a mental health concept in several words.</p></main><footer>Copyright 2026 Vendor</footer>'
  with self.assertRaises(ValueError):cdc_record('https://www.cdc.gov/mental-health/about/index.html',raw)
 def test_recorded_hpo_licence_matches_verbatim_public_file(self):
  from core import ROOT
  sources={s['id']:s for s in json.loads((ROOT/'data/sources.json').read_text())['sources']}
  source=sources['hpo-2026-09-01']
  self.assertEqual(hashlib.sha256((ROOT/source['licence_text_path']).read_bytes()).hexdigest(),source['licence_text_sha256'])
  self.assertNotIn('draft_basis',source['roles']);self.assertEqual(source['decision'],'yes')
 def test_hpo_custom_permission_never_becomes_cc_by_drafting_basis(self):
  self.assertFalse(permitted({'decision':'yes','licence':'HPO-attribution-integrity','licence_confirmed':True,'roles':['aliases','links','related_topic']}))
 def test_redirect_aliases_do_not_use_two_candidate_slots(self):
  row={'term':'Motivation','field':'mental health','failed_entry_ids':['old']}
  text='Motivation is the drive to initiate and maintain purposeful actions.'
  base={'source_id':'cdc-mental-health-substance-use','term':'Motivation','aliases':[],'text':text,'revision':'1','snapshot_sha256':'a'*64,'url':'https://www.cdc.gov/mental-health/','source_kind':'cdc_original_mental_health_substance_use_page'}
  records=[{**base,'record_id':'canonical'},{**base,'record_id':'redirect-alias'}]
  sources={'cdc-mental-health-substance-use':{'id':'cdc-mental-health-substance-use','licence':'public-domain-US-government'}}
  with patch('prepare_reference_packets.validate_packet'):packets,_=options(row,records,{'records':[]},sources,[])
  self.assertEqual(len(packets),1)
 def test_alias_lookup_never_puts_hpo_prose_into_government_packet(self):
  row={'term':'Abulia','headword_key':'abulia','field':'mental health','failed_entry_ids':['old']}
  hpo={'records':[{'id':'HP:test','term':'Abulia','aliases':['Loss of motivation']}],'version':'1','snapshot_sha256':'b'*64}
  records=[{'source_id':'medlineplus-health-topics','record_id':'one','term':'Loss of motivation','aliases':[],'text':'Loss of motivation is a marked reduction in the drive to initiate actions.','revision':'1','snapshot_sha256':'a'*64,'url':'https://medlineplus.gov/test.html','source_kind':'medlineplus_nlm_owned_health_topic_summary'}]
  sources={'medlineplus-health-topics':{'id':'medlineplus-health-topics','licence':'public-domain-US-government'}}
  with patch('prepare_reference_packets.validate_packet'):packets,references=options(row,records,hpo,sources,[])
  self.assertEqual(len(packets),1);self.assertEqual(packets[0]['text'],records[0]['text']);self.assertEqual(packets[0]['source'],'medlineplus-health-topics');self.assertEqual(references[0]['id'],'HP:test')
if __name__=='__main__':unittest.main()
