"""Check generated internal links, term-page coverage, and indexed content boundaries."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import argparse,json
from core import ROOT,load_inputs
class Page(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.add(a['id'])
  if tag=='a' and 'href'in a:self.links.append(a['href'])
def check(root,base):
 pages={p:Page() for p in root.rglob('*.html')}
 for p,parser in pages.items():parser.feed(p.read_text())
 errors=[];base='/'+base.strip('/') if base.strip('/') else ''
 for p,parser in pages.items():
  for href in parser.links:
   parsed=urlsplit(href)
   if parsed.scheme or parsed.netloc:continue
   value=unquote(parsed.path)
   if not value:target=p
   elif value.startswith('/'):
    if base and not (value==base or value.startswith(base+'/')):errors.append(f'{p.name}: outside configured base {href}');continue
    target=root/value[len(base):].lstrip('/')
   else:target=p.parent/value
   if target.is_dir():target=target/'index.html'
   if not target.exists():errors.append(f'{p.relative_to(root)}: missing {href}');continue
   if parsed.fragment and target in pages and parsed.fragment not in pages[target].ids:errors.append(f'Invalid fragment {href}')
 distribution=json.loads((ROOT/'dist-data/dictionary.json').read_text());entries=distribution['entries']
 for dropped in distribution.get('dropped',[]):
  if (root/'terms'/dropped['id']/'index.html').exists():errors.append('Dropped term still has a page: '+dropped['id'])
 for e in entries:
  p=root/'terms'/e['id']/'index.html'
  if not p.exists():errors.append('Missing term page '+e['id'])
 assert not errors,'\n'.join(errors)
 return {'html_pages':len(pages),'term_pages':len(entries),'broken_links':0,'base':base or '/'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',default='/');a=p.parse_args();print(json.dumps(check(ROOT/'site/dist',a.base),indent=2))
