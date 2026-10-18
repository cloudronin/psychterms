"""Audit all charged pilot receipts and export itemized costs, without model calls."""
import csv
import hashlib
import json
import math
import re
import sqlite3
from collections import defaultdict
from core import ROOT, canonical, digest
from budget import Budget
from combined_contract import make_context, DRAFT_PROMPT, JUDGE_PROMPT, DRAFT_SCHEMA, JUDGE_SCHEMA
from arcsim_adapter import build_card, vignette_view


def audit():
    root = ROOT / '.private/pilot-combined'; old = ROOT / '.private/pilot'
    original = json.loads((ROOT / 'data/pilot-preregistration.json').read_text())
    combined = json.loads((ROOT / 'data/pilot-combined-preregistration.json').read_text())
    packets = {p['id']: p for p in json.loads((old / 'packets.json').read_text())}
    definitions = {r['id']: r for r in json.loads((root / 'selected-definitions.json').read_text())}
    fits = {r['term_id']: r for r in json.loads((root / 'fit-ledger.json').read_text())}
    editorial = {r['term_id']: r for r in json.loads((root / 'editorial-decisions.json').read_text())}
    cache_index = {}; item_costs = defaultdict(lambda: {'calls': 0, 'cost_micro': 0, 'input_tokens': 0, 'output_tokens': 0, 'categories': defaultdict(int)})
    for directory, domain in [(old, 'definition'), (root, 'vignette')]:
        for path in (directory / 'calls').glob('*.json'):
            row = json.loads(path.read_text()); match = re.match(r'^(D\d+)(-redraft)?-(.+)\.json$', path.name)
            if not match: raise ValueError('Unrecognized call cache name')
            cache_index[row['receipt_id']] = {'directory': directory, 'domain': domain, 'term_id': match[1], 'redraft': bool(match[2]), 'kind': match[3], 'cached': row}
    # Reconstruct every vignette request from the frozen inputs, including editorial feedback.
    checked_requests = 0
    def cached(ident, kind, revised=False):
        return json.loads((root / 'calls' / (ident + ('-redraft' if revised else '') + '-' + kind + '.json')).read_text())
    for ident in definitions:
        fit = fits[ident]; context = make_context(fit, definitions[ident], packets[ident], vignette_view(build_card(fit['build_recipe']), fit['build_recipe']))
        first = cached(ident, 'vignette_drafting')['parsed']
        first_output = {'term_id': ident, 'scene': first['scene'], 'notice_line': first['notice_line']}
        for revised in (False, True):
            writer_file = root / 'calls' / (ident + ('-redraft-vignette_redrafting.json' if revised else '-vignette_drafting.json'))
            if not writer_file.exists(): continue
            result = json.loads(writer_file.read_text()); payload = {'context': context}
            if revised:
                if editorial[ident]['decision'] == 'redraft': reasons = editorial[ident]['reasons']
                else:
                    reasons = []
                    for label in ('judge_a', 'judge_b'):
                        verdict = cached(ident, 'vignette_' + label)['parsed']
                        if not verdict['passed']: reasons.extend(verdict['reasons'] or ['Judge rejected without explanation'])
                    if not json.loads((root / 'scans' / ident / 'scan.json').read_text())['scan_15_passed']: reasons.insert(0, '15-word output overlap')
                payload['revision_feedback'] = {'previous_scene': first_output, 'reasons': reasons}
            pairs = [(result, combined['models']['draft'], DRAFT_PROMPT, payload, DRAFT_SCHEMA)]
            parsed = result['parsed']
            for label in ('judge_a', 'judge_b'):
                pairs.append((cached(ident, 'vignette_' + label, revised), combined['models'][label], JUDGE_PROMPT, {'context': context, 'scene': parsed['scene'], 'notice_line': parsed['notice_line']}, JUDGE_SCHEMA))
            for saved, model, prompt, data, schema in pairs:
                body = {'model': model, 'messages': [{'role': 'system', 'content': prompt}, {'role': 'user', 'content': json.dumps(data, ensure_ascii=False)}],
                        'response_format': {'type': 'json_schema', 'json_schema': {'name': 'dictionary_result', 'strict': True, 'schema': schema}},
                        'max_completion_tokens': 1000, 'reasoning_effort': 'low', 'store': False}
                if saved['request_hash'] != hashlib.sha256(canonical(body)).hexdigest(): raise ValueError('Vignette request differs from allowed frozen inputs')
                checked_requests += 1
    with sqlite3.connect(old / 'budget.sqlite') as db:
        ledger = db.execute('SELECT id,category,reserved,charged,state FROM calls').fetchall()
    unassigned = []; charged_count = 0
    for ident, category, reserved, charged, state in ledger:
        if charged is None:
            unassigned.append({'request_id': ident, 'category': category, 'reserved_usd': reserved / 1e6})
            continue
        item = cache_index.get(ident)
        if not item: raise ValueError('Charged call lacks a parsed-result receipt binding')
        receipt = json.loads((item['directory'] / 'receipts' / (ident + '.json')).read_text())
        if receipt['model'] not in combined['prices_per_million']: raise ValueError('Unexpected model')
        if receipt['choices'][0]['finish_reason'] != 'stop' or json.loads(receipt['choices'][0]['message']['content']) != item['cached']['parsed']:
            raise ValueError('Cache differs from raw model response')
        usage = receipt['usage']; prices = combined['prices_per_million'][receipt['model']]
        expected = math.ceil(usage['prompt_tokens'] * prices['input'] + usage['completion_tokens'] * prices['output'])
        if expected != charged or state != 'receipted': raise ValueError('Usage differs from ledger cost')
        entry = item_costs[(item['domain'], item['term_id'])]
        entry['calls'] += 1; entry['cost_micro'] += charged; entry['input_tokens'] += usage['prompt_tokens']; entry['output_tokens'] += usage['completion_tokens']
        split_category = category
        if category not in ('transport_schema_retry', 'drafting', 'redrafting', 'vignette_drafting', 'vignette_redrafting'):
            split_category = ('repeated_' if item['redraft'] else 'initial_') + category
        entry['categories'][split_category] += charged
        charged_count += 1
    with (ROOT / 'reports/pilot-item-costs.csv').open('w', newline='') as f:
        writer = csv.writer(f, lineterminator='\n'); writer.writerow(['domain', 'term_id', 'term', 'charged_usd', 'receipted_calls', 'input_tokens', 'output_tokens', 'category_cost_usd'])
        for (domain, ident), row in sorted(item_costs.items()):
            writer.writerow([domain, ident, packets[ident]['term'], f"{row['cost_micro']/1e6:.6f}", row['calls'], row['input_tokens'], row['output_tokens'], json.dumps({k: v / 1e6 for k, v in sorted(row['categories'].items())})])
    summary = Budget(old / 'budget.sqlite', 20_000_000).summary()
    if sum(r['cost_micro'] for r in item_costs.values()) != round(summary['receipted_usd'] * 1e6): raise ValueError('Item costs do not reconcile')
    report = {'charged_receipts_verified': charged_count, 'definition_request_binding': 'Verified independently by recover_pilot.py against all frozen definition requests',
              'vignette_requests_reconstructed_from_permitted_inputs': checked_requests, 'item_cost_rows': len(item_costs),
              'usage_and_raw_response_match_cache_and_ledger': True, 'unresolved_reservations': unassigned,
              'budget': summary, 'costs_are_conservative_usage_estimates_not_invoice': True, 'latency_measured': False,
              'latency_limitation': 'The executor did not record request start/end timestamps; do not infer latency from file timestamps.', 'paid_calls_this_audit': 0}
    (ROOT / 'reports/pilot-receipt-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('budget', 'unresolved_reservations')}, indent=2))
    return report

if __name__ == '__main__': audit()
