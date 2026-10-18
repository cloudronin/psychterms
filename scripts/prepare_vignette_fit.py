"""Select the pilot's room-term candidates before card-fit outcomes; no API calls."""
import json
import random
from core import ROOT, digest

# Explicit editorial eligibility review of the existing independent 200-term sample.
# It asks whether the concept can occur in a counselling room, not whether a card fits.
TYPES = {
    'presentation': '''D000068376 D000074043 D000077062 D000079524 D000082002 D000084783 D000084802 D000086522 D000088102 D000092442 D000093902 D000094964 D000096865 D000275 D000381 D000425 D000430 D000856 D001332 D001523 D002653 D003147 D003193 D003858 D004775 D005162 D006677 D007174 D009110 D009440 D009771 D010200 D010259 D010554 D010623 D012560 D012565 D012753 D012934 D019959 D019960 D019964 D020178 D020187 D020774 D020922 D052018 D053207 D057180 D061218 D065446 D066229''',
    'skill': '''D000071441 D000079062 D000083626 D001326 D001346 D001521 D001638 D003887 D007171 D008388 D008884 D009147 D009629 D009974 D011616 D012064 D012094 D012731 D012949 D014167 D019122 D020557 D023801 D056147 D058611''',
    'experience': '''D000067489 D000067656 D000533 D001288 D003657 D004291 D005120 D005239 D005639 D007439 D007578 D008570 D009042 D010467 D011889 D012752 D012919 D012929 D019545 D028681 D035501 D037921 D055500 D058445 D061347 D062487 D000095422''',
    'assessment': '''D000073220 D002416 D008609 D008950 D010555 D010556 D013803 D058010''',
    'risk': '''D000081042 D000088782 D003419 D004637 D005391 D017406 D047568'''
}
RISK_REASONS = {
    'D000081042': 'The concept involves desired bodily harm; this interface provides no risk scenes.',
    'D000088782': 'Trauma/disaster first-response support is outside the risk-free card interface.',
    'D003419': 'Crisis response is outside the risk-free card interface.',
    'D004637': 'Psychiatric emergency response is outside the risk-free card interface.',
    'D005391': 'Firesetting entails harm risk; no risk facts may be added to a card.',
    'D017406': 'Sexual-harassment safety/ethics scenes are excluded from the first risk-free vignette release.',
    'D047568': 'Sexual-risk behaviour is outside the risk-free card interface.'
}
SELECTION_SEED = 2026101803


def prepare():
    rows = json.loads((ROOT / '.private/pilot/recovered-results.json').read_text())
    classifications = {ident: kind for kind, ids in TYPES.items() for ident in ids.split()}
    if sum(len(ids.split()) for ids in TYPES.values()) != len(classifications):
        raise ValueError('Repeated eligibility ID')
    pool = []; eligibility = []
    for row in rows:
        kind = classifications.get(row['id'])
        reviewed = row['status'] in ('initial_pass', 'redraft_pass')
        eligible = kind is not None and reviewed
        eligibility.append({'term_id': row['id'], 'term': row['term'], 'field': row['field'], 'type': kind,
                            'eligible': eligible, 'reason': 'Room-relevant concept with two passing recorded machine reviews; card fit not yet evaluated.' if eligible else
                            'Definition review is incomplete or failed.' if not reviewed else 'Research/discipline, sensory/biological process or otherwise outside this room-scene pilot scope.'})
        if eligible: pool.append(row)
    sample = sorted(random.Random(SELECTION_SEED).sample(sorted(pool, key=lambda r: r['id']), 50), key=lambda r: r['id'])
    decisions = []
    for row in sample:
        ident = row['id']; kind = classifications[ident]
        decisions.append({'term_id': ident, 'term': row['term'], 'field': row['field'], 'type': kind,
                          'definition_version': row['definition_version'], 'definition_hash': row['definition_hash'], 'packet_hash': row['packet_hash'],
                          'risk_term': kind == 'risk', 'status': 'excluded_risk' if kind == 'risk' else 'pending',
                          'card_id': None, 'reason': RISK_REASONS.get(ident, ''), 'reviewer': 'dictionary_session_editorial_classification'})
    selection = {'selection_seed': SELECTION_SEED, 'source': 'independent frozen 200-term pilot, no legacy vocabulary', 'eligible_pool_count': len(pool),
                 'candidate_count': len(sample), 'eligible_pool_hash': digest([r['id'] for r in sorted(pool, key=lambda r: r['id'])]),
                 'candidate_ids': [r['id'] for r in sample], 'resampling_after_fit_allowed': False,
                 'selection_stage': 'after definition receipt recovery, before term-to-card fit outcomes', 'site_release_authorized': False}
    target = ROOT / 'data/vignette-pilot-selection.json'
    if target.exists() and json.loads(target.read_text()) != selection:
        raise ValueError('Pilot term selection already fixed; do not replace it')
    target.write_text(json.dumps(selection, indent=2) + '\n')
    (ROOT / 'data/vignette-eligibility.json').write_text(json.dumps(eligibility, indent=2) + '\n')
    dest = ROOT / '.private/pilot-combined'; dest.mkdir(exist_ok=True)
    initial = dest / 'fit-decisions.initial.json'
    if initial.exists() and json.loads(initial.read_text()) != decisions:
        raise ValueError('Initial fit selection already fixed')
    initial.write_text(json.dumps(decisions, indent=2) + '\n')
    print(json.dumps(selection, indent=2))
    return decisions

if __name__ == '__main__': prepare()
