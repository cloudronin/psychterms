"""Reconcile all drafting-line receipts after dispatch finishes; export aggregate costs only."""
import collections
import json
import math
from pathlib import Path
from core import ROOT, digest
from budget import Budget


def report(dest=ROOT / '.private/candidate-drafts'):
    current = json.loads((dest / 'preregistration.json').read_text())
    manifests = {current['registration_hash']: current}
    for path in (dest / 'registrations').glob('*.json'):
        if path.name.endswith('-packets.json'):
            continue
        manifest = json.loads(path.read_text())
        assert manifest['registration_hash'] == digest({k: v for k, v in manifest.items() if k != 'registration_hash'})
        manifests[manifest['registration_hash']] = manifest
    assert all(m['model'] == current['model'] and m['prices_per_million'] == current['prices_per_million'] for m in manifests.values())
    proofs = {}
    for path in (dest / 'calls').glob('*.json'):
        proof = json.loads(path.read_text())
        assert proof['registration_hash'] in manifests and proof['model'] == current['model']
        assert (dest / 'receipts' / (proof['receipt_id'] + '.json')).exists()
        proofs[proof['request_hash']] = proof
    totals = collections.Counter()
    prices = current['prices_per_million']
    for path in (dest / 'receipts').glob('*.json'):
        if path.name.endswith('-error.json'):
            continue
        receipt = json.loads(path.read_text())
        assert receipt['model'] == current['model'] and receipt.get('service_tier') == 'default'
        usage = receipt['usage']
        cached = usage.get('prompt_tokens_details', {}).get('cached_tokens', 0)
        charge = math.ceil((usage['prompt_tokens'] - cached) * prices['input'] + cached * prices['cached_input'] + usage['completion_tokens'] * prices['output'])
        totals.update(receipts=1, input_tokens=usage['prompt_tokens'], cached_input_tokens=cached, output_tokens=usage['completion_tokens'], microusd=charge)
    budget = Budget(dest / 'budget.sqlite', int(float(current['authorized_cap_usd']) * 1e6)).summary()
    assert round(budget['receipted_usd'] * 1e6) == totals.pop('microusd'), 'Receipt/ledger mismatch; run only after drafting finishes'
    entries = [json.loads(p.read_text()) for p in (ROOT / 'data/entries').glob('*.json')]
    line_entries = [e for e in entries if e.get('draft_evidence', {}).get('registration_hash') in manifests]
    outcomes = json.loads((dest / 'outcomes.json').read_text())
    return {
        'line': current['line'], 'current_registration_hash': current['registration_hash'],
        'model': current['model'], 'registration_count': len(manifests),
        'budget': budget, 'receipt_usage': dict(totals), 'unique_cached_request_results': len(proofs),
        'packet_sufficient_results': sum(p['parsed']['packet_sufficient'] for p in proofs.values()),
        'packet_insufficient_results': sum(not p['parsed']['packet_sufficient'] for p in proofs.values()),
        'raw_entries_with_this_line_evidence': len(line_entries),
        'latest_term_outcomes': dict(collections.Counter(o.get('reason', o.get('status', 'unknown')) for o in outcomes.values())),
        'receipted_usd_per_raw_entry': round(budget['receipted_usd'] / len(line_entries), 6) if line_entries else None,
        'reader_report': 'independent-readers.json', 'status_report': 'release-note.md',
        'vignettes': 0,
        'limitations': 'Cumulative drafting-line costs include insufficient packets, redrafts, retries and withheld output. Raw entries include later reader drops. Source alternatives can produce multiple request results per term. Unknown charges remain reserved. Earlier pilot costs are separate.'
    }


if __name__ == '__main__':
    result = report()
    (ROOT / 'reports/candidate-drafting.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
