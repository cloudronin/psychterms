# Wave-two editorial review and field-tagging correction

19 October 2026, frozen before paid calls. Vishnu supplied 74 PASS, seven FAIL and 36 field retags. Five failures are scope exclusions, not redraft work: dry eyes, graph theory, Henle fiber, shape and superposition. Two failures, preparatory response and redundancy, are retried against unchanged source text. The 36 supplied retags are authoritative in the staged decision overlay; frozen definitions and their original receipts are not edited.

`data/headword-exclusions.json` persists the five current exclusions and the two previously instructed pilot exclusions (including the SQUID alias). The generated candidate pool respects that registry, so regeneration cannot reinsert them. Existing failed entry versions and forward-only entry history remain unchanged. Scope exclusion of a headword is separate from its old entry's terminal status.

## Field classification

`data/field-definitions.json` defines each of the existing 14 fields in one line. A separate cheap field call receives the headword, complete source packet, actual label and publisher aliases; it sees no inherited field, draft prose or Claude answer. The task is the headword's meaning, not the paper's research venue or subject. Classification never grants dictionary scope.

A confident classification chooses one field. An uncertain biological fallback requires an actual laboratory-paper context and a relevant biological meaning; an uncertain research-methods fallback requires a methods-paper context and methodological meaning. Both need a literal supporting context quote. Other uncertainty returns null and holds the packet for field review instead of defaulting to one of those buckets. Uncertain routed classifications remain flagged. Both fit and reader prompts now explicitly reject unrelated ocular/anatomical, pure mathematics and physical-property meanings despite psychological article context.

Before wave three, the pipeline performs tagging before fit/drafting, updates only a copied packet's field metadata and packet hash, and gives fit/draft/read roles the same corrected field and packet binding. Field-tagging evidence retains the original packet, receipt and source content for audit. An abstention holds drafting, rather than being reported as no supporting source. These paths have offline regression tests. The old frozen wave-two registration is not rewritten.

## This execution

- Validate exactly the 81 exported proposal IDs and headword keys, all 14 field names, the 74/7 split and 36 retags before applying decisions.
- Compare the new tagger against Claude's resolved fields on the 74 passed entries. These are inspected development examples, not a held-out estimate. Keep disagreements, abstentions and unverifiable responses visible. Do not overwrite Claude's retags with the model output.
- Retry the two narrowing failures only, without showing old definitions or verdicts to the drafter. Keep source text identical. Any resulting proposal is a new version 3 with fresh fit, drafting and two-reader evidence and a 15-word copy scan. If the packet cannot establish the general meaning, retain redraft status rather than inventing it.
- Reuse existing pinned GPT-5.4 mini for field classification, GPT-5.2 for fit, GPT-5.4 for drafting, and GPT-5.4 mini/GPT-5.2 readers. Existing prices and bounded retries apply. Reserve every call against the same original $200 redraft ledger, including all previous charges and uncertain calls. No new allowance.
- Freeze prompts, schema, field-guide and exclusion-registry hashes in `data/wave-two-corrections-registration.json` before dispatch. Retain real provider receipts and separately report actual-token usage at the registered rates.
- No definition publication and no wave-three calls in this execution. Update the existing draft PR with the decisions, pipeline changes and measured field comparison.

## Executed development results

The first execution is preserved as v1, including exact executed code and receipts. Its evidence validator mistakenly required literal quote formatting on confident tags and abstentions, invalidating 73/74 responses; it does not establish taxonomy accuracy. The amended v2 registration was frozen before its own calls and preserves all prior costs and reservations.

In v2, 48 classifications were confident, 37 matched Claude and 11 disagreed; 22 abstained and four responses were unverifiable. All 36 authoritative retags remain in the decision overlay. One of the two same-packet drafts passed both fresh readers and the copy scan; the other remains unverified because the first reader returned no supporting evidence. It is not a confirmed reader FAIL. Both drafts were exported for Claude. Both executions together used $0.381159 in receipted usage; shared total $16.031413, with $0.820085 reserved, under the same $200 cap. Wave three has not started.

The updated batch CLI takes `--wave`, with the next batch defaulting to 3; updating this interface does not execute that batch. Historical wave-two code is pinned by its executed commit and original registration. Field tagging before future fit/drafting is opt-in through the new frozen registration, with original source text and tagging evidence audited separately.
