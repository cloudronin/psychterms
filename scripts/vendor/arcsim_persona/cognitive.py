"""Build a persona card from a seed (persona schema v0.2), with no model in the loop.

The cognitive-model fields follow Patient-Ψ (Wang et al. 2024, arXiv 2405.19660): relevant history, core beliefs (the
helpless, unlovable and worthless families), intermediate beliefs, coping strategies, situation, automatic thoughts,
emotions, behaviours. Only the schema is used; every phrase below is written for ArcSim. Presenting problems follow
RealCBT's distribution (anxiety 33%, self-esteem 25%, relationships 18%, career 9%, other 15%). Six talking styles.
"""

from __future__ import annotations

import random
import re

STYLES = {
    "plain": "answers simply and directly, in short everyday sentences",
    "upset": "is visibly distressed: speaks in bursts, sometimes trails off or comes back to what hurts",
    "verbose": "talks at length, adds detail and background, sometimes has to be brought back",
    "reserved": "says little unless asked, gives short answers, opens up slowly",
    "tangent": "drifts to side stories and other worries, then finds the way back",
    "pleasing": "wants to be a good client: agrees quickly, plays problems down, apologises",
}
PROBLEMS = (("anxiety", 33), ("self-esteem", 25), ("relationships", 18), ("career", 9), ("other", 15))
NAMES = {"female": ["Maya", "Priya", "Grace", "Lucia", "Hannah", "Aisha", "Nora", "Elena", "Joy", "Ruth", "Mei", "Fatima",
                    "Claire", "Dana", "Imani", "Sofia", "Leah", "Rosa", "Anika", "Beth"],
         "male": ["Daniel", "Omar", "Marcus", "Theo", "Raj", "Samuel", "Luis", "Ben", "Kwame", "Owen", "Hiro", "Andre",
                  "Peter", "Tomas", "Elias", "Jamal", "Victor", "Nate", "Arjun", "Colin"],
         "non-binary": ["Alex", "Jordan", "Riley", "Sam", "Quinn", "Robin"]}
OCCUPATIONS = [  # (text, youngest, oldest)
    ("works as a nurse on night shifts", 23, 64), ("teaches at a primary school", 23, 64), ("works in a warehouse", 19, 62),
    ("is a software developer", 21, 60), ("manages a small cafe", 25, 66), ("drives for a delivery company", 21, 66),
    ("is a second-year university student", 19, 30), ("works in customer support", 19, 62), ("is an accountant", 24, 66),
    ("is a stay-at-home parent of two", 25, 50), ("works as a hairdresser", 19, 64),
    ("is retired after thirty years in sales", 58, 72), ("works in a call centre", 19, 62), ("is a junior lawyer", 25, 35),
    ("works as a carer for older adults", 19, 66), ("is between jobs after a layoff", 22, 64),
    ("runs a small cleaning business", 25, 68), ("works in a bank branch", 20, 64)]
LIVING = [  # (text, youngest, oldest)
    ("lives alone in a flat", 19, 72), ("lives with a partner of six years", 25, 72), ("lives with two flatmates", 19, 40),
    ("lives with their parents again", 19, 38), ("lives with a partner and a young child", 24, 48),
    ("lives alone since a breakup", 19, 72), ("shares a house with a sibling", 19, 70),
    ("lives with a teenage son after a divorce", 36, 62)]
HEALTH = ["takes no regular medication", "takes sertraline from their GP", "has asthma and uses an inhaler",
          "has migraines a few times a month", "has high blood pressure and takes medication for it",
          "had knee surgery last year", "has trouble sleeping most weeks", "drinks two or three coffees a day"]

BANK = {
    "anxiety": {
        "beliefs": ["helpless"],
        "situations": ["has started avoiding the supermarket because of panic in the queue",
                       "lies awake replaying conversations from work",
                       "has had chest tightness before meetings and is sure something is wrong",
                       "checks the doors and the stove several times before leaving the house"],
        "thoughts": ["Something terrible is going to happen.", "If I panic, everyone will see and I'll lose control.",
                     "I can't cope with this.", "What if I've missed something important?"],
        "intermediate": ["If I let my guard down, things will go wrong.",
                         "It is better to avoid things than to risk panicking.",
                         "If I worry enough, I can stop bad things happening."],
        "coping": ["avoids places that set it off", "asks people for reassurance", "keeps busy so there's no time to think",
                   "scrolls on the phone late at night"],
        "emotions": ["anxious", "tense", "scared", "on edge"],
    },
    "self-esteem": {
        "beliefs": ["worthless"],
        "situations": ["was passed over for a promotion and keeps going over it",
                       "compares themself with friends online every evening",
                       "turned down an invitation because they felt they had nothing to say",
                       "got critical feedback at work and has not slept well since"],
        "thoughts": ["I'm not good enough.", "Everyone else has it together except me.", "I'm a failure.",
                     "They only put up with me."],
        "intermediate": ["If I'm not perfect, I'm worthless.", "If people saw the real me, they'd leave.",
                         "I have to earn the right to be liked."],
        "coping": ["works late to prove themself", "stays quiet in groups", "puts themself down before others can",
                   "avoids trying new things"],
        "emotions": ["ashamed", "sad", "embarrassed", "flat"],
    },
    "relationships": {
        "beliefs": ["unlovable"],
        "situations": ["keeps arguing with their partner about money and chores",
                       "has drifted from their closest friend and doesn't know why",
                       "is going through a separation and sharing care of the children",
                       "feels shut out by their adult daughter"],
        "thoughts": ["Nobody really wants me around.", "I always ruin things.", "They'll leave like everyone else.",
                     "I'm too much for people."],
        "intermediate": ["If I say what I need, people will leave.", "It's safer not to depend on anyone.",
                         "If someone is upset, it must be my fault."],
        "coping": ["goes quiet and withdraws after arguments", "tries hard to keep everyone happy",
                   "checks their partner's messages", "spends evenings alone with the television"],
        "emotions": ["lonely", "hurt", "angry", "guilty"],
    },
    "career": {
        "beliefs": ["helpless", "worthless"],
        "situations": ["has a new manager who criticises everything", "dreads Mondays and calls in sick more often",
                       "was made redundant and is struggling to apply for jobs",
                       "is stuck in a role they hate but can't see a way out"],
        "thoughts": ["I'll never get anywhere.", "I'm going to get fired.", "There's no point trying.",
                     "I picked the wrong life."],
        "intermediate": ["If I make one mistake, it's over.", "Work success is what makes me worth something.",
                         "Asking for help shows weakness."],
        "coping": ["procrastinates and then works all night", "avoids opening work emails",
                   "complains to friends but doesn't change anything", "drinks a few beers to switch off"],
        "emotions": ["stressed", "hopeless", "frustrated", "tired"],
    },
    "other": {
        "beliefs": ["helpless"],
        "situations": ["has been grieving their father who died in the spring",
                       "is caring for a parent with dementia and has no time for themself",
                       "moved to a new city and knows nobody", "has a chronic pain condition that limits work"],
        "thoughts": ["I can't keep going like this.", "Nobody understands.", "It's never going to get better.",
                     "I should be handling this better."],
        "intermediate": ["If I stop, everything will fall apart.", "My needs come last.",
                         "Other people have it worse, so I shouldn't complain."],
        "coping": ["keeps going until exhausted", "cries in the car", "throws themself into chores",
                   "stays in bed on weekends"],
        "emotions": ["sad", "overwhelmed", "numb", "tired"],
    },
}
HISTORY = ["had a hard time at school and was bullied for a year", "grew up with a parent who drank",
           "had a period of low mood in their twenties that passed without help",
           "saw a counsellor once before, years ago, for a few sessions", "moved house many times as a child",
           "was close to a grandparent who died when they were a teenager", "has never been in therapy before"]
BEHAVIOURS = {
    "plain": "Answers what is asked, plainly.",
    "upset": "Gets tearful when the main worry comes up.",
    "verbose": "Gives long answers with lots of background.",
    "reserved": "Waits to be asked; short answers at first.",
    "tangent": "Wanders off to side topics and comes back.",
    "pleasing": "Says things are fine more than they are; apologises often.",
}


def _pick(rng: random.Random, xs):
    return xs[rng.randrange(len(xs))]


# fit: "of two" cannot match a home with one young child, so the fit card says only "a stay-at-home parent"
FIT_TEXT = {"is a stay-at-home parent of two": "is a stay-at-home parent"}
# fit: card wording reworded so no 6-word run of any card a vignette may draw on matches the private pools (the
# Psych Terms licence check, experiments/bank_overlap.py; "Something terrible is going to happen." is in a HOPE transcript)
FIT_WORDING = {"Something terrible is going to happen.": "Something awful is about to happen."}
MEDICATION = ("takes sertraline from their GP", "has high blood pressure and takes medication for it",
              "has asthma and uses an inhaler")


PARTNER_LIVING = ("lives with a partner of six years", "lives with a partner and a young child")
# fit: a card with no job gets no work-based situation or coping (a retiree passed over for a promotion)
NO_JOB = ("is retired after thirty years in sales", "is between jobs after a layoff", "is a stay-at-home parent of two",
          "is a stay-at-home parent", "is a second-year university student")
WORK = re.compile(r"promotion|at work|from work|manager|mondays|calls in sick|a role they hate|before meetings|work emails|"
                  r"works late|works all night")
APPEARANCE = ["casually dressed and well groomed", "neatly dressed", "dressed for work", "looks tired, clothes a little creased"]
MSE_BY_STYLE = {  # (behaviour, speech, thought process)
    "plain": ("cooperative, good eye contact", "normal rate and volume", "logical and goal-directed"),
    "upset": ("tearful at times, fidgets with their hands", "halting at times", "logical, returns to what upsets them"),
    "verbose": ("cooperative and talkative", "rapid, with a lot of detail", "logical, over-detailed"),
    "reserved": ("quiet, little eye contact at first", "soft, short answers", "logical and goal-directed"),
    "tangent": ("cooperative, easily side-tracked", "normal rate, drifts to other topics", "tangential at times, can be redirected"),
    "pleasing": ("eager to please, apologises often", "soft, normal rate", "logical and goal-directed"),
}
SETTINGS = ["community mental health centre", "private practice", "primary care clinic",
            "employee assistance programme"]
SIB = [("older sister", "female"), ("younger sister", "female"), ("older brother", "male"), ("younger brother", "male")]


def _backstory(rng: random.Random, age: int, occupation: str, living: str, situation: str, history: str,
               emotions: list[str], style: str, client_name: str = "") -> dict:
    """The fit card's backstory: relationship status, family, setting, type of counselling, mental status. Follows the
    living situation and what the card's situation and history already say (a father who died, a parent with dementia,
    an adult daughter, a separation, a partner)."""
    sit, hist = situation.lower(), history.lower()
    if living in PARTNER_LIVING:
        rel = rng.choice(["married", "in a relationship"])
    elif "separation" in sit:
        rel = "separated"
    elif "divorce" in living:
        rel = "divorced"
    elif age >= 66 and "alone" in living and rng.random() < 0.4:
        rel = "widowed"
    else:
        rel = "single"
    fam = []

    def person(relation, gender, alive=True, where="lives nearby", note=None):
        taken = {client_name, *(m["name"] for m in fam)}  # no two people on a card share a first name
        d = {"relation": relation, "name": _pick(rng, [n for n in NAMES[gender] if n not in taken]), "alive": alive}
        d["where"] = where if alive else "died"
        if note:
            d["note"] = note
        fam.append(d)

    if rel in ("married", "in a relationship"):
        person("partner", rng.choice(["female", "male"]), where="lives with the client")
    if "young child" in living:
        kid = "daughter" if rng.random() < 0.5 else "son"
        person(kid, "female" if kid == "daughter" else "male", where="lives with the client", note=f"aged {rng.randint(2, 6)}")
    if "teenage son" in living:
        person("son", "male", where="lives with the client", note=f"aged {rng.randint(13, 17)}")
    if "stay-at-home parent" in occupation and not any(m["relation"] in ("son", "daughter") for m in fam):
        person("daughter", "female", where="lives with the client", note=f"aged {rng.randint(2, 9)}")
    if "separation" in sit:
        for _ in range(2):
            kid = rng.choice(["son", "daughter"])
            person(kid, "female" if kid == "daughter" else "male", where="lives with the client part of the week",
                   note=f"aged {rng.randint(4, 14)}")
    if "adult daughter" in sit:
        person("daughter", "female", where="lives in another town", note=f"aged {rng.randint(18, max(18, age - 22))}")
    with_parents = "parents" in living
    old = age >= 66
    mother_alive = with_parents or "parent with dementia" in sit or rng.random() < (0.9 if age < 50 else 0.6 if not old else 0.2)
    father_alive = (with_parents or rng.random() < (0.85 if age < 50 else 0.5 if not old else 0.15)) and "father who died" not in sit
    if "father who died" in sit:
        father_alive = False
    mnote = "has dementia" if "parent with dementia" in sit else None
    person("mother", "female", mother_alive, "lives with the client" if with_parents or mnote else rng.choice(["lives nearby", "lives in another town"]), mnote)
    person("father", "male", father_alive, "lives with the client" if with_parents else rng.choice(["lives nearby", "lives in another town"]),
           "died in the spring" if "father who died" in sit else None)
    n_sib = rng.choice([0, 1, 1, 2])
    for rel_s, g in rng.sample(SIB, n_sib):
        person(rel_s, g, where="lives with the client" if "sibling" in living and not any(
            m.get("where") == "lives with the client" and "sister" in m["relation"] + "brother" for m in fam)
            else rng.choice(["lives two hours away", "lives nearby", "lives abroad"]))
    if "sibling" in living and not any(m["relation"] in [r for r, _ in SIB] and m["where"] == "lives with the client" for m in fam):
        r_s, g = rng.choice(SIB)
        person(r_s, g, where="lives with the client")
    setting = "university counselling centre" if "university student" in occupation else rng.choice(SETTINGS)
    beh, speech, thought = MSE_BY_STYLE[style]
    looks = [a for a in APPEARANCE if not (a == "dressed for work" and occupation in NO_JOB)]
    mse = [f"Appearance: {rng.choice(looks)}", f"Behaviour: {beh}", f"Speech: {speech}",
           f"Mood: describes feeling {emotions[0]} and {emotions[1]}", "Affect: congruent with the mood they describe",
           f"Thought process: {thought}", "Orientation: oriented to person, place and time",
           f"Insight: {rng.choice(['fair', 'good', 'limited'])}"]
    return {"relationship_status": rel, "family": fam, "setting": setting, "counselling_type": "individual",
            "mental_status": mse}


def build(seed: int | str, problem: str | None = None, style: str | None = None, fit: bool = True) -> dict:
    """One persona card, the same for the same seed (and problem and style, when given). fit (the default since the
    persona rebuild, arcsim/PREREG.md): the card does not contradict itself (no "takes no regular medication" beside a
    medicine; a stay-at-home parent lives with their children; a partner the client argues with about chores lives
    with them; a separation is not lived with a partner; an adult daughter needs an age of 40 or more; no partner in
    the coping lines without a partner; no work-based situation or coping for a card with no job) and carries the
    backstory of persona schema v0.3 (relationship status, family, setting, type of counselling, mental status), drawn
    from a second seeded stream so the other fields stay as they were. fit=False rebuilds the cards of every earlier run."""
    rng = random.Random(f"arcsim-persona:{seed}")
    if problem is None:
        problem = rng.choices([p for p, _ in PROBLEMS], [w for _, w in PROBLEMS])[0]
    style = style or _pick(rng, list(STYLES))
    gender = rng.choices(["female", "male", "non-binary"], [48, 48, 4])[0]
    age = rng.randint(19, 72)
    b = BANK[problem]
    health = rng.sample(HEALTH, 2)
    if fit and "takes no regular medication" in health and any(h in MEDICATION for h in health):
        keep = next(h for h in health if h != "takes no regular medication")
        health = [keep, rng.choice([h for h in HEALTH if h not in (keep, "takes no regular medication")])]
    name = _pick(rng, NAMES[gender])
    occupation = _pick(rng, [t for t, lo, hi in OCCUPATIONS if lo <= age <= hi])
    living = _pick(rng, [t for t, lo, hi in LIVING if lo <= age <= hi])
    if fit and "stay-at-home parent" in occupation and not re.search(r"child|son", living):
        living = _pick(rng, [t for t, lo, hi in LIVING if lo <= age <= hi and re.search(r"child|son", t)])
    history = _pick(rng, HISTORY).capitalize() + "."
    intermediate = _pick(rng, b["intermediate"])
    coping = "; ".join(rng.sample(b["coping"], 2)).capitalize() + "."
    situation = _pick(rng, b["situations"]).capitalize() + "."
    thoughts = " ".join(rng.sample(b["thoughts"], 2))
    if fit:
        for old, new in FIT_WORDING.items():
            thoughts = thoughts.replace(old, new)
    emotions = rng.sample(b["emotions"], 3)
    profile = {"name": name, "age": age, "gender": gender, "occupation": occupation, "living_situation": living,
               "details": health}
    if fit:
        r2 = random.Random(f"arcsim-persona-backstory:{seed}")
        sit = situation.lower()
        if "adult daughter" in sit and age < 40:
            situation = _pick(r2, [x for x in b["situations"] if "adult daughter" not in x]).capitalize() + "."
            sit = situation.lower()
        ages_ok = [t for t, lo, hi in LIVING if lo <= age <= hi]
        if "arguing with their partner" in sit and living not in PARTNER_LIVING:
            if any(t in PARTNER_LIVING for t in ages_ok):
                living = _pick(r2, [t for t in ages_ok if t in PARTNER_LIVING])
            else:  # too young for a shared home in the bank: another situation
                situation = _pick(r2, [x for x in b["situations"] if "partner" not in x and "adult daughter" not in x
                                       and "separation" not in x]).capitalize() + "."
                sit = situation.lower()
        if "separation" in sit and living in PARTNER_LIVING:
            living = _pick(r2, [t for t in ages_ok if t not in PARTNER_LIVING and "parents" not in t])
        if "stay-at-home parent" in occupation and not re.search(r"child|son", living):
            occupation = "is between jobs after a layoff" if 22 <= age <= 64 else occupation
        if "partner" in coping.lower() and living not in PARTNER_LIVING:  # no partner's messages without a partner
            coping = "; ".join(r2.sample([x for x in b["coping"] if "partner" not in x], 2)).capitalize() + "."
        if occupation in NO_JOB and WORK.search(situation.lower()):
            free = [x for x in b["situations"] if not WORK.search(x) and "partner" not in x and "adult daughter" not in x
                    and "separation" not in x]
            jobs = [t for t, lo, hi in OCCUPATIONS if lo <= age <= hi and t not in NO_JOB]
            if free:
                situation = _pick(r2, free).capitalize() + "."
            elif jobs:  # every situation in this problem's bank is about work: the client has a job
                occupation = _pick(r2, jobs)
        if occupation in NO_JOB and WORK.search(coping.lower()):
            coping = "; ".join(r2.sample([x for x in b["coping"] if not WORK.search(x) and
                                          ("partner" not in x or living in PARTNER_LIVING)], 2)).capitalize() + "."
        occupation = FIT_TEXT.get(occupation, occupation)
        profile.update({"occupation": occupation, "living_situation": living})
        profile.update(_backstory(r2, age, occupation, living, situation, history, emotions, style, name))
    return {
        "persona_id": f"p_{seed}",
        "seed": seed,
        "presenting_problem": problem,
        "talking_style": style,
        "profile": profile,
        "cognitive_model": {
            "relevant_history": history,
            "core_beliefs": list(b["beliefs"]),
            "intermediate_beliefs": intermediate,
            "coping_strategies": coping,
            "situation": situation,
            "automatic_thoughts": thoughts,
            "emotions": emotions,
            "behaviors": BEHAVIOURS[style] + " " + STYLES[style].capitalize() + ".",
        },
    }


# ------------------------------------------------------------------------------------- intake-only fields (library)
SEXUALITY = ["heterosexual", "gay or lesbian", "bisexual", "not stated"]
ETHNICITY = ["White", "Black or African American", "Hispanic or Latino", "Asian", "Middle Eastern or North African",
             "Native American or Alaska Native", "Native Hawaiian or Pacific Islander", "Multiracial", "not stated"]


def assign_intake_only(cards: dict, strata: dict) -> dict:
    """Sexuality and ethnicity for a library of cards (card id -> card), spread evenly by a round robin within each
    stratum (strata: card id -> "risk" / "diagnosis" / "other"), the order within a stratum set by a hash of the id, so
    no value follows a risk or a diagnosis. Returns card id -> {"sexuality", "ethnicity"}; the cards are not changed
    here: intake-only fields live beside the card, never in what the client is given."""
    import hashlib

    out = {}
    for stratum in sorted(set(strata.values())):
        ids = sorted((i for i in cards if strata[i] == stratum), key=lambda i: hashlib.sha256(str(i).encode()).hexdigest())
        for n, i in enumerate(ids):
            out[i] = {"sexuality": SEXUALITY[n % len(SEXUALITY)], "ethnicity": ETHNICITY[(n * 4 + len(out)) % len(ETHNICITY)]}
    return out


def client_card(persona: dict) -> str:
    """The card as the client is given it: who they are, their backstory and their cognitive model. Never an
    intake-only field (sexuality, ethnicity) and never the mental-status observations (the clinician's, not the client's)."""
    p, m = persona["profile"], persona["cognitive_model"]
    lines = [f"You are {p['name']}. Your card (notes about you):", f"- Age: {p['age']}. Gender: {p['gender']}.",
             f"- Work: {p['occupation']}.", f"- Home: {p['living_situation']}."]
    if p.get("relationship_status"):
        lines.append(f"- Relationship: {p['relationship_status']}.")
    for f in p.get("family", []):
        bits = [f"your {f['relation']}, {f['name']}"] + ([f["note"]] if f.get("note") else []) + \
               ([f["where"]] if f.get("alive") else ["died" if "died" not in (f.get("note") or "") else ""])
        lines.append("- Family: " + ", ".join(x for x in bits if x) + ".")
    lines += [f"- {d[0].upper()}{d[1:]}." for d in p["details"]]
    lines += [f"- History: {m['relevant_history']}", f"- Now: {m['situation']}",
              f"- Deep down you feel {' and '.join(m['core_beliefs'])}. {m['intermediate_beliefs']}",
              f"- Thoughts that come up: {m['automatic_thoughts']}", f"- Feelings: {', '.join(m['emotions'])}.",
              f"- Coping: {m['coping_strategies']}", f"- Manner: {m['behaviors']} Talking style: {persona['talking_style']}."]
    return "\n".join(lines)
