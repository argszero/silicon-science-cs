#!/usr/bin/env python3
"""Issue #135 -- the THEORY arm: is the budget boundary alpha*(k_max) predictable
by a closed form, and does the same law serve both schemes?

P3 in v1 located the boundary by measurement.  A `theory+empirics` contribution
needs it PREDICTED, so this instrument asks the closed-form question directly:

  candidate A (the textbook design rule):  the load at which the classical MEAN
      equals the budget,  U(a) = 1/2 (1 + 1/(1-a)^2) = k   =>  a = 1 - 1/sqrt(2k-1)
  candidate B (the memoryless tail):       P(probes > k) = a^k   =>  a = level^(1/k)

Both are closed forms a designer could actually use.  The measured boundary comes
from the same definition v1 used: the load at which the fraction of unsuccessful
lookups needing MORE than k probes crosses the level.

Deterministic, standard-library only, CPU-only, no timings; ground truth by
construction (the table state is the ground truth, every probe an exact integer).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spike_v1 as V

M = 65536
ALPHAS = (0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30,
          0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.99)
SEEDS = (1000013, 2000026, 3000039)
KMAXES = V.KMAXES                     # 2, 4, 8, 16, 32, 64
LEVELS = (1e-2, 1e-3, 1e-4)


def candidates(k, level):
    return {
        "A_mean_based": V.mean_based_load(k),
        "B_memoryless": level ** (1.0 / k),
    }


def measure(scheme, family, alpha, seed):
    """One cell: the unsuccessful-search tail probabilities and their event counts."""
    hfn = V.mixer
    n = int(round(alpha * M))
    keys = V.key_family(family, n, seed)
    if scheme == "linear":
        table, _d, dist = V.build_linear(keys, M, hfn)
        probe = lambda k: V.lookup_linear(table, M, k, hfn)
    else:
        table, _d, dist = V.build_robinhood(keys, M, hfn)
        probe = lambda k: V.lookup_robinhood(table, dist, M, k, hfn)

    r = V.SplitMix64(seed ^ 0xABCDEF0123456789)
    look = []
    spent = 0
    while spent < V.PROBE_BUDGET and len(look) < 300000:
        p = probe(r.next())
        spent += p
        look.append(p)
    look.sort()
    n_look = len(look)
    ev = {}
    rate = {}
    for k in KMAXES:
        e = sum(1 for v in look if v > k)
        ev[k] = e
        rate[k] = e / n_look
    return {"scheme": scheme, "family": family, "alpha": alpha, "seed": seed,
            "n": n, "n_lookups": n_look, "events": ev, "rate": rate}


def series(cells, scheme, family, k):
    """[(alpha, mean rate over seeds, total events)] for one (scheme, family, k)."""
    grp = {}
    for c in cells:
        if c["scheme"] == scheme and c["family"] == family:
            grp.setdefault(c["alpha"], []).append(c)
    pts, ev = [], {}
    for a in sorted(grp):
        cs = grp[a]
        pts.append((a, sum(c["rate"][k] for c in cs) / len(cs)))
        ev[a] = sum(c["events"][k] for c in cs)
    return pts, ev


def exponent(cells, scheme, family, alpha):
    """Is the tail geometric IN k?  Fit log(rate) = c + s*k over the k grid for
    the cells where every rate is resolvable (>0), and return (s, log(alpha))."""
    grp = [c for c in cells if c["scheme"] == scheme and c["family"] == family
           and c["alpha"] == alpha]
    if not grp:
        return None
    xs, ys = [], []
    for k in KMAXES:
        e = sum(c["events"][k] for c in grp)
        n = sum(c["n_lookups"] for c in grp)
        if e > 0:
            xs.append(float(k))
            ys.append(math.log(e / n))
    if len(xs) < 3:
        return None
    # least squares of log(rate) on k
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    s = sxy / sxx if sxx > 0 else None
    return {"slope": s, "log_alpha": math.log(alpha), "n_points": len(xs)}


def build():
    cells = []
    for scheme in ("linear", "robinhood"):
        for family in ("uniform", "sequential"):
            for alpha in ALPHAS:
                for seed in SEEDS:
                    cells.append(measure(scheme, family, alpha, seed))
    return cells


def checks(cells):
    out = {}

    # C16 -- the measured boundary, per (scheme, family, level, k)
    C16 = {}
    for scheme in ("linear", "robinhood"):
        for family in ("uniform", "sequential"):
            for level in LEVELS:
                rows = {}
                for k in KMAXES:
                    pts, ev = series(cells, scheme, family, k)
                    cr = V.crossing(pts, level, events=ev)
                    rows[str(k)] = {"crossing": cr, "events": ev}
                C16["%s|%s|%g" % (scheme, family, level)] = rows
    out["C16_measured_boundary"] = C16

    # C17 -- the closed-form comparison
    C17 = {}
    for key, rows in C16.items():
        _, _, lvl = key.split("|")
        level = float(lvl)
        per = {}
        for k in KMAXES:
            a = rows[str(k)]["crossing"].get("alpha")
            cand = candidates(k, level)
            per[str(k)] = {
                "measured": a,
                "A_mean_based": cand["A_mean_based"],
                "B_memoryless": cand["B_memoryless"],
                "dev_A": (cand["A_mean_based"] - a) if a is not None else None,
                "dev_B": (cand["B_memoryless"] - a) if a is not None else None,
            }
        C17[key] = per
    out["C17_closed_form_comparison"] = C17

    # C19 -- a SCHEME-CALIBRATED closed form, and its out-of-sample leg.
    # The tail's decay exponent is measured from the TAIL PROBABILITIES (C18),
    # never from the boundary, so using it to predict alpha*(k) is prediction
    # rather than fit.  candidate C:  P(X > k) ~ alpha^(c*k)  =>  a = level^(1/(c k))
    C18_pre = {}
    for scheme in ("linear", "robinhood"):
        rats = []
        for alpha in (0.30, 0.50, 0.70, 0.80, 0.85, 0.90, 0.95):
            r = exponent(cells, scheme, "uniform", alpha)
            if r and r["slope"]:
                rats.append(r["slope"] / r["log_alpha"])
        C18_pre[scheme] = (sum(rats) / len(rats)) if rats else None
    C19 = {"c_by_scheme": C18_pre, "rows": {}}
    for key, rows in C16.items():
        scheme, family, lvl = key.split("|")
        level = float(lvl)
        c = C18_pre.get(scheme)
        if not c:
            continue
        per = {}
        for k in KMAXES:
            a = rows[str(k)]["crossing"].get("alpha")
            if a is None:
                per[str(k)] = {"measured": None, "C_scheme_calibrated": None,
                               "dev_C": None}
                continue
            pc = level ** (1.0 / (c * k))
            per[str(k)] = {"measured": a, "C_scheme_calibrated": pc,
                           "dev_C": pc - a}
        C19["rows"][key] = per
    out["C19_scheme_calibrated"] = C19

    # C18 -- is the tail geometric in k?  (slope vs log alpha)
    C18 = {}
    for scheme in ("linear", "robinhood"):
        for alpha in (0.30, 0.50, 0.70, 0.80, 0.85, 0.90, 0.95):
            r = exponent(cells, scheme, "uniform", alpha)
            if r:
                C18["%s|%.2f" % (scheme, alpha)] = {
                    "slope": r["slope"], "log_alpha": r["log_alpha"],
                    "ratio": (r["slope"] / r["log_alpha"]) if r["log_alpha"] else None,
                    "n_points": r["n_points"]}
    out["C18_geometric_in_k"] = C18
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
    report = {"instrument": "spike_v3", "issue": 135, "m": M,
              "alphas": list(ALPHAS), "seeds": list(SEEDS),
              "kmaxes": list(KMAXES), "levels": list(LEVELS),
              "cells": cells, "checks": checks(cells)}
    with open(out_path("spike_v3_results.json"), "w") as fh:
        fh.write(json.dumps(report, sort_keys=True, indent=1))
    return report



# ---------------------------------------------------------------- selftest
def selftest():
    """Plant battery: the closed forms are checked against independently written
    expressions, and the exponent fit is checked on a series whose exponent is
    known by construction."""
    ok, miss = [], []

    def want(name, cond):
        (ok if cond else miss).append(name)

    # candidate A is the textbook mean-based load, written out independently
    want("A_k8", abs(candidates(8, 1e-3)["A_mean_based"]
                     - (1 - 1 / (2 * 8 - 1) ** 0.5)) < 1e-15)
    # candidate B is the memoryless tail inversion
    want("B_k8", abs(candidates(8, 1e-3)["B_memoryless"] - 1e-3 ** (1 / 8)) < 1e-15)
    want("B_ge_A_is_false_at_low_k", candidates(2, 1e-3)["B_memoryless"]
         < candidates(2, 1e-3)["A_mean_based"])

    # an EXACTLY geometric tail: rate(k) = alpha^k.  The fitted slope must equal
    # log(alpha) and the ratio must be 1.0 -- the definition of geometric.
    # Build a synthetic cell set the fitter accepts (needs >0 events at >=3 k).
    # Use a large sample count so the series stays RESOLVABLE across the k grid
    # (a rate that rounds to zero at high k is skipped by the >0 filter, which is
    # why n must be big enough for the k values the fit uses).
    a = 0.5
    N = 1 << 70          # a power of two: a^k * N is then EXACTLY representable,
                         # so the recovery is limited by the fit, not by rounding.

    def synth(scheme, exponent_of_k):
        """Cells shaped exactly as measure() emits them: every cell carries the
        FULL k grid (the fitter reads every k on every cell)."""
        ev = {k: N >> exponent_of_k(k) for k in KMAXES}
        return [{"scheme": scheme, "family": "uniform", "alpha": a, "seed": i,
                 "n": 1, "n_lookups": N,
                 "events": dict(ev), "rate": {k: ev[k] / N for k in KMAXES}}
                for i in range(3)]

    cells = synth("synthetic", lambda k: k)
    r = exponent(cells, "synthetic", "uniform", a)
    want("exponent_recovers_log_alpha", r is not None and abs(r["slope"] - math.log(a)) < 1e-9)
    want("exponent_ratio_is_one", r is not None and abs(r["slope"] / r["log_alpha"] - 1.0) < 1e-9)

    # PLANT: a SUPER-geometric series (rate = alpha^(2k)) must come out at ratio
    # ~2, not ~1 -- this is the discrimination C18/C19 rest on.
    cells2 = synth("synthetic2", lambda k: 2 * k)
    r2 = exponent(cells2, "synthetic2", "uniform", a)
    want("plant_super_geometric_ratio_is_two",
         r2 is not None and abs(r2["slope"] / r2["log_alpha"] - 2.0) < 1e-6)

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
    for key in sorted(k for k in ch["C17_closed_form_comparison"]
                      if k.startswith("linear|uniform")):
        per = ch["C17_closed_form_comparison"][key]
        print("C17 %s:" % key)
        for k in ("2", "4", "8", "16", "32", "64"):
            r = per[k]
            print("   k=%-3s meas=%-8s A=%-7.4f dev_A=%-8s B=%-7.4f dev_B=%s" % (
                k, "%.4f" % r["measured"] if r["measured"] is not None else "undef",
                r["A_mean_based"],
                "%.4f" % r["dev_A"] if r["dev_A"] is not None else "undef",
                r["B_memoryless"],
                "%.4f" % r["dev_B"] if r["dev_B"] is not None else "undef"))
    c19 = ch["C19_scheme_calibrated"]
    print("C19 c by scheme (tail exponent / log alpha):", {k: round(v,3) for k,v in c19["c_by_scheme"].items()})
    for key in sorted(k for k in c19["rows"] if k.endswith("|0.001")):
        print("C19 %s:" % key)
        for k in ("4","8","16","32"):
            r = c19["rows"][key][k]
            print("   k=%-3s meas=%-8s C=%-8s dev_C=%s" % (
                k, "%.4f"%r["measured"] if r["measured"] is not None else "undef",
                "%.4f"%r["C_scheme_calibrated"] if r["C_scheme_calibrated"] is not None else "undef",
                "%.4f"%r["dev_C"] if r["dev_C"] is not None else "undef"))
    print("C18 tail-slope / log(alpha) (1.0 would be exactly geometric):")
    for k, v in sorted(ch["C18_geometric_in_k"].items()):
        print("   %-18s slope=%.3f log_a=%.3f ratio=%.3f" % (
            k, v["slope"], v["log_alpha"], v["ratio"]))
