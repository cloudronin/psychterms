# Local redraft preregistration

Status: superseded for active execution by [API drafting with local fit and readers](hybrid-redraft-preregistration.md), following Vishnu’s instruction to use the API for drafting alone. The local-only run was interrupted after 39 headwords; its frozen registration and evidence are retained. The historical protocol below describes that run.

Vishnu authorized local execution in place of the hosted-model plan. This line spends **$0 on hosted models**. The earlier $200 ceiling remains unused; this implementation cannot dispatch hosted inference, read an API key or fall back to a paid model.

Freeze the 2,600 current redraft headwords in headword-key order, then shuffle with seed **20261018**. Split into five waves of 500 and a final wave of 100. The original failed entries retain their IDs, statuses, reasons and evidence. “Old entry stays dropped” means retained as a withheld failed entry, using its existing `redraft` status. A replacement has a new ID, version **2**, a new permitted packet, fresh provenance and its own two independent reads.

## Retrieval and ranking

Use the locally cached, pinned source inventory and its permitted original source texts. No legacy definition file or inherited headword list is read. The cohort comes from the existing build-owned redraft pool. Failed source packet bases are excluded, including changes to ID, whitespace, case or revision labels that do not change source content. Failed definition prose is used only by the hash-based copy comparison, never by retrieval, ranking, drafting, packet-fit or readers.

Retrieve up to five distinct source-record packets per headword using exact labels/aliases or whole-word source-text mentions. Packets contain at most 4,200 source characters around the term. A retrieved mention is not assumed to explain the term. The corpus includes MeSH, NCI Thesaurus, permitted historical texts, other admitted texts and article backgrounds with verified reuse rights. Wikipedia/SA, NC and ND sources remain excluded. Source inventory licence decisions, pinned versions and snapshot hashes are reused, not inferred from search results.

Rank those packets with the existing pinned **BAAI/bge-small-en-v1.5** weights against exactly `{headword}: psychology or counselling term, {field}`. Keep the top two, no padding or cosine floor. Record the embedding device and freeze the resulting cohort before language-model inference. The local ranking cache makes subsequent runs reusable; a fresh GPU encode is not claimed to be bitwise identical to a CPU encode.

## Installed models and isolation

| Role | Installed model | Weight digest prefix |
|---|---|---|
| Packet fit | Qwen 3.5 4B | `2a654d98e6fb` |
| Drafter | Qwen 2.5 7B | `845dbda0ea48` |
| Reader A | Qwen 3 4B | `359d7dd4bcda` |
| Reader B | Qwen 3.5 4B | `2a654d98e6fb` |

Full digests, the Ollama version, model licence notice hashes, prompts, output schemas, code hashes, cohort hash and copy-comparison hash are frozen in the registration. These are three distinct installed weight sets from the Qwen family, not a claim of independent model families. The fit gate and Reader B use fresh, stateless requests; the reader receives no fit verdict or other reader's result.

Only the literal loopback Ollama endpoint is reachable through the inference client. Proxies and redirects are disabled. Model digests are checked before and after inference. Temperature is zero, seed 20261018, context 8,192 tokens; thinking output is disabled for models that support that switch. Each fit response is yes/no with a one-line reason; a mention, association, study result or wrong sense is insufficient. Only yes packets can reach the drafter.

Each yes packet permits one draft and two independent, non-drafter reads. If the first packet fails, the second yes packet may be attempted as a separate new entry. There are no semantic rewrites against the same packet. One bounded transport/schema retry is allowed; infrastructure or changed-model failures pause the wave. Malformed model outputs and unsupported drafts are recorded, never treated as passes. Existing paragraph, sentence, no-advice and risk rules still apply. Vignettes remain deferred.

Every attempt records the actual local request and response, weight digest, registration hash, packet hash, elapsed time and zero paid cost. These are labelled **local Ollama inference**, not fabricated hosted API receipts. Accepted replacement evidence is independently revalidated against its actual response before reporting or publication.

Runtime semantics were checked against Ollama's own [structured-output documentation](https://docs.ollama.com/capabilities/structured-outputs) and [thinking-control documentation](https://docs.ollama.com/capabilities/thinking).

## Copy check, reporting and stop rule

Compare every draft with the frozen fifteen-word hash index of all existing pinned source packets, the selected replacement packets and the existing dictionary definitions. Check cross-entry runs against staged replacements too. A 15-word hit prevents acceptance.

**Primary wave pass rate = headwords with a replacement passing both readers and the copy check / all frozen headwords in that wave.** Missing packets, two no-fit decisions, insufficient drafts and reader failures stay in the denominator. Report retrieval coverage, fit outcomes, draft attempts and reader failures separately; do not inflate the primary rate by reporting only drafted entries.

Write and emit wave one's JSON and Markdown report before wave two. A complete wave below **60%** stops further waves. An incomplete wave cannot authorize continuation. Every subsequent wave has the same stop rule. No yes packet means headword outcome `redraft`, reason **“no supporting source found yet”**, limited to the registered local corpus. This is stored as a separate headword sourcing outcome; it never overwrites the old entry's original rejection reason.

Accepted entries are staged privately until their actual receipts, provenance and copy checks pass import validation. Publishing requires the normal corpus, risk, status, see-also and site checks; the old entries are never restored in place.

## Commands

```sh
.private/also-see-venv/bin/python scripts/prepare_local_redrafts.py
python3 scripts/local_redraft.py register
python3 scripts/local_redraft.py run --wave 1
python3 scripts/local_redraft.py report --wave 1
```

Preparation can resume the saved retrieval stage with `--rank-only`. Registered inputs cannot be regenerated in place. Running again reuses validated local receipts; another worker cannot run the same registration concurrently. `--limit` is a resumable execution limit, never a smaller denominator or permission to report an incomplete wave.

A completion helper can refresh the build-owned headword queue once the report has been emitted, without performing inference:

```sh
python3 scripts/finalize_local_redraft_wave.py --wave 1 --wait
```

Wave one's helper is running separately from the model worker. It writes `.private/local-redraft/run-state.json`, refreshes the new sourcing reasons without modifying original entry reasons, and stops there. It never starts wave two or publishes definitions automatically. The human-facing wave-one report comes first. The partial progress JSON uses `drafted` to mean headwords with a draft attempt, not necessarily valid or accepted prose.

After the report, the importer first performs a private dry run. It verifies actual local receipts, the fit yes, both reader passes, version, lineage, fresh provenance and the full current copy comparison before any public source entry is written:

```sh
python3 scripts/import_local_redrafts.py --wave 1
python3 scripts/import_local_redrafts.py --wave 1 --write
python3 scripts/entry_status.py --write-history
```

Rebuild the see-also graph and site after import, then run the normal corpus/status/risk/site checks. The original failed files remain unchanged. New version-2 entries receive their own pinned local-run metadata and actual inference receipts; the reader models appear on About through the normal build.
