import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from scan_pilot_definitions import scanner_markdown
from overlap_scan import parse_entries, words

class ScannerExportTests(unittest.TestCase):
    def test_colon_in_initial_definition_does_not_replace_term_or_omit_words(self):
        rows = [{'id': 'DTEST', 'term': 'Example', 'definition': 'A supported concept: one that is explained in an independent way.'}]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'entries.md'; path.write_text(scanner_markdown(rows)); entries = parse_entries(path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][0], 'DTEST Example')
        self.assertEqual(words(entries[0][1]), words(rows[0]['definition']))

if __name__ == '__main__': unittest.main()
