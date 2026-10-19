import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import digest
from redraft_policy import packet_rejected,candidate_pool,headword_key,disposition,packet_basis_hash,validate_replacements,LEGACY_SCOPE_REASON
from entry_status import check_forward,load_migration

class RedraftPolicyTests(unittest.TestCase):
 def rows(self):
  old={'id':'old','term':'Term','status':'redraft','packet_hash':'a'*64,
       'provenance':[{'source':'old'}],'reader_reviews':[{'receipt_id':'old-reader'}]}
  new={'id':'new','term':'Term','status':'candidate','packet_hash':'b'*64,
       'provenance':[{'source':'new'}],'redraft_of':['old']}
  packets={'old':{'id':'old','term':'Term','source':'source','source_record':'r','revision':'1','text':'Old source.'},
           'new':{'id':'new','term':'Term','source':'source','source_record':'r2','revision':'1','text':'Fresh source.','redraft_of':['old']}}
  return [old,new],packets
 def test_combining_forms_remain_distinct_headwords(self):
  self.assertNotEqual(headword_key('-scope'),headword_key('scope'))
  self.assertNotEqual(headword_key('ab-'),headword_key('ab'))
  self.assertEqual(headword_key('  Social  Support '),headword_key('social support'))
 def test_only_named_scope_reason_is_dropped_all_other_reasons_redraft(self):
  for reason in ['No psychology or counselling context established','No psychology or counselling context established.',LEGACY_SCOPE_REASON]:
   self.assertEqual(disposition(reason),'dropped')
  for reason in ['Unsupported claim.','Wrong headword sense.','Insufficient context for this particular sense.']:
   self.assertEqual(disposition(reason),'redraft')
 def test_both_failed_statuses_are_terminal_per_entry_not_per_headword(self):
  for status in ('dropped','redraft'):
   old={'status':status,'term':'Term','definition_hash':'original'}
   check_forward({'old':old},{'old':old,'new':{'status':'candidate','term':'Term'}})
   for new in (dict(old,status='candidate'),dict(old,definition_hash='edited'),dict(old,status='redraft' if status=='dropped' else 'dropped')):
    with self.assertRaises(ValueError):check_forward({'old':old},{'old':new},migration={})
 def test_pinned_migration_only_allows_exact_before_after_records(self):
  old={'status':'dropped','term':'Term','definition_hash':'original'}
  new=dict(old,status='redraft',new_packet_required=True)
  pin={'old':{'before':digest(old),'after':digest(new)}}
  check_forward({'old':old},{'old':new},migration=pin)
  with self.assertRaises(ValueError):check_forward({'old':old},{'old':dict(new,definition_hash='edited')},migration=pin)
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data/status-migrations').mkdir(parents=True)
   (root/'data/status-migrations/redraft-split-v1.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'pin differs'):load_migration(root)
 def test_headword_reenters_pool_without_failed_prose_and_leaves_once_replaced(self):
  rows,_=self.rows();pool=candidate_pool(rows[:1])['candidates']
  self.assertEqual(pool[0]['requirement'],'new packet required');self.assertEqual(pool[0]['status'],'candidate')
  self.assertEqual(pool[0]['failed_entry_ids'],['old']);self.assertNotIn('definition',pool[0])
  self.assertEqual(candidate_pool(rows)['candidates'],[])
  self.assertEqual(candidate_pool([dict(rows[0],status='dropped')])['candidates'],[])
 def test_fresh_entry_with_new_packet_provenance_and_no_inherited_reads(self):
  rows,packets=self.rows();validate_replacements(rows,packets)
  for change in ({'redraft_of':[]},{'packet_hash':'a'*64},{'provenance':rows[0]['provenance']},
                 {'reader_reviews':[{'receipt_id':'old-reader'}]}):
   bad=copy.deepcopy(rows);bad[1].update(change)
   with self.assertRaises(ValueError):validate_replacements(bad,packets)
 def test_new_id_or_administrative_changes_do_not_make_a_new_packet(self):
  rows,packets=self.rows();packets['new']={**packets['old'],'id':'new','redraft_of':['old'],'planned_field':'cognition','revision':'2','term':'TERM','text':'  OLD   source. '}
  self.assertEqual(packet_basis_hash(packets['new']),packet_basis_hash(packets['old']))
  with self.assertRaisesRegex(ValueError,'new source packet'):validate_replacements(rows,packets)
 def test_packet_preparation_requeues_headword_but_skips_its_failed_packet(self):
  import prepare_candidate_packets as prep
  source={'id':'mesh-2026','decision':'yes','roles':['draft_basis'],'licence':'CC0-1.0','pinned_version':'2026'}
  old={'id':'synthetic-topic','term':'Synthetic topic','source':'mesh-2026','source_record':'old',
       'revision':'2026','text':'Synthetic topic concerns memory and learning in this source description.'}
  records=[{'source_id':'mesh-2026','record_id':ident,'term':'Synthetic topic','aliases':[],
            'text':text,'snapshot_sha256':'a'*64,'url':'https://example.org/'+ident}
           for ident,text in [('old',old['text']),('fresh','Synthetic topic is a learning process supported by a new source passage.')]]
  row={'term':'Synthetic topic','production_scope':'term','status':'exact_label_source_candidate',
       'matches':[{'source':'mesh-2026','record_id':r['record_id']} for r in records]}
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp).resolve();(root/'data/packets').mkdir(parents=True);(root/'.private/audit').mkdir(parents=True)
   (root/'data/packets/synthetic-topic.json').write_text(json.dumps(old))
   (root/'data/redraft-candidates.json').write_text(json.dumps({'candidates':[{'term':'Synthetic topic','failed_entry_ids':['synthetic-topic']}]}))
   (root/'.private/audit/coverage.json').write_text(json.dumps([row]))
   with patch.object(prep,'ROOT',root),patch.object(prep,'load_inputs',return_value=([{'id':'synthetic-topic','term':'Synthetic topic'}],{'mesh-2026':source},[])),patch.object(prep,'load_records',return_value=records):
    prep.prepare(root/'.private/audit',root/'.private/out')
    packets=json.loads((root/'.private/out/packets.json').read_text())
    self.assertEqual(len(packets),1);self.assertEqual(packets[0]['source_record'],'fresh')
    self.assertNotEqual(packets[0]['id'],'synthetic-topic');self.assertEqual(packets[0]['redraft_of'],['synthetic-topic'])
 def test_editorial_packet_rejection_survives_metadata_changes_and_keeps_new_sources(self):
  rows,packets=self.rows()
  rejected=packet_basis_hash(packets['old'])
  outcomes={'term':{'requirement':'new general-sense packet required','excluded_packet_basis_hashes':[rejected]}}
  row=candidate_pool(rows[:1],outcomes,exclusions=set())['candidates'][0]
  self.assertEqual(row['requirement'],'new general-sense packet required')
  changed={**packets['old'],'id':'v3','planned_field':'cognition','revision':'2','term':'TERM','text':'  OLD   source. '}
  self.assertTrue(packet_rejected(changed,row))
  self.assertFalse(packet_rejected(packets['new'],row))
  self.assertFalse(packet_rejected(changed,{}))
 def test_scope_dropped_headword_cannot_be_redrafted_under_a_new_id(self):
  rows,packets=self.rows();rows[0]['status']='dropped'
  with self.assertRaisesRegex(ValueError,'Out-of-scope'):validate_replacements(rows,packets)

if __name__=='__main__':unittest.main()
