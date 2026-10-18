"""Materialize the explicit editorial fit review; no model calls or inferred matches."""
import copy
import json
from core import ROOT, digest
from arcsim_adapter import build_card, recipe_for, preview_vignette_view, COMMIT
from vignette_fit import summarize


def build():
    dest = ROOT / '.private/pilot-combined'
    rows = copy.deepcopy(json.loads((dest / 'fit-decisions.initial.json').read_text()))
    review = json.loads((ROOT / 'data/vignette-fit-review.json').read_text())
    covered = set(review['matched']) | set(review['additional_risk_exclusions']) | set(review['unmatched'])
    if covered != {r['term_id'] for r in rows if r['status'] != 'excluded_risk'}:
        raise ValueError('Fit review does not cover the exact candidate sample')
    payloads = []
    for row in rows:
        ident = row['term_id']; row['reviewer'] = review['reviewer']
        if ident in review['matched']:
            decision = review['matched'][ident]; recipe = recipe_for(decision['seed']); card = build_card(recipe)
            row.update(status='matched', card_id=card['persona_id'], builder_commit=COMMIT, build_recipe=recipe, reason='')
            row['fit_evidence'] = {'problem': card['presenting_problem'], 'history': card['cognitive_model']['relevant_history'],
                                   'situation': card['cognitive_model']['situation'], 'mental_status': ' | '.join(card['profile']['mental_status']),
                                   'rationale': decision['rationale']}
            payloads.append({'term_id': ident, 'recipe': recipe, 'card_view_preview': preview_vignette_view(card, recipe), 'production_authorized': False})
        elif ident in review['additional_risk_exclusions']:
            row.update(status='excluded_risk', risk_term=True, reason=review['additional_risk_exclusions'][ident])
        elif ident in review['unmatched']:
            row.update(status='unmatched', reason=review['unmatched'][ident])
    summary = summarize(rows)
    summary.update(status='editorial_fit_review_complete_no_scenes_drafted', candidate_sample_hash=digest([r['term_id'] for r in rows]),
                   matched_terms=[{'term_id': r['term_id'], 'term': r['term'], 'card_id': r['card_id']} for r in rows if r['status'] == 'matched'],
                   fit_ledger_hash=digest(rows), scene_drafted=0, scene_accepted=0, production_authorized=False,
                   risk_entry_notice='No scene is provided for this risk term.', paid_calls=0)
    (dest / 'fit-ledger.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    (dest / 'card-view-previews.json').write_text(json.dumps(payloads, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'reports/vignette-fit.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'no_vignette_reasons'}, indent=2))
    return rows

if __name__ == '__main__': build()
