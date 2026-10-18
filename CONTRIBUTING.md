# Contributing

Use one entry per pull request where practical. Edit data/entries/<stable-id>.json.
Keep IDs stable. Field tags must come from data/fields.json. Do not invent sources,
external anchors or exam-layer IDs. A related-topic link never counts as support.

Each released definition needs a permitted, pinned drafting packet and two passes
from distinct judge models, both tied to the exact definition and packet hashes.
A content edit invalidates earlier judge results. Judges do not see each other's
verdicts. One editorial redraft is permitted; unresolved failures are recorded
as drops. Do not add biographies, identifiable cases, treatment instructions,
doses or diagnostic criteria lists. Eponyms and scientific attribution are allowed.

Offline PR checks never receive paid keys. A maintainer authorizes any paid
editorial work under a preregistered budget line. Nothing is merged to main
without Vishnu. Near duplicates require contextual review; similarity alone
never authorizes a merge.

Risk classification is build-owned. Add terms to `data/risk_terms.json` by pull request, with the applicable section 4a test and reason. Keep earlier records and risk rules; increment the register version and update `data/risk-terms-pin.json` to its exact file SHA-256. Never set, clear or delete an entry's risk flag by hand. The build derives `risk: true` from register membership (including names and anchor IDs), and rejects scenes on listed entries. An entry whose packet/anchor triggers the diagnosis/assessment check, whose name identifies a risk duty/practice, or whose packet identifies a risk instrument or ArcSim exclusion must be registered before it builds. Instrument and ArcSim exclusions require editorial coverage in the register; text matching alone does not establish exhaustive coverage. Every release includes the exact register snapshot and its version/hash in the manifest. Run `python3 scripts/risk_registry.py --base <base-commit>` for the same additive-register check as CI.
