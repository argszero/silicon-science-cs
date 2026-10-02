#!/usr/bin/env python3
"""Detection/breakage sweep and the frontier curve (issue #114).

For each base program and each (s_target, r_target) cell, build the specification,
verify its COMPUTED (s, r), then measure over that program's whole single-site
mutation population (verdicts from the semantics oracle):

    detection = share of semantics-CHANGING mutations the spec rejects
    breakage  = share of semantics-PRESERVING mutations the spec rejects

and the graded net value

    net(s; lambda, r) = detection(s, r) - lambda * breakage(s, r)

whose argmax over s is `s*(lambda, r)`.  Nothing here is asserted: s, r, detection
and breakage are all recomputed from the specs and the oracle's own verdicts.

Usage: python3 frontier.py            (prints the tables; exit 0)
"""

from __future__ import annotations

import sys

from mutations import enumerate_mutations
from oracle import classify
from specs import clause_counts, exposure, make_spec, satisfies, specificity

from toylang import parse

BASE_PROGRAMS = [
    "(add x 1)",
    "(mul x x)",
    "(max (min x 200) 10)",
    "(ite (lt x 128) (mul x 2) (sub 200 x))",
    "(mod (add (mul x 3) 7) 5)",
    "(ite (and (lt x 100) (not (lt x 50))) (sub x 50) x)",
]

S_GRID = [0.0, 0.125, 0.25, 0.375, 0.5, 0.75, 1.0]
R_GRID = [0.0, 0.05, 0.10, 0.20]
LAMBDA_GRID = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0]


def population(prog):
    """Every single-site mutation of `prog`, split by the ORACLE's verdict."""
    changing, preserving = [], []
    for m in enumerate_mutations(prog):
        ok, _ = classify(prog, m["mutant"])
        (preserving if ok else changing).append(m["mutant"])
    return changing, preserving


def measure(spec, changing, preserving):
    misses = sum(1 for m in changing if not satisfies(spec, m))
    false_alarms = sum(1 for m in preserving if not satisfies(spec, m))
    det = misses / len(changing) if changing else float("nan")
    brk = false_alarms / len(preserving) if preserving else float("nan")
    return det, brk, misses, false_alarms


def main() -> int:
    programs = [parse(s) for s in BASE_PROGRAMS]
    pops = [population(p) for p in programs]
    n_chg = sum(len(c) for c, _ in pops)
    n_prs = sum(len(p) for _, p in pops)
    print("=" * 84)
    print("issue #114 -- detection / breakage sweep over the graded specification family")
    print(f"base programs: {len(programs)}   mutations: {n_chg} changing, {n_prs} preserving")
    print("=" * 84)

    # ---- the (s, r) grid, pooled over base programs -------------------------
    print("\n[s, r] cells -- 'computed(s,r)' is re-derived from the spec, never assumed")
    print(f"{'s_tgt':>6} {'r_tgt':>6} | {'s_cmp':>6} {'r_cmp':>6} | {'detect':>7} {'break':>7}"
          f" | {'reached':>7} | clauses(obs+struct)")
    grid = {}
    for s_t in S_GRID:
        for r_t in R_GRID:
            specs = [make_spec(p, s_t, r_t) for p in programs]
            s_cmp = sum(specificity(x) for x in specs) / len(specs)
            r_cmp = sum(exposure(x) for x in specs) / len(specs)
            chg = sum(sum(len(c) for c in [pops[i][0]]) for i in range(len(programs)))
            misses = sum(sum(1 for m in pops[i][0] if not satisfies(specs[i], m))
                         for i in range(len(programs)))
            fa = sum(sum(1 for m in pops[i][1] if not satisfies(specs[i], m))
                     for i in range(len(programs)))
            det = misses / chg
            brk = fa / n_prs
            n_obs = sum(clause_counts(x)[0] for x in specs)
            n_st = sum(clause_counts(x)[1] for x in specs)
            reached = all(x["r_reachable"] for x in specs)
            grid[(s_t, r_t)] = (s_cmp, r_cmp, det, brk)
            print(f"{s_t:>6.3f} {r_t:>6.3f} | {s_cmp:>6.3f} {r_cmp:>6.3f} | {det:>7.4f} {brk:>7.4f}"
                  f" | {'yes' if reached else 'NO':>7} | {n_obs}+{n_st}")

    # ---- the mechanism, at matched specificity ------------------------------
    print("\n[mechanism] breakage at matched computed specificity, across exposure")
    print(f"{'s':>6} | " + " ".join(f"r={r:<5.2f}" for r in R_GRID) + "   (breakage)")
    for s_t in S_GRID:
        if s_t == 0.0:
            continue
        row = []
        for r_t in R_GRID:
            _, r_cmp, _, brk = grid[(s_t, r_t)]
            row.append(f"{brk:7.4f}")
        print(f"{s_t:>6.2f} | " + " ".join(row))

    # ---- the frontier: argmax over s of detection - lambda*breakage ---------
    print("\n[frontier] s*(lambda, r) = argmax_s [ detection(s,r) - lambda*breakage(s,r) ]")
    header = "  lambda |" + "".join(f"   r={r:<4.2f}" for r in R_GRID)
    print(header)
    for lam in LAMBDA_GRID:
        cells = []
        for r_t in R_GRID:
            best_s, best_v = None, None
            for s_t in S_GRID:
                _, _, det, brk = grid[(s_t, r_t)]
                v = det - lam * brk
                if best_v is None or v > best_v + 1e-12:
                    best_s, best_v = s_t, v
            interior = best_s not in (min(S_GRID), max(S_GRID))
            cells.append(f"{best_s:.3f}{'*' if interior else ' '}")
        print(f"  {lam:>6.2f} |" + "".join(f"   {c:<6}" for c in cells))
    print("  ('*' marks an INTERIOR s*, i.e. not at either end of the s grid)")

    # ---- two-sided sanity on the curves -------------------------------------
    print("\n[shape] detection and breakage vs s, at the highest reachable exposure")
    r_hi = max(r for r in R_GRID if any(grid[(s, r)][1] > 0 for s in S_GRID))
    print(f"  r target {r_hi}")
    print(f"{'s':>6} | {'detect':>7} {'break':>7}")
    for s_t in S_GRID:
        _, _, det, brk = grid[(s_t, r_hi)]
        print(f"{s_t:>6.2f} | {det:>7.4f} {brk:>7.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
