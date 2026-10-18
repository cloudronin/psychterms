"""Audit a private legacy parser fixture. Never emit its text or headwords."""
import argparse
from collections import Counter
from pathlib import Path
import json
import re

ENTRY = re.compile(r'^#### ([^\n]+)\n<a id="(e\d+)"></a>\n\n(.*?)(?=\n#### |\n### |\n## |\Z)', re.M | re.S)

def audit(text):
    blocks = list(ENTRY.finditer(text))
    ids = [m[2] for m in blocks]
    bio_start = text.find('\n## Biographies\n')
    sections = Counter('biographies' if bio_start >= 0 and m.start() > bio_start else 'dictionary' for m in blocks)
    return {'parsed_entries': len(blocks), 'unique_ids': len(set(ids)), 'duplicate_ids': len(ids)-len(set(ids)), 'sections': dict(sections), 'fixture_only': True, 'content_exported': False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-fixture', type=Path, required=True)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    if a.private_fixture.resolve().is_relative_to(root):
        p.error('Legacy fixtures must stay outside the public project')
    print(json.dumps(audit(a.private_fixture.read_text()), indent=2))

if __name__=='__main__': main()
