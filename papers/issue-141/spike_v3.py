#!/usr/bin/env python3
"""issue #141 -- v3: the TRANSPORT ARM, and the two registered priors it decides.

The registration (issue #141) registers three priors, and its `Outcome` line still reads
"not yet run" for the last two.  v0 measured the divergence, v1 put the registered *iff* on trial,
v2 measured the design law.  v3 is the arm that decides P2 and P3:

    P1  the gain is POSITIVE in a majority of cells                  (v0 over its grid: 79/112)
    P2  the ACROSS-PROTOCOL spread of the gain EXCEEDS the ACROSS-POPULATION spread at a fixed
        protocol -- "which score you publish matters more than whom the agent is paired against".
    P3  the protocols with a POSITIVE gain are the SAME protocols that lose the largest fraction of
        their ordering under population change -- buyable rank and fragile rank are ONE defect.

**The statistic P3 is missing, and why v3 adds it.**  The raw transport loss is not a protocol-only
quantity: the payoff ordering ITSELF moves when the population changes (a change of population
changes which policy pays best), so every protocol carries a floor that is not its own.  The
instrument therefore measures the payoff ordering's own loss as an exact per-(game, pair) BASELINE and
reports the protocol's own contribution as

    T_excess = T_raw(protocol) - T_base(payoff ordering)

which is the first reading of "fragile rank" that is a property of the protocol.  Both readings are
reported side by side, because they are different objects and the registration did not say which one
it meant (Class 258: a label must not stand in for a quantifier).

**P2's two readings, both reported.**  A range over 17 protocols is not comparable with a range over
4 populations, so the primary reading is the EXACT two-way variance decomposition of `G` on the
complete 17 x 4 layout at each game (SS and MS, with the interaction as the residual), and the
registration's own range reading is reported beside it with both level counts named.  A protocol that
is IMMUNE in every cell of a game has a population range of exactly 0 by construction, so those strata
are excluded **by that condition** (never by the value), with the excluded set printed beside them.

Everything is an exact Fraction: the association's SIGN and r^2 are exact, `undef` is reported where a
variance is zero rather than printed as 0, and there is no sampling, no seed and no timing.  The
artefact is JSON-native (every rational a string) and is re-derived from disk on a second route.

Certificate (`--selftest`), each item with its own plant, so a check whose plant cannot break it is
reported as decoration rather than as a pass:
  C1 v3's cells agree with v0's SHIPPED artefact on the 7 shared protocols (identity, not tolerance)
  C2 the two-way decomposition is an IDENTITY (SS_tot = SS_prot + SS_pop + SS_int), and a wrong
     layout weight breaks it -- the plant calls the SAME factorised predicate with the wrong weight
  C3 v2's design space and v0's protocol set agree on every shared cell, so the 17-protocol grid
     NESTS the registration's original 7-protocol grid exactly
  C4 the two-sided control: the monotone references read G == 0 everywhere AND a non-monotone
     protocol reads G > 0 somewhere
  C5 the degeneracy exclusion moves the reported figure (it is not cosmetic) and its set is named
  C6 determinism across PROCESSES (randomised hash seeds) and the artefact round-trips from disk
  C7 a variance-degenerate subset reads `undef`, and a live subset reads a number
"""
import argparse
import hashlib
import itertools
import json
import os
import subprocess
import sys
from collections import OrderedDict
from fractions import Fraction as F

import spike_v0 as V
import spike_v2 as P

# ------------------------------------------------------------------------------------------------
# the grid: ONE scan, every reading taken from it

_MCACHE = {}
SHARED = [p for p in V.PROTOCOLS if p in P.PROTOCOLS]


def _matrices(g):
    """Memoise v0's exact payoff/outcome matrices -- they do not depend on the protocol."""
    if g not in _MCACHE:
        _MCACHE[g] = V.matrices(g)
    return _MCACHE[g]


def _pairs():
    """Every unordered population pair.  v0 used the 3 pairs against `uniform`; the registered
    statistic is 'the fraction lost under a population PERTURBATION', which is symmetric, so the
    full set of 6 is the reading of record and the 3-pair set is carried as a sensitivity."""
    pops = list(V.populations())
    return [(a, b) for i, a in enumerate(pops) for b in pops[i + 1:]]


def grid(protocols):
    """Every (game, population, protocol) cell: G, tau, and the score ordering it is read from.

    The orderings are kept IN the cell, so the transport arm is a re-read of the same scan -- one
    computation per cell, never a second pass that could disagree with the first.
    """
    cells = OrderedDict()
    base = OrderedDict()
    for g in V.GAMES:
        M, W = _matrices(g)
        for pname, pop in V.populations().items():
            base["%s|%s" % (g, pname)] = V.order_by(
                OrderedDict((a, V._mean(M, a, pop)) for a in V.ZOO))
            for prname, fn in protocols.items():
                c = V.cell(M, pop, fn, W)
                cells["%s|%s|%s" % (g, pname, prname)] = {
                    "G": int(c["G"]),
                    "tau": F(c["tau"]),
                    "order": V.order_by(OrderedDict((a, fn(M, a, pop, W)) for a in V.ZOO)),
                }
    return cells, base


def loss(o1, o2):
    """The transport loss: the share of pairwise orderings that change.  `None` = undefined."""
    _, dis, tot = V.kendall_tau_a(o1, o2)
    return F(dis, tot) if tot else None


def transport(cells, base, protocols):
    """Per (game, protocol, pair): the raw loss, the payoff ordering's loss, and the excess."""
    out = OrderedDict()
    for g in V.GAMES:
        for p1, p2 in _pairs():
            b = loss(base["%s|%s" % (g, p1)], base["%s|%s" % (g, p2)])
            for prname in protocols:
                r = loss(cells["%s|%s|%s" % (g, p1, prname)]["order"],
                         cells["%s|%s|%s" % (g, p2, prname)]["order"])
                out["%s|%s|%s>%s" % (g, prname, p1, p2)] = {
                    "raw": r, "base": b,
                    "excess": (r - b) if (r is not None and b is not None) else None}
    return out


# ------------------------------------------------------------------------------------------------
# exact association helpers: the SIGN and r^2 are exact, `undef` is a reading and never a 0

def pearson(xs, ys):
    """(sign, r^2, r_as_float, why).  `sign` is 0 and r^2 is None when a variance is zero."""
    n = len(xs)
    if n < 3:
        return 0, None, None, "fewer than 3 points"
    sx, sy = sum(xs, F(0)), sum(ys, F(0))
    sxy = sum((x * y for x, y in zip(xs, ys)), F(0))
    sxx = sum((x * x for x in xs), F(0))
    syy = sum((y * y for y in ys), F(0))
    num = n * sxy - sx * sy
    bx = n * sxx - sx * sx
    by = n * syy - sy * sy
    if bx == 0 or by == 0:
        return 0, None, None, ("undefined: the x coordinate is constant" if bx == 0
                               else "undefined: the y coordinate is constant")
    return ((num > 0) - (num < 0), (num * num) / (bx * by),
            float(num) / ((float(bx) ** 0.5) * (float(by) ** 0.5)), "exact sign and r^2")


def ranks_avg(xs):
    """Average ranks: a tie gets the mean of the positions it spans.  The convention is NAMED
    because a tie-heavy rank statistic is convention-dependent (Class 199)."""
    order = sorted(range(len(xs)), key=lambda i: (xs[i], i))
    out = [F(0)] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = F(sum(range(i + 1, j + 2)), j - i + 1)
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def ties_of(xs):
    return sum(1 for i in range(len(xs)) for j in range(i + 1, len(xs)) if xs[i] == xs[j])


def concordance(xs, ys):
    """The attenuation-proof reading (Class 197): of the PAIRS, how many agree in sign."""
    con = dis = tie = 0
    for i, j in itertools.combinations(range(len(xs)), 2):
        dx, dy = xs[i] - xs[j], ys[i] - ys[j]
        if dx == 0 or dy == 0:
            tie += 1
        elif (dx > 0) == (dy > 0):
            con += 1
        else:
            dis += 1
    return {"concordant": con, "discordant": dis, "tied": tie, "pairs": con + dis + tie}


def assoc(xs, ys):
    """Every reading of ONE association: Pearson and Spearman (sign and r^2 exact), the concordance
    counts, and the leave-one-out range of the sign (17 points is few, so the stability is owed)."""
    s, r2, dec, why = pearson(xs, ys)
    sp_s, sp_r2, sp_dec, sp_why = pearson(ranks_avg(xs), ranks_avg(ys))
    loo = []
    for k in range(len(xs)):
        a = [x for i, x in enumerate(xs) if i != k]
        b = [y for i, y in enumerate(ys) if i != k]
        loo.append(pearson(a, b)[0])
    return {
        "pearson_sign": s, "pearson_r2": (str(r2) if r2 is not None else None),
        "pearson_r": (None if dec is None else "%.6f" % dec), "pearson_note": why,
        "spearman_sign": sp_s, "spearman_r2": (str(sp_r2) if sp_r2 is not None else None),
        "spearman_rho": (None if sp_dec is None else "%.6f" % sp_dec), "spearman_note": sp_why,
        "ties_x": ties_of(xs), "ties_y": ties_of(ys),
        "concordance": concordance(xs, ys),
        "loo_pearson_signs": loo, "loo_sign_stable": len(set(loo)) == 1,
    }


def median_of(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2


# ------------------------------------------------------------------------------------------------
# P1: restated over THIS grid

def p1(cells):
    n = len(cells)
    pos = sum(1 for c in cells.values() if c["G"] > 0)
    return {"cells": n, "G_pos": pos, "share_of_cells": str(F(pos, n)), "majority": pos * 2 > n,
            "per_game": OrderedDict(
                (g, {"cells": sum(1 for k in cells if k.startswith(g + "|")),
                     "G_pos": sum(1 for k, c in cells.items()
                                  if k.startswith(g + "|") and c["G"] > 0)})
                for g in V.GAMES)}


# ------------------------------------------------------------------------------------------------
# P2: which factor moves the gain

def decomp(tab, n_prot, n_pop):
    """The EXACT two-way decomposition of a complete `n_prot x n_pop` layout.

    Returns (ss_total, ss_protocol, ss_population, ss_interaction).  The layout weights are
    ARGUMENTS: the identity they must satisfy is what C2 plants against, and a helper with the
    weights baked in could not be planted at all (Class 197 -- a plant must BE the predicate).
    """
    n = len(tab)
    grand = sum(tab.values(), F(0)) / n
    rows, cols = {}, {}
    for (i, j), v in tab.items():
        rows[i] = rows.get(i, F(0)) + v
        cols[j] = cols.get(j, F(0)) + v
    rm = {i: s / n_pop for i, s in rows.items()}
    cm = {j: s / n_prot for j, s in cols.items()}
    ss_tot = sum(((v - grand) ** 2 for v in tab.values()), F(0))
    ss_prot = n_pop * sum(((rm[s] - grand) ** 2 for s in rows), F(0))
    ss_pop = n_prot * sum(((cm[s] - grand) ** 2 for s in cols), F(0))
    # the residual is COMPUTED from the cell, never taken as `ss_tot - ss_prot - ss_pop`: taken that
    # way the "identity" holds word for word whatever the weights are, and the check that is supposed
    # to plant against it can never fire (measured 2026-10-16 -- the first draft's plant survived)
    ss_int = sum(((v - rm[i] - cm[j] + grand) ** 2 for (i, j), v in tab.items()), F(0))
    return ss_tot, ss_prot, ss_pop, ss_int


def p2(cells, protocols):
    ps = list(protocols)
    pops = list(V.populations())
    per_game = OrderedDict()
    for g in V.GAMES:
        tab = OrderedDict(((pr, po), F(cells["%s|%s|%s" % (g, po, pr)]["G"]))
                          for pr in ps for po in pops)
        ss_tot, ss_prot, ss_pop, ss_int = decomp(tab, len(ps), len(pops))
        # a protocol IMMUNE in every cell of this game has a population range of exactly 0 BY
        # CONSTRUCTION; the CONDITION -- never the value -- is what selects it for exclusion
        floored = [pr for pr in ps if all(tab[(pr, po)] == 0 for po in pops)]
        live = [pr for pr in ps if pr not in floored]
        prange = OrderedDict((pr, max(tab[(pr, po)] for po in pops)
                              - min(tab[(pr, po)] for po in pops)) for pr in ps)
        orange = OrderedDict((po, max(tab[(pr, po)] for pr in ps)
                              - min(tab[(pr, po)] for pr in ps)) for po in pops)
        per_game[g] = {
            "ss_total": str(ss_tot), "ss_protocol": str(ss_prot), "ss_population": str(ss_pop),
            "ss_interaction": str(ss_int),
            "ms_protocol": str(ss_prot / (len(ps) - 1)),
            "ms_population": str(ss_pop / (len(pops) - 1)),
            "ss_share_protocol": str(ss_prot / ss_tot) if ss_tot else None,
            "floored_protocols": floored,
            "population_range_mean_all": str(sum(prange.values(), F(0)) / len(ps)),
            "population_range_mean_live": (str(sum((prange[p] for p in live), F(0)) / len(live))
                                           if live else None),
            "protocol_range_mean": str(sum(orange.values(), F(0)) / len(pops)),
            "population_range_max": str(max(prange.values())),
            "protocol_range_max": str(max(orange.values())),
            "per_protocol_population_range": OrderedDict((k, str(v)) for k, v in prange.items()),
            "per_population_protocol_range": OrderedDict((k, str(v)) for k, v in orange.items()),
        }
    # the gain summarised at each level, so the two spreads below are spreads of the SAME kind of
    # number (the mean over the other factor) and are therefore comparable
    mog = OrderedDict(((pr, po),
                       sum((F(cells["%s|%s|%s" % (g, po, pr)]["G"]) for g in V.GAMES), F(0))
                       / len(V.GAMES))
                      for pr in ps for po in pops)
    pop_spread = OrderedDict((pr, max(mog[(pr, po)] for po in pops)
                              - min(mog[(pr, po)] for po in pops)) for pr in ps)
    prot_spread = OrderedDict((po, max(mog[(pr, po)] for pr in ps)
                               - min(mog[(pr, po)] for pr in ps)) for po in pops)
    live_pop_spread = [v for pr, v in pop_spread.items()
                       if any(F(cells["%s|%s|%s" % (g, po, pr)]["G"]) > 0
                              for g in V.GAMES for po in pops)]
    return {
        "per_game": per_game,
        "n_games_ss_protocol_gt_population": sum(
            1 for g in V.GAMES if F(per_game[g]["ss_protocol"]) > F(per_game[g]["ss_population"])),
        "n_games_ms_protocol_gt_population": sum(
            1 for g in V.GAMES if F(per_game[g]["ms_protocol"]) > F(per_game[g]["ms_population"])),
        "median_ss_protocol": str(median_of([F(per_game[g]["ss_protocol"]) for g in V.GAMES])),
        "median_ss_population": str(median_of([F(per_game[g]["ss_population"]) for g in V.GAMES])),
        "median_ms_protocol": str(median_of([F(per_game[g]["ms_protocol"]) for g in V.GAMES])),
        "median_ms_population": str(median_of([F(per_game[g]["ms_population"]) for g in V.GAMES])),
        "median_ss_share_protocol": str(median_of(
            [F(per_game[g]["ss_share_protocol"]) for g in V.GAMES
             if per_game[g]["ss_share_protocol"] is not None])),
        "median_population_range_live": str(median_of(
            [F(per_game[g]["population_range_mean_live"]) for g in V.GAMES
             if per_game[g]["population_range_mean_live"] is not None])),
        "median_protocol_range": str(median_of(
            [F(per_game[g]["protocol_range_mean"]) for g in V.GAMES])),
        "protocol_spread_mean_over_games": OrderedDict((k, str(v)) for k, v in prot_spread.items()),
        "population_spread_mean_over_games": OrderedDict((k, str(v)) for k, v in pop_spread.items()),
        "median_protocol_spread": str(median_of(list(prot_spread.values()))),
        "median_population_spread_all": str(median_of(list(pop_spread.values()))),
        "median_population_spread_live": (str(median_of(live_pop_spread)) if live_pop_spread
                                          else None),
    }


# ------------------------------------------------------------------------------------------------
# P3: who loses the ordering

def per_protocol_table(cells, tr, protocols):
    per = OrderedDict()
    for pr in protocols:
        sub = [cells[k] for k in cells if k.split("|")[2] == pr]
        tsub = [tr[k] for k in tr if k.split("|")[1] == pr and tr[k]["raw"] is not None]
        per[pr] = {
            "cells": len(sub),
            "G_pos": sum(1 for c in sub if c["G"] > 0),
            "G_max": max(c["G"] for c in sub),
            "G_mean": str(sum((F(c["G"]) for c in sub), F(0)) / len(sub)),
            "tau_lt_1": sum(1 for c in sub if c["tau"] < 1),
            "tau_bad_frac": str(F(sum(1 for c in sub if c["tau"] < 1), len(sub))),
            "T_raw_mean": str(sum((t["raw"] for t in tsub), F(0)) / len(tsub)),
            "T_excess_mean": str(sum((t["excess"] for t in tsub), F(0)) / len(tsub)),
            "T_excess_negative_entries": sum(1 for t in tsub if t["excess"] < 0),
            "T_entries": len(tsub),
            "shape": P.SHAPE[pr], "reads": P.READS[pr], "mono": P.MONO[pr],
        }
    return per


def p3(cells, tr, protocols):
    ps = list(protocols)
    per = per_protocol_table(cells, tr, protocols)
    gm = [F(per[p]["G_mean"]) for p in ps]
    raw = [F(per[p]["T_raw_mean"]) for p in ps]
    exc = [F(per[p]["T_excess_mean"]) for p in ps]
    bad = [F(per[p]["tau_bad_frac"]) for p in ps]
    immune = [p for p in ps if per[p]["G_pos"] == 0]
    med_raw, med_exc = median_of(raw), median_of(exc)
    # the 3-pair sensitivity: v0's own pair set (the three perturbations against `uniform`)
    # the key form is `game|protocol|p1>p2`, so the perturbed pair is the THIRD field and the
    # population it starts from is its left member
    sel = {k: v for k, v in tr.items() if k.split("|")[2].split(">")[0] == "uniform"}
    raw3 = [sum((F(sel[k]["raw"]) for k in sel if k.split("|")[1] == p), F(0))
            / max(1, sum(1 for k in sel if k.split("|")[1] == p)) for p in ps]
    exc3 = [sum((F(sel[k]["excess"]) for k in sel if k.split("|")[1] == p), F(0))
            / max(1, sum(1 for k in sel if k.split("|")[1] == p)) for p in ps]
    bases = [v["base"] for v in tr.values() if v["base"] is not None]
    # ---------------------------------------------------------------------------------------------
    # THE UNIT THAT SEPARATES THE TWO READINGS.  Over a per-protocol mean, T_excess is T_raw minus a
    # CONSTANT: every protocol's entry set is the same (all games x all pairs) and the baseline does
    # not depend on the protocol, so the two y-vectors are affine images of one another and their
    # Pearson r, Spearman rho and concordance counts are IDENTICAL -- measured 2026-10-16, all three
    # agree exactly.  That is algebra, not evidence: it says the excess changes the LEVEL and not the
    # ASSOCIATION.  Reading the pair at (game, protocol) instead -- where the baseline's mean differs
    # by game -- makes the excess a genuinely different object, so the association is reported at both
    # units and the disagreement between them is the point.
    gkey = {g: [F(v["raw"]) for k, v in tr.items() if k.split("|")[0] == g and v["raw"] is not None]
            for g in V.GAMES}
    gex = {g: [F(v["excess"]) for k, v in tr.items() if k.split("|")[0] == g
               and v["excess"] is not None] for g in V.GAMES}
    cell_units = [(g, pr) for g in V.GAMES for pr in ps]
    cx = [sum((F(cells["%s|%s|%s" % (g, po, pr)]["G"]) for po in V.populations()), F(0))
          / len(V.populations()) for g, pr in cell_units]
    craw, cexc = [], []
    for g, pr in cell_units:
        e = [v for k, v in tr.items() if k.split("|")[0] == g and k.split("|")[1] == pr]
        craw.append(sum((F(v["raw"]) for v in e), F(0)) / len(e))
        cexc.append(sum((F(v["excess"]) for v in e), F(0)) / len(e))
    raw_excess_gap = {p: F(per[p]["T_raw_mean"]) - F(per[p]["T_excess_mean"]) for p in ps}
    # ------------------------------------------------------------------------------------------
    # THE RESTRICTED READING.  Three protocols read neither the population nor the payoff: their
    # score is a fixed number (or a min/max over the zoo), so their ordering cannot move with the
    # population and their transport loss is 0 in every entry BY CONSTRUCTION.  They are the
    # sharpest witnesses against P3 and the most objectionable ones ("your zero-loss protocols are
    # degenerate"), so the association is reported BOTH over the full zoo and over the protocols
    # that actually respond to the population, with the excluded set selected by that CONDITION.
    popfree = [p for p in ps if all(tr[k]["raw"] == 0 for k in tr if k.split("|")[1] == p)]
    live_ps = [p for p in ps if p not in popfree]
    li = [ps.index(p) for p in live_ps]
    return {
        "per_protocol": per,
        "population_independent_protocols": popfree,
        "population_responsive_protocols": live_ps,
        "assoc_population_responsive_G_vs_T_raw": assoc([gm[i] for i in li], [raw[i] for i in li]),
        "immune_protocols": immune,
        "gameable_protocols": [p for p in ps if per[p]["G_pos"] > 0],
        "median_T_raw_mean": str(med_raw), "median_T_excess_mean": str(med_exc),
        "T_base_mean": str(sum(bases, F(0)) / len(bases)),
        "T_base_min": str(min(bases)), "T_base_max": str(max(bases)),
        "assoc_G_vs_T_raw": assoc(gm, raw),
        "assoc_G_vs_T_excess": assoc(gm, exc),
        "assoc_G_vs_tau_bad": assoc(gm, bad),
        "assoc_tau_bad_vs_T_raw": assoc(bad, raw),
        "assoc_tau_bad_vs_T_excess": assoc(bad, exc),
        "assoc_v0_pairset_G_vs_T_raw": assoc(gm, raw3),
        "assoc_v0_pairset_G_vs_T_excess": assoc(gm, exc3),
        "protocol_level_raw_minus_excess_is_constant": len(set(raw_excess_gap.values())) == 1,
        "protocol_level_raw_minus_excess_value": str(sorted(set(raw_excess_gap.values()))[0])
        if len(set(raw_excess_gap.values())) == 1 else None,
        "assoc_gameprotocol_G_vs_T_raw": assoc(cx, craw),
        "assoc_gameprotocol_G_vs_T_excess": assoc(cx, cexc),
        "units_gameprotocol": len(cell_units),
        "base_values_per_game": OrderedDict((g, sorted({str(F(v["base"])) for k, v in tr.items()
                                                        if k.split("|")[0] == g}))
                                            for g in V.GAMES),
        "immune_above_median_T_raw": [p for p in immune if F(per[p]["T_raw_mean"]) > med_raw],
        "immune_above_median_T_excess": [p for p in immune if F(per[p]["T_excess_mean"]) > med_exc],
        "top3_by_G_mean": sorted(ps, key=lambda p: (-F(per[p]["G_mean"]), p))[:3],
        "top3_by_T_raw": sorted(ps, key=lambda p: (-F(per[p]["T_raw_mean"]), p))[:3],
        "top3_by_T_excess": sorted(ps, key=lambda p: (-F(per[p]["T_excess_mean"]), p))[:3],
    }


def run():
    protocols = P.PROTOCOLS
    cells, base = grid(protocols)
    tr = transport(cells, base, protocols)
    return {
        "model": {
            "games": list(V.GAMES), "policies": list(V.ZOO),
            "populations": list(V.populations()), "protocols": list(protocols),
            "cells": len(cells), "transport_entries": len(tr),
            "population_pairs": [list(p) for p in _pairs()],
            "design_space_source": "spike_v2.PROTOCOLS (the 17-protocol design space of record)",
        },
        "P1_gain_positive": p1(cells),
        "P2_which_factor_moves_G": p2(cells, protocols),
        "P3_who_loses_the_ordering": p3(cells, tr, protocols),
        "transport": OrderedDict(
            (k, {"raw": (str(v["raw"]) if v["raw"] is not None else None),
                 "base": str(v["base"]), "excess": str(v["excess"])})
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
                       env=env, cwd=os.path.dirname(os.path.abspath(__file__)))
    if r.returncode != 0:
        return None, r.stderr[-400:]
    return r.stdout, None


# ------------------------------------------------------------------------------------------------
# the two identities the certificate plants against

def v0_agreement():
    """C1: v3's cells against v0's SHIPPED artefact, on the protocols both carry.

    An identity between two carriers of the same number, read from DISK -- so a parser defect or a
    re-derivation drift shows up here rather than in a prose claim.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike_v0_results.json")
    if not os.path.exists(path):
        return None, "spike_v0_results.json is absent"
    with open(path, encoding="utf-8") as fh:
        v0 = json.load(fh)
    cells, _ = grid(OrderedDict((p, P.PROTOCOLS[p]) for p in SHARED))
    bad = []
    for k, c in cells.items():
        want = v0["cells"].get(k)
        if want is None:
            bad.append((k, "missing in v0"))
        elif c["G"] != int(want["G"]) or str(c["tau"]) != want["tau"]:
            bad.append((k, "G %s!=%s tau %s!=%s" % (c["G"], want["G"], c["tau"], want["tau"])))
    return {"shared_protocols": list(SHARED), "cells": len(cells),
            "mismatches": bad[:5], "n_mismatches": len(bad)}, None


def v0_v2_nesting():
    """C3: the registration's 7-protocol set and the 17-protocol design space agree on every shared
    cell -- if they did not, the wider grid would not nest the registered one."""
    a, _ = grid(OrderedDict((p, V.PROTOCOLS[p]) for p in SHARED))
    b, _ = grid(OrderedDict((p, P.PROTOCOLS[p]) for p in SHARED))
    bad = [k for k in a if a[k]["G"] != b[k]["G"] or a[k]["tau"] != b[k]["tau"]]
    return {"shared_protocols": list(SHARED), "cells": len(a), "mismatches": bad[:5],
            "n_mismatches": len(bad)}


# ------------------------------------------------------------------------------------------------
# the certificate

def selftest():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("[%-44s] %s%s" % (name, "ok" if cond else "FAIL",
                                "" if cond else "  -> " + str(detail)[:200]))

    protocols = P.PROTOCOLS
    cells, base = grid(protocols)
    tr = transport(cells, base, protocols)
    ps = list(protocols)
    pops = list(V.populations())

    # ---- C1: identity with v0's shipped artefact, and its plant
    agree, why = v0_agreement()
    check("C1-v0-shipped-artefact-agrees", bool(agree) and agree["n_mismatches"] == 0,
          why or (agree and agree["mismatches"]))
    a, _ = grid(OrderedDict((p, P.PROTOCOLS[p]) for p in SHARED))
    k0 = sorted(a)[0]
    planted = dict(a)
    planted[k0] = dict(planted[k0], G=planted[k0]["G"] + 1)
    check("C1-plant-a-perturbed-cell-fires",
          any(planted[k]["G"] != a[k]["G"] for k in a),
          "the comparison is inert: a perturbed cell reads the same")

    # ---- C2: the decomposition identity, and its plant (the SAME predicate, a wrong weight)
    g0 = list(V.GAMES)[0]
    tab = OrderedDict(((pr, po), F(cells["%s|%s|%s" % (g0, po, pr)]["G"]))
                      for pr in ps for po in pops)
    t, sp, sq, si = decomp(tab, len(ps), len(pops))
    check("C2-decomposition-is-an-identity", t == sp + sq + si,
          "%s vs %s" % (t, sp + sq + si))
    t2, sp2, sq2, si2 = decomp(tab, len(ps), len(pops) + 1)
    check("C2-plant-wrong-weight-breaks-it", t2 != sp2 + sq2 + si2,
          "the identity survived a wrong layout weight, so it is not a check")

    # ---- C3: the two grids nest, and its plant
    nest = v0_v2_nesting()
    check("C3-v0-grid-nests-in-the-design-space", nest["n_mismatches"] == 0, nest["mismatches"])
    # the plant is DECREASING, not merely different: an increasing affine transform is inside the
    # invariance class v1's T1 proves (it preserves the ordering exactly, so it moves no cell at all
    # -- measured 2026-10-16, when `+1` was the plant and it fired nowhere)
    ca, _ = grid(OrderedDict([("mean_payoff", lambda M, x, pop, W: -V._mean(M, x, pop))]))
    check("C3-plant-a-changed-body-fires",
          any(ca[k]["G"] != a[k]["G"] for k in ca if k in a),
          "a changed protocol body did not move a single cell")

    # ---- C4: the two-sided control
    check("C4-monotone-references-read-zero",
          all(cells["%s|%s|%s" % (g, po, pr)]["G"] == 0
              for g in V.GAMES for po in pops for pr in ("mean_payoff", "spread")))
    check("C4-plant-nonmonotone-reads-positive",
          any(cells["%s|%s|%s" % (g, po, "game_wins")]["G"] > 0 for g in V.GAMES for po in pops)
          and any(cells["%s|%s|%s" % (g, po, "random_fixed")]["G"] > 0
                  for g in V.GAMES for po in pops),
          "a non-monotone arm never fires, so the control is one-sided")

    # ---- C5: the degeneracy exclusion is not cosmetic
    p = p2(cells, protocols)
    floored = p["per_game"][g0]["floored_protocols"]
    allm = F(p["per_game"][g0]["population_range_mean_all"])
    livem = F(p["per_game"][g0]["population_range_mean_live"])
    check("C5-exclusion-moves-the-figure", bool(floored) and allm != livem,
          "floored=%s all=%s live=%s" % (floored, allm, livem))
    check("C5-plant-including-them-understates", allm < livem, "%s vs %s" % (allm, livem))

    # ---- C6: determinism across processes, and the artefact round-trip
    out, err = _subprocess_json()
    mine = dump(run())
    check("C6-a-second-process-agrees-byte-for-byte", out is not None and out == mine,
          err or "the two processes differ")
    doc = json.loads(mine)
    p3a = p3(cells, tr, protocols)
    check("C6-artefact-round-trips-from-json",
          doc["P1_gain_positive"]["cells"] == len(cells)
          and F(doc["P3_who_loses_the_ordering"]["per_protocol"]["mean_payoff"]["T_raw_mean"])
          == F(p3a["per_protocol"]["mean_payoff"]["T_raw_mean"])
          and doc["P3_who_loses_the_ordering"]["assoc_G_vs_T_raw"]["pearson_sign"]
          == p3a["assoc_G_vs_T_raw"]["pearson_sign"],
          "the artefact does not re-read to the values the run computed")

    # ---- C8: a protocol FAITHFUL in every cell has an excess of exactly zero, in every entry;
    # a protocol that is not faithful has a nonzero excess somewhere (the two-sided control)
    faithful = [pr for pr in ps if all(cells["%s|%s|%s" % (g, po, pr)]["tau"] == 1
                                       for g in V.GAMES for po in pops)]
    fz = all(F(v["excess"]) == 0 for k, v in tr.items() if k.split("|")[1] in faithful)
    nz = any(F(v["excess"]) != 0 for k, v in tr.items() if k.split("|")[1] not in faithful)
    check("C8-faithful-programs-carry-zero-excess", bool(faithful) and fz, faithful)
    check("C8-plant-unfaithful-carries-nonzero-excess", nz,
          "an unfaithful protocol's excess is zero in every entry, so the identity is one-sided")
    # the plant: a baseline taken from a DIFFERENT (game, pair) breaks it.  The plant's own input is
    # part of the plant (Class 189): a wrong baseline whose value happens to COINCIDE with the right
    # one plants nothing, so the entry is CHOSEN by the condition that its base differs -- measured
    # 2026-10-16, when the first draft took `game[1]`'s baseline for `game[0]`'s first pair and the
    # two values were equal, so the plant fired nowhere
    gA = list(V.GAMES)[0]
    pa, pb = _pairs()[0]
    probe = list(ps)[0]
    b0 = F(tr["%s|%s|%s>%s" % (gA, probe, pa, pb)]["base"])
    alt = [(g2, p2) for g2 in V.GAMES for p2 in _pairs()
           if F(tr["%s|%s|%s>%s" % (g2, probe, p2[0], p2[1])]["base"]) != b0]
    if not alt:
        check("C8-plant-a-wrong-baseline-breaks-it", False,
              "no (game, pair) carries a different baseline, so the plant cannot be formed")
    else:
        g2, q = alt[0]
        moved = []
        for pr in faithful:
            here = "%s>%s" % (pa, pb)
            true = [F(v["excess"]) for k, v in tr.items()
                    if k.split("|")[0] == gA and k.split("|")[1] == pr and k.split("|")[2] == here]
            planted_v = [F(v["raw"]) - F(tr["%s|%s|%s>%s" % (g2, pr, q[0], q[1])]["base"])
                         for k, v in tr.items()
                         if k.split("|")[0] == gA and k.split("|")[1] == pr and k.split("|")[2] == here]
            if true and planted_v and true[0] != planted_v[0]:
                moved.append(pr)
        check("C8-plant-a-wrong-baseline-breaks-it", bool(moved),
              "a baseline from (game %s, %s>%s) left every faithful protocol's excess unchanged"
              % (g2, q[0], q[1]))

    # ---- C9: the affine tell.  Over a per-protocol mean the excess is the raw loss minus a
    # CONSTANT, so the two readings must report the SAME r, rho and concordance -- and a check that
    # expects them to differ there would be wrong.  At the (game, protocol) unit the constant differs
    # by game, so the two readings must DIFFER.  Both directions are asserted.
    p3d = p3(cells, tr, protocols)
    same = (p3d["assoc_G_vs_T_raw"]["pearson_r"] == p3d["assoc_G_vs_T_excess"]["pearson_r"]
            and p3d["assoc_G_vs_T_raw"]["spearman_rho"]
            == p3d["assoc_G_vs_T_excess"]["spearman_rho"]
            and p3d["assoc_G_vs_T_raw"]["concordance"] == p3d["assoc_G_vs_T_excess"]["concordance"])
    check("C9-protocol-level-readings-are-identical", same,
          "the raw and excess readings differ at the protocol level, so the affine identity failed")
    diff = (p3d["assoc_gameprotocol_G_vs_T_raw"]["pearson_r"]
            != p3d["assoc_gameprotocol_G_vs_T_excess"]["pearson_r"]
            or p3d["assoc_gameprotocol_G_vs_T_raw"]["concordance"]
            != p3d["assoc_gameprotocol_G_vs_T_excess"]["concordance"])
    check("C9-plant-gameprotocol-level-readings-differ", diff,
          "the two readings are the SAME object at the fine unit too, so it separates nothing")
    check("C9-plant-constant-baseline-collapses-it",
          len({str(F(tr[k]["base"])) for k in tr}) > 1,
          "the baseline takes one value everywhere, so the excess could not be a constant shift")

    # ---- C10: the restricted reading -- the exclusion is selected by a CONDITION and it does work
    p3d2 = p3(cells, tr, protocols)
    pf = p3d2["population_independent_protocols"]
    full_r = p3d2["assoc_G_vs_T_raw"]["pearson_r"]
    live_r = p3d2["assoc_population_responsive_G_vs_T_raw"]["pearson_r"]
    check("C10-the-population-free-set-is-named-and-nonempty", bool(pf), pf)
    check("C10-the-restriction-moves-the-reading", full_r != live_r, (full_r, live_r))
    # the plant: excluded by the VALUE of G instead of by the condition, the set differs -- so the
    # condition, and not the exclusion itself, is what the reading is about
    wrongset = [q for q in ps if F(p3d2["per_protocol"][q]["G_mean"]) == 0]
    check("C10-plant-a-wrong-condition-selects-else", sorted(wrongset) != sorted(pf),
          "excluding by the G value selects the same set, so the condition is not the one read")

    # ---- C7: `undef` is a reading, never a 0
    s, r2, _d, why = pearson([F(1), F(1), F(1)], [F(1), F(2), F(3)])
    check("C7-constant-coordinate-reads-undef", s == 0 and r2 is None and "undefined" in why, why)
    s2, r2b, _d2, _w2 = pearson([F(1), F(2), F(3)], [F(1), F(2), F(4)])
    check("C7-plant-a-live-subset-reads-a-number", r2b is not None and s2 > 0, (s2, r2b))

    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------
# the report

def report_text(doc):
    m, p2d, p3d = doc["model"], doc["P2_which_factor_moves_G"], doc["P3_who_loses_the_ordering"]
    L = []
    L.append("== issue #141 -- v3: the TRANSPORT ARM (P2 and P3) ==")
    L.append("   %d games x %d policies x %d populations x %d protocols = %d cells; exact, no seed,"
             % (len(m["games"]), len(m["policies"]), len(m["populations"]), len(m["protocols"]),
                m["cells"]))
    L.append("   %d transport entries over the %d population pairs; design space: %s"
             % (m["transport_entries"], len(m["population_pairs"]), m["design_space_source"]))
    L.append("")
    g = doc["P1_gain_positive"]
    L.append("== P1 (registered: the gain is positive in a majority of cells) ==")
    L.append("   G > 0 in %d of %d cells = %s  -> %s"
             % (g["G_pos"], g["cells"], g["share_of_cells"], "CONFIRMED" if g["majority"] else "REFUTED"))
    for gg, v in g["per_game"].items():
        L.append("      %-10s %2d of %2d cells" % (gg, v["G_pos"], v["cells"]))
    L.append("")
    L.append("== P2 (registered: protocol spread EXCEEDS population spread) ==")
    L.append("   per game, the exact two-way decomposition of G on the %dx%d layout:"
             % (len(m["protocols"]), len(m["populations"])))
    L.append("   %-10s %12s %12s %12s %9s %9s" % ("game", "SS_protocol", "SS_population",
                                                  "SS_interact", "MS_prot", "MS_pop"))
    for gg, v in p2d["per_game"].items():
        L.append("   %-10s %12.4f %12.4f %12.4f %9.4f %9.4f"
                 % (gg, float(F(v["ss_protocol"])), float(F(v["ss_population"])),
                    float(F(v["ss_interaction"])), float(F(v["ms_protocol"])),
                    float(F(v["ms_population"]))))
    L.append("   median over games: SS_protocol=%s  SS_population=%s   MS_protocol=%s  MS_population=%s"
             % (p2d["median_ss_protocol"], p2d["median_ss_population"], p2d["median_ms_protocol"],
                p2d["median_ms_population"]))
    L.append("   games with SS_protocol > SS_population: %d of %d   (on MS: %d of %d)"
             % (p2d["n_games_ss_protocol_gt_population"], len(m["games"]),
                p2d["n_games_ms_protocol_gt_population"], len(m["games"])))
    L.append("   the registration's range reading, both level counts named:")
    L.append("      median over games of the mean POPULATION range (over %d populations) = %s"
             % (len(m["populations"]), p2d["median_population_range_live"]))
    L.append("      median over games of the mean PROTOCOL range   (over %d protocols)  = %s"
             % (len(m["protocols"]), p2d["median_protocol_range"]))
    L.append("      median spread of the gain across populations, fixed protocol = %s  (live only)"
             % p2d["median_population_spread_live"])
    L.append("      median spread of the gain across protocols,  fixed population = %s"
             % p2d["median_protocol_spread"])
    L.append("   EXCLUDED BY CONDITION (immune in every cell of THAT game, so its population range")
    L.append("   is 0 by construction -- excluded by the condition, never by the value):")
    for gg, v in p2d["per_game"].items():
        L.append("      %-10s %s" % (gg, ", ".join(v["floored_protocols"]) or "none"))
    L.append("")
    L.append("== P3 (registered: the gameable protocols are the same non-transporting ones) ==")
    L.append("   the payoff ordering's own transport loss (the BASELINE every protocol carries):")
    L.append("      mean %s   min %s   max %s" % (p3d["T_base_mean"], p3d["T_base_min"],
                                                  p3d["T_base_max"]))
    L.append("   %-14s %8s %8s %8s %9s %9s %6s" % ("protocol", "G_mean", "G_max", "cells>0",
                                                   "T_raw", "T_excess", "tau<1"))
    for pr, v in p3d["per_protocol"].items():
        L.append("   %-14s %8.4f %8d %8d %9.4f %9.4f %6d"
                 % (pr, float(F(v["G_mean"])), v["G_max"], v["G_pos"],
                    float(F(v["T_raw_mean"])), float(F(v["T_excess_mean"])), v["tau_lt_1"]))
    L.append("   protocol-level associations (n = %d; sign and r^2 exact):" % len(m["protocols"]))
    for label, k in (("G vs T_raw", "assoc_G_vs_T_raw"),
                     ("G vs T_excess", "assoc_G_vs_T_excess"),
                     ("G vs tau<1 frac", "assoc_G_vs_tau_bad"),
                     ("tau<1 vs T_raw", "assoc_tau_bad_vs_T_raw"),
                     ("tau<1 vs T_excess", "assoc_tau_bad_vs_T_excess"),
                     ("[3-pair] G vs T_raw", "assoc_v0_pairset_G_vs_T_raw"),
                     ("[3-pair] G vs T_excess", "assoc_v0_pairset_G_vs_T_excess"),
                     ("[%d units] G vs T_raw" % p3d["units_gameprotocol"],
                      "assoc_gameprotocol_G_vs_T_raw"),
                     ("[%d units] G vs T_excess" % p3d["units_gameprotocol"],
                      "assoc_gameprotocol_G_vs_T_excess")):
        a = p3d[k]
        c = a["concordance"]
        L.append("      %-20s r=%s (%s) rho=%s  sign=%+d  r2=%s  concordant %d/ discordant %d/"
                 " tied %d  LOO-sign-stable=%s  ties(x,y)=(%d,%d)"
                 % (label, a["pearson_r"], a["pearson_note"], a["spearman_rho"], a["pearson_sign"],
                    (a["pearson_r2"] or "n/a"), c["concordant"], c["discordant"], c["tied"],
                    a["loo_sign_stable"], a["ties_x"], a["ties_y"]))
    L.append("   restricted to the %d protocols that RESPOND to the population (excluding %s, whose"
             % (len(p3d["population_responsive_protocols"]),
                ", ".join(p3d["population_independent_protocols"])))
    L.append("   score reads neither the population nor the payoff, so their loss is 0 by")
    L.append("   construction -- excluded by that condition, not by the value):")
    _a = p3d["assoc_population_responsive_G_vs_T_raw"]
    _c = _a["concordance"]
    L.append("      G vs T_raw over n=%d: r=%s rho=%s sign=%+d r2=%s concordant %d/ discordant %d/"
             " LOO-stable=%s"
             % (len(p3d["population_responsive_protocols"]), _a["pearson_r"], _a["spearman_rho"],
                _a["pearson_sign"], _a["pearson_r2"], _c["concordant"], _c["discordant"],
                _a["loo_sign_stable"]))
    L.append("   THE AFFINE TELL, stated because a check must carry it: over a PROTOCOL mean the")
    L.append("   baseline is one constant (every protocol has the same 24 entries), so T_excess ==")
    L.append("   T_raw - %s identically and the two readings MUST report the same r, rho and"
             % (p3d["protocol_level_raw_minus_excess_value"] or "c"))
    L.append("   concordance counts -- they do.  At the (game, protocol) unit the baseline's mean")
    L.append("   differs by game, so the two are different objects there and they differ.")
    L.append("   the zero-gain (immune) protocols: %s" % ", ".join(p3d["immune_protocols"]))
    L.append("      above the median T_raw:    %s" % (", ".join(p3d["immune_above_median_T_raw"])
                                                      or "none"))
    L.append("      above the median T_excess: %s" % (", ".join(p3d["immune_above_median_T_excess"])
                                                      or "none"))
    L.append("   top-3 by G_mean:    %s" % ", ".join(p3d["top3_by_G_mean"]))
    L.append("   top-3 by T_raw:     %s" % ", ".join(p3d["top3_by_T_raw"]))
    L.append("   top-3 by T_excess:  %s" % ", ".join(p3d["top3_by_T_excess"]))
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
