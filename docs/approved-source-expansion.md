# Three-source expansion, 19 October 2026

Vishnu permitted exactly these added source families for mental health, development, substance use and behavioural phenotype headwords. Other OpenMD-listed sources are not admitted by this change. Previously approved source inventory rows are preserved.

| Source family | Admitted use | Pin and licence evidence |
|---|---|---|
| MedlinePlus, US NLM | Own English health-topic full summaries only; drafting and supporting references | XML snapshot 2026-10-17, per-packet SHA-256, NLM own-text public-domain policy |
| CDC | Own unmarked mental-health, developmental and substance-use prose; drafting and supporting references | HTML snapshots 2026-10-19, per-page SHA-256, CDC agency-materials policy |
| Human Phenotype Ontology Consortium | Scoped labels, EXACT aliases, links and related references | HPO 2026-09-01, original OBO SHA-256 `93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22`; original licence text retained byte-for-byte |

MedlinePlus does not grant blanket reuse of everything hosted on its site. The importer extracts only `full-summary` and NLM topic metadata. Licensed encyclopedia text, drug monographs, images and linked external prose are excluded. The attribution identifies MedlinePlus and the National Library of Medicine. [NLM policy](https://medlineplus.gov/about/using/usingcontent/)

CDC materials can include protected third-party works. The scoped importer excludes marked material, images, tables, direct quotations and external source text. Citations carry attribution, the non-endorsement disclaimer and a statement that the original is available free from CDC. Independent wording must preserve substantive meaning. [CDC policy](https://www.cdc.gov/other/agencymaterials.html)

HPO is not labelled CC BY or public domain. Its published terms require acknowledgement/citation, version display, unchanged HPO files and unchanged logical relationships. The original licence text is in [hpo-licence-original.md](../data/source-licences/hpo-licence-original.md), with its hash recorded in `data/sources.json`. The current official repository links to an unavailable JAX licence URL; the original project's published licence page and markdown are retained as the actual evidence. The importer preserves the full original release file privately and builds only a scoped lookup view under the verified mental-function and neurodevelopment roots. It does not change the HPO file, add HPO prose to drafting packets, or relabel the licence. [Published HPO licence](https://human-phenotype-ontology.github.io/license.html)

## Retrieved coverage

- 71 NLM-owned topic summaries and 49 admitted CDC URL snapshots (43 distinct passages; six redirect aliases) were recovered, without paid calls.
- 616 HPO reference records are in the mental-function/neurodevelopment view; no HPO drafting records were admitted.
- On the fixed 500-item pilot, new government records yield 37 top-two packets for 24 headwords, plus seven HPO reference matches.
- Across the existing 2,600 redraft headwords, the same records yield 295 packets for 189 headwords, plus 22 HPO reference matches. These are retrieval candidates, not reader passes or new entries.

## Reproduction and integration

```sh
.venv/bin/python scripts/recover_approved_sources.py
.private/also-see-venv/bin/python scripts/prepare_reference_packets.py
.private/also-see-venv/bin/python scripts/prepare_reference_packets.py --all
```

The recovery command writes admitted government records in the existing `.private/source-recovery/records/` format. The ordinary re-source corpus loader already reads them. The dedicated packet preparer also uses the scoped HPO aliases as retrieval hints, keeps at most five government candidates and ranks the top two with the pinned bge-small model. It never adds headwords from HPO to the pool. HPO-related citations retain the original record ID, release, link and acknowledgement.

The active development rerun pins the expanded source inventory and tries the added packets as a distinct third phase after the original-packet comparison and unused-packet rescue. Existing entries, source packets and their original rejection reasons are unchanged.

Redirect aliases are deduplicated by source-text content before they can consume candidate slots. This full-pool preparation fix followed the frozen pilot replay; the pilot report still refers to its original 37 packets and records its executable revision separately.
