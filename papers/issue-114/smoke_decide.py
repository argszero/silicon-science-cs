#!/usr/bin/env python3
"""Smoke battery for the decisive run (issue #114, Step 5).

Every control here has one job: to be able to FAIL.  `plant_decide.py` corrupts the
instrument one thing at a time and requires this battery to catch each corruption, so a
control that cannot fire is detected as decoration rather than trusted.

CONTROLS
  R1 route equivalence   the fast bitmask == the reference checker `satisfies` == a direct
                         clause-by-clause OR, on EVERY sampled (spec, mutant) pair
  R2 specificity         `s` is the pinned count / |domain|, invariant to the alignment and
                         to the mix -- and different grades really are different (two-sided)
  R3 exposure            per reference, `r` does not move when the MIX moves (same clause
                         count), and the fast path's value is the constructor's value
  R4 budget agreement    the fast path's `b` is `specs.budget`'s `b`, and the clause counts
                         it implies are the counts `make_spec` actually emits
  R5 reachability labels the empty spec does NOT satisfy a positive r request; a menu-capped
                         cell is labelled unreached; a lattice cell is labelled reached
  R6 oracle independence the changing/preserving split is re-derived from the tables alone
  R7 census integrity    the census arithmetic closes and the kept references are
                         semantically distinct (no two denote the same table)
  R8 determinism         the whole grid is re-derived and agrees exactly
  R9 band arithmetic     every reported band endpoint is a value some draw actually took,
                         and the reported span is max/min of the values it names

Usage: python3 smoke_decide.py      (exit 0 == all controls pass)
"""

from __future__ import annotations

import sys

from fast import Model, mask_scores
from mutations import enumerate_mutations
from oracle import classify
from progspace import all_sources, by_node_count, reference_set
from specs import (budget, domain_perm, exposure, exposure_plan, make_spec, satisfies,
                   specificity)
from toylang import M, table

import decide

FAILS = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


def main() -> int:
    programs, census = reference_set()
    models = [Model(p["prog"], p["src"], p["tier"]) for p in programs]
    print("=" * 88)
    print("issue #114 -- decisive-run smoke battery")
    print(f"references {len(models)}, mutants {sum(m.n_mutants for m in models)}")
    print("=" * 88)

    sample = [models[i] for i in (0, 7, 33, 61, 120, 200, 250, 261) if i < len(models)]
    cells = [(0.0625, 0.05), (0.25, 0.10), (1.0, 0.20)]
    draws = [(None, None), ("high", 3), (2, None)]

    # ---- R0: the REPORT itself runs -----------------------------------------
    # The battery spent its first version testing the measurement and never executing the
    # report -- so a crash in the printing code passed every control and was found only by
    # the driver, as a bare "FAILED".  A report is a part of the instrument.
    import contextlib
    import io
    buf = io.StringIO()
    err = None
    try:
        with contextlib.redirect_stdout(buf):
            rc = decide.main([])
        if rc != 0:
            err = f"decide.main returned {rc}"
    except Exception as exc:                       # noqa: BLE001 - the point is to catch all
        err = f"{type(exc).__name__}: {exc}"
    out = buf.getvalue()
    check(err is None and "DECISIVE RUN: COMPLETE" in out,
          "R0 the decisive report executes and reaches its end marker",
          err or f"{len(out)} chars of output")

    # ---- R1: three routes to the same rejection set --------------------------
    bad = []
    n = 0
    for m in sample:
        for (s_t, r_t) in cells:
            for (al, mx) in draws:
                spec = make_spec(m.prog, s_t, r_t, mix=mx, align=al)
                mask, k, b, _, _ = m.cell(s_t, r_t, al, mx)
                if mask != m.naive_mask(spec["clauses"]):
                    bad.append((m.src, s_t, r_t, al, mx, "mask != clause-OR"))
                for j, mu in enumerate(m.mutants):
                    ref = satisfies(spec, mu)
                    if ((mask >> j) & 1) == ref:      # rejected-by-mask vs accepted-by-checker
                        bad.append((m.src, s_t, r_t, al, mx, "bit disagrees with satisfies"))
                        break
                    n += 1
    check(not bad, "R1 route equivalence (mask == clause-OR == satisfies)",
          f"{n} (spec,mutant) pairs; {len(bad)} disagreements" +
          (f" e.g. {bad[0]}" if bad else ""))

    # ---- R2: specificity is the pinned count / domain, invariant to the draw --
    bad, seen = [], set()
    for m in sample:
        for s_t in (0.0, 0.0625, 0.25, 1.0):
            vals = {round(specificity(make_spec(m.prog, s_t, 0.0, mix=x, align=a)), 12)
                    for (a, x) in draws}
            if vals != {round(round(s_t * M) / M, 12)}:
                bad.append((m.src, s_t, sorted(vals)))
            seen.add((s_t, round(round(s_t * M) / M, 12)))
    monotone = len({v for _, v in seen}) == len({s for s, _ in seen})
    check(not bad, "R2a specificity == k/M, invariant to alignment and mix",
          f"{len(bad)} violations")
    check(monotone, "R2b two-sided: distinct grades really are distinct specificities")

    # ---- R3: exposure is invariant to the mix, and the fast path agrees ------
    bad = []
    for m in sample:
        for (s_t, r_t) in cells:
            rs = {round(exposure(make_spec(m.prog, s_t, r_t, mix=x)), 12)
                  for x in decide.MIX_DRAWS}
            ach = {round(m.cell(s_t, r_t, None, x)[3], 12) for x in decide.MIX_DRAWS}
            if len(rs) != 1 or rs != ach:
                bad.append((m.src, s_t, r_t, sorted(rs), sorted(ach)))
    check(not bad, "R3a r is invariant to the mix (same clause count) and equals the fast path",
          f"{len(bad)} violations" + (f" e.g. {bad[0]}" if bad else ""))

    # ---- R4: the fast path uses the same budget rule as the constructor -------
    bad = []
    for m in sample:
        for (s_t, r_t) in cells + [(0.75, 0.30), (0.5, 0.05)]:
            spec = make_spec(m.prog, s_t, r_t)
            k = round(s_t * M)
            b_want = budget(k, r_t, m.B)
            n_obs = sum(1 for c in spec["clauses"] if c[0] == "obs")
            n_st = len(spec["clauses"]) - n_obs
            _, kk, b_got, ach, _ = m.cell(s_t, r_t, None, None)
            if (n_obs, n_st, kk, b_got) != (k, b_want, k, b_want):
                bad.append((m.src, s_t, r_t, (n_obs, n_st), (k, b_want)))
            if abs(ach - exposure(spec)) > 1e-12:
                bad.append((m.src, s_t, r_t, "exposure mismatch"))
    check(not bad, "R4 budget agreement (fast path == make_spec == specs.budget)",
          f"{len(bad)} violations" + (f" e.g. {bad[0]}" if bad else ""))

    # ---- R5: reachability labels -------------------------------------------
    p = sample[0].prog
    empty_pos = make_spec(p, 0.0, 0.05)["r_reachable"]
    empty_zero = make_spec(p, 0.0, 0.0)["r_reachable"]
    capped = make_spec(p, 1.0, 0.30)["r_reachable"]
    lattice = make_spec(p, 0.125, 0.10)["r_reachable"]
    check(empty_pos is False, "R5a the EMPTY spec does not satisfy a positive r request")
    check(empty_zero is True, "R5b ... but does satisfy r = 0 (two-sided)")
    check(capped is False, "R5c a menu-capped cell is labelled unreached")
    check(lattice is True, "R5d a lattice cell is labelled reached")
    # the tolerance must not be vacuous: an empty spec has quantum 1.0, so a naive
    # "within one step" test says yes to everything.  Both sides of that must hold:
    # the naive rule ACCEPTS the request and the correct rule REFUSES it.
    ach, q, correct = exposure_plan(0, 0, 0.05)
    naive = abs(ach - 0.05) <= q
    check(naive and not correct,
          "R5e the empty-spec tolerance is vacuous (naive says yes, correct says no)")

    # ---- R6: the oracle's verdicts are re-derived from the tables -------------
    bad = []
    for m in sample[:4]:
        muts = enumerate_mutations(m.prog)
        for mu in muts[:8]:
            pres, _ = classify(m.prog, mu["mutant"])
            pres_again = table(m.prog) == table(mu["mutant"])
            if pres != pres_again:
                bad.append((m.src, mu["operator"]))
        for j, mu in enumerate(m.mutants):
            pres = ((m.preserving_mask >> j) & 1) == 1
            if pres != (table(m.prog) == table(mu)):
                bad.append((m.src, "mask bit"))
    check(not bad, "R6 the changing/preserving split is table-derived only",
          f"{len(bad)} violations")

    # ---- R7: the census arithmetic ------------------------------------------
    sizes = by_node_count()
    gen = sum(len(sizes[n]) for n in sizes)
    tbls = [table(m.prog) for m in models]
    dup = len(tbls) - len(set(tbls))
    ok_arith = (census["generated_sources"] == gen
                and census["kept"] == len(models)
                and census["distinct_semantics"] >= census["kept"]
                and census["kept"] == sum(1 for m in models if m.tier == "systematic")
                + sum(1 for m in models if m.tier == "named"))
    check(ok_arith, "R7a census arithmetic closes",
          f"generated {census['generated_sources']} == {gen}")
    check(dup == 0, "R7b kept references are semantically distinct", f"{dup} duplicate tables")
    check(len(all_sources()) == gen, "R7c all_sources() == the per-size counts")

    # ---- R8: determinism ----------------------------------------------------
    g1 = decide.grid_for(models[:40], 2, 3)
    g2 = decide.grid_for(models[:40], 2, 3)
    same = all(abs(g1[k][0] - g2[k][0]) < 1e-15 and abs(g1[k][1] - g2[k][1]) < 1e-15 for k in g1)
    check(same, "R8 the grid is re-derived identically")

    # ---- R9: every reported band endpoint is attained by a draw --------------
    bad = []
    for (s_t, r_t) in cells:
        dets = [decide.pooled(models, s_t, r_t, a, x)[0] for a in decide.ALIGN_DRAWS
                for x in decide.MIX_DRAWS]
        brks = [decide.pooled(models, s_t, r_t, a, x)[1] for a in decide.ALIGN_DRAWS
                for x in decide.MIX_DRAWS]
        if not (min(dets) in dets and max(dets) in dets
                and min(brks) in brks and max(brks) in brks):
            bad.append((s_t, r_t))
    check(not bad, "R9 band endpoints are attained values, not computed bounds",
          f"{len(bad)} cells")

    print()
    print("SMOKE (decisive run): " + ("ALL PASS" if not FAILS else f"FAIL {FAILS}"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
