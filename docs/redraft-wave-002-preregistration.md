# Redraft wave two, after editorial judging

Vishnu explicitly instructed: “proceed with the next batch after incorporating findings/learnings from this round of judging first”. This authorizes the next 500 frozen headwords despite the earlier pilot yield. It does not authorize automatic later batches or publication. Registration is frozen before paid dispatch.

The batch is wave two in the original seeded 2,600-headword cohort, disjoint from the 500-headword pilot. No count padding or new headwords. Original failed entries, statuses and provenance remain unchanged. The original seed is retained. The 44 Claude passes, four subsequent model-reviewed corrections and all existing retags remain separate from this batch.

## Incorporated findings

Source support does not establish that prose defines the general headword. A source can support a study-specific usage, finding or application of a theory without supporting a general definition. Removing “in this article” does not fix the conceptual narrowing. The fit and both reader prompts carry the named **Term meaning, not study usage** check. Drafting bans source-relative framing and findings, prefers one concise definitional sentence, and omits research implications or motivation. Insufficient evidence must remain insufficient. Actual source labels and publisher aliases reach all roles. Field labels are metadata, never a licence to add scientific claims; field-review flags remain explicit.

Before batch drafting, the two reader models each receive three valid and three deliberately narrowed/finding developer controls. All negative examples must fail, and each reader must accept at least two positive examples. This checks the known failure mechanism while retaining positive examples; it is not held-out accuracy evidence. A failed control check stops dispatch for correction, without silently proceeding.

## Retrieval and execution

- Use only already permitted cached records: existing up-to-five retrieval candidates plus the previously prepared MedlinePlus/CDC options. Deduplicate identical text before candidate slots. Prefer exact source labels, then direct government records over incidental article mentions; retain at most five stored candidates. Locally rank with the pinned bge-small model against “{headword}: psychology or counselling term, {field}”; retain the top two. HPO remains aliases/links only. No other OpenMD sources are added.
- Exclude known rejected standalone headwords, including SQUID and blank screen. Up to two packets per term get a fit read; only yes packets go to drafting. One draft per admitted packet, with bounded transport/schema retries and no iterative content repair. No prior definitions or verdicts are shown to the drafter; readers see only the fresh draft and its packet.
- Existing pinned models: GPT-5.2 fit, GPT-5.4 draft, GPT-5.4 mini and GPT-5.2 readers. Distinct drafter and reader identities. Twelve concurrent headwords, all under the same original $200 redraft ledger, including prior charges and uncertain reservations. No budget reset. Full manifests, model request hashes and receipts remain private.
- Require both readers and a 15-word source/cross-entry scan. Freeze comparison texts before drafting, then perform a deterministic final scan against accepted batch proposals. Retain old failed versions and create separate version-2 entries with new provenance and receipts. Check old-entry hashes again at completion.
- Report all 500 headwords, missing packets, fit failures, draft/reader failures, unresolved responses, model passes and field flags. Export model-reviewed proposals with complete source packets for Claude, keeping prior judged batches separate. These are proposals, not newly Claude-approved entries.
- Publish no definitions and start no third batch automatically. Final reports and code go into the existing draft PR.

Commands: `scripts/run_redraft_batch.py prepare`, `verify`, then `run`. Frozen registration: `data/redraft-wave-002-registration.json`. The preparer uses the existing local embedding environment and does not make paid calls.

## Executed result

Executed code: `ee01acad`. All 500 headwords completed. Of 469 with ranked packets, 81 passed both fresh non-drafter readers and the final source/cross-entry copy audit; 22 carry field-review flags. Both readers matched all 12 seeded control labels. There were 31 missing-packet cases, 342 without a supporting yes packet, 22 draft/read/copy failures and 24 unverifiable model-output cases. These are development outcomes, not an independent accuracy estimate.

Receipted batch usage including preflight and retries: $5.078386. Total shared redraft usage: $15.650254; outstanding uncertain reservations: $0.789697, all under the same $200 cap. All 500 original failed-entry hashes remained unchanged. No publication or third batch. The 81 proposals were exported with complete source packets for Claude review. Full outcomes: `reports/redraft-wave-002-outcomes.csv`; summary: `reports/redraft-wave-002.md`.
