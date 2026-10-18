import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from core import digest
from vignette_output import reference_manifest, scan_generated, require_checks, output_hash

class VignetteOutputTests(unittest.TestCase):
    def setUp(self):
        self.row = {'term_id': 'DTEST', 'scene': ' '.join('token'+str(i) for i in range(110)), 'notice_line': 'Notice the defined concept.'}
        self.fit = {'term_id': 'DTEST', 'status': 'matched', 'risk_term': False}
    def scan(self, reference):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); refs = root/'refs'; refs.mkdir(); (refs/'permitted.txt').write_text(reference)
            return scan_generated([self.row], refs, reference_manifest(refs), root/'scan')
    def reviews(self):
        return [{'model': m, 'passed': True, 'output_hash': output_hash(self.row), 'context_hash': 'context', 'receipt_id': m, 'rubric_hash': 'rubric'} for m in ('judge-a', 'judge-b')]
    def test_actual_output_scan_flags_15_word_source_run(self):
        result = self.scan(' '.join('token'+str(i) for i in range(15)))
        self.assertFalse(result['scan_15_passed']); self.assertEqual(len(result['hits_15']), 1)
    def test_notice_line_is_also_scanned(self):
        self.row['notice_line'] = ' '.join('copied'+str(i) for i in range(16))
        self.assertFalse(self.scan(self.row['notice_line'])['scan_15_passed'])
    def test_5_word_hit_requires_triage_not_automatic_failure(self):
        result = self.scan(' '.join('token'+str(i) for i in range(5)))
        self.assertTrue(result['scan_15_passed'])
        with self.assertRaisesRegex(ValueError, 'triage'): require_checks(self.row, self.fit, 'context', result, self.reviews(), False)
        self.assertTrue(require_checks(self.row, self.fit, 'context', result, self.reviews(), True))
    def test_bank_check_cannot_replace_output_scan(self):
        with self.assertRaisesRegex(ValueError, '15-word scan'):
            require_checks(self.row, self.fit, 'context', {'bank_6_clean': True}, self.reviews(), True)
    def test_redraft_invalidates_scan_and_judges(self):
        result = self.scan('unrelated reference words'); old_reviews = self.reviews(); self.row['scene'] += ' revised'
        with self.assertRaisesRegex(ValueError, '15-word scan'): require_checks(self.row, self.fit, 'context', result, old_reviews, True)
        result['input_hash'] = digest([self.row])
        with self.assertRaisesRegex(ValueError, 'stale'): require_checks(self.row, self.fit, 'context', result, old_reviews, True)
    def test_one_failed_judge_blocks_output(self):
        result = self.scan('unrelated reference words'); reviews = self.reviews(); reviews[1]['passed'] = False
        with self.assertRaisesRegex(ValueError, 'Failed'): require_checks(self.row, self.fit, 'context', result, reviews, True)
    def test_risk_exclusion_blocks_scene(self):
        self.fit.update(status='excluded_risk', risk_term=True)
        with self.assertRaisesRegex(ValueError, 'non-risk'): require_checks(self.row, self.fit, 'context', self.scan('unrelated reference'), self.reviews(), True)
    def test_changed_reference_set_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); refs=root/'refs'; refs.mkdir(); (refs/'a.txt').write_text('reference'); manifest=reference_manifest(refs)
            (refs/'added.txt').write_text('unregistered text')
            with self.assertRaisesRegex(ValueError, 'reference set changed'): scan_generated([self.row], refs, manifest, root/'scan')

if __name__ == '__main__': unittest.main()
