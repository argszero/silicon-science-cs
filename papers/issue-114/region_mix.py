#!/usr/bin/env python3
"""The reachable (s, r) region, and the MIX BAND of the exposure axis (issue #114).

Two questions the enriched menu makes answerable, both about whether the exposure axis
is as well-defined as the design assumes.

1. THE REACHABLE REGION.  `r = b / (b + |obs|)` with `b <= B(prog)`, the number of
   representational clauses the reference's syntax offers.  So the (s, r) plane is not a
   rectangle: the reachable region is bounded by

       r <= B / (B + s*M)

   A high-specificity spec simply cannot carry much exposure, because it already spends
   `s*M` clauses on observable behaviour.  Reported per program, with the ceiling at
   s = 1 -- and it is a real constraint on what the study may claim, not an artefact.

2. THE MIX BAND.  A spec's clause list is a PREFIX of the candidate list, so which
   KINDS fill a given `r` depends on the ordering.  If breakage depended on the kind
   mix rather than on the amount of exposure, the whole r axis would be confounded.
   `mix` reshuffles the candidates with the same count (so `r` is unchanged) and we
   report the spread of detection and breakage across mixes -- plus whether the
   frontier conclusion survives in EVERY mix separately.

Usage: python3 region_mix.py
"""

from __future__ import annotations

import statistics
import sys

from frontier import BASE_PROGRAMS, population
from specs import (exposure, make_spec, mixed_candidates, representational_candidates,
                   satisfies, specificity)
from toylang import parse

S_GRID = [0.0, 0.125, 0.25, 0.5, 0.75, 1.0]
R_GRID = [0.0, 0.05, 0.10, 0.20]
MIXES = [None, 1, 2, 3, 4, 5]
LAMBDA_GRID = [0.25, 0.5, 1.0, 2.0]


def cell(programs, pops, s_t, r_t, mix):
    """detection, breakage at (s_t, r_t) under one candidate ordering."""
    specs = [make_spec(p, s_t, r_t, mix=mix) for p in programs]
    chg = sum(len(c) for c, _ in pops)
    n_prs = sum(len(p) for _, p in pops)
    miss = sum(sum(1 for m in pops[i][0] if not satisfies(specs[i], m))
               for i in range(len(programs)))
    fa = sum(sum(1 for m in pops[i][1] if not satisfies(specs[i], m))
             for i in range(len(programs)))
    return miss / chg, fa / n_prs


def main() -> int:
    programs = [parse(s) for s in BASE_PROGRAMS]
    pops = [population(p) for p in programs]
    print("=" * 86)
    print("issue #114 -- reachable (s, r) region, and the mix band of the exposure axis")
    print("=" * 86)

    # ---- 1. the reachable region -------------------------------------------
    print("\n[1] reachable region: r is bounded by B/(B + s*M), B = menu size")
    print(f"{'program':<46} {'B':>4} | {'r_max(s=1.0)':>12} {'r_max(s=0.25)':>13} {'r_max(s=0.0625)':>15}")
    for src, p in zip(BASE_PROGRAMS, programs):
        B = len(representational_candidates(p))
        row = [B / (B + s * 256) for s in (1.0, 0.25, 0.0625)]
        print(f"{src[:46]:<46} {B:>4} | {row[0]:>12.4f} {row[1]:>13.4f} {row[2]:>15.4f}")
    print("\n  reading: exposure is CHEAP at low specificity and capped at high specificity --")
    print("  the plane is a bounded region, which is a limitation to state, not to hide.")

    # ---- 2. the mix band ---------------------------------------------------
    print("\n[2] mix band: the SAME (s, r) under six candidate orderings")
    print(f"{'s_t':>6} {'r_t':>6} | {'r_cmp':>6} (invariant?) | {'detect min..max':>19} | "
          f"{'break min..max':>19} | {'break spread':>12}")
    worst_spread, r_mismatch = 0.0, []
    for s_t in S_GRID:
        for r_t in R_GRID:
            # invariance is PER PROGRAM: two references have different menu sizes B and
            # therefore legitimately different r at the same request, so the check is
            # that a given program's r does not move when the ORDER moves.
            per_prog = {i: set() for i in range(len(programs))}
            dts, brs = [], []
            for mix in MIXES:
                specs = [make_spec(p, s_t, r_t, mix=mix) for p in programs]
                for i, x in enumerate(specs):
                    per_prog[i].add(round(exposure(x), 12))
                d, b = cell(programs, pops, s_t, r_t, mix)
                dts.append(d)
                brs.append(b)
            moved = {i: sorted(v) for i, v in per_prog.items() if len(v) != 1}
            if moved:
                r_mismatch.append((s_t, r_t, moved))
            spread = (max(brs) - min(brs))
            worst_spread = max(worst_spread, spread)
            r_lo, r_hi = min(next(iter(v)) for v in per_prog.values()), \
                max(next(iter(v)) for v in per_prog.values())
            print(f"{s_t:>6.3f} {r_t:>6.3f} | {r_lo:>6.4f} {'yes' if not moved else 'NO':>11} | "
                  f"{min(dts):>9.4f}..{max(dts):<9.4f} | {min(brs):>9.4f}..{max(brs):<9.4f} | "
                  f"{spread:>12.4f}")

    print(f"\n  [control M1] exposure is INVARIANT to the mix (same clause count): "
          f"{'PASS' if not r_mismatch else 'FAIL ' + str(r_mismatch[:2])}")
    print(f"  [control M2] the mix changes the numbers, as the design intends: "
          f"{'PASS' if worst_spread > 0 else 'FAIL (no composition dependence at all)'}"
          f"  (worst breakage spread {worst_spread:.4f})")
    print("  reading: the r axis has a COMPOSITION component. The band is reported, not")
    print("  averaged away -- a claim about r must hold across the band or be narrowed.")

    # ---- 3. does the frontier conclusion survive in every mix? -------------
    print("\n[3] robustness: is the frontier's shape the same under every mix?")
    print("    s*(lambda, r) per mix -- the claim is: r=0 -> s*=1.0 (boundary) at every lambda;")
    print("    r>0 -> an INTERIOR s* for at least one lambda, in every mix.")
    shapes = {}
    for mix in MIXES:
        grid = {}
        for s_t in S_GRID:
            for r_t in R_GRID:
                grid[(s_t, r_t)] = cell(programs, pops, s_t, r_t, mix)
        row = []
        for lam in LAMBDA_GRID:
            for r_t in R_GRID:
                best_s, best_v = None, None
                for s_t in S_GRID:
                    det, brk = grid[(s_t, r_t)]
                    v = det - lam * brk
                    if best_v is None or v > best_v + 1e-12:
                        best_s, best_v = s_t, v
            row.append((lam, r_t, best_s))
        claim = all((bs == 1.0) for (l, r, bs) in row if r == 0.0)
        shapes[mix] = (row, claim)
        cols = []
        for lam in LAMBDA_GRID:
            cells = " ".join(f"{bs:.2f}" for (l, r, bs) in row if l == lam)
            cols.append(f"{cells:>26}")
        print(f"    {str(mix):<5} | " + " | ".join(cols))
    print("    ^ columns are lambda = " + ", ".join(str(l) for l in LAMBDA_GRID)
          + "; within a column: r = " + ", ".join(f"{r}" for r in R_GRID))

    all_ok = all(v[1] for v in shapes.values())
    inter = {mix: [bs for (l, r, bs) in row if r > 0 and 0 < bs < 1.0]
             for mix, (row, _) in shapes.items()}
    print(f"\n  [control M3] 'r = 0 pins s* at the boundary' holds in EVERY mix: "
          f"{'PASS' if all_ok else 'FAIL'}")
    print(f"  [control M4] interior s* appears for r > 0 in every mix: "
          f"{'PASS' if all(inter[m] for m in MIXES) else 'FAIL ' + str({k: len(v) for k, v in inter.items()})}")

    print("\n" + "=" * 86)
    bad = (not r_mismatch) and worst_spread > 0 and all_ok and all(inter[m] for m in MIXES)
    print("REGION/MIX: " + ("ALL PASS" if bad else "CHECK ABOVE"))
    return 0 if bad else 1


if __name__ == "__main__":
    sys.exit(main())
