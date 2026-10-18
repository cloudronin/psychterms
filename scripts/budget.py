"""Atomic micro-dollar reservations; uncertain billable attempts retain their reserve."""
import sqlite3,time
class Budget:
 def __init__(self,path,cap_microusd):
  self.path=str(path);self.cap=cap_microusd
  with sqlite3.connect(self.path) as c:
   c.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, category TEXT, reserved INTEGER, charged INTEGER, state TEXT)')
 def reserve(self,ident,category,amount):
  if type(amount) is not int or amount<=0:raise ValueError('Positive integer reservation required')
  with sqlite3.connect(self.path,timeout=30) as c:
   c.execute('BEGIN IMMEDIATE')
   used=c.execute("SELECT COALESCE(SUM(CASE WHEN charged IS NULL THEN reserved ELSE charged END),0) FROM calls").fetchone()[0]
   if used+amount>self.cap:raise RuntimeError('Budget cap prevents dispatch')
   c.execute('INSERT INTO calls VALUES (?,?,?,NULL,?)',(ident,category,amount,'reserved'))
 def reconcile(self,ident,actual):
  if type(actual) is not int or actual<0:raise ValueError('Nonnegative integer charge required')
  with sqlite3.connect(self.path) as c:
   c.execute('BEGIN IMMEDIATE');row=c.execute('SELECT reserved,state FROM calls WHERE id=?',(ident,)).fetchone()
   if not row or row[1]!='reserved':raise ValueError('Not an outstanding reservation')
   c.execute('UPDATE calls SET charged=?,state=? WHERE id=?',(actual,'receipted',ident))
  if actual>row[0]:raise RuntimeError('Provider charge exceeded reservation; stop line for reconciliation')
 def summary(self):
  with sqlite3.connect(self.path) as c:
   rows=c.execute('SELECT category,reserved,charged,state FROM calls').fetchall()
  return {'calls_reserved':len(rows),'cap_usd':self.cap/1e6,'receipted_usd':sum(r[2] or 0 for r in rows)/1e6,'unresolved_reservations_usd':sum(r[1] for r in rows if r[2] is None)/1e6,'by_category':{k:{'calls':sum(r[0]==k for r in rows),'receipted_usd':sum((r[2] or 0) for r in rows if r[0]==k)/1e6,'unresolved_reservations_usd':sum(r[1] for r in rows if r[0]==k and r[2] is None)/1e6} for k in sorted({r[0] for r in rows})}}
