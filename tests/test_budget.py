import concurrent.futures,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from budget import Budget
class BudgetTests(unittest.TestCase):
 def test_outstanding_reservations_count_against_cap(self):
  with tempfile.TemporaryDirectory() as d:
   b=Budget(Path(d)/'budget.sqlite',100);b.reserve('a','draft',70)
   with self.assertRaisesRegex(RuntimeError,'cap'):b.reserve('b','judge',40)
   self.assertEqual(b.summary()['unresolved_reservations_usd'],.00007)
 def test_reconcile_releases_unused_reserve(self):
  with tempfile.TemporaryDirectory() as d:
   b=Budget(Path(d)/'budget.sqlite',100);b.reserve('a','draft',70);b.reconcile('a',20);b.reserve('b','judge',80)
   self.assertEqual(b.summary()['receipted_usd'],.00002)
 def test_concurrent_reservations_cannot_overspend(self):
  with tempfile.TemporaryDirectory() as d:
   b=Budget(Path(d)/'budget.sqlite',100)
   def reserve(n):
    try:b.reserve(str(n),'judge',30);return True
    except RuntimeError:return False
   with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:ok=list(pool.map(reserve,range(20)))
   self.assertEqual(sum(ok),3);self.assertEqual(b.summary()['calls_reserved'],3)
 def test_unexpected_charge_is_recorded_before_stop(self):
  with tempfile.TemporaryDirectory() as d:
   b=Budget(Path(d)/'budget.sqlite',100);b.reserve('a','judge',30)
   with self.assertRaisesRegex(RuntimeError,'exceeded reservation'):b.reconcile('a',40)
   self.assertEqual(b.summary()['receipted_usd'],.00004)
if __name__=='__main__':unittest.main()
