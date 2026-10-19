# PsychTerms: see-also report

Review required before merge. Definitions, entry files, hashes and reader verdicts are unchanged.

| Measure | Count |
|---|---:|
| Entries eligible | 9,324 |
| Entries with 0 links | 110 |
| Entries with 1–2 links | 931 |
| Entries with 3–4 links | 1,306 |
| Entries with 5 links | 6,977 |
| Links: mention | 11,587 |
| Links: same_source | 0 |
| Links: embedding | 29,457 |
| Headword targets appearing in more than 40 definitions | 286 |
| Mention pairs rejected by document frequency | 37,286 |
| Embedding proposals rejected by field filter | 106,097 |
| Unique inbound risk pairs blocked | 1,575 |

## Kept embedding cosine distribution

| Min | p25 | Median | p75 | Max |
|---:|---:|---:|---:|---:|
| 0.601087 | 0.714359 | 0.747208 | 0.787065 | 0.991275 |

## Reproduction and interpretation

- Model: `BAAI/bge-small-en-v1.5`; revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`.
- Weights SHA-256: `3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad`.
- Entry-set hash: `29ac69411f05d3899a6557f815f4b60f565e23b0a87a1e289e8e08476d736a1f`.
- Input hash (retagged entries, risk, redirects, stop list, parameters): `d9d459c7894362a4277ee21313e44c08326e3a0656980d55c0cf4650235b4df2`.
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

### [family dynamics](https://psychterms.org/terms/family-dynamics/)

Field: social.

Family dynamics are the patterns within a family that shape how family members influence a child’s emotional and social experiences. In this context, they strongly affect children’s sense of belonging, emotion regulation, and how socially connected they feel in virtual interactions such as mobile gaming.

- [emotion regulation](https://psychterms.org/terms/emotion-regulation/): `mention`.
- [belonging](https://psychterms.org/terms/belonging/): `mention`.
- [social dynamics](https://psychterms.org/terms/social-dynamics/): `embedding`; cosine 0.797313.
- [family](https://psychterms.org/terms/family/): `embedding`; cosine 0.789817.
- [group dynamics](https://psychterms.org/terms/group-dynamics/): `embedding`; cosine 0.789646.

### [mu](https://psychterms.org/terms/mu/)

Field: cognition.

Mu is an EEG sensorimotor rhythm made up of two nonharmonic oscillatory components in the alpha and beta frequency ranges. In psychology and cognitive research, it is used as a neural marker of sensorimotor integration during speech perception and comprehension.

- [sensorimotor rhythm](https://psychterms.org/terms/sensorimotor-rhythm/): `mention`.
- [Speech Perception](https://psychterms.org/terms/speech-perception/): `mention`.
- [alpha wave](https://psychterms.org/terms/alpha-wave/): `embedding`; cosine 0.755503.
- [beta wave](https://psychterms.org/terms/beta-wave/): `embedding`; cosine 0.728356.
- [cognitive electrophysiology](https://psychterms.org/terms/cognitive-electrophysiology/): `embedding`; cosine 0.727918.

### [biomarker](https://psychterms.org/terms/biomarker/)

Field: diagnosis.

A biomarker is a measurable biological sign, such as a level of a substance or another quantifiable body-related feature, that is used to help assess health or physiological states. It can be used in areas such as estimating disease risk, identifying psychiatric disorders, tracking environmental exposure and its effects, and supporting diagnosis or research.

- [psychiatric disorder](https://psychterms.org/terms/psychiatric-disorder/): `mention`.
- [circulating levels](https://psychterms.org/terms/circulating-levels/): `embedding`; cosine 0.738168.
- [blood levels](https://psychterms.org/terms/blood-levels/): `embedding`; cosine 0.725286.
- [PChE](https://psychterms.org/terms/pche/): `embedding`; cosine 0.713053.

### [scotopic](https://psychterms.org/terms/scotopic/)

Field: biological.

Scotopic refers to vision under very low light, such as in darkness or nighttime conditions. It relies on the eye’s rod cells, which are especially light-sensitive and respond most strongly to wavelengths around 507 nm toward the blue part of the spectrum.

- [blues](https://psychterms.org/terms/blues/): `mention`.
- [scotopic vision](https://psychterms.org/terms/scotopic-vision/): `embedding`; cosine 0.966121.
- [photopic vision](https://psychterms.org/terms/photopic-vision/): `embedding`; cosine 0.838711.
- [photopic](https://psychterms.org/terms/photopic/): `embedding`; cosine 0.837289.
- [twilight vision](https://psychterms.org/terms/twilight-vision/): `embedding`; cosine 0.824356.

### [stereotypic movement disorder](https://psychterms.org/terms/stereotypic-movement-disorder/)

Field: diagnosis.

Stereotypic movement disorder is a condition marked by repetitive, seemingly driven movements that have no clear function. These behaviors significantly disrupt normal activity or can lead to serious self-inflicted injury, and are not explained by a substance or a general medical condition.

- [movement disorder](https://psychterms.org/terms/movement-disorder/): `mention`.
- [disruptive behavior disorder](https://psychterms.org/terms/disruptive-behavior-disorder/): `embedding`; cosine 0.739428.
- [disorganized behavior](https://psychterms.org/terms/disorganized-behavior/): `embedding`; cosine 0.738180.
- [somatic symptom disorder](https://psychterms.org/terms/somatic-symptom-disorder-v2-a843562809/): `embedding`; cosine 0.736985.
- [Tourette’s disorder](https://psychterms.org/terms/tourettes-disorder/): `embedding`; cosine 0.736492.

### [unconscious](https://psychterms.org/terms/unconscious/)

Field: cognition.

Unconscious refers to a state of awareness in which a person is consistently unresponsive to stimuli.

- [unconscious perception](https://psychterms.org/terms/unconscious-perception/): `embedding`; cosine 0.835359.
- [unconscious cognition](https://psychterms.org/terms/unconscious-cognition/): `embedding`; cosine 0.822573.
- [conscious](https://psychterms.org/terms/conscious/): `embedding`; cosine 0.810833.
- [unconscious process](https://psychterms.org/terms/unconscious-process/): `embedding`; cosine 0.799810.
- [consciousness](https://psychterms.org/terms/consciousness/): `embedding`; cosine 0.789366.

### [congenital character](https://psychterms.org/terms/congenital-character/)

Field: history.

A congenital character is a trait or property an organism has from the start, as part of its original endowment. In this historical usage, it is contrasted with acquired characters, though the source notes that in actual development most traits reflect both innate qualities and environmental influence.

- [congenital](https://psychterms.org/terms/congenital/): `mention`.
- [ontogeny](https://psychterms.org/terms/ontogeny/): `embedding`; cosine 0.745462.
- [characteristic](https://psychterms.org/terms/characteristic/): `embedding`; cosine 0.705515.
- [epigenesis](https://psychterms.org/terms/epigenesis/): `embedding`; cosine 0.700301.
- [connate](https://psychterms.org/terms/connate/): `embedding`; cosine 0.697069.

### [gender nonconformity](https://psychterms.org/terms/gender-nonconformity/)

Field: social.

Gender nonconformity refers to gender expression that differs from what society expects or accepts. In this packet, it is discussed as a difference that can expose people to stigma, bullying, discrimination, and related mental health strain.

- [nonconformity](https://psychterms.org/terms/nonconformity/): `mention`.
- [Bullying](https://psychterms.org/terms/bullying/): `mention`.
- [nonnormative](https://psychterms.org/terms/nonnormative/): `embedding`; cosine 0.768940.
- [gender stereotype](https://psychterms.org/terms/gender-stereotype/): `embedding`; cosine 0.764346.
- [transsexualism](https://psychterms.org/terms/transsexualism/): `embedding`; cosine 0.747247.

### [behavior observation](https://psychterms.org/terms/behavior-observation/)

Field: learning.

Behavior observation is the use of many different formal or informal methods to record and describe behavior.

- [behavior record](https://psychterms.org/terms/behavior-record/): `embedding`; cosine 0.845950.
- [behavior sampling](https://psychterms.org/terms/behavior-sampling/): `embedding`; cosine 0.835748.
- [behavior](https://psychterms.org/terms/behavior/): `embedding`; cosine 0.772090.
- [Coaching Behavior Assessment System](https://psychterms.org/terms/coaching-behavior-assessment-system/): `embedding`; cosine 0.767986.
- [rule-governed behavior](https://psychterms.org/terms/rule-governed-behavior/): `embedding`; cosine 0.743349.

### [intoxication](https://psychterms.org/terms/intoxication/)

Field: history.

Intoxication is the condition produced by drugs or poisons, often used more narrowly for drunkenness from alcohol. It usually appears soon after the substance is taken in and can involve noticeable changes in mind and behavior, such as excitement, lowered restraint, disorganized speech or conduct, and other less obvious disturbances that vary with the substance.

- [disorganized speech](https://psychterms.org/terms/disorganized-speech/): `mention`.
- [excitement](https://psychterms.org/terms/excitement/): `mention`.
- [acute alcoholism](https://psychterms.org/terms/acute-alcoholism/): `embedding`; cosine 0.766066.
- [sobriety](https://psychterms.org/terms/sobriety/): `embedding`; cosine 0.749388.

### [imago](https://psychterms.org/terms/imago/)

Field: history.

In historical usage, imago means the fully developed adult or winged stage of an insect that undergoes complete metamorphosis. This is the stage in which the sexual organs are mature.

- [metamorphosis](https://psychterms.org/terms/metamorphosis/): `mention`.
- [heteromorphosis](https://psychterms.org/terms/heteromorphosis/): `embedding`; cosine 0.701948.
- [infancy](https://psychterms.org/terms/infancy/): `embedding`; cosine 0.658443.
- [ontogeny](https://psychterms.org/terms/ontogeny/): `embedding`; cosine 0.655886.
- [cleavage](https://psychterms.org/terms/cleavage/): `embedding`; cosine 0.651659.

### [equity theory](https://psychterms.org/terms/equity-theory/)

Field: cognition.

Equity theory is the idea that people judge an exchange as fair when what each person puts in and gets out are in proportion. It treats perceived input–outcome balance as a main basis for deciding whether a situation is just or unjust.

- [regret theory](https://psychterms.org/terms/regret-theory/): `embedding`; cosine 0.722468.
- [probability theory](https://psychterms.org/terms/probability-theory/): `embedding`; cosine 0.717271.
- [appraisal theory](https://psychterms.org/terms/appraisal-theory/): `embedding`; cosine 0.704757.

### [trophic](https://psychterms.org/terms/trophic/)

Field: biological.

In this biological context, trophic refers to the support and maintenance a nerve cell of origin provides to its axon and terminal branches. If that connection is destroyed or interrupted, the nerve fibers can lose function and undergo trophic degeneration.

- [degeneration](https://psychterms.org/terms/degeneration/): `mention`.
- [transection](https://psychterms.org/terms/transection/): `embedding`; cosine 0.756011.
- [fragmentation](https://psychterms.org/terms/fragmentation/): `embedding`; cosine 0.731380.
- [tropism](https://psychterms.org/terms/tropism/): `embedding`; cosine 0.727600.
- [retrograde degeneration](https://psychterms.org/terms/retrograde-degeneration/): `embedding`; cosine 0.722650.

### [subliminal stimulation](https://psychterms.org/terms/subliminal-stimulation/)

Field: cognition.

Subliminal stimulation is stimulation presented at a level too weak to produce a distinct, differentiated response.

- [subliminal](https://psychterms.org/terms/subliminal/): `mention`.
- [subliminal perception](https://psychterms.org/terms/subliminal-perception/): `embedding`; cosine 0.798376.
- [dichoptic stimulation](https://psychterms.org/terms/dichoptic-stimulation/): `embedding`; cosine 0.746281.
- [stimulus strength](https://psychterms.org/terms/stimulus-strength/): `embedding`; cosine 0.697885.

### [autoshaping](https://psychterms.org/terms/autoshaping/)

Field: learning.

Autoshaping is a Pavlovian/instrumental learning procedure in which an organism acquires a new operant response around a conditioned stimulus linked to a reward. It involves forming a conditioned stimulus–unconditioned stimulus association and the transfer of incentive value from the reward to that cue.

- [instrumental learning](https://psychterms.org/terms/instrumental-learning/): `mention`.
- [operant response](https://psychterms.org/terms/operant-response/): `mention`.
- [automaintenance](https://psychterms.org/terms/automaintenance/): `embedding`; cosine 0.786650.
- [instrumental conditioning](https://psychterms.org/terms/instrumental-conditioning/): `embedding`; cosine 0.737228.
- [autonomic learning](https://psychterms.org/terms/autonomic-learning/): `embedding`; cosine 0.733187.

### [hepatic encephalopathy](https://psychterms.org/terms/hepatic-encephalopathy/)

Field: biological.

Hepatic encephalopathy is a syndrome of brain and central nervous system dysfunction linked to liver failure, including problems related to portal-systemic shunting. It can involve reduced alertness and confusion that may worsen to coma, along with abnormal movement and reflex signs.

- [encephalopathy](https://psychterms.org/terms/encephalopathy/): `mention`.
- [confusion](https://psychterms.org/terms/confusion/): `mention`.
- [portal-systemic encephalopathy](https://psychterms.org/terms/portal-systemic-encephalopathy/): `embedding`; cosine 0.919070.
- [cerebral dysfunction](https://psychterms.org/terms/cerebral-dysfunction/): `embedding`; cosine 0.762172.
- [traumatic encephalopathy](https://psychterms.org/terms/traumatic-encephalopathy/): `embedding`; cosine 0.740751.

### [corticofugal](https://psychterms.org/terms/corticofugal/)

Field: biological.

Corticofugal refers to nerve fibers that travel outward from the cerebral cortex to lower brain regions and the spinal cord. In this packet, they are described as large longitudinal bundles on each side of the ventral midbrain.

- [longitudinal](https://psychterms.org/terms/longitudinal/): `mention`.
- [midbrain](https://psychterms.org/terms/midbrain/): `mention`.
- [tract](https://psychterms.org/terms/tract/): `embedding`; cosine 0.790634.
- [lateral corticospinal tract](https://psychterms.org/terms/lateral-corticospinal-tract-v2-0455a4e2ac/): `embedding`; cosine 0.780548.
- [U fiber](https://psychterms.org/terms/u-fiber/): `embedding`; cosine 0.768709.

### [component evaluation](https://psychterms.org/terms/component-evaluation/)

Field: mental health.

In this source, component evaluation means assessing a program through several distinct parts rather than a single overall outcome. It looks separately at effects on individuals, effects on the surrounding community, how operating context shapes results, and the costs involved.

No see-also links.

### [cannabis dependence](https://psychterms.org/terms/cannabis-dependence/)

Field: mental health.

Cannabis dependence is a dependent pattern of cannabis use in which the severity of dependence can vary among users. In the source, it is discussed as a common problem linked with cannabis use frequency and with some motives for use, especially coping and routine motives.

- [cannabis](https://psychterms.org/terms/cannabis/): `mention`.
- [motive](https://psychterms.org/terms/motive/): `mention`.
- [substance dependence](https://psychterms.org/terms/substance-dependence/): `embedding`; cosine 0.826575.
- [drug addiction](https://psychterms.org/terms/drug-addiction/): `embedding`; cosine 0.781212.
- [polysubstance dependence](https://psychterms.org/terms/polysubstance-dependence/): `embedding`; cosine 0.751941.

### [generalizability theory](https://psychterms.org/terms/generalizability-theory/)

Field: learning.

Generalizability theory is a statistical approach to evaluating how reliable a measurement is in the behavioral sciences. It examines several possible sources of measurement error at the same time and estimates how much each testing condition or factor contributes to score variation across acceptable observations.

- [Behavioral Sciences](https://psychterms.org/terms/behavioral-sciences/): `mention`.
- [generalizability](https://psychterms.org/terms/generalizability/): `mention`.
- [stimulus generalization](https://psychterms.org/terms/stimulus-generalization/): `embedding`; cosine 0.728109.
- [generalized matching law](https://psychterms.org/terms/generalized-matching-law/): `embedding`; cosine 0.727129.
- [frequentist inference](https://psychterms.org/terms/frequentist-inference/): `embedding`; cosine 0.691223.

