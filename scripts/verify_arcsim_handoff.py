"""Rebuild the fixed verification cards from pinned local Git objects; no API calls."""
import argparse
import copy
import hashlib
import json
import platform
import re
import subprocess
import types
from pathlib import Path
from core import ROOT

BUILDER_COMMIT = '12bd28281f5d8ed607e1ff6f46e7246293f925f3'
HANDOFF_COMMIT = '2973eb9a84d62386022a8aecb5e4a5450cb0ff6e'
PREVIOUS_COMMIT = 'd0ccc6cfa596cf72e382ed2c79ddaa9198a645ff'
BUILDER_PATH = 'arcsim/arcsim/persona/cognitive.py'
SCHEMA_PATH = 'arcsim/arcsim/schemas/persona.schema.json'
BUILDER_SHA256 = '31088a31425b31a2de29a8e8ed5ee4f656822983fbf6b07bc44f9dd38415453e'
SCHEMA_SHA256 = '5d1d5782f20fad84e113658ca5f703bd9a312ca0c8fea10bd4bb08bd47c86829'
OLD = 'Something terrible is going to happen.'
NEW = 'Something awful is about to happen.'

def expected_update(card):
    result = copy.deepcopy(card)
    result['cognitive_model']['automatic_thoughts'] = result['cognitive_model']['automatic_thoughts'].replace(OLD, NEW)
    return result

def verify(repository, handoff):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repository), *args])
    def blob(commit, path):
        return git('show', f'{commit}:{path}')
    def load_builder(commit, expected_sha):
        raw = blob(commit, BUILDER_PATH)
        if hashlib.sha256(raw).hexdigest() != expected_sha:
            raise ValueError('Pinned builder hash differs')
        module = types.ModuleType('verified_arcsim_builder')
        exec(compile(raw, f'{commit}/{BUILDER_PATH}', 'exec'), module.__dict__)
        return module
    handoff_raw = handoff.read_bytes()
    if handoff_raw != blob(HANDOFF_COMMIT, 'arcsim/PSYCH_TERMS_INTERFACE.md'):
        raise ValueError('Attachment differs from pinned handoff')
    schema = blob(BUILDER_COMMIT, SCHEMA_PATH)
    if hashlib.sha256(schema).hexdigest() != SCHEMA_SHA256:
        raise ValueError('Pinned schema hash differs')
    current = load_builder(BUILDER_COMMIT, BUILDER_SHA256)
    previous = load_builder(PREVIOUS_COMMIT, '3a3a849492eba8d2141c920ba8d09c0fefdfd884d4c85537a178ad8a3117cd85')
    example = json.loads(re.findall(r'```json\n(.*?)\n```', handoff_raw.decode(), re.S)[-1])
    example_base = {k: v for k, v in example.items() if k != 'intake_only'}
    assert current.build('example-4', problem=None, style=None, fit=True) == example_base
    assert previous.build('example-4', problem=None, style=None, fit=True) == example_base
    assert current.assign_intake_only({'p_example-4': example_base}, {'p_example-4': 'other'})['p_example-4'] == example['intake_only']
    changed = []
    cards = []
    for seed in range(1000):
        old = previous.build(seed, problem=None, style=None, fit=True)
        card = current.build(seed, problem=None, style=None, fit=True)
        assert card == expected_update(old), f'Unexpected change for seed {seed}'
        assert current.build(seed, problem=None, style=None, fit=False) == previous.build(seed, problem=None, style=None, fit=False)
        if card != old:
            changed.append(seed)
        assert OLD not in card['cognitive_model']['automatic_thoughts']
        names = [card['profile']['name']] + [f['name'] for f in card['profile']['family']]
        assert len(names) == len(set(names))
        if card['profile']['occupation'] in current.NO_JOB:
            assert not current.WORK.search(card['cognitive_model']['situation'].lower())
            assert not current.WORK.search(card['cognitive_model']['coping_strategies'].lower())
            assert 'Appearance: dressed for work' not in card['profile']['mental_status']
        cards.append(card)
    assert changed, 'Regression set must exercise the wording change'
    private = ROOT / '.private/arcsim-verification'
    private.mkdir(parents=True, exist_ok=True)
    # Serialization here is storage only. No card/view hash rule is introduced or changed.
    (private / 'cards.json').write_text(json.dumps([example_base] + cards, indent=2) + '\n')
    report = {
        'handoff_commit': HANDOFF_COMMIT, 'builder_commit': BUILDER_COMMIT,
        'handoff_sha256': hashlib.sha256(handoff_raw).hexdigest(),
        'attached_matches_committed_handoff': True, 'repository': 'cloudronin/uofa-lab',
        'code_hashes': {BUILDER_PATH: BUILDER_SHA256, SCHEMA_PATH: SCHEMA_SHA256},
        'previous_builder_commit': PREVIOUS_COMMIT,
        'fixed_build_inputs': {'example_seed': 'example-4', 'integer_seeds': {'start': 0, 'stop_exclusive': 1000}, 'problem': None, 'style': None, 'fit': True},
        'python_runtime': platform.python_version(),
        'example_unchanged': True, 'rebuilt_fit_cards': len(cards) + 1,
        'changed_integer_seed_count': len(changed), 'changed_integer_seeds': changed,
        'only_expected_automatic_thought_replacement': True,
        'fit_false_unchanged_for_1000_seeds': True,
        'three_previous_regression_checks_passed': True,
        'fields_changed': False, 'card_hash_rule_changed': False,
        'card_hash_rule_status': 'not_implemented_or_registered_in_dictionary',
        'seed_parameter_changes_require_vishnu': True,
        'field_or_card_hash_rule_changes_require_vishnu': True,
        'pilot_card_sample_selected': False, 'paid_calls': 0,
        'private_pool_overlap_not_rerun': True
    }
    (ROOT / 'docs/PSYCH_TERMS_INTERFACE.md').write_bytes(handoff_raw)
    (ROOT / 'reports/arcsim-handoff-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'changed_integer_seeds'}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, required=True)
    args = parser.parse_args()
    verify(args.repository, args.handoff)
