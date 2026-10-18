# PsychTerms

An independent dictionary of psychology and counselling, rebuilt from verified permitted sources. There is no entry-count target or deadline. Fresh, cited definitions publish as candidates before reader review. The build sets four forward-only statuses: candidate, reviewed (one passing reader other than the drafter), judged (two), and dropped (with a reason). The 15-word copy check must be clear for active entries. Released is a separate numbered-release marker.

**Status: public review preview.** Current build counts and reader models are recorded in [the generated release note](reports/release-note.md). Candidates carry an explicit plain-language badge. Dropped entries have no term page or searchable definition; their names and reasons remain on the Dropped page. Vignettes are deferred. The inherited prose and raw source audit remain private; old definitions are never a source or drafting input.

## Local preview

Requirements: Python 3.11+ and Node 22.22+ (Node 24 recommended).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check_schemas.py
npm ci --ignore-scripts
python3 -m unittest discover -s tests -v
npm run build
python3 scripts/check_site.py
npm run preview
```

`npm run dev` provides the site scaffold. Pagefind search is produced by `npm run build` and works in the built preview. The default site origin is `https://psychterms.org` and `BASE_PATH=/`. Both remain configurable for other hosting. The public repository is https://github.com/cloudronin/psychterms; GitHub Pages deploys the public review preview at https://psychterms.org/ from main.

## Contents

- [Spec v0.2](docs/spec.md) and [recorded decisions](docs/decisions.md).
- [Source inventory](reports/source-inventory.csv): a decision for every candidate; unconfirmed sources are excluded.
- [Independent term inventory report](reports/independent-term-inventory.json).
- [Completed pilot report](reports/pilot-report.md), [combined PREREG](docs/pilot-combined-preregistration.md), and [per-item receipt costs](reports/pilot-item-costs.csv).
- [ArcSim adapter baseline](docs/card-hash-proposal.md) and [term-to-card fit results](reports/vignette-fit.json).
- [Progress and verification](reports/progress.md).
- Name and owner: PsychTerms, Vishnu Vettrivel. Sole domain: psychterms.org. GitHub Pages hosts the review preview at https://psychterms.org/ with the site rooted at `/`.

The offline build never dispatches paid calls. The registered pilot has completed its attempts: 195/200 definitions passed the machine checks; 12 still have wording holds. Of 50 scene candidates, seven matched a fixed card, 38 were unmatched and five were risk exclusions. Five scenes were retained privately; two failed the final audit after their allowed redraft, crossing the registered 20% stop. Both judges had passed those two scenes, so this configuration is not cleared for scale.

The usage-based pilot cost is $1.813129 plus $0.053720 still reserved for three original uncertain calls, within the same $20 cap. Paid dispatch is disabled, no full-run line exists, and nothing has been released. Python 3.15.0 was used for the registered pilot. PR checks have no paid key.

## Rights

Original code: MIT; the unmodified vendored ArcSim builder/schema retain Apache-2.0 and their notices. Eligible original dictionary contributions: CC BY 4.0. Third-party source materials retain their own notices and conditions; see [NOTICE.md](NOTICE.md). The source licence review does not imply endorsement by a source institution.

## Candidate drafting

`python3 scripts/prepare_candidate_packets.py` prepares a private source-text queue. `python3 scripts/run_candidate_drafts.py` verifies the proposed registration without paid calls. Execution remains disabled until Vishnu sets the new line’s cap; see [candidate drafting registration](docs/candidate-drafting-preregistration.md). The 15-word copy scan and source/receipt bindings continue to apply even when judge review is deferred.
