"""Product UI copy rules; definition and source text have their own editorial checks."""
import json,re
from html.parser import HTMLParser
from core import ROOT
POLICY=json.loads((ROOT/'data/copy-policy.json').read_text())
PATTERNS=[r'\bscribes?\b',r'\blisten\w*',r'\balways[\s-]+on\b',r'\bcloud\w*']
def hits(text,product='PsychTerms'):
 patterns=PATTERNS+([] if POLICY['ai_allowed'][product] else [r'\bAI\b',r'\bA\.I\.'])
 return [m.group() for pattern in patterns for m in re.finditer(pattern,text,re.I)]
class Copy(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.stack=[];self.text=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);skip='data-entry-content' in a or tag in ('script','style') or 'data-pagefind-body' in a or bool({'definition','citation','metadata'} & set(a.get('class','').split()))
  if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):
   self.stack.append((tag,skip));self.depth+=skip
 def handle_endtag(self,tag):
  if self.stack and self.stack[-1][0]==tag:self.depth-=self.stack.pop()[1]
 def handle_data(self,text):
  if not self.depth:self.text.append(text)
if __name__=='__main__':
 paths=list((ROOT/'site/dist').rglob('*.html'))
 if not paths:raise ValueError('Build the site before checking product copy')
 for p in paths:
  parser=Copy();parser.feed(p.read_text());found=hits(' '.join(parser.text))
  if found:raise ValueError(str(p.relative_to(ROOT))+': '+str(found))
 print(json.dumps({'product':'PsychTerms','html_pages':len(paths),'copy_hits':0,'AI_allowed':True}))
