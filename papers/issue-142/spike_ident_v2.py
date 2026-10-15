#!/usr/bin/env python3
"""Issue #142 / research v2 -- P3's PREDICTIVE HALF: the identifiability set, and its test.

BOUNDED GOAL (one goal, stated before it runs).  v0 measured a 684x separation between the two
identification routes' errors at interior against pinned cells, but never built the PREDICTOR: the
registration's P3 is that the identifiable set is *exactly the argmax set, and is predictable from
the pricing alone before any sweep is run*, with success criterion (iii) "0 disagreements over the
cell set".  This instrument builds the predictor and runs the two-sided test.

THE PREDICTOR, written out.  A cell is the deployment's own report at one price: (lam, L*) plus the
operator's declared operable range [lo, Lmax].  The rule is
    pinned   iff  L* <= lo + TOL   or   L* >= Lmax - TOL      (TOL = one lattice step),  else interior
and it reads NO ground truth: the twin of the truth is the *error* of the identification formula at
that cell, e = |J - c(tau+L*)| / c(tau+L*), which this instrument can compute only because the plant
is known.  Label and truth are therefore computed from DISJOINT inputs, and that is certified
(plant-label-is-a-function-of-the-pricing-not-the-truth): moving the declared floor moves labels while
leaving every error exactly where it was.

THE TEST, in both directions.  At a declared resolution tau (reported at 1e-3 / 1e-2 / 1e-1, so the
reading is not one threshold's opinion):
    false positive of identifiability : predicted interior  AND  e >  tau
    P3 REFUTATION                     : predicted pinned      AND  e <= tau
P3's own registered expectation is 0 of BOTH.  A control that must fire: an engineer's rule that
predicts pinning from the PRICE ALONE (lam below a threshold), which must disagree -- if it did not,
the test would be blind to the predictor's content.

Second reading, same predictor: the sweep route (a centred difference of G across the price ladder).
If the predictor really names the identifiable set, its "pinned" cells must also be the ones where the
sweep's estimate misses the point value.

Ground truth is exact by construction (v0's plant family, the delivered model's linearly interpolated
c(.)).  Nothing here is fitted.

python3 spike_ident_v2.py                (writes spike_ident_v2_results.json)
python3 spike_ident_v2.py --selftest     (plants; must all fire)
"""
import json
import os
import sys
import tempfile

import numpy as np

import spike_ident_v0 as v0
import spike_ident_v1 as v1

DELTA = v0.DELTA
TOL = DELTA + 1e-9                       # one lattice step: the classification's declared resolution
TAUS = (0.0, 2.0, 4.0, 6.0, 8.0)
TAUS_OF_RESOLUTION = (1e-3, 1e-2, 1e-1)  # the resolutions the contradiction counts are read at
BUILD = v0.BUILD


# ------------------------------------------------------------------ the predictor (pricing only)
def predict(lam, Lstar, lo, Lmax, lo_shift=0.0):
    """The pricing-only label.  Reads (lam, L*, lo, Lmax) and nothing else -- no c, no error."""
    lo = lo + lo_shift
    if Lstar <= lo + TOL or Lstar >= Lmax - TOL:
        return "pinned"
    return "interior"


def predict_by_price(lam, lo, price_cut):
    """The CONTROL: an engineer's rule -- 'a low price pins the deployment'.  Reads the price only,
    so it cannot see the visited point; it must disagree somewhere."""
    return "pinned" if lam <= price_cut else "interior"


# ------------------------------------------------------------------ the cells (price sweep)
def price_cells(c, dmax, taus=TAUS, prices=None, lo_shift=0.0):
    """One cell per (plant, tau, price): the deployment's report, the predictor's label, and the
    exact error of the identification formula at that cell."""
    prices = v0.LAM_GRID if prices is None else prices
    out = []
    for tau in taus:
        Ls, C = v1.objective_grid_fn(lambda x: v0.interp(c, dmax, x), dmax, tau)
        if Ls is None:
            continue
        lo = max(tau, 1.0)
        m = Ls >= lo - 1e-9
        Li, Ci = Ls[m], C[m]
        if len(Li) < 2:
            continue
        Lmax = float(Li[-1])
        cg = np.array([v0.interp(c, dmax, tau + L) for L in Li])
        for lam in prices:
            i = int(np.argmin(Ci + lam / Li))
            L = float(Li[i])
            ct = float(cg[i])
            if not (ct > 0):
                continue
            J = float(Ci[i]) + lam / L
            G = L * J - lam
            e = abs(J - ct) / ct
            out.append({
                "tau": tau, "lam": float(lam), "Lstar": L, "lo": lo, "Lmax": Lmax,
                "J": J, "G": G, "c_true": ct, "err": e,
                "label": predict(lam, L, lo, Lmax),
                "label_shifted_floor": predict(lam, L, lo, Lmax, lo_shift=lo_shift),
                "boundary": bool(L <= lo + TOL or L >= Lmax - TOL),
                "at_floor": bool(L <= lo + TOL), "at_ceiling": bool(L >= Lmax - TOL),
            })
    return out


def verdict(cells, tau, key="label"):
    """The two contradiction classes, at one resolution.  Empty is P3's registered expectation."""
    fp = [c for c in cells if c[key] == "interior" and c["err"] > tau]
    ref = [c for c in cells if c[key] == "pinned" and c["err"] <= tau]
    return fp, ref


def err_stat(cells, label, key="label"):
    e = sorted(c["err"] for c in cells if c[key] == label)
    if not e:
        return {"n": 0}
    a = np.array(e)
    return {"n": int(a.size), "median": float(np.median(a)), "worst": float(a.max()),
            "best": float(a.min())}


def block_fractions(cells):
    """Per (tau of the plant, not the resolution): predicted against measured pinned fraction --
    the registration's '2-12 of 22 prices' statement, read off per block."""
    out = []
    byplant = {}
    for c in cells:
        byplant.setdefault(c["tau"], []).append(c)
    for tau, cs in sorted(byplant.items()):
        n = len(cs)
        pred = sum(1 for c in cs if c["label"] == "pinned")
        meas = sum(1 for c in cs if c["boundary"])
        ctrl = sum(1 for c in cs if predict_by_price(c["lam"], c["lo"], 1.0) == "pinned")
        out.append({"tau": tau, "n_prices": n, "predicted_pinned": pred, "measured_pinned": meas,
                    "price_only_control_pinned": ctrl})
    return out


# ------------------------------------------------------------------ second reading: the sweep
def sweep_cells(cells):
    """The sweep route on the same ladder: a centred difference of G across neighbouring prices,
    its estimate against the POINT value at the middle cell, labelled by the middle cell's
    predictor label.  A pinned cell is used as a middle cell here -- the sweep can still be run
    across it, which is exactly why the predictor has to name it."""
    bytau = {}
    for c in cells:
        # GROUPED BY (plant, tau): G is a per-plant quantity, so differencing across plants would
        # compare two different objectives -- the ladder has to be one deployment's own.
        bytau.setdefault((c.get("plant", "?"), c["tau"]), []).append(c)
    out = []
    for key, cs in sorted(bytau.items()):
        tau = key[1]
        cs = sorted(cs, key=lambda z: z["Lstar"])
        for k in range(1, len(cs) - 1):
            a, m, b = cs[k - 1], cs[k], cs[k + 1]
            span = b["Lstar"] - a["Lstar"]
            if span <= 1e-12:
                continue
            slope = (b["G"] - a["G"]) / span
            out.append({"plant": key[0], "tau": tau, "label": m["label"], "lam": m["lam"],
                        "span": span, "est": slope, "point": m["c_true"],
                        "spanmean": (b["J"] - a["J"]) / span,
                        "err": abs(slope - m["c_true"]) / m["c_true"]})
    return out


# ------------------------------------------------------------------ selftest
def _fixture(pairs):
    return [{"label": p, "err": e, "lam": 1.0, "lo": 1.0, "Lstar": 1.0, "Lmax": 10.0}
            for p, e in pairs]


def selftest():
    ok, checks = 0, []

    def check(name, cond, detail=""):
        nonlocal ok
        checks.append({"plant": name, "fired": bool(cond), "detail": detail})
        if cond:
            ok += 1

    # 1. the counters can report a clean case and both contradiction classes
    cells = _fixture([("interior", 1e-9), ("pinned", 1.0)])
    fp, ref = verdict(cells, 1e-2)
    check("plant-perfect-case-has-zero-disagreements", len(fp) == 0 and len(ref) == 0,
          "fp=%d ref=%d" % (len(fp), len(ref)))

    # 2. a pinned cell that is accurate IS the registered refutation
    cells = _fixture([("pinned", 1e-9), ("pinned", 0.5)])
    fp, ref = verdict(cells, 1e-2)
    check("plant-pinned-and-accurate-is-counted-as-a-refutation", len(ref) == 1,
          "refutations=%d" % len(ref))

    # 3. and the other direction: an interior cell that is wild is a false positive
    cells = _fixture([("interior", 1.0), ("interior", 1e-9)])
    fp, ref = verdict(cells, 1e-2)
    check("plant-interior-and-wild-is-counted-as-a-false-positive", len(fp) == 1,
          "false_positives=%d" % len(fp))

    # 4. the counts are monotone in the declared resolution (a weaker resolution forgives more)
    cells = _fixture([("interior", 0.05), ("interior", 5e-4), ("pinned", 5e-3)])
    n = [len(verdict(cells, t)[0]) for t in TAUS_OF_RESOLUTION]
    # (the fixture's errors must STRADDLE the resolutions, or a constant count proves nothing)
    check("plant-contradiction-count-is-monotone-in-tau", n[0] >= n[1] >= n[2] and n[0] > n[2],
          "counts=%s (fixture 0.05/5e-4: must be 2/1/0)" % n)

    # 5. the label is exactly a function of the pricing input, NOT of the truth
    curves = v1.plants_with_curves()
    name = sorted(curves)[0]
    c, dmax = curves[name]
    base = price_cells(c, dmax)
    shifted = price_cells(c, dmax, lo_shift=5 * DELTA)
    flips = sum(1 for a, b in zip(base, shifted) if a["label"] != b["label_shifted_floor"])
    same_err = all(abs(a["err"] - b["err"]) < 1e-15 for a, b in zip(base, shifted))
    check("plant-label-is-a-function-of-the-pricing-not-the-truth", flips > 0 and same_err,
          "flips=%d, errors_identical=%s" % (flips, same_err))

    # 6. a cell within one lattice step of the declared floor is labelled pinned
    check("plant-within-one-step-of-the-floor-is-pinned",
          predict(1.0, 1.0 + DELTA / 2.0, 1.0, 10.0) == "pinned")
    check("plant-well-inside-is-interior", predict(1.0, 5.0, 1.0, 10.0) == "interior")

    # 7. the CONTROL predictor (price alone) must disagree -- the test is not blind
    ctrl_pinned = sum(1 for x in base if predict_by_price(x["lam"], x["lo"], 1.0) == "pinned")
    ctrl_label = [dict(x, label=predict_by_price(x["lam"], x["lo"], 1.0)) for x in base]
    fp, ref = verdict(ctrl_label, 1e-2)
    check("plant-price-only-control-disagrees", (len(fp) + len(ref)) > 0,
          "control pinned=%d, disagreements=%d" % (ctrl_pinned, len(fp) + len(ref)))

    # 8. the pinned class really is the worse class for the identification formula
    s_int, s_pin = err_stat(base, "interior"), err_stat(base, "pinned")
    check("plant-pinned-class-is-worse-than-interior",
          s_pin["n"] > 0 and s_int["n"] > 0 and s_pin["median"] > 100 * s_int["median"],
          "median interior=%.3g pinned=%.3g" % (s_int["median"], s_pin["median"]))

    # 9. the sweep reading is computed and carries both labels
    sw = sweep_cells(base)
    check("plant-sweep-reading-covers-both-labels",
          any(s["label"] == "interior" for s in sw) and any(s["label"] == "pinned" for s in sw),
          "n=%d" % len(sw))

    # 10. bookkeeping: every cell is exactly one label, and the boundary flag agrees with it
    check("plant-every-cell-has-exactly-one-label",
          all((x["label"] == "pinned") == x["boundary"] for x in base))

    print(json.dumps({"plants": checks, "passed": ok, "total": len(checks)}, indent=2))
    return 0 if ok == len(checks) else 1


# ------------------------------------------------------------------ main
def measure_all():
    curves = v1.plants_with_curves()
    all_cells, per_plant = [], {}
    for name, (c, dmax) in sorted(curves.items()):
        cs = price_cells(c, dmax)
        per_plant[name] = block_fractions(cs)
        for x in cs:
            x["plant"] = name
        all_cells.extend(cs)
    sw = sweep_cells(all_cells)

    res = {"build": BUILD,
           "goal": "P3 (predictive half) -- the pricing-only identifiability predictor, and 0 disagreements",
           "rule": "pinned iff L* <= lo + one lattice step, or L* >= Lmax - one lattice step",
           "resolution": TOL,
           "totals": {"cells": len(all_cells),
                      "interior": sum(1 for x in all_cells if x["label"] == "interior"),
                      "pinned": sum(1 for x in all_cells if x["label"] == "pinned"),
                      "at_floor": sum(1 for x in all_cells if x["at_floor"]),
                      "at_ceiling": sum(1 for x in all_cells if x["at_ceiling"]),
                      "blocks": sum(len(v) for v in per_plant.values())},
           "error_by_label": {"interior": err_stat(all_cells, "interior"),
                              "pinned": err_stat(all_cells, "pinned")},
           "contradictions": {}, "price_only_control": {}, "per_plant": per_plant,
           "sweep": {"n": len(sw),
                     "err_vs_point_by_label": {
                         "interior": err_stat(sw, "interior"),
                         "pinned": err_stat(sw, "pinned")}}}
    for t in TAUS_OF_RESOLUTION:
        fp, ref = verdict(all_cells, t)
        res["contradictions"]["%g" % t] = {
            "false_positive_of_identifiability": len(fp),
            "p3_refutation": len(ref),
            "fp_worst_err": max([c["err"] for c in fp]) if fp else None,
            "ref_worst_err": max([c["err"] for c in ref]) if ref else None}
        ctrl = [dict(x, label=predict_by_price(x["lam"], x["lo"], 1.0)) for x in all_cells]
        fpc, refc = verdict(ctrl, t)
        res["price_only_control"]["%g" % t] = {"disagreements": len(fpc) + len(refc),
                                               "pinned_labelled": sum(1 for x in ctrl if x["label"] == "pinned")}
    res["boundary_agreement"] = {"cells": len(all_cells),
                                 "label_matches_boundary": sum(
                                     1 for x in all_cells if (x["label"] == "pinned") == x["boundary"])}
    # --- the two readings the P3 test is decided on -------------------------------------------
    # (a) SOUNDNESS: every cell the predictor calls identifiable really is -- read at the paper's
    #     own resolution 1e-2 (0 false positives), and against the interior class's own worst error.
    # (b) SET EQUALITY: the registered criterion (iii).  A pinned cell at or below the interior
    #     class's worst error has an interior cell's accuracy, and the registration says outright
    #     that such a cell refutes P3.  The line is the interior class's own worst error -- a
    #     quantity this data supplies -- so no threshold of ours decides the verdict.
    int_worst = res["error_by_label"]["interior"]["worst"]
    bad = [x for x in all_cells if x["label"] == "pinned" and x["err"] <= int_worst]
    res["soundness"] = {
        "reading": "predicted interior => the identification formula is accurate there",
        "interior_worst_err": int_worst,
        "predicted_interior_cells": res["totals"]["interior"],
        "interior_cells_above_1e-2": sum(1 for x in all_cells
                                         if x["label"] == "interior" and x["err"] > 1e-2),
    }
    res["set_equality"] = {
        "reading": "registered criterion (iii): pinned => not identifiable, 0 disagreements",
        "threshold_free_line": int_worst,
        "pinned_cells_at_or_below": len(bad),
        "pinned_cells_total": res["totals"]["pinned"],
        "examples": [{"plant": x["plant"], "tau": x["tau"], "lam": x["lam"], "Lstar": x["Lstar"],
                      "at_floor": int(x["at_floor"]), "at_ceiling": int(x["at_ceiling"]),
                      "err": x["err"]} for x in sorted(bad, key=lambda z: z["err"])],
    }
    res["boundary_asymmetry"] = {}
    for k in ("at_floor", "at_ceiling"):
        sub = [x for x in all_cells if x[k]]
        e = np.array([x["err"] for x in sub]) if sub else np.array([float("inf")])
        res["boundary_asymmetry"][k] = {
            "n": len(sub), "median": float(np.median(e)), "best": float(e.min()),
            "at_or_below_interior_worst": int((e <= int_worst).sum())}
    return res


def write_json(path, obj):
    """Stage to a temp file and os.replace: a truncate-then-fail write is not atomic."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-v2-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
    os.chmod(tmp, 0o644)          # mkstemp is 0600; the artefact is meant to be read
    os.replace(tmp, path)


def main():
    R = measure_all()
    slim = {k: R[k] for k in ("build", "totals", "error_by_label", "contradictions",
                              "price_only_control", "boundary_agreement", "soundness",
                              "set_equality", "boundary_asymmetry", "sweep")}
    print(json.dumps(slim, indent=2, sort_keys=True))
    write_json("spike_ident_v2_results.json", R)
    return R


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
