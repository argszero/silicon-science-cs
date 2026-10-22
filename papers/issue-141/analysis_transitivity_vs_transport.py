#!/usr/bin/env python3
"""Required change 1(b) of the issue #141 minor-revision decision (R673).

The question the editor asks, stated as a computation rather than a concession:

    Does this paper's transport statistic reduce to the non-transitivity dimension of
    Czarnecki et al. (arXiv:2004.09468) on the 19 x 9 space the manuscript already enumerates,
    or does it carry something that dimension does not?

Both objects are built here from the same exact payoff matrices, in `Fraction` arithmetic:

  * the **transitivity coordinate** of a game -- the fraction of strategy triples that are CYCLIC
    under "a beats b" (M[a][b] > M[b][a]).  This is the quantity Czarnecki et al. order games by:
    0 is a fully transitive (totally ordered) game, 1 is fully cyclic (rock-paper-scissors).
    It is a property of the PAYOFF STRUCTURE, and it is computed for the full zoo and, because
    their axis is read at a population (the "spinning top" is transitivity against population),
    for each declared population restricted to the policies it gives positive weight.

  * the **transport excess** of an entry (game, protocol, ordered pair of populations), taken from
    the package's own machinery of record (`spike_v3.transport`), so this analysis cannot drift
    from the paper's definition.

The reduction test, stated so it can FAIL:

    If transport reduced to the transitivity coordinate, then within one game -- where the
    coordinate is a single number (or, per population, a pair of them) -- the transport excess
    could not vary across protocols.  A game whose entries take more than one distinct excess
    value ACROSS PROTOCOLS at a fixed population pair refutes the reduction, and the count of
    distinct values measures how much the statistic carries beyond the coordinate.

Output is exact (Fractions printed as p/q) and the script exits 0 with a verdict line.
"""
import json
import os
import sys
from collections import OrderedDict
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import spike_v0 as V          # noqa: E402
import spike_v2 as P          # noqa: E402
import spike_v3 as T3         # noqa: E402
import spike_v4 as V4         # noqa: E402  (its import installs the 9-game ladder into V.GAMES)

LADDER = V4.LADDER
PROTOCOLS = V4.PROTOCOLS
POPS = list(V.populations())


def beats(M, a, b):
    """Strict preference relation of the payoff matrix: a beats b iff a profits more than b does."""
    return M[a][b] > M[b][a]


def transitivity_coordinate(M, names):
    """Fraction of unordered triples of `names` that are CYCLIC (non-transitive).

    0 = the relation is a total order on these names; 1 = every triple cycles.  A tie in any
    comparison makes the triple transitive (a tie is not a cycle), which is the conservative
    choice: it can only LOWER the coordinate, never inflate the separation claimed below.
    """
    ns = list(names)
    cyc = tot = 0
    for i in range(len(ns)):
        for j in range(i + 1, len(ns)):
            for k in range(j + 1, len(ns)):
                a, b, c = ns[i], ns[j], ns[k]
                tot += 1
                # count directed wins inside the triple
                w = 0
                for x, y in ((a, b), (b, c), (a, c)):
                    if beats(M, x, y):
                        w += 1
                    elif beats(M, y, x):
                        w += 2
                # a 3-cycle: one of the two cycle patterns (cw or ccw) -- exactly 3 directed
                # wins with no "both beat one" star.  Detect directly.
                pairs = [(a, b), (b, c), (a, c)]
                dirs = []
                for x, y in pairs:
                    if beats(M, x, y):
                        dirs.append((x, y))
                    elif beats(M, y, x):
                        dirs.append((y, x))
                    else:
                        dirs.append(None)          # tie
                if None in dirs:
                    continue                        # a tie cannot cycle
                # a cycle on {a,b,c} exists iff the three edges form a directed 3-cycle
                src = {p[0] for p in dirs}
                dst = {p[1] for p in dirs}
                if len(src) == 3 and len(dst) == 3:
                    cyc += 1
    return (F(cyc, tot) if tot else None), cyc, tot


def main():
    # ---- 1. the transitivity coordinate, per game (full zoo) and per (game, population)
    M_of = {}
    coords = OrderedDict()
    print("== the transitivity coordinate (cyclic-triple fraction), exact")
    print(f"{'game':9s} {'n_bidders':>9s} {'full zoo':>12s}    per-population (restricted to weighted policies)")
    for g in LADDER:
        M, W = V.matrices(g)
        M_of[g] = M
        c_full, cyc, tot = transitivity_coordinate(M, list(V.ZOO))
        coords[g] = {"full": str(c_full), "cycles": cyc, "triples": tot, "pop": {}}
        cells = []
        for pname, pop in V.populations().items():
            keep = [a for a, w in pop.items() if w > 0]
            c, cy2, t2 = transitivity_coordinate(M, keep)
            coords[g]["pop"][pname] = {"coord": str(c), "cycles": cy2, "triples": t2,
                                       "n_policies": len(keep)}
            cells.append(f"{pname}={cy2}/{t2}")
        print(f"{g:9s} {LADDER[g][0]:>9d} {cyc:>5d}/{tot:<6d}    " + "  ".join(cells))

    # ---- 2. the transport excess, from the package's own machinery of record
    cells, base = T3.grid(PROTOCOLS)
    tr = T3.transport(cells, base, PROTOCOLS)

    # The key shape is READ from the machinery of record, not assumed: "game|protocol|popA>popB".
    ks = list(tr)
    assert ks, "transport returned no entries"
    sample = ks[0]
    assert sample.count("|") == 2, f"unexpected transport key shape: {sample!r}"
    g0, pr0, pp0 = sample.split("|")
    assert ">" in pp0, f"third field is not a population pair: {sample!r}"

    # ---- 3. the reduction test: within a game and a FIXED population pair, does excess vary
    #         across protocols?  (If transport were a function of the transitivity coordinate
    #         alone, a fixed game + fixed population pair would pin it.)
    print("\n== the reduction test: distinct transport-excess values ACROSS PROTOCOLS, per game")
    print("   (a fixed game + fixed population pair; if transport reduced to the transitivity")
    print("    coordinate, this set would have exactly ONE member -- the coordinate pins it)")
    by_gp = OrderedDict()
    for k, v in tr.items():
        g, pr, pp = k.split("|")
        if v["excess"] is None:
            continue
        by_gp.setdefault((g, pp), OrderedDict()).setdefault(v["excess"], set()).add(pr)

    widest = OrderedDict()   # the illustrated pair per game, with its two extreme excesses
    verdict_rows = []
    for g in LADDER:
        vals = [len(d) for (gg, pp), d in by_gp.items() if gg == g]
        span = [(pp, len(d)) for (gg, pp), d in by_gp.items() if gg == g]
        mx = max(vals) if vals else 0
        mn = min(vals) if vals else 0
        verdict_rows.append((g, mn, mx, len(vals)))
        print(f"  {g:9s} distinct-value counts across its {len(vals)} population pairs: "
              f"min={mn} max={mx}")
        if mx > 1:
            # show the pair with the widest spread and the protocols at its extremes
            pp_max = max(span, key=lambda t: t[1])[0]
            d = by_gp[(g, pp_max)]
            lo = min(d)
            hi = max(d)
            print(f"      widest: {pp_max}  ->  {len(d)} distinct values; "
                  f"lowest {lo} by {sorted(d[lo])[:3]}, highest {hi} by {sorted(d[hi])[:3]}")
            # keep it: a number the instrument prints and the package does not store can
            # drift with every gate green (issue #141 R2).
            # `lo`/`hi` are Fractions here, and a Fraction is not JSON-serialisable:
            # store their exact string form (the artifact's own convention elsewhere).
            widest[g] = {"pair": pp_max, "n_distinct": len(d),
                         "low": str(lo), "low_protocols": sorted(d[lo]),
                         "high": str(hi), "high_protocols": sorted(d[hi])}

    print("\n== verdict")
    multi = [r for r in verdict_rows if r[2] > 1]
    if multi:
        print(f"  NO REDUCTION. In {len(multi)} of {len(verdict_rows)} games the transport excess "
              f"takes more than one distinct value at a FIXED population pair, so it varies with "
              f"the protocol -- an axis the transitivity coordinate does not have. The coordinate "
              f"is a property of the payoff structure; the excess is a property of the PROTOCOL.")
    else:
        print("  REDUCED. At every fixed (game, population pair) the excess is a single value; "
              "the statistic carries nothing beyond the payoff structure's coordinate, and the "
              "honest revision is to say so and claim the classification only.")

    # ---- 4. does the coordinate ORDER the games the way the excess does?  (a weaker, ordinal
    #         test: even if transport is not a function of the coordinate, it might be monotone in it)
    print("\n== the ordinal test: is the game-level mean excess monotone in the transitivity coordinate?")
    gmean = {}
    for g in LADDER:
        ex = [v["excess"] for k, v in tr.items() if k.split("|")[0] == g and v["excess"] is not None]
        gmean[g] = sum(ex, F(0)) / len(ex) if ex else None
    rows = sorted(LADDER, key=lambda g: F(coords[g]["full"]))
    print(f"  {'game':9s} {'coord(full)':>22s} {'mean excess':>22s}")
    for g in rows:
        print(f"  {g:9s} {coords[g]['full']:>22s} {str(gmean[g]):>22s}")
    xs = [F(coords[g]["full"]) for g in rows]
    ys = [gmean[g] for g in rows]
    inv = sum(1 for i in range(len(xs)) for j in range(i + 1, len(xs))
              if (xs[i] - xs[j]) * (ys[i] - ys[j]) < 0)
    ties = sum(1 for i in range(len(xs)) for j in range(i + 1, len(xs)) if xs[i] == xs[j])
    tot = len(xs) * (len(xs) - 1) // 2
    print(f"  coordinate ties: {ties}/{tot} game pairs (a tie means the axis cannot order them)")

    # ---- 5. the two quantities the manuscript quotes, computed here so no shell one-liner can own
    #         a number the paper states: the rank-gaming cells split by coordinate, and the baseline
    #         term's variability WITHIN a game whose coordinate is fixed at 0.
    import spike_v4 as V4S
    cells_gt = V4S.__dict__
    res = json.load(open(os.path.join(HERE, "spike_v4_results.json")))
    cgt = res["cells_G_tau"]

    zero_games = [g for g in LADDER if F(coords[g]["full"]) == 0]
    gpos = {g: {"cells": 0, "Gpos": 0} for g in LADDER}
    for k, v in cgt.items():
        g = k.split("|")[0]
        gpos[g]["cells"] += 1
        if int(v["G"]) > 0:
            gpos[g]["Gpos"] += 1
    gpos_coord0 = sum(gpos[g]["Gpos"] for g in zero_games)
    gpos_total = sum(gpos[g]["Gpos"] for g in LADDER)

    # base (the payoff ordering's own loss) distinct values per game
    base_by_game = {}
    for k, v in tr.items():
        g = k.split("|")[0]
        if v["base"] is not None:
            base_by_game.setdefault(g, set()).add(v["base"])
    base_within_zero = max(len(base_by_game.get(g, set())) for g in zero_games)

    out = os.path.join(HERE, "analysis_transitivity_vs_transport.json")
    with open(out, "w") as f:
        json.dump({"coords": coords,
                   "per_game_pair_distinct_counts": {
                       f"{g}|{pp}": len(d) for (g, pp), d in by_gp.items()},
                   "mean_excess": {g: str(v) for g, v in gmean.items()},
                   "coord_ties": ties, "game_pairs": tot,
                   "coord_zero_games": len(zero_games),
                   "coord_nonzero_games": len(LADDER) - len(zero_games),
                   "gpos_by_game": gpos,
                   "gpos_coord0": gpos_coord0,
                   "gpos_total": gpos_total,
                   "distinct_max": max(len(d) for d in by_gp.values()),
                   "widest_pair_by_game": widest,
                   "distinct_gt1_games": len(multi),
                   "games": len(LADDER),
                   "base_distinct_by_game": {g: sorted(str(x) for x in s2)
                                             for g, s2 in base_by_game.items()},
                   "base_distinct_max_within_coord0": base_within_zero,
                   "verdict": ("no_reduction" if multi else "reduced")},
                  f, indent=2, sort_keys=True)
    print(f"\n  written: {os.path.basename(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
