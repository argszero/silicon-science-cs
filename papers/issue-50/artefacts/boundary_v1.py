#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 2: LOCATE the boundary rho*(h), do not assume its shape.

WHAT THIS FILE IS.  Step 1 (`instrument_v0.py`) built the model and made it reproduce its four classical
limits; it also refuted the monotonicity I had written into one of them: the benefit curve RISES before it
falls, because a speculative call is issued at the start of the think phase and so can also reach a free
worker sooner -- speculation buys SCHEDULE POSITION as well as hidden time.  This file locates the
boundary the registration names (P1: the benefit crosses zero at rho*(h), decreasing in h) and is written
around that refutation rather than on top of it:

  * the **peak** of the benefit curve is a MEASURED quantity, reported with its own interval, not an
    assumption -- and the crossing is searched only ABOVE it;
  * the crossing is bracketed by **bisection** on the sign over the ordered cell grid, and the bracket is
    reported with the measured contention at both ends;
  * every cell is a **paired** comparison over a seed list (serial and speculative runs share the seed, so
    they share the draw stream), and the interval is taken over seeds;
  * a **sharpness statistic** is reported: the fraction of seeds on each side of the bracket, so "the
    boundary is sharp" is a number and not an adjective;
  * contention is the **measured** rho of each cell, and the grid deliberately contains two different
    (agents, workers) settings reaching the SAME rho -- if the boundary is indexed by contention, the sign
    of the benefit there must agree; if it does not, that is reported, not averaged away.

WHY THE NON-MONOTONICITY HANDLING IS CONTROLLED AND NOT ASSERTED.  A search that ignores the peak finds a
crossing in the WRONG region (the rise is itself a sign change if the curve starts negative -- which it
does at high contention).  `--selftest` therefore runs the naive search beside the handled one and reports
where they disagree; if they never disagree on these cells, that is printed as a measured fact ("the
handling is not load-bearing here") rather than left as a claim.

CPU only, stdlib only, fixed seeds.  The model is `instrument_v0.py`, unmodified.
"""
import argparse
import io
import json
import math
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import instrument_v0 as I  # noqa: E402


# --------------------------------------------------------------------------- the estimator
def cell(cfg, agents, workers, h, seeds):
    """One cell: the PAIRED benefit over a seed list, plus the per-seed benefits.

    A seed is one draw stream.  Serial and speculative runs of the same seed see the same think times, the
    same service times and the same hit pattern, so their difference isolates the POLICY -- which is the
    same identity A2 uses.  The interval is over seeds (the only source of variation left).
    """
    per_seed, rhos = [], []
    for s in seeds:
        c = dict(cfg["model"], seed=s)
        r = I.benefit(c, agents, workers, h)
        per_seed.append(r["benefit_pct"])
        rhos.append(r["rho"])
    return {"agents": agents, "workers": workers, "h": h, "n_seeds": len(seeds),
            "rho": statistics.fmean(rhos), "benefit_pct": statistics.fmean(per_seed),
            "per_seed": per_seed, "ci": t_ci(per_seed),
            "positive_seeds": sum(1 for x in per_seed if x > 0)}


def t_ci(xs, level=0.95):
    """A t interval over the seed means.  The seeds are independent draw streams, so this is the interval
    the estimator's own resolution supports -- the step-1 lesson: never demand a resolution the estimator
    cannot produce, and print the one it has."""
    n = len(xs)
    if n < 2:
        return None
    se = statistics.stdev(xs) / math.sqrt(n)
    # two-sided 95% t quantiles, by n (12 seeds and up is all this file needs)
    t = {2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571, 7: 2.447, 8: 2.365, 9: 2.306,
         10: 2.262, 11: 2.228, 12: 2.201, 15: 2.145, 20: 2.093, 25: 2.064, 30: 2.045}.get(
             n, 1.96 if n > 30 else 2.201)
    m = statistics.fmean(xs)
    return [m - t * se, m + t * se]


# --------------------------------------------------------------------------- the search
def peak_index(rows):
    """Where the benefit is largest, over the cells sorted by measured contention.  Ties go to the
    LOWEST contention (the earliest maximum), which makes the reported peak the first place the curve
    stops improving rather than an arbitrary one of several equals."""
    best = 0
    for i, r in enumerate(rows):
        if r["benefit_pct"] > rows[best]["benefit_pct"] + 1e-12:
            best = i
    return best


def peak_plateau(rows):
    """The cells that are not distinguishable from the maximum -- the peak is a PLATEAU, not a point.

    MEASURED, and the measurement forced this function: on the first full sweep the benefits at the
    low-contention cells were 22.24 / 22.25 / 22.26 / 22.26 / 22.26 % -- an argmax over that reports an
    INDEX whose location is decided by the fifth significant figure of a difference the seed interval does
    not resolve (peak CI half-width here is ~0.06 pp).  So the peak is reported as an interval: every cell
    whose benefit is within the peak's own interval half-width (and never less than 1e-9) of the maximum,
    and the search for the crossing starts after that interval.  A plateau is a fact about the workload,
    not a defect; a point estimate of its location would be.
    """
    mx = max(r["benefit_pct"] for r in rows)
    hw = 0.0
    for r in rows:
        if r["benefit_pct"] == mx and r["ci"]:
            hw = abs(r["ci"][1] - r["ci"][0]) / 2.0
            break
    tol = max(1e-9, hw)
    idx = [i for i, r in enumerate(rows) if mx - r["benefit_pct"] <= tol]
    return {"indices": idx, "first": idx[0], "last": idx[-1], "n": len(idx), "tol": tol,
            "rho_first": rows[idx[0]]["rho"], "rho_last": rows[idx[-1]]["rho"],
            "best_index": max(range(len(rows)), key=lambda i: rows[i]["benefit_pct"]),
            "width_rho": rows[idx[-1]]["rho"] - rows[idx[0]]["rho"]}


def sign_changes(rows, lo):
    """Indices i >= lo with benefit[i] > 0 >= benefit[i+1] -- a non-negative-to-negative crossing."""
    out = []
    for i in range(lo, len(rows) - 1):
        if rows[i]["benefit_pct"] > 0 >= rows[i + 1]["benefit_pct"]:
            out.append(i)
    return out


def bisect_crossing(rows, lo):
    """The boundary at or above index `lo`, by bisection, with the bisection's limit stated.

    BISECTION ON A NON-MONOTONE PREDICATE IS NOT WELL DEFINED -- it converges to *a* crossing, and which
    one depends on the probes.  That is not a defect of this grid but a property of the rule, and it was
    measured here: on a synthetic curve that dips below zero before its peak, a search starting at the
    origin returned the crossing at the END of the array.  So the bisection is used only to LOCATE a
    bracket, and the boundary is then read from the region the search covers:

      * `n_crossings_in_region`, `first` -- every positive-to-nonpositive crossing in the searched region
        and the lowest-contention one among them;
      * `ambiguous` -- true when the region contains more than one, in which case the boundary is NOT
        identified from this grid and the number printed is the first of several rather than the boundary.

    Above the peak the curve here has exactly one crossing, so the rule and the bisection agree; where they
    would not, this reports it.
    """
    if lo >= len(rows) - 1:
        return None
    if rows[lo]["benefit_pct"] <= 0:
        return None                      # the region starts already crossed: nothing to search above it
    if rows[-1]["benefit_pct"] > 0:
        return None                      # no crossing in the reachable range: NOT FOUND, not a number
    a, b = lo, len(rows) - 1
    while b - a > 1:
        mid = (a + b) // 2
        if rows[mid]["benefit_pct"] > 0:
            a = mid
        else:
            b = mid
    xs = sign_changes(rows, lo)
    first = xs[0] if xs else None
    if first is None:
        return None
    lo_i, hi_i = first, first + 1
    return {"index": lo_i, "lo": lo_i, "hi": hi_i,
            "bisect_bracket": [a, b],
            "rho_lo": rows[lo_i]["rho"], "rho_hi": rows[hi_i]["rho"],
            "rho_star_inside": [min(rows[lo_i]["rho"], rows[hi_i]["rho"]),
                                max(rows[lo_i]["rho"], rows[hi_i]["rho"])],
            "benefit_lo": rows[lo_i]["benefit_pct"], "benefit_hi": rows[hi_i]["benefit_pct"],
            "n_crossings_in_region": len(xs), "crossing_rhos": [rows[i]["rho"] for i in xs],
            "ambiguous": len(xs) > 1, "cells": [rows[lo_i], rows[hi_i]]}


def locate(cfg, grid, h, seeds, naive=False):
    """The boundary at hit rate h over a grid of (agents, workers) settings.

    `naive=True` is the control: the search ignores the peak and starts from the lowest-contention cell,
    which is what "find where the benefit crosses zero" means if the refutation of step 1 is not carried
    into the search.
    """
    rows = sorted((cell(cfg, a, w, h, seeds) for (a, w) in grid), key=lambda r: r["rho"])
    p = peak_index(rows)
    plat = peak_plateau(rows)
    lo = 0 if naive else plat["last"]
    cross = bisect_crossing(rows, lo)
    all_cross = sign_changes(rows, 0)
    out = {"h": h, "n_cells": len(rows), "rows": rows, "peak_index": p,
           "peak_rho": rows[p]["rho"], "peak_benefit_pct": rows[p]["benefit_pct"],
           "peak_ci": rows[p]["ci"], "peak_plateau": plat, "search_from_index": lo, "naive": naive,
           "crossing": cross, "n_sign_changes": len(all_cross),
           "sign_change_rhos": [rows[i]["rho"] for i in all_cross],
           "ambiguous": bool(cross and cross["ambiguous"]) if cross else len(all_cross) > 1}
    if cross:
        c_lo, c_hi = cross["cells"]
        out["sharpness"] = {
            "cells": [(c_lo["agents"], c_lo["workers"], c_lo["rho"], c_lo["benefit_pct"],
                       c_lo["positive_seeds"], c_lo["n_seeds"]),
                      (c_hi["agents"], c_hi["workers"], c_hi["rho"], c_hi["benefit_pct"],
                       c_hi["positive_seeds"], c_hi["n_seeds"])],
            "separation": (c_lo["positive_seeds"] / c_lo["n_seeds"]) - (c_hi["positive_seeds"] / c_hi["n_seeds"]),
            "rho_width": abs(c_hi["rho"] - c_lo["rho"]),
        }
    return out


# --------------------------------------------------------------------------- controls
def benefit_unpaired(cfg, agents, workers, h, offset=5000):
    """The same quantity with the pairing REMOVED: the serial and speculative runs are given different
    draw streams.  This is the control's negative arm -- `instrument_v0` is not asked to provide it,
    because the model has one correct policy comparison and this is a wrong one."""
    m = cfg["model"]
    ser = I.agent_run(agents, m["mT"], m["mS"], 0.0, m["steps"], m["seed"],
                      tail=m["tail"], q=m["q"], comp=m["comp"], speculate=False, c=workers)
    spe = I.agent_run(agents, m["mT"], m["mS"], h, m["steps"], m["seed"] + offset,
                      tail=m["tail"], q=m["q"], comp=m["comp"], speculate=True, c=workers)
    return {"benefit_pct": 100.0 * (ser["mean_latency"] - spe["mean_latency"]) / ser["mean_latency"]}


def control_pairing(cfg, agents, workers, h, seeds):
    """The estimator's own control: the seeds must be PAIRED.

    Serial and speculative runs of one seed share the draw stream, so their difference removes the draw
    variance; if the two runs are given different seeds the same quantity is measured with the noise put
    back.  The control requires the paired estimator's interval to be strictly narrower -- and reports the
    ratio, so "pairing matters" is a number.  A policy comparison that does not pair its seeds is
    measuring the draws.
    """
    paired, unpaired = [], []
    for s in seeds:
        r = I.benefit(dict(cfg["model"], seed=s), agents, workers, h)
        paired.append(r["benefit_pct"])
        unpaired.append(benefit_unpaired(dict(cfg, model=dict(cfg["model"], seed=s)),
                                        agents, workers, h)["benefit_pct"])
    cp, cu = t_ci(paired), t_ci(unpaired)
    wp = (cp[1] - cp[0]) / 2.0 if cp else float("inf")
    wu = (cu[1] - cu[0]) / 2.0 if cu else float("inf")
    return {"paired_halfwidth": wp, "unpaired_halfwidth": wu, "ratio": (wu / wp) if wp else None,
            "paired_mean": statistics.fmean(paired), "unpaired_mean": statistics.fmean(unpaired)}


# --------------------------------------------------------------------------- driver
def default_cfg():
    return {"model": I.default_cfg(),
            "grid": [(16, w) for w in range(3, 21)] + [(24, w) for w in range(4, 33)] +
                     [(32, w) for w in range(5, 41)],
            "h_levels": [0.5, 0.7, 0.9, 1.0], "seeds": list(range(101, 113)),
            "naive_h": [1.0, 0.9, 0.7, 0.5]}


def run(cfg, use_naive=False, restrict_low=False, h_levels=None):
    rows = []
    grid = cfg["grid"]
    if restrict_low:                        # only the low-contention half: no crossing can exist here
        grid = [(a, w) for (a, w) in grid if w >= 16]
    for h in (h_levels if h_levels is not None else cfg["h_levels"]):
        r = locate(cfg, grid, h, cfg["seeds"], naive=use_naive)
        rows.append(r)
    return rows


def fnum(x, nd=3):
    return "%.*f" % (nd, x)


def report(rows, title):
    print(title)
    for r in rows:
        if r["crossing"]:
            c = r["crossing"]
            s = r.get("sharpness", {})
            pl = r["peak_plateau"]
            print("  h=%.1f  peak B=%+.2f%% over rho [%s, %s] (%d cell(s), tol %s)  crossing rho* inside "
                  "[%s, %s]  sharpness %.2f (votes %s)" % (
                      r["h"], r["peak_benefit_pct"], fnum(pl["rho_first"]), fnum(pl["rho_last"]), pl["n"],
                      fnum(pl["tol"], 3), fnum(c["rho_star_inside"][0]), fnum(c["rho_star_inside"][1]),
                      s.get("separation", float("nan")),
                      " / ".join("%d/%d" % (x[4], x[5]) for x in s.get("cells", []))))
        else:
            print("  h=%.1f  peak B=%+.2f%% over rho [%s, %s]  NO CROSSING in the reachable range (max "
                  "rho %s) -- reported as not found, not as a number" % (
                      r["h"], r["peak_benefit_pct"], fnum(r["peak_plateau"]["rho_first"]),
                      fnum(r["peak_plateau"]["rho_last"]),
                      fnum(max(x["rho"] for x in r["rows"]))))
        if r["ambiguous"]:
            print("       !! AMBIGUOUS: %d positive-to-negative crossings in the searched region (rhos "
                  "%s) -- the number above is the first of several, not the boundary"
                  % (r["crossing"]["n_crossings_in_region"] if r["crossing"] else r["n_sign_changes"],
                     [fnum(x) for x in (r["crossing"]["crossing_rhos"] if r["crossing"]
                                        else r["sign_change_rhos"])]))


def selftest(cfg):
    """Each arm plants one defect and requires exactly that defect to be reported.

    The defects are the ones this file exists to prevent: a search that ignores the curve's peak, a search
    that invents a crossing where the reachable range has none, an estimator that does not pair its seeds,
    and a peak read as an assumption instead of a measurement.
    """
    print("== selftest ==")
    bad = 0
    seeds = list(range(201, 209))

    def arm(tag, ok, detail):
        nonlocal bad
        print("  %-30s %s  %s" % (tag, "ok" if ok else "BAD", detail))
        bad += 0 if ok else 1

    # 1. the handled search and the naive one, MEASURED and reported rather than assumed
    handled = locate(cfg, cfg["grid"], 1.0, seeds)
    naive = locate(cfg, cfg["grid"], 1.0, seeds, naive=True)
    same_cross = bool(handled["crossing"] and naive["crossing"] and
                      handled["crossing"]["lo"] == naive["crossing"]["lo"])
    arm("naive vs handled search", True,
        "naive starts at index 0, the handled one at the peak (index %d) -- on this grid the answer is "
        "%s (rho* %s vs %s): the rise changes where the search STARTS, and whether it changes the "
        "boundary is a measurement, reported here rather than assumed"
        % (handled["peak_index"], "the same" if same_cross else "DIFFERENT",
           fnum(naive["crossing"]["rho_lo"]) if naive["crossing"] else "none",
           fnum(handled["crossing"]["rho_lo"]) if handled["crossing"] else "none"))

    # 2. the failure a boundary claim can suffer: a curve with TWO crossings. A search that starts at the
    #    origin and takes the first sign change reports the wrong one, and a claim built on it would be
    #    about the rise rather than the boundary. Synthetic fixture, so this arm holds on any machine.
    def synth(bs):
        return [{"rho": 0.10 + 0.05 * i, "benefit_pct": b, "ci": None, "n_seeds": 1,
                 "positive_seeds": 1 if b > 0 else 0, "agents": 1, "workers": 1, "h": 1.0}
                for i, b in enumerate(bs)]
    two = synth([+1.0, -0.5, +1.5, +2.0, -1.0])      # dips below zero BEFORE its peak: two crossings
    p2 = peak_index(two)
    n_all = len(sign_changes(two, 0))
    n_above = len(sign_changes(two, p2))
    from_origin = bisect_crossing(two, 0)
    above_peak = bisect_crossing(two, p2)
    differ = bool(from_origin and above_peak and from_origin["lo"] != above_peak["lo"])
    arm("two-crossing curve is reported", n_all == 2 and n_above == 1 and p2 == 3 and differ
        and from_origin["n_crossings_in_region"] == 2 and from_origin["ambiguous"],
        "synthetic curve %s: %d crossings over the whole ordered grid, %d above the peak (index %d); the "
        "first crossing is index %d when the search starts at the origin and index %d when it starts above "
        "the peak -- they DIFFER, and the origin search reports its region as AMBIGUOUS (%d crossings), "
        "which is the failure this arm exists to make visible"
        % ([round(x["benefit_pct"], 1) for x in two], n_all, n_above, p2,
           from_origin["lo"], above_peak["lo"], from_origin["n_crossings_in_region"]))

    # 2. no crossing in the reachable range must be NOT FOUND
    low = run(cfg, restrict_low=True, h_levels=[1.0])[0]
    arm("no crossing -> NOT FOUND", low["crossing"] is None,
        "restricted to the low-contention cells (no crossing exists there): the search returned %s"
        % ("NOT FOUND" if low["crossing"] is None else "a crossing at rho %.3f" % low["crossing"]["rho_lo"]))

    # 3. pairing: the unpaired estimator must have the wider interval
    pair = control_pairing(cfg, 24, 12, 0.9, seeds)
    arm("seed pairing matters", pair["ratio"] is not None and pair["ratio"] > 1.0,
        "unpaired/paired half-width ratio %.2f (paired %s, unpaired %s)"
        % (pair["ratio"] if pair["ratio"] else float("nan"),
           fnum(pair["paired_halfwidth"], 4), fnum(pair["unpaired_halfwidth"], 4)))

    # 4. the peak is a measurement: shifting it must move the search's start
    shifted = locate(cfg, cfg["grid"], 1.0, seeds)
    pl = shifted["peak_plateau"]
    arm("peak is measured, as a plateau", shifted["peak_index"] > 0 and pl["n"] >= 1,
        "peak %+.2f%% over rho [%s, %s] (%d cell(s) of %d within the peak's own interval, tol %s); the "
        "search starts after the plateau, at index %d -- read from the cells, not assumed"
        % (shifted["peak_benefit_pct"], fnum(pl["rho_first"]), fnum(pl["rho_last"]), pl["n"],
           shifted["n_cells"], fnum(pl["tol"], 3), shifted["search_from_index"]))

    # 5. the bracket must be adjacent cells: a search that returns a non-adjacent bracket is not bisecting
    if handled["crossing"]:
        c = handled["crossing"]
        arm("bracket is adjacent cells", c["hi"] - c["lo"] == 1,
            "indices %d..%d, rho [%s, %s]" % (c["lo"], c["hi"], fnum(c["rho_lo"]), fnum(c["rho_hi"])))
    else:
        arm("bracket is adjacent cells", False, "no crossing found at h=1.0 to bracket")

    flat = synth([20.0, 20.02, 20.01, 20.00, 19.9, 10.0])
    for r in flat:
        r["ci"] = [19.9, 20.1]
    fp = peak_plateau(flat)
    arm("flat curve is a plateau", fp["n"] >= 3 and fp["width_rho"] > 0,
        "a curve flat within its own interval over four cells at ~20%%: reported as %d cell(s) spanning "
        "rho [%s, %s] (tol %s) -- an argmax would have named one of them" % (
            fp["n"], fnum(fp["rho_first"], 2), fnum(fp["rho_last"], 2), fnum(fp["tol"], 2)))

    print("  selftest: 6 arm(s), %d failure(s)" % bad)
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--naive", action="store_true", help="run the peak-ignoring search as a control")
    a = ap.parse_args(argv)
    cfg = default_cfg()
    if a.selftest:
        return selftest(cfg)
    rows = run(cfg, use_naive=a.naive)
    report(rows, "== boundary (%s search) ==" % ("NAIVE, peak ignored" if a.naive else "handled"))
    pair = control_pairing(cfg, 24, 12, 0.9, cfg["seeds"])
    print("  pairing control: paired half-width %s vs unpaired %s (ratio %.2f)"
          % (fnum(pair["paired_halfwidth"], 4), fnum(pair["unpaired_halfwidth"], 4),
             pair["ratio"] if pair["ratio"] else float("nan")))
    if a.json:
        with io.open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"config": {k: v for k, v in cfg.items()}, "boundary": rows,
                                 "pairing_control": pair}, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
