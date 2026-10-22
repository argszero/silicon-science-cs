#!/usr/bin/env python3
"""R5 and R6 — two analyses the revision round owes, over cells the package already ships.

R5. The reduction test in §10 measures the transport excess against the **cyclic-fraction
    coordinate only**, while Czarnecki et al.'s construction is two-dimensional: transitive
    strength upright, cycles radial, both read at a population. So the question the paragraph
    leaves open is whether the across-protocol spread at a fixed population pair *survives
    conditioning on the other axis* — transitive strength and population size. Answering it
    needs no new data: the design space is enumerated, `analysis_transitivity_vs_transport.json`
    stores the coordinate and the policy count per (game, population), and
    `spike_v4_results.json` stores the excess per (game, protocol, population pair).

R6. The four-bidder common-value game `cv_n4` carries no certified anchor ("counted everywhere
    and independently confirmed nowhere"). The three headline numbers are re-reported with its
    cells excluded, so a reader can see how far the anchor-free game carries the result.

Exact rationals throughout (`Fraction`), no seed and no draw. Every printed number is stored in
the JSON this script writes, so §10's sentences can bind to keys instead of to prose.

Usage: python3 analysis_conditioning.py [--json-out FILE]
Exit: 0 on success, 1 if an invariant below fails.
"""
import argparse
import json
import sys
from collections import OrderedDict, defaultdict
from fractions import Fraction as F

SRC = "spike_v4_results.json"
TRANS = "analysis_transitivity_vs_transport.json"
ANCHOR_FREE = "cv_n4"          # certified_absent == true; the report's own label


def load():
    with open(SRC) as f:
        v4 = json.load(f)
    with open(TRANS) as f:
        tr = json.load(f)
    return v4, tr


def pairs_by_game_pop(transport):
    """{(game, 'popA>popB'): {protocol: excess}} from the transport block."""
    out = defaultdict(dict)
    for key, cell in transport.items():
        game, protocol, pair = key.split("|")
        out[(game, pair)][protocol] = F(cell["excess"])
    return out


def support(coords, game, pop):
    """Population size = how many policies carry weight (the coordinate's own `n_policies`)."""
    return coords[game]["pop"][pop]["n_policies"]


def coord(coords, game, pop):
    return F(coords[game]["pop"][pop]["coord"].replace(" ", "")) if False else \
        F(coords[game]["pop"][pop]["coord"])


def spread_record(vals):
    xs = sorted(set(vals))
    return {"n_protocols": len(vals), "n_distinct": len(xs),
            "low": str(xs[0]), "high": str(xs[-1]), "distinct": [str(x) for x in xs]}


def condense(cells, label):
    """Summarise spread under one conditioning.

    `cells` maps a conditioning key -> list of per-pair spread records. The question is not
    "is the mean spread large" but "does any conditioning cell collapse it", so the statistic
    reported is the MINIMUM distinct count over the pairs inside each cell.
    """
    rows = []
    for k in sorted(cells, key=lambda x: str(x)):
        recs = cells[k]
        rows.append({
            "conditioning": str(k),
            "n_pairs": len(recs),
            "min_distinct": min(r["n_distinct"] for r in recs),
            "max_distinct": max(r["n_distinct"] for r in recs),
            "min_spread": str(min(F(r["high"]) - F(r["low"]) for r in recs)),
        })
    return {"label": label,
            "cells": rows,
            "all_cells_show_spread": all(r["min_distinct"] >= 2 for r in rows),
            "min_distinct_over_all_cells": min(r["min_distinct"] for r in rows) if rows else None}


def r6(v4, drop):
    """Re-report the three headline numbers with `drop`'s cells excluded."""
    def keep(cell_key):
        return not cell_key.startswith(drop + "|")

    # (1) G > 0 cells
    total = gp = 0
    for key, cell in v4["cells_G_tau"].items():
        if not keep(key):
            continue
        total += 1
        gp += 1 if cell["G"] > 0 else 0

    # (2) inclusion: gameable (G>0 and not faithful) strictly inside fragile (tau<1)
    gameable = fragile = 0
    counterexamples = 0
    for key, cell in v4["cells_G_tau"].items():
        if not keep(key):
            continue
        tau = F(cell["tau"])
        g = cell["G"]
        if g > 0 and tau < 1:
            gameable += 1
        if tau < 1:
            fragile += 1
        if g > 0 and tau >= 1:
            counterexamples += 1

    # (3) protocol variance vs population variance, per game
    per_game = {}
    for game, rec in v4["factor_split"].items():
        if game == drop:
            continue
        per_game[game] = {
            "ratio": str(F(rec["MS_protocol"]) / F(rec["MS_population"])),
            "protocol_exceeds_population": rec["protocol_exceeds_population"],
        }
    ratios = sorted(F(r["ratio"]) for r in per_game.values())
    return {
        "excluded_game": drop,
        "g_positive": gp,
        "cells": total,
        "share": str(F(gp, total)) if total else None,
        "gameable_cells": gameable,
        "fragile_cells": fragile,
        "strictly_contains": gameable <= fragile,
        "g_positive_without_fragility": counterexamples,
        "games": len(per_game),
        "protocol_exceeds_population": sum(
            1 for r in per_game.values() if r["protocol_exceeds_population"]),
        "ratio_min": str(ratios[0]),
        "ratio_max": str(ratios[-1]),
        # the paper prints 3 decimals; the exact rational is kept beside it so the printed
        # form has a key of its own (a value no key holds is a number the gate cannot police)
        "ratio_min_3dp": round(float(ratios[0]), 3),
        "ratio_max_3dp": round(float(ratios[-1]), 3),
        "ratio_min_game": min(per_game, key=lambda g: F(per_game[g]["ratio"])),
        "ratio_max_game": max(per_game, key=lambda g: F(per_game[g]["ratio"])),
        "per_game": per_game,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", default="analysis_conditioning.json")
    a = ap.parse_args()

    v4, tr = load()
    coords = tr["coords"]
    by_pair = pairs_by_game_pop(v4["transport"])

    # ---------------- R5 -------------------------------------------------------------------
    per_pair_spread = OrderedDict()
    by_coord = defaultdict(list)
    by_size = defaultdict(list)
    by_both = defaultdict(list)
    for (game, pair), vals in sorted(by_pair.items()):
        popA, popB = pair.split(">")
        rec = spread_record(list(vals.values()))
        per_pair_spread["%s|%s" % (game, pair)] = rec
        cA, cB = coord(coords, game, popA), coord(coords, game, popB)
        nA, nB = support(coords, game, popA), support(coords, game, popB)
        by_coord["coord(%s,%s)" % (cA, cB)].append(rec)
        by_size["size(%d,%d)" % (nA, nB)].append(rec)
        by_both["coord(%s,%s)&size(%d,%d)" % (cA, cB, nA, nB)].append(rec)

    c1 = condense(by_coord, "transitive strength only (the coordinate pair)")
    c2 = condense(by_size, "population size only (policy count pair)")
    c3 = condense(by_both, "both at once (coordinate pair AND size pair)")

    # the sharpest form: games whose coordinate is zero at EVERY population, so the coordinate
    # pair is (0,0) for every pair -- conditioning on it pins it completely.
    zero_games = [g for g in coords
                  if all(F(p["coord"]) == 0 for p in coords[g]["pop"].values())]
    zero_only = {}
    for (game, pair), vals in by_pair.items():
        if game in zero_games:
            zero_only["%s|%s" % (game, pair)] = spread_record(list(vals.values()))
    zero_min = min((r["n_distinct"] for r in zero_only.values()), default=None)
    zero_max = max((r["n_distinct"] for r in zero_only.values()), default=None)

    r5 = {
        "pairs": len(per_pair_spread),
        "conditioning_on_transitive_strength": c1,
        "conditioning_on_population_size": c2,
        "conditioning_on_both": c3,
        "coord_zero_at_every_population_games": sorted(zero_games),
        "coord_zero_game_pairs": len(zero_only),
        "coord_zero_min_distinct": zero_min,
        "coord_zero_max_distinct": zero_max,
    }
    r5["verdict"] = ("survives_both_conditionings"
                     if (c1["all_cells_show_spread"] and c2["all_cells_show_spread"]
                         and c3["all_cells_show_spread"])
                     else "collapses_under_conditioning")

    # ---------------- R6 -------------------------------------------------------------------
    r6_full = r6(v4, drop="__none__")
    r6_excl = r6(v4, drop=ANCHOR_FREE)

    out = OrderedDict([
        ("source", {"spike_v4_results": SRC, "transitivity": TRANS}),
        ("anchor_free_game", ANCHOR_FREE),
        ("R5", r5),
        ("R6", OrderedDict([("all_games", r6_full), ("anchor_free_excluded", r6_excl)])),
        ("per_pair_spread", per_pair_spread),
    ])
    blob = json.dumps(out, indent=1, sort_keys=False)
    with open(a.json_out, "w") as f:
        f.write(blob + "\n")

    # ---------------- report ---------------------------------------------------------------
    print("R5  spread survives transitive-strength conditioning: %s (min distinct %s)"
          % (c1["all_cells_show_spread"], c1["min_distinct_over_all_cells"]))
    print("R5  spread survives population-size conditioning:     %s (min distinct %s)"
          % (c2["all_cells_show_spread"], c2["min_distinct_over_all_cells"]))
    print("R5  spread survives both at once:                     %s (min distinct %s)"
          % (c3["all_cells_show_spread"], c3["min_distinct_over_all_cells"]))
    print("R5  coordinate zero at every population: %d games, %d pairs, distinct %s..%s"
          % (len(zero_games), len(zero_only), zero_min, zero_max))
    print("R5  VERDICT: %s" % r5["verdict"])
    print()
    for tag, rec in (("all 9 games", r6_full), ("cv_n4 excluded", r6_excl)):
        print("R6  %-16s G>0 %d/%d (%s)  gameable %d ⊂ fragile %d (%s)  counterexamples %d"
              % (tag, rec["g_positive"], rec["cells"], rec["share"],
                 rec["gameable_cells"], rec["fragile_cells"],
                 "yes" if rec["strictly_contains"] else "NO",
                 rec["g_positive_without_fragility"]))
        print("R6  %-16s protocol>population in %d/%d games, ratio %s..%s (%s..%s)"
              % (tag, rec["protocol_exceeds_population"], rec["games"],
                 rec["ratio_min"], rec["ratio_max"],
                 rec["ratio_min_game"], rec["ratio_max_game"]))

    # ---------------- invariants ------------------------------------------------------------
    ok = True
    if r5["verdict"] != "survives_both_conditionings":
        print("FAIL: the spread does not survive conditioning; §10 must carry the scope clause")
        ok = False
    if r6_full["g_positive"] != v4["T3_inclusion"]["gameable_cells"]:
        print("FAIL: recomputed gameable cells %d != artifact's %d"
              % (r6_full["g_positive"], v4["T3_inclusion"]["gameable_cells"]))
        ok = False
    if r6_full["fragile_cells"] != v4["T3_inclusion"]["fragile_cells"]:
        print("FAIL: recomputed fragile cells %d != artifact's %d"
              % (r6_full["fragile_cells"], v4["T3_inclusion"]["fragile_cells"]))
        ok = False
    if r6_excl["g_positive_without_fragility"] != 0:
        print("FAIL: the exclusion changed the 0-counterexample result")
        ok = False
    print("\nartifact: %s" % a.json_out)
    print("VERDICT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
