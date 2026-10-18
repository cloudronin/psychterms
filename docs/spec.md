# PsychTerms, the open psychology dictionary: project spec v0.2

18 Oct 2026. A standalone project.

**v0.2 (same day, after the implementation-plan review).** The supplied 26,286-entry markdown was found to be a paraphrase of the APA dictionary, scrubbed for overlap; it is derivative and is not released (kill criterion one). The dictionary is rebuilt from permitted sources. Vishnu's standing instruction: this gets done right, however long it takes and whatever it costs; no count target, no date; the quality bar is two judges per entry. The implementation plan (`PROJECT-PLAN.md`, 18 Oct) is the engineering reference; where it and this spec differ, this spec is corrected to match. It feeds Plainword Prep's Reference screen but does not depend on it, and ships on its own.

## 1. What it is, and why

A free, open dictionary of psychology and counselling terms, as broad as the permitted sources support (the APA's scale, about 25,000, is the ambition, not a target), in our own words, under CC BY 4.0, on its own website, with the source file in a public repo. Students, trainees, lay helpers and anyone else can read it, cite it, copy it and build on it without copyright worries.

Why: as far as we have found, no open dictionary of the field exists (checked before it goes in launch copy). The APA's is copyrighted. Textbook glossaries live inside textbooks. Prep companies keep theirs behind paywalls. Nobody with the definitions had a reason to give them away. We have the definitions, a reason that is not money, and a pipeline that checks them.

Name, domain and repo (Vishnu, 18 Oct): **PsychTerms**, one word, at **psychterms.org** and `cloudronin/psychterms`: the site, the citation line, the name on the page; `.org` because it is a free public resource. One domain only; no `.io`, no redirect domains. A trademark knockout on "PsychTerms" runs before launch copy.

## 2. What ships

| Piece | Form |
|---|---|
| The dictionary | one JSON file and one markdown file, 25,000 entries, versioned and hashed |
| The website | a static site, one page per term, search in the browser, on its own domain |
| The repo | the source files, the licence, the build, the checks, the scan report, a contribution guide |
| The release note | what it is, where the definitions came from, what was checked, what it is not |

Plainword Prep takes the dictionary as a versioned dependency: each release is a hashed JSON file; the app's knowledge-base bundle pins one release and shows its version beside the knowledge base version in Account's "On this Mac"; Reference entries link to the site's term URLs for that release. The app never fetches from the site at runtime; moving the pin is a bundle release.

## 3. The entry

```
{
  "id": "reflection-of-meaning",
  "term": "reflection of meaning",
  "definition": "A reply that names what the thing matters for ...",
  "also_see": ["reflection-of-feeling", "reflection-of-content", "values"],
  "field": "counselling skills",
  "aliases": ["meaning reflection"],
  "sources": ["mesh:D012998", "wikidata:Q1234"],
  "provenance": [{"role": "draft_basis", "source": "mesh:D012998", "revision": "2026", "scope": "definition"},
                 {"role": "supports_definition", "source": "samhsa:...", "revision": "2023", "scope": "definition"}],
  "vignette": {"text": "...", "notice": "...", "card_id": "p_...", "card_hash": "sha256:...", "builder_commit": "..."},
  "checks": {"readers": "2/2", "copy": "clear"},
  "version": 1,
  "hash": "7f3a9c..."
}
```

Entries without a vignette omit the `vignette` key. A risk term's page shows "No scene is provided for this risk term." and nothing more. The site design (the PsychTerms canvas, 18 Oct) is the reference for every page; a vignette shown on the site must come from an unbound ArcSim card, never from a Prep scenario.

- `definition`: one to three sentences, plain words, no criteria lists, no treatment advice, no diagnosis of anyone.
- `field`: a short tag from a fixed list (counselling skills, assessment, diagnosis, ethics, development, cognition, social, biological, research methods, history, and so on).
- `sources` and `provenance`: where the definition came from and what each source did (`draft_basis`, `supports_definition`, `related_topic`), with a pinned revision. A related-topic link never counts as support. Never a copyrighted dictionary. No entry is ever labelled as a writer's original work unless a real writer wrote it.
- Entries that match a Plainword exam-layer entry carry an `exam_layer_id`. The exam layer itself is not in the open file.

## 4. Where the text comes from

- **The definitions** are drafted by the teacher model from permitted source packets only, one packet per term, and judged against those packets. The old markdown is never shown to the drafting model and never used as a term list.
- **The term list** is built independently from MeSH, Wikidata and the other permitted lists, not from the inherited headwords.
- **The source inventory** (work package B): one row per candidate with the licence confirmed from the source's own page, a pinned version, its role, and yes or no. Licences are verified at the source, never assumed.

| Group | Candidates | Licence | Status |
|---|---|---|---|
| US government | NIMH, SAMHSA, NIH and HHS glossaries, MedlinePlus (most), the VA National Center for PTSD, CDC, NCI Thesaurus, MeSH | public domain (NLM credited, no implied endorsement) | to verify per source |
| ERIC Thesaurus (US Dept of Education) | ~11,000 descriptors with scope notes; counselling, school counselling, testing | public domain | to verify |
| UK and Commonwealth government | NHS and NICE glossaries (Open Government Licence v3); Australian government health glossaries (CC BY) | OGL v3 and CC BY, both CC BY-compatible | to verify |
| EU bodies | EU publications under the reuse policy | CC BY 4.0 | to verify |
| Public-domain historical texts | Baldwin's Dictionary of Philosophy and Psychology (1901), early James, Titchener, the York classics archive | pre-1929 | drafting basis for historical terms; wording dated, never copied |
| CC BY open textbooks | BCcampus and Lumen psychology texts that are CC BY | CC BY, checked per book and edition | to verify each |
| CC BY journals | PLOS, Frontiers, BMC | CC BY | research-method terms |
| Structured | Wikidata | CC0 | term list, aliases, links |

- **Out, with the reason:** the APA Dictionary and any published dictionary (copyright); Noba and OpenStax Psychology 2e (CC BY-NC-SA); Wikipedia and Wiktionary text (CC BY-SA; Wikipedia URLs may be kept as background references only); ICD-11 and WHO materials (ND); UMLS and SNOMED (own licences); DSM text; prep-site text.

## 4a. Vignettes: the term in a room (Vishnu, 18 Oct)

Beside the definition, where a person could be in the room, a short written case that shows the term: a client line, a moment, a choice. 100 to 150 words. Fiction, no identifiable person, drafted from the entry's definition and an ArcSim character card only.

| Layer | What | Where | Which terms |
|---|---|---|---|
| The vignette | the term shown in a scene, with one line saying what to notice | psychterms.org, CC BY, beside the definition, in the open file | terms a person could meet in a room: skills, presentations, defences, ethics, development, assessment moments. Not research methods, anatomy or statistics. Perhaps a third of the dictionary |
| The playable case | a Prep scenario built from the same card: persona, the term planted, a journey step, a debrief that cites the term | Plainword Prep, closed, through the scenario library and B3's field pass | the subset where the term is a judgment to practise, not only to recognise |

- **One pipeline, two outputs.** The ArcSim card schema (with the 18 Oct fields) plus a planted term plus the intake builder yields the vignette; the same card plus the journey builder yields the case. The term's `field` and type decide which output it earns.
- **Checks:** two judges per vignette (does the scene show the term; does it stay clear of advice, criteria lists and identifiable people), the overlap scan, the same provenance record naming the card id. Same CC BY release.
- **Risk terms carry no vignette (v1), by a rule in code, not a writer's call.** An entry is a risk term when any of these hold: (1) its field is diagnosis or assessment and its packet or anchor carries suicide, self-harm, non-suicidal self-injury, homicide, harm to others, violence, abuse (child, elder, intimate partner), neglect, overdose, lethal means or firearm; (2) it names a risk-assessment instrument, a safety-planning practice, or a duty (duty to warn, duty to protect, mandated reporting, involuntary hold, welfare check); (3) ArcSim's card schema excludes it by its no-risk-history rule. Mechanics: `risk_terms.json` in the repo, pinned and hashed per release; the build sets `risk: true` from it; a term can be added to the list by pull request, and the flag is never removed from an entry by hand. The page shows "No scene is provided for this risk term." and a build check fails any pull request that adds a scene to a flagged entry. Strict is the only safe error: a wrong flag costs a scene; a missing one shows a method.
- **The site never links to a planted answer.** A vignette shows the term; the playable case hides what it plants. The exam-layer "Try it" link stays as it is.
- **Order:** definitions ship first; vignettes are a second release so the first is not held by the harder half. The pilot includes 50 vignettes and reports their per-item cost beside the definitions'.

## 5. The pipeline

| Step | What | Tool |
|---|---|---|
| 1. Parse and dedupe | read the markdown, one entry per term, merge exact and near duplicates | `overlap_scan.py` reports entry-to-entry duplicate windows |
| 2. Draft | the teacher model writes one to three sentences per term from its source packet only | frozen prompt, pinned sources |
| 3. Two judges | two separate models read each definition against its packet; a unit passes only if both say yes. Each rejects anything unsupported by the packet, invented names or instruments, treatment advice, criteria lists, identifiable cases, more than three sentences; redraft once, then drop with the reason recorded | the same two-judge pattern as the exam layer; cost set by the pilot |
| 3a. Copy check | verbatim runs of 15 or more words against the frozen comparison set; a hit is a redraft; five-word runs are triage, not gates | `overlap_scan.py`, unchanged; definition-only input; exit 1 on any hit |
| 4. Anchor | match terms to MeSH and Wikidata ids where they exist; record in `sources` and `provenance`; unknown anchors stay unmatched | script |
| 5. Link | build `also_see` from Wikidata relations and the writer's cross-references; mark exam-layer matches | script |
| 6. Build | JSON and markdown, hashed; the site from the JSON | static site generator |
| 7. Release | repo public, site live, release note, scan report attached | |

Cost: a 200-term stratified pilot first under a $20 PREREG, with receipts for drafting, judging and retries. The full line is set from the pilot's real per-entry number and sized to finish, not to fit a figure chosen beforehand. The old $150 figure is withdrawn. PREREG before every paid line; the runner reserves each call's maximum cost before dispatch; stop before the cap. Vishnu's instruction: done right, whatever it costs.

What the pipeline does not do: the supervisor read that the Prep exam layer uses. Corrections arrive as pull requests and run the same checks.

## 6. The website

- Static (Astro, Pagefind for browser search indexing term, aliases and first sentence only). No server, no database, no accounts, no analytics that leave the browser. Configurable base URL, so GitHub Pages works before any domain is bought.
- One page per term: the term, the definition, "also see" links, the field tag, the CC BY line with a copy-ready citation, "edit this entry" pointing at the repo file, and the entry version and hash.
- Search in the browser over a small index (term, aliases, first sentence).
- An A to Z index and a per-field index.
- psychterms.org, not under plainword.health, so it reads as a public resource. One footer line: "built by Plainword, free forever."
- Free static hosting (GitHub Pages or Cloudflare Pages). A merge to main rebuilds the site.
- Each page is a stable URL the Prep app links to.
- Read-aloud is a Prep app feature, not a site feature, in v1.

## 7. Licence and attribution

- CC BY 4.0 for the data; MIT for the code. Anyone may use, copy, adapt and redistribute with credit. Not CC BY-SA: share-alike binds adaptations to the same licence, which would keep programs and prep companies from folding entries into their own material. Not CC0: attribution is the one thing that keeps a corrupted copy from being mistaken for ours.
- The attribution line on every page and in the release note: "PsychTerms (psychterms.org), by Plainword, CC BY 4.0, version N."
- Third-party pieces carry their own notices in `NOTICE.md`: MeSH and other US government sources (public domain, credited, no implied endorsement), OGL sources (credited), Wikidata (CC0, credited), each CC BY text by name and edition.

## 8. Corrections and contributions

- Pull requests to the repo, one entry per PR preferred.
- The automated check and the copy check run on every PR.
- A maintainer merges; a merge rebuilds the site and bumps the entry version.
- No forum, no moderation queue, no accounts on the site.
- Contributors are credited in the repo, never paid, never rewarded for ratings or reviews.

## 9. What it is not

- Not a treatment guide, not medical advice; a line on every page says so.
- Not the Prep exam layer; those entries stay closed and are not in the file.
- Not a chatbot; it never answers questions, only defines terms.
- Not a place to describe a real person: no clinical narrative or question input anywhere. The term search box is local to the browser. Biographies are excluded; historical eponyms and scientific attribution are allowed; identifiable personal cases are not.

## 10. Tests before release

- Every entry parses; every `also_see` target exists; no duplicate ids.
- Copy check: zero runs of 15 or more words against the saved reference set; the scan report is in the repo.
- Automated check: pass rate reported; dropped entries listed by term, not hidden.
- No entry contains a treatment dose, a diagnostic criteria list, or an identifiable personal case.
- Every released definition has a permitted drafting basis and two judge passes recorded; a related-topic link never counts as support.
- Exact normalized duplicates flagged; near duplicates reviewed, never merged on a similarity score alone; homonyms kept separate.
- Two builds from identical inputs produce identical hashes; Markdown and JSON agree.
- The public export contains no restricted reference text, secrets, prompt caches, old prose, or local paths.
- No banned product words in the site's own copy.
- The site builds from a clean checkout and every term page resolves.
- The Prep app's Reference entries resolve to live site URLs.

## 11. Order of work (the plan's work packages A to G)

1. A, B and the site scaffold start now, no paid call: parser fixtures from the old file (private), schema, deterministic ids, the source inventory with licences verified, field taxonomy, site pages on fixtures.
2. C and E: the editorial runner with per-call reservation and receipts; checks, exports, parity tests.
3. PREREG and the 200-term pilot ($20): real per-entry cost for drafting, two judges and retries; coverage report from the permitted sources.
4. Vishnu sets the full line from the pilot number.
5. F: the full run; drops and unmatched anchors reported, never hidden.
6. G: release rehearsal; the 200-entry held-out read by Vishnu from the frozen corpus with a recorded seed; fixes; rerun affected checks.
7. Release: repo public, site live on GitHub Pages, release note stating what was checked and what was not.
8. Prep pins a release and its Reference screen points at the live URLs when the exam-layer mapping exists.

## 12. Kill and stop criteria

- Fired 18 Oct: the supplied file is derivative of a copyrighted dictionary; not released; rebuilt from permitted sources.
- More than 10% of drafted entries carry a run of 15 or more words against the frozen comparison set (definition-only denominator): stop; review the source packets and prompt before continuing.
- More than 20% of entries dropped after one redraft: stop; review the packets and the judge rubric before continuing.
- The permitted sources support far fewer terms than hoped: report the number and release that number. Never pad.

## 13. With Vishnu

- Confirm the record of origin for the old file (a paraphrase of the APA dictionary by a session) so the repo's history is honest.
- The full cost line after the pilot.
- The banned product-word list for the site's own copy.
- The repo slug (`cloudronin/psychterms` proposed) and GitHub access.
- The trademark knockout on the name before launch copy.
- The 200-entry held-out read before release.

## 14. Rules carried

CC BY 4.0 data, MIT code, never share-alike. Never a copyrighted dictionary's text, paraphrased or otherwise. No PHI, no identifiable person anywhere. No banned product words. PREREG before every paid line; each line stops before its cap; no untrusted PR runs with a paid key. Nothing to main without Vishnu. Done right, however long it takes.

## Direct decisions retained

No count target applies. Term-to-card fit is required, with unmatched reasons recorded. Generated scenes and notice lines require their own overlap scan and two judges. Public product mentions remain footer-only; that direct decision governs the conflicting publisher wording in section 7.

## Latest copy and publisher-domain decision

AI is allowed in PsychTerms, Prep and site copy; it remains banned in Session and Desk. Scribe, listen, always on and cloud remain banned everywhere in product copy. The Plainword site moves to plainword.ai and the PsychTerms footer links there; PsychTerms itself retains psychterms.org.

## Latest user decisions: definition publication and judging

Definitions ship without waiting for vignettes. Publish model-passed definitions with citations as a live review preview; Vishnu reviews after publication. One designated cheap model judge, separate from the drafting model and the assistant, is sufficient: gpt-5.4-mini-2026-03-17. This supersedes the earlier two-judge and human-read-before-preview requirements. Existing model-verdict receipts are reused without paid reruns. The 15-word copy check continues; five-word wording concerns are displayed for human review rather than hidden. Any approved source may provide a citation when its pinned record or passage supports the term. Continue expanding independently sourced terms; the legacy corpus remains excluded. Paid work still requires a registered budget line and cap.

## Latest priority: complete source coverage first

Privately audit all 26,286 supplied headwords against permitted sources before more drafting. Use the headwords only; no old definition text enters a source query or drafting model, and the inherited headword list remains private. Record specific source candidates, source roles, pinned snapshots, semantic-review status and unresolved gaps for every row. Source records and background anchors are distinguished. The production term inventory remains independently sourced.

## Latest direct decision: candidates before judging

Publish newly drafted, cited definitions with review_status candidate and the label “Candidate · not yet reviewed”. Judge review follows publication and may promote an entry or leave the status unchanged. No passing verdict is inferred. Definitions use admitted source packets only; inherited prose is never model input or public content. Source discovery and packet preparation continue for candidates that currently have only background anchors. The old pilot is not reopened; new paid drafting still requires its own registered cap.
