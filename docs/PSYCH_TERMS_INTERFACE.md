# PsychTerms and ArcSim character cards: the interface

A standalone handoff for whoever builds PsychTerms vignettes and playable cases. It assumes no other context.
Status: agreed design, **not built**. 18 Oct 2026. Written by the ArcSim side; Vishnu carries it across.

## What this is about

- **PsychTerms** is an open psychology dictionary (psychterms.org, CC BY 4.0). Beside some definitions it will show a
  **vignette**: a short written scene (100 to 150 words) that shows the term in a room, with one line saying what to
  notice.
- **ArcSim** is our code that builds fictional therapy clients. Each client is a **character card**: a JSON object with
  who they are, their history, how they think and talk. Cards are built by code from fixed word lists (no model writes
  them), from a seed, so the same seed always gives the same card.
- **Plainword Prep** is our closed practice app for trainee counsellors. It can turn the same card into a **playable
  case**: a simulated client the trainee talks to, with something planted in the conversation to notice, and a
  debrief afterwards.
- **One pipeline, two outputs:** a card plus a "planted term" gives a vignette (open, on the dictionary site) and, for
  some terms, a playable case (closed, in Prep). Terms a reader only needs to recognise get a vignette; terms that are
  a judgment to practise can also get a case.

## Where the code is

- Repository `cloudronin/uofa-lab`, branch `arcsim`, folder `arcsim/` (Apache 2.0).
- The card builder: `arcsim/arcsim/persona/cognitive.py`, function `build(seed)` (sha256 `31088a31425b31a2de29a8e8ed5ee4f656822983fbf6b07bc44f9dd38415453e`).
- The card schema: `arcsim/arcsim/schemas/persona.schema.json`, version 0.3 (sha256 `5d1d5782f20fad84e113658ca5f703bd9a312ca0c8fea10bd4bb08bd47c86829`).
- Sexuality and ethnicity for a whole library of cards: `assign_intake_only(cards, strata)` in the same file.
- The intake builder (the exam-style briefing a trainee reads first): `arcsim/arcsim/journey/intake.py`.
- The journey builder (a client across sessions): `arcsim/arcsim/journey/build.py`.

## 1. The card: every field and its type (schema v0.3)

| Field | Type | What it holds |
| --- | --- | --- |
| `persona_id` | string | `p_<seed>`; a card bound to a Prep scenario is renamed `scenario:<id>` |
| `seed` | string or integer | the seed it was built from |
| `presenting_problem` | string | one of anxiety, self-esteem, relationships, career, other |
| `talking_style` | string | one of plain, upset, verbose, reserved, tangent, pleasing |
| `profile.name` | string | a first name from a fixed fictional list |
| `profile.age` | integer | 19 to 72 |
| `profile.gender` | string | female, male or non-binary |
| `profile.occupation` | string | a job phrase from a fixed list, fitted to the age |
| `profile.living_situation` | string | a home phrase from a fixed list, fitted to the age |
| `profile.details` | array of strings | two health facts from a fixed list |
| `profile.relationship_status` | string | single, in a relationship, married, separated, divorced, widowed |
| `profile.family` | array of objects | each: `relation` (string), `name` (string), `alive` (boolean), `where` (string), optional `note` (string) |
| `profile.setting` | string | where the client is seen (for example community mental health centre) |
| `profile.counselling_type` | string | individual, couples, family or group (these cards: individual) |
| `profile.mental_status` | array of strings | eight observation lines: appearance, behaviour, speech, mood, affect, thought process, orientation, insight |
| `cognitive_model.relevant_history` | string | one sentence of history |
| `cognitive_model.core_beliefs` | array of strings | helpless, unlovable, worthless |
| `cognitive_model.intermediate_beliefs` | string | one rule the client lives by |
| `cognitive_model.coping_strategies` | string | two coping habits |
| `cognitive_model.situation` | string | what brings them in now |
| `cognitive_model.automatic_thoughts` | string | two thoughts that come up |
| `cognitive_model.emotions` | array of strings | three feelings |
| `cognitive_model.behaviors` | string | their manner in a session |
| `intake_only.sexuality` | string | heterosexual, gay or lesbian, bisexual, not stated: **never for a vignette** |
| `intake_only.ethnicity` | string | a neutral intake-form category, or not stated: **never for a vignette** |

The card is checked to not contradict itself: no medicine beside "takes no regular medication"; a stay-at-home parent
lives with their children; no work-based problem for someone with no job; no partner in the coping lines of someone
with no partner; family that matches the home and the story (a father who died is not alive); no two people sharing a
first name. The cognitive-model fields follow the Patient-Psi structure (Wang et al. 2024); every phrase is ours.

## 2. Fields a vignette may use, and fields it may not

| May use | May not use |
| --- | --- |
| name, age, gender, occupation, living situation, relationship status, family, health details, setting, type of counselling | **`intake_only` (sexuality, ethnicity), in any form** |
| situation, relevant history, emotions, automatic thoughts, intermediate and core beliefs, coping, manner, talking style | anything from a Prep scenario a card is bound to (`persona_id` "scenario:..."): its planted facts, labels, hidden answers, session notes. Do not use bound cards at all |
| the eight mental-status lines (for assessment terms, for example "flat affect") | any risk history (self-harm, suicidal thoughts, a weapon at home, harm to others): cards have none, and none is to be added from a scenario |
| | anything identifiable: no real person, place or organisation |
| | any text not produced by `build()` at a pinned commit (no hand-written card, no session transcript, no outside dataset) |

A helper, `vignette_view(card)`, is proposed: it returns exactly the left column plus the card id, the builder commit
and a hash of the card, for the vignette's provenance record. Not built yet.

## 3. The planted term: what the dictionary adds

The term is **not written into the card**. Cards stay term-free and reusable. Each vignette is one request:

```json
{"term_id": "pt:...", "headword": "...", "field": "...", "type": "...",
 "show": "client_line | moment | choice",
 "notice_line": "one line saying what to notice",
 "card_id": "p_...", "card_hash": "sha256:...", "builder_commit": "..."}
```

- `show` says how the scene shows the term: something the client says, a moment between client and helper, or a choice
  the helper faces.
- The dictionary writes the scene from the term's definition and the card's allowed fields only.
- The vignette's provenance record keeps the request, so anyone can rebuild the card from the open code and check it.

## 4. The licence boundary

Vignettes are released under CC BY 4.0. So every card string a vignette draws on must be ours to release, by rule:

- Card text comes only from the word lists in `cognitive.py` (names, jobs, homes, health, the problem lists, history,
  manner, settings, mental-status phrases). They were written for ArcSim. Patient-Psi supplied the structure only, no
  wording.
- That text is ours and published under Apache 2.0, so using it inside a CC BY vignette is ours to allow.
- **Only cards built by `build()` at a pinned commit qualify.** A card with any hand-written or imported string does not.
- No ArcSim card holds text from any other source: no session transcripts, no research datasets, no lexicons.
- **RealCBT is used only as numbers.** The builder draws a card's presenting problem with RealCBT's published problem mix
  as five weights (anxiety 33, self-esteem 25, relationships 18, career 9, other 15; `PROBLEMS` in `cognitive.py`). No
  RealCBT wording is in any bank.
- **The test that proves no outside wording is in card text:** `arcsim/arcsim/experiments/bank_overlap.py` and
  `arcsim/tests/test_bank_overlap.py`. They build 5,000 cards, take every field a vignette may use, split it into runs of
  6 words (case and punctuation ignored), and look for each run in the private text pools on the machine where they are
  kept. Result on 18 Oct 2026: **1,209 distinct runs, 0 found** in HOPE (596 transcripts, 4.9 million words, which
  include the 41 RealCBT sessions that are also HOPE videos), AnnoMI (678,000 words) and the pipeline's therapy pool
  (493,000 words). CACTUS text and the full rebuilt RealCBT set have never been on that machine (they live only in
  private cloud storage, by rule). The NRC lexicon is a list of single words with scores; no bank holds any of it.
- Before the check, one card line (the thought "Something terrible is going to happen.") also appeared once in a HOPE
  transcript. It is a stock phrase, but cards now say "Something awful is about to happen." instead.

## 5. From a vignette to a playable case

For terms that are a judgment to practise:

1. Take the same card and the planted term. A new Prep scenario binds the card as `scenario:<id>`.
2. The journey builder makes a two-session journey for that client. The term becomes the scenario's planted moment: the
   segment of the session where it lands, how it surfaces, what the client does if the trainee misses or catches it,
   and what counts as catching it.
3. Prep's scenario library runs its **field pass** on it, which adds:
   - the modality it fits (or "student's choice");
   - the population it suits;
   - the client's stated goals;
   - a label: "required" only for safety and ethics, otherwise "favoured";
   - where relevant, a diagnostic picture (the differential, the deciding facts, what to assess, when to refer);
   - tags for the exam domains.
4. The intake builder writes the briefing the trainee reads before session one. It adds sexuality and ethnicity from
   `intake_only` as two intake-form lines. **Those two lines are never sent to the simulated client and never shown to
   the checking judges.**
5. The debrief cites the term's dictionary entry. The case hides what it plants. The vignette only shows the term.
   **The dictionary site never links to a case's planted answer.**

## 6. Scope

Both outputs train helpers. A vignette is a written third-person scene for learners: no advice to the reader, no chat,
no crisis conversation. Any feature that would have either output talk to a person in distress, rather than train the
helper, is removed (Plainword's standing rule).

## Example card

Built by `build("example-4")` with the builder at commit `12bd2828` (branch `arcsim`); `intake_only` added by
`assign_intake_only`. It is shown only to mark where that field sits: a vignette must not use it.

```json
{
 "persona_id": "p_example-4",
 "seed": "example-4",
 "presenting_problem": "self-esteem",
 "talking_style": "upset",
 "profile": {
  "name": "Nate",
  "age": 67,
  "gender": "male",
  "occupation": "is retired after thirty years in sales",
  "living_situation": "lives alone in a flat",
  "details": [
   "drinks two or three coffees a day",
   "has asthma and uses an inhaler"
  ],
  "relationship_status": "single",
  "family": [
   {
    "relation": "mother",
    "name": "Rosa",
    "alive": false,
    "where": "died"
   },
   {
    "relation": "father",
    "name": "Victor",
    "alive": false,
    "where": "died"
   },
   {
    "relation": "younger brother",
    "name": "Colin",
    "alive": true,
    "where": "lives two hours away"
   }
  ],
  "setting": "community mental health centre",
  "counselling_type": "individual",
  "mental_status": [
   "Appearance: neatly dressed",
   "Behaviour: tearful at times, fidgets with their hands",
   "Speech: halting at times",
   "Mood: describes feeling embarrassed and sad",
   "Affect: congruent with the mood they describe",
   "Thought process: logical, returns to what upsets them",
   "Orientation: oriented to person, place and time",
   "Insight: fair"
  ]
 },
 "cognitive_model": {
  "relevant_history": "Was close to a grandparent who died when they were a teenager.",
  "core_beliefs": [
   "worthless"
  ],
  "intermediate_beliefs": "If people saw the real me, they'd leave.",
  "coping_strategies": "Stays quiet in groups; puts themself down before others can.",
  "situation": "Turned down an invitation because they felt they had nothing to say.",
  "automatic_thoughts": "I'm a failure. They only put up with me.",
  "emotions": [
   "embarrassed",
   "sad",
   "flat"
  ],
  "behaviors": "Gets tearful when the main worry comes up. Is visibly distressed: speaks in bursts, sometimes trails off or comes back to what hurts."
 },
 "intake_only": {
  "sexuality": "heterosexual",
  "ethnicity": "White"
 }
}
```

## Not built

This is the interface only. Building it needs the dictionary's term list and its own registration on the dictionary
side.
