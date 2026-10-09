#!/usr/bin/env python3
"""Controls for the alignment axis (issue #114, prior P1).

The sweep reports detection curves from a closed form.  The danger is that the curve is
then a statement about THIS FILE's model rather than about the checker, so the central
control is three-way: the real checker `satisfies`, the closed-form model, and the
step-function prediction must agree at every (alignment, region, t).

  G1  specificity is MATCHED: every alignment pins exactly k inputs (s = k/M identical)
  G2  THREE-WAY agreement: satisfies(spec, mutant) == model == prediction, everywhere
  G3  prior P1: the span across alignments is >= 2x, at each k and on both regions
  G4  the REVERSAL is real: the best alignment for low-region changes differs from the
      best for high-region changes
  G5  the regional wrapper's difference set IS what the design claims, for every t
  G6  base-program independence: a different reference gives the same curve
  G7  determinism: two runs agree (the random alignments are seeded)

Run: python3 smoke_align.py
"""

from __future__ import annotations

import sys

from align import (ALIGNMENTS, M, T_GRID, diff_set, measure_curve, obs_spec, pins,
                   predict_curve, predict_extremes, regional_high, regional_low)
from specs import satisfies
from toylang import parse

K_VALUES = [16, 32, 64]
BASE = parse("(mul x 3)")
OTHER = parse("(add x 7)")


def real_curve(prog, P, region, ts):
    """The curve from the REAL checker, with no model in the loop."""
    spec = obs_spec(prog, P)
    out = []
    for t in ts:
        mut = regional_low(prog, t) if region == "low" else regional_high(prog, t)
        out.append(0.0 if satisfies(spec, mut) else 1.0)
    return out


def main() -> int:
    fails = []
    print("=" * 80)
    print("issue #114 -- alignment-axis controls")
    print("=" * 80)

    # G1 ---------------------------------------------------------------------
    # "Matched specificity" is a claim about the SPEC, so the control must read the
    # spec's own clause list, not just the pin list it was built from (a spec builder
    # that adds a clause would otherwise pass).
    print("\n[G1] specificity is matched: every alignment builds a spec with exactly k obs clauses")
    bad1 = []
    for k in K_VALUES:
        sizes = {a: len(pins(a, k)) for a in ALIGNMENTS}
        spec_sizes = {a: sum(1 for c in obs_spec(BASE, pins(a, k))["clauses"] if c[0] == "obs")
                      for a in ALIGNMENTS}
        if set(sizes.values()) != {k} or set(spec_sizes.values()) != {k}:
            bad1.append((k, sizes, spec_sizes))
    print(f"     {'PASS' if not bad1 else 'FAIL'}  |P| == k AND obs clauses == k for all "
          f"{len(ALIGNMENTS)} alignments at k in {K_VALUES}")
    if bad1:
        fails.append("G1")
        print(f"        {bad1[:2]}")

    # G2 ---------------------------------------------------------------------
    # The control OWNS its expectation (`expect`, written out below) rather than
    # importing the prediction it is testing: against a prediction that echoes the
    # measurement, an imported expectation would self-satisfy (the Class-118 shape).
    # The real checker `satisfies` is the independent anchor -- the model and the
    # prediction must agree with IT, not merely with each other.
    print("\n[G2] THREE-WAY: real checker == closed-form model == step prediction (expectation owned here)")
    def expect(P, region, ts):
        if not P:
            return [0.0 for _ in ts]
        edge = min(P) if region == "low" else max(P)
        return [1.0 if (t > edge if region == "low" else t < edge) else 0.0 for t in ts]

    dis = []
    checked = 0
    for k in K_VALUES:
        for a in ALIGNMENTS:
            P = pins(a, k)
            for region in ("low", "high"):
                ts = T_GRID
                legs = {
                    "real": real_curve(BASE, P, region, ts),
                    "model": measure_curve(P, region, ts),
                    "predict": predict_curve(P, region, ts),
                    "expect": expect(P, region, ts),
                }
                for t in range(len(ts)):
                    vals = {n: v[t] for n, v in legs.items()}
                    checked += 1
                    if len(set(vals.values())) != 1:
                        dis.append((k, a, region, ts[t], vals))
    print(f"     {'PASS' if not dis else 'FAIL'}  {checked} (cell, t) quadruples agree "
          f"(real/model/predict/expect); {len(dis)} disagreement(s)")
    if dis:
        fails.append("G2")
        print(f"        e.g. {dis[:2]}")

    # G3 ---------------------------------------------------------------------
    print("\n[G3] prior P1: span across alignments >= 2x (registered criterion)")
    bad3 = []
    for k in K_VALUES:
        for region in ("low", "high"):
            vals = [predict_extremes(pins(a, k), region) for a in ALIGNMENTS]
            lo_v = [v for v in vals if v > 0]
            span = (max(lo_v) / min(lo_v)) if lo_v else float("inf")
            mark = "PASS" if span >= 2.0 else "FAIL"
            if span < 2.0:
                bad3.append((k, region, span))
            print(f"     {mark}  k={k:<3} {region:<4}-region  detection "
                  f"{min(vals):.4f} .. {max(vals):.4f}  span "
                  f"{span:.2f}x" if lo_v else
                  f"     {mark}  k={k:<3} {region:<4}-region  span >= "
                  f"{max(vals) * M:.0f}x (a floor of 0)")
    if bad3:
        fails.append("G3")
        print(f"        below threshold: {bad3}")

    # G4 ---------------------------------------------------------------------
    print("\n[G4] the REVERSAL: best alignment differs by change location")
    bad4 = []
    for k in K_VALUES:
        best_lo = max(ALIGNMENTS, key=lambda a: predict_extremes(pins(a, k), "low"))
        best_hi = max(ALIGNMENTS, key=lambda a: predict_extremes(pins(a, k), "high"))
        worst_lo = min(ALIGNMENTS, key=lambda a: predict_extremes(pins(a, k), "low"))
        worst_hi = min(ALIGNMENTS, key=lambda a: predict_extremes(pins(a, k), "high"))
        rev = (best_lo != best_hi) and (best_lo in (worst_hi,)) is False
        print(f"     {'PASS' if rev else 'FAIL'}  k={k:<3} best-low={best_lo:<11} "
              f"best-high={best_hi:<11} worst-low={worst_lo:<11} worst-high={worst_hi}")
        if not rev:
            bad4.append(k)
    if bad4:
        fails.append("G4")

    # G5 ---------------------------------------------------------------------
    print("\n[G5] the wrapper's difference set is exactly the intended region (every t)")
    bad5 = []
    for region in ("low", "high"):
        for t in T_GRID:
            mut = regional_low(BASE, t) if region == "low" else regional_high(BASE, t)
            want = frozenset(i for i in range(M)
                             if (i < t if region == "low" else i > t))
            if diff_set(BASE, mut) != want:
                bad5.append((region, t))
    print(f"     {'PASS' if not bad5 else 'FAIL'}  2 x {len(T_GRID)} wrappers verified "
          f"by evaluating both tables; {len(bad5)} mismatch(es)")
    if bad5:
        fails.append("G5")

    # G6 ---------------------------------------------------------------------
    print("\n[G6] base-program independence: the curve does not depend on the reference")
    bad6 = []
    for k in K_VALUES:
        for a in ALIGNMENTS:
            P = pins(a, k)
            for region in ("low", "high"):
                if real_curve(BASE, P, region, T_GRID) != real_curve(OTHER, P, region, T_GRID):
                    bad6.append((k, a, region))
    print(f"     {'PASS' if not bad6 else 'FAIL'}  identical curves for two different "
          f"reference programs; {len(bad6)} difference(s)")
    if bad6:
        fails.append("G6")

    # G7 ---------------------------------------------------------------------
    print("\n[G7] determinism: seeded alignments reproduce exactly")
    snap1 = {a: pins(a, 32) for a in ALIGNMENTS}
    snap2 = {a: pins(a, 32) for a in ALIGNMENTS}
    ok7 = snap1 == snap2
    print(f"     {'PASS' if ok7 else 'FAIL'}  {len(ALIGNMENTS)} alignments identical over two calls")
    if not ok7:
        fails.append("G7")

    print("\n" + "=" * 80)
    if fails:
        print(f"ALIGNMENT: FAIL ({len(fails)}): {', '.join(fails)}")
        return 1
    print("ALIGNMENT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
