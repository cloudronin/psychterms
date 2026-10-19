# Pilot correction after Claude's 70-entry review

Registered before new paid calls, 19 October 2026. This is a correction of the inspected pilot, not wave two or an independent validation.

The user supplied 44 PASS, 26 FAIL and 20 field retags. Exactly 24 failures return for a same-packet redraft. Superconducting quantum interference device is excluded as out of scope; blank screen is excluded as not a standalone term. Original proposal files and all prior receipts remain unchanged. A decision overlay retains the 70 entry identities, reasons and resolved fields. No other entries or canonical statuses change.

The drafter must define the general headword, not one article's operational use, and must not report findings or use source-relative framing. If the existing packet cannot support a general definition, it must return insufficient rather than invent missing meaning. Both reader prompts carry the named **Term meaning, not study usage** check. A separate source-context reader path carries the same rule. A local phrase guard rejects explicit prohibited framing even if a model returns PASS. Semantic narrowing without those phrases still requires the model check; a developer regression example covers that distinction. These contract tests do not establish model detection accuracy.

## Frozen execution

- Input: exactly the 24 eligible failures from the attached verdict file, bound by SHA-256 and exact IDs to the 70 previously exported proposals.
- Sources: the same source text, labels and publisher aliases as each failed proposal. No retrieval, new sources or new headwords. Only metadata, corrected fields and new proposal IDs change; original text hashes remain fixed.
- One fresh packet-fit call, at most one fresh sufficient draft, and two independent non-drafter reads per admitted packet. Drafter sees no previous definition or reader verdict. Readers see only the new definition and source evidence, not Claude's verdict.
- Models and existing price schedule are frozen in `data/pilot-claude-redraft-registration.json`. Existing roles: GPT-5.2 fit, GPT-5.4 draft, GPT-5.4 mini and GPT-5.2 readers.
- Every paid call reserves and reconciles against the **same original $200 redraft ledger**, including all prior development and uncertain reservations. There is no reset or additional allowance. Existing bounded transport/schema retry policy remains one retry; it is not an iterative content-redraft loop.
- New proposals are version 3, superseding the privately reviewed failed version 2 proposals. Own packet bindings and receipts are retained. A 15-word scan compares against frozen sources, previous comparison corpus, the 44 retained definitions and accepted corrections.
- Output: independent model passes, field flags and unresolved same-packet failures reported separately from the 44 Claude passes. No automatic publication and no wave two. The 60% original-cohort continuation criterion remains unchanged; correcting 24 inspected failures is not a new denominator for that criterion.

Run `scripts/revise_pilot_after_claude.py prepare --verdicts <file>` before `run`. Frozen code and request receipts are kept with the private run; public reports contain decision summaries and source/definition hashes. Corrected proposals can be exported for another Claude review.

## Executed result

Executed from commit `d0e2a63d`: four new proposals passed both readers and the 15-word scan; 20 remain unresolved. All 24 outcomes were exported with unchanged source text for Claude. These four are model-reviewed corrections, separate from the 44 earlier Claude passes. Incremental receipted usage was $0.329586. No canonical entries were changed, nothing was published and wave two did not start. All 20 field retags remain in the staged decision overlay.
