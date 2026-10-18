# Psych Terms: consumer acceptance of the ArcSim interface

18 October 2026. Dictionary-side design acceptance, recorded from Vishnu's updated `PSYCH_TERMS_INTERFACE.md` at handoff commit `2973eb9a84d62386022a8aecb5e4a5450cb0ff6e`, using builder commit `12bd28281f5d8ed607e1ff6f46e7246293f925f3`; this supersedes both earlier handoffs. This records our half; it does not claim a message was delivered to the producer chat or that its proposed adapter exists.

## Accepted boundary

Psych Terms drafts the open vignette from its accepted definition and ArcSim's approved card view only. ArcSim supplies cards, not vignette prose. The planted term stays outside the reusable card. A vignette contains a 100–150 word fictional third-person scene and one separate “what to notice” line. It trains recognition or judgment by a helper and never addresses a person in distress.

Use only code-built persona-schema v0.3 cards with `fit=True`, at a pinned builder commit, from ArcSim's own banks. Hand-made cards, including B1/Sandra, and `scenario:...` personas are excluded. The field allow-list and prohibitions in the supplied producer document govern the view: no sexuality, ethnicity, risk history, imported text, transcripts, shared-tier material or hidden scenario content. Nested free-text values need the same filtering as top-level fields. No real place or organisation may survive the projection.

## Dictionary-owned request and checks

The producer's term envelope is accepted: `term_id`, `headword`, `field`, `type`, `show` (`client_line`, `moment` or `choice`), `notice_line`, `card_id`, `card_hash`, and `builder_commit`. Psych Terms additionally pins the accepted definition's version and hash, the card-view schema version and hash, the view payload hash, this contract hash, and the drafting/check protocol. `notice_line` is a proposed teaching focus in the input; the final line must be judged with the scene. The producer's `pt:...` example is illustrative; the integration must preserve the dictionary's stable term identifier rather than silently renaming entries.

Two distinct judges independently receive the same definition, permitted source packet, approved card view, scene and notice line. Both must pass the same output hash. They check conceptual fidelity, card consistency, the word range and exclusions, including advice, doses, criteria lists and identifiable people. Record each verdict and its receipt. Apply the overlap scan against the frozen permitted comparison set: 15-word hits require redraft; five-word hits receive triage. Any scene repair requires both judges again. Register the retry and redraft limits before calls.

Select 50 eligible terms for the combined pilot from the independent frozen inventory, with the sample and seed recorded. No quota follows from the spec's approximate fraction. Research methods, anatomy and statistics do not acquire scenes merely to fill the pilot. Risk terms have no vignette in the first vignette release and display the one-line notice in vignette-pilot-protocol.md. No separate risk-card path is authorized.

Definitions release first. Vignettes have separate versions, hashes and review status; unfinished scenes cannot hold back accepted definitions. Public provenance identifies the open card and builder without any closed-case crosswalk, answer key or planted-answer link. Playable-case generation and B3 remain ArcSim/Prep responsibilities.

## Verified producer handoff and remaining implementation

The updated attachment is byte-identical to `arcsim/PSYCH_TERMS_INTERFACE.md` at handoff commit `2973eb9a84d62386022a8aecb5e4a5450cb0ff6e` in `cloudronin/uofa-lab`. The builder is pinned independently to `12bd28281f5d8ed607e1ff6f46e7246293f925f3` with SHA-256 `31088a31425b31a2de29a8e8ed5ee4f656822983fbf6b07bc44f9dd38415453e`. Both declared builder/schema SHA-256 values match those Git objects. The repository contains the Apache 2.0 licence and the package declares it. The builder's source documents that its phrase banks are ArcSim's own writing, with Patient-Psi supplying structure only. This is recorded provenance from the producer, not an independent authorship audit.

The example base card reproduces exactly using `build("example-4", fit=True)` at the pinned builder commit. Its intake-only example also reproduces for a one-card `other` stratum. The three reported fixes pass direct checks over 1,000 generated cards: unique first names, no work-based situation/coping for a no-job card, and no “dressed for work” observation for those cards. The producer's 114-test suite count is user-reported and was not rerun here. Verification details are in `reports/arcsim-handoff-verification.json`.

The seed and default `problem`/`style` parameters now provide a concrete rebuild recipe. Store these alongside the full commit, builder/schema hashes, Python runtime, and `fit=True`; the exact builder pin above controls execution. The builder-verification turn did not implement a card hash rule. The subsequent authorized adapter implementation now fixes the initial base-card rule using the project’s existing canonical digest, documented in card-hash-proposal.md. Any later change goes through Vishnu first. Never send `intake_only` to writers or judges. The generated base card itself contains none of those intake fields.

The dictionary adapter is now implemented in scripts/arcsim_adapter.py. Rebuild cards from their registered seeds and parameters, reject scenario-bound or altered cards, and construct the view by explicit field selection. Nested text receives the same exclusions. The model receives only that view and the accepted definition; provenance metadata is kept separately. Pin this adapter and its verification tests in the combined pilot PREREG. No additional producer handoff or chat agreement is needed to start this implementation.

## Execution status

Paid dispatch is disabled. The old 200-definition-only registration and original executor are preserved as historical evidence; neither authorizes another call. The amended registration must cover 200 definitions plus 50 vignettes, both judges, sampling, all executable dependency hashes and separate per-item cost reporting. Its $20 total includes the interrupted run's receipted spend and unresolved reservations. No full run is authorized. No interface code or vignette generation is claimed complete by this document.

## Fixed inputs and change control, 18 October update

The verification corpus retains the same seeds (`example-4` and integer seeds 0–999), with `problem=None`, `style=None`, `fit=True`. Those inputs are fixed. Rebuilding with the approved builder changes 161 integer-seed cards, exclusively through `FIT_WORDING` in automatic thoughts. The example card is unchanged. All 1,000 `fit=False` comparisons are unchanged; the previous three card consistency regression checks still pass. Rebuilt cards stay in the private verification folder; these are not a selected 50-vignette pilot sample.

From now on, do not change the builder seeds or parameters without Vishnu's direction. Any change to vignette fields or the card hash rule goes through Vishnu first. A later builder commit is not adopted automatically; verify its file hash against the approved pin and preserve the fixed inputs. Private-pool overlap results in the producer handoff are producer-reported; this session did not access those pools or repeat that scan.

Reproduce the rebuild with `python3 scripts/verify_arcsim_handoff.py --repository <local-uofa-lab> --handoff <approved-attachment>`. This offline script verifies the pinned Git blobs and attachment before executing the builder and checks the complete card against the previous output plus the single authorized wording replacement.

## Fit and output checks, subsequent direct decisions

Term-to-card fit is an explicit pre-drafting step: review field/type and the accepted definition against the fixed card problem, situation, history and mental-status lines, recording evidence and rationale. No fitting card means no scene, with a reason and an unmatched pilot count; never force the story or resample to fill a quota. Risk exclusions are counted separately. See `vignette-pilot-protocol.md` and `data/vignette-policy.json`.

ArcSim’s six-word bank check covers inputs only. Generated scenes and notice lines independently require the dictionary’s unchanged 15-word overlap scan and both distinct judges. Redrafts repeat all output checks. Five-word output matches remain triage.

## Implementation under the instruction to proceed

The pinned adapter, explicit fit ledger, independent generated-output scans and bound two-judge checks are now implemented. The existing canonical digest fixes the initial base-card hash, with no prior registered hash rule changed. The earlier suggestion to require an additional initial-hash approval was an implementation interpretation, not a new user prerequisite. Future field or hash-rule changes still require Vishnu. The combined registration is frozen before its bounded calls; the 50 candidates yield seven supported card matches, 38 unmatched concepts and five risk exclusions. No sample is padded. No public release is authorized by these machine checks.
