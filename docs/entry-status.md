# Entry status and headword eligibility

The build derives five entry statuses: candidate, reviewed, judged, dropped and redraft. A numbered release is a separate marker. The drafter never counts as a reader.

| Entry status | Meaning | Headword disposition |
|---|---|---|
| Candidate | Drafted from its source packet; no passing reader yet | Published with its candidate badge |
| Reviewed | One distinct non-drafter reader passed it; copy check clear | Published with its reviewed badge |
| Judged | Two distinct non-drafter readers passed it; copy check clear | Published with its judged badge |
| Dropped | Headword out of scope | Not redrafted; current exclusions await a scope read |
| Redraft | In-scope headword; definition failed its packet | Returns to the candidate pool marked “new packet required” |

Both failed statuses are excluded from term pages, search and definition downloads. The Dropped page and the dictionary’s `dropped` metadata array include both, with explicit status, reason, and source citations. Failed definition prose is not included in that array. `redraft_candidates` in the download and `data/redraft-candidates.json` expose the waiting headwords, failed entry IDs and excluded packet hashes, without the failed prose.

A failed entry cannot be restored or edited in place. A replacement uses a new entry ID and a `redraft_of` list bound into the semantic hash and source packet. Its source content must differ from every failed packet for that headword; a different ID or administrative packet metadata alone does not qualify. It carries fresh provenance and cannot inherit drafting or reader receipts. It starts with its own evidence-derived candidate/reviewed/judged state and needs its own two independent reads to become judged. Once a replacement is active, the headword leaves the waiting pool; the failed entry remains in the history.

`prepare_candidate_packets.py` admits waiting redraft headwords while continuing to exclude active and dropped headwords. It rejects the failed packet basis before drafting and writes replacement lineage into fresh packets. The existing publication safeguard prevents overwriting entry or packet files. This policy change dispatches no paid calls.

## Initial reclassification

The supplied scope label is “No psychology or counselling context established”. The existing build used “The pinned source packet does not establish a psychology, counselling, neural, educational, ethical or research-method context.” for the same scope exclusion. Those 24 records remain dropped, pending a scope read. Every other reason in the previous failed list becomes redraft: 2,600 entries and 2,600 waiting headwords. The 9,201 published judged entries are unchanged.

`data/status-migrations/redraft-split-v1.json` binds this one-time reclassification to exact before/after status snapshots and is SHA-256 pinned in `entry_status.py`. Later changes cannot use it to reset a failed entry. Source definitions, entry hashes, packets, receipts, supplied verdicts, risk flags and the approved see-also graph remain unchanged.

Regenerate and check the build-owned history and candidate pool with:

```sh
python scripts/entry_status.py --write-history
python scripts/entry_status.py --base origin/main
npm run build
```
