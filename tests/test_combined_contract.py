import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from core import digest
from combined_contract import make_context

class CombinedContextTests(unittest.TestCase):
    def setUp(self):
        self.definition = {'id': 'test', 'term': 'Test', 'status': 'initial_pass', 'definition': 'A supported concept.', 'field': 'cognition', 'definition_version': 1, 'packet_hash': 'packet'}
        self.definition['definition_hash'] = digest({'definition': self.definition['definition'], 'field': 'cognition', 'packet_sufficient': True})
        self.fit = {'term_id': 'test', 'term': 'Test', 'type': 'experience', 'field': 'cognition', 'status': 'matched', 'risk_term': False, 'definition_hash': self.definition['definition_hash'], 'definition_version': 1, 'packet_hash': 'packet', 'card_id': 'p_1', 'builder_commit': 'pinned'}
        self.packet = {'packet_hash': 'packet'}
        self.view = {'card_id': 'p_1', 'builder_commit': 'pinned', 'card_hash': 'preview'}
    def test_term_outside_card_and_no_other_verdict(self):
        context = make_context(self.fit, self.definition, self.packet, self.view)
        self.assertEqual(context['request']['term_id'], 'test')
        self.assertNotIn('request', context['card_view']); self.assertNotIn('judges', context['definition'])
    def test_definition_text_edit_rejected_even_with_old_claimed_hash(self):
        self.definition['definition'] = 'Altered concept.'
        with self.assertRaisesRegex(ValueError, 'review hash'): make_context(self.fit, self.definition, self.packet, self.view)
    def test_changed_packet_or_card_rejected(self):
        self.packet['packet_hash'] = 'new'
        with self.assertRaisesRegex(ValueError, 'packet changed'): make_context(self.fit, self.definition, self.packet, self.view)
        self.packet['packet_hash'] = 'packet'; self.view['card_id'] = 'p_other'
        with self.assertRaisesRegex(ValueError, 'assignment changed'): make_context(self.fit, self.definition, self.packet, self.view)
    def test_risk_or_unmatched_cannot_build_writer_request(self):
        for status, risk in [('excluded_risk', True), ('unmatched', False)]:
            fit = copy.deepcopy(self.fit); fit.update(status=status, risk_term=risk)
            with self.assertRaisesRegex(ValueError, 'unmatched or risk'): make_context(fit, self.definition, self.packet, self.view)

if __name__ == '__main__': unittest.main()
