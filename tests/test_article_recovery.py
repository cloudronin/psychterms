import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from recover_article_sources import parse_article

def article(licence='https://creativecommons.org/licenses/by/4.0/',extra='',group='contrib-group',contrib='contrib contrib-type="author"'):
 return f'''<article><front><article-meta><article-id pub-id-type="doi">10.1/test</article-id><title-group><article-title>Memory concepts</article-title></title-group><{group}><{contrib}><name><surname>Researcher</surname><given-names>A</given-names></name></contrib></contrib-group><pub-date><year>2024</year></pub-date><permissions><license><license-p>CC BY <ext-link href="{licence}">licence</ext-link></license-p></license></permissions><abstract><p>Memory is a set of processes used to retain information.</p></abstract></article-meta></front><body><sec sec-type="intro"><title>Introduction</title><p>Retrieval brings stored information back into awareness.</p>{extra}</sec><sec><title>Results</title><p>SECRET RESULTS</p></sec></body></article>'''.encode()

class ArticleRecoveryTests(unittest.TestCase):
 def test_own_notice_and_authors_are_pinned_results_excluded(self):
  source,record=parse_article(article(),'PMC1','10.1/test')
  self.assertEqual(source['licence'],'CC-BY-4.0');self.assertIn('Researcher A',source['candidate'])
  self.assertEqual(source['content_snapshot_sha256'],record['snapshot_sha256']);self.assertNotIn('SECRET RESULTS',record['text'])
 def test_noncommercial_sharealike_and_unversioned_not_inferred(self):
  for licence in ['https://creativecommons.org/licenses/by-nc/4.0/','https://creativecommons.org/licenses/by-sa/4.0/','Creative Commons Attribution']:
   with self.assertRaises(ValueError):parse_article(article(licence),'PMC1','10.1/test')
 def test_publisher_author_group_without_contrib_type(self):
  source,_=parse_article(article(group='contrib-group content-type="author"',contrib='contrib'),'PMC1','10.1/test');self.assertIn('Researcher A',source['candidate'])
 def test_inline_third_party_quotation_and_dictionary_definition_excluded(self):
  _,record=parse_article(article(extra='<p>A writer stated “These are eight or more words from a different work.”</p><p>The APA Dictionary defines a term here.</p>'),'PMC1','10.1/test')
  self.assertNotIn('different work',record['text']);self.assertNotIn('APA Dictionary',record['text'])
 def test_quoted_material_and_wrong_doi_excluded(self):
  _,record=parse_article(article(extra='<p><disp-quote>SECRET QUOTE</disp-quote></p>'),'PMC1','10.1/test');self.assertNotIn('SECRET QUOTE',record['text'])
  with self.assertRaises(ValueError):parse_article(article(),'PMC1','10.1/wrong')
if __name__=='__main__':unittest.main()
