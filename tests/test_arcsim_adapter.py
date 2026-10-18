import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from arcsim_adapter import recipe_for, build_card, preview_vignette_view, vignette_view, pinned_builder
from core import digest

class ArcSimAdapterTests(unittest.TestCase):
    def setUp(self):
        self.recipe = recipe_for('example-4'); self.card = build_card(self.recipe)
    def test_exact_allowlist_and_proposed_base_hash(self):
        view = preview_vignette_view(self.card, self.recipe)
        self.assertEqual(set(view), {'card_id', 'builder_commit', 'card_hash', 'talking_style', 'profile', 'cognitive_model'})
        self.assertEqual(view['card_hash'], 'sha256:' + digest(self.card))
        self.assertNotIn('seed', view); self.assertNotIn('presenting_problem', view)
    def test_intake_fields_never_affect_view_or_preview_hash(self):
        expected = preview_vignette_view(self.card, self.recipe)
        self.card['intake_only'] = {'sexuality': 'PRIVATE_SENTINEL', 'ethnicity': 'PRIVATE_SENTINEL'}
        self.assertEqual(preview_vignette_view(self.card, self.recipe), expected)
    def test_edited_nested_text_rejected(self):
        self.card['profile']['family'][0]['note'] = 'IMPORTED TEXT'
        with self.assertRaisesRegex(ValueError, 'differs'): preview_vignette_view(self.card, self.recipe)
    def test_unknown_root_text_rejected(self):
        self.card['session_transcript'] = 'IMPORTED TEXT'
        with self.assertRaisesRegex(ValueError, 'differs'): preview_vignette_view(self.card, self.recipe)
    def test_json_boolean_integer_substitution_rejected(self):
        self.card['profile']['family'][0]['alive'] = int(self.card['profile']['family'][0]['alive'])
        with self.assertRaisesRegex(ValueError, 'differs'): preview_vignette_view(self.card, self.recipe)
    def test_scenario_binding_rejected(self):
        self.card['persona_id'] = 'scenario:closed'
        with self.assertRaisesRegex(ValueError, 'Scenario'): preview_vignette_view(self.card, self.recipe)
    def test_recipe_changes_rejected(self):
        for key, value in [('fit', False), ('problem', 'anxiety'), ('style', 'plain'), ('seed', 1000), ('builder_commit', 'later')]:
            bad = copy.deepcopy(self.recipe); bad[key] = value
            with self.assertRaises(ValueError): build_card(bad)
    def test_output_mutation_does_not_change_card(self):
        before = copy.deepcopy(self.card); view = preview_vignette_view(self.card, self.recipe)
        view['profile']['family'][0]['name'] = 'Changed'
        self.assertEqual(before, self.card)
    def test_pinned_builder_bytes_checked_before_loading(self):
        with patch.object(Path, 'read_bytes', return_value=b'altered'):
            with self.assertRaisesRegex(ValueError, 'Pinned builder'): pinned_builder()
    def test_unregistered_adapter_baseline_rejected(self):
        with patch('arcsim_adapter.json.loads', return_value={'status': 'draft'}):
            with self.assertRaisesRegex(RuntimeError, 'frozen initial'): vignette_view(self.card, self.recipe)
    def test_fixed_wording_exercised(self):
        card = build_card(recipe_for(1))
        self.assertIn('Something awful is about to happen.', card['cognitive_model']['automatic_thoughts'])
        self.assertNotIn('Something terrible is going to happen.', card['cognitive_model']['automatic_thoughts'])

if __name__ == '__main__': unittest.main()
