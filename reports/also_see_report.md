# PsychTerms: see-also report

Review required before merge. Definitions, entry files, hashes and reader verdicts are unchanged.

| Measure | Count |
|---|---:|
| Entries eligible | 9,201 |
| Entries with 0 links | 115 |
| Entries with 1–2 links | 916 |
| Entries with 3–4 links | 1,297 |
| Entries with 5 links | 6,873 |
| Links: mention | 11,357 |
| Links: same_source | 0 |
| Links: embedding | 29,095 |
| Headword targets appearing in more than 40 definitions | 283 |
| Mention pairs rejected by document frequency | 36,756 |
| Embedding proposals rejected by field filter | 104,929 |
| Unique inbound risk pairs blocked | 1,585 |

## Kept embedding cosine distribution

| Min | p25 | Median | p75 | Max |
|---:|---:|---:|---:|---:|
| 0.601391 | 0.713814 | 0.746720 | 0.786645 | 0.991275 |

## Reproduction and interpretation

- Model: `BAAI/bge-small-en-v1.5`; revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
- Weights SHA-256: `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad`.
- Entry-set hash: `72991b96724b2deaa094d19cd79acd5e1dd9607eb134774b95d3eae3d84e439e`.
- Input hash (retagged entries, risk, redirects, stop list, parameters): `c8edf0ba4ecf2ede783f2f5578df6aaec045c3de8a819aeec23ae08a6b24cfbf`.
- Parameters: cap 5; mention cap 2; headword document frequency ≤ 40; source cap 3; global nearest 20 excluding self; cosine ≥ 0.60; embedding links require identical fields.
- Sampling seed: `20261018`. Uniform sample without replacement from all eligible IDs, including zero-link and risk entries.
- Risk blocking is applied to all three signals after redirect resolution; risk entries may link out.
- Document frequency counts published definitions containing a canonical headword, case-insensitive whole words with singular/plural matching. Each definition counts once, including the target’s own definition; aliases do not increase this count. Targets above 40 cannot supply mention links, including through aliases. The stop list remains a backstop. Other signals remain eligible.
- Diagnostic counts audit all mention/source proposals and qualifying top-20 embedding proposals even when five slots are already full. Field rejection excludes already-linked and risk targets. Risk count deduplicates the same directed pair across signals after the mention-frequency filter. Frequency rejection counts unique non-self mention pairs after stop-list filtering, before risk filtering.
- Local CPU inference only. Input is exactly `term: definition`, with normalized vectors and no retrieval prefix. No paid calls, no remote embedding service, no LLM-written links.
- Source identity requires an identical nonempty `packet_hash`; shared provenance scope does not qualify. It is a structural candidate signal, not an additional model judgment.
- Singular/plural matching uses English suffix rules and an explicit irregular-noun table; punctuation separates words. Mentions prefer the longest matched phrase globally, then first occurrence, then headword and ID. At most two mention links are retained; after up to three identical-packet links, embeddings fill remaining slots. Cosine ties use ID order.
- Entry `also_see` is hash-covered. Source entries and exported entry hashes remain untouched; the site reads the separate graph in signal order.

## Twenty random entries

### [feeling](https://psychterms.org/terms/feeling/)

Field: history.

In this historical psychology source, feeling is the aspect of consciousness concerned with experienced changes apart from identifying objects or directing action. It is used broadly as a phase of mental life within the traditional division of knowledge, feeling, and will, and is treated as an abstraction from a fuller state of mind.

- [abstraction](https://psychterms.org/terms/abstraction/): `mention`.
- [experience](https://psychterms.org/terms/experience/): `embedding`; cosine 0.839159.
- [feeling of reality](https://psychterms.org/terms/feeling-of-reality/): `embedding`; cosine 0.821866.
- [content](https://psychterms.org/terms/content/): `embedding`; cosine 0.819207.
- [image](https://psychterms.org/terms/image/): `embedding`; cosine 0.809122.

### [myelination](https://psychterms.org/terms/myelination/)

Field: cognition.

Myelination is the process in which oligodendrocyte precursor cells develop in ways that produce myelin, a covering that gives neurons structural and metabolic support and helps nerve signals travel efficiently along axons. When myelin is lost, neurons become more vulnerable and can undergo degeneration, contributing to lasting disability.

- [oligodendrocyte](https://psychterms.org/terms/oligodendrocyte/): `mention`.
- [precursor](https://psychterms.org/terms/precursor/): `mention`.

### [bipolar](https://psychterms.org/terms/bipolar/)

Field: biological.

Bipolar disorder is a mental health condition that often begins during adolescence, a key period of brain development. In this context, it is described as having neurobiological features that are partly shared with, and partly distinct from, major depressive disorder.

- [bipolar disorder](https://psychterms.org/terms/bipolar-disorder/): `mention`.
- [depressive disorder](https://psychterms.org/terms/depressive-disorder/): `mention`.
- [depression](https://psychterms.org/terms/depression/): `embedding`; cosine 0.797355.
- [mania](https://psychterms.org/terms/mania/): `embedding`; cosine 0.780622.

### [self-esteem](https://psychterms.org/terms/self-esteem/)

Field: learning.

Self-esteem is a person’s overall evaluation of themselves, including both positive and negative views of who they are. In psychology, it is treated as an important aspect of children’s physical and psychological development.

- [self-affirmation](https://psychterms.org/terms/self-affirmation/): `embedding`; cosine 0.803467.
- [self-image](https://psychterms.org/terms/self-image/): `embedding`; cosine 0.794550.
- [pride](https://psychterms.org/terms/pride/): `embedding`; cosine 0.760920.
- [self-efficacy](https://psychterms.org/terms/self-efficacy/): `embedding`; cosine 0.750902.
- [self psychology](https://psychterms.org/terms/self-psychology/): `embedding`; cosine 0.748282.

### [substance use disorder](https://psychterms.org/terms/substance-use-disorder/)

Field: diagnosis.

Substance use disorder is a disorder related to the use of substances. In the supplied source, it is described as a major global health problem that contributes substantially to overall disease burden.

- [alcohol use disorder](https://psychterms.org/terms/alcohol-use-disorder/): `embedding`; cosine 0.870385.
- [tobacco use disorder](https://psychterms.org/terms/tobacco-use-disorder/): `embedding`; cosine 0.805581.
- [gambling disorder](https://psychterms.org/terms/gambling-disorder/): `embedding`; cosine 0.784819.
- [alcohol dependence](https://psychterms.org/terms/alcohol-dependence/): `embedding`; cosine 0.778306.
- [tobacco dependence](https://psychterms.org/terms/tobacco-dependence/): `embedding`; cosine 0.772482.

### [verbal abuse](https://psychterms.org/terms/verbal-abuse/)

Field: mental health.

Verbal abuse is harmful or aggressive speech directed at a person. In the packet, it refers to patient verbal abuse toward newly graduated nurses, which is often treated as part of the job but can unsettle emotions and influence how people interpret and cope with their work experiences.

- [workplace violence](https://psychterms.org/terms/workplace-violence/): `embedding`; cosine 0.781582.
- [patient violence](https://psychterms.org/terms/patient-violence/): `embedding`; cosine 0.756416.
- [physical abuse](https://psychterms.org/terms/physical-abuse/): `embedding`; cosine 0.744611.

### [consensus](https://psychterms.org/terms/consensus/)

Field: cognition.

Consensus is a shared view or general agreement within a group. It refers to the judgment accepted by most of the people involved.

- [agreement](https://psychterms.org/terms/agreement/): `mention`.
- [submission](https://psychterms.org/terms/submission/): `embedding`; cosine 0.706755.
- [judgment](https://psychterms.org/terms/judgment/): `embedding`; cosine 0.705227.
- [principle of common fate](https://psychterms.org/terms/principle-of-common-fate/): `embedding`; cosine 0.704611.
- [group structure](https://psychterms.org/terms/group-structure/): `embedding`; cosine 0.704139.

### [-genic](https://psychterms.org/terms/genic/)

Field: history.

-genic is a suffix used in compounds in an active sense to mean producing, causing, or giving rise to something in its genesis or development.

- [genitive](https://psychterms.org/terms/genitive/): `embedding`; cosine 0.723747.
- [genu](https://psychterms.org/terms/genu/): `embedding`; cosine 0.706322.
- [mnemonic](https://psychterms.org/terms/mnemonic/): `embedding`; cosine 0.664659.
- [connate](https://psychterms.org/terms/connate/): `embedding`; cosine 0.646916.
- [saltation](https://psychterms.org/terms/saltation/): `embedding`; cosine 0.643269.

### [behavioral avoidance test](https://psychterms.org/terms/behavioral-avoidance-test/)

Field: assessment.

A behavioral avoidance test is a practical assessment in which a person is asked to face a situation they have been avoiding so their avoidance and actual performance can be observed. In this source, it refers to a post-treatment driving test in real traffic used to see whether patients could carry out previously feared driving tasks.

- [avoidance](https://psychterms.org/terms/avoidance/): `mention`.
- [behavior rating](https://psychterms.org/terms/behavior-rating/): `embedding`; cosine 0.718209.

### [irregular](https://psychterms.org/terms/irregular/)

Field: cognition.

In this context, irregular means not happening on a steady or predictable schedule. It describes episodes that occur occasionally at uneven intervals.

- [asynchrony](https://psychterms.org/terms/asynchrony/): `embedding`; cosine 0.695492.
- [conjunction](https://psychterms.org/terms/conjunction/): `embedding`; cosine 0.690160.

### [inborn error of metabolism](https://psychterms.org/terms/inborn-error-of-metabolism/)

Field: biological.

An inborn error of metabolism is a disorder present from birth in which a genetic change disrupts a normal metabolic process, often because an enzyme is faulty or unstable. In the example described here, cystathionine beta-synthase deficiency causes homocysteine to build up and can be associated with learning and behavioral problems.

- [metabolism](https://psychterms.org/terms/metabolism/): `mention`.
- [homocystinuria](https://psychterms.org/terms/homocystinuria/): `embedding`; cosine 0.809603.
- [porphyria](https://psychterms.org/terms/porphyria/): `embedding`; cosine 0.752578.
- [biochemical defect](https://psychterms.org/terms/biochemical-defect/): `embedding`; cosine 0.748598.
- [inherited disorder](https://psychterms.org/terms/inherited-disorder/): `embedding`; cosine 0.733433.

### [estrogen antagonist](https://psychterms.org/terms/estrogen-antagonist/)

Field: biological.

An estrogen antagonist is a substance that opposes or blocks the effects of estrogen. In this study context, it was used to test whether estrogen was one of the diffusible signals influencing brain development.

- [estrogen](https://psychterms.org/terms/estrogen/): `mention`.
- [serotonin antagonist](https://psychterms.org/terms/serotonin-antagonist/): `embedding`; cosine 0.756728.
- [dopamine-receptor antagonist](https://psychterms.org/terms/dopamine-receptor-antagonist/): `embedding`; cosine 0.742113.
- [pharmacological antagonism](https://psychterms.org/terms/pharmacological-antagonism/): `embedding`; cosine 0.739433.
- [GABA antagonist](https://psychterms.org/terms/gaba-antagonist/): `embedding`; cosine 0.728561.

### [unique trait](https://psychterms.org/terms/unique-trait/)

Field: biological.

A unique trait is a characteristic that distinguishes one organism or strain from related ones because it has not been observed in the others. In this source, it refers to the ability of a diatom strain to both grow and accumulate large amounts of lipids at the same time.

- [strain](https://psychterms.org/terms/strain/): `mention`.
- [polygenic trait](https://psychterms.org/terms/polygenic-trait/): `embedding`; cosine 0.762117.
- [warning coloration](https://psychterms.org/terms/warning-coloration/): `embedding`; cosine 0.695699.

### [Symmetrel](https://psychterms.org/terms/symmetrel/)

Field: biological.

Symmetrel is a brand name for amantadine hydrochloride, a drug with antiviral and antiparkinsonian effects. In brain-related use, it is described as affecting dopamine activity and also having some influence on NMDA- and acetylcholine-related signaling.

- [amantadine](https://psychterms.org/terms/amantadine/): `mention`.
- [NMDA](https://psychterms.org/terms/nmda/): `mention`.
- [Cylert](https://psychterms.org/terms/cylert/): `embedding`; cosine 0.718344.
- [Anafranil](https://psychterms.org/terms/anafranil/): `embedding`; cosine 0.716557.
- [armodafinil](https://psychterms.org/terms/armodafinil/): `embedding`; cosine 0.712110.

### [average](https://psychterms.org/terms/average/)

Field: research methods.

Average usually means the arithmetic mean, found by combining values and dividing by how many there are. More broadly, it can refer to any measure that represents the center of a set of values.

- [mean](https://psychterms.org/terms/mean/): `embedding`; cosine 0.903818.
- [median](https://psychterms.org/terms/median/): `embedding`; cosine 0.787562.
- [mean difference](https://psychterms.org/terms/mean-difference/): `embedding`; cosine 0.781786.
- [harmonic mean](https://psychterms.org/terms/harmonic-mean/): `embedding`; cosine 0.764888.
- [standard deviation](https://psychterms.org/terms/standard-deviation/): `embedding`; cosine 0.752109.

### [history effect](https://psychterms.org/terms/history-effect/)

Field: research methods.

A history effect is a type of confounding in which changes that happen over time, rather than the variable being studied, account for the observed results. In other words, the passage of time introduces another influence that can make findings misleading.

- [period effect](https://psychterms.org/terms/period-effect/): `embedding`; cosine 0.764050.
- [main effect](https://psychterms.org/terms/main-effect/): `embedding`; cosine 0.713475.
- [longitudinal](https://psychterms.org/terms/longitudinal/): `embedding`; cosine 0.706276.
- [general effect](https://psychterms.org/terms/general-effect/): `embedding`; cosine 0.705024.
- [confounded effects](https://psychterms.org/terms/confounded-effects/): `embedding`; cosine 0.704856.

### [CPI](https://psychterms.org/terms/cpi/)

Field: research methods.

CPI stands for Consumer Price Index, also called the cost-of-living index. It is a financial statistic used to track how the prices of a representative set of goods change over time.

- [consumer](https://psychterms.org/terms/consumer/): `mention`.
- [statistics](https://psychterms.org/terms/statistics/): `mention`.

### [concept hierarchy](https://psychterms.org/terms/concept-hierarchy/)

Field: learning.

A concept hierarchy is an arrangement of related ideas into different levels of detail or granularity. In this kind of structure, each level captures distinct but complementary information, and understanding can be improved by linking information across levels.

- [hierarchy](https://psychterms.org/terms/hierarchy/): `mention`.
- [task structure](https://psychterms.org/terms/task-structure/): `embedding`; cosine 0.730724.
- [deep structure](https://psychterms.org/terms/deep-structure/): `embedding`; cosine 0.716313.

### [CAR](https://psychterms.org/terms/car/)

Field: biological.

CAR usually refers to chimeric antigen receptor T-cell therapy, a cancer treatment in which a person’s own T cells are genetically modified to recognize and attack cancer cells. It is used especially for some blood cancers when standard treatments have not worked, though it can cause serious immune-related and neurological side effects.

- [T cell](https://psychterms.org/terms/t-cell/): `mention`.
- [armoring](https://psychterms.org/terms/armoring/): `embedding`; cosine 0.767814.
- [cell-mediated immunity](https://psychterms.org/terms/cell-mediated-immunity/): `embedding`; cosine 0.706604.
- [cytokine](https://psychterms.org/terms/cytokine/): `embedding`; cosine 0.706142.
- [biological therapy](https://psychterms.org/terms/biological-therapy/): `embedding`; cosine 0.704963.

### [Gesellschaft](https://psychterms.org/terms/gesellschaft/)

Field: history.

In this historical source, Gesellschaft is the German term used for an association in the sense of an organized group formed to advance a shared aim or carry out a common purpose. It is contrasted with a mere aggregation of people.

- [aggregation](https://psychterms.org/terms/aggregation/): `mention`.
- [Gemeinschaft](https://psychterms.org/terms/gemeinschaft/): `embedding`; cosine 0.770473.
- [social organism](https://psychterms.org/terms/social-organism/): `embedding`; cosine 0.766320.
- [group](https://psychterms.org/terms/group/): `embedding`; cosine 0.734732.
- [organization](https://psychterms.org/terms/organization/): `embedding`; cosine 0.722144.

