#!/usr/bin/env python3
"""Issue #122 -- reference CURATION.

Curation is NOT discovery and NOT verification.  Discovery returned 1812 candidates, most of them
noise (a relevance search matches any paper sharing a word -- "collapse" alone pulls in stars,
proteins and markets).  This file applies an EXPLICIT, reproducible RULE to that pool -- a title must
mention generative/self-consuming/synthetic training at all AND match one family's pattern AND carry
a computer-science category -- and assigns each kept entry a role naming WHERE it is used.

Titles are COPIED from the discovery artefact (`refs/candidates.json`) by identifier, never
retyped.  Any chosen id that is NOT in the pool must be declared in EXTRAS with its own title, so
the difference between "found by search" and "supplied by the author" stays visible.

A role is a statement about WHERE an entry is used, not a quality label.

Usage:  /usr/bin/python3 refs_curate.py
Out:    refs/curated.json
"""
import json
import os
import re
import sys

CAND = "refs/candidates.json"
OUT = "refs/curated.json"

# The selection RULE, in limbs -- ALL must hold:
#   (a) TOPIC ANCHOR: the title must be about generative models / their training data at all
#       (without this, "collapse", "diversity" or "entropy" alone pull in astronomy and medicine);
#   (b) FAMILY: the title must match one family's pattern; the first family that matches IS the
#       role, and the role is what the entry is cited for;
#   (c) EXCLUSION of fields that share the vocabulary but not the object.
ANCHOR = re.compile(
    r"model collaps|self-consuming|self consuming|autophag|recursive training|"
    r"training on (generated|synthetic|its own)|train\w* on (generated|synthetic)|"
    r"synthetic (data|sample|text|corpus|instruct)|generated (data|sample|text|content|token)|"
    r"generative (model|ai|network|system|pretraining)|diffusion model|"
    r"large language model|\bllm\b|language model|foundation model|"
    r"training data|data mixtur|data curation|dataset curation|data selection|"
    r"knowledge distillat|distillation|continual learning|catastrophic forgetting",
    re.I)

# The THEORY family needs its OWN anchor: a paper titled "On the Perron-Frobenius theorem for
# non-negative matrices" is a legitimate foundation for this paper's recursion and will never
# mention a language model.  So the anchor is PER-FAMILY -- the generative object for the applied
# roles, a named mathematical object for theory -- rather than one global gate that either lets
# signal processing in (too loose) or removes the foundations (too tight).
THEORY_ANCHOR = re.compile(
    r"branching process|galton|perron|coupon collector|first passage|hitting time|"
    r"ergodic|stationary distribution|renewal process|extinction probability|"
    r"jensen|multinomial|"
    # information geometry is a broad mathematics term (operator scaling, groupoids, game theory,
    # sensor configuration all carry it); the entry must be about its use on a LEARNING object.
    r"fisher[- ]rao.*(neural|learning|network|generativ)|"
    r"information geometr\w*.*(neural|learning|network|generativ)|"
    r"mean[- ]field.*(learning|neural|network|generativ)", re.I)

FAMILIES = [
    # the construct: the self-consuming loop itself and the failure it is named for
    ("construct", re.compile(
        r"model collapse|self-consuming|self consuming|recursive training|"
        r"training on (generated|synthetic|its own)|generat\w* data|synthetic data|"
        r"data collaps|autophag|degenerat\w* (model|generat)|collapse of (generativ|model)|"
        r"inbreeding|model eating|curse of recursion", re.I)),
    # the theory the paper builds on: the exact chain, its stationary law and its tail
    ("theory", re.compile(
        r"branching process|galton|perron|stationary distribution|markov chain|"
        r"mean[- ]field|population dynamic|information geometr|fisher[- ]rao|"
        r"wasserstein|empirical (measure|distribution)|"
        r"jensen|multinomial|coupon collector|"
        r"first passage|hitting time|ergodic|stationary distribution|"
        r"renewal process|extinction probability|branching process|galton|perron|"
        r"fisher[- ]rao|information geometr", re.I)),
    # the mechanism: how a distribution loses its support / its diversity / its tail
    ("mechanism", re.compile(
        r"mode collaps|diversity (collaps|loss|degrad)|entropy (collaps|decreas|regulariz)|"
        r"catastrophic forgetting|forgetting|rare (event|class|token|word)|long tail|"
        r"support (loss|shrink|collaps)|degenerat\w*|memoriz|sample (diversity|quality)|"
        r"distribution(al)? (shift|drift|collaps)", re.I)),
    # the protocol: how the pool is formed -- the axis P2 turns on
    ("protocol", re.compile(
        r"data mixtur|data mixing|mixing law|data (selection|curation|filtering)|"
        r"dataset (curation|filtering)|deduplicat|quality filter|distillat|self[- ]training|"
        r"self[- ]play|replay|curriculum|data (recipe|budget|schedul)|"
        r"ratio of (real|synthetic)|real data|fresh data|data (pool|store|accumulat)", re.I)),
    # what the field does instead of measuring recovery
    ("prevention", re.compile(
        r"mitigat|prevent|avoid\w* collaps|detect\w* collaps|anchor|regulariz|"
        r"entropy bonus|data augmentation|early stopping|"
        r"stabiliz|preserv\w* (diversity|entropy|support)", re.I)),
    # how the degradation is measured from outside
    ("measurement", re.compile(
        r"contamination|benchmark|evaluation|measur|estimator|metric|"
        r"generalization (bound|error)|covariate shift|transfer|"
        r"out[- ]of[- ]distribution|ood", re.I)),
    # adjacent loops that run the same machinery on a different object
    ("adjacent", re.compile(
        r"continual learning|lifelong|online learning|domain adaptation|"
        r"test[- ]time adaptation|few[- ]shot learning|federated learning|"
        r"continual (learning|adaptation)|online (learning|adaptation)|lifelong learning",
        re.I)),
]

# limb (c): fields that share the vocabulary but not the object -- read on review, not a regex guess
EXCLUDE = re.compile(
    r"\bstar\b|stellar|galax|cosmol|astrophys|gravitational|black hole|neutron|"
    r"protein|molecul|clinic|patient|covid|tumor|epidem|"
    r"seismic|earthquake|material|chemist|market|stock|econom|"
    r"plasma|supernova|dark matter|solar|climate", re.I)

# entries removed BY HAND on review, by bare id, with the reason kept here so the removal is visible
REVIEWED_OUT = [
    # -- construct: "recursive training" used as a TRAINING SCHEDULE, and synthetic data used in an
    #    application domain -- the title matches the word, the paper is about another object.
    "1508.04843",   # recursive training of 2D-3D conv nets for neuronal boundary detection
    "1702.05711",   # zoom out-and-in network with recursive training for object proposal
    "2103.00086",   # recursive training for zero-shot semantic segmentation
    "2003.10839",   # bone structures in chest radiographs via CNN trained on synthetic data
    "2507.00822",   # particle size distribution measurement using CNNs trained on synthetic data
    # -- protocol: knowledge distillation for MODEL COMPRESSION.  Distillation is a pool protocol
    #    (the student trains on the teacher's outputs); compressing a U-net is not.
    "1812.00249", "1812.00660", "1907.09682", "1909.11723", "1910.01348", "2002.09168",
    "2004.08116", "2007.01476", "2007.06889", "2007.09029", "2104.07163", "2108.12905",
    "1908.00928",   # a multi-media EXCHANGE FORMAT for dataset curation -- a file format
    # -- mechanism: catastrophic forgetting inside a specific application or architecture
    "1705.07241", "1804.04286", "2101.06984", "2102.07686", "2108.02786", "2207.08180",
    "2211.14177", "2305.16252", "2305.17244", "2306.17091",
    # -- adjacent: the loop is not the object (self-organising maps, meta-learning, surveillance)
    "1904.09330", "1905.12588", "2004.07941", "2004.10862",
    # -- prevention: claim identification, matched only through "data augmentation"
    "2107.05684",
    # -- theory: the named object is right, the paper is about another use of it
    "0912.2523",    # coupon collectors in cooperative multiplayer games
    "1011.3710",    # mean-field accuracy on real-world networks (no learning object)
    "1503.02951",   # mean-field GAMES for societal nudging
    "2002.07688",   # quantum coupon collector
    "2112.07884",   # experimental quantum advantage, quantum coupon collector
    "2107.04050",   # multi-agent mean-field reinforcement learning
    "2304.11017",   # Las Vegas algorithm acceleration via reverse Jensen
    # -- construct tail: synthetic data inside a specific application domain (a crop, a radar, a
    #    detector, a privacy tool) rather than the loop.  Support separates these cleanly: the 20
    #    entries returned by >=2 independent queries are ALL model-collapse work.
    "2212.06896", "2212.10310", "2202.00632", "2207.14406", "2109.05294", "2105.00717",
    # -- protocol tail: more compression-flavoured distillation, plus domain-specific curation
    "1805.07170", "2101.06554", "2103.13885", "2109.15014", "2111.11747", "2111.12170",
    "2112.05638",
    # -- theory tail: further coupon-collector variants with no learning object
    "2507.15231", "2602.20705", "2601.05030", "2010.00145",
    # ---- R522: the SECOND PASS promoted a new tail (a per-object cap and a repaired support
    #      metric both re-order a truncated pool, so the entries just below the old cut are new to
    #      review).  Read on review, same limb (c) as above -- the title matches the word, the paper
    #      is about another object.
    # construct: synthetic data used for PRIVACY / ANONYMISATION, i.e. a different object entirely
    "1902.03468",   # sequential/private synthetic data generators
    "2004.07740",   # a data-UTILITY framework for synthetic data release
    "2006.02397",   # "One Step to Efficient Synthetic Data" -- efficient generation, not the loop
    "2011.07018",   # anonymisation "Groundhog Day" -- privacy, matched only by "synthetic data"
    # measurement: a benchmark/leakage instrument about ANOTHER object
    "2106.02585",   # procedural world generation for evaluating continual-LEARNING agents
    "2310.07637",   # OpsEval -- an IT-operations benchmark suite, matched by "benchmark"
    # mechanism: a paper about contamination measurement, matched only through the word "memoriz"
    "2402.15938",   # generalization-or-memorization under DATA CONTAMINATION (a measurement object)
    # prevention: mitigation of a DIFFERENT degradation than the one this paper studies
    "2506.17627",   # mitigating benchmark leakage in LLM assessment
    "2407.21523",   # a survey of TABULAR data augmentation
]


def _words(q):
    return set(re.findall(r"[a-z0-9]+", q.lower()))


def is_nested(q1, q2):
    """True when one query's words are all present in the other's -- the two strings name the SAME
    phrase at two lengths, so a paper returned by both tells us nothing that one of them alone did
    not already tell us.

    This is the round's central repair.  The second discovery pass added a paraphrase partner for
    each enumerative query, and the ranking by raw query support rose immediately -- but on
    inspection EVERY theory entry that rose was raised by a NESTED pair ("coupon collector" +
    "coupon collector problem", "Jensen inequality" + "Jensen's inequality"), i.e. support was
    manufactured by the instrumentation rather than measured from the literature.  Support that
    ranks a family must therefore count only INDEPENDENT agreements.
    """
    a, b = _words(q1), _words(q2)
    return a <= b or b <= a


def indep_support(keys, text):
    """How many of the queries that returned an entry are independent phrasings.  Greedy over the
    shortest query first, so the count does not depend on the order the queries happened to run."""
    kept = []
    for k in sorted(keys, key=lambda s: len(text.get(s, s).split())):
        q = text.get(k, k)
        if any(is_nested(q, text.get(o, o)) for o in kept):
            continue
        kept.append(k)
    return len(kept)


# THEORY cannot be ranked by support at all, and this is now MEASURED rather than assumed: of the
# 30 theory entries that reach curation, ZERO are found by two independent phrasings (the second
# discovery pass raised 12 of them to support >= 2 and every one of those agreements was a NESTED
# pair -- once nesting is discounted the family returns to 0).  The reason is structural: the
# applied families probe ONE object with many paraphrases, while the theory family enumerates
# DISTINCT objects (coupon collector, Perron-Frobenius, Jensen, ...), so support ranks nothing
# there and the cap would otherwise cut the pool by publication date.
# So theory's cap is applied by a DECLARED order naming the object each entry serves, in the order
# this paper's own chain uses them.  Declared, not derived -- and therefore visible in the artefact.
THEORY_ORDER = [
    "branching-process", "galton-watson", "extinction-probability",      # the recursion itself
    "markov-stationary", "stationary-distributions",                     # its stationary law
    "coupon-collector", "hitting-times",                                 # the support/healing time
    "tail-bound", "concentration-inequality", "large-deviations",        # the tail
    "multinomial-distribution",                                          # the per-symbol law
    "mean-field",                                                        # the mean-field limit
    "empirical-measure", "optimal-transport",                            # the empirical measure
    "information-geometry", "fisher-rao", "jensen-inequality",           # the convexity/geometry
]


THEORY_PER_OBJECT_CAP = 3   # at most three references serve any one object in the chain


def theory_rank(keys, text):
    """Where an entry's own query sits in the declared chain; unknown queries sort last."""
    order = {k: i for i, k in enumerate(THEORY_ORDER)}
    ranks = [order[k] for k in keys if k in order]
    return min(ranks) if ranks else len(THEORY_ORDER)


def bare(aid):
    return aid.split("/")[-1].split("v")[0] if "/" not in aid else aid


def is_cs(cats):
    return any(c.startswith(("cs.", "cs")) for c in cats)


def role_of(title):
    for role, pat in FAMILIES:
        if pat.search(title):
            return role
    return None


def diff_for(role, title):
    """A one-line statement of WHERE the entry is used -- generated from the role, so it is not
    typed per entry and cannot drift from the rule that selected it."""
    return {
        "construct": "a treatment of the self-consuming loop and the failure this paper measures",
        "theory": "theory for the exact chain this paper's recursion belongs to (its stationary law, its tail, or its support)",
        "mechanism": "a treatment of how a distribution loses support, diversity or its tail -- the mechanism this paper isolates",
        "protocol": "a training-data protocol whose fresh-data fraction and pool history this paper shows are not interchangeable",
        "prevention": "the field's mitigation literature, which is prevention-only and is what this paper is measured against",
        "measurement": "an instrument or metric for detecting the degradation this paper studies",
        "adjacent": "an adjacent loop (online / continual / agentic) that runs the same machinery on a different object",
    }[role]


def main():
    if not os.path.exists(CAND):
        print("missing %s -- run refs_discover.py first" % CAND, file=sys.stderr)
        sys.exit(1)
    art = json.load(open(CAND))
    pool = art["candidates"]
    text = art["query_text"]
    missing = [k for k in THEORY_ORDER if k not in text]
    if missing:
        print("  ! THEORY_ORDER names queries that do not exist: %s" % missing, file=sys.stderr)
        sys.exit("refusing to run: the declared theory order must name real queries")
    kept = []
    for c in pool:
        if not is_cs(c["cats"]):
            continue
        gen = bool(ANCHOR.search(c["title"]))       # limb (a): about the generative/training object
        th = bool(THEORY_ANCHOR.search(c["title"]))  # or about the named mathematical object
        if not (gen or th):
            continue
        if EXCLUDE.search(c["title"]):             # limb (c): not an adjacent field
            continue
        if bare(c["id"]) in REVIEWED_OUT:          # limb (d): removed on review, by id
            continue
        role = role_of(c["title"])
        if role is None:
            continue
        if role == "theory" and not th:            # theory must carry its own object
            continue
        if role != "theory" and not gen:           # applied roles must carry the generative object
            continue
        kept.append((c, role))

    # CAP per family, ranked by QUERY SUPPORT -- how many of the discovery queries returned the
    # entry, a reproducible proxy for topical centrality (an entry several independent queries
    # agree on is more likely to be about the topic than one a single broad query matched).
    CAPS = {"construct": 24, "theory": 14, "mechanism": 16, "protocol": 14,
            "prevention": 10, "measurement": 16, "adjacent": 8}
    out, seen = [], set()
    pressure = []   # class 164(e): a filter UPSTREAM of a truncation cannot be observed downstream
    for role, _pat in FAMILIES:
        fam = [(c, r) for c, r in kept if r == role]
        if role == "theory":
            # support is undefined here (measured 0/30 independent agreements) -> use the declared
            # chain, and keep support only as a tie-break that can never matter on its own
            fam.sort(key=lambda t: (theory_rank(t[0]["queries"], text),
                                    -indep_support(t[0]["queries"], text), t[0]["published"]))
        else:
            fam.sort(key=lambda t: (-indep_support(t[0]["queries"], text), t[0]["published"]))
        # A family whose queries name DISTINCT objects (theory) must also cap PER OBJECT: ranking
        # alone let 7 of the 14 theory slots go to coupon-collector variants, because one object's
        # cluster outnumbers every other object -- a reference list that spends half a family on one
        # object is padded, not covered.  Applied to theory only: the applied families' queries are
        # paraphrases of a single object, so an object cap there would collapse the family.
        if role == "theory":
            picked, per_obj, rest = [], {}, []
            for c, _r in fam:
                o = theory_rank(c["queries"], text)
                if per_obj.get(o, 0) < THEORY_PER_OBJECT_CAP:
                    per_obj[o] = per_obj.get(o, 0) + 1
                    picked.append((c, _r))
                else:
                    rest.append((c, _r))
            fam = picked + rest
        # Report the truncation itself: the pool that reached the cap, the cap, and the TOP OF THE
        # DROPPED TAIL.  Without this, a family sitting exactly at its cap re-prints the same count
        # after any upstream removal while silently promoting the next-ranked (noisier) candidate,
        # so "capped" and "the whole family" look identical from the artefact.
        n_support2 = sum(1 for c, _ in fam if indep_support(c["queries"], text) >= 2)
        pressure.append(dict(role=role, pool=len(fam), cap=CAPS[role],
                             kept=min(len(fam), CAPS[role]), support_ge2=n_support2,
                             dropping=len(fam) > CAPS[role],
                             tail=[(c["id"], indep_support(c["queries"], text))
                                   for c, _ in fam[CAPS[role]:CAPS[role] + 3]]))
        for c, _r in fam[:CAPS[role]]:
            b = bare(c["id"])
            if b in seen:
                continue
            seen.add(b)
            out.append(dict(id=c["id"], bare=b, title=c["title"], published=c["published"],
                            cats=c["cats"], role=role, diff=diff_for(role, c["title"]),
                            support=indep_support(c["queries"], text),
                            raw_support=len(c["queries"]), source="discovery"))

    roles = {}
    for o in out:
        roles[o["role"]] = roles.get(o["role"], 0) + 1
    os.makedirs("refs", exist_ok=True)
    print("\n%-12s %6s %5s %6s %8s  %s" % ("role", "pool", "cap", "kept", "sup>=2", "dropped tail (id, support)"))
    for p in pressure:
        print("%-12s %6d %5d %6d %8d  %s%s" % (
            p["role"], p["pool"], p["cap"], p["kept"], p["support_ge2"],
            "TRUNCATED " if p["dropping"] else "", p["tail"]))
    json.dump(dict(n=len(out), roles=roles, cap_pressure=pressure,
                   rule="cs category AND a PER-FAMILY anchor (the generative/training object for "
                        "applied roles, a named mathematical object for theory) AND a family "
                        "pattern; capped per family by query support",
                   entries=out), open(OUT, "w"), indent=1)
    print("curated %d entries -> %s" % (len(out), OUT))
    for r in sorted(roles):
        print("   %-12s %d" % (r, roles[r]))
    print("   source: %d discovery, %d author" % (
        sum(1 for o in out if o["source"] == "discovery"),
        sum(1 for o in out if o["source"] == "author")))


if __name__ == "__main__":
    main()
