"""Private headword-only source audit; never imports legacy prose or exports a term list."""
import argparse,collections,csv,hashlib,html,json,re,unicodedata,sqlite3
from pathlib import Path
from core import ROOT
from seed_terms import parse_mesh

def norm(value):
 value=html.unescape(value);value=unicodedata.normalize('NFKD',value).casefold()
 value=''.join(ch for ch in value if not unicodedata.combining(ch))
 return ' '.join(re.findall(r'\w+',value))

def build_index(records):
 index=collections.defaultdict(list)
 for pos,row in enumerate(records):
  for key in {norm(row['term']),*(norm(a) for a in row.get('aliases',[]))}:
   if key:index[key].append(pos)
 return index

def related_keys(value):
 # Retrieval-only spelling variants, never semantic equivalence.
 keys={norm(re.sub(r"['’]s\b",'',value)),norm(re.sub(r'[-–—]','',value))}
 key=norm(value)
 if key.endswith('s') and not key.endswith(('ss','is','us')):keys.add(key[:-1])
 elif key:keys.add(key+'s')
 return {k for k in keys if k and k!=key}

def build_related_index(records):
 index=collections.defaultdict(list)
 for pos,row in enumerate(records):
  for value in (row['term'],*row.get('aliases',[])):
   for key in related_keys(value):index[key].append(pos)
 return index

def classify(term,index,records,related_index=None):
 key=norm(term);ids=index.get(key,[])
 if ids:
  selected=[records[i] for i in ids]
  sources=sorted({r['source_id'] for r in selected});ready=[r for r in selected if r['definition_available']]
  status='exact_label_source_candidate' if ready else 'exact_label_anchor_only'
  return status,selected
 # Removing a sense qualifier is retrieval only: the result is never called an exact match.
 base=norm(re.sub(r'\([^)]*\)|\[[^]]*\]','',term))
 ids=index.get(base,[]) if base!=key else []
 if not ids:
  ids=sorted({i for k in related_keys(term) for i in index.get(k,[])} | set((related_index or {}).get(key,[])))
 return ('related_candidate_needs_review',[records[i] for i in ids]) if ids else ('source_not_yet_found',[])

def audit(headwords,records):
 index=build_index(records);related_index=build_related_index(records);rows=[];counts=collections.Counter();source_counts=collections.Counter()
 for position,item in enumerate(headwords,1):
  status,matches=classify(item['term'],index,records,related_index)
  counts[status]+=1
  for source in {m['source_id'] for m in matches}:source_counts[source]+=1
  rows.append({'row':position,'term':item['term'],'section':item.get('section','dictionary'),'status':status,
   'production_scope':'excluded_biography' if item.get('section')=='biographies' else 'term',
   'meaning_verified':False,'matches':[{'source':m['source_id'],'record_id':m['record_id'],'source_term':m['term'],'url':m['url'],
    'definition_available':m['definition_available'],'source_kind':m.get('source_kind','permitted_descriptor_record'),'snapshot_sha256':m.get('snapshot_sha256','')} for m in matches]})
 return rows,{'headwords_checked':len(rows),'status_counts':dict(counts),'source_match_counts':dict(source_counts),'source_records_indexed':len(records),
   'biographies':sum(r['section']=='biographies' for r in rows),'citations_semantically_verified':0,'definition_text_used_from_legacy':False,
   'headwords_exported_publicly':False,'paid_calls':0,'interpretation':'Exact labels retrieve possible sources, not proof that a source supports the intended sense. Unmatched rows remain visible.'}

def load_records(directory):
 mesh_path=ROOT/'.private/source-snapshots/mesh-d2026.bin';raw=mesh_path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 mesh=[dict(r,definition_available=bool(r['scope_note']),text=r['scope_note'],snapshot_sha256=sha) for r in parse_mesh(raw.decode())]
 records=mesh
 ncit=directory/'ncit-flat.txt'
 if ncit.exists():
  sha=hashlib.sha256(ncit.read_bytes()).hexdigest()
  with ncit.open(encoding='utf-8-sig') as f:
   for line in f:
    c=line.rstrip('\n').split('\t')
    if len(c)<5:continue
    names=[v for v in c[3].split('|') if v]
    if not names:continue
    preferred=c[5] if len(c)>5 and c[5] else names[0]
    records.append({'source_id':'ncit','record_id':c[0],'term':preferred,'aliases':names,'definition_available':bool(c[4]),'text':c[4],'semantic_types':c[7].split('|') if len(c)>7 else [],'snapshot_sha256':sha,
      'url':'https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/Thesaurus.FLAT.zip'})
 baldwin=directory/'baldwin-records.json'
 if baldwin.exists():records.extend(json.loads(baldwin.read_text()))
 wikidata=directory/'wikidata-records.json'
 if wikidata.exists():records.extend(json.loads(wikidata.read_text()))
 for filename in ('approved-text-records.json','approved-index-records.json','statbook-records.json','wikipedia-records.json','historical-records.json'):
  p=directory/filename
  if p.exists():records.extend(json.loads(p.read_text()))
 return records


def passage_candidates(rows,records,directory):
 dbpath=directory/'source-passages.sqlite'
 db=sqlite3.connect(dbpath)
 db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS passages USING fts5(record_index UNINDEXED, text, tokenize='unicode61 remove_diacritics 2')")
 db.execute('CREATE TABLE IF NOT EXISTS audit_meta (key TEXT PRIMARY KEY,value TEXT)')
 signature=hashlib.sha256(json.dumps([(i,r['source_id'],r['record_id'],r.get('snapshot_sha256'),len(r.get('text',''))) for i,r in enumerate(records) if r.get('text')]).encode()).hexdigest()
 stored=db.execute("SELECT value FROM audit_meta WHERE key='signature'").fetchone()
 if not stored or stored[0]!=signature:
  db.execute('DELETE FROM passages')
  db.executemany('INSERT INTO passages(record_index,text) VALUES (?,?)',[(i,r['text']) for i,r in enumerate(records) if r.get('text')]);db.execute("INSERT OR REPLACE INTO audit_meta VALUES ('signature',?)",(signature,));db.commit()
 counts=collections.Counter()
 for row in rows:
  if row['status'] not in ('source_not_yet_found','related_candidate_needs_review','exact_label_anchor_only'):continue
  query='"'+norm(row['term']).replace('"','""')+'"'
  if not norm(row['term']):continue
  found=db.execute('SELECT record_index, snippet(passages,1,"[", "]", " … ",45) FROM passages WHERE passages MATCH ? LIMIT 3',(query,)).fetchall()
  if found:
   row['status']='source_passage_candidate'
   for ident,snippet in found:
    r=records[int(ident)]
    row['matches'].append({'source':r['source_id'],'record_id':r['record_id'],'source_term':r['term'],'url':r['url'],'definition_available':True,'snapshot_sha256':r['snapshot_sha256'],'passage_excerpt':snippet,'source_kind':r.get('source_kind','permitted_descriptor_record')})
   counts['passage_candidates']+=1
 db.close()
 return dict(counts)

def add_article_candidates(rows,directory):
 byterm=collections.defaultdict(list)
 for filename in ('article-records.json','article-wide-records.json'):
  path=directory/filename
  if path.exists():
   for candidate in json.loads(path.read_text()):byterm[norm(candidate['term'])].append(candidate)
 for row in rows:
  found=byterm.get(norm(row['term']),[])
  if not found:continue
  if row['status']=='source_not_yet_found':row['status']='article_reference_candidate'
  seen=set()
  for item in found:
   key=(item['source'],item['record_id'])
   if key in seen:continue
   seen.add(key);row['matches'].append(item)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--private-headwords',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--passages',action='store_true');args=p.parse_args()
 for path in (args.private_headwords.resolve(),args.out.resolve()):
  if path.is_relative_to(ROOT) and '.private' not in path.relative_to(ROOT).parts:raise ValueError('Coverage input/output must remain private')
 args.out.mkdir(parents=True,exist_ok=True);records=load_records(args.out)
 rows,report=audit(json.loads(args.private_headwords.read_text()),records)
 if args.passages:
  report['passage_search']=passage_candidates(rows,records,args.out)
  report['status_counts']=dict(collections.Counter(r['status'] for r in rows))
  report['source_match_counts']=dict(collections.Counter(source for r in rows for source in {m['source'] for m in r['matches']}))
 add_article_candidates(rows,args.out)
 report['article_query_runs']=[]
 for name in ('article-query-progress.json','article-wide-query-progress.json'):
  progress=args.out/name
  if progress.exists():
   run=json.loads(progress.read_text());report['article_query_runs'].append({'report':name,'batches_done':run['batches_done'],'batches_total':run['batches_total'],'complete':run['batches_done']==run['batches_total'],'failed_batches':len(run.get('failed_batches',[])),'truncated_batches':len(run.get('truncated_batches',[]))})
 report['status_counts']=dict(collections.Counter(r['status'] for r in rows))
 report['source_match_counts']=dict(collections.Counter(source for r in rows for source in {m.get('source',m.get('source_id')) for m in r['matches']}))
 (args.out/'coverage.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 with (args.out/'coverage.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['row','term','section','status','production_scope','source_ids','source_record_ids','source_urls','meaning_verified'])
  for r in rows:w.writerow([r['row'],r['term'],r['section'],r['status'],r['production_scope'],'; '.join(m['source'] for m in r['matches']),'; '.join(m['record_id'] for m in r['matches']),'; '.join(m['url'] for m in r['matches']),False])
 (args.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
