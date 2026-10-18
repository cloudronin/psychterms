import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_copy import hits,Copy
class CopyPolicyTests(unittest.TestCase):
 def test_ai_product_matrix(self):
  for product in ('Prep','PsychTerms','site'):self.assertFalse(hits('AI model. A.I. model.',product))
  for product in ('Session','Desk'):self.assertTrue(hits('AI model',product))
 def test_other_bans_apply_everywhere(self):
  for product in ('Prep','PsychTerms','site','Session','Desk'):
   for text in ('Scribe','listen','listening','always-on','always on','Cloud sync'):self.assertTrue(hits(text,product))
 def test_definition_text_is_not_ui_copy(self):
  p=Copy();p.feed('<header>Free dictionary</header><p class="definition">A listening skill.</p><footer>Free forever</footer>')
  self.assertFalse(hits(' '.join(p.text)))
 def test_dictionary_title_is_data_and_marketing_title_is_still_checked(self):
  source=Copy();source.feed('<title data-entry-content>Listening attitude | PsychTerms</title><header>Free dictionary</header>')
  self.assertFalse(hits(' '.join(source.text)))
  product=Copy();product.feed('<title>Always on dictionary</title>')
  self.assertTrue(hits(' '.join(product.text)))
if __name__=='__main__':unittest.main()
