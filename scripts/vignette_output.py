"""Generated scenes require their own immutable scanner run and two bound verdicts."""
import csv
import hashlib
import json
import re
import subprocess
import sys
from core import ROOT, digest
from overlap_scan import words


def reference_manifest(directory):
    paths = sorted(p for p in directory.rglob('*') if p.is_file() and p.suffix.lower() in {'.txt', '.md', '.html', '.htm'})
    if not paths: raise ValueError('Output comparison set is empty')
    if any(p.is_symlink() for p in paths): raise ValueError('Reference symlinks are forbidden')
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def validate_form(row):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', row['term_id']): raise ValueError('Invalid scene identifier')
    scene = row['scene']; notice = row['notice_line']
    if not isinstance(scene, str) or '\n' in scene or not 100 <= len(words(scene)) <= 150:
        raise ValueError('Scene must be one paragraph of 100 to 150 scanner-normalized words')
    if not isinstance(notice, str) or not notice.strip() or '\n' in notice:
        raise ValueError('One notice line required')


def scan_generated(rows, refs, expected_refs, out):
    if reference_manifest(refs) != expected_refs: raise ValueError('Frozen reference set changed')
    if not rows or len({r['term_id'] for r in rows}) != len(rows): raise ValueError('Unique nonempty scene input required')
    for row in rows: validate_form(row)
    out.mkdir(parents=True, exist_ok=True)
    md = out / 'vignettes.md'
    md.write_text(''.join(f"## {r['term_id']}\n\n{r['scene']}\n\n{r['notice_line']}\n\n" for r in rows))
    scanner = ROOT / 'scripts/overlap_scan.py'
    reports = {}
    for minimum in (15, 5):
        csv_path = out / f'hits-{minimum}.csv'
        result = subprocess.run([sys.executable, str(scanner), str(md), str(refs), '--min-words', str(minimum), '--out', str(csv_path)], capture_output=True, text=True)
        if result.returncode not in (0, 1): raise ValueError('Overlap scanner failed: ' + result.stderr)
        with csv_path.open() as f: hits = list(csv.DictReader(f))
        reports[minimum] = {'exit_code': result.returncode, 'hits': hits}
        (out / f'summary-{minimum}.txt').write_text(result.stderr)
    if reference_manifest(refs) != expected_refs: raise ValueError('Reference set changed during scan')
    report = {'input_hash': digest(rows), 'comparison_set_hash': digest(expected_refs), 'scanner_sha256': hashlib.sha256(scanner.read_bytes()).hexdigest(),
              'scan_15_passed': reports[15]['exit_code'] == 0, 'hits_15': reports[15]['hits'], 'triage_5': reports[5]['hits'],
              'entry_duplicates_reported_in_scanner_summary': True, 'producer_bank_result_used_as_output_check': False}
    (out / 'scan.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def output_hash(row): return digest({'term_id': row['term_id'], 'scene': row['scene'], 'notice_line': row['notice_line']})


def require_checks(row, fit, context_hash, scan, reviews, triage_complete):
    validate_form(row)
    if fit['status'] != 'matched' or fit['risk_term'] or fit['term_id'] != row['term_id']:
        raise ValueError('No scene without a non-risk card match')
    if scan.get('input_hash') != digest([row]) or scan.get('scan_15_passed') is not True:
        raise ValueError('Generated output has no passing current 15-word scan')
    if scan.get('triage_5') and triage_complete is not True:
        raise ValueError('Five-word output hits still need editorial triage')
    if len(reviews) != 2 or len({r.get('model') for r in reviews}) != 2:
        raise ValueError('Two distinct output judges required')
    for r in reviews:
        if r.get('passed') is not True or r.get('output_hash') != output_hash(row) or r.get('context_hash') != context_hash or not r.get('receipt_id') or not r.get('rubric_hash'):
            raise ValueError('Failed, stale or unreceipted scene verdict')
    return True
