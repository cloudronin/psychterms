# Independent reader line: approved and frozen

This line is separate from the approved $100 drafting-only line. Its approved hard cap is **$25**, including both reader models, transport/schema retries and uncertain calls. Vishnu approved this separate cap on 18 October 2026 with “Approve $25 reader cap”. Dispatch is enabled for this frozen line. The old $150 figure was withdrawn in spec v0.2 section 5. The approval covers the fixed reader jobs and retries described below.

Two fixed models independently read each definition against exactly its pinned source packet: `gpt-5.4-mini-2026-03-17` and `gpt-5.4-nano-2026-03-17`. Neither receives the other reader's result. Neither can read its own draft. The existing 198 mini reader passes remain bound to their exact definitions and packets and are not bought again; those entries need only the other reader. A model's refusal or malformed/unfinished response is not a semantic verdict and never counts as a pass.

Each reader checks source support, the requested sense and field, original clear wording, and the one-to-three-sentence definition contract. Unsupported facts, wrong acronym senses, invented entities, identifiable cases, treatment advice, dosing, procedures or diagnostic criteria lists fail. Historical text must not be represented as current clinical consensus. Failures require concrete reasons. No rewriting, source searching, scenes, or paid tools use this line.

The build derives reviewed from one passing non-drafter reader and clear copy checks, judged from two, or dropped with reasons after two rejections. A disagreement remains reviewed if one reader passed. Published status cannot move backward. Numbered-release inclusion is a separate marker. The existing 15-word source and cross-entry copy checks remain mandatory.

Standard text prices verified from the [OpenAI mini model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini) and [nano model page](https://developers.openai.com/api/docs/models/gpt-5.4-nano), 18 October 2026:

| Snapshot | Input / 1M | Cached input / 1M | Output / 1M |
|---|---:|---:|---:|
| GPT-5.4 mini, 2026-03-17 | $0.75 | $0.075 | $4.50 |
| GPT-5.4 nano, 2026-03-17 | $0.20 | $0.02 | $1.25 |

Both fixed IDs were present in this account's read-only model inventory on 18 October. Nano is marked deprecated in the documentation but currently available; an unavailable model stops execution rather than causing a silent substitution. These checks establish availability and prices, not reader accuracy. The first 400 calls yielded 326 passes and 74 rejections, with 34 disagreements among 197 pairs whose two new calls were in that batch. Reconciled cost was $0.329903; $0.012579 remained reserved for uncertain attempts. No item lacked a valid verdict after the allowed retries. Final whole-corpus outcomes and receipt-derived costs are recorded in `reports/independent-readers.json`; disagreement and explicit provider refusal counts are separate from pass counts.

The prepared job set, model IDs, prompts, structured schema, executor and dependencies are hashed before execution. Registration amendments retain prior receipts and the same reader ledger. Each request reserves its serialized UTF-8 byte count plus 512 input tokens at uncached prices and its full 1,000-token completion allowance. One transport/schema retry is allowed across resumes and reserved separately. Unknown charges retain their whole reservation. Successful receipts reconcile actual input, cached input and output usage. The reader ledger is separate from drafting and pilot ledgers and must never be reset to get around a cap.

The private frozen registration is `.private/reader-reviews/preregistration.json`, with a pinned `jobs.json`. Preparation and dry runs cost zero. `scripts/run_reader_reviews.py --execute` refuses to run until the frozen manifest records the approved cap and human authorization and the public release policy enables precisely that reader cap. Before each paid call the current authorization must still match. No reader key is supplied to GitHub Actions.

## Prepared corpus

Approved registration SHA-256: `7e82aff66f337c6fe5d7ddbbe9cb4c76ece07a01379e2e612f5d8f6ea3b4e7f8`. The frozen job set contains 9,854 reader calls for 5,026 active entries; the 198 existing mini passes are reused. The illustrative uncached estimate is **$7.15**. The approved **$25 hard cap** includes retries and unresolved reservations. Job-set SHA-256: `4625ebe7d587b9a28e7a326512b3540d6640165fd74ebcb72b402af2f6de2b1c`.

## Completed run

All 9,854 new reader calls returned valid verdicts, completing pairs for all 5,026 registered entries. There were 3,875 pairs with two passes, 846 disagreements and 305 pairs with two rejections. Together with the 24 prior scope drops, the build reports 3,875 judged, 846 reviewed, 329 dropped and zero candidates. No numbered release is marked.

Receipt-backed cost is **$8.036780**, including retries, with **$0.229910** retained for 46 uncertain transport attempts. No explicit provider refusals or unfinished responses occurred. The new reader cost per registered entry is **$0.001599**, excluding the 198 reused pilot passes. Model-specific costs and token usage are in the aggregate receipt report. No definitions were rewritten on this line.

## Source-recovery continuation

Vishnu instructed source recovery, fresh drafting and independent review of the eligible remainder. The first continuation registered 330 calls for 165 newly drafted definitions at `7c2778639e8f52f858599a71824349ff4be590460c96258d91cd515065e24738`. Model snapshots and prompts are unchanged; every previous charge and uncertain reservation remains on the original **$25 ledger**. This is a queue amendment, not a new cap. Cumulative outcomes and cost are regenerated in `reports/independent-readers.json`.

Before publication, 22 first-wave entries were quarantined after a source extraction check found external quotations. Their verdicts and costs remain in the private audit and cumulative cost report, but they do not contribute to public entry statuses. Clean re-extraction must precede any new definition from these articles.

## Status policy amendment: dropped and redraft

The later human instruction supersedes the historical use of “dropped” above for definition failures. `dropped` is for out-of-scope headwords, pending a scope read for the current exclusions; they are not redrafted. `redraft` is for in-scope headwords whose definitions failed their packets. Those headwords return to the candidate pool marked “new packet required”. A replacement is a new entry with new provenance and its own two independent reads. Forward-only state applies to entries, not headwords; existing receipts and verdicts remain unchanged.
