"""Reconstruct interrupted pilot results from matching cached requests and usage receipts, offline."""
import json
import hashlib
import math
import sqlite3
from core import ROOT, canonical, digest
from run_pilot import longest_overlap
from check_packets import validate_packet
from budget import Budget


def recover():
    dest = ROOT / '.private/pilot'
    manifest = json.loads((ROOT / 'data/pilot-preregistration.json').read_text())
    packets = json.loads((dest / 'packets.json').read_text())
    if manifest['preregistration_hash'] != digest({k: v for k, v in manifest.items() if k != 'preregistration_hash'}):
        raise ValueError('Historical registration changed')
    if digest(packets) != manifest['packet_set_hash']:
        raise ValueError('Historical packets changed')
    if hashlib.sha256((dest / 'executor-original.py').read_bytes()).hexdigest() != manifest['executor_sha256']:
        raise ValueError('Historical executor changed')
    sources = {s['id']: s for s in json.loads((ROOT / 'data/sources.json').read_text())['sources']}
    for packet in packets:
        validate_packet(packet, sources)
    with sqlite3.connect(dest / 'budget.sqlite') as db:
        ledger = {r[0]: r for r in db.execute('SELECT id,category,reserved,charged,state FROM calls')}
    references = [p['text'] for p in packets]

    def read(category, ident, model, system, data, schema):
        path = dest / 'calls' / f'{ident}-{category}.json'
        if not path.exists():
            return None
        cached = json.loads(path.read_text())
        body = {'model': model, 'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': json.dumps(data, ensure_ascii=False)}],
                'response_format': {'type': 'json_schema', 'json_schema': {'name': 'dictionary_result', 'strict': True, 'schema': schema}},
                'max_completion_tokens': manifest['max_completion_tokens'], 'reasoning_effort': manifest['reasoning_effort'], 'store': False}
        if cached['request_hash'] != hashlib.sha256(canonical(body)).hexdigest():
            raise ValueError('Cached request differs from frozen inputs: ' + path.name)
        receipt = json.loads((dest / 'receipts' / (cached['receipt_id'] + '.json')).read_text())
        choice = receipt['choices'][0]
        if receipt['model'] != model or choice['finish_reason'] != 'stop' or json.loads(choice['message']['content']) != cached['parsed']:
            raise ValueError('Receipt differs from cached response')
        usage = receipt['usage']; prices = manifest['prices_per_million'][model]
        charge = math.ceil(usage['prompt_tokens'] * prices['input'] + usage['completion_tokens'] * prices['output'])
        row = ledger[cached['receipt_id']]
        if row[3] != charge or row[4] != 'receipted' or row[1] not in (category, 'transport_schema_retry'):
            raise ValueError('Receipt differs from ledger')
        return {'parsed': cached['parsed'], 'receipt_id': cached['receipt_id'], 'model': model}

    rows = []
    for packet in packets:
        ident = packet['id']
        draft = read('drafting', ident, manifest['models']['draft'], manifest['draft_prompt'], {'packet': packet, 'fields': manifest['fields']}, manifest['draft_schema'])
        if draft is None: raise ValueError('Initial draft missing')
        def judge(label, candidate, revised=False):
            return read(label, ident + ('-redraft' if revised else ''), manifest['models'][label], manifest['judge_prompt'],
                        {'packet': packet, 'definition': candidate['parsed']['definition'], 'field': candidate['parsed']['field']}, manifest['judge_schema'])
        def passed(candidate, judges):
            d = candidate['parsed']
            return all(j is not None and j['parsed']['passed'] is True for j in judges) and d['packet_sufficient'] is True and d['field'] in manifest['fields'] and not longest_overlap(d['definition'], references)
        first_judges = [judge(label, draft) for label in ('judge_a', 'judge_b')]
        first_pass = passed(draft, first_judges)
        selected = draft; selected_judges = first_judges; status = 'initial_pass' if first_pass else 'incomplete'
        if not first_pass:
            feedback = {'previous_definition': draft['parsed']['definition'], 'reasons': [reason for j in first_judges if j for reason in j['parsed']['reasons']],
                        'overlap_15': longest_overlap(draft['parsed']['definition'], references)}
            revised = read('redrafting', ident, manifest['models']['draft'], manifest['draft_prompt'], {'packet': packet, 'fields': manifest['fields'], 'revision_feedback': feedback}, manifest['draft_schema'])
            if revised:
                rjudges = [judge(label, revised, True) for label in ('judge_a', 'judge_b')]
                selected = revised; selected_judges = rjudges
                if all(j is not None for j in rjudges): status = 'redraft_pass' if passed(revised, rjudges) else 'final_drop'
        rows.append({'id': ident, 'term': packet['term'], 'status': status, 'definition': selected['parsed']['definition'], 'field': selected['parsed']['field'],
                     'definition_version': 1 if first_pass else 2, 'definition_hash': digest(selected['parsed']), 'packet_hash': packet['packet_hash'],
                     'draft_receipt_id': selected['receipt_id'], 'judges': selected_judges, 'release_authorized': False})
    (dest / 'recovered-results.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    counts = {s: sum(r['status'] == s for r in rows) for s in ('initial_pass', 'redraft_pass', 'final_drop', 'incomplete')}
    report = {'status': 'interrupted_results_reconstructed_offline', 'historical_registration_hash': manifest['preregistration_hash'], 'attempted': len(rows),
              'counts': counts, 'machine_passed': counts['initial_pass'] + counts['redraft_pass'], 'completed_reviews': len(rows) - counts['incomplete'],
              'cache_requests_receipts_and_ledger_verified': True, 'released_entries': 0, 'budget': Budget(dest / 'budget.sqlite', 20_000_000).summary(), 'paid_calls_this_recovery': 0}
    (ROOT / 'reports/pilot-recovery.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return rows

if __name__ == '__main__': recover()
