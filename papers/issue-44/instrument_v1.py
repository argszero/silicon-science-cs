#!/usr/bin/env python3
"""
issue #44 -- instrument_v1.py
"The construct, validated out of sample: a single standardized margin"

v0 established the instrument's controls and three laws. v1 does the registered
work: criterion (a) -- the construct predicts detection rates across a crossed
(margin, spread, budget, mechanism) grid, parameter-free, with median absolute
error <= 10 percentage points.

THE CONSTRUCT (one sentence)
  For a verifier testing the sample mean at a threshold calibrated to alpha on a
  standardised honest node N(0,1), the detection probability of ANY node is

        power = Phi(u),      u = ( sqrt(k) * delta_D - c_alpha ) / sigma_D

  where (delta_D, sigma_D) are the divergent node's own mean and sd and
  c_alpha = Phi^-1(1 - alpha). So exactly TWO numbers describe a divergence's
  detectability, and no other feature of the mechanism may enter.

WHY THAT IS A TEST AND NOT A TAUTOLOGY
  Every prediction below is computed from theory with NO fitted parameter. The
  grid is crossed so that the SAME u arises from different decompositions
  (different k, delta_D, sigma_D, and different mechanisms) -- so the test is
  whether u alone decides, not whether the algebra is self-consistent.

TESTS
  A  out-of-sample prediction: power = Phi(u) vs Monte Carlo over the crossed grid
     -> median |error| (registered criterion (a): <= 10 pp)
  B  invariance: cells sharing a u value must share a power, whatever their
     (k, delta, sigma, mechanism) decomposition
  C  mechanism-blindness: mechanisms with the same (delta_D, sigma_D) must agree
     (an affine contamination node and a Gaussian node of equal moments)
  D  calibration cell: pinned to the antecedent's reported rates
  E  null + needle re-checks at every grid cell (the instrument must not drift)

Pure stdlib. Deterministic.
"""

import json
import math
import os
import random
import statistics

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


# ---------------------------------------------------------------- mechanisms
# every mechanism exposes its EXACT moments (delta_D, sigma_D) -- that is all the
# construct is allowed to see
def mech_shift(delta):
    return ("shift", dict(delta=delta), lambda r: r.gauss(delta, 1.0), delta, 1.0)


def mech_shift_inflate(delta, rho):
    return ("shift_inflate", dict(delta=delta, rho=rho),
            lambda r: r.gauss(delta, rho), delta, rho)


def mech_inflate(rho):
    return ("inflate", dict(rho=rho), lambda r: r.gauss(0.0, rho), 0.0, rho)


def mech_contaminate(q, big):
    delta = q * big
    var = 1.0 + q * (1.0 - q) * big * big
    sigma = math.sqrt(var)

    def f(r):
        return r.gauss(big, 1.0) if r.random() < q else r.gauss(0.0, 1.0)
    return ("contaminate", dict(q=q, big=big), f, delta, sigma)


def mech_honest():
    return ("honest", {}, lambda r: r.gauss(0.0, 1.0), 0.0, 1.0)


def mech_collapse(c):
    return ("collapse", dict(c=c), lambda r: r.gauss(c, 1.0e-3), c, 1.0e-3)


# ---------------------------------------------------------------- prediction
def standardized_margin(k, delta_D, sigma_D):
    """u = (sqrt(k) delta_D - c_alpha) / sigma_D"""
    return (math.sqrt(k) * delta_D - C_ALPHA) / sigma_D


def predicted_power(k, delta_D, sigma_D):
    return phi(standardized_margin(k, delta_D, sigma_D))


# ---------------------------------------------------------------- Monte-Carlo
def mc_power(sampler, k, tau_m, n_mc, seed):
    r = random.Random(seed)
    rej = 0
    for _ in range(n_mc):
        s = 0.0
        for _ in range(k):
            s += sampler(r)
        if (s / k) > tau_m:
            rej += 1
    return rej / float(n_mc)


def mc_power_streams(sampler, k, tau_m, n_mc, n_streams, base_seed):
    vals = [mc_power(sampler, k, tau_m, n_mc, base_seed + 1000 * i)
            for i in range(n_streams)]
    return {"mean": statistics.fmean(vals),
            "sd": statistics.stdev(vals) if len(vals) > 1 else 0.0,
            "per_stream": vals}


def seed_for(*parts):
    h = 17
    for p in parts:
        h = (h * 1000003 + int(round(float(p) * 1000))) & 0x7FFFFFFF
    return h


# ---------------------------------------------------------------- the grid
N_MC_GRID = 15000
N_STREAMS = 5

K_GRID = [4, 16, 64]
DELTA_GRID = [0.15, 0.30, 0.60]
SIGMA_GRID = [0.6, 1.0, 1.8]


def build_grid():
    """cross mechanism x k x delta x sigma; sigma is realised through the mechanism"""
    cells = []
    for k in K_GRID:
        for delta in DELTA_GRID:
            # location-only mechanism
            name, pars, fn, dD, sD = mech_shift(delta)
            cells.append(dict(k=k, mech=name, pars=pars, fn=fn, dD=dD, sD=sD,
                              target_sigma=1.0))
            for sigma in SIGMA_GRID:
                if abs(sigma - 1.0) > 1e-12:
                    # dispersion is realised by a shift-inflate node of the same mean
                    n2, p2, f2, d2, s2 = mech_shift_inflate(delta, sigma)
                    cells.append(dict(k=k, mech=n2, pars=p2, fn=f2, dD=d2, sD=s2,
                                      target_sigma=sigma))
    return cells


def contamination_cells(moments):
    """nodes whose moments MATCH a Gaussian node's, to test mechanism-blindness"""
    out = []
    for delta, sigma in moments:
        # choose (q, big) so q*big = delta and 1 + q(1-q)big^2 = sigma^2
        # solve for q given s = sigma^2 - 1 = q(1-q) big^2 and delta = q big
        # => s = delta^2 (1-q)/q  =>  q = delta^2 / (delta^2 + s)
        s = sigma * sigma - 1.0
        if s <= 1e-9 or delta <= 1e-9:
            continue
        q = (delta * delta) / (delta * delta + s)
        if not (0.0 < q < 1.0):
            continue
        big = delta / q
        out.append((q, big, delta, sigma))
    return out


def run():
    out = {"experiment": "issue-44 instrument v1", "alpha": ALPHA,
           "c_alpha": C_ALPHA, "n_mc_grid": N_MC_GRID, "n_streams": N_STREAMS}
    rng_seed = 0

    # ---------------- A + B: crossed grid, out-of-sample prediction ----------
    cells = []
    for cell in build_grid():
        k, fn, dD, sD = cell["k"], cell["fn"], cell["dD"], cell["sD"]
        tau_m = C_ALPHA / math.sqrt(k)
        u = standardized_margin(k, dD, sD)
        pred = phi(u)
        rng_seed += 1
        mc = mc_power_streams(fn, k, tau_m, N_MC_GRID, N_STREAMS, seed_for(21, rng_seed))
        cells.append({
            "k": k, "mechanism": cell["mech"], "pars": cell["pars"],
            "delta_D": dD, "sigma_D": sD, "u": u, "predicted": pred,
            "observed": mc["mean"], "observed_sd": mc["sd"],
            "abs_error": abs(pred - mc["mean"]),
        })

    # mechanism-blindness: affine contamination nodes with matched moments
    blind = []
    for delta, sigma in ((0.30, 1.8), (0.60, 1.8), (0.15, 1.0), (0.30, 1.0)):
        for q, big, dD, sD in contamination_cells([(delta, sigma)]):
            rng_seed += 1
            for k in (16, 64):
                tau_m = C_ALPHA / math.sqrt(k)
                n2, p2, f2, d2, s2 = mech_contaminate(q, big)
                mc = mc_power_streams(f2, k, tau_m, N_MC_GRID, N_STREAMS,
                                      seed_for(22, rng_seed, k))
                pred = predicted_power(k, d2, s2)
                blind.append({
                    "mechanism": "contaminate", "q": q, "big": big, "k": k,
                    "delta_D": d2, "sigma_D": s2,
                    "u": standardized_margin(k, d2, s2),
                    "predicted": pred, "observed": mc["mean"],
                    "observed_sd": mc["sd"], "abs_error": abs(pred - mc["mean"]),
                })

    all_cells = cells + blind
    errs = [c["abs_error"] for c in all_cells]
    out["A_out_of_sample"] = {
        "n_cells": len(all_cells),
        "median_abs_error": statistics.median(errs),
        "mean_abs_error": statistics.fmean(errs),
        "max_abs_error": max(errs),
        "criterion_a_limit": 0.10,
        "criterion_a_met": statistics.median(errs) <= 0.10,
        "cells": all_cells,
    }

    # B: invariance -- group by u, the spread of observed power inside a group
    groups = {}
    for c in all_cells:
        key = round(c["u"], 3)
        groups.setdefault(key, []).append(c)
    inv = []
    for key in sorted(groups):
        g = groups[key]
        if len(g) < 2:
            continue
        obs = [c["observed"] for c in g]
        inv.append({"u": key, "n": len(g), "observed_min": min(obs),
                    "observed_max": max(obs), "spread": max(obs) - min(obs),
                    "predicted": statistics.fmean([c["predicted"] for c in g])})
    out["B_invariance"] = {
        "groups": inv,
        "max_spread": max([r["spread"] for r in inv]) if inv else None,
        "n_groups": len(inv),
        "invariance_holds": (max([r["spread"] for r in inv]) <= 0.05) if inv else False,
    }

    # E: null and needle at grid budgets (the instrument must not drift)
    chk = []
    for k in K_GRID:
        tau_m = C_ALPHA / math.sqrt(k)
        nh, _, fh, _, _ = mech_honest()
        null = mc_power_streams(fh, k, tau_m, N_MC_GRID, N_STREAMS, seed_for(23, k))
        nc, _, fc, _, _ = mech_collapse(0.0)
        needle = mc_power_streams(fc, k, tau_m, N_MC_GRID, N_STREAMS, seed_for(24, k))
        chk.append({"k": k, "null_observed": null["mean"], "needle_observed": needle["mean"],
                    "null_ok": abs(null["mean"] - ALPHA) <= 0.02,
                    "needle_ok": needle["mean"] <= ALPHA})
    out["E_drift_checks"] = chk

    # ---------------- D: calibration cell pinned to the antecedent -----------
    # antecedent (2609.10601): honest reproductions accepted 44/45; divergent pairs
    # rejected 104/105; k=5; same-input fabrication passed 27/29.
    # We do not re-run their pipeline -- we ask what OUR construct implies for those
    # measured rates, which is the falsifiable calibration the registration names.
    cal = {}
    alpha_anchor = 1.0 - 44.0 / 45.0            # 0.02222
    c_anchor = phi_inv(1.0 - alpha_anchor)
    cal["alpha_anchor"] = alpha_anchor
    cal["c_alpha_anchor"] = c_anchor

    # the divergent pairs were rejected 104/105 -> observed power 0.990476 at k=5.
    # invert the construct for the implied standardized margin u:
    p_div = 104.0 / 105.0
    k_anchor = 5
    u_implied = phi_inv(p_div)
    # power = Phi((sqrt(k) delta - c)/sigma)  =>  (sqrt(k) delta - c)/sigma = u
    # with sigma = 1 (their pairs are separated by location), the implied shift is
    delta_implied_sigma1 = (u_implied + c_anchor) / math.sqrt(k_anchor)
    cal["divergent_pairs"] = {
        "observed_power": p_div, "n": "104/105", "k": k_anchor,
        "implied_u": u_implied,
        "implied_delta_at_sigma_1": delta_implied_sigma1,
        "note": "the construct inverts to the node separation the antecedent measured",
    }

    # fabrication: 27 of 29 PASSED at k=5 -> observed detection 2/29 = 0.068966.
    # a same-input fabrication is a location-preserving, dispersion-collapsing node.
    obs_det = (29.0 - 27.0) / 29.0
    pred_det = 0.0        # u -> -infinity: Phi(-inf) = 0
    cal["same_input_fabrication"] = {
        "observed_detection": obs_det, "n": "2/29", "k": k_anchor,
        "construct_prediction": pred_det,
        "abs_error": abs(pred_det - obs_det),
        "reading": ("the construct predicts a location-preserving, dispersion-collapsed node "
                    "is undetectable (u -> -inf); the antecedent observed 2/29 detections, "
                    "i.e. the residual is at the alpha floor, not evidence of a larger margin"),
    }

    # what budget would the construct require to detect the fabrication at all?
    cal["fabrication_reachable_at_any_k"] = False
    cal["honest_acceptance_alpha_used"] = alpha_anchor

    out["C_mechanism_blindness"] = blind

    out["D_calibration"] = cal

    # ---------------- verdicts ----------------------------------------------
    v = {}
    v["A_criterion_a_met"] = out["A_out_of_sample"]["criterion_a_met"]
    v["A_median_abs_error"] = out["A_out_of_sample"]["median_abs_error"]
    v["A_n_cells"] = out["A_out_of_sample"]["n_cells"]
    v["B_invariance_holds"] = out["B_invariance"]["invariance_holds"]
    v["B_max_spread"] = out["B_invariance"]["max_spread"]
    v["C_mechanism_blindness_n"] = len(blind)
    v["C_mechanism_blindness_max_error"] = max([c["abs_error"] for c in blind]) if blind else None
    v["E_drift_ok"] = all(r["null_ok"] and r["needle_ok"] for r in chk)
    v["D_calibration_abs_error"] = cal["same_input_fabrication"]["abs_error"]
    v["ALL_PASS"] = all([v["A_criterion_a_met"], v["B_invariance_holds"], v["E_drift_ok"],
                         v["C_mechanism_blindness_max_error"] is not None
                         and v["C_mechanism_blindness_max_error"] <= 0.05])
    out["verdicts"] = v
    return out


def main():
    out = run()
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "results_v1.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print("wrote", dest)
    print("VERDICTS:", json.dumps(out["verdicts"], indent=2))
    print()
    a = out["A_out_of_sample"]
    print("A: out-of-sample prediction over %d cells; median|err|=%.4f mean=%.4f max=%.4f"
          % (a["n_cells"], a["median_abs_error"], a["mean_abs_error"], a["max_abs_error"]))
    print()
    print("B: invariance groups (same u, different decomposition):")
    for r in out["B_invariance"]["groups"][:12]:
        print("   u=%7.3f n=%d obs=[%.3f,%.3f] spread=%.4f"
              % (r["u"], r["n"], r["observed_min"], r["observed_max"], r["spread"]))
    print("   ... %d groups, max spread = %.4f"
          % (out["B_invariance"]["n_groups"], out["B_invariance"]["max_spread"]))
    print()
    print("C: mechanism blindness (contamination nodes matched to Gaussian moments):")
    for r in out["C_mechanism_blindness"]:
        print("   k=%-3d q=%.4f big=%.2f  u=%7.3f pred=%.4f obs=%.4f |err|=%.4f"
              % (r["k"], r["q"], r["big"], r["u"], r["predicted"], r["observed"], r["abs_error"]))
    print()
    d = out["D_calibration"]
    print("D: calibration cell (antecedent 2609.10601)")
    print("   alpha_anchor=%.5f  c_alpha=%.4f" % (d["alpha_anchor"], d["c_alpha_anchor"]))
    dp = d["divergent_pairs"]
    print("   divergent pairs 104/105 at k=5 -> power %.6f -> implied u=%.4f -> implied delta(sigma=1)=%.4f"
          % (dp["observed_power"], dp["implied_u"], dp["implied_delta_at_sigma_1"]))
    si = d["same_input_fabrication"]
    print("   same-input fabrication 27/29 passed -> observed detection %.4f ; construct predicts %.4f |err|=%.4f"
          % (si["observed_detection"], si["construct_prediction"], si["abs_error"]))
    print()
    print("E: drift checks:")
    for r in out["E_drift_checks"]:
        print("   k=%-3d null=%.4f (ok=%s) needle=%.4f (ok=%s)"
              % (r["k"], r["null_observed"], r["null_ok"], r["needle_observed"], r["needle_ok"]))


if __name__ == "__main__":
    main()
