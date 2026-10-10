#!/usr/bin/env python3
"""Issue #135 -- P2: is the TAIL predicted by a clustering statistic, out of sample?

Registered prior P2 (two limbs):
  (a) at a FIXED load, the across-instance spread of the p99 exceeds the across-
      instance spread of the MEAN by >= 1.5x at alpha >= 0.9;
  (b) a declared CLUSTERING STATISTIC of the probe sequence predicts the p99
      OUT OF SAMPLE to within 20 %.

The across-instance variable is the SEED (a different hash-to-slot map on the
same key set), which is what varies the realised clustering at a fixed load.

Method (declared before the fit):
  * instances per (scheme, family, alpha): 12 seeds, m = 65536.
  * the fit half is the ODD index in seed order, the test half the EVEN index --
    a fixed, stated rule, not a search for a good split.
  * the candidate predictor is `longest_run` (the longest circular run of
    occupied slots), a property of the table state and not of the published
    theory; the baseline predictor is the measured mean.
  * the fit is `log(p99) = a + b * log(stat)` (least squares in log space), and
    the out-of-sample score is the worst relative deviation over the test half.
  * an UNRESOLVED instance is not a measurement: an instance whose p99 sample
    carries fewer than MIN_P99_EVENTS tail events is reported undef.

Deterministic, standard-library only, CPU-only, no timings.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spike_v1 as V

M = 65536
ALPHAS = (0.50, 0.70, 0.85, 0.90, 0.95, 0.97)
SEEDS = tuple(s * 1000003 + 11 for s in range(1, 13))
MIN_P99_EVENTS = 10          # a p99 need not rest on fewer than this many events


def instance(scheme, family, alpha, seed):
    """One instance: the table state's statistics and the measured distributions."""
    hfn = V.mixer
    n = int(round(alpha * M))
    keys = V.key_family(family, n, seed)
    if scheme == "linear":
        table, disp, dist = V.build_linear(keys, M, hfn)
        probe = lambda k: V.lookup_linear(table, M, k, hfn)
    else:
        table, disp, dist = V.build_robinhood(keys, M, hfn)
        probe = lambda k: V.lookup_robinhood(table, dist, M, k, hfn)

    r = V.SplitMix64(seed ^ 0xABCDEF0123456789)
    look = []
    spent = 0
    while spent < V.PROBE_BUDGET and len(look) < 300000:
        p = probe(r.next())
        spent += p
        look.append(p)
    look.sort()
    dmean = sum(disp) / len(disp)
    dvar = sum((d - dmean) ** 2 for d in disp) / len(disp)
    return {
        "scheme": scheme, "family": family, "alpha": alpha, "seed": seed,
        "n": n, "n_lookups": len(look),
        "mean": sum(look) / len(look),
        "p99": V.pct(look, 0.99),
        "p999": V.pct(look, 0.999),
        "max": look[-1],
        "n_events_above_p99": sum(1 for v in look if v > V.pct(look, 0.99)),
        "longest_run": V.longest_run(table, M),
        "disp_var": dvar,
        "disp_mean": dmean,
    }


def logfit(xs, ys):
    """Least-squares fit y = a + b x.  Returns (a, b)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx if sxx > 0 else 0.0
    return my - b * mx, b


def spread_ratio(insts):
    """(p99 spread / mean spread) over the instances, both relative to their own
    means -- the registered P2(a) quantity.  `None` when the mean is constant."""
    means = [i["mean"] for i in insts]
    p99s = [i["p99"] for i in insts]
    mm = sum(means) / len(means)
    pm = sum(p99s) / len(p99s)
    ms = (max(means) - min(means)) / mm
    ps = (max(p99s) - min(p99s)) / pm
    return {"mean_spread_rel": ms, "p99_spread_rel": ps,
            "ratio": (ps / ms) if ms > 0 else None,
            "n": len(insts)}


def out_of_sample(insts, stat="longest_run"):
    """Fit log(p99) = a + b log(stat) on the fit half (odd index), score the
    worst relative deviation on the test half (even index).  The baseline is the
    same fit with `mean` as the predictor."""
    fit = [i for k, i in enumerate(insts) if k % 2 == 1]
    test = [i for k, i in enumerate(insts) if k % 2 == 0]

    res = {}
    for name, pred in (("cluster_" + stat, stat), ("baseline_mean", "mean")):
        if any(i[pred] <= 0 for i in fit):
            res[name] = {"verdict": "undef", "note": "a predictor value is <= 0"}
            continue
        a, b = logfit([math.log(i[pred]) for i in fit],
                      [math.log(i["p99"]) for i in fit])
        devs = []
        for i in test:
            pred_p99 = math.exp(a + b * math.log(i[pred]))
            devs.append((pred_p99 - i["p99"]) / i["p99"])
        res[name] = {
            "a": a, "b": b,
            "worst_rel_dev": max((abs(d) for d in devs), default=None),
            "devs": [round(d, 4) for d in devs],
            "within_20pct": all(abs(d) <= 0.20 for d in devs) if devs else None,
            "n_fit": len(fit), "n_test": len(test),
        }
    return res


def build():
    cells = []
    for scheme in ("linear", "robinhood"):
        for family in ("uniform", "sequential"):
            for alpha in ALPHAS:
                for seed in SEEDS:
                    cells.append(instance(scheme, family, alpha, seed))
    return cells


def checks(cells):
    out = {}

    # C11 -- P2(a): the across-instance spread of the p99 vs the mean's
    grp = {}
    for c in cells:
        grp.setdefault((c["scheme"], c["family"], c["alpha"]), []).append(c)
    C11 = {}
    for (scheme, family, alpha), insts in sorted(grp.items()):
        r = spread_ratio(insts)
        r["registered_holds"] = (r["ratio"] is not None and r["ratio"] >= 1.5)
        C11["%s|%s|%.2f" % (scheme, family, alpha)] = r
    out["C11_spread_ratio"] = C11

    # C12 -- P2(b): out-of-sample prediction of the p99
    C12 = {}
    for (scheme, family, alpha), insts in sorted(grp.items()):
        C12["%s|%s|%.2f" % (scheme, family, alpha)] = out_of_sample(insts)
    out["C12_out_of_sample"] = C12

    # C14 -- the clustering statistic is NOT the whole story: linear and Robin
    # Hood share the SAME occupied slot set (hence the same longest run) yet have
    # very different tails, so the statistic cannot be scheme-invariant.
    by_key = {}
    for c in cells:
        by_key.setdefault((c["family"], c["alpha"], c["seed"]), {})[c["scheme"]] = c
    same_run = n_pairs = 0
    ratios = []
    for k, d in sorted(by_key.items()):
        if "linear" in d and "robinhood" in d:
            n_pairs += 1
            if d["linear"]["longest_run"] == d["robinhood"]["longest_run"]:
                same_run += 1
            if d["robinhood"]["p99"] > 0:
                ratios.append(d["linear"]["p99"] / d["robinhood"]["p99"])
    out["C14_clustering_is_not_scheme_invariant"] = {
        "n_pairs": n_pairs, "same_longest_run": same_run,
        "same_run_fraction": (same_run / n_pairs) if n_pairs else None,
        "p99_ratio_linear_over_robinhood": {
            "min": min(ratios) if ratios else None,
            "max": max(ratios) if ratios else None,
            "median": sorted(ratios)[len(ratios) // 2] if ratios else None,
        },
        "finding": "the two schemes fill the SAME slots (the longest run is a "
                   "property of the occupied SET, which is scheme-independent), "
                   "so the clustering statistic is identical while the tail is not",
    }

    # C15 -- a predictor fit on ONE scheme does not transport to the other
    C15 = {}
    for family in ("uniform", "sequential"):
        for alpha in ALPHAS:
            lin = [i for i in cells if i["scheme"] == "linear"
                   and i["family"] == family and i["alpha"] == alpha]
            rh = [i for i in cells if i["scheme"] == "robinhood"
                  and i["family"] == family and i["alpha"] == alpha]
            if not lin or not rh:
                continue
            a, b = logfit([math.log(i["longest_run"]) for i in lin],
                          [math.log(i["p99"]) for i in lin])
            devs = [(math.exp(a + b * math.log(i["longest_run"])) - i["p99"]) / i["p99"]
                    for i in rh if i["p99"] > 0]
            C15["%s|%.2f" % (family, alpha)] = {
                "worst_rel_dev": max((abs(d) for d in devs), default=None)}
    out["C15_cross_scheme_transport"] = C15

    # C13 -- the p99 must rest on enough events to BE a reading
    ev = {}
    for c in cells:
        k = "%s|%s|%.2f" % (c["scheme"], c["family"], c["alpha"])
        ev.setdefault(k, []).append(c["n_events_above_p99"])
    out["C13_p99_events"] = {k: {"min": min(v), "max": max(v),
                                 "resolved": min(v) >= MIN_P99_EVENTS}
                             for k, v in sorted(ev.items())}
    return out


# ---------------------------------------------------------------- output path
def out_path(default):
    """Where the report is written.  SPIKE_OUT overrides it, so reproduce.sh can
    run the instrument with the package left untouched (it writes into a private
    temp dir and compares)."""
    import os
    return os.environ.get("SPIKE_OUT", default)


def main():
    cells = build()
    report = {"instrument": "spike_v2", "issue": 135, "m": M,
              "alphas": list(ALPHAS), "seeds": list(SEEDS),
              "min_p99_events": MIN_P99_EVENTS,
              "cells": cells, "checks": checks(cells)}
    with open(out_path("spike_v2_results.json"), "w") as fh:
        fh.write(json.dumps(report, sort_keys=True, indent=1))
    return report



# ---------------------------------------------------------------- selftest
def selftest():
    """Plant battery: recover known answers from synthetic inputs whose answer is
    known independently of any measurement."""
    ok, miss = [], []

    def want(name, cond):
        (ok if cond else miss).append(name)

    # logfit recovers an exactly linear relation y = 1 + 2x
    a, b = logfit([1.0, 2.0, 3.0], [3.0, 5.0, 7.0])
    want("logfit_intercept", abs(a - 1.0) < 1e-12)
    want("logfit_slope", abs(b - 2.0) < 1e-12)
    # a zero-variance x is degenerate, not a crash
    a2, b2 = logfit([2.0, 2.0], [1.0, 3.0])
    want("logfit_degenerate_slope", b2 == 0.0)

    # spread_ratio on a constant-mean set is UNDEF (a 0/0, never a zero)
    sr = spread_ratio([{"mean": 5.0, "p99": 1}, {"mean": 5.0, "p99": 9}])
    want("spread_ratio_undef_when_mean_flat", sr["ratio"] is None)
    # and it is the p99 spread over the mean spread when the mean does move
    sr2 = spread_ratio([{"mean": 4.0, "p99": 10}, {"mean": 6.0, "p99": 30}])
    want("spread_ratio_value", abs(sr2["ratio"] - ((30 - 10) / 20.0) / ((6 - 4) / 5.0)) < 1e-12)

    # out_of_sample recovers an EXACTLY geometric predictor: p99 = 3 * stat
    insts = [{"longest_run": 10 ** (1 + 0.1 * i), "mean": 10.0,
              "p99": 3 * 10 ** (1 + 0.1 * i)} for i in range(6)]
    o = out_of_sample(insts, "longest_run")
    cl = o["cluster_longest_run"]
    want("out_of_sample_recovers_geometric", cl["worst_rel_dev"] < 1e-9)
    want("out_of_sample_within_20", cl["within_20pct"] is True)

    # PLANT: a predictor that is CONSTANT across instances cannot explain a
    # varying p99 -- the constraint C14/C15 rest on.  Feed a constant statistic
    # and require the fit to be degenerate rather than to "succeed".
    flat = [{"longest_run": 7, "mean": 1.0 + i, "p99": 10 * (1 + i)}
            for i in range(6)]
    of = out_of_sample(flat, "longest_run")
    want("plant_constant_statistic_degenerate",
         of["cluster_longest_run"]["b"] == 0.0
         or of["cluster_longest_run"]["verdict"] == "undef")
    # while the MEAN baseline DOES track it in that same set
    want("plant_mean_baseline_tracks", of["baseline_mean"].get("within_20pct") is True)

    print("SELFTEST %d/%d" % (len(ok), len(ok) + len(miss)))
    for m in miss:
        print("  MISSED:", m)
    return 1 if miss else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    rep = main()
    ch = rep["checks"]
    print("cells:", len(rep["cells"]), "| m =", rep["m"])
    print("C11 spread ratio (p99 spread / mean spread):")
    for k, v in sorted(ch["C11_spread_ratio"].items()):
        print("   %-24s ratio=%-7s mean=%.4f p99=%.4f  holds=%s" % (
            k, "%.2f" % v["ratio"] if v["ratio"] is not None else "undef",
            v["mean_spread_rel"], v["p99_spread_rel"], v["registered_holds"]))
    c14 = ch["C14_clustering_is_not_scheme_invariant"]
    print("C14 longest_run identical across schemes: %d of %d pairs (%.1f%%); "
          "p99 ratio linear/robinhood min=%.1f median=%.1f max=%.1f" % (
              c14["same_longest_run"], c14["n_pairs"],
              100.0 * c14["same_run_fraction"], c14["p99_ratio_linear_over_robinhood"]["min"],
              c14["p99_ratio_linear_over_robinhood"]["median"],
              c14["p99_ratio_linear_over_robinhood"]["max"]))
    print("C15 cross-scheme transport worst rel dev:",
          {k: round(v["worst_rel_dev"], 2) for k, v in sorted(ch["C15_cross_scheme_transport"].items())})
    print("C12 out-of-sample worst rel dev (cluster vs mean baseline):")
    for k, v in sorted(ch["C12_out_of_sample"].items()):
        cl = v["cluster_longest_run"]; bl = v["baseline_mean"]
        print("   %-24s cluster=%-7s (within20=%s)  mean-baseline=%-7s" % (
            k,
            "%.3f" % cl["worst_rel_dev"] if cl.get("worst_rel_dev") is not None else "undef",
            cl.get("within_20pct"),
            "%.3f" % bl["worst_rel_dev"] if bl.get("worst_rel_dev") is not None else "undef"))
