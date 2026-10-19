# PsychTerms: see-also report

Review required before merge. Definitions, entry files, hashes and reader verdicts are unchanged.

| Measure | Count |
|---|---:|
| Entries eligible | 9,201 |
| Entries with 0 links | 2 |
| Entries with 1–2 links | 80 |
| Entries with 3–4 links | 305 |
| Entries with 5 links | 8,814 |
| Links: mention | 38,699 |
| Links: same_source | 735 |
| Links: embedding | 5,882 |
| Embedding proposals rejected by field filter | 101,734 |
| Unique inbound risk pairs blocked | 1,586 |

## Kept embedding cosine distribution

| Min | p25 | Median | p75 | Max |
|---:|---:|---:|---:|---:|
| 0.605147 | 0.707228 | 0.738965 | 0.780981 | 0.982278 |

## Reproduction and interpretation

- Model: `BAAI/bge-small-en-v1.5`; revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
- Weights SHA-256: `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad`.
- Entry-set hash: `72991b96724b2deaa094d19cd79acd5e1dd9607eb134774b95d3eae3d84e439e`.
- Input hash (retagged entries, risk, redirects, stop list, parameters): `b8bf3fcf4cedb7ca13b651a8e24e7862989a88543dc2772bc72114f7c91e4854`.
- Parameters: cap 5; source cap 3; global nearest 20 excluding self; cosine ≥ 0.60; embedding links require identical fields.
- Sampling seed: `20261018`. Uniform sample without replacement from all eligible IDs, including zero-link and risk entries.
- Risk blocking is applied to all three signals after redirect resolution; risk entries may link out.
- Diagnostic counts audit all mention/source proposals and qualifying top-20 embedding proposals even when five slots are already full. Field rejection excludes already-linked and risk targets. Risk count deduplicates the same directed pair across signals.
- Local CPU inference only. Input is exactly `term: definition`, with normalized vectors and no retrieval prefix. No paid calls, no remote embedding service, no LLM-written links.
- Source identity is exact packet hash or exact provenance scope. It is a structural candidate signal, not an additional model judgment.
- Singular/plural matching uses English suffix rules and an explicit irregular-noun table; punctuation separates words. Equal-position mentions prefer the longer phrase, then headword and ID. Cosine ties use ID order.
- Entry `also_see` is hash-covered. Source entries and exported entry hashes remain untouched; the site reads the separate graph in signal order.

## Twenty random entries

### [feeling](https://psychterms.org/terms/feeling/)

Field: history.

In this historical psychology source, feeling is the aspect of consciousness concerned with experienced changes apart from identifying objects or directing action. It is used broadly as a phase of mental life within the traditional division of knowledge, feeling, and will, and is treated as an abstraction from a fuller state of mind.

- [psychology](https://psychterms.org/terms/psychology/): `mention`.
- [aspect](https://psychterms.org/terms/aspect/): `mention`.
- [consciousness](https://psychterms.org/terms/consciousness/): `mention`.
- [object](https://psychterms.org/terms/object/): `mention`.
- [action](https://psychterms.org/terms/action/): `mention`.

### [myelination](https://psychterms.org/terms/myelination/)

Field: cognition.

Myelination is the process in which oligodendrocyte precursor cells develop in ways that produce myelin, a covering that gives neurons structural and metabolic support and helps nerve signals travel efficiently along axons. When myelin is lost, neurons become more vulnerable and can undergo degeneration, contributing to lasting disability.

- [oligodendrocyte](https://psychterms.org/terms/oligodendrocyte/): `mention`.
- [precursor](https://psychterms.org/terms/precursor/): `mention`.
- [cell](https://psychterms.org/terms/cell/): `mention`.
- [myelin](https://psychterms.org/terms/myelin/): `mention`.
- [neuron](https://psychterms.org/terms/neuron/): `mention`.

### [bipolar](https://psychterms.org/terms/bipolar/)

Field: biological.

Bipolar disorder is a mental health condition that often begins during adolescence, a key period of brain development. In this context, it is described as having neurobiological features that are partly shared with, and partly distinct from, major depressive disorder.

- [bipolar disorder](https://psychterms.org/terms/bipolar-disorder/): `mention`.
- [mental health](https://psychterms.org/terms/mental-health/): `mention`.
- [health](https://psychterms.org/terms/health/): `mention`.
- [adolescence](https://psychterms.org/terms/adolescence/): `mention`.
- [period](https://psychterms.org/terms/period/): `mention`.

### [self-esteem](https://psychterms.org/terms/self-esteem/)

Field: learning.

Self-esteem is a person’s overall evaluation of themselves, including both positive and negative views of who they are. In psychology, it is treated as an important aspect of children’s physical and psychological development.

- [self](https://psychterms.org/terms/self/): `mention`.
- [evaluation](https://psychterms.org/terms/evaluation/): `mention`.
- [negative](https://psychterms.org/terms/negative/): `mention`.
- [psychology](https://psychterms.org/terms/psychology/): `mention`.
- [aspect](https://psychterms.org/terms/aspect/): `mention`.

### [substance use disorder](https://psychterms.org/terms/substance-use-disorder/)

Field: diagnosis.

Substance use disorder is a disorder related to the use of substances. In the supplied source, it is described as a major global health problem that contributes substantially to overall disease burden.

- [health](https://psychterms.org/terms/health/): `mention`.
- [disease](https://psychterms.org/terms/disease/): `mention`.
- [alcohol use disorder](https://psychterms.org/terms/alcohol-use-disorder/): `embedding`; cosine 0.870385.
- [tobacco use disorder](https://psychterms.org/terms/tobacco-use-disorder/): `embedding`; cosine 0.805581.
- [gambling disorder](https://psychterms.org/terms/gambling-disorder/): `embedding`; cosine 0.784819.

### [verbal abuse](https://psychterms.org/terms/verbal-abuse/)

Field: mental health.

Verbal abuse is harmful or aggressive speech directed at a person. In the packet, it refers to patient verbal abuse toward newly graduated nurses, which is often treated as part of the job but can unsettle emotions and influence how people interpret and cope with their work experiences.

- [speech](https://psychterms.org/terms/speech/): `mention`.
- [patient](https://psychterms.org/terms/patient/): `mention`.
- [emotion](https://psychterms.org/terms/emotion/): `mention`.
- [experience](https://psychterms.org/terms/experience/): `mention`.
- [workplace violence](https://psychterms.org/terms/workplace-violence/): `embedding`; cosine 0.781582.

### [consensus](https://psychterms.org/terms/consensus/)

Field: cognition.

Consensus is a shared view or general agreement within a group. It refers to the judgment accepted by most of the people involved.

- [agreement](https://psychterms.org/terms/agreement/): `mention`.
- [group](https://psychterms.org/terms/group/): `mention`.
- [judgment](https://psychterms.org/terms/judgment/): `mention`.
- [submission](https://psychterms.org/terms/submission/): `embedding`; cosine 0.706755.
- [principle of common fate](https://psychterms.org/terms/principle-of-common-fate/): `embedding`; cosine 0.704611.

### [-genic](https://psychterms.org/terms/genic/)

Field: history.

-genic is a suffix used in compounds in an active sense to mean producing, causing, or giving rise to something in its genesis or development.

- [compound](https://psychterms.org/terms/compound/): `mention`.
- [active](https://psychterms.org/terms/active/): `mention`.
- [mean](https://psychterms.org/terms/mean/): `mention`.
- [rise](https://psychterms.org/terms/rise/): `mention`.
- [development](https://psychterms.org/terms/development/): `mention`.

### [behavioral avoidance test](https://psychterms.org/terms/behavioral-avoidance-test/)

Field: assessment.

A behavioral avoidance test is a practical assessment in which a person is asked to face a situation they have been avoiding so their avoidance and actual performance can be observed. In this source, it refers to a post-treatment driving test in real traffic used to see whether patients could carry out previously feared driving tasks.

- [avoidance](https://psychterms.org/terms/avoidance/): `mention`.
- [assessment](https://psychterms.org/terms/assessment/): `mention`.
- [performance](https://psychterms.org/terms/performance/): `mention`.
- [treatment](https://psychterms.org/terms/treatment/): `mention`.
- [Real](https://psychterms.org/terms/real/): `mention`.

### [irregular](https://psychterms.org/terms/irregular/)

Field: cognition.

In this context, irregular means not happening on a steady or predictable schedule. It describes episodes that occur occasionally at uneven intervals.

- [mean](https://psychterms.org/terms/mean/): `mention`.
- [interval](https://psychterms.org/terms/interval/): `mention`.
- [gene](https://psychterms.org/terms/gene/): `same_source`.
- [massage](https://psychterms.org/terms/massage/): `same_source`.
- [misdiagnosis](https://psychterms.org/terms/misdiagnosis/): `same_source`.

### [inborn error of metabolism](https://psychterms.org/terms/inborn-error-of-metabolism/)

Field: biological.

An inborn error of metabolism is a disorder present from birth in which a genetic change disrupts a normal metabolic process, often because an enzyme is faulty or unstable. In the example described here, cystathionine beta-synthase deficiency causes homocysteine to build up and can be associated with learning and behavioral problems.

- [metabolism](https://psychterms.org/terms/metabolism/): `mention`.
- [genetics](https://psychterms.org/terms/genetics/): `mention`.
- [normal](https://psychterms.org/terms/normal/): `mention`.
- [cause](https://psychterms.org/terms/cause/): `mention`.
- [homocystinuria](https://psychterms.org/terms/homocystinuria/): `embedding`; cosine 0.809603.

### [estrogen antagonist](https://psychterms.org/terms/estrogen-antagonist/)

Field: biological.

An estrogen antagonist is a substance that opposes or blocks the effects of estrogen. In this study context, it was used to test whether estrogen was one of the diffusible signals influencing brain development.

- [estrogen](https://psychterms.org/terms/estrogen/): `mention`.
- [study](https://psychterms.org/terms/study/): `mention`.
- [signal](https://psychterms.org/terms/signal/): `mention`.
- [brain](https://psychterms.org/terms/brain/): `mention`.
- [development](https://psychterms.org/terms/development/): `mention`.

### [unique trait](https://psychterms.org/terms/unique-trait/)

Field: biological.

A unique trait is a characteristic that distinguishes one organism or strain from related ones because it has not been observed in the others. In this source, it refers to the ability of a diatom strain to both grow and accumulate large amounts of lipids at the same time.

- [characteristic](https://psychterms.org/terms/characteristic/): `mention`.
- [organism](https://psychterms.org/terms/organism/): `mention`.
- [strain](https://psychterms.org/terms/strain/): `mention`.
- [ability](https://psychterms.org/terms/ability/): `mention`.
- [polygenic trait](https://psychterms.org/terms/polygenic-trait/): `embedding`; cosine 0.762117.

### [Symmetrel](https://psychterms.org/terms/symmetrel/)

Field: biological.

Symmetrel is a brand name for amantadine hydrochloride, a drug with antiviral and antiparkinsonian effects. In brain-related use, it is described as affecting dopamine activity and also having some influence on NMDA- and acetylcholine-related signaling.

- [amantadine](https://psychterms.org/terms/amantadine/): `mention`.
- [drug](https://psychterms.org/terms/drug/): `mention`.
- [brain](https://psychterms.org/terms/brain/): `mention`.
- [dopamine](https://psychterms.org/terms/dopamine/): `mention`.
- [NMDA](https://psychterms.org/terms/nmda/): `mention`.

### [average](https://psychterms.org/terms/average/)

Field: research methods.

Average usually means the arithmetic mean, found by combining values and dividing by how many there are. More broadly, it can refer to any measure that represents the center of a set of values.

- [mean](https://psychterms.org/terms/mean/): `mention`.
- [center](https://psychterms.org/terms/center/): `mention`.
- [median](https://psychterms.org/terms/median/): `embedding`; cosine 0.787562.
- [mean difference](https://psychterms.org/terms/mean-difference/): `embedding`; cosine 0.781786.
- [harmonic mean](https://psychterms.org/terms/harmonic-mean/): `embedding`; cosine 0.764888.

### [history effect](https://psychterms.org/terms/history-effect/)

Field: research methods.

A history effect is a type of confounding in which changes that happen over time, rather than the variable being studied, account for the observed results. In other words, the passage of time introduces another influence that can make findings misleading.

- [variable](https://psychterms.org/terms/variable/): `mention`.
- [period effect](https://psychterms.org/terms/period-effect/): `embedding`; cosine 0.764050.
- [main effect](https://psychterms.org/terms/main-effect/): `embedding`; cosine 0.713475.
- [longitudinal](https://psychterms.org/terms/longitudinal/): `embedding`; cosine 0.706276.
- [general effect](https://psychterms.org/terms/general-effect/): `embedding`; cosine 0.705024.

### [CPI](https://psychterms.org/terms/cpi/)

Field: research methods.

CPI stands for Consumer Price Index, also called the cost-of-living index. It is a financial statistic used to track how the prices of a representative set of goods change over time.

- [consumer](https://psychterms.org/terms/consumer/): `mention`.
- [statistics](https://psychterms.org/terms/statistics/): `mention`.

### [concept hierarchy](https://psychterms.org/terms/concept-hierarchy/)

Field: learning.

A concept hierarchy is an arrangement of related ideas into different levels of detail or granularity. In this kind of structure, each level captures distinct but complementary information, and understanding can be improved by linking information across levels.

- [hierarchy](https://psychterms.org/terms/hierarchy/): `mention`.
- [idea](https://psychterms.org/terms/idea/): `mention`.
- [level](https://psychterms.org/terms/level/): `mention`.
- [understanding](https://psychterms.org/terms/understanding/): `mention`.
- [task structure](https://psychterms.org/terms/task-structure/): `embedding`; cosine 0.730724.

### [CAR](https://psychterms.org/terms/car/)

Field: biological.

CAR usually refers to chimeric antigen receptor T-cell therapy, a cancer treatment in which a person’s own T cells are genetically modified to recognize and attack cancer cells. It is used especially for some blood cancers when standard treatments have not worked, though it can cause serious immune-related and neurological side effects.

- [receptor](https://psychterms.org/terms/receptor/): `mention`.
- [T cell](https://psychterms.org/terms/t-cell/): `mention`.
- [cell](https://psychterms.org/terms/cell/): `mention`.
- [treatment](https://psychterms.org/terms/treatment/): `mention`.
- [cause](https://psychterms.org/terms/cause/): `mention`.

### [Gesellschaft](https://psychterms.org/terms/gesellschaft/)

Field: history.

In this historical source, Gesellschaft is the German term used for an association in the sense of an organized group formed to advance a shared aim or carry out a common purpose. It is contrasted with a mere aggregation of people.

- [association](https://psychterms.org/terms/association/): `mention`.
- [group](https://psychterms.org/terms/group/): `mention`.
- [aggregation](https://psychterms.org/terms/aggregation/): `mention`.
- [Gemeinschaft](https://psychterms.org/terms/gemeinschaft/): `embedding`; cosine 0.770473.
- [social organism](https://psychterms.org/terms/social-organism/): `embedding`; cosine 0.766320.

