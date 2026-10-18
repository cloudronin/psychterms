"""Validate or execute only the bounded combined pilot against its shared historical ledger."""
import argparse
import hashlib
import json
from pathlib import Path
from core import ROOT, digest
from budget import Budget
from run_pilot import Client, require_paid_dispatch, longest_overlap
from recover_pilot import recover
from arcsim_adapter import build_card, vignette_view
from combined_contract import make_context, DRAFT_PROMPT, JUDGE_PROMPT, DRAFT_SCHEMA, JUDGE_SCHEMA
from vignette_output import scan_generated, require_checks, output_hash, reference_manifest


def verify(execute=False):
    manifest = json.loads((ROOT / 'data/pilot-combined-preregistration.json').read_text())
    if manifest['registration_hash'] != digest({k: v for k, v in manifest.items() if k != 'registration_hash'}): raise ValueError('Combined registration changed')
    for rel, expected in manifest['file_sha256'].items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected: raise ValueError('Registered file changed: ' + rel)
    for rel, expected in manifest['private_input_sha256'].items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected: raise ValueError('Registered private input changed: ' + rel)
    if manifest['cap_usd'] != '20.00' or manifest['full_run_authorized'] is not False: raise ValueError('Wrong budget line')
    if len(set(manifest['models'][key] for key in ('judge_a', 'judge_b'))) != 2: raise ValueError('Distinct judges required')
    dest = ROOT / '.private/pilot-combined'
    if reference_manifest(dest / 'refs') != manifest['reference_manifest']: raise ValueError('Registered references changed')
    fit = json.loads((dest / 'fit-ledger.json').read_text())
    if len(fit) != 50 or any(r['status'] == 'pending' for r in fit): raise ValueError('50 completed fit decisions required')
    if execute:
        require_paid_dispatch()
        if manifest['status'] != 'frozen' or manifest['dispatch_authorized'] is not True: raise RuntimeError('Combined PREREG is reviewable but not authorized for dispatch')
    return manifest


def finish_definitions(key, budget):
    original = json.loads((ROOT / 'data/pilot-preregistration.json').read_text())
    dest = ROOT / '.private/pilot'; client = Client(original, key, budget, dest)
    packets = json.loads((dest / 'packets.json').read_text()); lookup = {p['id']: p for p in packets}
    recovered = json.loads((dest / 'recovered-results.json').read_text())
    refs = [p['text'] for p in packets]
    for row in recovered:
        if row['status'] != 'incomplete': continue
        verify(True); ident = row['id']; p = lookup[ident]
        def cached(suffix): return json.loads((dest / 'calls' / f'{ident}-{suffix}.json').read_text())['parsed']
        old = cached('drafting'); a = cached('judge_a'); b = cached('judge_b')
        feedback = {'previous_definition': old['definition'], 'reasons': a['reasons'] + b['reasons'], 'overlap_15': longest_overlap(old['definition'], refs)}
        # Same frozen redraft request: missing transport outcomes do not grant another editorial revision.
        draft, _ = client.call('redrafting', ident, original['models']['draft'], original['draft_prompt'], {'packet': p, 'fields': original['fields'], 'revision_feedback': feedback}, original['draft_schema'])
        for label in ('judge_a', 'judge_b'):
            verify(True)
            client.call(label, ident + '-redraft', original['models'][label], original['judge_prompt'], {'packet': p, 'definition': draft['definition'], 'field': draft['field']}, original['judge_schema'])
    return recover()


def run(key_path):
    manifest = verify(True)
    import re
    match = re.search(r'sk-[A-Za-z0-9_-]+', key_path.read_text())
    if not match: raise ValueError('API key missing')
    budget = Budget(ROOT / '.private/pilot/budget.sqlite', 20_000_000)
    definitions = {r['id']: r for r in finish_definitions(match[0], budget)}
    dest = ROOT / '.private/pilot-combined'
    (dest / 'receipts').mkdir(exist_ok=True)
    client = Client(manifest, match[0], budget, dest)
    packets = {p['id']: p for p in json.loads((ROOT / '.private/pilot/packets.json').read_text())}
    fits = json.loads((dest / 'fit-ledger.json').read_text()); results = []
    matched_count = sum(f['status'] == 'matched' for f in fits)
    initial_overlap_hits = 0; stop_reason = None
    for fit in fits:
        if fit['status'] != 'matched': continue
        verify(True)
        view = vignette_view(build_card(fit['build_recipe']), fit['build_recipe'])
        context = make_context(fit, definitions[fit['term_id']], packets[fit['term_id']], view)
        row = None; feedback = None
        for revision in range(2):
            ident = fit['term_id'] + ('-redraft' if revision else '')
            payload = {'context': context}
            if feedback: payload['revision_feedback'] = feedback
            verify(True)
            draft, draft_receipt = client.call('vignette_redrafting' if revision else 'vignette_drafting', ident, manifest['models']['draft'], DRAFT_PROMPT, payload, DRAFT_SCHEMA)
            item = {'term_id': fit['term_id'], 'scene': draft['scene'], 'notice_line': draft['notice_line']}
            row = {'term_id': fit['term_id'], 'output': item, 'revision': revision, 'draft_receipt': draft_receipt, 'context_hash': digest(context), 'accepted': False}
            (dest / 'current-scene.json').write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
            failures = []
            if draft['can_illustrate'] is not True: failures.append('Writer cannot illustrate from the supplied card: ' + draft['reason'])
            scan = None; reviews = []
            try: scan = scan_generated([item], dest / 'refs', manifest['reference_manifest'], dest / 'scans' / ident)
            except ValueError as error: failures.append(str(error))
            if scan and not scan['scan_15_passed']:
                failures.append('15-word output overlap')
                if revision == 0:
                    initial_overlap_hits += 1
                    if initial_overlap_hits / matched_count > manifest['stop_initial_overlap_fraction']:
                        stop_reason = 'stopped_initial_vignette_overlap_threshold'
                        row.update(scan=scan, failures=failures, five_word_triage_pending=bool(scan['triage_5']), status=stop_reason)
                        break
            for label in ('judge_a', 'judge_b'):
                verify(True)
                verdict, receipt = client.call('vignette_' + label, ident, manifest['models'][label], JUDGE_PROMPT, {'context': context, 'scene': item['scene'], 'notice_line': item['notice_line']}, JUDGE_SCHEMA)
                reviews.append(dict(verdict, model=manifest['models'][label], receipt_id=receipt, output_hash=output_hash(item), context_hash=digest(context), rubric_hash=digest(JUDGE_PROMPT)))
                row['reviews'] = reviews
                (dest / 'current-scene.json').write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
                if verdict['passed'] is not True: failures.extend(verdict['reasons'] or ['Judge rejected without explanation'])
            triage_pending = bool(scan and scan['triage_5'])
            row.update(scan=scan, reviews=reviews, failures=failures, five_word_triage_pending=triage_pending)
            if not failures and scan:
                if triage_pending:
                    row['status'] = 'pending_editorial_five_word_triage'
                    break
                require_checks(item, fit, digest(context), scan, reviews, True)
                row.update(accepted=True, status='passed_machine_checks')
                break
            row['status'] = 'dropped_after_redraft' if revision else 'needs_one_redraft'
            feedback = {'previous_scene': item, 'reasons': failures}
        results.append(row)
        (dest / 'scene-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
        if sum(r['status'] == 'dropped_after_redraft' for r in results) / matched_count > manifest['stop_final_drop_fraction']:
            stop_reason = 'stopped_vignette_final_drop_threshold'
        if stop_reason: break
        print(json.dumps({'stage': 'vignettes', 'completed': len(results), 'matched': sum(f['status'] == 'matched' for f in fits), 'receipted_usd': budget.summary()['receipted_usd']}), flush=True)
    report = {'status': stop_reason or 'completed_machine_phase_pending_editorial_report', 'definitions_attempted': 200, 'vignette_candidates': 50,
              'matched': sum(f['status'] == 'matched' for f in fits), 'unmatched': sum(f['status'] == 'unmatched' for f in fits),
              'excluded_risk': sum(f['status'] == 'excluded_risk' for f in fits), 'drafted': len(results), 'initial_vignette_overlap_hits': initial_overlap_hits, 'unattempted_matched': matched_count - len(results), 'machine_passed_scenes': sum(r['accepted'] for r in results),
              'five_word_triage_pending': sum(r['five_word_triage_pending'] for r in results), 'budget': budget.summary(), 'released_entries': 0, 'full_run_authorized': False}
    (ROOT / 'reports/combined-pilot.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--execute', action='store_true'); parser.add_argument('--key-file', type=Path); args = parser.parse_args()
    if args.execute:
        if not args.key_file: parser.error('--key-file required')
        try:
            run(args.key_file)
        except (OSError, ValueError, RuntimeError) as error:
            report = {'status': 'interrupted_or_blocked', 'error_type': type(error).__name__, 'budget': Budget(ROOT / '.private/pilot/budget.sqlite', 20_000_000).summary(), 'full_run_authorized': False}
            (ROOT / 'reports/combined-pilot-interruption.json').write_text(json.dumps(report, indent=2) + '\n')
            raise
    else:
        m = verify(); print(json.dumps({'manifest_verified': True, 'status': m['status'], 'dispatch_authorized': m['dispatch_authorized'], 'paid_calls': 0}, indent=2))
