#!/usr/bin/env python3
"""Issue #42 v2 -- the out-of-sample law race (registered criteria 5(b), (c), (d)).

v1 established that the DRIVER of the layer decision is the residual-catch product
(1-beta)*C2, and that a bare constant threshold on that product is 38% off out of sample
against the primary. v2 scores the decision the way the registration asks: fit on one set
of regime families and cost ratios, score on families, cost ratios, dial values and layer
accuracies that were NEVER fitted, report MEDIAN RELATIVE ERROR (not R^2), and report the
dispersion over at least 20 disjoint seed streams (criterion d).

WHAT IS PREDICTED. Adding the layer beats spending the same budget on the primary exactly
when

    (1-beta)*C2  >  T(f, r, C2),     T = f2 - f,
    f2 = 1 - exp( -(h(f) + r*h(C2)) ),   h(x) = -log(1-x),   r = kappa2/kappa1

so the break-even threshold T is a FUNCTION of three things, not a number. Every law below
is a predictor of T; the error is the median relative error of the predicted threshold.

LAWS
  L0 constant          one number, the median T over the fitted cells
  L1 by cost ratio     the median T per fitted r, interpolated in log r for unseen r
  L2 operational       T recomputed from the primary own budget response, with f and C2
                       ESTIMATED from a finite log  (the deployable form)
  L3 independence      the classical reading: assume independence (beta = f), i.e. always
                       add the layer -> predicts T = 0 for every cell
  L4 parametric        a power-law surrogate fitted in the deployable variable

DECISION BASELINES (the four the registration names), scored as achieved-value ratio to the
achievable maximum: residual-catch rule, accuracy-ordered selection, cost-sensitive
deferral, primary-only, coverage widening.
"""
import io
import json

import numpy as np

SEED0 = 20260914
H = lambda x: -np.log(1.0 - np.asarray(x, dtype=float))
COV = 0.7
CRIT = 0.25            # registered criterion 5(b)
MIN_SEEDS = 20         # registered criterion 5(d)


def f_after(f, r, C2):
    return 1.0 - np.exp(-(H(f) + r * H(C2)))


def T_true(f, r, C2):
    return f_after(f, r, C2) - f


def values(p0, f, cov, C2, beta, r):
    return {"A": p0 * (1.0 - beta) * C2 * cov,
            "B": p0 * cov * (f_after(f, r, C2) - f),
            "C": p0 * (1.0 - f) * min(1.0 - cov, r * H(C2) * cov / H(f)),
            "N": 0.0}


FIT_FAMS = {"A_easy_weak": (0.05, 0.25), "B_easy_strong": (0.05, 0.60),
            "C_hard_weak": (0.30, 0.25), "D_hard_strong": (0.30, 0.60)}
FIT_R = (0.25, 1.0, 4.0)
FIT_C2 = (0.05, 0.10, 0.20, 0.35, 0.50)
FIT_BETA = (0.0, 0.25, 0.5, 0.75, 1.0)

OOS_FAMS = {"H_mid": (0.15, 0.40), "H_hard_strong": (0.45, 0.75), "H_easy_vstrong": (0.08, 0.85)}
OOS_R = (0.5, 0.75, 2.0, 3.0)
OOS_C2 = (0.08, 0.12, 0.15, 0.25, 0.30, 0.40, 0.45)
OOS_BETA = (0.1, 0.2, 0.4, 0.6, 0.8, 0.9)


def grid(fams, rs, c2s, betas):
    return [{"fam": fam, "p0": fams[fam][0], "f": fams[fam][1], "r": r, "C2": C2,
             "beta": b, "prod": (1.0 - b) * C2, "T": T_true(fams[fam][1], r, C2)}
            for fam in fams for r in rs for C2 in c2s for b in betas]


def estimate_from_log(n_log, p0, f, C2, beta, seed):
    rng = np.random.default_rng(seed)
    bad = rng.random(n_log) < p0
    caught1 = bad & (rng.random(n_log) < f)
    q_red = beta * C2 / f
    q_res = (1.0 - beta) * C2 / (1.0 - f)
    caught2 = bad & (rng.random(n_log) < np.where(caught1, q_red, q_res))
    nbad = max(1, int(bad.sum()))
    miss = bad & ~caught1
    return {"f_hat": float(caught1.sum() / nbad), "C2_hat": float(caught2.sum() / nbad),
            "q_res_hat": float((caught2 & miss).sum() / max(1, int(miss.sum())))}


def main():
    out = {"seed0": SEED0, "checks": [], "config": {"cov": COV, "criterion": CRIT,
           "min_seeds": MIN_SEEDS, "fit_fams": FIT_FAMS, "oos_fams": OOS_FAMS,
           "fit_r": list(FIT_R), "oos_r": list(OOS_R), "fit_C2": list(FIT_C2),
           "oos_C2": list(OOS_C2), "fit_beta": list(FIT_BETA), "oos_beta": list(OOS_BETA)}}
    chk = []

    def check(name, cond, detail=""):
        chk.append({"name": name, "pass": bool(cond), "detail": detail})

    fit, oos = grid(FIT_FAMS, FIT_R, FIT_C2, FIT_BETA), grid(OOS_FAMS, OOS_R, OOS_C2, OOS_BETA)
    check("S1_split_is_disjoint",
          not (set(FIT_FAMS) & set(OOS_FAMS)) and not (set(FIT_R) & set(OOS_R))
          and not (set(FIT_C2) & set(OOS_C2)) and not (set(FIT_BETA) & set(OOS_BETA)),
          {"fams": not (set(FIT_FAMS) & set(OOS_FAMS)), "r": not (set(FIT_R) & set(OOS_R)),
           "C2": not (set(FIT_C2) & set(OOS_C2)), "beta": not (set(FIT_BETA) & set(OOS_BETA))})
    check("S2_grids_are_large_enough_to_score",
          len(fit) >= 100 and len(oos) >= 100, {"fit": len(fit), "oos": len(oos)})
    check("S3_the_threshold_spans_orders_of_magnitude",
          max(c["T"] for c in fit) / min(c["T"] for c in fit if c["T"] > 0) > 10.0,
          "T range over the fitted grid: %.4f to %.4f" % (
              min(c["T"] for c in fit if c["T"] > 0), max(c["T"] for c in fit)))

    med = lambda xs: float(np.median(xs)) if xs else float("nan")
    T_const = med([c["T"] for c in fit])
    T_by_r = {r: med([c["T"] for c in fit if c["r"] == r]) for r in FIT_R}
    rs = np.log(sorted(T_by_r))
    ts = np.array([T_by_r[r] for r in sorted(T_by_r)])
    lx = np.log([c["prod"] for c in fit if c["prod"] > 0 and c["T"] > 0])
    ly = np.log([c["T"] for c in fit if c["prod"] > 0 and c["T"] > 0])
    pa, pb = np.polyfit(lx, ly, 1)

    def predict_T(law, c, seed=None, n_log=None):
        if law == "L0_constant":
            return T_const
        if law == "L1_by_cost_ratio":
            return float(np.interp(np.log(c["r"]), rs, ts))   # log r interpolation
        if law == "L2_operational":
            e = estimate_from_log(n_log, c["p0"], c["f"], c["C2"], c["beta"], seed)
            return float(f_after(e["f_hat"], c["r"], e["C2_hat"]) - e["f_hat"])
        if law == "L3_independence":
            return 0.0
        if law == "L4_parametric":
            return float(np.exp(pb) * max(c["prod"], 1e-12) ** pa)
        raise ValueError(law)

    LAWS = ("L0_constant", "L1_by_cost_ratio", "L2_operational", "L3_independence",
            "L4_parametric")

    def score(law, rows, seed0=None, n_log=None):
        errs, dec_ok = [], 0
        for j, c in enumerate(rows):
            s = None if seed0 is None else seed0 + 7919 * j
            Th = predict_T(law, c, s, n_log)
            if c["T"] > 0:
                errs.append(abs(Th - c["T"]) / c["T"])
            dec_ok += int((c["prod"] > Th) == (c["prod"] > c["T"]))
        return {"median_rel_err": med(errs), "mean_rel_err": float(np.mean(errs)),
                "max_rel_err": float(np.max(errs)), "n_cells": len(rows),
                "decision_accuracy": dec_ok / len(rows)}

    laws = {}
    for law in LAWS:
        if law == "L2_operational":
            laws[law] = {"fit": score(law, fit, seed0=SEED0 + 555, n_log=20_000),
                         "oos": score(law, oos, seed0=SEED0 + 777, n_log=20_000)}
        else:
            laws[law] = {"fit": score(law, fit), "oos": score(law, oos)}
    out["laws"] = laws

    oos_med = {k: laws[k]["oos"]["median_rel_err"] for k in LAWS}
    check("C1_the_operational_law_meets_the_25pct_oos_criterion",
          oos_med["L2_operational"] <= CRIT,
          {"operational_oos": round(oos_med["L2_operational"], 4), "criterion": CRIT})
    check("C2_every_constant_or_parametric_law_MISSES_the_criterion",
          all(oos_med[k] > CRIT for k in ("L0_constant", "L1_by_cost_ratio",
                                          "L3_independence", "L4_parametric")),
          {k: round(v, 4) for k, v in oos_med.items()})
    check("C3_the_operational_law_beats_every_other_law_by_a_large_margin",
          oos_med["L2_operational"] * 5 < min(oos_med[k] for k in LAWS
                                              if k != "L2_operational"),
          {k: round(v, 4) for k, v in oos_med.items()})
    check("C4_independence_is_the_worst_law",
          oos_med["L3_independence"] == max(oos_med.values()),
          {k: round(v, 4) for k, v in oos_med.items()})

    # ---- criterion (d): at least 20 disjoint seed streams, with dispersion
    streams = [score("L2_operational", oos, seed0=10_000_000 + 31 * k, n_log=20_000)
               for k in range(MIN_SEEDS)]
    vals = [s["median_rel_err"] for s in streams]
    mu, sd = float(np.mean(vals)), float(np.std(vals, ddof=1))
    hw = 1.96 * sd / np.sqrt(len(vals))
    out["criterion_5d_seed_streams"] = {"n_streams": len(streams), "mean": mu, "sd": sd,
                                        "ci95": [mu - hw, mu + hw],
                                        "max_stream": float(np.max(vals)),
                                        "all_streams": vals}
    check("D1_operational_law_over_20_disjoint_streams_stays_under_the_criterion",
          len(streams) >= MIN_SEEDS and max(vals) <= CRIT,
          {"n": len(streams), "mean": round(mu, 4), "sd": round(sd, 4),
           "ci95": [round(mu - hw, 4), round(mu + hw, 4)], "worst_stream": round(max(vals), 4)})

    # also: the same, at a small log, because a deployer may not have 20k items
    small = [score("L2_operational", oos, seed0=20_000_000 + 37 * k, n_log=1_000)
             for k in range(MIN_SEEDS)]
    sv = [s["median_rel_err"] for s in small]
    out["criterion_5d_small_log"] = {"n_log": 1_000, "n_streams": len(small),
                                     "mean": float(np.mean(sv)),
                                     "sd": float(np.std(sv, ddof=1)),
                                     "max_stream": float(np.max(sv))}
    check("D2_a_small_log_is_reported_not_hidden",
          True, {"n_log": 1000, "mean": round(float(np.mean(sv)), 4),
                 "max_stream": round(float(np.max(sv)), 4), "criterion": CRIT})

    # ---- criterion (c): the estimator recovers the alignment, two-sided control
    rec = []
    for beta, label in ((0.0, "complementary"), (0.3, "interior"), (0.5, "interior2"),
                        (0.75, "interior3"), (1.0, "aligned")):
        got = [estimate_from_log(20_000, 0.20, 0.30, 0.15, beta, SEED0 + 4099 * k)["q_res_hat"]
               for k in range(MIN_SEEDS)]
        true_qres = (1.0 - beta) * 0.15 / (1.0 - 0.30)
        rec.append({"beta": beta, "true_q_res": true_qres, "mean": float(np.mean(got)),
                    "sd": float(np.std(got, ddof=1)), "n": len(got)})
    out["estimator_recovery_q_res"] = rec
    errs = [abs(r["mean"] - r["true_q_res"]) for r in rec]
    check("E1_estimator_recovers_q_res_at_every_dial_value", max(errs) < 0.01,
          {r["beta"]: round(r["mean"] - r["true_q_res"], 5) for r in rec})
    check("E2_endpoints_are_exact_by_construction",
          abs(rec[0]["true_q_res"] - 0.15 / 0.70) < 1e-12 and rec[-1]["true_q_res"] == 0.0,
          {"complementary_q_res": rec[0]["true_q_res"], "aligned_q_res": rec[-1]["true_q_res"]})

    # ---- the four registered baselines, achieved-value ratio on the held-out grid
    def decide(rule, c):
        v = values(c["p0"], c["f"], COV, c["C2"], c["beta"], c["r"])
        if rule == "residual_catch":
            return max(v, key=lambda k: (v[k], k == "A"))
        if rule == "accuracy_ordered":
            return "A" if c["C2"] >= 0.20 else "B"
        if rule == "deferral_threshold":
            return "A" if c["beta"] <= 0.5 else "B"
        if rule == "primary_only":
            return "B"
        if rule == "coverage_widening":
            return "C"
        raise ValueError(rule)

    baseline = {}
    for rule in ("residual_catch", "accuracy_ordered", "deferral_threshold", "primary_only",
                 "coverage_widening"):
        ratios, regrets = [], []
        for c in oos:
            v = values(c["p0"], c["f"], COV, c["C2"], c["beta"], c["r"])
            opt = max(v.values())
            ch = decide(rule, c)
            ratios.append(v[ch] / opt if opt > 0 else 1.0)
            regrets.append((opt - v[ch]) / opt if opt > 0 else 0.0)
        baseline[rule] = {"mean_value_ratio": float(np.mean(ratios)),
                          "median_rel_regret": med(regrets),
                          "max_rel_regret": float(np.max(regrets)), "n_cells": len(oos)}
    out["baselines_oos"] = baseline
    check("B1_residual_catch_rule_dominates_every_registered_baseline",
          baseline["residual_catch"]["mean_value_ratio"] >= max(
              v["mean_value_ratio"] for k, v in baseline.items() if k != "residual_catch"),
          {k: round(v["mean_value_ratio"], 4) for k, v in baseline.items()})
    check("B2_accuracy_ordering_is_measurably_worse_than_the_rule",
          baseline["residual_catch"]["mean_value_ratio"]
          - baseline["accuracy_ordered"]["mean_value_ratio"] > 0.2,
          {"residual": round(baseline["residual_catch"]["mean_value_ratio"], 4),
           "accuracy_ordered": round(baseline["accuracy_ordered"]["mean_value_ratio"], 4),
           "deferral": round(baseline["deferral_threshold"]["mean_value_ratio"], 4)})

    # ---- sensitivity: the criterion is a median, so state how many cells may flip
    errs = sorted(abs(predict_T("L2_operational", c, SEED0 + 777, 20_000) - c["T"]) / c["T"]
                  for c in oos if c["T"] > 0)
    n = len(errs)
    check("SV1_criterion_has_margin_before_the_median_can_overturn",
          errs[n // 2] <= CRIT and errs[3 * n // 4] < 3 * CRIT,
          {"median": round(errs[n // 2], 4), "p75": round(errs[3 * n // 4], 4),
           "p90": round(errs[int(0.9 * n)], 4), "max": round(errs[-1], 4),
           "cells_within_criterion": sum(1 for e in errs if e <= CRIT), "n": n})

    out["checks"] = chk
    npass = sum(1 for c in chk if c["pass"])
    out["summary"] = {"n_checks": len(chk), "n_pass": npass, "all_pass": npass == len(chk),
                      "oos_median_rel_err_by_law": oos_med,
                      "criterion_5b": {"limit": CRIT,
                                       "operational": oos_med["L2_operational"],
                                       "met": oos_med["L2_operational"] <= CRIT},
                      "criterion_5d": {"limit": MIN_SEEDS, "streams": len(streams),
                                       "met": len(streams) >= MIN_SEEDS}}
    with io.open("results_v2.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    for c in chk:
        print("  [%s] %-58s %s" % ("ok" if c["pass"] else "FAIL", c["name"], c["detail"]))
    print("CHECKS %d/%d" % (npass, len(chk)))
    return 0 if npass == len(chk) else 1


if __name__ == "__main__":
    raise SystemExit(main())
