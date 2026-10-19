# Current progress

The public repository is [cloudronin/psychterms](https://github.com/cloudronin/psychterms). The [GitHub Pages review preview](https://psychterms.org/) uses build-owned candidate, reviewed, judged and dropped statuses. See [the generated release note](release-note.md) for current counts. Reader models are named on About. Human review happens on the live preview; vignettes remain deferred. The publisher footer links to https://www.plainword.ai/.

Fresh definitions are drafted from individually permitted source packets and read independently by the fixed mini and nano readers. The current validated publication contains **7,612 entries: 5,515 judged and 2,097 reviewed**, with 1,200 total drops. Source recovery continues under the original $100 drafting and $25 reader caps. See source-recovery.json and independent-readers.json for this snapshot; the generated release note carries the build counts. Original definition prose and private audit rows are never exported or provided to models. Vignettes remain deferred.

The inventory includes article-specific CC BY decisions and NIMH-owned publication pages with pinned snapshots. A bibliographic lead alone is not an admitted source or a supported definition. No claim is made that unsuccessful searches establish the absence of other usable sources.

## Historical implementation records

The records below describe earlier milestones, not the current deployment or publication policy.

# PsychTerms: implementation status

A standalone local project on branch `cloudronin/bootstrap`. No remote repository, public deployment or DNS change has been made.

| Work | Evidence |
|---|---|
| Private parser fixture | All 26,286 entry blocks counted, no duplicate IDs. The audit emits aggregate counts only; no legacy headwords/text enter the project data or model packets. |
| Source inventory | 34 candidates, 16 scoped yes decisions and 18 no decisions. Unconfirmed sources stay excluded. |
| Independent vocabulary | Fresh MeSH 2026 download: 31,130 descriptors, 1,267 psychology-tree candidates with scope notes. Candidates are not accepted entries. |
| Packets | Three site-preview packets pinned to the new MeSH snapshot. Pilot packets are separately frozen in private storage. |
| Validation | 62 unit tests pass, including concurrent budget reservations, two distinct judges, stale-result rejection, packet tampering and legacy-fixture isolation. Three entry and 34 source records pass JSON Schema validation. |
| Site | Astro builds 11 pages. Three term pages indexed by Pagefind; only term/aliases/first sentence is in the marked index body. All generated internal links resolve with both root and GitHub project base paths. |
| Branding | PsychTerms, owned by Vishnu Vettrivel; psychterms.org is the sole configured domain. Custom-domain activation is false and there is no CNAME file. |
| Publication | No remote, no push, no site deployment; preview examples are not release-approved dictionary entries. |
| Pilot | Attempts complete: 195/200 definition machine passes, five drops and 12 wording holds. Of 50 scene candidates: seven fits, 38 unmatched, five risk exclusions; five scenes retained privately and two dropped after redraft. The 28.6% scene drop rate crosses the 20% stop. No full run. |

Browser access to the local preview was declined. Visual and interactive browser review has not been completed, and no alternate browser route was attempted.

The source inventory is an initial item-by-item review, not blanket permission for whole websites. Additional source-specific snapshots, Wikidata integration and field/coverage review remain. See source-inventory.md for the eligibility decisions and limitations.

The banned product-word list is still pending. The custom domain will not be activated until the site is ready to be seen. The pilot report is complete; no full-generation budget line has been set. Paid dispatch is disabled. See pilot-report.md for results, per-item receipts and the failed vignette gate.

## Latest site revision

PsychTerms naming is applied throughout current project copy; citation and breadcrumb domains are lowercase. The term-page presentation has scene, definition-only and risk states. Risk classification is hash-bound and exports the exact notice. Pilot scenes remain private; public scene import is not enabled. The original pinned builder bytes are unchanged. The supplied design URL was inaccessible following browser-origin denial, so visual comparison remains outstanding.

Validation: 65 Python tests and five site tests pass; three synthetic presentation states rendered in a private build under the GitHub Pages base path; normal build produces 11 pages with no broken internal links. All 3 entry records, 34 source records and 3 source packets validate. Frozen pilot dependencies remain reproducible at 797791e. No paid calls, publishing or DNS changes occurred.

## Section 4a risk register

Build-owned `risk: true` replaces the earlier presentation flag. The version-1 register contains 30 named category, duty and recorded ArcSim exclusion records, with an exact-byte SHA-256 pin. This is a seed inventory, not a claim of exhaustive risk-term coverage. Missing detected coverage blocks builds until a register PR; source entry flags and scenes on listed entries are rejected. CI preserves earlier register records/rules and requires version bumps. Exports carry both the register snapshot and pin. The page renders the risk badge, exact no-scene sentence and build-check note. No paid calls or release/deployment changes.

Verification: 81 Python tests and five site tests pass, including the three rule paths, manual flag edits, scene rejection, register deletion/weakening, pin tampering and secret-scan regression. Normal static build and schema/packet/link checks pass; the private three-state render test also passes.

## Copy policy and publisher domain

AI is permitted in Prep, PsychTerms and site copy; Session and Desk retain the ban. The four universal product-word bans remain. Product-specific regression tests and the built-site copy check pass. PsychTerms keeps psychterms.org; the footer publisher link now points to plainword.ai. Verification: 84 Python tests, five site tests, normal build and copy/link checks pass. No deployment or model calls occurred.

## Completed candidate drafting continuation

The source-ready queue is finished and the final publication contains 5,026 active entries (4,828 candidate, 198 reviewed), plus 24 recorded earlier scope drops. The build writes current counts in the release note. Three copy holds remain unpublished; insufficient source packets were declined rather than forced. See candidate-drafting.json for the $100 line receipts and held reservations. Historical drafting-stage counts above preceded the now-completed independent-reader run. See the build-written release note and independent-readers.json for current status and costs.

## Source recovery underway

Vishnu instructed recovery of usable permitted packets for the eligible remainder. Article-specific CC BY background passages are being retrieved and pinned, with authors retained and cases, quotations, tables, references and results sections excluded. The first recovered wave prepared 190 packets and drafted 165 definitions; both readers have now attempted each definition. Bibliographic discovery also covers terms previously represented only by anchors. Original $100 drafting and $25 reader ledgers retain all charges and reservations. See source-recovery.json for the current retrieval snapshot and release-note.md for published counts. No inherited definition prose or scenes are used.

Before source-recovery publication, an extraction check found long external quotations in 24 packets. The 22 affected unpublished entries were quarantined privately, including their packets and receipts; nothing from them is published. Extraction now rejects these paragraphs before drafting. The clean first wave adds 119 live entries, with all original charges retained.

## Further recovered definitions

The next completed waves bring the local validated preview to 5,471 active entries: 4,318 judged and 1,153 reviewed, with 521 total drops. Source retrieval and expanded bibliographic discovery continue. See recovery-coverage.json for aggregate dispositions of every private audit label; the private term list is not exported. Original CC BY licences are linked on term pages and beside drop reasons, and the contribution notice marks new wording.

## Recovery publication, batch 003

Eleven completed recovery waves bring the validated preview to 7,612 active entries. All 161 Python tests pass; the 7,612 term pages have no broken internal links and the product-copy check is clear. A whole-word excerpt-window regression was fixed before the next paid dispatch. Source retrieval and further drafting continue on the same ledgers.
