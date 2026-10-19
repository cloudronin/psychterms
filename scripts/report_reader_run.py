"""Summarize the private reader ledger and receipt-backed outcomes after execution finishes, without exporting receipts."""
import collections
import json
import math
from pathlib import Path
from core import ROOT, digest
from budget import Budget
from run_reader_reviews import MODELS


def report(dest=ROOT / '.private/reader-reviews'):
    registration = json.loads((dest / 'preregistration.json').read_text())
    jobs = json.loads((dest / 'jobs.json').read_text())
    assert registration['registration_hash'] == digest({k: v for k, v in registration.items() if k != 'registration_hash'})
    assert registration['job_set_hash'] == digest(jobs)
    outcomes = {}
    for path in (dest / 'calls').glob('*.json'):
        proof = json.loads(path.read_text())
        assert proof['registration_hash'] == registration['registration_hash']
        assert (dest / 'receipts' / (proof['receipt_id'] + '.json')).exists()
        outcomes[proof['request_hash']] = proof
    by_model = {}
    finish_reasons = collections.Counter()
    refusals = 0
    total_charge = 0
    for path in (dest / 'receipts').glob('*.json'):
        if path.name.endswith('-error.json'):
            continue
        receipt = json.loads(path.read_text())
        model = receipt['model']
        assert model in MODELS and receipt.get('service_tier') == 'default'
        row = by_model.setdefault(model, collections.Counter())
        usage = receipt['usage']
        cached = usage.get('prompt_tokens_details', {}).get('cached_tokens', 0)
        price = MODELS[model]
        charge = math.ceil((usage['prompt_tokens'] - cached) * price['input'] + cached * price['cached_input'] + usage['completion_tokens'] * price['output'])
        total_charge += charge
        row.update(receipts=1, input_tokens=usage['prompt_tokens'], cached_input_tokens=cached, output_tokens=usage['completion_tokens'], charged_microusd=charge)
        for choice in receipt['choices']:
            finish_reasons[choice['finish_reason']] += 1
            refusals += bool(choice.get('message', {}).get('refusal'))
    for proof in outcomes.values():
        by_model[proof['model']]['passes' if proof['passed'] else 'rejections'] += 1
    for row in by_model.values():
        row['receipted_usd'] = row.pop('charged_microusd') / 1e6
    budget = Budget(dest / 'budget.sqlite', int(float(registration['authorized_cap_usd']) * 1e6)).summary()
    assert round(budget['receipted_usd'] * 1e6) == total_charge, 'Receipt/ledger mismatch; run this report after the reader process finishes'
    entries = {}
    for job in jobs:
        path = ROOT / 'data/entries' / (job['id'] + '.json')
        if job['id'] not in entries:
            entry = json.loads(path.read_text())
            proofs = ([entry['model_review']] if entry.get('model_review') else []) + entry.get('reader_reviews', [])
            entries[job['id']] = {p['model']: p['passed'] for p in proofs if p['model'] in MODELS}
    pairs = [list(value.values()) for value in entries.values() if len(value) == 2]
    errors = collections.Counter(json.loads(p.read_text())['error_type'] for p in (dest / 'receipts').glob('*-error.json'))
    return {
        'line': registration['line'], 'registration_hash': registration['registration_hash'],
        'job_set_hash': registration['job_set_hash'], 'registered_calls': len(jobs),
        'valid_new_reader_verdicts': len(outcomes), 'calls_without_valid_verdict': len(jobs) - len(outcomes),
        'entries_in_registered_run': len(entries), 'reused_prior_mini_passes': 198,
        'complete_reader_pairs_including_reused_passes': len(pairs),
        'both_pass': sum(all(p) for p in pairs), 'both_reject': sum(not any(p) for p in pairs),
        'disagreements': sum(p[0] != p[1] for p in pairs),
        'reader_models': by_model, 'budget': budget,
        'receipt_finish_reasons': dict(finish_reasons), 'explicit_provider_refusals': refusals,
        'transport_or_schema_errors': dict(errors),
        'new_reader_cost_per_registered_entry_usd': round(budget['receipted_usd'] / len(entries), 6),
        'limitations': 'Model verdicts against pinned packets; not human review. Costs exclude reused pilot passes. Unknown charges retain full reservations. No redrafting or scenes on this line.'
    }


if __name__ == '__main__':
    result = report()
    (ROOT / 'reports/independent-readers.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
