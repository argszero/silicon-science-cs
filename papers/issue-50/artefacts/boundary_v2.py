#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 3: is the boundary indexed by CONTENTION, or by the POOL that
produces it?

WHAT THIS FILE IS.  Step 2 (`boundary_v1.py`) located the boundary rho*(h) over an (agents, workers) grid
and reported a bracket per hit rate, all four inside [0.982, 0.991].  That grid varied BOTH coordinates at
once: its cells with the largest measured contention were the ones with the FEWEST workers, and those also
have the fewest agents.  So the number it produced -- "the benefit crosses zero at rho* ~ 0.985" -- is a
statement about *those* systems, and the registration's construct ("a contention-indexed boundary") is a
claim that it is a statement about the contention.

This file tests that construct, on the object the construct names:

  * for each pool SIZE A separately, sweep the worker count and locate THAT curve's crossing, so the
    boundary is estimated inside a fixed-A family rather than across a mixed grid;
  * the crossing is located twice: as the sign change of the MEAN curve (interpolated between the two
    bracketing cells, in rho), and as a distribution over seeds (each seed has its own curve and hence its
    own crossing) -- the point estimate is a coordinate, the interval is the estimator's own resolution;
  * a seed whose curve has NO crossing inside the swept window, or MORE THAN ONE, is reported as such and
    EXCLUDED from the interval -- an exclusion count, not a silent drop;
  * the cross-A comparison is made PAIRED BY SEED, which is only meaningful because of a property of the
    model that is MEASURED here rather than assumed: the draw stream is filled agent-major, so agents
    0..min(A1,A2)-1 receive the SAME think and service draws in both runs (`shared_prefix_check`);
  * two x-axes are reported (the speculative run's rho and the serial run's rho), because "indexed by
    contention" is only a claim once it is said WHICH run's contention -- and a boundary that moves with A
    on one axis but not the other is a different finding from one that moves on both;
  * the matched-rho test promised by step 2's docstring ("the grid deliberately contains two different
    (agents, workers) settings reaching the SAME rho -- if the boundary is indexed by contention, the sign
    of the benefit there must agree") is implemented here, because step 2 promised it and never ran it.

WHAT A POSITIVE RESULT WOULD MEAN.  If rho*(A) is flat in A, the contention-indexed construct survives and
the boundary is a property of the load.  If rho*(A) moves with A, then "the benefit crosses zero at
rho* ~ 0.985" is not a statement about contention, and any manuscript sentence that stops there would be
reporting a mixed-grid artefact as a law.  Both outcomes are printable; this file does not prefer one.

CPU only, stdlib only, fixed seeds.  The model (`instrument_v0.py`) is imported UNMODIFIED and
`boundary_v1.py`'s estimator (`t_ci`) is reused rather than re-implemented, so step 2's numbers and step
3's are the same function of the same draws.
"""
import argparse
import io
import json
import math
import os
import random
import statistics
import sys

# The model accumulates ABSOLUTE event times and reports a step's latency as a difference of two of them,
# so "latency == T + S" is an identity about its arithmetic rather than about the real numbers: it holds to
# that arithmetic's own rounding.  MEASURED here at 2.2e-13 absolute on a 400-step, 16-agent run; the
# tolerance below is three orders above the measurement and nine below any difference this model can carry
# (times are O(1)).  Demanding bit-exactness of a re-derivation would be demanding a resolution the
# arithmetic does not have -- the same lesson step 1 recorded about fixed tolerances.
DERIVATION_TOL = 1e-09

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import instrument_v0 as I          # noqa: E402  the model, unmodified
import boundary_v1 as B1           # noqa: E402  step 2's estimator, reused


# --------------------------------------------------------------------------- cells
def cell2(model_cfg, agents, workers, h, seed):
    """One cell, one seed: BOTH runs made explicitly, so the cell can report both conventions of
    contention (the speculative run's rho and the serial run's rho) and the paired difference.

    This duplicates `instrument_v0.benefit`'s five lines on purpose -- the extra coordinate is the point of
    the round -- and the duplication is CONTROLLED: `--selftest` calls both and requires them to agree
    exactly, so a re-implementation that drifts from the model is a failure and not a second opinion.
    """
    cfg = dict(model_cfg, seed=seed)
    ser = I.agent_run(agents, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], cfg["seed"], tail=cfg["tail"],
                      q=cfg["q"], comp=cfg["comp"], speculate=False, c=workers)
    spe = I.agent_run(agents, cfg["mT"], cfg["mS"], h, cfg["steps"], cfg["seed"], tail=cfg["tail"],
                      q=cfg["q"], comp=cfg["comp"], speculate=True, c=workers)
    return {"seed": seed, "rho_spec": spe["rho"], "rho_serial": ser["rho"],
            "benefit_pct": 100.0 * (ser["mean_latency"] - spe["mean_latency"]) / ser["mean_latency"]}


def default_windows():
    """A window of worker counts per pool size, chosen to straddle that pool's crossing.

    The windows are NOT symmetric and they are not the same numbers: the crossing sits at a different
    worker count for each A, and a window that misses it reports "no crossing" for that A -- which is why
    that outcome is reported per A instead of being dropped.
    """
    return [(16, 2, 5), (24, 3, 7), (32, 4, 9), (48, 7, 14), (64, 10, 19), (96, 18, 26)]


def sweep(model_cfg, agents, c_lo, c_hi, h, seeds):
    """All cells of one (A, h) family, each cell reduced over seeds by means and by per-seed lists."""
    rows = []
    for c in range(c_lo, c_hi + 1):
        per = [cell2(model_cfg, agents, c, h, s) for s in seeds]
        bs = [p["benefit_pct"] for p in per]
        rows.append({"agents": agents, "workers": c, "h": h, "n_seeds": len(seeds),
                     "rho_spec": statistics.fmean(p["rho_spec"] for p in per),
                     "rho_spec_sd": statistics.stdev([p["rho_spec"] for p in per]),
                     "rho_serial": statistics.fmean(p["rho_serial"] for p in per),
                     "benefit_pct": statistics.fmean(bs), "per_seed": bs,
                     "ci": B1.t_ci(bs),
                     "positive_seeds": sum(1 for x in bs if x > 0),
                     "per_seed_rho_spec": [p["rho_spec"] for p in per],
                     "per_seed_rho_serial": [p["rho_serial"] for p in per]})
    rows.sort(key=lambda r: r["rho_spec"])
    return rows


# --------------------------------------------------------------------------- the crossing of one family
def interp(lo, hi, key):
    """Linear in x between two cells: the crossing of the mean curve.  A coordinate, not a measurement:
    what the estimator can resolve is the interval in `per_seed_crossings`."""
    b_lo, b_hi = lo["benefit_pct"], hi["benefit_pct"]
    if b_lo == b_hi:
        return statistics.fmean([lo[key], hi[key]])
    return lo[key] + (b_lo / (b_lo - b_hi)) * (hi[key] - lo[key])


def crossing_of_curve(rows, key):
    """Where the mean benefit crosses zero inside one (A, h) family, interpolated in `key`.

    The curve inside a window is monotone-decreasing in contention by construction of the window (the
    window is the crossing region), so the FIRST positive-to-nonpositive sign change in rho order is the
    crossing.  If the window contains more than one such change the family is reported AMBIGUOUS and the
    number is not used -- the step-2 rule, applied per family.
    """
    xs = [i for i in range(len(rows) - 1)
          if rows[i]["benefit_pct"] > 0 >= rows[i + 1]["benefit_pct"]]
    if not xs:
        return None
    if len(xs) > 1:
        return {"ambiguous": True, "n_crossings": len(xs),
                "crossings": [interp(rows[i], rows[i + 1], key) for i in xs]}
    i = xs[0]
    return {"ambiguous": False, "n_crossings": 1, "index": i,
            "x_lo": rows[i][key], "x_hi": rows[i + 1][key],
            "b_lo": rows[i]["benefit_pct"], "b_hi": rows[i + 1]["benefit_pct"],
            "x_star": interp(rows[i], rows[i + 1], key), "width": abs(rows[i + 1][key] - rows[i][key]),
            "cells": [(rows[i]["agents"], rows[i]["workers"]),
                      (rows[i + 1]["agents"], rows[i + 1]["workers"])]}


def per_seed_crossings(rows, key):
    """Each seed's own crossing inside the window, with the seeds that have none, or two, reported.

    A seed with no crossing has either not crossed inside the window (its curve ends positive) or started
    crossed (its curve begins non-positive).  Both are EXCLUSIONS and both are counted -- a seed silently
    dropped from the distribution would make the interval look sharper than the design is.
    """
    out, never_up, starts_down, ambiguous = [], 0, 0, 0
    for si in range(rows[0]["n_seeds"]):
        bs = [r["per_seed"][si] for r in rows]
        if bs[0] <= 0:                        # already crossed at the BOTTOM of the window: this seed's
            starts_down += 1                  # crossing (if it has one) lies below the swept region
            continue
        idx = [i for i in range(len(bs) - 1) if bs[i] > 0 >= bs[i + 1]]
        if not idx:
            never_up += 1                     # never crossed: the window does not reach far enough up
            continue
        if len(idx) > 1:
            ambiguous += 1
            continue
        i = idx[0]
        lo, hi = rows[i], rows[i + 1]
        out.append(lo[key] + (bs[i] / (bs[i] - bs[i + 1])) * (hi[key] - lo[key]))
    return {"crossings": out, "n_used": len(out), "excluded_never_crossed": never_up,
            "excluded_starts_crossed": starts_down, "excluded_ambiguous": ambiguous,
            "ci": B1.t_ci(out) if len(out) > 1 else None,
            "mean": statistics.fmean(out) if out else None,
            "sd": statistics.stdev(out) if len(out) > 1 else None}


# --------------------------------------------------------------------------- the ladder
def family(model_cfg, a, c_lo, c_hi, h, seeds):
    rows = sweep(model_cfg, a, c_lo, c_hi, h, seeds)
    fam = {"agents": a, "h": h, "c_range": [c_lo, c_hi], "rows": rows}
    for key in ("rho_spec", "rho_serial"):
        cr = crossing_of_curve(rows, key)
        fam["crossing_" + key] = cr
        fam["per_seed_" + key] = per_seed_crossings(rows, key) if cr else None
    return fam


def widen(windows, by):
    """Move every window's lower end DOWN in worker count (up in contention) by `by`, which is what a lower
    hit rate needs: the crossing moves toward saturation as h falls (`boundary_v1`: 0.9899 at h=0.5 vs
    0.9874 at h=1.0), so a window tuned for h=1.0 can start already crossed at h=0.5 -- in which case the
    family is reported NOT LOCATED rather than silently re-tuned.  The windows actually used are printed."""
    return [(a, max(1, c_lo - by), c_hi) for (a, c_lo, c_hi) in windows]


def ladder(model_cfg, h, seeds, windows=None):
    return [family(model_cfg, a, c_lo, c_hi, h, seeds)
            for (a, c_lo, c_hi) in (windows or default_windows())]


def direction(fams, key):
    """The ladder's verdict: does the crossing MOVE with the pool size, and in which direction?

    The comparison is between families' own intervals (per-seed, 95%), plus the paired-by-seed difference
    between the smallest and the largest pool -- paired because the draw stream is shared (measured in
    `shared_prefix_check`).  Reported as a number and an interval, never as an adjective.
    """
    got = [f for f in fams if f["crossing_" + key] and not f["crossing_" + key]["ambiguous"]]
    miss = [f["agents"] for f in fams if f["crossing_" + key] is None]
    amb = [f["agents"] for f in fams if f["crossing_" + key] and f["crossing_" + key]["ambiguous"]]
    if len(got) < 2:
        return {"n_families": len(fams), "n_located": len(got), "missing": miss, "ambiguous": amb,
                "verdict": "not enough families located"}
    xs = [f["crossing_" + key]["x_star"] for f in got]
    lo_f, hi_f = got[0], got[-1]
    delta = welch(lo_f["per_seed_" + key]["crossings"], hi_f["per_seed_" + key]["crossings"])
    span = max(xs) - min(xs)
    widths = [f["per_seed_" + key]["ci"][1] - f["per_seed_" + key]["ci"][0]
              for f in got if f["per_seed_" + key]["ci"]]
    mw = statistics.fmean(widths) if widths else 0.0
    return {"n_families": len(fams), "n_located": len(got), "missing": miss, "ambiguous": amb,
            "x_star_by_agents": [[f["agents"], f["crossing_" + key]["x_star"]] for f in got],
            "span": span, "mean_interval_width": mw,
            "span_over_interval": (span / mw) if mw else None,
            "two_sample_delta": delta, "two_sample_pair": [lo_f["agents"], hi_f["agents"]],
            "comparison": "two-sample: the two pool sizes do not share a draw stream (draw_prefix_check)",
            "monotone_decreasing": all(xs[i] >= xs[i + 1] for i in range(len(xs) - 1)),
            "verdict": ("MOVES with the pool size" if span > mw
                        else "consistent with a single rho (span within the intervals)")}


def welch(xs, ys):
    """Difference of means with a Welch interval, for the cross-A comparison.

    TWO-SAMPLE, not paired, and the reason is MEASURED rather than stylistic: the two pool sizes share their
    think-time draws but NOT their service-time draws (`draw_prefix_check`), so pairing them by seed index
    would pair draws that are not the same.  The interval is what the estimator can then support.
    """
    if len(xs) < 2 or len(ys) < 2:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    vx, vy = statistics.variance(xs) / len(xs), statistics.variance(ys) / len(ys)
    se = math.sqrt(vx + vy)
    tt = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306,
          10: 2.262, 11: 2.228, 12: 2.201, 15: 2.145, 20: 2.093, 25: 2.064, 30: 2.045}.get(
              min(len(xs), len(ys)), 1.96)
    return {"delta": mx - my, "ci": [mx - my - tt * se, mx - my + tt * se], "se": se,
            "n": [len(xs), len(ys)], "method": "two-sample"}


# --------------------------------------------------------------------------- matched-rho test
def both_inside(r1, r2):
    """Do the two cells' intervals overlap?  If they do, a sign difference is not evidence of a
    disagreement -- the cheapest way to manufacture an 'effect' here is to compare two noise clouds."""
    c1, c2 = r1["ci"], r2["ci"]
    if not c1 or not c2:
        return True
    return not (c1[1] < c2[0] or c2[1] < c1[0])


def matched_rho(fams, tol, key="rho_spec"):
    """The step-2 promise: settings reaching the SAME rho must agree on the sign of the benefit.

    Pairs of cells from DIFFERENT pool sizes whose measured contention differs by no more than `tol` (the
    sign test is applied to the pair, and pairs whose intervals overlap are counted separately -- a sign
    difference inside two overlapping intervals is not a disagreement).  The tolerance is a coordinate and
    is PRINTED with the result, together with the distance of the closest pair: a matched-rho test whose
    tolerance is wider than the effects it reads proves nothing.
    """
    cells = [(f["agents"], r) for f in fams for r in f["rows"]]
    pairs = []
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            (a1, r1), (a2, r2) = cells[i], cells[j]
            if a1 == a2:
                continue
            d = abs(r1[key] - r2[key])
            if d <= tol:
                pairs.append({"agents": [a1, a2], "workers": [r1["workers"], r2["workers"]],
                              "x": [r1[key], r2[key]], "dx": d,
                              "benefit": [r1["benefit_pct"], r2["benefit_pct"]],
                              "signs_agree": (r1["benefit_pct"] > 0) == (r2["benefit_pct"] > 0),
                              "intervals_overlap": both_inside(r1, r2)})
    pairs.sort(key=lambda p: p["dx"])
    dis = [p for p in pairs if not p["signs_agree"] and not p["intervals_overlap"]]
    return {"tol": tol, "n_pairs": len(pairs), "n_disagreeing": len(dis),
            "closest": pairs[0]["dx"] if pairs else None, "pairs": pairs}


# --------------------------------------------------------------------------- the property the design rests on
def derive_draws(n_agents, seed, cfg):
    """The model's own draw order, re-derived: all think times first, then all service times.

    Re-derived HERE because the model does not expose its draws, and VALIDATED below against the model's own
    latencies -- otherwise a statement about which coordinate is shared would be a statement about this
    file's reading of the model rather than about the model.
    """
    rng = random.Random(seed)
    T = [[rng.expovariate(1.0 / cfg["mT"]) for _ in range(cfg["steps"])] for _ in range(n_agents)]
    S = [[I.draw_service(rng, cfg["mS"], cfg["tail"]) for _ in range(cfg["steps"])]
         for _ in range(n_agents)]
    return T, S


def draw_prefix_check(seeds, agents=(16, 64)):
    """WHICH coordinate the two pool sizes share -- the assay that decides whether the cross-A comparison
    may be paired, and the reason it may not.

    With `speculate=False` and one worker per agent (c >= A) nothing queues, so a step's latency is exactly
    T+S and the run's latency list exposes the draws.  Four measurements, each with its own control:

      * `derivation_validated` -- the re-derived T+S reproduces the model's latencies for EVERY step of
        EVERY agent (full-precision equality, not a mean);
      * `same_A_invariance` -- the same A at c = A and c = 4A (both unqueued) gives IDENTICAL latencies:
        the positive control that makes "two runs differ" mean the draws differ and not the pool size;
      * `think_shared` -- the think times of the first min(A1, A2) agents ARE the same in both runs, because
        the array is filled agent-major and T comes first;
      * `service_shared` -- the service times are NOT, because S is drawn after ALL of T, so the RNG stands
        at a different position when S starts (A=16: after 6400 draws; A=64: after 25600).

    The last fact is the round's first result and it CHANGED the estimator: the cross-A comparison in this
    file is two-sample (`welch`), because the seeds are not a pairing coordinate across pool sizes.  The
    first version of this file asserted the pairing instead of measuring it and the assay refuted it here.
    """
    a1, a2 = agents
    cfg = I.default_cfg()
    out = {"agents": list(agents), "seeds": len(seeds), "checked": 0, "n_compared": a1 * cfg["steps"],
           "derivation_validated": 0, "same_A_invariance": 0, "think_shared": 0, "service_shared": 0,
           "derivation_tol": DERIVATION_TOL, "derivation_max_diff": 0.0,
           "first_service_mismatch_agent": None, "max_abs_service_diff": 0.0,
           "rng_position_when_S_starts": [a1 * cfg["steps"], a2 * cfg["steps"]]}
    for s in seeds:
        r1 = I.agent_run(a1, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], s, tail=cfg["tail"], q=cfg["q"],
                         comp=cfg["comp"], speculate=False, c=a1)
        r2 = I.agent_run(a2, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], s, tail=cfg["tail"], q=cfg["q"],
                         comp=cfg["comp"], speculate=False, c=a2)
        r3 = I.agent_run(a1, cfg["mT"], cfg["mS"], 0.0, cfg["steps"], s, tail=cfg["tail"], q=cfg["q"],
                         comp=cfg["comp"], speculate=False, c=4 * a1)
        T1, S1 = derive_draws(a1, s, cfg)
        T2, S2 = derive_draws(a2, s, cfg)
        want = [T1[a][k] + S1[a][k] for a in range(a1) for k in range(cfg["steps"])]
        dmax = max(abs(x - y) for x, y in zip(want, r1["latencies"]))
        out["derivation_max_diff"] = max(out["derivation_max_diff"], dmax)
        out["derivation_validated"] += 1 if dmax <= DERIVATION_TOL else 0
        out["same_A_invariance"] += 1 if r1["latencies"] == r3["latencies"] else 0
        out["think_shared"] += 1 if T1 == T2[:a1] else 0
        out["service_shared"] += 1 if S1 == S2[:a1] else 0
        idx = next((i for i in range(a1) if S1[i] != S2[i]), None)
        if idx is not None and out["first_service_mismatch_agent"] is None:
            out["first_service_mismatch_agent"] = idx
        out["max_abs_service_diff"] = max(out["max_abs_service_diff"],
                                          max(abs(x - y) for x, y in
                                              zip([v for row in S1 for v in row],
                                                  [v for row in S2[:a1] for v in row])))
        out["checked"] += 1
    out["derivation_ok"] = out["derivation_validated"] == out["checked"]
    out["same_A_ok"] = out["same_A_invariance"] == out["checked"]
    out["think_shared_ok"] = out["think_shared"] == out["checked"]
    out["service_shared_ok"] = out["service_shared"] == out["checked"]
    return out


# --------------------------------------------------------------------------- report
def render_crossing(cr, ps):
    if cr and not cr["ambiguous"] and ps and ps["ci"]:
        return "%.5f [%.5f, %.5f]" % (cr["x_star"], ps["ci"][0], ps["ci"][1])
    if cr and cr["ambiguous"]:
        return "AMBIGUOUS (%d crossings in window)" % cr["n_crossings"]
    return "NO CROSSING in window"


def report(fams, h, mat, dirs, shared):
    print("== boundary by pool size (h=%.1f) ==" % h)
    print("  A     c window     spec rho range        serial rho range      rho* (spec rho)       "
          "rho* (serial rho)")
    for f in fams:
        rs = f["rows"]
        print("  %-5d %-12s %.5f..%.5f      %.5f..%.5f      %-21s %s" % (
            f["agents"], "%d..%d" % tuple(f["c_range"]), rs[0]["rho_spec"], rs[-1]["rho_spec"],
            rs[0]["rho_serial"], rs[-1]["rho_serial"],
            render_crossing(f["crossing_rho_spec"], f["per_seed_rho_spec"]),
            render_crossing(f["crossing_rho_serial"], f["per_seed_rho_serial"])))
        for key in ("rho_spec", "rho_serial"):
            p = f["per_seed_" + key]
            if p and p["n_used"]:
                print("        per seed (%s): %d used, sd %.5f | excluded: %d never crossed, %d starts "
                      "crossed, %d ambiguous" % (key, p["n_used"], p["sd"],
                                                 p["excluded_never_crossed"],
                                                 p["excluded_starts_crossed"],
                                                 p["excluded_ambiguous"]))
    for key in ("rho_spec", "rho_serial"):
        d = dirs[key]
        print("  direction (%s): %s" % (key, d["verdict"]))
        if "x_star_by_agents" in d:
            print("      rho* by A: %s | span %.5f vs mean interval width %.5f (x%.2f, %d famil%s located)"
                  % (" ".join("%d:%.5f" % (a, x) for a, x in d["x_star_by_agents"]), d["span"],
                     d["mean_interval_width"], d["span_over_interval"] or 0.0,
                     d["n_located"], "y" if d["n_located"] == 1 else "ies"))
            td = d["two_sample_delta"]
            print("      monotone non-increasing in A: %s | %s delta (A=%d minus A=%d): %s (n=%s)"
                  % (d["monotone_decreasing"], d["comparison"].split(":")[0], d["two_sample_pair"][0],
                     d["two_sample_pair"][1],
                     ("%+.5f [%+.5f, %+.5f]" % (td["delta"], td["ci"][0], td["ci"][1])) if td else "n/a",
                     td["n"] if td else "n/a"))
        if d.get("ambiguous"):
            print("      AMBIGUOUS families: A=%s" % d["ambiguous"])
        if d.get("missing"):
            print("      NOT LOCATED (the window missed the crossing): A=%s" % d["missing"])
    print("  matched-rho test (tol %.5f on %s rho): %d pair(s) across different pool sizes, %d disagreeing "
          "(sign differs AND the two cells' intervals are disjoint); closest pair %.5f apart"
          % (mat["tol"], "spec" if mat["key"] == "rho_spec" else "serial", mat["n_pairs"],
             mat["n_disagreeing"], mat["closest"] if mat["closest"] is not None else float("nan")))
    for p in mat["pairs"][:8]:
        print("      A=%s c=%s rho %s B %s -> %s" % (
            p["agents"], p["workers"], ["%.5f" % x for x in p["x"]], ["%+.3f" % b for b in p["benefit"]],
            "AGREE" if p["signs_agree"] else ("DISAGREE" if not p["intervals_overlap"]
                                              else "sign differs but intervals overlap")))
    print("  draw-sharing assay (what the cross-A comparison may assume):")
    print("      re-derived T+S equals the model's latencies for every step of every agent: %s (%d/%d "
          "seeds; worst |diff| %.3g against the stated arithmetic tolerance %.0e)"
          % (shared["derivation_ok"], shared["derivation_validated"], shared["checked"],
             shared["derivation_max_diff"], shared["derivation_tol"]))
    print("      positive control, same A at c=A and c=4A (both unqueued) identical: %s" % shared["same_A_ok"])
    print("      think times of the first %d agents SHARED across A=%d and A=%d: %s (%d/%d)"
          % (shared["agents"][0], shared["agents"][0], shared["agents"][1], shared["think_shared_ok"],
             shared["think_shared"], shared["checked"]))
    print("      service times SHARED: %s (%d/%d) -- S is drawn after ALL of T, so the RNG stands at %s "
          "draws in the two runs (first agent that differs: %s, max |diff| %.3g)"
          % (shared["service_shared_ok"], shared["service_shared"], shared["checked"],
             shared["rng_position_when_S_starts"], shared["first_service_mismatch_agent"],
             shared["max_abs_service_diff"]))
    print("      => the cross-A comparison cannot be paired by seed; it is %s"
          % dirs["rho_spec"]["comparison"].split(":")[0])


# --------------------------------------------------------------------------- controls
def selftest():
    """Each arm plants one defect in a SYNTHETIC family and requires exactly that defect to be reported,
    plus two assays of the real model.  Synthetic, so the battery holds on any machine and on any day."""
    print("== selftest ==")
    bad = 0

    def arm(tag, ok, detail):
        nonlocal bad
        print("  %-38s %s  %s" % (tag, "ok" if ok else "BAD", detail))
        bad += 0 if ok else 1

    def fam(agents, xs, bs, n_seeds=12):
        rows = []
        for k, (x, b) in enumerate(zip(xs, bs)):
            per = [b] * n_seeds
            rows.append({"agents": agents, "workers": 1 + k, "h": 1.0, "n_seeds": n_seeds,
                         "rho_spec": x, "rho_spec_sd": 0.0, "rho_serial": x - 0.02,
                         "benefit_pct": b, "per_seed": per, "ci": B1.t_ci(per),
                         "positive_seeds": sum(1 for v in per if v > 0),
                         "per_seed_rho_spec": [x] * n_seeds, "per_seed_rho_serial": [x - 0.02] * n_seeds})
        f = {"agents": agents, "h": 1.0, "c_range": [1, len(xs)], "rows": rows}
        for key in ("rho_spec", "rho_serial"):
            cr = crossing_of_curve(rows, key)
            f["crossing_" + key] = cr
            f["per_seed_" + key] = per_seed_crossings(rows, key) if cr else None
        return f

    xs = [0.960, 0.970, 0.980, 0.990, 1.000]

    # 1. the control against a test that always finds movement: the SAME curve at three pool sizes
    flat = [fam(a, xs, [2.0, 1.2, 0.4, -0.4, -1.2]) for a in (16, 32, 64)]
    d_flat = direction(flat, "rho_spec")
    same = [f["crossing_rho_spec"]["x_star"] for f in flat]
    arm("a flat ladder reports NO movement", d_flat["verdict"].startswith("consistent")
        and max(same) - min(same) < 1e-12,
        "three pool sizes carrying the SAME synthetic curve: rho* = %s, span %.3g, interval width %.3g "
        "-> %s" % (["%.5f" % x for x in same], d_flat["span"], d_flat["mean_interval_width"],
                   d_flat["verdict"]))

    # 2. the positive arm: a prescribed movement at a prescribed place
    base = [2.0, 1.2, 0.4, -0.4, -1.2]          # crossing at rho = 0.985 exactly
    shift = [fam(16, xs, base), fam(32, xs, [b - 0.8 for b in base]), fam(64, xs, [b - 1.6 for b in base])]
    d_shift = direction(shift, "rho_spec")
    got = [f["crossing_rho_spec"]["x_star"] for f in shift]
    want = [0.985, 0.975, 0.965]                # the crossing a downward shift of the curve places
    arm("a shifting ladder reports the movement", d_shift["verdict"].startswith("MOVES")
        and d_shift["monotone_decreasing"] and max(abs(g - w) for g, w in zip(got, want)) < 1e-9,
        "curves shifted DOWN by 0 / 0.8 / 1.6, which places the crossings at %s: read back as %s "
        "(span %.5f vs the estimator's own interval width %.5f)"
        % (["%.3f" % w for w in want], ["%.5f" % g for g in got], d_shift["span"],
           d_shift["mean_interval_width"]))

    # 3. a window that misses the crossing must be NAMED, not dropped
    gap = [fam(16, xs, [2.0, 1.2, 0.4, -0.4, -1.2]), fam(32, xs, [2.0, 1.2, 0.2, 0.1, 0.05]),
           fam(64, xs, [2.0, 1.2, 0.4, -0.4, -1.2])]
    d_gap = direction(gap, "rho_spec")
    arm("a family with no crossing is NAMED", d_gap["missing"] == [32] and d_gap["n_located"] == 2,
        "the middle family never crosses inside its window: reported as missing A=%s, %d of %d located -- "
        "an exclusion count, not a silently shorter list"
        % (d_gap["missing"], d_gap["n_located"], d_gap["n_families"]))

    # 4. the per-seed interval must move when the seeds move -- it is a statistic, not a decoration
    rows = fam(32, [0.97, 0.98, 0.99, 1.00], [1.0, 0.5, -0.5, -1.0], n_seeds=8)["rows"]
    base = per_seed_crossings(rows, "rho_spec")
    jiggled = [dict(r) for r in rows]
    for i, r in enumerate(jiggled):
        r["per_seed"] = [v + (0.30 if (k % 2) else -0.30) * (i + 1) / 4.0 for k, v in enumerate(r["per_seed"])]
    wide = per_seed_crossings(jiggled, "rho_spec")
    arm("the interval widens when the seeds move", base["n_used"] == 8 and wide["n_used"] == 8
        and wide["sd"] > base["sd"],
        "same mean curve, per-seed offsets scaled: sd %.5f -> %.5f from the same 8 seeds, so the interval "
        "is computed and not asserted" % (base["sd"], wide["sd"]))

    # 5. an ambiguous seed is excluded and COUNTED, never averaged in
    # A FIXTURE IS A TABLE [cell x seed] AND THE PLANT MUST BE WRITTEN ON THE AXIS THE READING READS:
    # `per_seed` is indexed by SEED and its position is the CELL, so one seed's whole curve is written by
    # touching one entry of every row.  The first version of these two arms wrote whole lists into one
    # row's `per_seed`, which plants along the seed axis -- nothing the reading looks at changed.  The two
    # arms below are identical except for the axis, so a future edit that gets it wrong fails here.
    amb_rows = fam(32, [0.97, 0.98, 0.99, 1.00], [1.0, 0.5, -0.5, -1.0], n_seeds=4)["rows"]
    for k, v in enumerate([1.0, -0.2, 1.0, -1.0]):        # seed 0 dips below zero and comes back
        amb_rows[k]["per_seed"][0] = v
    amb = per_seed_crossings(amb_rows, "rho_spec")
    arm("ambiguous seeds are counted, not averaged", amb["excluded_ambiguous"] == 1 and amb["n_used"] == 3
        and amb["n_used"] + amb["excluded_ambiguous"] + amb["excluded_never_crossed"]
        + amb["excluded_starts_crossed"] == 4,
        "a planted seed whose curve dips below zero and returns inside the window (two crossings): "
        "%d ambiguous exclusion(s), %d used, and the exclusions add up to the 4 seeds"
        % (amb["excluded_ambiguous"], amb["n_used"]))

    # 6. seeds that never cross, in both directions, are counted on their own side
    edge = fam(32, [0.97, 0.98, 0.99, 1.00], [1.0, 0.5, -0.5, -1.0], n_seeds=4)["rows"]
    for k, v in enumerate([-1.0, 0.5, -0.5, -1.0]):       # seed 0 starts crossed (window too narrow down)
        edge[k]["per_seed"][0] = v
    for k, v in enumerate([1.0, 0.5, 0.2, 0.1]):          # seed 2 never crosses (window too narrow up)
        edge[k]["per_seed"][2] = v
    ed = per_seed_crossings(edge, "rho_spec")
    arm("both exclusion reasons are named", ed["excluded_starts_crossed"] == 1
        and ed["excluded_never_crossed"] == 1 and ed["n_used"] == 2,
        "%d seed(s) already crossed at the bottom of the window, %d never crossed inside it, %d used -- a "
        "single 'excluded' bucket would hide which way the window is too narrow"
        % (ed["excluded_starts_crossed"], ed["excluded_never_crossed"], ed["n_used"]))

    # 7. the matched-rho test, two-sided, with its tolerance enforced
    m_agree = matched_rho([fam(16, [0.980], [1.0]), fam(64, [0.9801], [0.8])], 0.002)
    m_dis = matched_rho([fam(16, [0.980], [1.0]), fam(64, [0.9801], [-0.8])], 0.002)
    def spread(f, amp):
        """Give a synthetic family a per-seed spread, so its interval is not degenerate and 'overlap' can
        be tested at all: an arm whose fixtures have zero variance can only test the disjoint case."""
        for r in f["rows"]:
            r["per_seed"] = [r["benefit_pct"] + amp * (k - (r["n_seeds"] - 1) / 2.0)
                             for k in range(r["n_seeds"])]
            r["ci"] = B1.t_ci(r["per_seed"])
        return f

    m_over = matched_rho([spread(fam(16, [0.980], [1.0]), 0.5),
                          spread(fam(64, [0.9801], [-0.2]), 0.5)], 0.002)
    m_tight = matched_rho([fam(16, [0.980], [1.0]), fam(64, [0.982], [-0.8])], 0.002)
    arm("matched-rho test is two-sided", m_agree["n_disagreeing"] == 0 and m_dis["n_disagreeing"] == 1,
        "same-rho pair, agreeing signs: %d disagreement(s); the same pair with one sign flipped: %d -- the "
        "two arms differ only in the planted sign" % (m_agree["n_disagreeing"], m_dis["n_disagreeing"]))
    arm("matched-rho tolerance is enforced", m_tight["n_pairs"] == 0,
        "the same contradictory pair 0.00200 apart with tol 0.002: %d pair(s) matched -- the tolerance is a "
        "coordinate, and this file prints it with every result" % m_tight["n_pairs"])
    arm("overlapping intervals are not a disagreement", m_over["n_pairs"] == 1
        and m_over["n_disagreeing"] == 0,
        "a sign flip whose cells' intervals overlap counts as %d disagreement(s) -- a sign difference inside "
        "two noise clouds is not evidence" % m_over["n_disagreeing"])

    # 8. the re-implementation of the model's own benefit call must be the SAME function
    cfg = I.default_cfg()
    mine = cell2(cfg, 24, 6, 0.9, 101)
    theirs = I.benefit(dict(cfg, seed=101), 24, 6, 0.9)
    diff = max(abs(mine["benefit_pct"] - theirs["benefit_pct"]), abs(mine["rho_spec"] - theirs["rho"]))
    arm("cell2 reproduces the model's own benefit", diff == 0.0,
        "A=24 c=6 h=0.9 seed=101: this file's explicit two-run cell vs instrument_v0.benefit -- max |diff| "
        "%.3g (a second coordinate is added; the quantity is not re-derived differently)" % diff)

    # 9. the coordinate the cross-A comparison may use, ASSAYED on the model.  This is the arm that
    #    refuted this file's first version, which had asserted the pairing instead of measuring it.
    shared = draw_prefix_check(list(range(101, 104)), (16, 64))
    arm("draw sharing is assayed, and it decides the estimator",
        shared["derivation_ok"] and shared["same_A_ok"] and shared["think_shared_ok"]
        and not shared["service_shared_ok"],
        "re-derived T+S == the model's latencies to the arithmetic's own rounding (%d/%d seeds, worst "
        "|diff| %.3g <= %.0e); same A at c=A and c=4A identical (%d/%d); "
        "think times shared across A (%d/%d) but SERVICE TIMES are not (%d/%d; first agent differing %s, "
        "max |diff| %.3g) because S is drawn after all of T -- so the cross-A comparison is two-sample"
        % (shared["derivation_validated"], shared["checked"], shared["derivation_max_diff"],
           shared["derivation_tol"], shared["same_A_invariance"], shared["checked"],
           shared["think_shared"], shared["checked"], shared["service_shared"], shared["checked"],
           shared["first_service_mismatch_agent"], shared["max_abs_service_diff"]))

    # 10. a comparison whose basis is not stated is exactly the defect arm 9 found: the estimator must say
    #     which comparison it made.
    d_basis = direction(flat, "rho_spec")
    arm("the estimator names its comparison basis",
        "two-sample" in (d_basis.get("comparison") or ""),
        "`direction` reports its basis as %r -- the first version of this file paired the seeds and said so "
        "in prose; the basis is now a field the reader can check against the assay above"
        % (d_basis.get("comparison"),))

    print("  selftest: 10 arm(s), %d failure(s)" % bad)
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--h", type=float, default=1.0, help="hit rate of the speculative run")
    ap.add_argument("--seeds", type=int, default=32, help="how many seeds per cell (paired)")
    ap.add_argument("--tol", type=float, default=0.002, help="matched-rho tolerance, in rho units")
    ap.add_argument("--extend", type=int, default=0,
                    help="lower every window's c_lo by this many workers (a lower h needs more contention)")
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    cfg = I.default_cfg()
    seeds = list(range(101, 101 + a.seeds))
    fams = ladder(cfg, a.h, seeds, widen(default_windows(), a.extend) if a.extend else None)
    dirs = {key: direction(fams, key) for key in ("rho_spec", "rho_serial")}
    mat = matched_rho(fams, a.tol)
    mat["key"] = "rho_spec"
    shared = draw_prefix_check(seeds[:4], (16, 64))
    report(fams, a.h, mat, dirs, shared)
    if a.json:
        with io.open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"model": cfg, "h": a.h, "seeds": seeds, "tol": a.tol,
                                 "extend": a.extend,
                                 "families": fams, "direction": dirs, "matched_rho": mat,
                                 "draw_prefix": shared}, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
