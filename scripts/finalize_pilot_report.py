"""Close the pilot from pinned results and explicit editorial decisions; no paid calls."""
import copy
import json
from collections import defaultdict
from core import ROOT, digest
from budget import Budget
from vignette_output import require_checks, output_hash, scan_generated


def finalize():
    dest = ROOT / '.private/pilot-combined'
    manifest = json.loads((ROOT / 'data/pilot-combined-preregistration.json').read_text())
    rows = copy.deepcopy(json.loads((dest / 'final-scenes.json').read_text()))
    if len(rows) != 7: raise ValueError('Every matched term must have a final outcome')
    fits = {r['term_id']: r for r in json.loads((dest / 'fit-ledger.json').read_text())}
    drops = {
        'D005639': 'The allowed redraft invents a partner saying Alex seemed distant. This family interaction is absent from the pinned card. Both judges passed it; a second redraft is forbidden.',
        'D012752': 'The allowed redraft adds that the criticism stayed with Omar for days and that he had barely slept. The card provides no duration and says only that he has not slept well since the feedback. This adds timing/severity to the sleep problem. Both judges passed it; a second redraft is forbidden.'
    }
    decisions = []
    for row in rows:
        ident = row['term_id']; accepted = ident not in drops and not row.get('failures')
        triage = []
        for hit in row['scan']['triage_5']:
            triage.append(dict(hit, decision='keep_short_permitted_card_fragment', rationale='The short ordinary phrase or fictional thought is present in the permitted ArcSim card. It is below the 15-word gate; no automatic rewrite is warranted.'))
        if accepted:
            require_checks(row['output'], fits[ident], row['context_hash'], row['scan'], row['reviews'], True)
        row.update(accepted=accepted, status='pilot_editorially_retained_private' if accepted else 'dropped_after_allowed_redraft_editorial',
                   five_word_triage_pending=False, final_editorial_reason=drops.get(ident, 'No unsupported consequential client facts found in the final scene; ordinary room actions and paraphrased dialogue are within the registered fictional-scene scope.'),
                   final_five_word_triage=triage, public_release_authorized=False)
        decisions.append({'term_id': ident, 'output_hash': output_hash(row['output']), 'reviewer': 'dictionary_session_editorial_final_read',
                          'decision': 'retain_private' if accepted else 'drop', 'reason': row['final_editorial_reason'], 'five_word_triage': triage})
    (dest / 'final-scenes-adjudicated.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'reports/vignette-editorial-decisions.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + '\n')
    batch = scan_generated([r['output'] for r in rows if r['accepted']], dest / 'refs', manifest['reference_manifest'], dest / 'final-batch-scan')
    if not batch['scan_15_passed']: raise ValueError('Final retained batch has a 15-word reference hit')
    definitions = json.loads((ROOT / '.private/pilot/recovered-results.json').read_text())
    budget = Budget(ROOT / '.private/pilot/budget.sqlite', 20_000_000).summary()
    costs = defaultdict(float)
    for key, value in budget['by_category'].items(): costs['vignette' if key.startswith('vignette_') else 'definition'] += value['receipted_usd']
    retained = sum(r['accepted'] for r in rows); dropped = len(rows) - retained
    def_passed = sum(r['status'] in ('initial_pass', 'redraft_pass') for r in definitions)
    final_drop_gate = dropped / len(rows) > manifest['stop_final_drop_fraction']
    report = {
        'status': 'stopped_vignette_final_drop_threshold' if final_drop_gate else 'pilot_complete_pending_vishnu_full_line_decision',
        'pilot_attempts_complete': True, 'registration_hash': manifest['registration_hash'],
        'definition': {'attempted': 200, 'machine_passed': def_passed, 'dropped': sum(r['status'] == 'final_drop' for r in definitions), 'incomplete': sum(r['status'] == 'incomplete' for r in definitions),
                       'receipted_usd': costs['definition'], 'per_attempted_usd': costs['definition'] / 200, 'per_machine_passed_usd': costs['definition'] / def_passed},
        'vignette': {'candidate_count': 50, 'matched': 7, 'unmatched': 38, 'excluded_risk': 5, 'drafted': 7, 'retained_private': retained, 'dropped_after_one_redraft': dropped,
                     'initial_editorial_factuality_rejections': 5, 'initial_machine_passing_with_editorial_disagreement': 5,
                     'final_two_judge_passes_overruled_by_editorial_audit': len(drops), 'initial_15_word_hits': 0, 'final_15_word_hits': 0,
                     'initial_five_word_hit_entries': 2, 'final_five_word_hit_entries_all_outputs': sum(bool(r['scan']['triage_5']) for r in rows), 'pending_five_word_triage': 0,
                     'editorial_redraft_outputs': 6, 'final_drop_fraction': dropped / len(rows), 'stop_threshold': manifest['stop_final_drop_fraction'], 'stop_threshold_crossed': final_drop_gate,
                     'receipted_usd': costs['vignette'], 'per_drafted_usd': costs['vignette'] / 7, 'per_retained_usd': costs['vignette'] / retained,
                     'per_selected_candidate_usd': costs['vignette'] / 50},
        'budget': budget, 'charged_plus_outstanding_usd': budget['receipted_usd'] + budget['unresolved_reservations_usd'],
        'cost_basis': 'Conservative standard uncached list-price estimates from provider usage receipts, not an invoice. Unknown original outcomes retain their reservations.',
        'latency_measured': False, 'latency_limitation': 'Executor omitted request start/end timestamps; this pilot reports no measured latency.',
        'source_scope': 'Independent MeSH 2026 psychology-branch pilot; not all sources or all counselling fields. Fixed ArcSim cards only for scenes.',
        'released_entries': 0, 'held_out_vishnu_release_read_complete': False, 'full_run_authorized': False, 'paid_dispatch_enabled': False,
        'recommendation': 'Do not scale the vignette writer/judge configuration unchanged. The audit found unsupported factual additions passed by both judges. Any next experiment must be preregistered; no new paid line is inferred from this report.'
    }
    copy_review = json.loads((ROOT / 'reports/definition-overlap-triage.json').read_text())['summary']
    report['definition']['final_15_word_hit_entries'] = copy_review['min_15_hit_entries']
    report['definition']['five_word_hit_entries'] = copy_review['min_5_hit_entries']
    report['definition']['five_word_triage_complete'] = copy_review['triage_complete']
    report['definition']['wording_holds_before_any_release'] = copy_review['triage_counts']['hold_for_wording_revision']
    report['definition']['machine_passed_without_copy_wording_holds'] = def_passed - copy_review['triage_counts']['hold_for_wording_revision']
    (ROOT / 'reports/combined-pilot.json').write_text(json.dumps(report, indent=2) + '\n')
    policy_path = ROOT / 'data/release-policy.json'; policy = json.loads(policy_path.read_text())
    policy.update(paid_dispatch_enabled=False, active_pilot_status=report['status'], full_run_authorized=False)
    policy_path.write_text(json.dumps(policy, indent=2) + '\n')
    (ROOT / '.private/pilot/STOP').write_text('Vignette final-drop gate crossed: 2 of 7 after the allowed redraft. No further paid calls or full run without review and a new registered decision.\n')
    (dest / 'retained-scenes.md').write_text(''.join(f"## {r['term_id']}\n\n{r['output']['scene']}\n\n{r['output']['notice_line']}\n\n" for r in rows if r['accepted']))
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__': finalize()
