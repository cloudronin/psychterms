"""Apply existing single-redraft allowance after a pinned editorial review; no rule or card changes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from core import ROOT, digest
from budget import Budget
from run_pilot import Client, require_paid_dispatch
from run_combined_pilot import verify
from arcsim_adapter import vignette_view, build_card
from combined_contract import make_context, DRAFT_PROMPT, JUDGE_PROMPT, DRAFT_SCHEMA, JUDGE_SCHEMA
from vignette_output import scan_generated, output_hash, require_checks

DEST = ROOT / '.private/pilot-combined'
ADDENDUM = ROOT / 'data/pilot-editorial-addendum.json'


def prepare():
    m = verify()
    decisions = json.loads((DEST / 'editorial-decisions.json').read_text())
    initial = DEST / 'scene-results-initial.json'
    if not initial.exists(): initial.write_bytes((DEST / 'scene-results.json').read_bytes())
    rows = json.loads(initial.read_text())
    if {d['term_id'] for d in decisions} != {r['term_id'] for r in rows}: raise ValueError('Review must cover every scene')
    lookup = {r['term_id']: r for r in rows}
    for d in decisions:
        row = lookup[d['term_id']]
        if d['reviewed_output_hash'] != output_hash(row['output']): raise ValueError('Editorial review is stale')
        if d['decision'] == 'redraft' and row['revision'] != 0: raise ValueError('No second editorial redraft is permitted')
    if ADDENDUM.exists(): raise RuntimeError('Editorial addendum already recorded')
    addendum = {'status': 'frozen_before_editorial_calls', 'base_registration_hash': m['registration_hash'],
                'scope': 'Apply the existing one-redraft allowance to editorial factuality failures; same writer/judges/prompts, fixed cards/fields/hash rule, sample and shared $20 ledger.',
                'card_fields_changed': False, 'card_hash_rule_changed': False, 'additional_editorial_redrafts_per_scene': 0,
                'redraft_term_ids': [d['term_id'] for d in decisions if d['decision'] == 'redraft'],
                'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [DEST / 'editorial-decisions.json', initial]},
                'full_run_authorized': False}
    addendum['addendum_hash'] = digest(addendum)
    ADDENDUM.write_text(json.dumps(addendum, indent=2) + '\n')
    print(json.dumps(addendum, indent=2))


def validate():
    m = verify(True)
    a = json.loads(ADDENDUM.read_text())
    if a['addendum_hash'] != digest({k: v for k, v in a.items() if k != 'addendum_hash'}): raise ValueError('Addendum changed')
    if a['base_registration_hash'] != m['registration_hash'] or a['script_sha256'] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest(): raise ValueError('Editorial executor changed')
    for rel, expected in a['input_sha256'].items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected: raise ValueError('Editorial input changed')
    require_paid_dispatch()
    return m


def execute(key_path):
    import re
    manifest = validate()
    match = re.search(r'sk-[A-Za-z0-9_-]+', key_path.read_text())
    if not match: raise ValueError('API key missing')
    budget = Budget(ROOT / '.private/pilot/budget.sqlite', 20_000_000)
    client = Client(manifest, match[0], budget, DEST)
    decisions = {d['term_id']: d for d in json.loads((DEST / 'editorial-decisions.json').read_text())}
    fits = {r['term_id']: r for r in json.loads((DEST / 'fit-ledger.json').read_text())}
    definitions = {r['id']: r for r in json.loads((DEST / 'selected-definitions.json').read_text())}
    packets = {r['id']: r for r in json.loads((ROOT / '.private/pilot/packets.json').read_text())}
    rows = copy.deepcopy(json.loads((DEST / 'scene-results-initial.json').read_text()))
    final = []
    for original in rows:
        d = decisions[original['term_id']]; ident = original['term_id']
        if d['decision'] == 'keep':
            original['editorial_decision'] = d; final.append(original)
            continue
        validate()
        fit = fits[ident]; view = vignette_view(build_card(fit['build_recipe']), fit['build_recipe'])
        context = make_context(fit, definitions[ident], packets[ident], view)
        feedback = {'previous_scene': original['output'], 'reasons': d['reasons']}
        parsed, receipt = client.call('vignette_redrafting', ident + '-redraft', manifest['models']['draft'], DRAFT_PROMPT, {'context': context, 'revision_feedback': feedback}, DRAFT_SCHEMA)
        item = {'term_id': ident, 'scene': parsed['scene'], 'notice_line': parsed['notice_line']}
        result = {'term_id': ident, 'output': item, 'revision': 1, 'draft_receipt': receipt, 'context_hash': digest(context), 'accepted': False,
                  'initial_output_hash': output_hash(original['output']), 'editorial_decision': d}
        scan = None; failures = []
        if parsed['can_illustrate'] is not True: failures.append(parsed['reason'] or 'Writer cannot illustrate honestly')
        try: scan = scan_generated([item], DEST / 'refs', manifest['reference_manifest'], DEST / 'scans' / (ident + '-redraft'))
        except ValueError as error: failures.append(str(error))
        if scan and not scan['scan_15_passed']: failures.append('15-word output overlap after allowed redraft')
        reviews = []
        for label in ('judge_a', 'judge_b'):
            validate()
            verdict, rid = client.call('vignette_' + label, ident + '-redraft', manifest['models'][label], JUDGE_PROMPT,
                                       {'context': context, 'scene': item['scene'], 'notice_line': item['notice_line']}, JUDGE_SCHEMA)
            reviews.append(dict(verdict, model=manifest['models'][label], receipt_id=rid, output_hash=output_hash(item), context_hash=digest(context), rubric_hash=digest(JUDGE_PROMPT)))
            if verdict['passed'] is not True: failures.extend(verdict['reasons'] or ['Judge rejected'])
        pending = bool(scan and scan['triage_5'])
        result.update(scan=scan, reviews=reviews, failures=failures, five_word_triage_pending=pending,
                      status='dropped_after_redraft' if failures else 'pending_editorial_final_read')
        final.append(result)
        (DEST / 'final-scenes.json').write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'editorial_redraft_complete': ident, 'failures': len(failures), 'receipted_usd': budget.summary()['receipted_usd']}), flush=True)
        if sum(r['status'] == 'dropped_after_redraft' for r in final) / len(rows) > manifest['stop_final_drop_fraction']:
            print('Final-drop stop threshold crossed; no remaining calls.', flush=True)
            break
    (DEST / 'final-scenes.json').write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--prepare', action='store_true'); parser.add_argument('--execute', action='store_true'); parser.add_argument('--key-file', type=Path); args = parser.parse_args()
    if args.prepare: prepare()
    elif args.execute:
        if not args.key_file: parser.error('--key-file required')
        execute(args.key_file)
    else: parser.error('Choose --prepare or --execute')
