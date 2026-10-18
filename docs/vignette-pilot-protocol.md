# Combined pilot: vignette fit and output checks

Required protocol, not a frozen PREREG and not dispatch authorization. These decisions amend the upcoming 200-definition / 50-vignette-candidate pilot; the historical definition-only registration remains unchanged. The same $20 total includes previous spend and outstanding reservations.

## Fit protects whether the scene actually illustrates the term

Before drafting, review each candidate's accepted definition, field and type against the fixed cards' presenting problem, situation, relevant history and mental-status lines. Record the classification, reviewer, rationale and supporting card fields in the frozen fit ledger. A broad problem label is insufficient: an anxiety card does not by itself support a panic attack, and bereavement does not by itself establish complicated grief. The required concept must be supportable by the actual story; the writer cannot manufacture missing history, symptoms, risk facts or observations to make it fit.

A matched term names an unbound card and pinned builder, the accepted definition version, and explicit problem/history/situation/mental-status evidence. Evidence may state why a field is neutral or not determinative; it must not invent supportive detail. A term with no fitting card is `unmatched`, with its reason recorded and no card assigned. It gets no vignette. Do not change fixed seeds/parameters, add card text or replace unmatched terms to manufacture 50 scenes. Vignette fields and the card hash rule stay under Vishnu's change control.

The pilot reports candidate count, pending fit decisions, risk exclusions, unmatched count and reasons, matches, scenes drafted and scenes accepted. The requested 50 describes the candidate sample; the achieved scene count may be lower and must be reported honestly. Field/type ineligibility is recorded before drawing that sample. Missing fit work is pending, never zero unmatched. The ledger auditor `scripts/vignette_fit.py` checks decision structure and counts; it does not determine semantic fit. No actual pilot ledger or unmatched count exists yet.

## Risk decision: no vignette through this interface

Risk cards carry no risk history, and none may be added. Risk terms, including suicidal ideation, duty to warn and safety planning, are `excluded_risk`, recorded separately from unmatched non-risk terms. The first vignette release has no risk-term scenes. Their entries display exactly one line:

> No scene is provided for this risk term.

The open site has no product mention beyond its footer line. Prep’s field pass and required label remain an internal integration responsibility. There is no authorized separate risk-card path. A risk term remains eligible for a supported definition; exclusion from vignettes does not drop its dictionary entry.

## Output checks protect the generated writing

ArcSim's six-word bank test checks its input banks against the producer's private pools. It does not check generated writing and never substitutes for the dictionary's output scan or judges. This session does not import those private pools into the dictionary's reference set.

Export generated scenes and their notice lines to a separate scanner-ready Markdown file, one entry per term, then invoke the unchanged `scripts/overlap_scan.py` with `--min-words 15` against the registered frozen permitted reference set. Scan the definition export separately. Retain scanner version/hash, comparison-set manifest/hash, input hash and results for each output type. A reference hit of 15 or more words requires redraft; five-word matches receive editorial triage. Entry-to-entry duplicate reports receive dedupe review. No clean-bank result waives any of these checks.

Both distinct judges independently receive the same scene, notice line, accepted definition/source packet and permitted card view. They check that the scene illustrates the definition, fits the card without added facts, meets the 100–150 scene-word range, and avoids advice, criteria lists and identifiable people. The notice line is separate from the scene-word range but is included in the overlap scan and judge input. Use a vignette-specific form rubric rather than a definition's three-sentence limit. Neither judge sees the other's verdict. Both must pass the same final output and pinned inputs. Every redraft goes through the output scan and both judges again; unresolved failures drop the scene with a reason.

The combined PREREG must freeze these inputs, prompts, limits, executable hashes and report denominators before paid calls. Fit exclusions and unmatched candidates are not model failures; report them separately from generated scenes rejected by checks. Definitions release first, independently of vignette availability.
