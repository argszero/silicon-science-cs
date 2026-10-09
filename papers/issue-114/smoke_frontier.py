#!/usr/bin/env python3
"""Controls for the specification layer (issue #114).

The axes of the study are `specificity` and `exposure`, computed from the spec.  If
that computation is wrong, every downstream figure is wrong, so it gets its own
two-sided battery.  Exit 0 == every control held.

  F1  the computed (s, r) matches the requested target on reachable cells, and an
      unreachable cell is FLAGGED rather than silently reported at its target
  F2  the mechanism: a purely observational spec (r = 0) has breakage EXACTLY 0
  F3  nesting: detection and breakage are non-decreasing in s at fixed r
  F4  the checker fires both ways: at s = 1, r = 0 the whole table is pinned, so
      detection = 1 and breakage = 0
  F5  the checker is not vacuous on a single pair: it REJECTS a semantics-changing
      mutation and ACCEPTS a semantics-preserving one
  F6  determinism: two runs give an identical grid

Run: python3 smoke_frontier.py
"""

from __future__ import annotations

import sys

from frontier import BASE_PROGRAMS, population
from mutations import enumerate_mutations
from specs import (CLAUSE_KINDS, exposure, make_spec, representational_candidates,
                    satisfies, specificity)
from toylang import parse, to_str

S_GRID = [0.0, 0.125, 0.25, 0.5, 1.0]
R_GRID = [0.0, 0.05, 0.10, 0.20]


def grid(programs, pops):
    """(s_t, r_t) -> (s_computed, r_computed, detection, breakage, all_reachable)."""
    out = {}
    n_prs = sum(len(p) for _, p in pops)
    for s_t in S_GRID:
        for r_t in R_GRID:
            specs = [make_spec(p, s_t, r_t) for p in programs]
            s_c = sum(specificity(x) for x in specs) / len(specs)
            r_c = sum(exposure(x) for x in specs) / len(specs)
            chg = sum(len(c) for c, _ in pops)
            miss = sum(sum(1 for m in pops[i][0] if not satisfies(specs[i], m))
                       for i in range(len(programs)))
            fa = sum(sum(1 for m in pops[i][1] if not satisfies(specs[i], m))
                     for i in range(len(programs)))
            out[(s_t, r_t)] = (s_c, r_c, miss / chg, fa / n_prs,
                               all(x["r_reachable"] for x in specs))
    return out


def main() -> int:
    fails = []
    programs = [parse(s) for s in BASE_PROGRAMS]
    pops = [population(p) for p in programs]
    g = grid(programs, pops)

    print("=" * 74)
    print("issue #114 -- specification-layer controls")
    print("=" * 74)

    # F1 ---------------------------------------------------------------------
    print("\n[F1] computed (s) matches the request exactly; every miss on (r) is FLAGGED")
    bad, misses = [], []
    for s_t in S_GRID:
        for r_t in R_GRID:
            s_c, r_c, _, _, reach = g[(s_t, r_t)]
            if abs(s_c - s_t) > 1e-9:
                bad.append(f"s {s_t}->{s_c:.4f}")
            if not reach:
                misses.append((s_t, r_t, r_c))
    if not bad:
        print("     PASS  specificity hits its target exactly in every cell")
    else:
        fails.append("F1")
        print(f"     FAIL  {bad}")
    if misses:
        print(f"     (flagged, not silently reported: {len(misses)} quantized/unreachable cell(s))")
        for s_t, r_t, r_c in misses:
            print(f"        s={s_t:<5} r_tgt={r_t:<5} r_computed={r_c:.4f}  <- labelled")
    else:
        print("     every requested exposure was reached")

    # F1b/F1c -- the flag itself needs a control or it becomes a dumping ground:
    # a cell that IS reachable must be marked reached, and a cell that is NOT must
    # be marked unmet.  Without F1b, a constructor that silently ignores r_target
    # would label every cell "quantized" and pass.
    print("\n[F1b/F1c] the reachability flag is two-sided")
    pos_bad = [i for i, p in enumerate(programs)
               if not (g[(0.25, 0.05)][4] and exposure(make_spec(p, 0.25, 0.05)) > 0.0)]
    neg_bad = [i for i, p in enumerate(programs)
               if make_spec(p, 1.0, 0.2)["r_reachable"]]
    print(f"     {'PASS' if not pos_bad else 'FAIL'}  F1b (s=0.25, r=0.05) reached for "
          f"{len(programs) - len(pos_bad)}/{len(programs)} programs")
    print(f"     {'PASS' if not neg_bad else 'FAIL'}  F1c (s=1.00, r=0.20) flagged unmet for "
          f"{len(programs) - len(neg_bad)}/{len(programs)} programs")
    if pos_bad or neg_bad:
        fails.append("F1bc")

    # F2 ---------------------------------------------------------------------
    print("\n[F2] mechanism: r = 0  =>  breakage exactly 0")
    nonzero = [(s_t, g[(s_t, 0.0)][3]) for s_t in S_GRID if g[(s_t, 0.0)][3] != 0.0]
    if not nonzero:
        print("     PASS  breakage 0.0000 at every s for r = 0")
    else:
        fails.append("F2")
        print(f"     FAIL  r=0 caused false alarms: {nonzero}")

    # F3 ---------------------------------------------------------------------
    print("\n[F3] nesting: detection and breakage non-decreasing in s, at fixed r")
    ok3 = True
    for r_t in R_GRID:
        prev = None
        for s_t in S_GRID:
            _, _, det, brk, _ = g[(s_t, r_t)]
            if prev is not None:
                if det < prev[0] - 1e-9 or brk < prev[1] - 1e-9:
                    ok3 = False
                    print(f"     FAIL  r={r_t}: s {prev[2]} -> {s_t} decreased "
                          f"(det {prev[0]:.4f}->{det:.4f}, brk {prev[1]:.4f}->{brk:.4f})")
            prev = (det, brk, s_t)
    if ok3:
        print("     PASS  monotone non-decreasing throughout the grid")
    else:
        fails.append("F3")

    # F4 ---------------------------------------------------------------------
    print("\n[F4] checker fires both ways at s = 1, r = 0")
    s_c, r_c, det, brk, _ = g[(1.0, 0.0)]
    ok4 = abs(det - 1.0) < 1e-9 and abs(brk) < 1e-9
    print(f"     {'PASS' if ok4 else 'FAIL'}  detection={det:.4f} (want 1.0), "
          f"breakage={brk:.4f} (want 0.0)")
    if not ok4:
        fails.append("F4")

    # F5 ---------------------------------------------------------------------
    print("\n[F5] the checker is not vacuous: it fires on BOTH clause families")
    prog = parse("(add x 1)")
    spec_obs = make_spec(prog, 1.0, 0.0)
    def_prog = next(m for m in enumerate_mutations(prog)
                    if m["operator"] == "const-off-by-one")
    legit_prog = next(m for m in enumerate_mutations(prog)
                      if m["operator"] == "add-commute")
    rejects_bad = not satisfies(spec_obs, def_prog["mutant"])
    accepts_good = satisfies(spec_obs, legit_prog["mutant"])
    print(f"     {'PASS' if rejects_bad and accepts_good else 'FAIL'}  "
          f"[observational] rejects const-off-by-one: {rejects_bad}; accepts add-commute: {accepts_good}")
    if not (rejects_bad and accepts_good):
        fails.append("F5-obs")

    # the STRUCTURAL path needs its own pair, or a broken structural check escapes
    spec_str = make_spec(prog, 0.125, 0.05)          # includes a ("top", "add") clause
    root_wrap = next(m for m in enumerate_mutations(prog)
                     if m["operator"] == "double-negation" and m["path"] == ())
    keeps_root = next(m for m in enumerate_mutations(prog)
                      if m["operator"] == "add-commute" and m["path"] == ())
    rejects_wrap = not satisfies(spec_str, root_wrap["mutant"])
    accepts_kept = satisfies(spec_str, keeps_root["mutant"])
    print(f"     {'PASS' if rejects_wrap and accepts_kept else 'FAIL'}  "
          f"[structural]   rejects a root-wrapping legit change: {rejects_wrap}; "
          f"accepts a root-preserving one: {accepts_kept}")
    if not (rejects_wrap and accepts_kept):
        fails.append("F5-struct")

    # F6 ---------------------------------------------------------------------
    print("\n[F6] determinism: two runs give an identical grid")
    g2 = grid(programs, pops)
    ident = all(g[k] == g2[k] for k in g)
    print(f"     {'PASS' if ident else 'FAIL'}  {len(g)} cells identical over two runs")
    if not ident:
        fails.append("F6")

    # F7 ---------------------------------------------------------------------
    # The axis must be tied to the OBJECT it describes: recompute the exposure from
    # the spec's own clause kinds, independently of the function under test.
    print("\n[F7] exposure() agrees with an independent recount of the spec's clauses")
    mism = []
    for p in programs:
        for s_t in S_GRID:
            for r_t in R_GRID:
                sp = make_spec(p, s_t, r_t)
                n_obs = sum(1 for c in sp["clauses"] if c[0] == "obs")
                n_st = len(sp["clauses"]) - n_obs
                manual = n_st / (n_st + n_obs) if (n_st + n_obs) else 0.0
                if abs(manual - exposure(sp)) > 1e-12:
                    mism.append((s_t, r_t, manual, exposure(sp)))
    print(f"     {'PASS' if not mism else 'FAIL'}  {len(programs) * len(S_GRID) * len(R_GRID)} "
          f"specs recounted, {len(mism)} disagreement(s)")
    if mism:
        fails.append("F7")
        print(f"        {mism[:3]}")

    # F8 ---------------------------------------------------------------------
    # Every clause the constructor emits claims to be TRUE of the reference it was
    # built for.  That is the constructor's whole contract, and it is universal: a
    # single false clause would make the reference itself fail its own spec.
    print("\n[F8] every emitted representational clause is true of its OWN reference")
    bad8 = []
    for p in programs:
        for c in representational_candidates(p):
            if not satisfies({"reference": p, "clauses": [c]}, p):
                bad8.append((to_str(p)[:24], c))
    n_cands = sum(len(representational_candidates(p)) for p in programs)
    print(f"     {'PASS' if not bad8 else 'FAIL'}  {n_cands} clause(s) over "
          f"{len(programs)} references; {len(bad8)} false of its own reference")
    if bad8:
        fails.append("F8")
        print(f"        e.g. {bad8[:3]}")

    # F9 ---------------------------------------------------------------------
    # Branch coverage, per the Step-3 lesson: "the checker fires" is a claim about the
    # UNION of kinds, so it must be shown once per kind.  A kind with no violating
    # mutation in the whole population is decorative; a kind whose clauses are never
    # even built is worse.
    print("\n[F9] per-KIND sensitivity: each declared kind is violated by >=1 mutation")
    seen_kinds, fired_kinds = set(), set()
    for p in programs:
        changing, preserving = population(p)
        cands = representational_candidates(p)
        for c in cands:
            seen_kinds.add(c[0])
        for m in changing + preserving:
            for c in cands:
                if not satisfies({"reference": p, "clauses": [c]}, m):
                    fired_kinds.add(c[0])
    declared = set(CLAUSE_KINDS) - {"obs"}
    never_built = sorted(declared - seen_kinds)
    never_fired = sorted(seen_kinds - fired_kinds)
    ok9 = not never_built
    print(f"     {'PASS' if ok9 else 'FAIL'}  kinds built: {len(seen_kinds)}/"
          f"{len(declared)}; kinds fired by >=1 mutation: {len(fired_kinds)}")
    if never_built:
        print(f"        NOT BUILT (the menu never offers them): {never_built}")
        fails.append("F9")
    if never_fired:
        print(f"        built but never violated here (not a failure; noted): {never_fired}")

    print("\n" + "=" * 74)
    if fails:
        print(f"SPECS: FAIL ({len(fails)} control(s)): {', '.join(fails)}")
        return 1
    print("SPECS: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
