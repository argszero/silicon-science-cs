#!/usr/bin/env python3
"""Issue #155 -- emit results.json: every number the manuscript is allowed to state.

Nothing here is transcribed from a notebook. Each figure the paper quotes is
computed here, from floor.py, and written to results.json; make_manuscript.py
refuses a number the results file does not hold. The file is deterministic --
no sampling, no seeds, no network.

Exit status is non-zero if any certificate fails, so a broken instrument can
never produce a green run.
"""
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import floor as F  # noqa: E402

OUT = os.path.join(HERE, "results.json")
PROBLEMS = []
R = {}


def fail(msg):
    PROBLEMS.append(msg)
    print("  FAIL: %s" % msg)


def note(msg):
    print("  %s" % msg)


# ==========================================================================
# 1. certificate: the fast floor agrees with the slow one, on every instance
# ==========================================================================

def step_certificate():
    print("== 1/6 certificate: DP floor vs independent brute force")
    cert = {"distinct": {}, "ties": {}}

    d_pairs = d_bad = 0
    for n in [4, 5, 6]:
        for k in range(1, n + 1):
            for seq in itertools.permutations(range(n)):
                a = F.restricted_floor_dp(seq, k)
                b = F.restricted_floor_brute(seq, k)
                d_pairs += 1
                if a != b:
                    d_bad += 1
                    if d_bad <= 3:
                        fail("dp/brute disagree (distinct) n=%d k=%d seq=%s dp=%d brute=%d"
                             % (n, k, seq, a, b))
    cert["distinct"] = {"pairs": d_pairs, "mismatches": d_bad}
    note("distinct ranks: %d (window, k) pairs, %d mismatches" % (d_pairs, d_bad))

    t_pairs = t_bad = 0
    for n in [4, 5]:
        for m in [2, 3]:
            for seq in itertools.product(range(m), repeat=n):
                for k in range(1, min(n, m) + 1):
                    a = F.restricted_floor_dp(seq, k)
                    b = F.restricted_floor_brute(seq, k)
                    t_pairs += 1
                    if a != b:
                        t_bad += 1
                        if t_bad <= 3:
                            fail("dp/brute disagree (ties) n=%d m=%d seq=%s k=%d dp=%d brute=%d"
                                 % (n, m, seq, k, a, b))
    cert["ties"] = {"pairs": t_pairs, "mismatches": t_bad}
    note("tied ranks: %d (window, k) pairs, %d mismatches" % (t_pairs, t_bad))

    # the tie convention, stated as a check rather than assumed
    all_equal_zero = (F.restricted_floor_dp((3, 3, 3), 1) == 0
                      and F.restricted_floor_brute((3, 3, 3), 1) == 0)
    cert["ties_are_not_inversions"] = bool(all_equal_zero)
    if not all_equal_zero:
        fail("equal-rank pairs are being counted as inversions")

    # hand-checkable witnesses, asserted so the paper can quote them
    wit = {
        "reverse_window_n6_k1": F.restricted_floor_dp((5, 4, 3, 2, 1, 0), 1),
        "sorted_window_n6_k1": F.restricted_floor_dp((0, 1, 2, 3, 4, 5), 1),
        "hand_case_2_1_4_3_floor_k2": F.restricted_floor_dp((2, 1, 4, 3), 2),
        "hand_case_2_1_4_3_floor_k3": F.restricted_floor_dp((2, 1, 4, 3), 3),
        "hand_case_2_1_4_3_lds": F.lds((2, 1, 4, 3)),
        "hand_case_2_1_4_3_runs": F.runs_of_inverse((2, 1, 4, 3)),
    }
    cert["witnesses"] = wit
    if wit["reverse_window_n6_k1"] != 15:
        fail("reversed 6-window at k=1 must cost all 15 pairs, got %d"
             % wit["reverse_window_n6_k1"])
    if wit["sorted_window_n6_k1"] != 0:
        fail("sorted 6-window at k=1 must cost 0")
    if wit["hand_case_2_1_4_3_floor_k2"] != 1 or wit["hand_case_2_1_4_3_floor_k3"] != 0:
        fail("the hand counterexample no longer behaves as the paper states")
    if not (wit["hand_case_2_1_4_3_lds"] < wit["hand_case_2_1_4_3_runs"]):
        fail("the hand counterexample no longer separates LDS from runs(p)")

    R["certificate"] = cert


# ==========================================================================
# 2. the threshold under distinct ranks: which statistic names required k
# ==========================================================================

def step_threshold_distinct(n_max=7):
    print("== 2/6 threshold, distinct ranks: min{k : floor(k)=0} vs each candidate")
    rows = []
    for n in range(4, n_max + 1):
        windows = 0
        lds_wrong = 0
        runs_viol = 0
        for seq in itertools.permutations(range(n)):
            windows += 1
            r = F.runs_of_inverse(seq)
            # sufficiency at k=r, necessity at k=r-1: the two-sided boundary
            if F.restricted_floor_dp(seq, r) != 0:
                runs_viol += 1
            if r > 1 and F.restricted_floor_dp(seq, r - 1) == 0:
                runs_viol += 1
            l = F.lds(seq)
            # the free-merge answer would put required k at l
            if l != r:
                lds_wrong += 1
        rows.append({
            "n": n,
            "windows": windows,
            "runs_p_violations": runs_viol,
            "lds_understates_windows": lds_wrong,
            "lds_understates_fraction": lds_wrong / windows,
        })
        note("n=%d: %d windows, runs(p) violations %d, LDS understates %d (%.4f)"
             % (n, windows, runs_viol, lds_wrong, lds_wrong / windows))
        if runs_viol:
            fail("runs(p) is not the exact strict-priority threshold at n=%d (%d windows)"
                 % (n, runs_viol))
    R["threshold_distinct"] = rows

    # the inequality is a theorem, but a theorem with a proof can still be
    # mis-stated in code, so the direction of the gap is asserted as data
    neg = 0
    for n in range(4, n_max + 1):
        for seq in itertools.permutations(range(n)):
            if F.runs_of_inverse(seq) < F.lds(seq):
                neg += 1
    R["inequality_runs_p_ge_lds"] = {"violations": neg}
    note("runs(p) < LDS (must be 0, the inequality is proved): %d" % neg)
    if neg:
        fail("runs(p) < LDS on %d windows, contradicting the proof" % neg)


# ==========================================================================
# 3. the threshold under ties
# ==========================================================================

def step_threshold_ties():
    print("== 3/6 threshold, tied ranks: T1/T2/T3/LDS against required k")
    rows = []
    for n in [4, 5, 6]:
        for m in [2, 3, 4]:
            if m >= n:
                continue
            windows = 0
            v = {"T1": 0, "T2": 0, "T3": 0, "LDS": 0}
            req_sum = 0
            for seq in itertools.product(range(m), repeat=n):
                windows += 1
                req = F.required_k(seq)
                req_sum += req
                if F.stat_t1(seq) != req:
                    v["T1"] += 1
                if F.stat_t2(seq) != req:
                    v["T2"] += 1
                if F.stat_t3(seq) != req:
                    v["T3"] += 1
                if F.lds(seq) != req:
                    v["LDS"] += 1
            rows.append({"n": n, "m": m, "windows": windows,
                         "violations": v, "required_k_mean": req_sum / windows})
            note("n=%d m=%d: %d windows, T1 %d, T2 %d, T3 %d, LDS %d"
                 % (n, m, windows, v["T1"], v["T2"], v["T3"], v["LDS"]))
    R["threshold_ties"] = rows

    tot = {"windows": 0, "T1": 0, "T2": 0, "T3": 0, "LDS": 0}
    for r in rows:
        tot["windows"] += r["windows"]
        for key in ("T1", "T2", "T3", "LDS"):
            tot[key] += r["violations"][key]
    R["threshold_ties_totals"] = tot
    note("totals: %d windows, T1 %d, T2 %d, T3 %d, LDS %d"
         % (tot["windows"], tot["T1"], tot["T2"], tot["T3"], tot["LDS"]))
    if tot["T3"]:
        fail("T3 is not exact on every tie-bearing window (%d violations)" % tot["T3"])


# ==========================================================================
# 4. how far apart are the two disciplines, in frequency AND in size
# ==========================================================================

def step_gap():
    print("== 4/6 the discipline gap: frequency and magnitude")
    distinct = []
    for n in range(4, 8):
        hist = {}
        windows = 0
        for seq in itertools.permutations(range(n)):
            windows += 1
            g = F.runs_of_inverse(seq) - F.lds(seq)
            hist[g] = hist.get(g, 0) + 1
        row = {"n": n, "windows": windows,
               "histogram": {str(k): v for k, v in sorted(hist.items())},
               "max": max(hist), "nonzero": windows - hist.get(0, 0),
               "nonzero_fraction": (windows - hist.get(0, 0)) / windows}
        distinct.append(row)
        note("distinct n=%d: %s (max %d, nonzero %.4f)"
             % (n, row["histogram"], row["max"], row["nonzero_fraction"]))
    R["gap_distinct"] = distinct

    ties = []
    for n in [5, 6]:
        for m in [2, 3, 4]:
            if m >= n:
                continue
            hist = {}
            windows = 0
            for seq in itertools.product(range(m), repeat=n):
                windows += 1
                g = F.required_k(seq) - F.lds(seq)
                hist[g] = hist.get(g, 0) + 1
            row = {"n": n, "m": m, "windows": windows,
                   "histogram": {str(k): v for k, v in sorted(hist.items())},
                   "max": max(hist), "nonzero": windows - hist.get(0, 0),
                   "nonzero_fraction": (windows - hist.get(0, 0)) / windows}
            ties.append(row)
            note("ties n=%d m=%d: %s (max %d, nonzero %.4f)"
                 % (n, m, row["histogram"], row["max"], row["nonzero_fraction"]))
    R["gap_ties"] = ties

    # the headline magnitude claims, computed rather than typed
    R["gap_summary"] = {
        "distinct_n7_windows": distinct[-1]["windows"],
        "distinct_n7_nonzero": distinct[-1]["nonzero"],
        "distinct_max_gap": max(r["max"] for r in distinct),
        "distinct_max_gap_n": max(distinct, key=lambda r: r["max"])["n"],
        "ties_windows": sum(r["windows"] for r in ties),
        "ties_nonzero": sum(r["nonzero"] for r in ties),
        "ties_max_gap": max(r["max"] for r in ties),
    }
    s = R["gap_summary"]
    s["ties_nonzero_fraction"] = s["ties_nonzero"] / s["ties_windows"]
    note("max gap over distinct ranks: %d (at n=%d); over ties: %d"
         % (s["distinct_max_gap"], s["distinct_max_gap_n"], s["ties_max_gap"]))


# ==========================================================================
# 5. the deployed-shaped rule against the floor, anti-rule control per cell
# ==========================================================================

def step_rules():
    print("== 5/6 rank-band rule vs the floor, with the misaligned control")
    rows = []
    # n runs to 8 because that is the range registered criterion S3 names ("reported for every cell
    # to n = 8"). The earlier artifact stopped at 6, which made S3 a subset of what it promised --
    # a criterion reported as met while measuring less than it said. Measured cost of the extension
    # at n = 8: about 11 s for the k = 3 cell, well inside the enumeration's budget.
    for n in [5, 6, 7, 8]:
        for m in [2, 3]:
            for k in range(2, min(n, m) + 1):
                windows = 0
                a_lose = 0
                c_lose = 0
                worst = 0.0
                # Registered P2 conditions on the window's own LDS ("whenever 2 <= k < LDS"), which
                # is a different population from the cell's k < m. Both are carried, because the
                # registered prior is answered on its own condition or not at all.
                lds_windows = 0
                lds_lose = 0
                # A zero floor does not mean a free mapping: windows where the floor is already 0
                # can still lose, and that is the avoidable half of the gap the paper separates.
                zero_windows = 0
                zero_lose = 0
                for seq in itertools.product(range(m), repeat=n):
                    windows += 1
                    f = F.restricted_floor_dp(seq, k)
                    a = F.cost_of_assign(seq, F.band_assign(seq, k, m, True), k)
                    c = F.cost_of_assign(seq, F.band_assign(seq, k, m, False), k)
                    if a > f:
                        a_lose += 1
                    if c > f:
                        c_lose += 1
                    if f > 0 and a / f > worst:
                        worst = a / f
                    if k < F.lds(seq):
                        lds_windows += 1
                        if a > f:
                            lds_lose += 1
                    if f == 0:
                        zero_windows += 1
                        if a > 0:
                            zero_lose += 1
                row = {"n": n, "m": m, "k": k, "windows": windows,
                       "aligned_loses": a_lose, "aligned_fraction": a_lose / windows,
                       "aligned_worst_ratio": round(worst, 4),
                       "control_loses": c_lose, "control_fraction": c_lose / windows,
                       "p2_lds_windows": lds_windows, "p2_lds_loses": lds_lose,
                       "p2_lds_fraction": (lds_lose / lds_windows) if lds_windows else None,
                       "zero_floor_windows": zero_windows, "zero_floor_loses": zero_lose,
                       "zero_floor_fraction": (zero_lose / zero_windows) if zero_windows else None}
                rows.append(row)
                note("n=%d m=%d k=%d: aligned %d/%d (%.3f) worst %.3f, control %d/%d (%.3f)"
                     % (n, m, k, a_lose, windows, a_lose / windows, worst,
                        c_lose, windows, c_lose / windows))
                note("  registered P2 population (k < LDS): %d windows, %d lose%s; "
                     "zero-floor windows: %d, of which %d lose"
                     % (lds_windows, lds_lose,
                        (" (%.4f)" % (lds_lose / lds_windows)) if lds_windows else " -- EMPTY",
                        zero_windows, zero_lose))
                if c_lose == 0:
                    fail("control cannot lose in cell n=%d m=%d k=%d -- cell measures nothing"
                         % (n, m, k))
    R["rules"] = rows
    p2 = [r for r in rows if r["p2_lds_windows"]]
    zf = [r for r in rows if r["zero_floor_windows"]]
    R["rules_summary"] = {
        "cells": len(rows),
        "aligned_min_fraction": min(r["aligned_fraction"] for r in rows),
        "aligned_max_fraction": max(r["aligned_fraction"] for r in rows),
        "aligned_max_worst_ratio": max(r["aligned_worst_ratio"] for r in rows),
        "control_min_fraction": min(r["control_fraction"] for r in rows),
        "p2_registered_cells": len(p2),
        "p2_registered_windows": sum(r["p2_lds_windows"] for r in p2),
        "p2_registered_loses": sum(r["p2_lds_loses"] for r in p2),
        "p2_registered_max_fraction": max(r["p2_lds_fraction"] for r in p2) if p2 else None,
        "zero_floor_windows": sum(r["zero_floor_windows"] for r in zf),
        "zero_floor_loses": sum(r["zero_floor_loses"] for r in zf),
        "zero_floor_max_fraction": max(r["zero_floor_fraction"] for r in zf) if zf else None,
    }
    s = R["rules_summary"]
    note("aligned loses on %.3f..%.3f of windows across %d cells, worst ratio %.2f"
         % (s["aligned_min_fraction"], s["aligned_max_fraction"], s["cells"],
            s["aligned_max_worst_ratio"]))


# ==========================================================================
# 6. the forced cells, reported as forced rather than as results
# ==========================================================================

def step_forced_cells():
    print("== 6/6 cells that cannot measure anything, reported as such")
    # k=1: one queue admits exactly one assignment, so rule and floor coincide
    same = True
    for n in [4, 5]:
        for seq in itertools.permutations(range(n)):
            f = F.restricted_floor_dp(seq, 1)
            a = F.cost_of_assign(seq, F.band_assign(seq, 1, n, True), 1)
            if f != a:
                same = False
    R["forced_cells"] = {"k1_rule_equals_floor": bool(same)}
    note("k=1: rule equals floor on every window (forced, not a comparison): %s" % same)
    if not same:
        fail("k=1 is not forced, so the model admits a choice there -- check the enqueue model")


def main():
    step_certificate()
    step_threshold_distinct()
    step_threshold_ties()
    step_gap()
    step_rules()
    step_forced_cells()

    R["problems"] = PROBLEMS
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(R, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("\nwrote %s" % os.path.basename(OUT))
    if PROBLEMS:
        print("EMIT: %d PROBLEM(S)" % len(PROBLEMS))
        return 1
    print("EMIT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
