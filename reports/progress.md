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
