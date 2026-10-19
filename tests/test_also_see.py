import copy,importlib.util,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from also_see import assemble,document_frequency,forms,mention_index,mentions,resolve,validate_graph,PARAMS

def entry(ident,term=None,definition='',field='cognition',packet=None,scope=None,aliases=()):
 return {'id':ident,'term':term or ident,'definition':definition,'field':field,'packet_hash':packet or ident,
     'provenance':[{'scope':scope or ident}],'aliases':list(aliases)}

class AlsoSeeTests(unittest.TestCase):
 def test_whole_words_case_aliases_and_singular_plural(self):
  rows=[entry('panic','panic attack',aliases=['acute fear episode']),entry('axis','axis'),entry('analysis','analysis')]
  trie=mention_index(rows,[])
  self.assertEqual(set(mentions('PANIC ATTACKS and an acute fear episode, axes and analyses.',trie)),{'panic','axis','analysis'})
  self.assertFalse(mentions('panicky attackers',trie))
 def test_short_aliases_stoplist_and_plural_stoplist_are_skipped(self):
  rows=[entry('memory','memory'),entry('short','ABC'),entry('other','something',aliases=['test']),entry('working','working memory')]
  trie=mention_index(rows,['memory','test'])
  self.assertEqual(set(mentions('ABC tests, memories and working memory.',trie)),{'working'})
 def test_mentions_are_directional_ordered_and_deduplicated(self):
  rows=[entry('a','Anchor','Repeated learning then social support then repeated learning.'),entry('b','social support'),entry('c','repeated learning')]
  links,_=assemble(rows,set(),{},[],{})
  self.assertEqual([r['to'] for r in links['a']],['c','b']);self.assertEqual(links['b'],[])
 def test_longest_phrase_precedes_earlier_shorter_mention(self):
  rows=[entry('a',definition='Support then social support then perceived social support.'),
    entry('short','support'),entry('medium','social support'),entry('long','perceived social support')]
  links,_=assemble(rows,set(),{},[],{})
  self.assertEqual([r['to'] for r in links['a']],['long','medium'])
 def test_frequency_boundary_unique_definitions_and_alias_cannot_bypass(self):
  rows=[entry('target','common concept',aliases=['special alias']),
    entry('alias-user',definition='Special alias.')]+[
    entry('d'+str(i),definition='Common concepts and common concept.') for i in range(40)]
  self.assertEqual(document_frequency(rows)['target'],40)
  links,_=assemble(rows,set(),{},[],{})
  self.assertEqual([r['to'] for r in links['alias-user']],['target'])
  rows.append(entry('forty-first',definition='Common concept.'))
  links,stats=assemble(rows,set(),{},[],{})
  self.assertEqual(document_frequency(rows)['target'],41)
  self.assertEqual(links['alias-user'],[])
  self.assertEqual(stats['mention_targets_over_frequency_limit'],1)
  self.assertEqual(stats['mention_pairs_frequency_rejected'],42)
  # The frequency filter applies to the mention signal, not embeddings.
  links,_=assemble(rows,set(),{},[],{'alias-user':[('target',.8)]})
  self.assertEqual(links['alias-user'],[{'to':'target','signal':'embedding','score':.8}])
 def test_frequency_includes_self_and_excludes_alias_occurrences(self):
  rows=[entry('target','common concept',definition='Common concept.',aliases=['special alias'])]+[
    entry('d'+str(i),definition='Special alias.') for i in range(50)]
  self.assertEqual(document_frequency(rows)['target'],1)
  links,_=assemble(rows,set(),{},[],{})
  self.assertEqual([r['to'] for r in links['d0']],['target'])
 def test_signal_priority_packet_only_source_cap_and_headword_ties(self):
  rows=[entry('a',definition='Mention target.',packet='p',scope='s'),entry('m','mention target'),
    entry('z','Zulu',packet='p'),entry('b','Alpha',packet='p'),entry('c','Bravo',packet='p'),
    entry('d','Charlie',packet='p'),entry('scope-only','Aardvark',scope='s'),entry('e','Echo')]
  links,_=assemble(rows,set(),{},[],{'a':[('e',.8)]})
  self.assertEqual([(r['to'],r['signal']) for r in links['a']],[('m','mention'),('b','same_source'),('c','same_source'),('d','same_source'),('e','embedding')])
  self.assertEqual(links['scope-only'],[])
 def test_mention_cap_embeddings_fill_global_cap_without_padding(self):
  rows=[entry('anchor',definition=' '.join('Target '+str(i) for i in range(8)))]+[entry('t'+str(i),'Target '+str(i)) for i in range(8)]+[entry('isolated')]
  links,_=assemble(rows,set(),{},[],{})
  self.assertEqual(len(links['anchor']),2);self.assertEqual(links['isolated'],[])
  links,_=assemble(rows,set(),{},[],{'anchor':[('t'+str(i),.9-i*.01) for i in range(8)]})
  self.assertEqual([r['signal'] for r in links['anchor']],['mention','mention','embedding','embedding','embedding'])
  self.assertEqual([r['to'] for r in links['anchor']],['t0','t1','t2','t3','t4'])
 def test_risk_blocking_all_signals_and_risk_source_can_link_out(self):
  rows=[entry('a',definition='Danger term.',scope='shared'),entry('risk','danger term',definition='Anchor term.',scope='shared'),entry('safe','anchor term')]
  links,stats=assemble(rows,{'risk'},{},[],{'a':[('risk',.95)],'risk':[('safe',.8)]})
  self.assertNotIn('risk',[r['to'] for r in links['a']]);self.assertTrue(links['risk'])
  self.assertEqual(stats['inbound_risk_blocked'],1)
 def test_embedding_threshold_field_filter_and_duplicate_skip(self):
  rows=[entry('a',definition='Mention target.'),entry('m','mention target'),entry('wrong',field='social'),entry('near'),entry('below')]
  links,stats=assemble(rows,set(),{},[],{'a':[('m',.99),('wrong',.95),('near',.60),('below',.599999)]})
  self.assertEqual([r['to'] for r in links['a']],['m','near']);self.assertEqual(stats['embedding_field_rejected'],1)
 def test_top20_is_global_not_backfilled_with_the_21st_same_field(self):
  rows=[entry('a')]+[entry('w'+str(i),field='social') for i in range(20)]+[entry('safe')]
  links,_=assemble(rows,set(),{},[],{'a':[(e['id'],.99-i*.001) for i,e in enumerate(rows[1:])]})
  self.assertEqual(links['a'],[])
 def test_redirect_resolution_precedes_risk_and_deduplication(self):
  rows=[entry('a'),entry('safe'),entry('risk')]
  links,_=assemble(rows,{'risk'},{'old-safe':'safe','old-risk':'risk'},[],{'a':[('old-safe',.9),('safe',.8),('old-risk',.7)]})
  self.assertEqual([r['to'] for r in links['a']],['safe'])
  with self.assertRaises(ValueError):resolve('x',{'x':'y','y':'x'})
 def test_model_free_build_validation_rejects_unsafe_or_stale_data(self):
  rows=[entry('a'),entry('b')];fp={'input_hash':'i','entry_set_hash':'e','risk_register':{'version':1}}
  graph={'params':PARAMS,**fp,'model_hash':'a'*64,'links':{'a':[{'to':'b','signal':'embedding','score':.7}],'b':[]}}
  self.assertEqual(validate_graph(graph,rows,set(),{},fp)['links'],1)
  for key,value in [('to','a'),('score',.59),('signal','unknown')]:
   bad=copy.deepcopy(graph);bad['links']['a'][0][key]=value
   with self.assertRaises(ValueError):validate_graph(bad,rows,set(),{},fp)
  with self.assertRaises(ValueError):validate_graph(graph,rows,{'b'},{},fp)
  with self.assertRaises(ValueError):validate_graph(graph,rows,set(),{},dict(fp,input_hash='changed'))
 def test_validation_rejects_scope_only_source_and_bad_mention_order_or_cap(self):
  rows=[entry('a',definition='Support and social support and perceived social support.',scope='shared'),
    entry('short','support',scope='shared'),entry('medium','social support'),entry('long','perceived social support')]
  fp={'input_hash':'i','entry_set_hash':'e','risk_register':{'version':1}}
  graph={'params':PARAMS,**fp,'model_hash':'a'*64,'links':{e['id']:[] for e in rows}}
  def link(target,signal='mention'):return {'to':target,'signal':signal,'score':None}
  graph['links']['a']=[link('long'),link('medium')]
  validate_graph(graph,rows,set(),{},fp)
  for bad_links in ([link('short','same_source')],[link('medium'),link('long')],[link('long'),link('medium'),link('short')]):
   bad=copy.deepcopy(graph);bad['links']['a']=bad_links
   with self.assertRaises(ValueError):validate_graph(bad,rows,set(),{},fp)
 def test_validation_rejects_frequent_mention_target(self):
  rows=[entry('target','common concept')]+[entry('d'+str(i),definition='Common concept.') for i in range(41)]
  fp={'input_hash':'i','entry_set_hash':'e','risk_register':{'version':1}}
  graph={'params':PARAMS,**fp,'model_hash':'a'*64,'links':{e['id']:[] for e in rows}}
  graph['links']['d0']=[{'to':'target','signal':'mention','score':None}]
  with self.assertRaisesRegex(ValueError,'frequency'):validate_graph(graph,rows,set(),{},fp)
 @unittest.skipUnless(importlib.util.find_spec('numpy'),'Optional local embedding dependency')
 def test_nearest_excludes_self_orders_global_cosines_and_breaks_ties_by_id(self):
  import numpy as np
  from build_also_see import nearest
  rows=[entry('a'),entry('b'),entry('c')]
  neighbours=nearest(rows,np.array([[1.,0.],[0.,1.],[0.,1.]]),k=2)
  self.assertEqual([i for i,s in neighbours['a']],['b','c'])
  self.assertEqual(neighbours['b'][0][0],'c')
 @unittest.skipUnless(importlib.util.find_spec('numpy'),'Optional local embedding dependency')
 def test_incremental_cache_embeds_only_new_or_changed_text(self):
  import numpy as np
  from build_also_see import encode
  calls=[]
  def embed(texts):
   calls.extend(texts);return np.array([[1.,0.] for _ in texts],dtype=np.float32)
  pin={'weights_sha256':'a'*64,'files':{}}
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);rows=[entry('a'),entry('b')]
   _,stats=encode(rows,root,pin,root/'cache',embed_batch=embed)
   self.assertEqual(stats,{'embedded':2,'reused':0});self.assertEqual(len(calls),2)
   _,stats=encode(rows,root,pin,root/'cache',embed_batch=embed)
   self.assertEqual(stats,{'embedded':0,'reused':2});self.assertEqual(len(calls),2)
   rows.append(entry('c'));_,stats=encode(rows,root,pin,root/'cache',embed_batch=embed)
   self.assertEqual(stats,{'embedded':1,'reused':2});self.assertEqual(len(calls),3)
   rows[0]['definition']='A changed definition.'
   _,stats=encode(rows,root,pin,root/'cache',embed_batch=embed)
   self.assertEqual(stats,{'embedded':1,'reused':2});self.assertEqual(len(calls),4)

if __name__=='__main__':unittest.main()
