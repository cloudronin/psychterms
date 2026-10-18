"""A stopped or unregistered paid line must fail before any credential access."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_pilot import require_paid_dispatch, run

class DispatchGuardTests(unittest.TestCase):
 def test_policy_defaults_closed_and_stop_overrides_enabled(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'data').mkdir();(root/'.private/pilot').mkdir(parents=True)
   policy=root/'data/release-policy.json'
   policy.write_text('{}')
   with self.assertRaisesRegex(RuntimeError,'Paid dispatch blocked'):require_paid_dispatch(root)
   policy.write_text(json.dumps({'paid_dispatch_enabled':True}))
   require_paid_dispatch(root)
   (root/'.private/pilot/STOP').touch()
   with self.assertRaisesRegex(RuntimeError,'Paid dispatch blocked'):require_paid_dispatch(root)
 def test_execute_blocked_before_key_or_manifest_read(self):
  with patch('run_pilot.require_paid_dispatch',side_effect=RuntimeError('held')):
   with patch.object(Path,'read_text',side_effect=AssertionError('unexpected file read')):
    with self.assertRaisesRegex(RuntimeError,'held'):run(True,Path('/nonexistent/key'))

if __name__=='__main__':unittest.main()
