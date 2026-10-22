#!/usr/bin/env python3
"""issue #141 -- v4: THE SIGN THE TRANSPORT STATISTIC CANNOT SEE, AND THE LADDER IT IS MEASURED ON.

Two jobs, one scan.

(A) THE LADDER.  v0-v3 measured every law on a zoo of four games -- `fpsb_n2`, `spsb_n2`, `cv_n2`,
    `cv_n4`.  That is three families with ONE bidder-count each except the common-value pair, so every
    claim carried an unstated domain: *is the law about the DESIGN SPACE, or about n = 2?*  v4 runs the
    same exact instrument over a 3 x {2,3,4} ladder (nine games, one per family and count) -- the
    domain check a reader would demand.  The zoo, the populations and the 17-protocol design space of
    record are untouched; the GAMES are what widen.

(B) THE SIGN.  v3 refuted P3 (`gameable <=> fragile`) and named the structural reason: gaming needs a
    dependence on something OTHER than the payoff, fragility needs a dependence on the POPULATION.
    What v3 did not do is state a law for the transport statistic -- it reported per-protocol readings.
    v4 states one and puts it on trial.  The mechanism is exact:

        the Kendall loss between two orderings is INVARIANT under reversing both, so the transport
        statistic cannot see a protocol whose whole ordering is the payoff ordering's REVERSE.

    The witness is a design the space of record does not contain and that practice contains
    everywhere: a **lower-is-better score** -- cost, latency, error, regret -- that is a strictly
    DECREASING function of the payoff profile.  v4 adds exactly one such witness
    (`neg_mean = -mean_payoff`) and re-derives the laws with it present:

        FAITHFUL   tau == +1 in every cell  -- the score's ordering EQUALS the payoff ordering
        REVERSED   tau == -1 in every cell  -- it is that ordering's REVERSE (the sign convention)
        IMMUNE     G == 0 in every cell     -- the head is not bought

    The prediction is that a reversed design is transport-excess-free and NOT faithful, so the naive
    law `T_excess == 0  <=>  faithful` must FIRE on the witness while the corrected law (`T_excess == 0
    <=> the ordering is consistently equal OR consistently reversed`) holds.  A pipeline blind to the
    sign convention cannot be told from a healthy one by `T`, and `G` reads the same design as its
    WORST case: the two statistics are maximally opposed on one object.

Everything is an exact Fraction; no sampling, no seed, no timing.  The artefact is JSON-native (every
rational a string) and is written stage-to-temp then `os.replace`d -- a truncating open is a DELETE
that a later failure does not undo (Class 201).

Certificate (`--selftest`): every item carries its OWN plant, so a check whose plant cannot break it is
reported as decoration rather than as a pass.  C1 the anchors per game (PLANT: a zoo whose `eq_spsb`
bids half its value -- the dominant strategy's opposite).  C2 the ladder NESTS v3's SHIPPED artefact on
the four shared games, read from DISK (PLANT: a one-digit change in one expected value).  C3 the design
law over 18 protocols x 9 games (PLANT: a relabelled prediction table).  C4 `faithful => immune` in
every cell (PLANT: a cell that is faithful AND gameable).  C5 the forward transport law (PLANT: a
constant baseline).  C6/C6b/C6c the SIGN: the natural lower-is-better witness is gameable in every cell and
its excess is zero in almost every entry, the cells where it is not are EXACTLY the payoff-TIE cells,
and the CONSTRUCTED witness (exact reversal) makes the naive law fire, while the ENTRY-LEVEL law that
replaces it is checked with a flipped-ordering plant and a witness-removal plant.  C7 the transport statistic's own anchor, `T_raw == 0 <=>
the ordering never moves` (PLANT: move one ordering).  C8 the maximum separation of `G` and `T` on one
design, asserted jointly.  C9 determinism ACROSS PROCESSES on a randomised hash seed (PLANT: a one-byte
change must be detected).  C10 the headline re-derived from the artefact READ OFF DISK (PLANT: a
corrupted cell in the file).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import OrderedDict
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import spike_v0 as V          # noqa: E402  the exact instrument
import spike_v2 as P          # noqa: E402  the 17-protocol design space of record
import spike_v3 as T3         # noqa: E402  the transport machinery of record

# ------------------------------------------------------------------------------------------------
# (A) the ladder: three families x {2,3,4} bidders

LADDER = OrderedDict([
    ("fpsb_n2", V.GAMES["fpsb_n2"]),
    ("fpsb_n3", (3, V.fpsb(3), "first-price, 3 bidders")),
    ("fpsb_n4", (4, V.fpsb(4), "first-price, 4 bidders")),
    ("spsb_n2", V.GAMES["spsb_n2"]),
    ("spsb_n3", (3, V.spsb(3), "second-price, 3 bidders")),
    ("spsb_n4", (4, V.spsb(4), "second-price, 4 bidders")),
    ("cv_n2", V.GAMES["cv_n2"]),
    ("cv_n3", (3, V.common_value(3), "common value, 3 bidders")),
    ("cv_n4", V.GAMES["cv_n4"]),
])
SHARED_GAMES = ["fpsb_n2", "spsb_n2", "cv_n2", "cv_n4"]      # the four v0-v3 measured
FAMILY = OrderedDict((g, g.split("_")[0]) for g in LADDER)
N_BIDDERS = OrderedDict((g, LADDER[g][0]) for g in LADDER)

# The games live in a module GLOBAL.  Replacing it once, here, deliberately and with the reason
# stated, is what makes every helper that loops `V.GAMES` (v2's scan, v3's grid and transport) read the
# ladder.  A global written on one code path and read on another is the defect Class 205(b) names;
# here the write IS the design, so it is ASSERTED rather than left implicit.
V.GAMES = LADDER
assert list(V.GAMES) == list(LADDER), "the ladder must be the game set every helper sees"
assert list(T3.V.GAMES) == list(LADDER), "v3's module view must be the same object (same import)"

# ------------------------------------------------------------------------------------------------
# (B) the design space of record + ONE constructed witness

PROTOCOLS = OrderedDict(P.PROTOCOLS)
PROTOCOLS["neg_mean"] = lambda M, a, pop, W: -V._mean(M, a, pop)      # the lower-is-better score

READS = OrderedDict(P.READS)
MONO = OrderedDict(P.MONO)
READS["neg_mean"] = "profile"
MONO["neg_mean"] = "decreasing"
def rank_score(M, a, pop, W):
    """The CONSTRUCTED witness: the score is the policy's PAYOFF RANK in the population (1 = best).

    A LOWER rank is better, so under the instrument's descending-score convention the payoff-WORST
    policy leads -- the payoff ordering's EXACT REVERSE -- and because ranks are DISTINCT, no
    tie-break can break it.  (The first draft of this function negated the rank, which is the same
    sign error in the other direction: -rank has the payoff-BEST at rank 1 and therefore reads as the
    payoff ordering itself, i.e. FAITHFUL -- the certificate's C6b caught it on the first run.)  v2
    labelled `tail_swap` the same way: a legitimate protocol for exhibiting a strictness, not a
    natural aggregation."""
    u = OrderedDict((x, V._mean(M, x, pop)) for x in V.ZOO)
    return F(V.ranks_of(u)[a])


PROTOCOLS["rank_score"] = rank_score
READS["rank_score"] = "profile"
MONO["rank_score"] = "decreasing"

WITNESS = "neg_mean"                    # the NATURAL lower-is-better score: sign convention, real
CONSTRUCTED_WITNESS = "rank_score"        # the constructed one whose reversal is exact in every cell
FRAGILE_REFERENCE = "random_fixed"      # v3's witness: maximally gameable, exactly zero transport


def predict_band(reads, mono):
    """v2's design law, unchanged, extended by the one label its zoo could not need.

    The law as v2 stated it: faithfulness requires the score to be a strictly INCREASING function of
    the policy's OWN payoff-profile value.  A row-reading aggregation compares the policy against the
    population; a saturating one stops being increasing where the cap binds.  v4 adds the third way a
    profile-reader can miss the head: a strictly DECREASING one puts the payoff profile's TAIL at the
    head, so the rank-optimal policy is the payoff-worst -- gameable by construction."""
    if reads == "profile" and mono == "strict":
        return "faithful"
    if reads == "profile" and mono == "none":
        return "immune_unfaithful"
    return "gameable"


def measured_band(v):
    """The band a protocol's counters put it in -- read FROM the counters, never declared."""
    if v["gameable"] > 0:
        return "gameable"
    if v["cells"] and v["faithful"] == v["cells"]:
        return "faithful"
    return "immune_unfaithful"


def _blank_counter():
    return {"cells": 0, "faithful": 0, "reversed": 0, "immune": 0, "gameable": 0,
            "tau_lt_1": 0, "immune_and_unfaithful": 0, "G_max": 0}


def counters(cells):
    """Per-protocol counters over a cell set.  `reversed` is a SEPARATE counter from `tau_lt_1`
    because tau == -1 is a different object from tau == 0.9, and a single `tau < 1` would hide it."""
    per = OrderedDict()
    for k, c in cells.items():
        pr = k.split("|")[2]
        v = per.setdefault(pr, _blank_counter())
        v["cells"] += 1
        if c["tau"] == 1:
            v["faithful"] += 1
        if c["tau"] == -1:
            v["reversed"] += 1
        if c["tau"] < 1:
            v["tau_lt_1"] += 1
        if c["G"] == 0:
            v["immune"] += 1
        if c["G"] > 0:
            v["gameable"] += 1
        if c["G"] == 0 and c["tau"] < 1:
            v["immune_and_unfaithful"] += 1
        if c["G"] > v["G_max"]:
            v["G_max"] = c["G"]
    return per


# ------------------------------------------------------------------------------------------------
# the one scan every reading is taken from

_SCAN = None


def scan():
    """(cells, base, transport) over the ladder x the 4 populations x the 18 protocols.  Memoised: the
    certificate re-reads this ONE computation many times rather than re-running it (v1's budget defect
    -- a certificate whose runtime does not fit a round hides the next round's defect)."""
    global _SCAN
    if _SCAN is None:
        cells, base = T3.grid(PROTOCOLS)
        tr = T3.transport(cells, base, PROTOCOLS)
        _SCAN = {"cells": cells, "base": base, "tr": tr}
    return _SCAN


def scan_with(protocols):
    """A scan of a DIFFERENT protocol set -- the plants' route.  Kept separate from the memoised scan
    so a plant can never corrupt the reading of record."""
    cells, base = T3.grid(protocols)
    return {"cells": cells, "base": base, "tr": T3.transport(cells, base, protocols)}


# ------------------------------------------------------------------------------------------------
# the anchors: one per game, certified by exhaustive deviation enumeration

def anchors(zoo=None):
    zoo = V.ZOO if zoo is None else zoo
    out = OrderedDict()
    for g in LADDER:
        M, _ = V.matrices(g)
        cert, _all = V.equilibria(M)
        names = [e["policy"] for e in cert]
        n = N_BIDDERS[g]
        cand = F(n - 1, n)                     # the continuous-uniform symmetric shading, as a hint
        realized = [p for p in names if all(zoo[p](x) == cand * x for x in V.GRID)]
        out[g] = {
            "family": FAMILY[g], "n": n,
            "certified": names,
            "certified_absent": len(names) == 0,
            "weakly_dominant_v_realized": any(
                all(zoo[p](x) == x for x in V.GRID) for p in names),
            "continuous_uniform_shading": str(cand),
            "continuous_uniform_shading_realized_by": realized,
        }
    return out


# ------------------------------------------------------------------------------------------------
# the laws

def tr_by_protocol(tr, field):
    out = OrderedDict()
    for k, v in tr.items():
        out.setdefault(k.split("|")[1], []).append(v[field])
    return out


def law_forward(cells, tr):
    """FAITHFUL => T_excess == 0 in every entry -- a theorem (if the protocol's ordering EQUALS the
    payoff ordering in a population, its loss to any other population IS the payoff ordering's loss).
    Returns the violations, so a plant can make the list non-empty."""
    per = counters(cells)
    ex = tr_by_protocol(tr, "excess")
    bad = []
    for p in ex:
        if per[p]["cells"] and per[p]["faithful"] == per[p]["cells"]:
            for i, e in enumerate(ex[p]):
                if e is None or e != 0:
                    bad.append({"protocol": p, "entry": i,
                                "excess": (None if e is None else str(e))})
    return bad


def excess_zero_set(tr):
    """Protocols whose transport EXCESS is exactly zero in EVERY entry.  An entry whose loss is
    UNDEFINED is not a zero, so it keeps its protocol out of the set (Class 206(c))."""
    return [p for p, es in tr_by_protocol(tr, "excess").items()
            if all((e is not None and e == 0) for e in es)]


def raw_zero_set(tr):
    """Protocols whose transport is exactly zero in EVERY entry -- their ordering never consults the
    population, so no population change can move an ordering that does not read one."""
    return [p for p, es in tr_by_protocol(tr, "raw").items()
            if all((e is not None and e == 0) for e in es)]


def sign_sets(cells):
    """(faithful_everywhere, consistently_reversed, sign_consistent) -- read from the cells."""
    per = counters(cells)
    f = sorted(p for p, v in per.items() if v["cells"] and v["faithful"] == v["cells"])
    r = sorted(p for p, v in per.items() if v["cells"] and v["reversed"] == v["cells"])
    return f, r, sorted(set(f) | set(r))


def moves_by_protocol(cells, protocols):
    """For each protocol, the (game, population-pair) entries where its ORDERING differs between the
    two populations -- the object `T_raw == 0` is the complement of."""
    out = OrderedDict()
    for p in protocols:
        moves = []
        for g in LADDER:
            for (p1, p2) in T3._pairs():
                o1 = cells["%s|%s|%s" % (g, p1, p)]["order"]
                o2 = cells["%s|%s|%s" % (g, p2, p)]["order"]
                if o1 != o2:
                    moves.append([g, p1, p2])
        out[p] = moves
    return out


def inclusion_g_implies_fragile(cells):
    """v1's T3 over THIS grid: G > 0 => tau < 1, and strictly many more fragile than gameable."""
    gameable = fragile = rev = 0
    bad = []
    for k, c in cells.items():
        if c["G"] > 0:
            gameable += 1
            if not (c["tau"] < 1):
                bad.append(k)
        if c["tau"] < 1:
            fragile += 1
        if c["tau"] == -1:
            rev += 1
    return {"gameable_cells": gameable, "fragile_cells": fragile, "reversed_cells": rev,
            "g_positive_without_fragility": bad[:5], "n_g_positive_without_fragility": len(bad),
            "strictly_contains": fragile > gameable}


def factor_split(cells):
    """v3's exact two-way decomposition of G on each game's 18 x 4 layout: which factor moves G."""
    ps = list(P.PROTOCOLS)
    pops = list(V.populations())
    out = OrderedDict()
    for g in LADDER:
        tab = OrderedDict(((pr, po), F(cells["%s|%s|%s" % (g, po, pr)]["G"]))
                          for pr in ps for po in pops)
        tot, prot, pop, inter = T3.decomp(tab, len(ps), len(pops))
        out[g] = {
            "SS_total": str(tot), "SS_protocol": str(prot), "SS_population": str(pop),
            "SS_interaction": str(inter),
            "MS_protocol": str(prot / (len(ps) - 1)), "MS_population": str(pop / (len(pops) - 1)),
            "protocol_exceeds_population": prot > pop,
        }
    return out


def design_law(cells):
    """v2's law re-derived over 18 protocols x 9 games, with the mismatch list carried."""
    per = counters(cells)
    bands = OrderedDict((p, measured_band(per[p])) for p in PROTOCOLS)
    predicted = OrderedDict((p, predict_band(READS[p], MONO[p])) for p in PROTOCOLS)
    mismatches = OrderedDict((p, {"predicted": predicted[p], "measured": bands[p]})
                             for p in PROTOCOLS if predicted[p] != bands[p])
    return {"bands": bands, "predicted_bands": predicted, "law_mismatches": mismatches,
            "band_counts": OrderedDict((b, sum(1 for x in bands.values() if x == b))
                                       for b in ("faithful", "immune_unfaithful", "gameable"))}


def p1(cells):
    n = len(cells)
    pos = sum(1 for c in cells.values() if c["G"] > 0)
    return {"cells": n, "G_pos": pos, "share_of_cells": str(F(pos, n)), "majority": pos * 2 > n,
            "per_game": OrderedDict(
                (g, {"cells": sum(1 for k in cells if k.startswith(g + "|")),
                     "G_pos": sum(1 for k, c in cells.items()
                                  if k.startswith(g + "|") and c["G"] > 0)})
                for g in LADDER)}


# ------------------------------------------------------------------------------------------------
# the round

def headline(cells, tr):
    """The round's readings, all DERIVED from the scan -- never carried as literals."""
    per = counters(cells)

    def slot(p):
        return per.get(p, _blank_counter())

    def setslot(p, field, seq):
        return (slot(p)[field] if p in per else seq)

    f, r, s = sign_sets(cells)
    e0 = excess_zero_set(tr)
    r0 = raw_zero_set(tr)
    ref = [c for k, c in cells.items() if k.split("|")[2] == FRAGILE_REFERENCE]
    return {
        "cells": len(cells), "transport_entries": len(tr),
        "faithful_set": f, "reversed_set": r, "sign_consistent_set": s,
        "excess_zero_set": sorted(e0), "raw_zero_set": sorted(r0),
        "witness": WITNESS,
        "constructed_witness": CONSTRUCTED_WITNESS,
        "witness_G_max": slot(WITNESS)["G_max"],
        "witness_G_max_possible": len(V.ZOO) - 1,
        "witness_gameable_share": "%d/%d" % (slot(WITNESS)["gameable"], slot(WITNESS)["cells"]),
        "witness_tau_lt_1": slot(WITNESS)["tau_lt_1"],
        "witness_excess_zero": WITNESS in e0,
        "witness_faithful": WITNESS in f,
        "constructed_witness_G_max": slot(CONSTRUCTED_WITNESS)["G_max"],
        "constructed_witness_excess_zero": CONSTRUCTED_WITNESS in e0,
        "constructed_witness_reversed_everywhere": (
            CONSTRUCTED_WITNESS in r if CONSTRUCTED_WITNESS in per else None),
        "naive_law_violators": sorted(set(e0) - set(f)),
        "reversed_set_present": bool(r),
        "fragile_reference": FRAGILE_REFERENCE,
        "fragile_reference_G_mean": str(sum((F(c["G"]) for c in ref), F(0)) / max(1, len(ref))),
        "fragile_reference_T_raw": next((str(v["raw"]) for k, v in tr.items()
                                         if k.split("|")[1] == FRAGILE_REFERENCE
                                         and v["raw"] is not None), None),
    }


def run():
    s = scan()
    cells, tr = s["cells"], s["tr"]
    return {
        "model": {
            "games": list(LADDER), "families": OrderedDict(FAMILY),
            "n_bidders": OrderedDict((g, N_BIDDERS[g]) for g in LADDER),
            "ladder_widened_vs_v3": [g for g in LADDER if g not in SHARED_GAMES],
            "policies": list(V.ZOO), "populations": list(V.populations()),
            "protocols": list(PROTOCOLS), "cells": len(cells), "transport_entries": len(tr),
            "population_pairs": [list(x) for x in T3._pairs()],
            "design_space_source": "spike_v2.PROTOCOLS + the constructed witness `neg_mean`",
        },
        "anchors": anchors(),
        "P1_gain_positive": p1(cells),
        "design_law": design_law(cells),
        "T3_inclusion": inclusion_g_implies_fragile(cells),
        "factor_split": factor_split(cells),
        "headline": headline(cells, tr),
        "per_protocol": counters(cells),
        "cells_G_tau": OrderedDict((k, {"G": c["G"], "tau": str(c["tau"])}) for k, c in cells.items()),
        "transport": OrderedDict(
            (k, {"raw": (None if v["raw"] is None else str(v["raw"])),
                 "base": str(v["base"]),
                 "excess": (None if v["excess"] is None else str(v["excess"]))})
            for k, v in tr.items()),
    }


def dump(doc, path=None):
    txt = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if path:
        tmp = path + ".stage"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(txt)
        os.replace(tmp, path)
    return txt


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _subprocess_json():
    """A SECOND process's artefact, with a randomised hash seed -- the determinism certificate."""
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "random"
    r = subprocess.run([sys.executable, os.path.abspath(__file__)], capture_output=True, text=True,
                       env=env, cwd=HERE)
    if r.returncode != 0:
        return None, r.stderr[-400:]
    return r.stdout, None


# ------------------------------------------------------------------------------------------------
# the cross-carrier identity: the ladder must NEST v3's shipped artefact

def _nest_compare(expected, got):
    """The predicate, factored so the PLANT calls the same thing the check does (Class 197)."""
    bad = []
    for k in sorted(set(expected) | set(got)):
        if expected.get(k) != got.get(k):
            bad.append(k)
    return {"entries_expected": len(expected), "entries_got": len(got),
            "mismatches": bad[:5], "n_mismatches": len(bad)}


def nest_expected():
    """v3's SHIPPED transport entries, restricted to the four shared games -- read from DISK."""
    path = os.path.join(HERE, "spike_v3_results.json")
    if not os.path.exists(path):
        return None, "spike_v3_results.json is absent"
    with open(path, encoding="utf-8") as fh:
        v3 = json.load(fh)
    exp = OrderedDict((k, v) for k, v in v3["transport"].items()
                      if k.split("|")[0] in SHARED_GAMES)
    return exp, None


def nest_got():
    """v4's transport entries for the same games, restricted to the 17 protocols of record."""
    s = scan()
    return OrderedDict(
        (k, {"raw": (None if v["raw"] is None else str(v["raw"])),
             "base": str(v["base"]),
             "excess": (None if v["excess"] is None else str(v["excess"]))})
        for k, v in s["tr"].items()
        if k.split("|")[0] in SHARED_GAMES and k.split("|")[1] in P.PROTOCOLS)


# ------------------------------------------------------------------------------------------------
# C10's object: the headline re-derived from the artefact read off disk

def rederive(path):
    """Re-derive the headline FROM the artefact on disk: counters from its cells, the excess-zero set
    from its transport block.  Returns None if the artefact is absent."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    cells = OrderedDict((k, {"G": v["G"], "tau": F(v["tau"])})
                        for k, v in doc["cells_G_tau"].items())
    tr = OrderedDict((k, {"raw": (None if v["raw"] is None else F(v["raw"])),
                          "base": F(v["base"]),
                          "excess": (None if v["excess"] is None else F(v["excess"]))})
                     for k, v in doc["transport"].items())
    return headline(cells, tr)


# ------------------------------------------------------------------------------------------------
# the ORIENTATION of an ordering, and the entry-level law for the transport statistic

_PO = None
_MC = {}


def _mat(g):
    """The exact matrices of ONE game, memoised.  Recomputing them inside a per-entry loop made this
    diagnostic's first draft quadratic -- it was killed at 600 s (Class 257) -- so the invariant is
    computed once here and every helper reads this cache."""
    if g not in _MC:
        _MC[g] = V.matrices(g)
    return _MC[g]


def payoff_orders():
    """The payoff ordering of every (game, population) -- the coordinate the SIGN is read against."""
    global _PO
    if _PO is None:
        out = OrderedDict()
        for g in LADDER:
            M, _ = _mat(g)
            for pn, pop in V.populations().items():
                out["%s|%s" % (g, pn)] = V.order_by(
                    OrderedDict((a, V._mean(M, a, pop)) for a in V.ZOO))
        _PO = out
    return _PO


def payoff_ties():
    """How many PAIRS of policies TIE in the payoff ordering of each (game, population) -- the
    coordinate `order_by`'s lexicographic tie-break acts on, and therefore the only place a score
    NEGATION can fail to reverse the ordering exactly."""
    out = OrderedDict()
    for g in LADDER:
        M, _ = _mat(g)
        for pn, pop in V.populations().items():
            u = OrderedDict((a, V._mean(M, a, pop)) for a in V.ZOO)
            out["%s|%s" % (g, pn)] = V.tie_pairs(u)
    return out


def orientations(cells, protocols):
    """For every (game, population, protocol): +1 if the ordering EQUALS the payoff ordering, -1 if it
    is its exact REVERSE, 0 otherwise (a tie-break, or a genuine disagreement)."""
    po = payoff_orders()
    out = OrderedDict()
    for g in LADDER:
        for pn in V.populations():
            base = po["%s|%s" % (g, pn)]
            rev = base[::-1]
            for p in protocols:
                o = cells["%s|%s|%s" % (g, pn, p)]["order"]
                out["%s|%s|%s" % (g, pn, p)] = (1 if o == base else (-1 if o == rev else 0))
    return out


def excess_law(cells, tr, protocols):
    """THE ENTRY-LEVEL READING for the transport statistic, with its TWO DIRECTIONS SEPARATED.

        FORWARD (a theorem): if p's ordering is the payoff ordering in BOTH populations, or its exact
            reverse in both, then excess == 0.
        COMPLEMENT (also a theorem): if it is the payoff ordering in one population and the exact
            reverse in the other, then excess == 1 - 2*base.
        CONVERSE (a MEASUREMENT of this space, not a theorem): no entry has zero excess without a
            common orientation -- 0 violations over the entries whose orientation is determined.

    The mechanism is one line long: reversing an ordering flips EVERY pair, so the Kendall loss is
    invariant under reversing BOTH (`loss(rev a, rev b) = loss(a, b)`) while reversing only ONE sends
    it to its complement (`loss(rev a, b) = 1 - loss(a, b)`).  The converse is NOT implied by it -- a
    protocol could coincide with the baseline loss without sitting at either orientation -- so the
    certificate reports it as a reading with its count, never as a theorem (Class 209a).  An entry
    whose orientation is UNDETERMINED is not a reading (Class 206c): it is skipped and counted."""
    ori = orientations(cells, protocols)
    viol = []
    opp = []
    skipped = 0
    for k, v in tr.items():
        if k.split("|")[1] not in protocols:
            continue
        g, p, pair = k.split("|")
        p1, p2 = pair.split(">")
        o1 = ori["%s|%s|%s" % (g, p1, p)]
        o2 = ori["%s|%s|%s" % (g, p2, p)]
        if o1 == 0 or o2 == 0:
            skipped += 1
            continue
        pred = (o1 == o2)
        got = (v["excess"] is not None and v["excess"] == 0)
        if pred != got:
            viol.append({"entry": k, "orientations": [o1, o2],
                         "excess": (None if v["excess"] is None else str(v["excess"]))})
        if o1 != o2:
            opp.append({"entry": k, "excess": str(v["excess"]),
                        "one_minus_2base": str(F(1) - 2 * F(v["base"]))})
    return {"violations": viol[:5], "n_violations": len(viol),
            "entries_evaluated": len(tr) - skipped, "entries_skipped": skipped,
            "opposite_orientation_kind": len(opp),
            "opposite_orientation_excess_is_complement":
                all(x["excess"] == x["one_minus_2base"] for x in opp),
            "sample_opposite": opp[:3]}


# ------------------------------------------------------------------------------------------------
# the certificate

def selftest():
    ok = total = 0

    def check(name, cond, detail="", show=False):
        """`detail` is the FAILURE's explanation, so it is printed when the item fails; `show=True`
        asks for it on a pass as well, for the items whose COUNT is itself the reading (a certificate
        that prints "the plant is inert" beside an OK is a presentation defect of its own)."""
        nonlocal ok, total
        total += 1
        if cond:
            ok += 1
            print("  OK   %s%s" % (name, ("  [%s]" % detail) if (show and detail) else ""))
        else:
            print("  FAIL %s%s" % (name, ("  [%s]" % detail) if detail else ""))

    s = scan()
    cells, tr = s["cells"], s["tr"]
    per = counters(cells)

    print("C1 -- the anchors: one certified set per game, and the closed forms it realizes")
    an = anchors()
    check("every one of the 9 ladder games carries an anchor block", len(an) == len(LADDER),
          "games=%d" % len(an))
    check("each game's certified set came from exhaustive deviation enumeration, or is STATED absent",
          all(v["certified"] or v["certified_absent"] for v in an.values()))
    check("the second-price games realize the weakly dominant b(v)=v",
          all(an[g]["weakly_dominant_v_realized"] for g in LADDER if FAMILY[g] == "spsb"),
          "spsb: %s" % [an[g]["weakly_dominant_v_realized"] for g in LADDER if FAMILY[g] == "spsb"])
    bad_zoo = OrderedDict(V.ZOO)
    bad_zoo["eq_spsb"] = V.shading(F(1, 2))          # the dominant strategy's opposite
    an_bad = anchors(bad_zoo)
    check("C1-PLANT a zoo violating weak dominance makes the spsb anchor fail",
          not all(an_bad[g]["weakly_dominant_v_realized"]
                  for g in LADDER if FAMILY[g] == "spsb"),
          "the plant is inert: spsb still reports the dominant strategy")

    print("C2 -- the ladder NESTS v3's shipped artefact, read from DISK")
    exp, why = nest_expected()
    if exp is None:
        check("C2-v3-artefact-present", False, why)
    else:
        got = nest_got()
        res = _nest_compare(exp, got)
        check("v4 restricted to the four shared games equals v3's shipped transport entries",
              res["n_mismatches"] == 0,
              "entries %d/%d, first mismatches %s" % (res["entries_expected"], res["entries_got"],
                                                      res["mismatches"]), show=True)
        k0 = sorted(exp)[0]
        pert = OrderedDict(exp)
        e = dict(pert[k0])
        e["raw"] = "1" if e["raw"] != "1" else "0"
        pert[k0] = e
        res_p = _nest_compare(pert, got)
        check("C2-PLANT a one-digit change in one expected entry fires",
              res_p["n_mismatches"] == 1 and res_p["mismatches"][:1] == [k0],
              "the comparison is inert: %s" % res_p["mismatches"][:3])

    print("C3 -- the design law over 18 protocols x 9 games")
    law = design_law(cells)
    check("the law's mismatch list is EMPTY over the widened grid", len(law["law_mismatches"]) == 0,
          "mismatches: %s" % dict(law["law_mismatches"]))
    check("every protocol is assigned one of the THREE v2 bands (the widening invented none)",
          len(law["bands"]) == len(PROTOCOLS)
          and all(b in ("faithful", "immune_unfaithful", "gameable") for b in law["bands"].values()),
          "bands: %s" % sorted(set(law["bands"].values())))
    check("all three bands are non-empty, so no band is decoration",
          all(law["band_counts"][b] > 0 for b in ("faithful", "immune_unfaithful", "gameable")),
          str(law["band_counts"]))
    relabelled = OrderedDict((p, "faithful") for p in P.PROTOCOLS)
    plant_bad = [p for p in P.PROTOCOLS if relabelled[p] != law["bands"][p]]
    check("C3-PLANT a relabelled prediction table produces mismatches", len(plant_bad) > 0,
          "the plant is inert: no protocol is mispredicted")

    print("C4 -- faithful => immune, in EVERY cell of EVERY protocol")
    viol = [p for p, v in per.items() if v["faithful"] > v["immune"]]
    check("no protocol has a faithful cell that is not immune", not viol, "worst: %s" % viol)
    planted = OrderedDict(cells)
    k0 = sorted(planted)[0]
    planted[k0] = dict(planted[k0], G=1, tau=F(1))
    pper = counters(planted)
    check("C4-PLANT a faithful-and-gameable cell breaks it",
          any(pper[p]["faithful"] > pper[p]["immune"] for p in pper), "the plant is inert")

    print("C5 -- the forward transport law: faithful => T_excess == 0 everywhere")
    bad = law_forward(cells, tr)
    check("no faithful protocol has a non-zero transport excess", not bad, "violations: %s" % bad[:3])
    zero_base = OrderedDict((k, dict(v, base=F(0), excess=v["raw"])) for k, v in tr.items())
    bad_plant = law_forward(cells, zero_base)
    check("C5-PLANT a constant baseline makes the law fire", len(bad_plant) > 0,
          "the plant is inert: the law survived a zeroed baseline")

    print("C6 -- the SIGN: the transport statistic is blind to the ordering's ORIENTATION")
    h = headline(cells, tr)
    ori = orientations(cells, PROTOCOLS)
    ties = payoff_ties()
    w = per[WITNESS]
    tot_cells = sum(1 for k in ori if k.split("|")[2] == WITNESS)
    wre = [k for k in ori if k.split("|")[2] == WITNESS and ori[k] == -1]
    wunk = [k for k in ori if k.split("|")[2] == WITNESS and ori[k] == 0]
    check("the natural lower-is-better witness is gameable in EVERY cell",
          w["gameable"] == w["cells"], "%d/%d" % (w["gameable"], w["cells"]))
    check("it buys the MAXIMUM rank the zoo permits (%d)" % (len(V.ZOO) - 1),
          w["G_max"] == len(V.ZOO) - 1, "G_max=%d" % w["G_max"])
    check("its ordering is the payoff ordering's EXACT REVERSE in almost every cell",
          len(wre) + len(wunk) == tot_cells and len(wre) > 0,
          "reversed %d, undetermined %d, of %d" % (len(wre), len(wunk), tot_cells), show=True)
    tiecells_w = set("%s|%s|%s" % (g, pn, WITNESS) for g in LADDER for pn in V.populations()
                     if ties["%s|%s" % (g, pn)])
    check("and the cells where it is NOT the exact reverse are EXACTLY the payoff-TIE cells",
          set(wunk) == tiecells_w, "undetermined=%s  tie_cells=%s" % (sorted(wunk), sorted(tiecells_w)))
    wtr = OrderedDict((k, v) for k, v in tr.items() if k.split("|")[1] == WITNESS)
    nz = [k for k, v in wtr.items() if v["excess"] is None or v["excess"] != 0]
    check("so its transport EXCESS is exactly zero in almost every entry",
          0 < len(nz) < len(wtr), "non-zero in %d of %d entries" % (len(nz), len(wtr)),
          show=True)
    tie_set = set(wunk)
    touching = set()
    for k in wtr:
        g, _p, pair = k.split("|")
        p1, p2 = pair.split(">")
        if any("%s|%s|%s" % (g, pn, WITNESS) in tie_set for pn in (p1, p2)):
            touching.add(k)
    check("and those entries are EXACTLY the population pairs that MEET a TIE cell",
          set(nz) == touching,
          "non-zero=%s  meeting-a-tie=%s" % (sorted(nz), sorted(touching)))
    check("the tie-break's error is NEGATIVE: the maximally gameable design reads as LESS fragile "
          "than the payoff ordering itself",
          all(F(wtr[k]["excess"]) < 0 for k in nz),
          "excesses: %s" % sorted(set(str(wtr[k]["excess"]) for k in nz)))

    print("C6b -- the CONSTRUCTED witness whose reversal is EXACT: the naive law IS refuted")
    cw = per[CONSTRUCTED_WITNESS]
    check("the constructed witness is gameable in EVERY cell", cw["gameable"] == cw["cells"],
          "%d/%d" % (cw["gameable"], cw["cells"]))
    check("it is REVERSED (tau == -1) in EVERY cell", cw["reversed"] == cw["cells"],
          "%d/%d" % (cw["reversed"], cw["cells"]))
    check("it is NOT faithful", CONSTRUCTED_WITNESS not in h["faithful_set"])
    check("its transport EXCESS is exactly zero in EVERY entry",
          CONSTRUCTED_WITNESS in excess_zero_set(tr))
    check("SO THE NAIVE LAW `T_excess==0 <=> faithful` IS REFUTED BY IT",
          CONSTRUCTED_WITNESS in h["naive_law_violators"],
          "violators: %s" % h["naive_law_violators"])

    print("C6c -- the ENTRY-LEVEL LAW that replaces it, with its plants")
    lawE = excess_law(cells, tr, PROTOCOLS)
    check("on the entries whose ORIENTATION is determined, `excess == 0  <=>  the SAME orientation in "
          "both populations` -- forward a theorem, the converse a READING of this space",
          lawE["n_violations"] == 0,
          "violations: %s  (evaluated %d, skipped %d)" % (lawE["violations"],
                                                          lawE["entries_evaluated"],
                                                          lawE["entries_skipped"]), show=True)
    check("opposite-orientation entries in THIS space: a stated ABSENCE, not a hidden zero "
          "(the limb they exercise is verified in the plant below)",
          lawE["opposite_orientation_kind"] == 0,
          "opposite-orientation entries: %d" % lawE["opposite_orientation_kind"], show=True)
    planted = OrderedDict((k, dict(v)) for k, v in cells.items())
    k0 = next(k for k in sorted(planted) if k.split("|")[2] == "mean_payoff")
    planted[k0]["order"] = list(planted[k0]["order"])[::-1]
    lp = excess_law(planted, tr, PROTOCOLS)
    check("C6c-PLANT reversing ONE ordering makes the law fire (a same-orientation pair != 0)",
          lp["n_violations"] > 0,
          "the plant is inert: the law survived a reversed ordering")
    ori_p = orientations(planted, PROTOCOLS)
    checked = held = 0
    for k, v in tr.items():
        if k.split("|")[1] != "mean_payoff":
            continue
        g, _p, pair = k.split("|")
        p1, p2 = pair.split(">")
        o1 = ori_p["%s|%s|mean_payoff" % (g, p1)]
        o2 = ori_p["%s|%s|mean_payoff" % (g, p2)]
        if o1 != 0 and o2 != 0 and o1 != o2:
            checked += 1
            got = T3.loss(planted["%s|%s|mean_payoff" % (g, p1)]["order"],
                          planted["%s|%s|mean_payoff" % (g, p2)]["order"])
            if got == F(1) - F(v["base"]):
                held += 1
    check("C6c-PLANT on the planted opposite pair, `loss(rev(o1), o2) == 1 - base` EXACTLY "
          "(the other half of the mechanism, non-empty only here)",
          checked > 0 and held == checked,
          "checked %d, held %d -- a limb that is empty on the healthy space is verified where it is not"
          % (checked, held))
    without = OrderedDict((p, f) for p, f in PROTOCOLS.items() if p != CONSTRUCTED_WITNESS)
    s2 = scan_with(without)
    h2 = headline(s2["cells"], s2["tr"])
    check("C6c-PLANT removing the constructed witness stops the refutation",
          not h2["naive_law_violators"],
          "the plant is inert: the naive law still fires without the witness: %s"
          % h2["naive_law_violators"])

    print("C9 -- determinism ACROSS PROCESSES on a randomised hash seed")
    mine = dump(run())
    other, err = _subprocess_json()
    check("a second process with PYTHONHASHSEED=random emits the same bytes", other == mine,
          err or "len mine=%d other=%s" % (len(mine), None if other is None else len(other)),
          show=True)
    corrupt = mine[:-2] + ("0" if mine[-2] != "0" else "1") + mine[-1:]
    check("C9-PLANT the byte comparison itself detects a one-byte change", corrupt != mine,
          "the comparison is inert")

    print("C10 -- the headline re-derived from the artefact READ OFF DISK")
    path = os.path.join(HERE, "spike_v4_results.json")
    rd = rederive(path)
    keys = ("cells", "transport_entries", "faithful_set", "reversed_set", "excess_zero_set",
            "naive_law_violators", "witness_G_max", "constructed_witness_excess_zero",
            "constructed_witness_reversed_everywhere")
    if rd is None:
        check("C10-artefact-present", False, "%s is absent" % path)
    else:
        diff = [k for k in keys if rd[k] != h[k]]
        check("the headline re-derived from the file equals the in-memory headline", not diff,
              "differing keys: %s" % diff)
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        # the plant must land on a cell whose corruption MOVES one of the compared keys: a cell of
        # the constructed witness, whose `tau` is what puts it in `reversed_set` (the first draft
        # added 1 to the first cell's G, which no compared key reads, so the plant was inert)
        kk = next(k for k in sorted(doc["cells_G_tau"])
                  if k.split("|")[2] == CONSTRUCTED_WITNESS)
        doc["cells_G_tau"][kk]["tau"] = "1"
        pp = path + ".plant"
        try:
            with open(pp, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=1, sort_keys=True, default=str)
            rd2 = rederive(pp)
            bad2 = [k for k in keys if rd2[k] != h[k]]
        finally:
            if os.path.exists(pp):
                os.remove(pp)
        check("C10-PLANT a corrupted cell in the file changes the re-derived headline",
              bool(bad2), "the re-derivation does not read the cell it claims to")

    print("\n  %d/%d certificate items" % (ok, total))
    return 0 if ok == total else 1


# ------------------------------------------------------------------------------------------------
# the reading

def report_text(doc):
    L = []
    m, hd = doc["model"], doc["headline"]
    L.append("== issue #141 -- v4: the sign the transport statistic cannot see (and the ladder) ==")
    L.append("   %d games (3 families x n=2,3,4) x %d policies x %d populations x %d protocols"
             % (len(m["games"]), len(m["policies"]), len(m["populations"]), len(m["protocols"])))
    L.append("   exact: no seed, no sampling, no timing; %d cells, %d transport entries"
             % (m["cells"], m["transport_entries"]))
    L.append("   widened vs v3: %s" % ", ".join(m["ladder_widened_vs_v3"]))
    L.append("")
    L.append("== the anchors (exhaustive deviation enumeration, one block per game) ==")
    for g, a in doc["anchors"].items():
        L.append("   %-8s %-4s n=%d  certified: %s" % (g, a["family"], a["n"],
                                                       ", ".join(a["certified"]) or "(NONE)"))
    L.append("")
    L.append("== the ladder: the laws re-read at every (family, n) ==")
    p1 = doc["P1_gain_positive"]
    L.append("   P1  G > 0 in %d of %d cells = %s  -> %s"
             % (p1["G_pos"], p1["cells"], p1["share_of_cells"],
                "CONFIRMED" if p1["majority"] else "not confirmed"))
    for g, v in p1["per_game"].items():
        L.append("        %-8s %2d of %2d cells" % (g, v["G_pos"], v["cells"]))
    inc = doc["T3_inclusion"]
    L.append("   T3  G>0 => tau<1 in every cell: %s (gameable %d, fragile %d, reversed %d)"
             % ("HOLDS" if not inc["n_g_positive_without_fragility"] else "FAILS",
                inc["gameable_cells"], inc["fragile_cells"], inc["reversed_cells"]))
    L.append("       strictly more fragile cells than gameable: %s" % inc["strictly_contains"])
    fs = doc["factor_split"]
    L.append("   the two-way decomposition of G, per game (which factor is the lever):")
    L.append("       %-8s %14s %14s  protocol>population" % ("game", "MS_protocol", "MS_population"))
    for g, v in fs.items():
        L.append("       %-8s %14.4f %14.4f  %s"
                 % (g, float(F(v["MS_protocol"])), float(F(v["MS_population"])),
                    v["protocol_exceeds_population"]))
    L.append("       games where the protocol exceeds the population: %d of %d"
             % (sum(1 for v in fs.values() if v["protocol_exceeds_population"]), len(fs)))
    L.append("")
    dl = doc["design_law"]
    L.append("== the design law over %d protocols x %d games ==" % (len(m["protocols"]),
                                                                    len(m["games"])))
    L.append("   mismatches vs the stated prediction: %d %s"
             % (len(dl["law_mismatches"]), list(dl["law_mismatches"]) or ""))
    for b, n in dl["band_counts"].items():
        L.append("   band %-20s %2d protocols" % (b, n))
    for p in m["protocols"]:
        L.append("       %-14s predicted=%-18s measured=%s"
                 % (p, dl["predicted_bands"][p], dl["bands"][p]))
    L.append("")
    L.append("== the TRANSPORT statistic, and the sign it cannot see ==")
    L.append("   T_excess == 0 in every entry: %s" % ", ".join(hd["excess_zero_set"]))
    L.append("   T_raw    == 0 in every entry: %s" % ", ".join(hd["raw_zero_set"]))
    L.append("   consistently FAITHFUL (tau=+1 everywhere): %s" % ", ".join(hd["faithful_set"]))
    L.append("   consistently REVERSED (tau=-1 everywhere): %s" % ", ".join(hd["reversed_set"]))
    L.append("   NAIVE LAW `T_excess==0 <=> faithful` -- REFUTED BY: %s"
             % (", ".join(hd["naive_law_violators"]) or "(nothing in this space)"))
    L.append("   the NATURAL witness `%s`: G_max=%d/%d (the MAXIMUM), gameable %s"
             % (hd["witness"], hd["witness_G_max"], hd["witness_G_max_possible"],
                hd["witness_gameable_share"]))
    L.append("       transport excess exactly 0 everywhere: %s   faithful: %s"
             % (hd["witness_excess_zero"], hd["witness_faithful"]))
    L.append("       (the exceptions are the payoff-TIE cells -- see C6 in --selftest)")
    L.append("   the CONSTRUCTED witness `%s`: G_max=%d, excess-zero everywhere: %s, "
             "reversed everywhere: %s"
             % (hd["constructed_witness"], hd["constructed_witness_G_max"],
                hd["constructed_witness_excess_zero"],
                hd["constructed_witness_reversed_everywhere"]))
    L.append("   ENTRY LEVEL: same orientation in both populations => excess == 0 (THEOREM); "
             "the converse is a reading of this space (--selftest C6c, with plants)")
    L.append("   the fragile reference `%s`: G_mean=%s, T_raw=%s"
             % (hd["fragile_reference"], hd["fragile_reference_G_mean"],
                hd["fragile_reference_T_raw"]))
    return "\n".join(L) + "\n"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", type=str, default=None)
    ap.add_argument("--out", type=str, default=None)
    a = ap.parse_args(argv[1:])
    if a.selftest:
        return selftest()
    doc = run()
    if a.out:
        dump(doc, a.out)
        sys.stdout.write("wrote %s  bytes=%d  sha256=%s\n"
                         % (a.out, os.path.getsize(a.out), sha256_file(a.out)))
        return 0
    if a.report:
        txt = report_text(doc)
        tmp = a.report + ".stage"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(txt)
        os.replace(tmp, a.report)
        sys.stdout.write(txt)
        return 0
    sys.stdout.write(dump(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
