"""Validate public records against Draft 2020-12 schemas (development dependency)."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from core import ROOT
if __name__=='__main__':
 report={}
 for kind,records in [('entry',[json.loads(p.read_text()) for p in (ROOT/'data/entries').glob('*.json')]),('source',json.loads((ROOT/'data/sources.json').read_text())['sources'])]:
  schema=json.loads((ROOT/f'schema/{kind}.schema.json').read_text());Draft202012Validator.check_schema(schema)
  validator=Draft202012Validator(schema)
  for record in records:validator.validate(record)
  report[kind]=len(records)
 print(json.dumps({'schema_records_validated':report},indent=2))
