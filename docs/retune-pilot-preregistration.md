# PsychTerms pilot development rerun

Vishnu authorized rebuilding the redraft pipeline, using API models as needed, and testing the existing pilot items first. Active execution is `retune-pilot-v8`, frozen in `data/retune-pilot-v8-registration.json`. All paid attempts share the **original $200 total redraft ledger**; there is no new $200 allowance.

This is development on an already inspected 500-item corpus. Its results cannot be described as held-out accuracy or as independent validation. The original 16/500 report, source packets, failed entries and receipts remain unchanged.

## Models and evidence

| Role | Pinned snapshot | Reasoning |
|---|---|---|
| Packet fit | `gpt-5.2-2025-12-11` | low |
| Draft | `gpt-5.4-2026-03-05` | low |
| Reader A | `gpt-5.4-mini-2026-03-17` | low |
| Reader B | `gpt-5.2-2025-12-11` | low |

Readers differ from each other and the drafter. Fit and Reader B are separate stateless requests. No reader sees another verdict, fit decision or drafting feedback. All models are from OpenAI; no model-family independence is claimed. The API inputs contain only the headword, taxonomy hint, permitted source packet and, for readers, the new draft. Legacy or failed definition prose is never model input.

Fit checks the entire headword and intended sense, with explicit scope boundaries. It accepts explained concepts in ordinary prose without requiring the word “psychology”, recognizes neuroscience and research methods, and does not treat a multiword term as a request to define one prefix. It rejects biographies, acronym collisions, superficial mentions and unrelated biomedical senses. A yes must quote an exact source span.

Readers assess semantic entailment and accept faithful paraphrases and non-distorting omissions. Source text and draft have separate named containers. Passing readers must provide supporting source spans, which the executor verifies against the packet. Taxonomy issues are recorded separately and require field review before publication. No fields are changed automatically.

## Developer controls

Nineteen agent-authored examples have separate labels for source fit and draft support. These labels were assigned and checked by the execution agent, not a clinician. They test paraphrases, acronyms, combining forms, multiword neuroscience terms, research methods, historical framing, wrong senses, unsupported claims, advice and unrelated biomedical material.

Before replay, all 19 fit controls and all 18 unsupported-reader controls must be correct; at least 18 of 20 supported-reader decisions must pass. False rejections are reported. The current scoring is **56/57**, with no unsupported-reader passes and one false rejection of a supported combining-form definition.

A control-label correction is explicit: a ribosome definition can be entailed by its source while being outside this dictionary’s scope. Fit must reject that packet; support readers should recognize the factual entailment. The original label and actual decisions remain retained. Compatible control responses are reused with their original registration and provider IDs, not relabelled as new inference.

## Fixed corpus and phases

All 500 original headwords remain in the denominator, including missing packets. The seed remains **20261018**.

1. **Same packets:** use the original BGE top-two packets with the revised fit/readers and unchanged source-only drafting prompt.
2. **Unused retrieval:** for headwords still failing, try up to three unused candidates from the original permitted five-packet retrieval. Do not retry the original top two. Exact source-label matches come first, then packet hash.
3. **Added sources:** for remaining failures, try the top two BGE-ranked government packets from [the separately approved three-source expansion](approved-source-expansion.md).

The original source inventory rows must remain identical; its only permitted additions are the three specified source families. The new government options are prepared from up to five candidates each. HPO supplies exact aliases and related references only, never drafting prose or new headwords. In the pilot this adds 37 packets for 24 headwords, with seven HPO reference matches.

Every new source passage enters the 15-word comparison before drafting. One to three sentences, no advice/doses/identifiable cases, two non-drafter passes, fresh provenance, version 2, immutable old entries and source/cross-entry copy checks remain required. No semantic rewrites are performed against the same packet. Source fit, drafting and reader failures are reported separately; unverified outputs are not evidence that a source does not exist.

No second wave starts automatically. The existing 60% full-headword continuation rule is retained for future execution; a development replay does not establish unseen-corpus performance. Results remain private staged proposals until publication checks, including any field review, are complete.

## Budget, transport and resumption

The ledger is `.private/hybrid-redraft/budget.sqlite`. Every fit, draft, read, control and retry reserves cost before dispatch. Maximum request size is 30,000 bytes; completion limits are 1,600 fit, 1,000 draft and 3,000 reader tokens. At most six work items run concurrently.

One transport/schema retry is allowed per exact request, with a separate reservation. Every uncertain billable reservation remains counted against the same cap. Exhausted per-request failures remain unresolved; authentication/configuration and budget failures pause the whole run. Compatible actual responses from the explicitly pinned v7 parent are reused only after request, response, source, model, cost and manifest audits. Original provider IDs and registration bindings are retained, and inherited errors count toward the retry limit.

Prices and API capabilities were checked in official documentation: [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4), [GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini), [GPT-5.2](https://developers.openai.com/api/docs/models/gpt-5.2). Per-million input/cached-input/output rates: drafter $2.50/$0.25/$15; mini $0.75/$0.075/$4.50; GPT-5.2 $1.75/$0.175/$14. Actual usage, all attempts and unresolved reserves are reported by the shared ledger.

## Retained development history

| Registration | Finding or amendment |
|---|---|
| v1 | Mini/nano controls exposed unsupported passes; a connection reset left a reserved uncertain attempt. |
| v2 | Exact evidence support added; nano could not reliably distinguish draft claims from source spans. |
| v3 | GPT-5.2 replaced nano; reasoning-disabled checks remained overly literal. |
| v4 | Low reasoning improved controls to 47/48; one valid DBT example was treated as missing source text. |
| v5 | Source and draft containers separated; replay exposed exercise-biology sense confusion and overly broad batch stops. |
| v6 | GPT-5.2 fit, explicit scope controls, per-packet output failures and the approved source expansion. |
| v7 | Corrected the scope-versus-entailment control label and began replay; connection failures paused it after 115 completed headwords. |
| v8 | Resume/transport amendment with unchanged model prompts, controls and source packets; compatible actual responses reused. |

Each registration, original control decision, code snapshot and receipt is retained. Earlier attempts are not pooled as extra reader votes or hidden from costs.

## Artifacts and commands

```sh
.venv/bin/python scripts/recover_approved_sources.py
.private/also-see-venv/bin/python scripts/prepare_reference_packets.py
.venv/bin/python scripts/retune_pilot.py prepare
.venv/bin/python scripts/retune_pilot.py run
.venv/bin/python scripts/finish_retune_pilot.py --wait
```

Preparation refuses to overwrite a registered run. Frozen inputs and executable hashes are checked before dispatch. Active staging is `.private/retune-pilot-v8/`. The output report is `reports/retune-pilot-v8.md`, with JSON and a 500-row outcome CSV. The finalizer checks all original failed-entry hashes, adds failure diagnostics and a seeded sample of passing definitions with their sources. It performs no inference, publication or automatic next wave.

## Executed result and later preparation fix

The completed v8 replay used inference code from commit `3509dcd9` and the frozen source options in its private cohort. It yielded 128/500 two-reader/copy passes (25.6%): 96 with original packets, 31 from unused original packets, one from the added government sources. Thirty proposals have field flags. No definitions were published and no later wave started. The finalizer corrects missing-packet counts from the actual frozen arrays, separately from incomplete fit responses; the original dispatch summary is retained.

After paid inference finished, the source preparer was updated to deduplicate identical CDC text reached through redirect URLs before selecting five candidates. This changes future full-pool retrieval to 295 top-two packets for 189 headwords, with 22 HPO reference matches. The frozen 500-item replay and its paid model results were not regenerated or inflated by that later preparation fix.
