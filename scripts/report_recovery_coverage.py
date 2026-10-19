"""Keep one private disposition per audit label; publish aggregate coverage only."""
import collections,csv,json
from core import ROOT
from source_coverage_audit import norm
from run_candidate_drafts import source_content_hash

DEST=ROOT/'.private/source-recovery';AUDIT=ROOT/'.private/coverage-audit'

def build():
    rows=json.loads((AUDIT/'coverage.json').read_text());history=json.loads((ROOT/'data/status-history.json').read_text())['entries']
    by_term=collections.defaultdict(list)
    for ident,entry in history.items():by_term[norm(entry['term'])].append((ident,entry['status']))
    leads=set()
    for path in (AUDIT/'article-records.json',AUDIT/'article-wide-records.json',DEST/'new-article-records.json'):
        if not path.exists():continue
        try:records=json.loads(path.read_text())
        except json.JSONDecodeError:continue
        leads.update(norm(r['term']) for r in records)
    admitted=set()
    for path in (DEST/'records').glob('*.json'):
        try:record=json.loads(path.read_text())
        except json.JSONDecodeError:continue
        admitted.update(norm(t) for t in record['terms'])
    blocked_path=DEST/'declined-content-hashes.json';blocked=set(json.loads(blocked_path.read_text())) if blocked_path.exists() else set();declined=set()
    for path in (ROOT/'.private/candidate-drafts/registrations').glob('*-packets.json'):
        for packet in json.loads(path.read_text()):
            if source_content_hash(packet) in blocked:declined.add(norm(packet['term']))
    pending=json.loads((ROOT/'.private/candidate-drafts/pending-sources.json').read_text());scope={norm(r['term']) for r in pending if r.get('retrieval_status')=='scope_excluded_before_spend'}
    rank={'judged':0,'reviewed':1,'candidate':2,'dropped':3};dispositions=[]
    for row in rows:
        key=norm(row['term']);matches=by_term.get(key,[])
        if row['production_scope']=='excluded_biography':status='biography_excluded'
        elif matches:status=min((status for _,status in matches),key=lambda s:rank[s])
        elif key in declined:status='draft_packet_attempts_declined'
        elif key in admitted:status='licensed_article_lead_needs_usable_packet'
        elif key in leads:status='article_lead_not_admitted'
        elif key in scope:status='prior_match_out_of_scope_needs_alternative'
        else:status='no_usable_packet_yet'
        dispositions.append({'row':row['row'],'term':row['term'],'disposition':status,'entry_ids':'; '.join(ident for ident,_ in matches)})
    with (DEST/'coverage-dispositions.csv').open('w',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=['row','term','disposition','entry_ids'],lineterminator='\n');writer.writeheader();writer.writerows(dispositions)
    counts=dict(collections.Counter(r['disposition'] for r in dispositions));assert sum(counts.values())==len(rows)
    report={'audit_labels':len(rows),'dispositions':counts,'production_status_counts':dict(collections.Counter(e['status'] for e in history.values())),'private_rows_exported':False,'legacy_definition_text_used':False,'interpretation':'Label matching only, not semantic equivalence to private definitions. Licensed leads may still lack usable passages; a metadata hit is neither permission nor definition support. Model readers assess fresh definitions only against their permitted source packets.'}
    (ROOT/'reports/recovery-coverage.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':print(json.dumps(build(),indent=2))
