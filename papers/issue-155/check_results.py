#!/usr/bin/env python3
"""Issue #155 -- check that every summarised number still follows from its rows.

results.json holds two kinds of number: per-cell rows, and summary values the
manuscript quotes. A summary that is computed once and stored is exactly the
kind of number that goes stale when a row changes and the summary does not, so
each one is recomputed here from the rows and compared.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROBLEMS = []


def fail(msg):
    PROBLEMS.append(msg)
    print("  FAIL: %s" % msg)


def main():
    path = os.path.join(HERE, "results.json")
    if not os.path.exists(path):
        print("  FAIL: results.json absent -- run emit_results.py first")
        return 1
    with open(path, encoding="utf-8") as fh:
        R = json.load(fh)

    print("== check: summaries recomputed from their rows")

    if R.get("problems"):
        fail("results.json records problems: %s" % R["problems"])

    # --- gap_summary must follow from gap_distinct / gap_ties ---
    gd, gt = R["gap_distinct"], R["gap_ties"]
    s = R["gap_summary"]
    want = {
        "distinct_n7_windows": gd[-1]["windows"],
        "distinct_n7_nonzero": gd[-1]["nonzero"],
        "distinct_max_gap": max(r["max"] for r in gd),
        "distinct_max_gap_n": max(gd, key=lambda r: r["max"])["n"],
        "ties_windows": sum(r["windows"] for r in gt),
        "ties_nonzero": sum(r["nonzero"] for r in gt),
        "ties_max_gap": max(r["max"] for r in gt),
    }
    for k, v in want.items():
        if s.get(k) != v:
            fail("gap_summary.%s = %r but the rows give %r" % (k, s.get(k), v))
    frac = want["ties_nonzero"] / want["ties_windows"]
    if abs(s.get("ties_nonzero_fraction", -1) - frac) > 1e-12:
        fail("gap_summary.ties_nonzero_fraction = %r but rows give %.12f"
             % (s.get("ties_nonzero_fraction"), frac))
    print("  gap_summary: %d keys recomputed" % (len(want) + 1))

    # --- threshold_ties_totals must follow from its rows ---
    rows = R["threshold_ties"]
    tot = R["threshold_ties_totals"]
    for key in ("windows", "T1", "T2", "T3", "LDS"):
        if key == "windows":
            v = sum(r["windows"] for r in rows)
        else:
            v = sum(r["violations"][key] for r in rows)
        if tot.get(key) != v:
            fail("threshold_ties_totals.%s = %r but rows give %r" % (key, tot.get(key), v))
    print("  threshold_ties_totals: 5 keys recomputed")

    # --- rules_summary must follow from its cells ---
    rr = R["rules"]
    rs = R["rules_summary"]
    want_rs = {
        "cells": len(rr),
        "aligned_min_fraction": min(r["aligned_fraction"] for r in rr),
        "aligned_max_fraction": max(r["aligned_fraction"] for r in rr),
        "aligned_max_worst_ratio": max(r["aligned_worst_ratio"] for r in rr),
        "control_min_fraction": min(r["control_fraction"] for r in rr),
    }
    for k, v in want_rs.items():
        if rs.get(k) != v:
            fail("rules_summary.%s = %r but the cells give %r" % (k, rs.get(k), v))
    print("  rules_summary: %d keys recomputed" % len(want_rs))

    # --- the claims the paper leans on, asserted as relations not literals ---
    if R["certificate"]["distinct"]["mismatches"] or R["certificate"]["ties"]["mismatches"]:
        fail("the DP/brute certificate is not clean")
    if not R["certificate"]["ties_are_not_inversions"]:
        fail("the tie convention is not being honoured")
    if R["inequality_runs_p_ge_lds"]["violations"]:
        fail("runs(p) < LDS somewhere, contradicting the proof")
    for r in R["threshold_distinct"]:
        if r["runs_p_violations"]:
            fail("runs(p) is not exact at n=%d" % r["n"])
    if R["threshold_ties_totals"]["T3"]:
        fail("T3 is not exact on every tie-bearing window")
    if not R["forced_cells"]["k1_rule_equals_floor"]:
        fail("k=1 is not forced, so the paper's 'declined cell' wording is wrong")
    # the figure must exist, and must be newer than nothing (i.e. be present)
    for name in ("discipline-gap.svg", "discipline-gap.png"):
        p = os.path.join(HERE, "figures", name)
        if not os.path.exists(p):
            fail("figure %s absent -- run make_figure.py" % name)
    print("  claim relations: asserted")

    if PROBLEMS:
        print("CHECK: %d PROBLEM(S)" % len(PROBLEMS))
        return 1
    print("CHECK: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
