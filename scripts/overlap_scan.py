#!/usr/bin/env python3
"""Overlap scan: find verbatim word runs shared between dictionary entries and reference texts.

Usage:
  python3 overlap_scan.py ENTRIES.md REF_DIR [--min-words 15] [--out hits.csv]

ENTRIES.md : the broad-layer dictionary. One entry per heading ("## term" or "**term**" or "term: definition").
REF_DIR    : a folder of .txt / .md / .html files holding the reference texts to compare against
             (public dictionary pages you have saved for this check, prep-site pages, anything else).
             Every file in the folder is scanned; subfolders too.

Output: a CSV of every entry that shares a run of MIN_WORDS or more consecutive words with any reference
file, with the matching file, the run, and the run length. Exit code 1 if any hit, 0 if clean.

Also reports, on stderr: entries parsed, reference words indexed, entries with hits, longest run,
and entry-to-entry duplicates inside ENTRIES.md itself (same window shared by two entries).

Stdlib only. Matching is on lower-cased words with punctuation stripped, so "self-efficacy" and
"self efficacy" match. Numbers and single letters count as words.
"""
import argparse, csv, html, os, re, sys
from collections import defaultdict

WORD = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

def words(text):
    return WORD.findall(text.lower())

def strip_html(text):
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)

def parse_entries(path):
    """Yield (term, definition). Accepts '## term', '**term**', '- **term**: def', or 'term: def'."""
    entries = []
    term, buf = None, []
    def flush():
        if term is not None and buf:
            entries.append((term.strip(), " ".join(buf).strip()))
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            m = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
            if m:
                flush(); term, buf = m.group(1), []; continue
            m = re.match(r"^\s*(?:[-*]\s*)?\*\*(.+?)\*\*\s*[:\-–—]?\s*(.*)$", line)
            if m:
                flush(); term, buf = m.group(1), [m.group(2)] if m.group(2) else []; continue
            m = re.match(r"^([A-Za-z][^:]{0,80}):\s+(.+)$", line)
            if m and term is None or (m and not buf):
                flush(); term, buf = m.group(1), [m.group(2)]; continue
            if line.strip():
                buf.append(line.strip())
    flush()
    return entries

def index_refs(ref_dir, n):
    """Map each n-word window hash -> list of (file, start_word_index). Also keep file word lists."""
    index = defaultdict(list)
    files = {}
    total = 0
    for root, _, names in os.walk(ref_dir):
        for name in sorted(names):
            if not name.lower().endswith((".txt", ".md", ".html", ".htm")):
                continue
            p = os.path.join(root, name)
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
            if name.lower().endswith((".html", ".htm")):
                text = strip_html(text)
            w = words(text)
            files[p] = w
            total += len(w)
            for i in range(len(w) - n + 1):
                index[hash(tuple(w[i:i + n]))].append((p, i))
    return index, files, total

def longest_run(entry_words, start, ref_words, ref_start, n):
    """Extend a matched n-window forward as far as the words keep matching."""
    k = n
    while (start + k < len(entry_words) and ref_start + k < len(ref_words)
           and entry_words[start + k] == ref_words[ref_start + k]):
        k += 1
    return k

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entries")
    ap.add_argument("ref_dir")
    ap.add_argument("--min-words", type=int, default=15)
    ap.add_argument("--out", default="overlap_hits.csv")
    a = ap.parse_args()
    n = a.min_words

    entries = parse_entries(a.entries)
    if not entries:
        sys.exit("no entries parsed; check the heading format")
    index, files, ref_total = index_refs(a.ref_dir, n)

    hits = []
    seen_windows = defaultdict(list)  # for entry-to-entry duplicates
    for term, definition in entries:
        ew = words(definition)
        i = 0
        best_for_entry = None
        while i <= len(ew) - n:
            h = hash(tuple(ew[i:i + n]))
            seen_windows[h].append(term)
            cands = index.get(h)
            if cands:
                for (p, ri) in cands:
                    rw = files[p]
                    if rw[ri:ri + n] != ew[i:i + n]:
                        continue  # hash collision
                    k = longest_run(ew, i, rw, ri, n)
                    run = " ".join(ew[i:i + k])
                    if best_for_entry is None or k > best_for_entry[2]:
                        best_for_entry = (term, os.path.relpath(p, a.ref_dir), k, run)
                i += (best_for_entry[2] if best_for_entry else 1)
            else:
                i += 1
        if best_for_entry:
            hits.append(best_for_entry)

    dupes = {h: sorted(set(t)) for h, t in seen_windows.items() if len(set(t)) > 1}

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["term", "reference_file", "run_words", "run"])
        for row in sorted(hits, key=lambda r: -r[2]):
            wr.writerow(row)

    longest = max((h[2] for h in hits), default=0)
    print(f"entries parsed:            {len(entries)}", file=sys.stderr)
    print(f"reference words indexed:   {ref_total} across {len(files)} files", file=sys.stderr)
    print(f"entries with a run >= {n}: {len(hits)}", file=sys.stderr)
    print(f"longest run:               {longest} words", file=sys.stderr)
    print(f"entry-to-entry duplicate windows inside the file: {len(dupes)}", file=sys.stderr)
    if dupes:
        sample = list(dupes.values())[:5]
        for s in sample:
            print(f"  shared by: {', '.join(s[:4])}", file=sys.stderr)
    print(f"hits written to {a.out}", file=sys.stderr)
    sys.exit(1 if hits else 0)

if __name__ == "__main__":
    main()
