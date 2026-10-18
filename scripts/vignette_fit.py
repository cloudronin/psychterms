"""Audit recorded term-to-card fit decisions; never infer semantic fit from labels."""
import argparse
import collections
import json
from pathlib import Path


def summarize(records):
    counts = collections.Counter(candidates=len(records), pending_fit=0, excluded_risk=0, unmatched=0, matched=0)
    seen = set()
    reasons = collections.Counter()
    for row in records:
        ident = row['term_id']
        if ident in seen:
            raise ValueError('Duplicate term fit decision')
        seen.add(ident)
        if type(row.get('risk_term')) is not bool:
            raise ValueError('Explicit risk classification required')
        status = row['status']
        if status not in ('pending', 'excluded_risk', 'unmatched', 'matched'):
            raise ValueError('Unknown fit decision')
        if row['risk_term'] and status != 'excluded_risk':
            raise ValueError('Risk terms cannot enter the card fit or drafting path')
        if not row['risk_term'] and status == 'excluded_risk':
            raise ValueError('Risk exclusion requires risk classification')
        if status == 'matched':
            if not row.get('field') or not row.get('type') or not row.get('definition_version'):
                raise ValueError('Match must pin term field, type and definition version')
            if not row.get('card_id', '').startswith('p_') or not row.get('builder_commit'):
                raise ValueError('Match must name an unbound pinned card')
            evidence = row.get('fit_evidence', {})
            if not all(isinstance(evidence.get(k), str) and evidence[k].strip() for k in ('problem', 'history', 'situation', 'mental_status', 'rationale')):
                raise ValueError('Field/problem labels alone do not establish fit; record story and mental-status evidence')
        if status in ('unmatched', 'excluded_risk'):
            if not row.get('reason', '').strip():
                raise ValueError('No-vignette decision requires a reason')
            if row.get('card_id') is not None:
                raise ValueError('No-vignette decision cannot assign a card')
            reasons[row['reason']] += 1
        counts['pending_fit' if status == 'pending' else status] += 1
    return dict(counts, no_vignette_reasons=dict(reasons), fit_complete=counts['pending_fit'] == 0,
                semantic_fit_verified_by_script=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decisions', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(json.loads(args.decisions.read_text())), indent=2))
