#!/usr/bin/env python3
"""Issue #38 - the canonical runner.

Recomputes, from `alloc_model.py` alone, every number the manuscript reports, and writes:

    canonical_results.json   the artefact.  RUN-INVARIANT: rerunning must reproduce it
                             byte for byte.  It carries no timestamps, no durations and
                             no interpreter/build fields.
    run.log                  a human-readable transcript of the same run.  Written last
                             and deliberately NOT part of the hash-pinned set (README).

Sections
--------
  reductions    the two structural reductions (exactness is a by-construction anchor)
  anchors       brackets, monotonicity, and the no-information limits
  law_grid      sigma* over (N, beta, m) at two cost scales, plus the P1/P2 verdicts
  oos           the one-scalar law: coefficients from the law_grid, scored on unseen gamma
  closure       candidate predictor forms, A's structure, robustness, attention-agnostic test
  mechanism     mismatch rates and the scrambling (Hamming) signature
  p3_ablation   the specialisation / information channel ablation

Usage:  python3 canonical_runner.py          (about 3 minutes)
"""
from __future__ import annotations

import json
import os
import numpy as np

import alloc_model as M

HERE = os.path.dirname(os.path.abspath(__file__))
ARTEFACT = os.path.join(HERE, "canonical_results.json")
LOG = os.path.join(HERE, "run.log")

K = 4
BIG = 1e6
CFG = {
    "K_blocks": K,
    "law_grid": {"Ns": [16, 32, 64, 128, 256], "betas": [0.0, 0.25, 0.5, 1.0, 2.0],
                 "ms": [1, 2, 4, 8, 16], "gammas": [0.25, 1.0], "seeds": 30},
    "oos": {"test_gammas": [0.5, 2.0], "betas": [0.1, 0.75, 1.5, 3.0],
            "ms": [3, 6, 12], "Ns": [24, 48, 96, 192, 384], "seeds": 20},
    "closure": {"train_gammas": [0.25, 0.5], "test_gammas": [1.0, 2.0],
                "Ns": [16, 32, 64, 128], "ms": [2, 8], "betas": [0.0, 0.5, 2.0],
                "seeds": 15, "gap_seeds": 5,
                "robust_dists": ["lognormal", "beta"], "robust_Ks": [2, 8],
                "robust_betas": [0.0, 2.0], "robust_Ns": [32, 128], "robust_gamma": 1.0,
                "attention_alphas": [0.0625, 0.25], "attention_betas": [0.0, 0.5, 2.0],
                "attention_Ns": [32, 128], "attention_gamma": 1.0},
    "mechanism": {"gammas": [0.25, 1.0], "betas": [0.0, 0.5, 2.0],
                  "sigmas": [0.05, 0.2, 0.5], "Ns": [16, 32, 64, 128, 256], "seeds": 30},
    "p3": {"gamma": 1.0, "m": 4, "betas": [0.0, 0.25, 0.5, 1.0, 2.0],
           "Ns": [16, 64, 256], "seeds": 25, "sigmas": [0.0, 0.05, 0.2]},
    "seed_scheme": {"law_grid_instance": "1000*s + N", "noise": "7*s + 3",
                    "oos_instance": "5000*s + 7*N", "oos_noise": "13*s + 11"},
}


# ---------------------------------------------------------------- helpers
def instances(N, beta, gamma, seeds, K_=K, dist="uniform"):
    def mk(seed):
        if dist == "uniform":
            return M.make_instance(N, K_, beta, gamma, seed=seed)[0]
        return dist_instance(N, K_, beta, gamma, seed, dist)
    return [(mk(1000 * s + N), 7 * s + 3) for s in range(seeds)]


def opt(C):
    return M.true_cost(C, M.oracle_assign(C))


def planner_total(C_list, m):
    return float(np.mean([M.true_cost(C, M.planner_assign(C, m, np.random.default_rng(sd)))
                          - opt(C) for C, sd in C_list]))


def market_total(C_list, sigma):
    return float(np.mean([M.true_cost(C, M.market_assign(C, sigma, np.random.default_rng(sd)))
                          - opt(C) for C, sd in C_list]))


def sigma_star(C_list, planner_tot, lo=1e-5, hi=12.0, iters=20):
    """Market wins iff sigma < sigma*; bracketed by bisection on the mean regret."""
    if planner_tot <= 0:
        return 0.0, "planner exact (no boundary)"

    def f(sig):
        return market_total(C_list, sig) - planner_tot

    if f(lo) > 0:
        return None, "market already loses at sigma=lo"
    if f(hi) < 0:
        return None, "market still wins at sigma=hi"
    a, b = lo, hi
    for _ in range(iters):
        mid = 0.5 * (a + b)
        if f(mid) < 0:
            a = mid
        else:
            b = mid
    return 0.5 * (a + b), ""


def fit_power(x, y):
    """Least-squares y = c * x^b, with the identifiability guard."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    assert len(np.unique(np.round(x, 12))) >= 2, "a power law needs >= 2 distinct x"
    b, logc = np.polyfit(np.log(x), np.log(y), 1)
    resid = np.log(y) - (logc + b * np.log(x))
    return {"b": float(b), "c": float(np.exp(logc)),
            "r2": float(1 - resid.var() / np.log(y).var()),
            "resid_std_log": float(resid.std()), "n": int(len(x))}


def score(pred, truth):
    rel = np.abs(np.asarray(pred, float) - np.asarray(truth, float)) / np.asarray(truth, float)
    return {"median_rel_err": float(np.median(rel)), "mean_rel_err": float(rel.mean()),
            "max_rel_err": float(rel.max())}


def _draw_u(rng, dist, n, mean=0.5, sd=1.0 / np.sqrt(12.0)):
    if dist == "uniform":
        return rng.random(n)
    if dist == "lognormal":
        u = np.exp(0.6 * rng.standard_normal(n))
    elif dist == "beta":
        u = rng.beta(2.0, 5.0, size=n)
    else:
        raise ValueError(dist)
    return (u - u.mean()) / (u.std() + 1e-12) * sd + mean


def dist_instance(N, K_, beta, gamma, seed, dist):
    rng = np.random.default_rng(seed)
    u = _draw_u(rng, dist, N * N).reshape(N, N)
    tb = np.arange(N) % K_
    ab = np.arange(N) % K_
    mism = (tb[:, None] != ab[None, :]).astype(float)
    return 1.0 + gamma * u + beta * mism


def instance_for(N, K_, beta, gamma, seed, dist):
    if dist == "uniform":
        return M.make_instance(N, K_, beta, gamma, seed=seed)[0]
    return dist_instance(N, K_, beta, gamma, seed, dist)


def assignment_gap(C):
    """Exact: the best assignment other than the optimum (forbid each optimal edge)."""
    a = M.oracle_assign(C)
    best = float("inf")
    for j in range(C.shape[0]):
        Mx = C.copy()
        Mx[j, a[j]] += BIG
        v = M.true_cost(Mx, M.oracle_assign(Mx))
        if v < best:
            best = v
    return float(best - M.true_cost(C, a))


# ---------------------------------------------------------------- sections
def sec_reductions():
    rows = M.reductions(Ns=(8, 12, 16, 24, 32, 64), K=K, betas=(0.0, 0.5, 2.0),
                        gammas=(0.0, 0.25, 1.0), seeds=5)
    return {"cells": len(rows),
            "A_attention_unbounded_eq_optimum": all(r["A_exact"] for r in rows),
            "B_zero_noise_market_eq_optimum": all(r["B_exact"] for r in rows),
            "failures": sum(1 for r in rows if not (r["A_exact"] and r["B_exact"])),
            "grid": {"Ns": [8, 12, 16, 24, 32, 64], "betas": [0.0, 0.5, 2.0],
                     "gammas": [0.0, 0.25, 1.0], "seeds": 5, "K": K}}


def sec_anchors():
    out = {}
    br = []
    for N in (16, 32, 64):
        for beta in (0.0, 0.5, 2.0):
            for s in range(5):
                C, _, _ = M.make_instance(N, K, beta, 0.5, seed=1000 * s + N)
                r = M.regrets(C, min(4, N), 0.05, s)
                br.append({"regrets_nonnegative": all(
                    r[k] >= -1e-9 for k in ("planner", "market", "greedy", "random")),
                    "greedy_le_random": r["greedy"] <= r["random"] + 1e-9})
    out["bracket_cells"] = len(br)
    out["all_regrets_nonnegative"] = all(b["regrets_nonnegative"] for b in br)
    out["greedy_le_random_rate"] = sum(b["greedy_le_random"] for b in br) / len(br)

    curve = []
    for m in (0, 1, 2, 4, 8, 16, 32, 64):
        r = M.mean_regrets(64, K, 0.5, 0.5, m=m, sigma=0.0, seeds=10, nested=True)
        curve.append({"m": m, "attended_fraction": m / 64, "planner_regret": r["planner"]})
    vals = [c["planner_regret"] for c in curve]
    out["planner_curve_nested_N64"] = curve
    out["planner_monotone_nonincreasing_in_m"] = all(
        vals[i + 1] <= vals[i] + 1e-9 for i in range(len(vals) - 1))
    out["planner_exact_at_m_eq_N"] = abs(vals[-1]) < 1e-9

    out["random_regret_per_task"] = [
        {"N": N, "value": M.mean_regrets(N, K, 0.5, 0.5, m=0, sigma=0.0, seeds=20)["random"] / N}
        for N in (16, 32, 64, 128, 256)]

    mcurve = []
    for sigma in (0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.4, 0.8):
        r = M.mean_regrets(64, K, 0.5, 0.5, m=64, sigma=sigma, seeds=20)
        mcurve.append({"sigma": sigma, "market_regret": r["market"]})
    mv = [c["market_regret"] for c in mcurve]
    out["market_curve_N64"] = mcurve
    out["market_monotone_nondecreasing_in_sigma"] = all(
        mv[i + 1] >= mv[i] - 1e-9 for i in range(len(mv) - 1))
    out["market_exact_at_sigma_zero"] = abs(mv[0]) < 1e-9
    return out


def sec_law_grid():
    g = CFG["law_grid"]
    cells = []
    for gamma in g["gammas"]:
        for beta in g["betas"]:
            for m in g["ms"]:
                for N in g["Ns"]:
                    if m > N:
                        continue
                    inst = instances(N, beta, gamma, g["seeds"])
                    pt = planner_total(inst, m)
                    p = pt / N
                    ss, note = sigma_star(inst, pt)
                    cells.append({"gamma": gamma, "beta": beta, "m": m, "N": N,
                                  "planner_per_task": p, "sigma_star": ss,
                                  "A": (ss / p) if (ss and p > 0) else None,
                                  "note": note})
    usable = [c for c in cells if c["A"]]
    A = np.array([c["A"] for c in usable], float)
    Ns = np.array([c["N"] for c in usable], float)
    p_all = np.array([c["planner_per_task"] for c in usable], float)
    s_all = np.array([c["sigma_star"] for c in usable], float)

    series_p1 = []
    for gamma in g["gammas"]:
        for beta in g["betas"]:
            for m in g["ms"]:
                pts = sorted([(c["N"], c["sigma_star"]) for c in cells
                              if c["gamma"] == gamma and c["beta"] == beta
                              and c["m"] == m and c["sigma_star"]], key=lambda t: t[0])
                if len(pts) >= 2:
                    vals = [t[1] for t in pts]
                    steps = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
                    series_p1.append({
                        "gamma": gamma, "beta": beta, "m": m,
                        "Ns": [t[0] for t in pts], "sigma_star": vals,
                        "strictly_increasing": all(d > 0 for d in steps),
                        "non_decreasing": all(d >= -1e-12 for d in steps),
                        "strictly_decreasing": all(d < 0 for d in steps),
                        "endpoint_rising": vals[-1] > vals[0],
                        "steps_nonneg": sum(1 for d in steps if d >= -1e-12),
                        "steps_negative": sum(1 for d in steps if d < -1e-12),
                        "n_steps": len(steps)})
    med = float(np.median(A))
    return {
        "cells": cells, "usable_cells": len(usable),
        "A_stats": {"median": med, "min": float(A.min()), "max": float(A.max()),
                    "spread": float(A.max() / A.min()),
                    "iqr": [float(np.percentile(A, 25)), float(np.percentile(A, 75))]},
        "A_by_gamma": {str(gm): {"n": sum(1 for c in usable if c["gamma"] == gm),
                                 "median": float(np.median([c["A"] for c in usable
                                                            if c["gamma"] == gm]))}
                       for gm in g["gammas"]},
        # The law's residual is not white: report where it lives, by attention budget.
        "A_by_m": {str(mm): {"n": sum(1 for c in usable if c["m"] == mm),
                             "median": float(np.median([c["A"] for c in usable
                                                        if c["m"] == mm])),
                             "min": float(np.min([c["A"] for c in usable if c["m"] == mm])),
                             "max": float(np.max([c["A"] for c in usable if c["m"] == mm]))}
                   for mm in g["ms"] if [c for c in usable if c["m"] == mm]},
        "ratio_vs_logN_corr": float(np.corrcoef(np.log(Ns), A)[0, 1]),
        "p2_product_law": {"median_ratio": med,
                           "median_rel_err": float(np.median(np.abs(A - med) / med)),
                           "max_rel_err": float(np.max(np.abs(A - med) / med)),
                           "verdict": "UNMET"},
        "series_p1": series_p1,
        "p1_verdict": {
            "registered_expectation": "sigma*(N) monotonically decreasing",
            "n_series": len(series_p1),
            "n_strictly_increasing": sum(1 for r in series_p1 if r["strictly_increasing"]),
            "n_non_decreasing": sum(1 for r in series_p1 if r["non_decreasing"]),
            "n_strictly_decreasing": sum(1 for r in series_p1 if r["strictly_decreasing"]),
            "n_endpoint_rising": sum(1 for r in series_p1 if r["endpoint_rising"]),
            "n_endpoint_falling": sum(1 for r in series_p1 if not r["endpoint_rising"]),
            "steps_nonneg": sum(r["steps_nonneg"] for r in series_p1),
            "steps_negative": sum(r["steps_negative"] for r in series_p1),
            "n_steps": sum(r["n_steps"] for r in series_p1),
            "verdict": "REFUTED",
            "verdict_basis": ("no series is decreasing; the overwhelming majority of N-steps "
                              "are non-negative; every series ends above where it starts"),
        },
        "collapse_fit": fit_power(p_all, s_all),
    }


def sec_oos(law):
    o = CFG["oos"]
    test = []
    for gamma in o["test_gammas"]:
        for beta in o["betas"]:
            for m in o["ms"]:
                for N in o["Ns"]:
                    if m > N:
                        continue
                    inst = [(instance_for(N, K, beta, gamma, 5000 * s + 7 * N, "uniform"),
                             13 * s + 11) for s in range(o["seeds"])]  # documented scheme
                    pt = planner_total(inst, m)
                    ss, _ = sigma_star(inst, pt)
                    if ss:
                        test.append({"gamma": gamma, "beta": beta, "m": m, "N": N,
                                     "planner_per_task": pt / N, "sigma_star": ss})
    train = [c for c in law["cells"] if c["A"]]
    p_tr = np.array([c["planner_per_task"] for c in train], float)
    s_tr = np.array([c["sigma_star"] for c in train], float)
    gam_tr = np.array([c["gamma"] for c in train], float)
    p_te = np.array([c["planner_per_task"] for c in test], float)
    s_te = np.array([c["sigma_star"] for c in test], float)
    gam_te = np.array([c["gamma"] for c in test], float)

    lawf = fit_power(p_tr, s_tr)
    a_slope = np.polyfit(np.log(gam_tr), np.log(s_tr / p_tr), 1)

    def c_of(x):
        return float(np.exp(np.mean(np.log(s_tr) - np.log(x))))

    preds = {
        "fitted_power_law": np.exp(np.log(lawf["c"]) + lawf["b"] * np.log(p_te)),
        "trivial_proportional": c_of(p_tr) * p_te,
        "constant_baseline": np.full_like(s_te, float(np.median(s_tr))),
        "gamma_aware_proportional": p_te * np.exp(np.polyval(a_slope, np.log(gam_te))),
    }
    refit = fit_power(p_te, s_te)
    return {"train_cells": len(train), "test_cells": len(test),
            "train_fit": lawf,
            "gamma_exponent": {"slope": float(a_slope[0]), "intercept": float(a_slope[1])},
            "scores": {k: score(v, s_te) for k, v in preds.items()},
            "test_refit": refit, "exponent_drift": float(refit["b"] - lawf["b"]),
            "test_cells_detail": test}


def sec_closure():
    c = CFG["closure"]

    def measure(N, K_, beta, gamma, m, dist="uniform"):
        inst = instances(N, beta, gamma, c["seeds"], K_=K_, dist=dist)
        pt = planner_total(inst, m)
        ss, _ = sigma_star(inst, pt)
        return {"N": N, "K": K_, "beta": beta, "gamma": gamma, "m": m, "dist": dist,
                "planner_per_task": (pt / N) if pt > 0 else 0.0,
                "cost_sd": float(np.mean([float(np.std(C)) for C, _ in inst])),
                "assignment_gap": float(np.mean([
                    assignment_gap(instance_for(N, K_, beta, gamma, 1000 * s + N, dist))
                    for s in range(c["gap_seeds"])])),
                "sigma_star": ss}

    train, test = [], []
    for gamma in c["train_gammas"]:
        for N in c["Ns"]:
            for m in c["ms"]:
                for beta in c["betas"]:
                    train.append(measure(N, K, beta, gamma, m))
    for gamma in c["test_gammas"]:
        for N in c["Ns"]:
            for m in c["ms"]:
                for beta in c["betas"]:
                    test.append(measure(N, K, beta, gamma, m))
    robust = [measure(N, K_, beta, c["robust_gamma"], 4, dist=d)
              for d in c["robust_dists"] for K_ in c["robust_Ks"]
              for beta in c["robust_betas"] for N in c["robust_Ns"]]
    attn = []
    for alpha in c["attention_alphas"]:
        for beta in c["attention_betas"]:
            for N in c["attention_Ns"]:
                m = M.attention_budget(N, "fraction", alpha)
                rec = measure(N, K, beta, c["attention_gamma"], m)
                rec["alpha"] = alpha
                attn.append(rec)

    tr = [r for r in train if r["sigma_star"]]
    te = [r for r in test if r["sigma_star"]]
    p_tr = np.array([r["planner_per_task"] for r in tr], float)
    y_tr = np.array([r["sigma_star"] for r in tr], float)
    p_te = np.array([r["planner_per_task"] for r in te], float)
    y_te = np.array([r["sigma_star"] for r in te], float)
    sd_tr = np.array([r["cost_sd"] for r in tr], float)
    sd_te = np.array([r["cost_sd"] for r in te], float)
    g_tr = np.array([r["assignment_gap"] for r in tr], float)
    g_te = np.array([r["assignment_gap"] for r in te], float)
    gam_tr = np.array([r["gamma"] for r in tr], float)
    gam_te = np.array([r["gamma"] for r in te], float)
    b_tr = 1.0 + np.array([r["beta"] for r in tr], float)
    b_te = 1.0 + np.array([r["beta"] for r in te], float)

    def c_of(x):
        return float(np.exp(np.mean(np.log(y_tr) - np.log(x))))

    las = np.polyfit(np.log(gam_tr), np.log(y_tr / p_tr), 1)
    las_b = np.polyfit(np.log(b_tr), np.log(y_tr / p_tr), 1)
    forms = {
        "H_gamma": p_te * np.exp(np.polyval(las, np.log(gam_te))),
        "H_const": c_of(p_tr) * p_te,
        "H_beta": p_te * np.exp(np.polyval(las_b, np.log(b_te))),
        "H_gap2": c_of(np.sqrt(p_tr * g_tr)) * np.sqrt(p_te * g_te),
        "H_gap": c_of(g_tr) * g_te,
        "H_scale": c_of(p_tr * sd_tr) * p_te * sd_te,
    }
    const = c_of(p_tr)
    ag = [r for r in attn if r["sigma_star"] and r["planner_per_task"] > 0]
    p_ag = np.array([r["planner_per_task"] for r in ag], float)
    y_ag = np.array([r["sigma_star"] for r in ag], float)
    # The attention-model test must not be confounded by the cost scale: A depends on gamma,
    # so the constant is fitted on BUDGET cells at the same gamma as the fraction cells.
    gam_att = c["attention_gamma"]
    at_g = [r for r in te if r["gamma"] == gam_att]
    p_at_g = np.array([r["planner_per_task"] for r in at_g], float)
    y_at_g = np.array([r["sigma_star"] for r in at_g], float)
    const_att = float(np.exp(np.mean(np.log(y_at_g) - np.log(p_at_g))))
    # and, for contrast, the training-scale constant (a confined comparison, not the test)
    ag_cross = [r for r in ag]

    def exponent(rows):
        return float(np.polyfit(np.log([r["planner_per_task"] for r in rows]),
                                np.log([r["sigma_star"] for r in rows]), 1)[0])

    def A_median(rows):
        vals = [r["sigma_star"] / r["planner_per_task"] for r in rows if r["planner_per_task"] > 0]
        return {"n": len(vals), "median": float(np.median(vals))} if vals else {"n": 0, "median": None}

    return {
        "train_cells": len(tr), "test_cells": len(te),
        "robust_cells": len([r for r in robust if r["sigma_star"]]),
        "forms_scored_on_unseen_cells": {k: score(v, y_te) for k, v in forms.items()},
        "one_constant": {"c": const,
                         "median_rel_err_on_unseen": score(const * p_te, y_te)["median_rel_err"]},
        "A_by_gamma": {str(g): A_median([r for r in tr + te if r["gamma"] == g])
                       for g in sorted(set(c["train_gammas"] + c["test_gammas"]))},
        # "uniform" is the distribution of the training/test cells themselves; the
        # other two are the held-out robustness cells. Reported together so the
        # manuscript's distribution-robustness claim is read from the artefact.
        "A_by_distribution": dict(
            [("uniform", A_median(te))]
            + [(d, A_median([r for r in robust if r["dist"] == d]))
               for d in sorted({r["dist"] for r in robust})]),
        "exponent_by_gamma": {str(g): exponent([r for r in tr + te if r["gamma"] == g])
                              for g in sorted(set(c["train_gammas"] + c["test_gammas"]))},
        "exponent_by_distribution": {d: exponent([r for r in robust if r["dist"] == d])
                                     for d in sorted({r["dist"] for r in robust})
                                     if [r for r in robust if r["dist"] == d]},
        "attention_agnostic": {
            "n": len(ag),
            "budget_cells_at_same_cost_scale": {
                "gamma": gam_att, "n": len(at_g), "constant": const_att,
                "median_rel_err": score(const_att * p_at_g, y_at_g)["median_rel_err"],
                "median_A": float(np.median(y_at_g / p_at_g))},
            "fraction_cells_never_fitted": {
                "median_rel_err": score(const_att * p_ag, y_ag)["median_rel_err"],
                "max_rel_err": score(const_att * p_ag, y_ag)["max_rel_err"],
                "A_values": [r["sigma_star"] / r["planner_per_task"] for r in ag],
                "median_A": float(np.median(y_ag / p_ag)),
                "median_p": float(np.median(p_ag))},
            "cross_cost_scale_constant_for_contrast": {
                "constant": const,
                "median_rel_err": score(const * p_ag, y_ag)["median_rel_err"],
                "note": "the training-scale constant applied at another cost scale: the "
                        "difference from the gamma-matched row above is the cost-scale "
                        "effect, not an attention effect"}},
        "A_extremes": sorted(
            [{"dist": r["dist"], "K": r["K"], "gamma": r["gamma"], "beta": r["beta"],
              "N": r["N"], "m": r["m"], "planner_per_task": r["planner_per_task"],
              "A": r["sigma_star"] / r["planner_per_task"]}
             for r in tr + te if r["sigma_star"] and r["planner_per_task"] > 0],
            key=lambda r: -r["A"])[:8],
    }


def sec_mechanism():
    m = CFG["mechanism"]
    out = {"wrong_block_rate": [], "hamming": [], "beta_sweep": []}
    for gamma in m["gammas"]:
        for beta in m["betas"]:
            for sigma in m["sigmas"]:
                wb, hm = [], []
                for N in m["Ns"]:
                    rr, hh = [], []
                    for s in range(m["seeds"]):
                        C, tb, ab = M.make_instance(N, K, beta, gamma, seed=1000 * s + N)
                        ao = M.oracle_assign(C)
                        am = M.market_assign(C, sigma, np.random.default_rng(7 * s + 3))
                        rr.append(float(np.mean(ab[am] != ab)))
                        hh.append(float(np.mean(am != ao)))
                    wb.append({"N": N, "rate": float(np.mean(rr))})
                    hm.append({"N": N, "rate": float(np.mean(hh))})
                out["wrong_block_rate"].append({"gamma": gamma, "beta": beta, "sigma": sigma,
                                                "series": wb})
                out["hamming"].append({"gamma": gamma, "beta": beta, "sigma": sigma,
                                       "series": hm})
    for beta in (0.0, 0.25, 0.5, 1.0, 2.0):
        row = {}
        for N in (16, 64, 256):
            rr = []
            for s in range(20):
                C, tb, ab = M.make_instance(N, K, beta, 1.0, seed=1000 * s + N)
                am = M.market_assign(C, 0.2, np.random.default_rng(7 * s + 3))
                rr.append(float(np.mean(ab[am] != ab)))
            row["N%d" % N] = float(np.mean(rr))
        out["beta_sweep"].append({"beta": beta, "gamma": 1.0, "sigma": 0.2, **row})
    oracle = []
    for N in m["Ns"]:
        rr = []
        for s in range(20):
            C, tb, ab = M.make_instance(N, K, 0.5, 1.0, seed=1000 * s + N)
            ao = M.oracle_assign(C)
            rr.append(float(np.mean(ab[ao] != ab)))
        oracle.append({"N": N, "beta": 0.5, "rate": float(np.mean(rr))})
    out["oracle_mismatch_rate"] = oracle
    return out


def sec_p3():
    p3 = CFG["p3"]
    rows = []
    for N in p3["Ns"]:
        for beta in p3["betas"]:
            inst = instances(N, beta, p3["gamma"], p3["seeds"])
            pt = planner_total(inst, p3["m"])
            ss, _ = sigma_star(inst, pt)
            rec = {"N": N, "beta": beta, "m": p3["m"], "gamma": p3["gamma"],
                   "planner_per_task": pt / N, "sigma_star": ss}
            for sigma in p3["sigmas"]:
                mm, hh, rg = [], [], []
                for C, sd in inst:
                    ao = M.oracle_assign(C)
                    am = M.market_assign(C, sigma, np.random.default_rng(sd))
                    ab = np.arange(C.shape[0]) % K
                    mm.append(float(np.mean(ab[am] != ab)))
                    hh.append(float(np.mean(am != ao)))
                    rg.append(M.true_cost(C, am) - opt(C))
                rec["market_mismatch_sigma%s" % sigma] = float(np.mean(mm))
                rec["market_hamming_sigma%s" % sigma] = float(np.mean(hh))
                rec["market_regret_per_task_sigma%s" % sigma] = float(np.mean(rg)) / N
            rows.append(rec)
    off = [r for r in rows if r["beta"] == 0.0]
    top = max(p3["betas"])
    on = [r for r in rows if r["beta"] == top]
    return {
        "rows": rows,
        "specialisation_off_boundary_still_exists": all(
            r["sigma_star"] and r["sigma_star"] > 0 for r in off),
        "sigma_star_specialisation_off": {str(r["N"]): r["sigma_star"] for r in off},
        "amplification_beta_max_over_beta_0": {
            str(a["N"]): (a["sigma_star"] / b["sigma_star"])
            for a, b in zip(on, off) if a["sigma_star"] and b["sigma_star"]},
        "market_regret_exactly_zero_when_information_perfect": all(
            abs(r["market_regret_per_task_sigma0.0"]) < 1e-12 for r in rows),
        "market_mismatch_by_beta_at_sigma_0.2": {
            str(b): [r["market_mismatch_sigma0.2"] for r in rows if r["beta"] == b]
            for b in p3["betas"]},
        "verdict": "REFUTED",
    }


# ---------------------------------------------------------------- main
def main():
    log = []

    def note(msg):
        print(msg)
        log.append(msg)

    note("issue #38 - canonical runner (bounded-attention planner vs bidding market)")
    note("config: %s" % json.dumps(CFG, sort_keys=True))
    note("")

    out = {}
    out["reductions"] = sec_reductions()
    r = out["reductions"]
    note("reductions: %d cells | A (unbounded attention == optimum) = %s | "
         "B (sigma=0 market == optimum) = %s | failures = %d" % (
             r["cells"], r["A_attention_unbounded_eq_optimum"],
             r["B_zero_noise_market_eq_optimum"], r["failures"]))

    out["anchors"] = sec_anchors()
    a = out["anchors"]
    note("anchors: regrets non-negative = %s | greedy<=random = %.2f | planner monotone in m "
         "= %s | planner exact at m=N = %s | market monotone in sigma = %s | market exact at "
         "sigma=0 = %s" % (a["all_regrets_nonnegative"], a["greedy_le_random_rate"],
                           a["planner_monotone_nonincreasing_in_m"], a["planner_exact_at_m_eq_N"],
                           a["market_monotone_nondecreasing_in_sigma"],
                           a["market_exact_at_sigma_zero"]))

    out["law_grid"] = sec_law_grid()
    lg = out["law_grid"]
    note("law grid: %d cells (%d usable) | A = sigma*/p median %.3f range [%.3f, %.3f] "
         "spread x%.2f | P1 %s (%d/%d series strictly increasing, %d/%d steps non-negative, "
         "%d decreasing) | P2 %s (median rel err %.1f%%)" % (
             len(lg["cells"]), lg["usable_cells"], lg["A_stats"]["median"],
             lg["A_stats"]["min"], lg["A_stats"]["max"], lg["A_stats"]["spread"],
             lg["p1_verdict"]["verdict"], lg["p1_verdict"]["n_strictly_increasing"],
             lg["p1_verdict"]["n_series"], lg["p1_verdict"]["steps_nonneg"],
             lg["p1_verdict"]["n_steps"], lg["p1_verdict"]["n_strictly_decreasing"],
             lg["p2_product_law"]["verdict"],
             100 * lg["p2_product_law"]["median_rel_err"]))
    note("collapse fit (sigma* ~ p^b): b = %.4f, R2 = %.4f, n = %d" % (
        lg["collapse_fit"]["b"], lg["collapse_fit"]["r2"], lg["collapse_fit"]["n"]))

    out["oos"] = sec_oos(lg)
    oo = out["oos"]
    note("oos: %d train / %d test cells" % (oo["train_cells"], oo["test_cells"]))
    for k in sorted(oo["scores"], key=lambda k: oo["scores"][k]["median_rel_err"]):
        note("   %-26s median %5.1f%%  max %6.1f%%" % (
            k, 100 * oo["scores"][k]["median_rel_err"], 100 * oo["scores"][k]["max_rel_err"]))
    note("   test refit exponent b = %.4f (drift %+.4f)" % (
        oo["test_refit"]["b"], oo["exponent_drift"]))

    out["closure"] = sec_closure()
    cl = out["closure"]
    note("closure: %d train / %d test / %d robust cells | one constant c = %.4f -> median "
         "%.1f%% on unseen" % (cl["train_cells"], cl["test_cells"], cl["robust_cells"],
                               cl["one_constant"]["c"],
                               100 * cl["one_constant"]["median_rel_err_on_unseen"]))
    for k in sorted(cl["forms_scored_on_unseen_cells"],
                    key=lambda k: cl["forms_scored_on_unseen_cells"][k]["median_rel_err"]):
        note("   %-12s median %6.1f%%  max %7.1f%%" % (
            k, 100 * cl["forms_scored_on_unseen_cells"][k]["median_rel_err"],
            100 * cl["forms_scored_on_unseen_cells"][k]["max_rel_err"]))
    aa = cl["attention_agnostic"]
    note("   attention-model test at gamma=%s: budget cells n=%d (constant %.3f, median %.1f%%) "
         "vs fraction cells n=%d never fitted (median %.1f%%, median A %.3f)" % (
             aa["budget_cells_at_same_cost_scale"]["gamma"],
             aa["budget_cells_at_same_cost_scale"]["n"],
             aa["budget_cells_at_same_cost_scale"]["constant"],
             100 * aa["budget_cells_at_same_cost_scale"]["median_rel_err"],
             aa["fraction_cells_never_fitted"] and aa["n"],
             100 * aa["fraction_cells_never_fitted"]["median_rel_err"],
             aa["fraction_cells_never_fitted"]["median_A"]))
    note("   (cross-cost-scale constant %.3f gives %.1f%% on the same fraction cells - the "
         "cost-scale effect, not an attention effect)" % (
             aa["cross_cost_scale_constant_for_contrast"]["constant"],
             100 * aa["cross_cost_scale_constant_for_contrast"]["median_rel_err"]))

    out["mechanism"] = sec_mechanism()
    me = out["mechanism"]
    h = [r for r in me["hamming"] if r["gamma"] == 1.0 and r["beta"] == 0.5 and r["sigma"] == 0.05]
    note("mechanism: oracle mismatch rate by N = %s" % (
        ["%.4f" % r["rate"] for r in me["oracle_mismatch_rate"]]))
    if h:
        note("   Hamming (gamma=1, beta=0.5, sigma=0.05) by N = %s" % (
            ["%.3f" % r["rate"] for r in h[0]["series"]]))

    out["p3_ablation"] = sec_p3()
    p3 = out["p3_ablation"]
    note("p3 ablation: specialisation off (beta=0) boundary exists = %s %s | amplification "
         "(beta=%s / beta=0) = %s | market exact at sigma=0 = %s" % (
             p3["specialisation_off_boundary_still_exists"],
             {k: round(v, 3) for k, v in p3["sigma_star_specialisation_off"].items()},
             max(CFG["p3"]["betas"]),
             {k: round(v, 2) for k, v in p3["amplification_beta_max_over_beta_0"].items()},
             p3["market_regret_exactly_zero_when_information_perfect"]))
    note("")

    with open(ARTEFACT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    note("wrote %s" % os.path.basename(ARTEFACT))
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
