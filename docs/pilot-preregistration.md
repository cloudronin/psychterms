> Historical definition-only protocol. Superseded for future dispatch by the 200-definition plus 50-vignette instruction. Retained for auditing the interrupted run; not authorization to resume.

# Pilot preregistration: 200 terms, two judges, $20 maximum

Status: FROZEN before paid execution. Machine-readable manifest: data/pilot-preregistration.json. Preregistration SHA-256: `a1829e61865d72e6e9784993644b00b5adc2eae22a187652c15cb0a54bd1992a`. No full run is authorized.

## Question

What is the observed cost and acceptance rate of independently drafting and double-judging source-supported psychology definitions, including failed attempts and the allowed redraft?

## Fixed protocol

Use 200 terms selected from the independent permitted-source inventory, stratified across the represented psychology/counselling fields and difficult aliases, historical terminology, eponyms and biomedical homonyms. Never use legacy headwords to choose the sample. Report unsupported field coverage rather than filling it artificially.

A teacher drafts one to three sentences from a term-specific permitted packet. Two distinct judge models independently receive the definition and exactly that packet; neither sees the other's result. Both must pass the frozen rubric. Any failed judge or 15-word copy hit triggers at most one editorial redraft, then both judges must evaluate the new text again. An unresolved failure is a recorded drop. Transport/schema retries are separate from editorial redrafts and count toward the budget.

Stop and review if >10% of the initial 200 definitions have a >=15-word match against the frozen comparison set, or >20% are dropped after the one allowed redraft. Five-word matches are triage only. No threshold is a count target or deadline.

## Required freeze fields before dispatch

- Final sample IDs, stratification, selection seed and sample hash.
- Packet files and hashes, licence review, source revisions and permitted roles.
- Draft model and TWO distinct judge model IDs, settings and structured output contracts.
- Frozen draft prompt and two judge prompts/rubric hashes; both prompts reject unsupported claims, invented entities, treatment advice, criteria lists, personal cases and >3 sentences.
- Official price-page snapshot/date and input/output prices for each model, maximum prompt size and output-token reservation, retry bounds, aggregate worst-case reservation rules.
- Frozen definition-only comparison set and its source manifest/hash; overlap scanner hash.
- Immutable preregistration manifest hash; explicit record that the $20 pilot line is authorized and that no full-run line exists.

The runner must reject any missing freeze field. This document alone does not enable paid dispatch. No arbitrary placeholders may be accepted as model IDs, prices, samples or packet hashes.

## Budget and receipts

Total pilot cap: USD 20.00, including initial drafts, judge A, judge B, editorial redrafts, repeated judging, transport/schema retries and unsuccessful billable responses. Reserve each call's maximum configured cost atomically before dispatch; spent plus outstanding reservations must remain within the cap. Do not infer that a failed request cost nothing. Reconcile actual usage against receipts; unknown usage keeps its reservation until resolved.

Report total and per-attempted-entry cost separately for drafting, judge A, judge B, editorial redrafts, and transport/schema retries. Also report cost per accepted entry, initial and final pass rates, disagreement rate, drop reasons, latency, token counts and source/field coverage. Record zero-cost categories explicitly.

No full generation, new paid line, or cap increase follows automatically. Vishnu sets the full line after seeing the actual pilot report. There is no standing $150 limit or fixed target count.

## Frozen pilot scope

The initial eligible source coverage is MeSH 2026 psychology branches F01–F04: 50 independently selected terms from each branch, 200 in total, seed 2026101802. The pilot measures this source configuration, not all-source coverage or every counselling field. Scope notes over 1,200 characters and notes identifying restricted dictionaries or DSM sources are excluded.

Teacher and judge B: gpt-5.4-2026-03-05. Judge A: gpt-5.4-mini-2026-03-17. Judges are separate calls, use distinct model snapshots, and never see each other’s verdicts. Each model has a maximum of 1,000 completion tokens, low reasoning effort, no tools, and structured outputs. A failed or truncated response can retry once; an editorial failure can redraft once and must be judged twice again.

Standard uncached input/output prices per million tokens, verified from official model pages: GPT-5.4 $2.50/$15.00; GPT-5.4 mini $0.75/$4.50. Receipt accounting conservatively ignores cache discounts. Requests reserve the full serialized request byte count plus 512 input tokens and the entire output cap. The $20 total cap includes unresolved attempts.

Sources: [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4), [GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini). These are pilot choices to be evaluated, not a claim that two models provide clinical certification.
