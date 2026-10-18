# PsychTerms pilot report, 18 October 2026

**The vignette final-drop gate failed: two of seven scenes still added unsupported facts after their allowed redraft (28.6%, above the registered 20% stop). Paid dispatch is disabled. No full run or public dictionary release occurred.**

The adapter, fixed term-to-card fit ledger, generated-output scans, bound two-judge checks and receipt accounting are implemented. The initial adapter hash uses the existing canonical JSON SHA-256 function; builder seeds, parameters and card field allow-list were unchanged. Any later field or card-hash-rule change still goes through Vishnu.

## Outcomes

| Stage | Result |
|---|---|
| Definitions | 200 attempted; 195 machine passes, five drops, zero incomplete reviews |
| Definition final copy scan | One 15-word hit, already among the five drops |
| Definition five-word triage | 70 hit entries: 56 stock/technical fragments kept, 12 wording holds, two already dropped |
| Scene-candidate selection | 50 fixed candidates from 118 room-eligible double-reviewed terms; no post-fit replacements |
| Card fit | Seven matches, 38 unmatched with reasons, five risk exclusions |
| Scenes | Seven drafted; five retained privately, two dropped after the one allowed redraft |
| Scene copy scan | Zero initial/final 15-word hits; two short five-word hit entries triaged without blanket rewriting |
| Publication | Zero release-approved entries; three existing site preview fixtures remain separate |

The 195 definition machine passes are not 195 release-ready entries: 12 have unresolved wording holds, and the registered held-out human release read has not occurred. No second redraft was performed for any scene. Risk terms receive no scene; their site notice remains exactly “No scene is provided for this risk term.”

## Cost from receipts

| Output | Usage-based cost | Per attempted output | Per machine pass / retained scene |
|---|---:|---:|---:|
| Definitions | $1.579565 | $0.007898 (200) | $0.008100 (195 machine passes) |
| Scenes | $0.233564 | $0.033366 (seven) | $0.046713 (five retained privately) |
| Total receipted estimate | $1.813129 | | |
| Unresolved original reservations | $0.053720 | Three unreceipted outcomes remain held | |
| Spent estimate plus held | $1.866849 | Within the same $20 line | |

All earlier charges and uncertain reservations carried forward. The term-fit/exclusion step used no paid model calls. Unmatched/risk candidates were not charged as drafted scenes and were not replaced to manufacture 50 outputs. Per selected scene candidate, actual scene cost was $0.004671; that is a coverage denominator, not a drafting-unit price.

The receipt audit verified 828 charged calls against raw response content, pinned model prices, parsed caches and the shared ledger. It reconstructed all 39 scene request hashes from the permitted packets, accepted definition records and allowed card views. All definition request bindings were separately recovered against the original frozen protocol. The [207-row item cost CSV](pilot-item-costs.csv) includes term IDs, tokens, call counts and category costs. These are conservative usage-derived costs at uncached list prices, not a provider invoice.

| Paid category | Cost |
|---|---:|
| drafting | $0.462742 |
| initial judge a | $0.150059 |
| initial judge b | $0.611163 |
| initial vignette judge a | $0.014774 |
| initial vignette judge b | $0.058482 |
| redrafting | $0.178353 |
| repeated judge a | $0.041140 |
| repeated judge b | $0.135425 |
| repeated vignette judge a | $0.010428 |
| repeated vignette judge b | $0.048346 |
| transport schema retry | $0.000683 |
| vignette drafting | $0.052671 |
| vignette redrafting | $0.048863 |

## What the pilot found

The two judges passed five initial scenes that the editorial audit found had added client facts: a current asthma-related breathing action, an extra work stressor, an unprovided migraine/workplace episode, an objective work error, or an invented weekly course. Five editorial redrafts used the existing allowance; one other scene had already used its redraft after a judge rejection. Both judges and both scans ran again after every change.

Two final outputs still crossed the factual boundary. The Frustration scene invented a partner saying the client seemed distant. The Shame scene added an unsupported duration and strengthened “has not slept well” into “barely slept.” Both judges passed these outputs; editorial audit overruled those verdicts and dropped the scenes. The registered final-drop stop therefore applies. This is an observed disagreement with the packet/card audit, not a measured population-wide judge error rate.

The copy check and semantic checks answer different questions. ArcSim’s six-word bank check concerns its inputs; it did not substitute for any generated-output scan. Short five-word card fragments were not treated as automatic copying failures. Definition triage similarly distinguished technical/common phrasing from 12 passages needing more independent wording; those holds are recorded in [the triage report](definition-overlap-triage.json), with no further paid calls after the stop.

## Scope and remaining work

The definition source configuration is MeSH 2026 psychology branches, not all sources or all counselling fields. The seven supported card matches do not estimate coverage of an expanded card bank. The producer’s private pools and the legacy derivative fixture never entered a model request or this comparison corpus.

Request latency was not measured: the executor omitted start/end timestamps. No timings are inferred from file modification times. This reporting gap and the observed factuality disagreements must be addressed before scaling the configuration. Full generation remains unauthorized; this report does not infer a new spending line. No site, GitHub Pages deployment or DNS change occurred.

The immutable base PREREG is [pilot-combined-preregistration.json](../data/pilot-combined-preregistration.json); the bounded editorial executor was recorded before its calls in [pilot-editorial-addendum.json](../data/pilot-editorial-addendum.json). Original drafts, verdicts and private receipts remain available for audit. The five retained scenes and all generated definitions remain private pilot material.
