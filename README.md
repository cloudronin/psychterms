# PsychTerms

An independent dictionary of psychology and counselling, being rebuilt from verified permitted sources. There is no entry-count target or deadline. Each released entry must pass two distinct judge models against its pinned source packet.

**Status: development scaffold, not a dictionary release.** The three site examples are preview fixtures and have not passed the release review. The independent MeSH term inventory contains candidates, not approved entries. The legacy derivative corpus stays outside this repository and may be used only to audit the parser; it is never a term list or model input.

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

`npm run dev` provides the site scaffold. Pagefind search is produced by `npm run build` and works in the built preview. Set `BASE_PATH=/psychterms/` and `SITE_URL=https://cloudronin.github.io` for a GitHub project site. The public repository is https://github.com/cloudronin/psychterms. GitHub Pages builds the labelled development preview at https://cloudronin.github.io/psychterms/ from main. The custom domain is not activated.

## Contents

- [Spec v0.2](docs/spec.md) and [recorded decisions](docs/decisions.md).
- [Source inventory](reports/source-inventory.csv): a decision for every candidate; unconfirmed sources are excluded.
- [Independent term inventory report](reports/independent-term-inventory.json).
- [Completed pilot report](reports/pilot-report.md), [combined PREREG](docs/pilot-combined-preregistration.md), and [per-item receipt costs](reports/pilot-item-costs.csv).
- [ArcSim adapter baseline](docs/card-hash-proposal.md) and [term-to-card fit results](reports/vignette-fit.json).
- [Progress and verification](reports/progress.md).
- Name and owner: PsychTerms, Vishnu Vettrivel. Sole domain: psychterms.org. GitHub Pages first; custom-domain activation is disabled.

The offline build never dispatches paid calls. The registered pilot has completed its attempts: 195/200 definitions passed the machine checks; 12 still have wording holds. Of 50 scene candidates, seven matched a fixed card, 38 were unmatched and five were risk exclusions. Five scenes were retained privately; two failed the final audit after their allowed redraft, crossing the registered 20% stop. Both judges had passed those two scenes, so this configuration is not cleared for scale.

The usage-based pilot cost is $1.813129 plus $0.053720 still reserved for three original uncertain calls, within the same $20 cap. Paid dispatch is disabled, no full-run line exists, and nothing has been released. Python 3.15.0 was used for the registered pilot. PR checks have no paid key.

## Rights

Original code: MIT; the unmodified vendored ArcSim builder/schema retain Apache-2.0 and their notices. Eligible original dictionary contributions: CC BY 4.0. Third-party source materials retain their own notices and conditions; see [NOTICE.md](NOTICE.md). The source licence review does not imply endorsement by a source institution.
