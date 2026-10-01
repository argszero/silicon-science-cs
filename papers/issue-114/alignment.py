#!/usr/bin/env python3
"""Alignment sweep (issue #114, prior P1): does WHERE you pin matter at matched s?

For a fixed specificity (|P| = k, hence s = k/M exactly), sweep the pin-set alignment
against the change location, measure detection, and compare the measurement against the
closed-form prediction of `align.py`.  Reports the span across alignments -- the quantity
prior P1 makes a claim about.

Usage: python3 alignment.py
"""

from __future__ import annotations

import statistics
import sys

from align import (ALIGNMENTS, M, T_GRID, diff_set, measure_curve, obs_spec,
                   pins, predict_curve, predict_extremes, regional_high, regional_low)
from specs import satisfies
from toylang import parse

BASE = parse("(mul x 3)")     # a simple reference; the curve does not depend on it
K_VALUES = [16, 32, 64]


def verify_construct(prog, region, ts_sample=(0, 1, 127, 255)):
    """Confirm the regional wrapper's difference set IS what we claim (by computation)."""
    bad = []
    for t in ts_sample:
        mut = regional_low(prog, t) if region == "low" else regional_high(prog, t)
        want = frozenset(i for i in range(M) if (i < t if region == "low" else i > t))
        if diff_set(prog, mut) != want:
            bad.append((region, t))
    return bad


def main() -> int:
    print("=" * 88)
    print("issue #114 -- ALIGNMENT sweep (prior P1): at matched specificity, does WHERE matter?")
    print("=" * 88)

    # 0. the construction check: the difference sets are what the design claims
    bad = verify_construct(BASE, "low") + verify_construct(BASE, "high")
    print(f"\n[construction] regional wrappers' difference sets verified: "
          f"{'PASS' if not bad else 'FAIL ' + str(bad)}")

    for k in K_VALUES:
        s = k / M
        print(f"\n{'=' * 88}\nspecificity MATCHED at s = {k}/256 = {s:.3f} for every alignment")
        print(f"{'=' * 88}")
        print(f"{'alignment':<12} {'min(P)':>7} {'max(P)':>7} | "
              f"{'low: meas':>10} {'pred':>7} | {'high: meas':>11} {'pred':>7} | {'span':>6}")
        rows = {}
        for a in ALIGNMENTS:
            P = pins(a, k)
            meas_lo = statistics.fmean(measure_curve(P, "low", T_GRID))
            meas_hi = statistics.fmean(measure_curve(P, "high", T_GRID))
            pred_lo = predict_extremes(P, "low")
            pred_hi = predict_extremes(P, "high")
            rows[a] = (meas_lo, meas_hi, pred_lo, pred_hi, min(P), max(P))
            span = max(meas_lo, meas_hi) / min(meas_lo, meas_hi) if min(meas_lo, meas_hi) > 0 \
                else float("inf")
            print(f"{a:<12} {min(P):>7} {max(P):>7} | {meas_lo:>10.4f} {pred_lo:>7.4f} | "
                  f"{meas_hi:>11.4f} {pred_hi:>7.4f} | "
                  f"{span:>6.2f}" if span != float("inf") else
                  f"{a:<12} {min(P):>7} {max(P):>7} | {meas_lo:>10.4f} {pred_lo:>7.4f} | "
                  f"{meas_hi:>11.4f} {pred_hi:>7.4f} |   inf")
        lo_vals = [rows[a][0] for a in ALIGNMENTS]
        hi_vals = [rows[a][1] for a in ALIGNMENTS]
        print(f"\n  across alignments at s={s:.3f}:")
        print(f"    low-region changes : detection {min(lo_vals):.4f} .. {max(lo_vals):.4f}"
              f"   span {max(lo_vals)/min(lo_vals):.2f}x" if min(lo_vals) > 0 else
              f"    low-region changes : detection {min(lo_vals):.4f} .. {max(lo_vals):.4f}"
              f"   span >= {max(lo_vals)/ (1/M):.0f}x (floor at 0)")
        print(f"    high-region changes: detection {min(hi_vals):.4f} .. {max(hi_vals):.4f}"
              f"   span {max(hi_vals)/min(hi_vals):.2f}x" if min(hi_vals) > 0 else
              f"    high-region changes: detection {min(hi_vals):.4f} .. {max(hi_vals):.4f}"
              f"   span >= {max(hi_vals)/(1/M):.0f}x (floor at 0)")
        # the reversal: the ranking of alignments flips with the change location
        best_lo = max(ALIGNMENTS, key=lambda a: rows[a][0])
        best_hi = max(ALIGNMENTS, key=lambda a: rows[a][1])
        print(f"    best for low-region changes : {best_lo}")
        print(f"    best for high-region changes: {best_hi}"
              f"   {'(REVERSAL)' if best_lo != best_hi else '(same)'}")

    # ---- the shape at one specificity, printed in full ----------------------
    k = 32
    print(f"\n{'=' * 88}\ndetection vs change location t, at s = {k}/256 (t = 1..255)")
    print(f"{'=' * 88}")
    print(f"{'alignment':<12} {'low: t at which detection turns on':>36} "
          f"{'high: turns off':>18}")
    for a in ["block-low", "block-high", "spread", "rand1"]:
        P = pins(a, k)
        lo_on = next((t for t in T_GRID if detect_ok(P, "low", t)), None)
        hi_off = next((t for t in T_GRID if not detect_ok(P, "high", t)), None)
        print(f"{a:<12} {str(lo_on):>36} {str(hi_off):>18}")
    return 0


def detect_ok(P, region, t) -> bool:
    return (min(P) < t) if region == "low" else (max(P) > t)


if __name__ == "__main__":
    sys.exit(main())
