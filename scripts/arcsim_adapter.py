"""Pinned local ArcSim projection with a frozen initial adapter baseline."""
import copy
import hashlib
import importlib.util
import json
from core import ROOT, canonical, digest

COMMIT = '12bd28281f5d8ed607e1ff6f46e7246293f925f3'
BUILDER_SHA = '31088a31425b31a2de29a8e8ed5ee4f656822983fbf6b07bc44f9dd38415453e'
SCHEMA_SHA = '5d1d5782f20fad84e113658ca5f703bd9a312ca0c8fea10bd4bb08bd47c86829'
PROFILE_FIELDS = ('name', 'age', 'gender', 'occupation', 'living_situation', 'relationship_status', 'family', 'details', 'setting', 'counselling_type', 'mental_status')
COGNITIVE_FIELDS = ('situation', 'relevant_history', 'emotions', 'automatic_thoughts', 'intermediate_beliefs', 'core_beliefs', 'coping_strategies', 'behaviors')
FAMILY_FIELDS = {'relation', 'name', 'alive', 'where', 'note'}


def pinned_builder():
    path = ROOT / 'scripts/vendor/arcsim_persona/cognitive.py'
    if hashlib.sha256(path.read_bytes()).hexdigest() != BUILDER_SHA:
        raise ValueError('Pinned builder changed')
    schema = path.parent / 'persona.schema.json'
    if hashlib.sha256(schema.read_bytes()).hexdigest() != SCHEMA_SHA:
        raise ValueError('Pinned card schema changed')
    spec = importlib.util.spec_from_file_location('pinned_arcsim_persona', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_recipe(recipe):
    if set(recipe) != {'seed', 'problem', 'style', 'fit', 'builder_commit'}:
        raise ValueError('Exact fixed recipe required')
    if recipe['builder_commit'] != COMMIT or recipe['problem'] is not None or recipe['style'] is not None or recipe['fit'] is not True:
        raise ValueError('Builder or fixed parameters changed')
    seed = recipe['seed']
    if not (seed == 'example-4' or type(seed) is int and 0 <= seed < 1000):
        raise ValueError('Seed outside fixed pool')


def recipe_for(seed):
    recipe = {'seed': seed, 'problem': None, 'style': None, 'fit': True, 'builder_commit': COMMIT}
    validate_recipe(recipe)
    return recipe


def build_card(recipe):
    validate_recipe(recipe)
    return pinned_builder().build(recipe['seed'], problem=None, style=None, fit=True)


def preview_vignette_view(card, recipe):
    """Demonstrate the proposed hash rule; never a production dispatch authorization."""
    expected = build_card(recipe)
    if not isinstance(card, dict) or str(card.get('persona_id', '')).startswith('scenario:'):
        raise ValueError('Scenario-bound card is forbidden')
    # Intake-only data is discarded without copying, hashing, or serializing it.
    base = {key: value for key, value in card.items() if key != 'intake_only'}
    if canonical(base) != canonical(expected):
        raise ValueError('Card differs from exact pinned builder output')
    profile = {key: copy.deepcopy(base['profile'][key]) for key in PROFILE_FIELDS}
    for member in profile['family']:
        if set(member) - FAMILY_FIELDS:
            raise ValueError('Unexpected family field')
    return {'card_id': base['persona_id'], 'builder_commit': COMMIT, 'card_hash': 'sha256:' + digest(expected),
            'talking_style': base['talking_style'], 'profile': profile,
            'cognitive_model': {key: copy.deepcopy(base['cognitive_model'][key]) for key in COGNITIVE_FIELDS}}


def vignette_view(card, recipe):
    contract_path = ROOT / 'data/arcsim-adapter-contract.json'
    contract = json.loads(contract_path.read_text())
    if contract.get('status') != 'frozen_initial_adapter_baseline' or contract.get('production_enabled') is not True:
        raise RuntimeError('A frozen initial adapter baseline is required')
    manifest_path = ROOT / 'data/pilot-combined-preregistration.json'
    if not manifest_path.exists(): raise RuntimeError('Combined registration is required')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('status') != 'frozen' or manifest.get('file_sha256', {}).get('data/arcsim-adapter-contract.json') != hashlib.sha256(contract_path.read_bytes()).hexdigest():
        raise RuntimeError('Adapter baseline is not pinned by the frozen combined PREREG')
    return preview_vignette_view(card, recipe)
