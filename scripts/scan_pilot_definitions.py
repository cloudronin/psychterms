"""Audit final definition overlaps using the unchanged scanner and explicit five-word triage."""
import csv
import json
import subprocess
import sys
from core import ROOT, digest
from overlap_scan import parse_entries, words

REDRAFT = {
 'D020774': 'Anatomical names are fixed, but this 12-word run also copies the transition into the next explanatory clause; restructure that prose.',
 'D002653': 'The complete exclusion clause follows the source sentence; preserve named diagnoses but rewrite the surrounding explanation.',
 'D000067551': 'A ten-word ordered list and linking prose reproduce the source formulation rather than an unavoidable technical name.',
 'D000095422': 'The ten-word defining clause follows the source wording; it can be expressed independently without changing the concept.',
 'D000097163': 'The source-specific organisation/peers/other-settings phrasing can be replaced by an independent explanation.',
 'D007174': 'The nine-word impulse/drive/temptation construction retains source sentence structure; rewrite the definition rather than swapping isolated words.',
 'D003657': 'The eight-word defining process clause retains source prose; use a more direct independent explanation.',
 'D007859': 'The eight-word intellect/ability comparison preserves the source phrasing; restructure the relationship while retaining its meaning.',
 'D010467': 'The eight-word explanatory clause is ordinary rewritable prose, not a fixed diagnostic or instrument name.',
 'D035501': 'The eight-word risks/benefits/future clause follows source organisation and can be rewritten independently.',
 'D004291': 'The seven-word behavioural contrast reproduces the source sequence; explain the interaction in different prose.',
 'D000069551': 'The unusual climate-healthy/nature-supporting formulation is source-specific language, not an indispensable technical name.'
}


def scanner_markdown(rows):
    return ''.join(f"## {r['id']} {r['term']}\n\n> {r['definition']}\n\n" for r in rows)


def scan():
    dest = ROOT / '.private/pilot-combined'; refs = dest / 'definition-refs'; refs.mkdir(exist_ok=True)
    packets = json.loads((ROOT / '.private/pilot/packets.json').read_text())
    rows = json.loads((ROOT / '.private/pilot/recovered-results.json').read_text()); lookup = {r['id']: r for r in rows}
    for packet in packets: (refs / (packet['id'] + '.txt')).write_text(packet['text'] + '\n')
    path = dest / 'final-definitions.md'
    # A blockquote prefix stops the supplied scanner mistaking an initial colon for a new term.
    # It adds no normalized words and does not modify the scanner or the definition text.
    path.write_text(scanner_markdown(rows))
    parsed = parse_entries(path)
    if len(parsed) != len(rows) or any(term != f"{r['id']} {r['term']}" or words(body) != words(r['definition']) for (term, body), r in zip(parsed, rows)):
        raise ValueError('Scanner input does not preserve every term and definition word')
    results = {}
    for minimum in (15, 5):
        out = dest / f'definition-hits-{minimum}.csv'
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/overlap_scan.py'), str(path), str(refs), '--min-words', str(minimum), '--out', str(out)], capture_output=True, text=True)
        if result.returncode not in (0, 1): raise ValueError('Definition scanner failed')
        (dest / f'definition-scan-{minimum}.txt').write_text(result.stderr)
        with out.open() as f: results[minimum] = list(csv.DictReader(f))
    triage = []
    for hit in results[5]:
        ident = hit['term'].split(' ', 1)[0]; row = lookup[ident]
        if row['status'] == 'final_drop':
            action = 'already_dropped'; reason = 'Already rejected by semantic or 15-word checks; no extra rewrite is authorized.'
        elif ident in REDRAFT:
            action = 'hold_for_wording_revision'; reason = REDRAFT[ident]
        else:
            action = 'keep_short_technical_or_common_fragment'; reason = 'The shared run is a short stock expression, connective or necessary technical/clinical name/list. Do not force a rewrite solely to evade a five-word match.'
        triage.append(dict(hit, term_id=ident, action=action, reason=reason, reviewer='dictionary_session_editorial_copy_triage', paid_redraft_performed=False))
    counts = {action: sum(r['action'] == action for r in triage) for action in ('hold_for_wording_revision', 'keep_short_technical_or_common_fragment', 'already_dropped')}
    if set(REDRAFT) != {r['term_id'] for r in triage if r['action'] == 'hold_for_wording_revision'}: raise ValueError('Triage review does not match measured hits')
    report = {'definition_count': len(rows), 'min_15_hit_entries': len(results[15]), 'min_15_hit_ids': [r['term'].split(' ',1)[0] for r in results[15]],
              'min_5_hit_entries': len(results[5]), 'triage_counts': counts, 'triage_complete': True,
              'wording_holds_are_not_automatic_five_word_failures': True, 'no_further_paid_redrafts_after_stop': True,
              'machine_passed_with_wording_holds': counts['hold_for_wording_revision'], 'released_entries': 0,
              'input_word_stream_verified_against_all_definitions': True, 'legacy_reference_used': False}
    (ROOT / 'reports/definition-overlap-triage.json').write_text(json.dumps({'summary': report, 'triage': triage}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__': scan()
