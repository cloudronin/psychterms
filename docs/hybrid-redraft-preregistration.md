# Hybrid redraft preregistration

Vishnu instructed “then use the API for drafting alone” after the estimate of $10–20 for 2,600 drafts. This supersedes the local-only drafting role, within the previously approved **$200 total redraft cap**. Expected drafting spend is $2–4 for the first 500 headwords and $10–20 for all 2,600 if each needs one drafting call; those are estimates, not acceptance promises. Two yes packets can each receive a draft if the first fails.

| Role | Provider and model | Paid |
|---|---|---|
| Packet fit | Local Ollama Qwen 3.5 4B, pinned weights | No |
| Draft | OpenAI `gpt-5.4-2026-03-05` | Yes |
| Reader A | Local Ollama Qwen 3 4B, pinned weights | No |
| Reader B | Local Ollama Qwen 3.5 4B, pinned weights | No |

Only drafting may reach the hosted endpoint. Fit and both readers remain local, with distinct non-drafter weights and separate stateless requests. No other reader verdict is shown. Vignettes remain deferred. The key is read only by the hosted drafting function and is never written into requests on disk, logs or reports.

## Frozen inputs and continuation

Reuse the exact 2,600-headword cohort, source packets, fields, ranking and seed **20261018** from the local registration. Restart wave one with the hybrid roles; do not pool its results with the interrupted local-only pilot. The local-only run stopped after 39 complete headwords, with $0 spend; its registration, receipts and outcomes remain private and intact. Its unfinished wave cannot authorize wave two.

The source inventory, up-to-five retrieval and top-two BGE ranking, failed-packet exclusions, no legacy prose as model input, source-only fit gate, 15-word output scan, version-2 lineage and immutable old entries remain as in [the local protocol](local-redraft-preregistration.md). No changes to the frozen source packets or fit/read prompts are made in response to preliminary outcomes.

All 500 wave-one headwords remain in the pass-rate denominator. The numerator requires both independent reader passes and a clear copy scan. A complete report is emitted before wave two; below 60% stops the run. No yes packet leaves the headword in `redraft`, with “no supporting source found yet”. The existing entry’s rejection reason is preserved.

## Paid drafting and receipts

The only hosted endpoint is `https://api.openai.com/v1/chat/completions`, pinned to the snapshot above. Structured JSON, low reasoning, maximum **1,000 completion tokens**, `store: false`, at most **24,000 request bytes**. The same source-only drafting prompt is used. No failed definition, local draft or reader feedback is sent to the drafter.

Prices verified against [OpenAI’s GPT-5.4 model page](https://developers.openai.com/api/docs/models/gpt-5.4): $2.50 per million input tokens, $0.25 cached input, $15 output. A persistent SQLite budget reserves each call before dispatch, with a conservative request-byte bound for input and the full output-token allowance. Actual provider usage reconciles reservations; uncertain charges remain reserved and pause dispatch, including after restart. No automatic billable retries. The cap is shared across this registration’s waves and attempts, not reset per wave.

Local requests record actual Ollama responses and zero cost. Hosted requests record actual provider response IDs, usage, request and response bodies, role, source-packet binding and cost. The build validates each kind as its real origin; API drafts are never represented as local weight inference. Per-call costs and total ledger spend appear in the wave report. Only accepted entries and their relevant evidence are eligible for import after validation.

## Execution

```sh
.venv/bin/python scripts/hybrid_redraft.py register
.venv/bin/python scripts/hybrid_redraft.py run --wave 1
.venv/bin/python scripts/hybrid_redraft.py report --wave 1
.venv/bin/python scripts/import_local_redrafts.py --hybrid --wave 1
```

The importer defaults to a dry run. `--write` requires an emitted complete report and rechecks actual receipts, provenance, lineage, readers and copy scan. Build-owned status, graph, risk and site checks follow import. No wave two is started automatically.
