# Wave-two editorial decisions and field tagging

Claude verdicts: **74 PASS, 7 FAIL and 36 retags**. Scope exclusions: dry eyes, graph theory, Henle fiber, shape and superposition. They are removed from the active candidate pool and persisted in the headword exclusion registry. The two narrowing failures keep their original source packets for this retry; old failed definitions and earlier verdicts are unchanged.

Same-packet corrections passing both fresh readers and the 15-word scan: **1/2**. No definitions were published and wave three did not start.

Field guide: all 14 fields have one-line definitions. The tagger gets source packets and labels, not inherited tags or Claude's answers. On the 74 Claude-passed entries it matches **37/74** fields; **22** abstentions and **4** unverifiable responses. This is an inspected development comparison, not held-out accuracy. Claude's 36 retags remain authoritative in the staged decisions; classifier output does not overwrite them.

Receipted correction and taxonomy-check usage: **$0.165552**, within the same original $200 ledger.

## Field comparison

| Term | Claude field | Tagger field | Confident |
|---|---|---|---|
| adoption | development | development | True |
| age effect | research methods | research methods | True |
| agglutinative language | cognition | cognition | True |
| anorthopia | history | None | False |
| asphyxia | biological | None | False |
| baseline | research methods | research methods | True |
| block randomization | research methods | research methods | True |
| cell death | biological | None | False |
| cellular automata | research methods | unverified | unverified |
| central tendency | research methods | research methods | True |
| cerebral palsy | biological | diagnosis | True |
| collaboration | social | social | True |
| common factor | counselling skills | social | True |
| complementary and alternative medicine | mental health | unverified | unverified |
| construct validity | research methods | research methods | True |
| control processes | cognition | cognition | True |
| critical period | development | development | True |
| deafferentation | biological | None | False |
| diastolic blood pressure | biological | unverified | unverified |
| differential association | social | social | True |
| disability rating scale | assessment | assessment | True |
| dispersion | research methods | research methods | True |
| distraction | cognition | cognition | True |
| ehr | research methods | None | False |
| electronic health record | research methods | None | False |
| exhaustive search | cognition | cognition | True |
| expertise | cognition | cognition | True |
| exponential distribution | research methods | research methods | True |
| fight-or-flight response | biological | emotion and motivation | True |
| gender similarities hypothesis | social | social | True |
| hypnotherapy | counselling skills | counselling skills | True |
| imprinting | learning | learning | True |
| institutional animal care and use committee | ethics | None | False |
| job rotation | social | learning | True |
| lbw | development | None | False |
| mass media | social | None | False |
| muscarine | biological | None | False |
| nociceptor | biological | None | False |
| nomothetic | research methods | research methods | True |
| otolith | biological | None | False |
| pairwise comparison | research methods | research methods | True |
| parental leave | social | None | False |
| parental rejection | development | social | True |
| perceptual–motor coordination | cognition | cognition | True |
| perimetry | biological | assessment | True |
| prediction | research methods | research methods | True |
| predictive value | assessment | assessment | True |
| prenatal care | development | unverified | unverified |
| presupposition | cognition | cognition | True |
| primary process | history | history | True |
| razadyne | biological | None | False |
| recombination | biological | None | False |
| reminder | cognition | cognition | True |
| self-focus | cognition | cognition | True |
| semantic fluency | cognition | assessment | True |
| simple regression | research methods | research methods | True |
| single-case design | research methods | research methods | True |
| skin conductance | biological | None | False |
| spatial frequency | cognition | cognition | True |
| species recognition | biological | social | True |
| spinal canal | biological | None | False |
| steroid hormone | biological | None | False |
| stress-induced analgesia | biological | emotion and motivation | True |
| suprachiasmatic nucleus | biological | None | False |
| symptom cluster | mental health | mental health | True |
| tonal language | learning | cognition | True |
| toxicology | biological | None | False |
| transsynaptic degeneration | biological | biological | True |
| type identity theory | cognition | history | True |
| underload | cognition | cognition | True |
| up-regulation | biological | None | False |
| visual persistence | cognition | cognition | True |
| vocal cords | biological | None | False |
| zone of proximal development | development | development | True |

## Correction outcomes

| Term | Result | Reason |
|---|---|---|
| preparatory response | editorial PASS; staged judged | Two verified passing reads; general-sense concern resolved by supplied verdict. |
| redundancy | editorial FAIL; redraft | Silent narrowing; new general-sense packet required. Zero verified passing reads. |

## Interpretation and execution history

The tagger made 48 confident assignments: 37 match Claude and 11 disagree. Another 22 abstained and four responses were unverifiable. It therefore does not supply an automatic authoritative field for every entry. The staged 36 Claude retags are not overwritten; unresolved or uncertain future classifications require field review. No uncertain fallback was used in this comparison.

Version 1 is retained separately with its exact executed code, receipts and registration. Its overbroad evidence-format validation rejected 73/74 field responses, so its apparent 0/74 agreement is not a valid measurement. Version 2 limits the context-evidence requirement to the intended uncertain fallback contract. Total receipted usage for both executions is $0.381159; total shared redraft-line usage is $16.031413, with $0.820085 reserved, under the original $200 cap.

Preparatory response produced a fresh model-reviewed proposal. Redundancy produced a new draft but its first reader returned PASS without the required quoted support on both bounded attempts. That response was not counted as a read, and the second reader was not dispatched. Its unresolved status is not a verified reader FAIL. Both fresh texts and unchanged packets were exported for Claude.

The supplied follow-up verdict approves `preparatory-response-v3-aa974c0600`: “All clauses supported; general readiness before an expected event is the term's general sense, not one paper's”. This resolves the earlier editorial question. Across wave two there are now 75 editorial-approved headwords: 74 version-two proposals and this version-three correction. These remain staged, not newly published.

The supplied verdict rejects `redundancy-v3-dfd79156c9` for silently defining construct redundancy under the general headword. Its general-headword sourcing requirement is now “new general-sense packet required”; the rejected normalized source basis is excluded from packet preparation even if its ID or field changes. “Construct redundancy” is a separately named alternative requiring its own scope admission, entry and two verified reads. The external verdict cannot replace missing verified model reads.

Exact follow-up decisions and definition/packet hashes are recorded in `data/wave-two-correction-decisions.json`. Original version-two verdicts, executed metrics and provider receipts remain unchanged. No paid calls or wave-three run were made for this follow-up.
