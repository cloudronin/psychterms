"""Assemble the combined pilot; freeze only after the card-hash approval is recorded."""
import argparse
import hashlib
import json
import math
import platform
from core import ROOT, digest
from budget import Budget
from combined_contract import DRAFT_PROMPT, JUDGE_PROMPT, DRAFT_SCHEMA, JUDGE_SCHEMA
from vignette_output import reference_manifest


def text_values(value):
    if isinstance(value, str): yield value
    elif isinstance(value, dict):
        for item in value.values(): yield from text_values(item)
    elif isinstance(value, list):
        for item in value: yield from text_values(item)


def prepare(freeze=False):
    dest = ROOT / '.private/pilot-combined'
    historical = json.loads((ROOT / 'data/pilot-preregistration.json').read_text())
    packets = json.loads((ROOT / '.private/pilot/packets.json').read_text())
    fit = json.loads((dest / 'fit-ledger.json').read_text())
    if len(fit) != 50 or any(r['status'] == 'pending' for r in fit): raise ValueError('Complete the exact 50-candidate fit ledger first')
    definitions = json.loads((ROOT / '.private/pilot/recovered-results.json').read_text())
    chosen = {r['term_id'] for r in fit if r['status'] == 'matched'}
    selected = [r for r in definitions if r['id'] in chosen]
    (dest / 'selected-definitions.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2) + '\n')
    previews = json.loads((dest / 'card-view-previews.json').read_text())
    refs = dest / 'refs'; refs.mkdir(exist_ok=True)
    for packet in packets: (refs / (packet['id'] + '.txt')).write_text(packet['text'] + '\n')
    for item in previews:
        view = item['card_view_preview']
        # Only allowed content, never the full card, intake fields, transcripts or legacy corpus.
        text = '\n'.join(text_values({'talking_style': view['talking_style'], 'profile': view['profile'], 'cognitive_model': view['cognitive_model']}))
        (refs / ('card-' + item['term_id'] + '.txt')).write_text(text + '\n')
    expected_names = {p['id'] + '.txt' for p in packets} | {'card-' + p['term_id'] + '.txt' for p in previews}
    if set(reference_manifest(refs)) != expected_names: raise ValueError('Unexpected comparison reference')
    contract = json.loads((ROOT / 'data/arcsim-adapter-contract.json').read_text())
    approved = contract.get('status') == 'frozen_initial_adapter_baseline' and contract.get('production_enabled') is True and contract.get('initial_rule_uses_existing_core_digest') is True
    if freeze and not approved: raise RuntimeError('Initial adapter baseline must be fixed before freezing')
    target = ROOT / 'data/pilot-combined-preregistration.json'
    if target.exists() and json.loads(target.read_text()).get('status') == 'frozen': raise RuntimeError('Combined registration is already frozen; do not replace it')
    files = [p for root in ('scripts', 'schema') for p in (ROOT / root).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    files += [ROOT / 'data' / name for name in ('arcsim-adapter-contract.json', 'vignette-policy.json', 'vignette-pilot-selection.json', 'vignette-eligibility.json', 'vignette-fit-review.json', 'pilot-preregistration.json', 'sources.json', 'fields.json')]
    files += [ROOT / 'docs' / name for name in ('PSYCH_TERMS_INTERFACE.md', 'vignette-pilot-protocol.md', 'arcsim-interface-agreement.md')]
    private_names = ['.private/pilot/packets.json', '.private/pilot/executor-original.py', '.private/pilot-combined/fit-ledger.json', '.private/pilot-combined/selected-definitions.json', '.private/pilot-combined/card-view-previews.json']
    budget = Budget(ROOT / '.private/pilot/budget.sqlite', 20_000_000).summary()
    prices = historical['prices_per_million']; maximum = max(math.ceil((12000 + 512) * p['input'] + 1000 * p['output']) for p in prices.values())
    # 6 logical scene calls per match (one redraft plus two judges again), each with one transport retry.
    # At most 3 logical completions for each of the 2 interrupted definition units, also with one retry.
    maximum_calls = len(chosen) * 6 * 2 + 2 * 3 * 2
    cap_with_carry = budget['receipted_usd'] + budget['unresolved_reservations_usd'] + maximum_calls * maximum / 1e6
    if cap_with_carry > 20: raise ValueError('Worst-case carried reservation exceeds the pilot line')
    manifest = {
        'line': 'pilot-200-definitions-50-vignette-candidates-v02', 'status': 'frozen' if freeze else 'draft_awaiting_final_verification',
        'dispatch_authorized': freeze, 'cap_usd': '20.00', 'full_run_authorized': False,
        'supersedes_future_dispatch_under': historical['preregistration_hash'], 'historical_definition_count': 200,
        'definition_continuation': 'Reuse verified receipts; resume only missing transport outcomes for two incomplete units with the original redraft request and original two-judge contract; no additional editorial redraft.',
        'vignette_candidate_count': 50, 'vignette_matched_count': len(chosen),
        'unmatched_count': sum(r['status'] == 'unmatched' for r in fit), 'excluded_risk_count': sum(r['status'] == 'excluded_risk' for r in fit),
        'term_sample_seed': 2026101803, 'resampling_after_fit_allowed': False, 'fit_ledger_hash': digest(fit),
        'definition_machine_results_at_registration': {'passed': sum(r['status'] in ('initial_pass', 'redraft_pass') for r in definitions), 'dropped': sum(r['status'] == 'final_drop' for r in definitions), 'incomplete': sum(r['status'] == 'incomplete' for r in definitions)},
        'models': historical['models'], 'prices_per_million': prices, 'pricing_checked_on': '2026-10-18',
        'pricing_urls': historical['pricing_urls'], 'price_basis': 'Standard uncached text; no residency uplift, tools or paid extras; ignore cache discounts conservatively.',
        'max_completion_tokens': 1000, 'max_request_bytes': 12000, 'reasoning_effort': 'low', 'workers': 1,
        'transport_schema_retries': 1, 'editorial_redrafts': 1, 'both_distinct_judges_required': True,
        'stop_initial_overlap_fraction': 0.10, 'stop_final_drop_fraction': 0.20,
        'threshold_denominators': 'Definitions: 200 attempts. Vignettes: matched scenes attempted, not all 50 candidates. Risk/unmatched exclusions are not model failures.',
        'copy_threshold_words': 15, 'five_word_output_hits': 'editorial_triage_required_before_acceptance',
        'reference_manifest': reference_manifest(refs), 'reference_scope': '200 fresh permitted MeSH packets and seven permitted card-view texts; no legacy or private producer pools.',
        'scene_word_count': '100-150 words using unchanged overlap_scan.words; notice_line excluded from scene length but scanned/judged.',
        'draft_prompt': DRAFT_PROMPT, 'judge_prompt': JUDGE_PROMPT, 'draft_schema': DRAFT_SCHEMA, 'judge_schema': JUDGE_SCHEMA,
        'hash_contract': 'data/arcsim-adapter-contract.json', 'python_runtime': platform.python_version(),
        'carried_budget': budget, 'shared_ledger': '.private/pilot/budget.sqlite',
        'maximum_remaining_request_attempts': maximum_calls, 'maximum_reservation_per_attempt_usd': maximum / 1e6,
        'maximum_spent_plus_held_after_worst_case_usd': cap_with_carry,
        'reservation_rule': 'Before each call reserve UTF-8 request bytes + 512 input tokens plus full completion cap; spent plus all outstanding reservations must stay within $20; unreceipted outcomes retain reserves.',
        'file_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        'private_input_sha256': {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in private_names},
        'released_entries': 0
    }
    manifest['registration_hash'] = digest(manifest)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ('status', 'dispatch_authorized', 'vignette_candidate_count', 'vignette_matched_count', 'unmatched_count', 'excluded_risk_count', 'maximum_spent_plus_held_after_worst_case_usd', 'registration_hash')}, indent=2))
    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--freeze', action='store_true'); args = parser.parse_args(); prepare(args.freeze)
