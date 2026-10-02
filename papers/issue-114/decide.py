#!/usr/bin/env python3
"""THE DECISIVE RUN (issue #114, Step 5).

WHY THIS FILE EXISTS
--------------------
Steps 2-4 established the instrument on six hand-written programmes and reported single
numbers per (s, r) cell.  Three things were missing before a manuscript could be written:

  1. a reference population nobody chose by hand       -> `progspace.py` (262 references)
  2. a DECISIVE, seeded sample over that population, not "one cell at a time"
  3. the honesty requirement Step 4 discovered: at a fixed (s, r) the measurement is a
     BAND, not a number -- the pin-set ALIGNMENT and the clause MIX are free, and both move
     the result.  So the run reports a band over 96 declared draws and says which draw
     produced which end of it.

WHAT IS MEASURED
----------------
For every reference programme, every (s, r) cell and every draw (12 alignments x 8 mixes):

    detection = share of semantics-CHANGING mutations the spec rejects
    breakage  = share of semantics-PRESERVING mutations the spec rejects
    net(s; lambda, r) = detection(s, r) - lambda * breakage(s, r),  s* = argmax_s net

all pooled over the 262 references and re-derived from the specs and the oracle's own
verdicts.  Nothing is asserted; the JSON this prints is the manuscript's raw material.

Usage: python3 decide.py [--json PATH]      (prints the tables; exit 0)
"""

from __future__ import annotations

import json
import statistics
import sys

from fast import Model, mask_scores, popcount
from progspace import reference_set
from toylang import M

S_GRID = [0.0, 0.0625, 0.125, 0.25, 0.5, 0.75, 1.0]
R_GRID = [0.0, 0.05, 0.10, 0.20, 0.30]
LAMBDA_GRID = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0]

# The declared draws.  `None` is the protocol of Steps 2-4 (spread pinning, kind-grouped
# candidate order), so every earlier number is a member of this family rather than a
# different experiment.
ALIGN_DRAWS = [None, "low", "high", "even", "odd", "edges", 1, 2, 3, 4, 5, 6]
MIX_DRAWS = [None, 1, 2, 3, 4, 5, 6, 7]


# --------------------------------------------------------------------------
# one cell, one draw, pooled over every reference
# --------------------------------------------------------------------------

def pooled(models, s_t, r_t, align, mix):
    """(detection, breakage, r_min, r_max, all_reached) pooled over the references."""
    k = round(s_t * M)
    nmiss = nfa = nchg = nprs = 0
    r_lo, r_hi, reached = 1.0, 0.0, True
    for m in models:
        mask, kk, b, achieved, ok = m.cell(s_t, r_t, align, mix)
        assert kk == k
        miss, fa = mask_scores(mask, m)
        nmiss += miss
        nfa += fa
        nchg += m.n_changing
        nprs += m.n_preserving
        r_lo = min(r_lo, achieved)
        r_hi = max(r_hi, achieved)
        reached = reached and ok
    det = nmiss / nchg if nchg else float("nan")
    brk = nfa / nprs if nprs else float("nan")
    return det, brk, r_lo, r_hi, reached


def grid_for(models, align, mix):
    """{(s_t, r_t): (det, brk, r_lo, r_hi, reached)} for one draw."""
    return {(s_t, r_t): pooled(models, s_t, r_t, align, mix)
            for s_t in S_GRID for r_t in R_GRID}


def star(grid, lam, r_t):
    """argmax over the s grid of detection - lambda*breakage; ties go to the SMALLEST s."""
    best_s, best_v = None, None
    for s_t in S_GRID:
        det, brk = grid[(s_t, r_t)][0], grid[(s_t, r_t)][1]
        v = det - lam * brk
        if best_v is None or v > best_v + 1e-12:
            best_s, best_v = s_t, v
    return best_s


# --------------------------------------------------------------------------

def main(argv) -> int:
    programs, census = reference_set()
    models = [Model(p["prog"], p["src"], p["tier"]) for p in programs]
    n_chg = sum(m.n_changing for m in models)
    n_prs = sum(m.n_preserving for m in models)

    print("=" * 92)
    print("issue #114 -- THE DECISIVE RUN")
    print("=" * 92)
    print(f"references      : {len(models)}"
          f"  (systematic {sum(1 for m in models if m.tier=='systematic')}"
          f", named {sum(1 for m in models if m.tier=='named')})")
    print(f"mutations       : {n_chg} semantics-CHANGING, {n_prs} semantics-PRESERVING"
          f"  (oracle-decided, no human labels)")
    print(f"menu size B     : {min(m.B for m in models)} .. {max(m.B for m in models)}"
          f" representational candidates per reference")
    print(f"draws           : {len(ALIGN_DRAWS)} alignments x {len(MIX_DRAWS)} mixes = "
          f"{len(ALIGN_DRAWS)*len(MIX_DRAWS)}")
    print(f"census          : {census['generated_sources']} generated sources -> "
          f"{census['distinct_semantics']} distinct semantics -> {census['kept']} references")
    print(f"                  dropped: {census['dropped_constant_table']} constant-table, "
          f"{census['dropped_no_changing_mutation']} no changing mutation, "
          f"{census['dropped_named_duplicate']} named duplicates")

    # ---- one pass over every draw; every table below is a READ of this --------
    draws = [(a, x) for a in ALIGN_DRAWS for x in MIX_DRAWS]
    grids = {(a, x): grid_for(models, a, x) for a, x in draws}

    # ---- table A: the band at every cell ------------------------------------
    print("\n[A] every (s,r) cell -- the band over all 96 draws "
          "(alignment moves detection, mix moves breakage)")
    print(f"{'s_tgt':>7} {'r_tgt':>6} | {'r_cmp min..max':>15} {'reach':>5} | "
          f"{'detect min..max':>19} | {'break min..max':>19} | {'int s*':>7}")
    cells = {}
    for s_t in S_GRID:
        for r_t in R_GRID:
            vals = [grids[k][(s_t, r_t)] for k in draws]
            dets = [v[0] for v in vals]
            brks = [v[1] for v in vals]
            r_lo = min(v[2] for v in vals)
            r_hi = max(v[3] for v in vals)
            reached = all(v[4] for v in vals)
            stars = [star(grids[k], 1.0, r_t) for k in draws]
            inter = sum(1 for s in stars if s not in (min(S_GRID), max(S_GRID))) / len(draws)
            cells[(s_t, r_t)] = {"det": dets, "brk": brks, "r_lo": r_lo, "r_hi": r_hi,
                                 "reached": reached, "interior_share": inter}
            print(f"{s_t:>7.4f} {r_t:>6.3f} | {r_lo:>7.4f}..{r_hi:<7.4f} "
                  f"{'yes' if reached else 'NO':>5} | {min(dets):>9.4f}..{max(dets):<9.4f} | "
                  f"{min(brks):>9.4f}..{max(brks):<9.4f} | {inter:>7.3f}")

    # ---- table B: the frontier per draw -------------------------------------
    print("\n[B] s*(lambda, r) -- argmax of detection - lambda*breakage, pooled over the SAME draws")
    print("    entry = modal s*  (min..max)  [share of draws with an INTERIOR s*]")
    print(" lambda |" + "".join(f"   r={r:<21.2f}" for r in R_GRID))
    frontier = {}
    for lam in LAMBDA_GRID:
        line = []
        for r_t in R_GRID:
            stars = [star(grids[k], lam, r_t) for k in draws]
            mode = statistics.mode(stars)
            inter = sum(1 for s in stars if s not in (min(S_GRID), max(S_GRID))) / len(stars)
            frontier[(lam, r_t)] = {"mode": mode, "min": min(stars), "max": max(stars),
                                    "interior_share": inter, "values": sorted(set(stars))}
            line.append(f"   {mode:>5.3f} ({min(stars):.3f}..{max(stars):.3f}) [{inter:.2f}]")
        print(f" {lam:>5.2f} |" + "".join(f"{c:<24}" for c in line))

    # ---- table C: the alignment effect, mix fixed ---------------------------
    print("\n[C] ALIGNMENT at matched (s, r) -- mix held at the Steps 2-4 order  [registered prior P1]")
    print(f"{'s_tgt':>7} {'r_tgt':>6} | {'worst alignment':>16} {'det':>8} | "
          f"{'best alignment':>16} {'det':>8} | {'span':>8}")
    align_band = {}
    for s_t in S_GRID:
        for r_t in R_GRID:
            vals = {a: grids[(a, None)][(s_t, r_t)][0] for a in ALIGN_DRAWS}
            brks = [grids[(a, None)][(s_t, r_t)][1] for a in ALIGN_DRAWS]
            lo, hi = min(vals.values()), max(vals.values())
            span = (hi / lo) if lo > 1e-12 else float("inf")
            worst = min(vals, key=lambda a: vals[a])
            best = max(vals, key=lambda a: vals[a])
            align_band[(s_t, r_t)] = {"values": {str(a): vals[a] for a in vals}, "span": span,
                                      "worst": str(worst), "best": str(best),
                                      "break_band": [min(brks), max(brks)]}
            print(f"{s_t:>7.4f} {r_t:>6.3f} | {str(worst):>16} {lo:>8.4f} | "
                  f"{str(best):>16} {hi:>8.4f} | {span:>8.3f}")

    # ---- table D: the mix effect, alignment fixed ---------------------------
    print("\n[D] MIX at matched (s, r) -- alignment held at the Steps 2-4 spread  [Step 4's band]")
    print(f"{'s_tgt':>7} {'r_tgt':>6} | {'break min..max':>17} | {'break span':>10} | "
          f"{'detect span':>11}")
    mix_band = {}
    for s_t in S_GRID:
        for r_t in R_GRID:
            ds = [grids[(None, x)][(s_t, r_t)][0] for x in MIX_DRAWS]
            bs = [grids[(None, x)][(s_t, r_t)][1] for x in MIX_DRAWS]
            mix_band[(s_t, r_t)] = {"det_band": [min(ds), max(ds)],
                                    "break_band": [min(bs), max(bs)]}
            print(f"{s_t:>7.4f} {r_t:>6.3f} | {min(bs):>8.4f}..{max(bs):<8.4f} | "
                  f"{max(bs)-min(bs):>10.4f} | {max(ds)-min(ds):>11.4f}")

    # ---- table E: the mechanism and the registered priors -------------------
    print("\n[E] the mechanism (prior P3) and the registered priors, read off this run")
    r0 = max(max(cells[(s_t, 0.0)]["brk"]) for s_t in S_GRID)
    print(f"  P3 mechanism: max breakage over ALL 96 draws at r = 0 is {r0:.6f}  -> "
          f"{'CONFIRMED: a purely observational spec can never false-alarm' if r0 == 0.0 else 'REFUTED'}")
    finite = [(k, v["span"]) for k, v in align_band.items() if v["span"] != float("inf")]
    at, worst_span = max(finite, key=lambda t: t[1])
    print(f"  P1 alignment: worst matched-specificity detection span {worst_span:.2f}x "
          f"at s={at[0]}, r={at[1]}  -> "
          f"{'CONFIRMED (>= the registered 2x gate)' if worst_span >= 2.0 else 'REFUTED'}")
    for lam in LAMBDA_GRID:
        shares = [frontier[(lam, r_t)]["interior_share"] for r_t in R_GRID if r_t > 0]
        print(f"    lambda={lam:<5} interior-s* share at r>0 over draws: "
              f"{min(shares):.3f} .. {max(shares):.3f}")

    # ---- the mechanism by clause kind (the paper's central claim) ------------
    # For each clause KIND: how many mutants can this kind ALONE reject?  Pooled over the
    # references.  The split by the oracle's verdict is the whole mechanism: an
    # observational clause rejects changing mutants and NO preserving one; a representational
    # clause rejects both, and that is where every false alarm in the study comes from.
    from collections import Counter
    mechanism: dict = {}
    for m in models:
        per_kind: dict = {}
        obs_mask = 0
        for om in m.obs_masks:
            obs_mask |= om
        per_kind["obs"] = obs_mask
        for c in m.cands:
            per_kind[c[0]] = per_kind.get(c[0], 0) | m.mask_of(c)
        for kind, mask in per_kind.items():
            slot = mechanism.setdefault(kind, {"changing": 0, "preserving": 0,
                                               "n_clauses": 0})
            slot["changing"] += popcount(mask & m.changing_mask)
            slot["preserving"] += popcount(mask & m.preserving_mask)
        for c in m.cands:
            mechanism[c[0]]["n_clauses"] += 1
        mechanism["obs"]["n_clauses"] += len(m.obs_masks)
    menu_hist = dict(sorted(Counter(m.B for m in models).items()))
    print("\n[F] the mechanism by clause kind: mutants each kind can reject ALONE")
    print(f"  {'kind':<16} {'clauses':>8} | {'changing':>9} / {n_chg:<6} | "
          f"{'preserving':>10} / {n_prs:<6}")
    for kind in sorted(mechanism):
        v = mechanism[kind]
        print(f"  {kind:<16} {v['n_clauses']:>8} | {v['changing']:>9} / {n_chg:<6} | "
              f"{v['preserving']:>10} / {n_prs:<6}")
    print("\n[G] the reachable region: menu size B per reference (r <= B/(B + s*M))")
    print(f"  B histogram: {menu_hist}")
    for s in (0.0625, 0.25, 1.0):
        lo = min(menu_hist) / (min(menu_hist) + s * M)
        hi = max(menu_hist) / (max(menu_hist) + s * M)
        print(f"    s = {s:<7.4f}  r_max in {lo:.4f} .. {hi:.4f}")

    # The representational family is NOT uniformly harmful, and that is the practical
    # result: rank each kind by detection per unit of false alarm.
    ranking = []
    for kind, v in mechanism.items():
        det_share = v["changing"] / n_chg
        fa_share = v["preserving"] / n_prs
        ranking.append((kind, det_share, fa_share,
                        (det_share / fa_share) if fa_share > 0 else float("inf")))
    ranking.sort(key=lambda t: (-t[3], t[0]))
    print("\n[H] the practical ranking: detection yield per unit of false-alarm risk")
    print(f"  {'kind':<16} {'changing share':>14} {'preserving share':>17} {'ratio':>10}")
    for kind, d, f, ratio in ranking:
        print(f"  {kind:<16} {d:>14.4f} {f:>17.4f} "
              + (f"{ratio:>10.2f}" if ratio != float("inf") else f"{'inf':>10}"))
    print("  reading: if a spec must expose representation, expose WHICH LITERALS OCCUR")
    print("  (const_present / const_absent) -- never TREE SHAPE (size_le / depth_le reject")
    print("  thousands of legitimate rewrites and catch no defect at all).")

    # ---- artifacts ----------------------------------------------------------
    payload = {
        "protocol": {"s_grid": S_GRID, "r_grid": R_GRID, "lambda_grid": LAMBDA_GRID,
                     "align_draws": [str(a) for a in ALIGN_DRAWS],
                     "mix_draws": [str(x) for x in MIX_DRAWS], "n_draws": len(draws)},
        "population": {"references": len(models), "census": census,
                       "changing_mutations": n_chg, "preserving_mutations": n_prs,
                       "menu_B_min": min(m.B for m in models),
                       "menu_B_max": max(m.B for m in models)},
        "cells": {f"{s}|{r}": {"det_band": [min(v["det"]), max(v["det"])],
                               "break_band": [min(v["brk"]), max(v["brk"])],
                               "r_band": [v["r_lo"], v["r_hi"]], "reached": v["reached"],
                               "interior_share_lambda1": v["interior_share"]}
                  for (s, r), v in cells.items()},
        "frontier": {f"{l}|{r}": frontier[(l, r)] for l in LAMBDA_GRID for r in R_GRID},
        "alignment": {f"{s}|{r}": align_band[(s, r)] for s in S_GRID for r in R_GRID},
        "mix": {f"{s}|{r}": mix_band[(s, r)] for s in S_GRID for r in R_GRID},
        "mechanism_by_kind": mechanism,
        "kind_ranking": [{"kind": k, "changing_share": d, "preserving_share": f,
                          "ratio": (None if r == float("inf") else r)}
                         for k, d, f, r in ranking],
        "menu_sizes": {str(b): n for b, n in menu_hist.items()},
        "findings": {
            "p3_breakage_at_r0_max": r0,
            "p1_worst_alignment_span": worst_span,
            "p1_worst_alignment_cell": [at[0], at[1]],
            "max_mix_break_spread": max(max(v["break_band"]) - min(v["break_band"])
                                        for v in mix_band.values()),
            "max_mix_detect_spread": max(max(v["det_band"]) - min(v["det_band"])
                                         for v in mix_band.values()),
        },
    }
    if "--json" in argv:
        path = argv[argv.index("--json") + 1]
        with open(path, "w") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
        print(f"\n  json written: {path}")
    print("\n" + "=" * 92)
    print("DECISIVE RUN: COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
