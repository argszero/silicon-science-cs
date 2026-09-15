#!/usr/bin/env python3
"""
issue #44 -- instrument_v2.py
"Where does the budget stop paying? The insensitivity region and its boundary"

REGISTERED CRITERION (b) -- quoted from the registration:
    "(b) the insensitivity region, defined as a detection-rate slope in log k
     below 0.01, is non-empty and its measured boundary matches the predicted
     band width within plus or minus 20 percent"

OPERATIONALISATION (fixed here, before the run, and reported with the result)
  * slope in log k, at a node of divergence (delta, sigma), over the budget set
    K = {8, 32, 128, 512}:
        S(delta) = [ power(delta, k=512) - power(delta, k=8) ] / ln(512/8)
    A secant over the same k set is used for the prediction AND the measurement,
    so the comparison is like with like; the analytic tangent slope is reported
    separately as a consistency check.
  * the SENSITIVE band is { delta > 0 : S(delta) >= 0.01 }; its width is
    W = delta_hi - delta_lo.  The INSENSITIVITY region is the complement, and it
    is non-empty on the low side (S -> 0 as delta -> 0) and on the high side.
  * PREDICTED band: S from the construct power = Phi(u),
    u = (sqrt(k)*delta - c_alpha)/sigma, no fitted parameter.
  * MEASURED band: S from Monte Carlo detection rates on the same k set,
    5 disjoint streams per cell, mean and sd recorded per cell.
  * criterion (b) is MET iff, for every sigma tested, the band is non-empty
    under both the prediction and the measurement, and
        |W_meas - W_pred| / W_pred <= 0.20.

WHY THE SWEEP IS AFFORDABLE (an exact identity, stated so it can be checked)
  For a Gaussian node the sample mean of k draws is exactly N(delta, sigma/sqrt(k)),
  so one draw per trial estimates the same rejection probability as k raw draws.
  The identity is CHECKED, not assumed: the slow path (k raw draws) is re-run at
  spot cells and must agree with the fast path within Monte-Carlo error.

CONTROLS (each must be able to fail -- see verify_v2.py)
  K1 null: at delta = 0 (a location-preserving node) the measured rate must sit at
     alpha = 0.05 for every k, so the measured slope there is ~0 -- the low-side
     insensitivity region is non-empty by construction of the test.
  K2 fast/slow path agreement.
  K3 mutation control: the criterion is re-evaluated against a DELIBERATELY WRONG
     predicted width (+/- 30 %) and must then report UNMET.  A criterion that
     cannot fail is decoration.

Pure stdlib. Deterministic: no clock, no entropy beyond seeded streams, and the
artefact carries no timing field (the R241 lesson -- a wall-clock field in a
sha-pinned artefact is a cross-machine hash failure waiting to happen).
"""

import json
import math
import os
import random
import statistics
import sys

# ---------------------------------------------------------------- special funcs
def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def phi_inv(p):
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


ALPHA = 0.05
C_ALPHA = phi_inv(1.0 - ALPHA)

K_BAND = [8, 32, 128, 512]
LOG_SPAN = math.log(K_BAND[-1]) - math.log(K_BAND[0])
SLOPE_CUT = 0.01          # the registered threshold
N_REFINE = 12             # bisection steps on the measured secant, per edge
REFINE_MIN = 0.002        # stop refining a bracket narrower than this
TOL = 0.20                # the registered tolerance on the width

N_MC = 8000               # trials per (sigma, delta, k, stream)
N_STREAMS = 5             # disjoint streams -- registered criterion (d)
N_GRID = 81               # delta grid points for the measured band


# ---------------------------------------------------------------- the construct
def predicted_power(k, delta, sigma):
    return phi((math.sqrt(k) * delta - C_ALPHA) / sigma)


def predicted_secant(delta, sigma):
    return (predicted_power(K_BAND[-1], delta, sigma)
            - predicted_power(K_BAND[0], delta, sigma)) / LOG_SPAN


def predicted_tangent(k, delta, sigma):
    """d power / d ln k exactly, from the construct."""
    u = (math.sqrt(k) * delta - C_ALPHA) / sigma
    return 0.5 * math.exp(-0.5 * u * u) / math.sqrt(2.0 * math.pi) \
        * (math.sqrt(k) * delta / sigma)


def band_edges(f, hi_max):
    """The two crossings of f with SLOPE_CUT on (0, hi_max], by bisection.

    f is a hump: ~0 at delta=0, peaks above SLOPE_CUT, decays to ~0.  Returns
    (lo, hi) or None if the hump never reaches SLOPE_CUT."""
    # sample coarsely, then refine the bracketing windows
    n = 4000
    prev_d, prev_f = 0.0, f(0.0)
    brackets = []
    for i in range(1, n + 1):
        d = hi_max * i / n
        fv = f(d)
        if (prev_f - SLOPE_CUT) * (fv - SLOPE_CUT) < 0:
            brackets.append((prev_d, d, prev_f, fv))
        prev_d, prev_f = d, fv
    if len(brackets) < 2:
        return None
    (a, b, fa, fb) = brackets[0]
    for _ in range(80):
        m = 0.5 * (a + b)
        fm = f(m) - SLOPE_CUT
        if (fa - SLOPE_CUT) * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    lo = 0.5 * (a + b)
    (a, b, fa, fb) = brackets[-1]
    for _ in range(80):
        m = 0.5 * (a + b)
        fm = f(m) - SLOPE_CUT
        if (fa - SLOPE_CUT) * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    hi = 0.5 * (a + b)
    return (lo, hi)


def predicted_band(sigma):
    return band_edges(lambda d: predicted_secant(d, sigma), 20.0 * sigma)


# ---------------------------------------------------------------- Monte-Carlo
def seed_for(*parts):
    """Deterministic across processes: strings are hashed by ord(), never by
    Python's randomised str hash."""
    h = 17
    for p in parts:
        if isinstance(p, str):
            v = 0
            for i, ch in enumerate(p):
                v = (v * 131 + ord(ch)) & 0x7FFFFFFF
        else:
            v = int(round(float(p) * 1000))
        h = (h * 1000003 + v) & 0x7FFFFFFF
    return h


def mc_rate_fast(k, delta, sigma, n_mc, seed):
    """Exact mean distribution: N(delta, sigma/sqrt(k)) -- one draw per trial."""
    r = random.Random(seed)
    mu = delta
    sd = sigma / math.sqrt(k)
    tau = C_ALPHA / math.sqrt(k)
    rej = 0
    for _ in range(n_mc):
        if r.gauss(mu, sd) > tau:
            rej += 1
    return rej / float(n_mc)


def mc_rate_slow(k, delta, sigma, n_mc, seed):
    """The path the identity claims is equivalent: k raw draws per trial."""
    r = random.Random(seed)
    tau = C_ALPHA / math.sqrt(k)
    rej = 0
    for _ in range(n_mc):
        s = 0.0
        for _ in range(k):
            s += r.gauss(delta, sigma)
        if (s / k) > tau:
            rej += 1
    return rej / float(n_mc)


def streams(fn, k, delta, sigma, tag):
    vals = [fn(k, delta, sigma, N_MC, seed_for(tag, k, delta, sigma, i))
            for i in range(N_STREAMS)]
    return {"mean": statistics.fmean(vals),
            "sd": statistics.stdev(vals),
            "per_stream": vals}


def measured_secant(delta, sigma, tag="band"):
    """S from Monte Carlo on the same k set as the prediction, with its own SE.

    se_slope is the standard error of the secant estimate: the two k-rates are
    estimated on disjoint streams, so their errors add in quadrature before the
    division by the log-span."""
    hi = streams(mc_rate_fast, K_BAND[-1], delta, sigma, tag)
    lo = streams(mc_rate_fast, K_BAND[0], delta, sigma, tag)
    se = math.sqrt(hi["sd"] ** 2 / N_STREAMS + lo["sd"] ** 2 / N_STREAMS) / LOG_SPAN
    return {"slope": (hi["mean"] - lo["mean"]) / LOG_SPAN, "se_slope": se,
            "sd_hi": hi["sd"], "sd_lo": lo["sd"],
            "p_lo": lo["mean"], "p_hi": hi["mean"]}


def measured_band(sigma, delta_max, tag="band"):
    """Grid + linear interpolation; returns the two crossings and the grid step."""
    step = delta_max / N_GRID
    pts = []
    for i in range(N_GRID + 1):
        d = step * i
        ms = measured_secant(d, sigma, tag)
        pts.append((d, ms["slope"], ms["se_slope"]))
    brackets = []
    for i in range(1, len(pts)):
        (da, fa, sa), (db, fb, sb) = pts[i - 1], pts[i]
        if (fa - SLOPE_CUT) * (fb - SLOPE_CUT) < 0:
            brackets.append((da, fa, db, fb, sa, sb))
    if len(brackets) < 2:
        return {"ok": False, "grid_step": step, "n_brackets": len(brackets)}
    edges = []
    for (a, fa, b, fb, sa, sb) in (brackets[0], brackets[-1]):
        x = a + (b - a) * (SLOPE_CUT - fa) / (fb - fa)
        # resolution of this edge: the MC noise of the secant, divided by the
        # local slope of the secant in delta (taken as the bracket's own slope)
        local = abs((fb - fa) / (b - a)) if b != a else float("inf")
        noise = math.sqrt(sa ** 2 + sb ** 2)
        edges.append({"delta": x, "bracket": [a, b],
                      "se_slope_bracket": noise,
                      "local_dS_ddelta": local,
                      "delta_resolution": (noise / local) if local else None})
    # Refine each crossing by bisection ON THE MEASURED SECANT, so that the grid's
    # linear interpolation bias (a property of the instrument, not of the construct)
    # is separated from a genuine discrepancy.  Reported alongside the coarse value:
    # a coarse-grid artefact must not be presented as evidence about the theory.
    for e in edges:
        a, b = e["bracket"]
        for _ in range(N_REFINE):
            if (b - a) <= REFINE_MIN:
                break
            m = 0.5 * (a + b)
            fa = measured_secant(a, sigma, tag)["slope"] - SLOPE_CUT
            fm = measured_secant(m, sigma, tag)["slope"] - SLOPE_CUT
            if fa * fm <= 0:
                b = m
            else:
                a = m
        e["delta_refined"] = 0.5 * (a + b)
        e["bracket_width_after_refine"] = b - a
    lo, hi = edges[0]["delta"], edges[1]["delta"]
    rlo, rhi = edges[0]["delta_refined"], edges[1]["delta_refined"]
    return {"ok": True, "delta_lo": lo, "delta_hi": hi, "width": hi - lo,
            "grid_step": step, "n_brackets": len(brackets),
            "coarse_points": len(pts),
            "edge_lo": edges[0], "edge_hi": edges[1],
            "delta_lo_refined": rlo, "delta_hi_refined": rhi,
            "width_refined": rhi - rlo}


# ---------------------------------------------------------------- run
SIGMAS = [0.5, 1.0, 2.0]
SPOT_SLOW = [(8, 0.30, 1.0), (32, 0.60, 1.0), (128, 0.20, 2.0)]


def run():
    out = {"alpha": ALPHA, "c_alpha": C_ALPHA, "k_band": K_BAND,
           "slope_cut": SLOPE_CUT, "tol": TOL, "n_mc": N_MC,
           "n_streams": N_STREAMS, "n_grid": N_GRID, "sigmas": SIGMAS}

    # ---- 1. predicted bands
    preds = {}
    for s in SIGMAS:
        ph = predicted_band(s)
        lo, hi = ph
        preds[repr(s)] = {"delta_lo": lo, "delta_hi": hi, "width": hi - lo,
                          "peak_slope": max(predicted_secant(hi * i / 1000.0, s)
                                            for i in range(1001))}
    out["predicted_bands"] = preds

    # ---- 2. the band law at fixed sigma: width * sqrt(k) is constant (tangent def.)
    law = []
    for s in SIGMAS:
        for k in K_BAND:
            e = band_edges(lambda d, k=k, s=s: predicted_tangent(k, d, s),
                           20.0 * s / math.sqrt(k))
            law.append({"sigma": s, "k": k, "delta_lo": e[0], "delta_hi": e[1],
                        "width": e[1] - e[0],
                        "width_times_sqrt_k_over_sigma": (e[1] - e[0]) * math.sqrt(k) / s})
    out["band_law_tangent"] = law

    # ---- 3. measured bands, with the sweep range set from the prediction
    meas = {}
    for s in SIGMAS:
        pmax = preds[repr(s)]["delta_hi"] * 2.0
        mb = measured_band(s, pmax)
        pm = preds[repr(s)]
        if mb["ok"]:
            mb["width_pred"] = pm["width"]
            mb["width_rel_err"] = (mb["width"] - pm["width"]) / pm["width"]
            mb["delta_lo_rel_err"] = (mb["delta_lo"] - pm["delta_lo"]) / pm["delta_lo"]
            mb["delta_hi_rel_err"] = (mb["delta_hi"] - pm["delta_hi"]) / pm["delta_hi"]
            mb["delta_lo_abs_err"] = mb["delta_lo"] - pm["delta_lo"]
            mb["delta_hi_abs_err"] = mb["delta_hi"] - pm["delta_hi"]
            mb["delta_lo_abs_err_over_width"] = mb["delta_lo_abs_err"] / pm["width"]
            mb["delta_hi_abs_err_over_width"] = mb["delta_hi_abs_err"] / pm["width"]
            mb["delta_lo_rel_err_over_grid_step"] = mb["delta_lo_abs_err"] / mb["grid_step"]
            mb["delta_hi_rel_err_over_grid_step"] = mb["delta_hi_abs_err"] / mb["grid_step"]
            mb["width_rel_err_refined"] = (mb["width_refined"] - pm["width"]) / pm["width"]
            mb["delta_lo_rel_err_refined"] = ((mb["delta_lo_refined"] - pm["delta_lo"])
                                              / pm["delta_lo"])
            mb["delta_hi_rel_err_refined"] = ((mb["delta_hi_refined"] - pm["delta_hi"])
                                              / pm["delta_hi"])
            mb["delta_lo_abs_err_refined"] = mb["delta_lo_refined"] - pm["delta_lo"]
            mb["delta_hi_abs_err_refined"] = mb["delta_hi_refined"] - pm["delta_hi"]
        mb["sweep_delta_max"] = pmax
        if mb["ok"] and mb.get("coarse_points"):
            pts = [measured_secant(pmax * i / N_GRID, s, "band")["slope"]
                   for i in range(N_GRID + 1)]
            mb["n_grid_insensitive_low"] = sum(1 for i, v in enumerate(pts)
                                               if v < SLOPE_CUT and pmax * i / N_GRID < mb["delta_lo"])
            mb["n_grid_insensitive_high"] = sum(1 for i, v in enumerate(pts)
                                                if v < SLOPE_CUT and pmax * i / N_GRID > mb["delta_hi"])
            mb["insensitivity_region_nonempty"] = bool(mb["n_grid_insensitive_low"] > 0
                                                       and mb["n_grid_insensitive_high"] > 0)
        meas[repr(s)] = mb
    out["measured_bands"] = meas

    # ---- 4. K1: a location-preserving node, and the low-side insensitivity region
    # The construct's own prediction at delta = 0 is Phi(-c_alpha/sigma) -- which is
    # alpha exactly at sigma = 1 and NOT alpha elsewhere, because the threshold is
    # calibrated on a standardised honest node of spread 1.  Both statements are
    # checked: the measured rate against Phi(-c/sigma), and the special case
    # sigma = 1 against alpha itself.
    null = []
    for s in SIGMAS:
        for k in K_BAND:
            st = streams(mc_rate_fast, k, 0.0, s, "null")
            pred = phi(-C_ALPHA / s)
            se = st["sd"] / math.sqrt(N_STREAMS)
            null.append({"sigma": s, "k": k, "mean": st["mean"], "sd": st["sd"],
                         "se": se, "predicted": pred,
                         "abs_err": abs(st["mean"] - pred),
                         "ok_vs_construct": abs(st["mean"] - pred) <= 4.0 * se + 0.005,
                         "per_stream": st["per_stream"],
                         "ok_vs_alpha": (abs(st["mean"] - ALPHA) <= 4.0 * se + 0.005)
                         if abs(s - 1.0) < 1e-12 else None})
    out["K1_null_location_preserving"] = null
    out["K1_null_ok"] = all(r["ok_vs_construct"] and r["ok_vs_alpha"] is not False
                            for r in null)
    # the low-side insensitivity region, measured: the secant at delta = 0 is ~0
    zero = measured_secant(0.0, 1.0, "zero")
    out["K1_zero_delta_slope"] = {"slope": zero["slope"], "sd_hi": zero["sd_hi"],
                                  "sd_lo": zero["sd_lo"]}
    out["K1_zero_delta_insensitive"] = zero["slope"] <= SLOPE_CUT

    # ---- 5. K2: the fast path must reproduce the slow path
    spot = []
    for (k, d, s) in SPOT_SLOW:
        f = streams(mc_rate_fast, k, d, s, "spot_fast")
        g = streams(mc_rate_slow, k, d, s, "spot_slow")
        se = math.sqrt(f["sd"] ** 2 / N_STREAMS + g["sd"] ** 2 / N_STREAMS)
        spot.append({"k": k, "delta": d, "sigma": s,
                     "fast": f["mean"], "slow": g["mean"], "diff": f["mean"] - g["mean"],
                     "se_diff": se, "fast_per_stream": f["per_stream"],
                     "slow_per_stream": g["per_stream"],
                     "ok": abs(f["mean"] - g["mean"]) <= 4.0 * se + 0.005})
    out["K2_fast_slow_identity"] = spot
    out["K2_ok"] = all(r["ok"] for r in spot)

    # ---- 6. the criterion, and the mutation control that must break it
    def criterion(rel_errs, nonempty):
        return bool(nonempty) and all(abs(e) <= TOL for e in rel_errs)

    rel = [meas[repr(s)].get("width_rel_err") for s in SIGMAS]
    rel_ref = [meas[repr(s)].get("width_rel_err_refined") for s in SIGMAS]
    nonempty = all(meas[repr(s)]["ok"] and meas[repr(s)]["width"] > 0
                   and meas[repr(s)].get("insensitivity_region_nonempty", False)
                   for s in SIGMAS)
    # Two localisations of the SAME registered quantity are reported, and the
    # criterion is stated for both, so that the localisation cannot be chosen after
    # the fact: the grid-interpolated one (limited by my grid step) and the
    # bisection-refined one.  They agree, which is the point.
    out["criterion_b_met_coarse_grid"] = criterion(rel, nonempty)
    out["criterion_b_met"] = criterion(rel_ref, nonempty)
    out["criterion_b_width_rel_errs"] = dict((repr(s), meas[repr(s)].get("width_rel_err"))
                                             for s in SIGMAS)
    out["criterion_b_boundary_rel_errs"] = dict(
        (repr(s), [meas[repr(s)].get("delta_lo_rel_err"),
                   meas[repr(s)].get("delta_hi_rel_err")]) for s in SIGMAS)
    mut = {}
    for factor in (1.30, 0.70):
        mut[repr(factor)] = criterion([e + (factor - 1.0) for e in rel_ref], nonempty)
    # the STRICTER reading, reported rather than buried: each edge's POSITION
    # relative error, which is a different object from the width the criterion
    # names (an edge near zero has a small absolute error and a large relative one)
    edge_rel = []
    for s in SIGMAS:
        m = meas[repr(s)]
        if m["ok"]:
            edge_rel += [abs(m["delta_lo_rel_err"]), abs(m["delta_hi_rel_err"])]
    out["criterion_b_edge_position_max_rel_err"] = max(edge_rel) if edge_rel else None
    out["criterion_b_edge_position_within_tol"] = bool(edge_rel) and max(edge_rel) <= TOL
    out["criterion_b_width_within_tol"] = all(abs(e) <= TOL for e in rel)
    out["criterion_b_width_rel_errs_refined"] = dict(
        (repr(s), meas[repr(s)].get("width_rel_err_refined")) for s in SIGMAS)
    out["criterion_b_width_within_tol_refined"] = all(
        abs(meas[repr(s)]["width_rel_err_refined"]) <= TOL for s in SIGMAS)
    out["criterion_b_edge_position_max_rel_err_refined"] = max(
        max(abs(meas[repr(s)]["delta_lo_rel_err_refined"]),
            abs(meas[repr(s)]["delta_hi_rel_err_refined"])) for s in SIGMAS)
    out["criterion_b_edge_position_within_tol_refined"] = (
        out["criterion_b_edge_position_max_rel_err_refined"] <= TOL)
    out["criterion_b_mutation_control"] = mut
    out["criterion_b_mutation_ok"] = (mut["1.3"] is False and mut["0.7"] is False)

    out["ALL_PASS"] = bool(out["criterion_b_met"] and out["criterion_b_met_coarse_grid"]
                           and out["K1_null_ok"]
                           and out["K1_zero_delta_insensitive"] and out["K2_ok"]
                           and out["criterion_b_mutation_ok"])
    return out


def main():
    out = run()
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "results_v2.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print("wrote", dest)
    print("ALL_PASS:", out["ALL_PASS"])
    print("criterion_b_met:", out["criterion_b_met"],
          "| mutation control fires:", out["criterion_b_mutation_ok"])
    print("   width within tol:", out["criterion_b_width_within_tol"],
          "| STRICTER edge-position reading within tol:",
          out["criterion_b_edge_position_within_tol"],
          "(max edge rel err %.3f)" % out["criterion_b_edge_position_max_rel_err"])
    print("K1 null ok:", out["K1_null_ok"], "| K1 slope at delta=0: %.5f" % out["K1_zero_delta_slope"]["slope"],
          "(insensitive:", out["K1_zero_delta_insensitive"], ")")
    print("K2 fast/slow identity ok:", out["K2_ok"])
    print()
    print("sigma | pred band [lo, hi] width | meas band [lo, hi] width | width rel err")
    for s in SIGMAS:
        p = out["predicted_bands"][repr(s)]
        m = out["measured_bands"][repr(s)]
        if m["ok"]:
            print(" %4.1f | [%.4f, %.4f] %.4f | [%.4f, %.4f] %.4f | %+7.2f%%"
                  % (s, p["delta_lo"], p["delta_hi"], p["width"],
                     m["delta_lo"], m["delta_hi"], m["width"], 100.0 * m["width_rel_err"]))
            print("      refined | [%.4f, %.4f] %.4f | width rel err %+6.2f%% | edges %+6.2f%% / %+6.2f%%"
                  % (m["delta_lo_refined"], m["delta_hi_refined"], m["width_refined"],
                     100.0 * m["width_rel_err_refined"],
                     100.0 * m["delta_lo_rel_err_refined"],
                     100.0 * m["delta_hi_rel_err_refined"]))
        else:
            print(" %4.1f | [%.4f, %.4f] %.4f | NOT BRACKETED (%d)"
                  % (s, p["delta_lo"], p["delta_hi"], p["width"], m["n_brackets"]))
    print()
    print("band law (tangent definition): width * sqrt(k) / sigma, per (sigma, k)")
    for r in out["band_law_tangent"]:
        print("   sigma=%.1f k=%-4d width=%.4f  width*sqrt(k)/sigma=%.4f"
              % (r["sigma"], r["k"], r["width"], r["width_times_sqrt_k_over_sigma"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
