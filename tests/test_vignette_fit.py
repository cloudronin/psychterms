import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from vignette_fit import summarize

class VignetteFitTests(unittest.TestCase):
    def test_risk_cannot_be_matched(self):
        with self.assertRaisesRegex(ValueError, 'Risk terms cannot'):
            summarize([{'term_id': 'test-risk', 'risk_term': True, 'status': 'matched'}])
    def test_no_fitting_card_records_reason_and_no_assignment(self):
        record = {'term_id': 'test-grief', 'risk_term': False, 'status': 'unmatched', 'reason': 'No card supports the defined presentation'}
        report = summarize([record])
        self.assertEqual(report['unmatched'], 1)
        self.assertEqual(report['matched'], 0)
        record['card_id'] = 'p_wrong'
        with self.assertRaisesRegex(ValueError, 'cannot assign'): summarize([record])
    def test_reason_required(self):
        with self.assertRaisesRegex(ValueError, 'requires a reason'):
            summarize([{'term_id': 'test', 'risk_term': False, 'status': 'unmatched'}])
    def test_problem_label_is_insufficient(self):
        record = {'term_id': 'test-panic', 'risk_term': False, 'status': 'matched', 'field': 'presentations', 'type': 'recognise', 'definition_version': 1, 'card_id': 'p_test', 'builder_commit': 'pinned', 'fit_evidence': {'problem': 'anxiety'}}
        with self.assertRaisesRegex(ValueError, 'labels alone'): summarize([record])
    def test_pending_is_not_unmatched_or_complete(self):
        report = summarize([{'term_id': 'test', 'risk_term': False, 'status': 'pending'}])
        self.assertEqual(report['pending_fit'], 1)
        self.assertEqual(report['unmatched'], 0)
        self.assertFalse(report['fit_complete'])
    def test_risk_exclusions_separate_from_unmatched(self):
        report = summarize([{'term_id': 'test-risk', 'risk_term': True, 'status': 'excluded_risk', 'reason': 'No risk-card path'}])
        self.assertEqual(report['excluded_risk'], 1)
        self.assertEqual(report['unmatched'], 0)
    def test_repeated_term_not_double_counted(self):
        row = {'term_id': 'test', 'risk_term': False, 'status': 'pending'}
        with self.assertRaisesRegex(ValueError, 'Duplicate'): summarize([row, copy.deepcopy(row)])

if __name__ == '__main__': unittest.main()
