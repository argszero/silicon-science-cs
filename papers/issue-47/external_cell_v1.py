"""Issue #47 -- the committed EXTERNAL cell: does the instrument's ORDERING survive contact with a
published system result, and does the harness even REACH that system's cost scale?

The registration committed one cell anchored to published system numbers rather than to a specified
error family (its fallback clause: anchor to the published numbers and report the residual rather
than claiming a match).  The anchor, read from the arXiv record on 2026-09-15
(<https://arxiv.org/abs/2608.27975>, LAH / S4-FIFO cache eviction):

  * pre-trained on **4,140** production traces, evaluated on **1,035**;
  * S4-FIFO improves the **mean efficiency by 26%** over S3-FIFO, and by **8%** over 3L-Cache;
  * robustness: it "increases miss ratio over FIFO by **0.8% on the worst trace**, whereas 3L-Cache
    increases FIFO's miss ratio by **8.8%**".

Three tests.  The third was added because the first run of the second one failed in a way that is
itself a finding.

X1 -- ORDER (no unit conversion needed).  The published pair is CONCORDANT: the cache with the
      larger mean gain (26% vs the implied 16.7%) is also the one with the smaller worst-trace
      degradation (0.8% vs 8.8%).  Mean and tail move TOGETHER in that system.  Does the same hold
      across this harness's profiles -- is mean gain across units concordant with the best unit's
      degradation?  Reported with an interval and recomputed WITHOUT the zero-error anchor, which
      is extreme on both axes and would inflate the concordance by construction.

X2 -- REACH (not "match"), reported and NOT gated: it is a property of the harness, so a
      failing gate would be meaningless.  What IS gated is that the two counts summarise the
      blocks they claim to summarise and that the reference scale is the published pair.  The published reference scale is a worst-trace degradation of 0.8-8.8%
      of the non-learned baseline.  Is that scale reachable in this harness at all?  A family that
      never produces a worst unit worse than the classic arm would be *uniformly gentler than a
      real predictor's errors*, and that is a scope limit of the harness -- the thing this cell
      exists to expose.  Measured against FIFO for paging, because FIFO is the baseline the
      published robustness number is stated against, with LRU as the secondary reference.

X3 -- the maximum harm the harness can be made to produce, per problem, by an explicitly harmful
      policy (never buy; evict the most imminent page; order the schedule by descending predicted
      size).  Without this bound, "the grid never degrades" would be indistinguishable from "the
      grid cannot see degradation".

Run: python3 external_cell_v1.py     (deterministic; output JSON byte-identical across runs)
"""
import io
import json
import os
import random
import sys

import instrument_v0 as I
import paging_v1 as P1          # the repaired, frozen error ATTACHMENT for the paging cell

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "external_cell_v1_results.json")

REPS = 16              # this instrument's own replicate count (instrument_v0 uses 16, REPS=8)
TRACES = 8             # paging traces per replicate (instrument_v0 uses 4): 128 units per profile
                       # rather than 32, because most profiles coincide at the coarser resolution
                       # -- a measurement limit, not a finding, so it was raised.

# ---- the published anchor, numbers read from the arXiv abstract (verified 2026-09-15) ----
ANCHOR = {
    "arxiv": "2608.27975",
    "title": ("Learning-Augmented Heuristics: Simple, yet Smart, Robust and Interpretable "
              "Cache Eviction"),
    "submitted": "2026-08-28",
    "pretrain_traces": 4140,
    "eval_traces": 1035,
    "mean_gain_over_classic": 0.26,                  # S4-FIFO over S3-FIFO
    "worst_trace_degradation": 0.008,                # S4-FIFO over FIFO, worst trace
    "comparison_worst_trace_degradation": 0.088,     # 3L-Cache over FIFO, worst trace
    # DERIVED with the derivation written down rather than the value asserted: S4-FIFO is 8%
    # better than 3L-Cache and 26% better than S3-FIFO, so 3L-Cache sits at 1.26/1.08 of
    # S3-FIFO, i.e. +16.7% mean.
    "implied_comparison_mean_gain": 1.26 / 1.08 - 1.0,
}

checks = []
reports = []


def check(name, ok, detail=""):
    checks.append({"check": name, "pass": bool(ok), "detail": detail})
    print("%-6s %-58s %s" % ("PASS" if ok else "FAIL", name, detail))


def report(name, detail=""):
    """A MEASUREMENT, printed as one.  X2 is the reason this exists: it was first written as
    check(..., True, ...), which can never fire -- a gate that is always green is not a gate, and
    the reach numbers are an observation about the harness, not a property of it."""
    reports.append({"report": name, "detail": detail})
    print("%-6s %-58s %s" % ("REPORT", name, detail))


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return 0.0 if not n else (xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2]))


def kendall_tau(xs, ys):
    """Tau-a over pairs; a tied coordinate contributes to neither numerator nor denominator."""
    num = den = 0
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            a, b = xs[i] - xs[j], ys[i] - ys[j]
            if a == 0 or b == 0:
                continue
            num += 1 if (a * b) > 0 else -1
            den += 1
    return (num / den) if den else None


def boot_tau(xs, ys, reps=2000, seed=31):
    rng = random.Random(seed)
    n = len(xs)
    vals = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        t = kendall_tau([xs[i] for i in idx], [ys[i] for i in idx])
        if t is not None:
            vals.append(t)
    if not vals:
        return [None, None]
    vals.sort()
    return [vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]]


# ---------------------------------------------------------------- classic baselines
def fifo_cost(trace, k):
    """FIFO, implemented independently of the blend's score code: a queue, evict the oldest."""
    queue, cost = [], 0
    for p in trace:
        if p in queue:
            continue
        cost += 1
        if len(queue) >= k:
            queue.pop(0)
        queue.append(p)
    return cost


def lru_cost(trace, k):
    """LRU, a second independent implementation (most-recently-used kept at the end)."""
    order, cost = [], 0
    for p in trace:
        if p in order:
            order.remove(p)
            order.append(p)
            continue
        cost += 1
        if len(order) >= k:
            order.pop(0)
        order.append(p)
    return cost


# ---------------------------------------------------------------- unit measurements
PAGING_CLASSICS = {"fifo": fifo_cost, "lru": lru_cost}


def paging_units(rep, profile, mode="normal"):
    """The learned arm uses the PER-PAGE attachment (paging_v1.simulate, mode="per_page").

    The step-common attachment of instrument_v0 is kept as an explicit second arm, because the
    difference between them is the subject of control C5.
    """
    out = []
    for t in range(TRACES):
        trace = I.paging_realization(rep, t)
        occ = I.build_occurrences(trace)
        cap = I.TRACE_LEN + 1
        if mode == "anti":
            learned = paging_anti(trace, occ, I.K_PAGES, cap)
        elif mode == "shared_attachment":
            shared = (None if profile == "zero" else
                      I.gen_errors(profile, I.TRACE_LEN,
                                   I.seed_of("pg", "err", profile, rep, t)))
            learned = I.paging_cost(trace, occ, I.K_PAGES, 1.0, shared, cap)
        else:
            learned, _opt, _stats = P1.simulate(trace, occ, profile, rep, t, mode="per_page")
        out.append(({name: f(trace, I.K_PAGES) for name, f in PAGING_CLASSICS.items()}, learned))
    return out


def paging_anti(trace, occ, k, cap):
    """A deliberately harmful policy: evict the page whose next use is SOONEST.

    The first version of the adversarial arm collapsed every predicted distance to the floor,
    which does not produce harm -- it produces ties, and the tie-break happened to be harmless.
    A harmful arm must be stated as a POLICY, and the mirror image of Belady is the natural one.
    """
    cache, cost = set(), 0
    for i, p in enumerate(trace):
        if p in cache:
            continue
        cost += 1
        if len(cache) < k:
            cache.add(p)
        else:
            victim = min(cache, key=lambda q: (I.next_arrival(occ, i, q, cap), q))
            cache.discard(victim)
            cache.add(p)
    return cost


def ski_units(rep, profile, mode="normal"):
    ns = I.ski_realization(rep)
    out = []
    for i, n in enumerate(ns):
        classic = I.ski_cost(I.ski_classic_day(), n)
        if mode == "anti":
            learned = I.ski_cost(None, n)            # the policy: never buy
        else:
            e = I.gen_errors(profile, len(ns), I.seed_of("ski", "err", profile, rep))[i]
            learned = I.ski_cost(I.ski_trusted_day(max(1, int(round(n * (1.0 + e))))), n)
        out.append(({"classic": classic}, learned))
    return out


def sched_units(rep, profile, mode="normal"):
    jobs = I.sched_realization(rep)
    if mode == "anti":
        order = sorted(range(I.N_JOBS), key=lambda j: (-jobs[j], j))   # largest job first
    else:
        errs = I.gen_errors(profile, I.N_JOBS, I.seed_of("sc", "err", profile, rep))
        pred = [max(1, int(round(jobs[j] * (1.0 + errs[j])))) for j in range(I.N_JOBS)]
        order = sorted(range(I.N_JOBS), key=lambda j: (pred[j], j))
    classic = I.flow_of_order(list(range(I.N_JOBS)), jobs)
    return [({"classic": classic}, I.flow_of_order(order, jobs))]


BUILD = {"paging": paging_units, "ski": ski_units, "sched": sched_units}


def cells_for(prob, profile, mode="normal", classic="fifo"):
    """Mean gain over units and the worst unit's degradation, both relative to the classic arm."""
    gains, degr = [], []
    for rep in range(REPS):
        for clut, learned in BUILD[prob](rep, profile, mode):
            base = clut[classic] if classic in clut else clut["classic"]
            if base == 0:
                continue
            gains.append((base - learned) / base)       # >0 => the prediction arm is better
            degr.append((learned - base) / base)        # >0 => it is worse
    return {"problem": prob, "profile": profile, "mode": mode, "classic": classic,
            "n_units": len(gains), "mean_gain": mean(gains),
            "worst_unit_degradation": max(degr) if degr else 0.0,
            "best_unit_degradation": min(degr) if degr else 0.0,
            "units_helped": sum(1 for g in gains if g > 1e-12),
            "units_hurt": sum(1 for g in gains if g < -1e-12)}


def main():
    problems = ("ski", "paging", "sched")
    profiles = sorted(I.PROFILES)
    cells = {p: [cells_for(p, pr) for pr in profiles] for p in problems}
    out = {"anchor_published_numbers": ANCHOR, "reps": REPS, "paging_traces_per_rep": TRACES,
           "cells": cells, "tests": {}, "controls": {}}

    # ------------------------------------------------------------------ X1 (order)
    X1 = []
    for p in problems:
        g = [c["mean_gain"] for c in cells[p]]
        d = [-c["worst_unit_degradation"] for c in cells[p]]      # higher = better tail
        keep = [i for i, c in enumerate(cells[p]) if c["profile"] != "zero"]
        X1.append({"problem": p, "n_profiles": len(profiles),
                   "n_distinct_mean_gains": len({round(x, 9) for x in g}),
                   "kendall_tau_mean_vs_tail": kendall_tau(g, d),
                   "ci95": boot_tau(g, d),
                   "tau_excluding_the_zero_anchor": kendall_tau([g[i] for i in keep],
                                                                [d[i] for i in keep]),
                   "units_per_profile": cells[p][0]["n_units"]})
    published_concordant = (ANCHOR["mean_gain_over_classic"] > ANCHOR["implied_comparison_mean_gain"]
                            and ANCHOR["worst_trace_degradation"]
                            < ANCHOR["comparison_worst_trace_degradation"])
    out["tests"]["X1_order"] = {"blocks": X1, "published_pair_is_concordant": published_concordant}

    # ------------------------------------------------------------------ X2 (reach)
    ref_lo = ANCHOR["worst_trace_degradation"]
    ref_hi = ANCHOR["comparison_worst_trace_degradation"]
    X2 = []
    for p in problems:
        degrs = sorted(c["worst_unit_degradation"] for c in cells[p])
        X2.append({"problem": p, "min": degrs[0], "median": median(degrs), "max": degrs[-1],
                   "n_profiles_at_or_above_the_published_0.8pct": sum(1 for d in degrs if d >= ref_lo),
                   "n_profiles_at_or_above_the_published_8.8pct": sum(1 for d in degrs if d >= ref_hi),
                   "reaches_the_published_scale": bool(any(d >= ref_lo for d in degrs))})
    out["tests"]["X2_reach"] = {"blocks": X2, "reference_low": ref_lo, "reference_high": ref_hi}

    # ------------------------------------------------------------------ X3 (harm bound)
    X3 = []
    for p in problems:
        a = cells_for(p, "antipolicy", "anti")
        X3.append({"problem": p, "policy": {"ski": "never buy", "paging": "evict the soonest-reused page",
                                            "sched": "largest predicted job first"}[p],
                   "mean_gain": a["mean_gain"], "worst_unit_degradation": a["worst_unit_degradation"],
                   "units_hurt": a["units_hurt"], "n_units": a["n_units"]})
    out["tests"]["X3_harm_bound"] = {"blocks": X3}

    # ------------------------------------------------------------------ controls
    ctl = {}
    zero = {p: cells_for(p, "zero") for p in problems}
    ctl["C1_zero_error_both_arms"] = [(p, zero[p]["mean_gain"], zero[p]["worst_unit_degradation"])
                                      for p in problems]
    # C2 -- determinism, evaluated in two INDEPENDENT runs over the same units in different
    # orders (the first version compared one call to itself, which cannot fail).
    first = {}
    for rep in range(4):
        for t in range(TRACES):
            trace = I.paging_realization(rep, t)
            first[(rep, t)] = (fifo_cost(trace, I.K_PAGES), lru_cost(trace, I.K_PAGES))
    second, c2 = {}, []
    for t in range(TRACES):
        for rep in range(4):
            trace = I.paging_realization(rep, t)
            second[(rep, t)] = (fifo_cost(trace, I.K_PAGES), lru_cost(trace, I.K_PAGES))
    for key in sorted(first):
        c2.append(abs(first[key][0] - second[key][0]) + abs(first[key][1] - second[key][1]))
    ctl["C2_same_arm_identical"] = max(c2) if c2 else 0.0
    ctl["C2_n_units_compared"] = len(c2)
    # an INDEPENDENT check on the classic implementations: a constant trace pattern of length k
    # has no misses beyond the first k, and a periodic scan of k+1 pages under FIFO/LRU must miss
    # on every access to the (k+1)-th page -- known-by-hand values, not model outputs.
    hand = {}
    hand["fifo_cyclic_k1"] = fifo_cost([0, 1, 0, 1, 0, 1], 1)          # expect 6
    hand["lru_cyclic_k1"] = lru_cost([0, 1, 0, 1, 0, 1], 1)            # expect 6
    hand["fifo_repeat_1page_k2"] = fifo_cost([7] * 5, 2)               # expect 1
    hand["lru_repeat_1page_k2"] = lru_cost([7] * 5, 2)                 # expect 1
    hand["fifo_scan_k2"] = fifo_cost([0, 1, 2, 0, 1, 2], 2)            # expect 6
    hand["lru_scan_k2"] = lru_cost([0, 1, 2, 0, 1, 2], 2)              # expect 6
    ctl["C3_classic_implementations_against_hand_computed_values"] = hand
    ctl["C4_profile_grid_distinct_mean_gains"] = {
        p: len({round(c["mean_gain"], 9) for c in cells[p]}) for p in problems}

    # C5 -- THE ATTACHMENT CONTROL, three measurements, each stated as the relation it tests.
    #
    #   (a) a COMMON factor on every candidate's score cannot change an argmax, so the shared
    #       attachment must reproduce the zero-error cost EXACTLY -- but only for error vectors
    #       that never clamp: `max(1.0, d * (1 + e))` ties every candidate whose scaled distance
    #       falls below the floor, and a tie DOES change the victim.  The first version of this
    #       control used the profile `over_extreme` and failed 6 of 32 traces for exactly that
    #       reason -- a positive BIAS is not a non-negative MULTIPLIER.
    #   (b) the same non-negative vector under the per-page attachment must differ, because there
    #       each page carries its own multiplier.
    #   (c) reported for scale: how often a positive-bias profile under the shared attachment
    #       differs anyway (the clamp events in (a)).
    shared_prof = "over_extreme"
    exact_nonneg, differ_perpage, differ_shared_biased, n_tr = 0, 0, 0, 0
    for rep in range(4):
        for t in range(TRACES):
            trace = I.paging_realization(rep, t)
            occ = I.build_occurrences(trace)
            cap = I.TRACE_LEN + 1
            base = I.paging_cost(trace, occ, I.K_PAGES, 1.0, [0.0] * I.TRACE_LEN, cap)
            # (a) non-negative error vector: |e|, so every multiplier is >= 1 and cannot tie
            nonneg = [abs(e) for e in I.gen_errors(shared_prof, I.TRACE_LEN,
                                                   I.seed_of("pg", "err", shared_prof, rep, t))]
            sh = I.paging_cost(trace, occ, I.K_PAGES, 1.0, nonneg, cap)
            exact_nonneg += 1 if sh == base else 0
            # (b) the same information attached PER PAGE, so each page scales differently
            per_page_vec = [abs(e) for e in I.gen_errors(shared_prof, I.N_PAGES,
                                                         I.seed_of("pg", "err_perpage",
                                                                   shared_prof, rep, t))]
            saved = P1.page_errors
            try:
                P1.page_errors = lambda profile, r, tt, n_pages, _v=per_page_vec: list(_v)
                pp, _o, _s = P1.simulate(trace, occ, shared_prof, rep, t, mode="per_page")
            finally:
                P1.page_errors = saved
            differ_perpage += 1 if pp != base else 0
            # (c) the same profile, shared attachment, no abs(): clamp events inside
            raw = I.gen_errors(shared_prof, I.TRACE_LEN,
                               I.seed_of("pg", "err", shared_prof, rep, t))
            differ_shared_biased += 1 if I.paging_cost(
                trace, occ, I.K_PAGES, 1.0, raw, cap) != base else 0
            n_tr += 1
    ctl["C5_attachment_control"] = {
        "a_shared_attachment_exact_on_nonnegative_errors": "%d/%d" % (exact_nonneg, n_tr),
        "b_per_page_attachment_differs_on_the_same_information": "%d/%d" % (differ_perpage, n_tr),
        "c_shared_attachment_differs_on_a_positive_BIAS_profile": "%d/%d" % (differ_shared_biased, n_tr),
        "profile": shared_prof,
    }
    out["controls"] = ctl

    # ------------------------------------------------------------------ verdicts
    check("X1/published_pair_is_concordant", published_concordant,
          "mean 26.0%% vs %.1f%%, worst 0.8%% vs 8.8%%"
          % (ANCHOR["implied_comparison_mean_gain"] * 100))
    check("X1/harness_is_concordant_in_every_problem",
          all(b["kendall_tau_mean_vs_tail"] is not None and b["kendall_tau_mean_vs_tail"] > 0
              for b in X1),
          "tau %s" % [(b["problem"], round(b["kendall_tau_mean_vs_tail"], 3)) for b in X1])
    check("X1/concordance_survives_removing_the_zero_anchor",
          all(b["tau_excluding_the_zero_anchor"] is not None
              and b["tau_excluding_the_zero_anchor"] > 0 for b in X1),
          "tau without zero %s" % [(b["problem"], round(b["tau_excluding_the_zero_anchor"], 3))
                                   for b in X1])
    report("X2/reach_per_problem",
           "%s" % [(b["problem"], b["n_profiles_at_or_above_the_published_0.8pct"],
                    b["n_profiles_at_or_above_the_published_8.8pct"]) for b in X2])
    check("X2/the_reference_scale_is_the_published_pair",
          abs(ref_lo - ANCHOR["worst_trace_degradation"]) < 1e-15
          and abs(ref_hi - ANCHOR["comparison_worst_trace_degradation"]) < 1e-15
          and abs(ANCHOR["implied_comparison_mean_gain"] - (1.26 / 1.08 - 1.0)) < 1e-15,
          "ref %.4f / %.4f, derived comparison mean %.4f" % (ref_lo, ref_hi,
                                                             ANCHOR["implied_comparison_mean_gain"]))
    check("X2/the_counts_are_consistent_with_the_blocks_they_summarise",
          all(b["n_profiles_at_or_above_the_published_8.8pct"]
              <= b["n_profiles_at_or_above_the_published_0.8pct"] <= len(profiles)
              and b["reaches_the_published_scale"]
              == bool(b["n_profiles_at_or_above_the_published_0.8pct"] > 0) for b in X2)
          and [b["problem"] for b in X2] == list(problems),
          "counts vs blocks for %s" % [b["problem"] for b in X2])
    check("X3/an_explicitly_harmful_policy_is_reported_as_harm_in_every_problem",
          all(b["mean_gain"] < 0 and b["worst_unit_degradation"] > 0 for b in X3),
          "%s" % [(b["problem"], round(b["mean_gain"], 4), round(b["worst_unit_degradation"], 4))
                  for b in X3])
    check("C1/zero_error_is_the_consistency_anchor_and_never_degrades",
          all(g > 0 and d <= 1e-12 for _, g, d in ctl["C1_zero_error_both_arms"]),
          "%s" % [(p, round(g, 4), round(d, 4)) for p, g, d in ctl["C1_zero_error_both_arms"]])
    check("C2/same_arm_identical", ctl["C2_same_arm_identical"] == 0)
    check("C3/classic_implementations_match_hand_computed_values",
          ctl["C3_classic_implementations_against_hand_computed_values"]
          == {"fifo_cyclic_k1": 6, "lru_cyclic_k1": 6, "fifo_repeat_1page_k2": 1,
              "lru_repeat_1page_k2": 1, "fifo_scan_k2": 6, "lru_scan_k2": 6},
          str(ctl["C3_classic_implementations_against_hand_computed_values"]))
    check("C4/the_grid_is_not_degenerate",
          all(v >= 4 for v in ctl["C4_profile_grid_distinct_mean_gains"].values()),
          str(ctl["C4_profile_grid_distinct_mean_gains"]))
    c5 = ctl["C5_attachment_control"]
    check("C5a/shared_attachment_is_EXACTLY_invariant_to_non_negative_errors",
          c5["a_shared_attachment_exact_on_nonnegative_errors"] == "%d/%d" % (4 * TRACES, 4 * TRACES),
          "exact on %s traces" % c5["a_shared_attachment_exact_on_nonnegative_errors"])
    check("C5b/the_per_page_attachment_is_NOT_invariant_on_the_same_information",
          c5["b_per_page_attachment_differs_on_the_same_information"] != "0/%d" % (4 * TRACES,),
          "differs on %s" % c5["b_per_page_attachment_differs_on_the_same_information"])
    check("C5c/a_positive_BIAS_profile_is_not_a_non_negative_MULTIPLIER",
          c5["c_shared_attachment_differs_on_a_positive_BIAS_profile"] != "0/%d" % (4 * TRACES,),
          "the shared attachment still differs on %s traces"
          % c5["c_shared_attachment_differs_on_a_positive_BIAS_profile"])

    out["reports"] = reports
    out["ALL_PASS"] = all(c["pass"] for c in checks)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"ALL_PASS": out["ALL_PASS"],
                      "failed": [c["check"] for c in checks if not c["pass"]]}, indent=1))
    return 0 if out["ALL_PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
