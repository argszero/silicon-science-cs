#!/usr/bin/env python3
"""
issue #44 -- instrument_v3.py
"Is the derived rule better than the best constant threshold -- and by how much?"

REGISTERED CRITERION (c), quoted from the registration:
    "(c) the derived rule compared against the best constant threshold matched to zero
     honest rejections and reported as a factor with confidence intervals -- if it is
     not better, that is reported as unmet with the reason"

OPERATIONALISATION (frozen before the deciding run).  A first run of this instrument
had three broken CONTROLS -- not a changed criterion; the repairs are itemised in
notes_v3.md (a mis-AIMED direction control, an identity check given the wrong error
budget, and a multiplicity-naive match check).

  Honest node N(0, sigma_h), sigma_h = 1 (the derived rule carries sigma_h as a pure
  scale factor).  The sample mean of k draws is exactly N(delta, sigma_h/sqrt(k)).

  CONSTANT RULE -- the antecedent's own baseline, named by the registration's
  Baselines item (i) as "the best constant threshold matched to zero honest
  rejections".  Constant thresholds that reject no calibration execution are exactly
  those above the largest honest calibration sample mean, so the best of them is

        tau_c = max of n_cal honest sample means     (0 / n_cal rejections, exactly)

  DERIVED RULE -- the construct's threshold at the same false-positive budget:

        tau_d = c* * sigma_h / sqrt(k),   c* = Phi^-1(1 - 1/(n_cal+1))

  MATCHING: the max of n_cal iid draws exceeds exactly 1/(n_cal+1) of the honest
  distribution IN EXPECTATION (order-statistic symmetry, exact for any continuous
  law), so the constant rule's expected false-positive rate on fresh honest data is
  1/(n_cal+1); c* matches the derived rule to it.  That the match holds is a CONTROL
  (K1) measured on fresh data, not an assumption.

  FACTOR: ratio of the two rules' MEAN powers (ratio of expectations -- the rules'
  true detection rates), 95 % CI by the delta method with the PAIRED covariance from
  common random numbers.  A mean of per-stream ratios is NOT the estimand (it is
  dominated by streams whose denominator is near zero) -- the first run showed this
  as CIs of width +/-300 %; the ratio of means fixes it.

  GRID: margins in standard-error units, delta = lam * sigma_h/sqrt(k), because the
  informative comparison is set by the threshold's own scale:
  lam in {1,2,3,4}, k in {4,16,64}, n_cal in {5,20,100,1000} -> 48 cells.

  INFORMATIVE CELL: the derived rule's construct power in (0.01, 0.99).  Outside it
  both rules are 0 or both 1 and the comparison can be neither won nor lost.

  PRIMARY CRITERION (faithful to the registered wording, whose only ground for
  "unmet" is the derived rule NOT BEING BETTER):
     (i)  the derived rule's mean power exceeds the constant rule's in a significant
          majority of informative cells (one-sided sign test, p < 0.05), AND
     (ii) no informative cell shows the constant rule significantly better
          (paired-difference CI entirely below zero).
  SECONDARY, STRICTER READING (pre-declared here, reported whether or not it passes):
  the factor's 95 % CI lower bound exceeds 1 in EVERY informative cell; reported as
  unmet with the reason if it fails.

  MECHANISM, as a countable statistic: the standardised threshold gap
        g = (tau_c - tau_d) / (sigma_h / sqrt(k))
  MECHANISM, corrected at R313 (the first version of this block is documented in
  the code below, where it was replaced).  Does the mean gap g ORDER the factor?
  Measured order-free, over every unordered pair of informative cells whose mean gaps
  differ by more than GAP_TOL and oriented by the gap: yes, in ~92 % of compared pairs
  (tau-like +0.84).  What the mean gap does NOT do is DETERMINE the factor's
  magnitude -- inside a gap quartile the factor still spreads by up to 0.46 -- because
  power is a nonlinear function of the threshold.  The mechanism the instrument
  therefore tests is the whole DISTRIBUTION of tau_c (Jensen), and it predicts
        E[power_constant] = E_{tau_c}[ Phi((delta - tau_c)/se) ],  se = sigma_h/sqrt(k)
  and scores the measurement against it (K4).

CONTROLS
  K1 matched budget: on fresh honest streams, |measured - 1/(n_cal+1)| <= 4 SE for
     both rules.  The band is 4 SE, not a 95 % interval, because ~96 simultaneous
     95 % checks are expected to fail ~5 times by chance; max |z| is reported.
  K2 the sample-mean identity: the fast drawer (one draw from N(delta,sigma/sqrt(k)))
     must reproduce the slow drawer (k raw draws) on the DRAWER's own moments and on
     a fixed-threshold rejection rate -- calibration variance is excluded from this
     check, because re-drawing tau_c per path swamps the identity being tested (the
     first run's error).
  K3 direction control, TWO-SIDED: a derived threshold placed WORSE than the constant
     rule (1.5 c*, higher) must give factor < 1; a threshold placed better but at an
     unmatched budget (0.5 c*, lower) must give factor > 1.  The first run aimed the
     control only in the "better" direction and therefore tested nothing.
  K4 mechanism: the measured mean power of the constant rule must agree with the
     construct's E_{tau_c}[Phi((delta - tau_c)/se)] within 4 between-stream SE.

Pure stdlib. Deterministic. No timing/date field in the artefact (the R241 lesson).
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


SIGMA_H = 1.0
N_CAL_GRID = [5, 20, 100, 1000]
K_GRID = [4, 16, 64]
LAM_GRID = [1.0, 2.0, 3.0, 4.0]
N_MC = 12000
N_STREAMS = 41
GAP_TOL = 0.05           # two cells' mean gaps are compared only if they differ by more than this
T_975_DF40 = 2.021      # two-sided 95 % t quantile at df = 40
Z_TOL = 4.0             # multiplicity-aware band for the match checks


def c_star(n_cal):
    return phi_inv(1.0 - 1.0 / (n_cal + 1.0))


def predicted_power_derived(lam, n_cal):
    return phi(lam - c_star(n_cal))


def seed_for(*parts):
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


def draw_mean(r, delta, sigma, k):
    """Sample mean of k draws, drawn EXACTLY: N(delta, sigma/sqrt(k))."""
    return r.gauss(delta, sigma / math.sqrt(k))


def draw_mean_slow(r, delta, sigma, k):
    s = 0.0
    for _ in range(k):
        s += r.gauss(delta, sigma)
    return s / k


def draw_max_of_n(r, n):
    """Exact draw of the max of n iid standard normals: invert F^n."""
    u = r.random()
    return phi_inv(u ** (1.0 / n))


def binom_sf(k, n, p=0.5):
    """P(X >= k) for X ~ Binomial(n, p)."""
    tot = 0.0
    for i in range(k, n + 1):
        tot += math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
    return tot


# ---------------------------------------------------------------- statistics
def mean_sd_ci(vals, t=T_975_DF40):
    m = statistics.fmean(vals)
    if len(vals) < 2:
        return {"mean": m, "sd": 0.0, "se": 0.0, "ci_lo": m, "ci_hi": m}
    sd = statistics.stdev(vals)
    se = sd / math.sqrt(len(vals))
    return {"mean": m, "sd": sd, "se": se, "ci_lo": m - t * se, "ci_hi": m + t * se,
            "per_stream": vals}


def paired_diff_ci(a, b, t=T_975_DF40):
    d = [x - y for x, y in zip(a, b)]
    m = statistics.fmean(d)
    if len(d) < 2:
        return {"mean": m, "sd": 0.0, "se": 0.0, "ci_lo": m, "ci_hi": m}
    sd = statistics.stdev(d)
    se = sd / math.sqrt(len(d))
    return {"mean": m, "sd": sd, "se": se, "ci_lo": m - t * se, "ci_hi": m + t * se,
            "per_stream": d}


def ratio_of_means_ci(a, b, t=T_975_DF40):
    """The factor = ratio of the two rules' MEAN powers, with a delta-method CI that
    keeps the paired covariance (the two rules are scored on the same draws).

        Var(a/b)/(a/b)^2 = Va/a^2 + Vb/b^2 - 2 Cov(a,b)/(a b)
    """
    a = list(a)
    b = list(b)
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    if ma <= 0.0 or mb <= 0.0:
        return {"mean": None, "ci_lo": None, "ci_hi": None,
                "note": "non-positive mean power: the factor is undefined"}
    n = len(a)
    var_a = statistics.variance(a) / n
    var_b = statistics.variance(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (n - 1) / n
    rel = var_a / (ma * ma) + var_b / (mb * mb) - 2.0 * cov / (ma * mb)
    rel = max(rel, 0.0)
    f = ma / mb
    half = t * f * math.sqrt(rel)
    return {"mean": f, "rel_se": math.sqrt(rel), "half_width": half,
            "ci_lo": f - half, "ci_hi": f + half,
            "mean_power_derived": ma, "mean_power_constant": mb,
            "covariance_share": cov / (ma * mb)}


# ---------------------------------------------------------------- one stream
def run_stream(n_cal, k, lam, stream, n_mc, tag, tau_d_scale=1.0):
    """One independent stream: its own calibration set, its own evaluation draws.

    tau_d_scale is the K3 hook: 1.0 is the derived rule; other values deliberately
    mis-place it (a WORSE rule has a scale above 1, since a higher threshold rejects
    less)."""
    se = SIGMA_H / math.sqrt(k)
    delta = lam * se
    tau_d = tau_d_scale * c_star(n_cal) * se
    r_cal = random.Random(seed_for(tag, "cal", n_cal, k, lam, stream))
    tau_c = max(draw_mean(r_cal, 0.0, SIGMA_H, k) for _ in range(n_cal))

    r_hon = random.Random(seed_for(tag, "hon", n_cal, k, lam, stream))
    fpr_d = fpr_c = 0
    for _ in range(n_mc):
        x = draw_mean(r_hon, 0.0, SIGMA_H, k)
        if x > tau_d:
            fpr_d += 1
        if x > tau_c:
            fpr_c += 1

    r_div = random.Random(seed_for(tag, "div", n_cal, k, lam, stream))
    pow_d = pow_c = 0
    for _ in range(n_mc):
        x = draw_mean(r_div, delta, SIGMA_H, k)
        if x > tau_d:
            pow_d += 1
        if x > tau_c:
            pow_c += 1

    return {"tau_d": tau_d, "tau_c": tau_c,
            "fpr_d": fpr_d / float(n_mc), "fpr_c": fpr_c / float(n_mc),
            "power_d": pow_d / float(n_mc), "power_c": pow_c / float(n_mc)}


# ---------------------------------------------------------------- run
def run():
    out = {"sigma_h": SIGMA_H, "n_cal_grid": N_CAL_GRID, "k_grid": K_GRID,
           "lam_grid": LAM_GRID, "n_mc": N_MC, "n_streams": N_STREAMS,
           "t_975_df40": T_975_DF40, "z_tol": Z_TOL}

    # ---- the construct's prediction of the constant rule's power and of the factor
    # E[tau_c] and E[power_c] come from the max-of-n distribution drawn EXACTLY
    # (F^n inversion), so the prediction is cheap and parameter-free.
    pred_table = {}
    for n_cal in N_CAL_GRID:
        r = random.Random(seed_for("pred", n_cal))
        draws = [draw_max_of_n(r, n_cal) for _ in range(40000)]
        emax = statistics.fmean(draws)
        for k in K_GRID:
            se = SIGMA_H / math.sqrt(k)
            for lam in LAM_GRID:
                delta = lam * se
                epc = statistics.fmean([phi((delta - m * se) / se) for m in draws])
                key = "n%d_k%d_l%d" % (n_cal, k, int(lam))
                pred_table[key] = {
                    "E_max_standard_normal": emax,
                    "c_star": c_star(n_cal),
                    "g_pred": emax - c_star(n_cal),
                    "expected_fpr": 1.0 / (n_cal + 1.0),
                    "power_constant_predicted": epc,
                    "power_derived_predicted": predicted_power_derived(lam, n_cal),
                    "factor_predicted": (predicted_power_derived(lam, n_cal) / epc)
                    if epc > 0 else None,
                    "jensen_note": "E[Phi((delta-tau)/se)] != Phi((delta-E[tau])/se)",
                }
    out["construct_prediction"] = pred_table

    # ---- the grid
    cells = {}
    for n_cal in N_CAL_GRID:
        for k in K_GRID:
            for lam in LAM_GRID:
                st = [run_stream(n_cal, k, lam, s, N_MC, "grid") for s in range(N_STREAMS)]
                pdv = [s["power_d"] for s in st]
                pcv = [s["power_c"] for s in st]
                pow_d = mean_sd_ci(pdv)
                pow_c = mean_sd_ci(pcv)
                f = ratio_of_means_ci(pdv, pcv)
                pdiff = paired_diff_ci(pdv, pcv)
                fpr_d = mean_sd_ci([s["fpr_d"] for s in st])
                fpr_c = mean_sd_ci([s["fpr_c"] for s in st])
                g = mean_sd_ci([(s["tau_c"] - s["tau_d"]) / (SIGMA_H / math.sqrt(k))
                                for s in st])
                p_hat = predicted_power_derived(lam, n_cal)
                key = "n%d_k%d_l%d" % (n_cal, k, int(lam))
                pr = pred_table[key]
                cells[key] = {
                    "n_cal": n_cal, "k": k, "lam": lam,
                    "delta": lam * SIGMA_H / math.sqrt(k),
                    "predicted_power_derived": p_hat,
                    "informative": bool(0.01 < p_hat < 0.99),
                    "power_derived": pow_d, "power_constant": pow_c,
                    "factor": f, "paired_power_difference": pdiff,
                    "fpr_derived": fpr_d, "fpr_constant": fpr_c,
                    "expected_fpr": 1.0 / (n_cal + 1.0),
                    "standardised_threshold_gap": g,
                    "g_pred": pr["g_pred"],
                    "power_constant_predicted": pr["power_constant_predicted"],
                    "factor_predicted": pr["factor_predicted"],
                }
    out["cells"] = cells

    # ---- K1 matched budget, at a multiplicity-aware band
    k1 = []
    for key, c in sorted(cells.items()):
        exp_fpr = c["expected_fpr"]
        for which in ("derived", "constant"):
            m = c["fpr_" + which]
            se = m["se"] if m["se"] > 0 else float("nan")
            z = (m["mean"] - exp_fpr) / se if se and se == se and se > 0 else 0.0
            k1.append({"cell": key, "rule": which, "fpr": m["mean"], "expected": exp_fpr,
                       "se": m["se"], "z": z, "matched": abs(z) <= Z_TOL})
    out["K1_matched_budget"] = k1
    out["K1_ok"] = all(r["matched"] for r in k1)
    out["K1_n_checks"] = len(k1)
    out["K1_n_unmatched"] = sum(1 for r in k1 if not r["matched"])
    out["K1_max_abs_z"] = max(abs(r["z"]) for r in k1)
    out["K1_worst"] = sorted(k1, key=lambda r: -abs(r["z"]))[:5]

    # ---- K2 the sample-mean identity, on the DRAWER's own moments
    k2 = []
    n_id = 12000
    for (n_cal, k, lam) in [(5, 4, 2.0), (20, 16, 2.0), (100, 64, 3.0)]:
        se = SIGMA_H / math.sqrt(k)
        delta = lam * se
        tau_fixed = c_star(n_cal) * se
        rf = random.Random(seed_for("k2fast", n_cal, k, lam))
        rs = random.Random(seed_for("k2slow", n_cal, k, lam))
        fv = [draw_mean(rf, delta, SIGMA_H, k) for _ in range(n_id)]
        sv = [draw_mean_slow(rs, delta, SIGMA_H, k) for _ in range(n_id)]
        se_mean = SIGMA_H / math.sqrt(k * n_id)
        sd_pred = SIGMA_H / math.sqrt(k)
        se_sd = sd_pred / math.sqrt(2.0 * n_id)
        rej_f = sum(1 for x in fv if x > tau_fixed) / float(n_id)
        rej_s = sum(1 for x in sv if x > tau_fixed) / float(n_id)
        p_ref = phi(lam - c_star(n_cal))
        se_rej = math.sqrt(2.0 * max(p_ref * (1.0 - p_ref), 1e-9) / n_id)
        k2.append({
            "n_cal": n_cal, "k": k, "lam": lam, "n_draws": n_id,
            "mean_fast": statistics.fmean(fv), "mean_slow": statistics.fmean(sv),
            "mean_diff": statistics.fmean(fv) - statistics.fmean(sv),
            "se_mean": se_mean,
            "sd_fast": statistics.stdev(fv), "sd_slow": statistics.stdev(sv),
            "sd_pred": sd_pred, "se_sd": se_sd,
            "rej_fast": rej_f, "rej_slow": rej_s, "se_rej": se_rej,
            "ok_mean": abs(statistics.fmean(fv) - statistics.fmean(sv)) <= 4.0 * se_mean,
            "ok_sd": abs(statistics.stdev(fv) - SIGMA_H / math.sqrt(k)) <= 4.0 * se_sd
            and abs(statistics.stdev(sv) - SIGMA_H / math.sqrt(k)) <= 4.0 * se_sd,
            "ok_rej": abs(rej_f - rej_s) <= 4.0 * se_rej,
        })
        k2[-1]["ok"] = k2[-1]["ok_mean"] and k2[-1]["ok_sd"] and k2[-1]["ok_rej"]
    out["K2_sample_mean_identity"] = k2
    out["K2_ok"] = all(r["ok"] for r in k2)

    # ---- K3 direction control, two-sided
    k3 = []
    for (n_cal, k, lam) in [(5, 16, 2.0), (20, 16, 2.0), (100, 16, 3.0), (1000, 64, 2.0)]:
        arms = {}
        for label, scale in (("worse_1.5c", 1.5), ("better_0.5c", 0.5)):
            st = [run_stream(n_cal, k, lam, s, N_MC, "K3" + label, tau_d_scale=scale)
                  for s in range(9)]
            f = ratio_of_means_ci([s["power_d"] for s in st], [s["power_c"] for s in st])
            arms[label] = {"factor": f["mean"], "ci_lo": f["ci_lo"], "ci_hi": f["ci_hi"]}
        k3.append({"n_cal": n_cal, "k": k, "lam": lam, "arms": arms,
                   "fires_worse": arms["worse_1.5c"]["factor"] < 1.0,
                   "fires_better": arms["better_0.5c"]["factor"] > 1.0})
    out["K3_direction_control"] = k3
    out["K3_ok"] = all(r["fires_worse"] and r["fires_better"] for r in k3)

    # ---- K4 the mechanism: the tau_c DISTRIBUTION predicts the constant rule's power
    k4 = []
    for key, c in sorted(cells.items()):
        pc_meas = c["power_constant"]
        pc_pred = c["power_constant_predicted"]
        se = pc_meas["se"] if pc_meas["se"] > 0 else float("nan")
        z = (pc_meas["mean"] - pc_pred) / se if se and se == se and se > 0 else 0.0
        k4.append({"cell": key, "power_constant_measured": pc_meas["mean"],
                   "power_constant_predicted": pc_pred, "se": pc_meas["se"], "z": z,
                   "ok": abs(z) <= Z_TOL})
    out["K4_mechanism_distribution"] = k4
    out["K4_ok"] = all(r["ok"] for r in k4)
    out["K4_max_abs_z"] = max(abs(r["z"]) for r in k4)
    out["K4_n_unmatched"] = sum(1 for r in k4 if not r["ok"])

    # ---- MECHANISM: does the mean standardised threshold gap ORDER the factor?
    #
    # CORRECTED at R313.  The first version of this block counted pairs
    # (gap_i, gap_j) in the order the cells dict happened to be built, required
    # gap_j - gap_i > 0.05, counted factor_j < factor_i as a "concordant" pair, and
    # called the mechanism refuted when that fraction fell below 0.9.  Two defects,
    # both found only by RECOMPUTING the statistic from the committed artefact:
    #   (1) the pairs were taken in dict-iteration order, so the recorded count is
    #       NOT reproducible from the artefact -- json.dump(sort_keys=True) does not
    #       preserve build order, and re-deriving from the artefact gave 366 pairs
    #       where the original run reported 194;
    #   (2) the verdict rule was inverted.  A pair in which the factor FALLS as the
    #       gap RISES is evidence AGAINST the ordering; a low fraction of such pairs
    #       is evidence FOR it, not against it.  The recorded verdict "refuted" was
    #       therefore the opposite of what its own statistic said.
    # The block below is order-free: every unordered pair of informative cells whose
    # mean gaps differ by more than GAP_TOL is oriented by the gap, and only then is
    # the factor compared.
    pairs = []
    for key, c in sorted(cells.items()):
        f = c["factor"]
        if c["informative"] and f.get("mean") is not None and math.isfinite(f["mean"]):
            pairs.append((c["standardised_threshold_gap"]["mean"], f["mean"], key))
    rises = falls = 0
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            if abs(pairs[j][0] - pairs[i][0]) <= GAP_TOL:
                continue
            lo, hi = (i, j) if pairs[i][0] < pairs[j][0] else (j, i)
            if pairs[hi][1] > pairs[lo][1]:
                rises += 1
            elif pairs[hi][1] < pairs[lo][1]:
                falls += 1
    compared = rises + falls
    tau_like = ((rises - falls) / float(compared)) if compared else None
    ordered = sorted(pairs)
    quartiles = []
    for b in range(4):
        chunk = ordered[b * len(ordered) // 4:(b + 1) * len(ordered) // 4]
        fs = [c[1] for c in chunk]
        quartiles.append({"gap_lo": chunk[0][0], "gap_hi": chunk[-1][0],
                          "n": len(chunk), "factor_min": min(fs), "factor_max": max(fs),
                          "factor_spread": max(fs) - min(fs)})
    out["mechanism_gap_ordering"] = {
        "statistic": ("every unordered pair of informative cells whose mean standardised "
                      "threshold gaps differ by more than %.2f, oriented by the gap"
                      % GAP_TOL),
        "order_free": True,
        "pairs_compared": compared, "factor_rises_with_gap": rises,
        "factor_falls_with_gap": falls, "tau_like": tau_like,
        "verdict": ("the mean gap ORDERS the factor"
                    if (tau_like is not None and tau_like > 0.5)
                    else "the mean gap does not order the factor"),
        "ordering_is_not_determination": {
            "gap_quartiles": quartiles,
            "max_factor_spread_inside_a_quartile":
                max(q["factor_spread"] for q in quartiles)}}
    out["mechanism_correct_is_distribution"] = {
        "max_abs_z": out["K4_max_abs_z"], "n_unmatched": out["K4_n_unmatched"],
        "verdict": "holds" if out["K4_ok"] else "fails",
        "why": "power is a NONLINEAR function of the threshold, so the MAGNITUDE of the "
               "loss is carried by the whole distribution of tau_c, not by its mean "
               "(Jensen: E[Phi((delta - tau_c)/se)] != Phi((delta - E[tau_c])/se))."}

    # ---- PRIMARY criterion (registered wording): is the derived rule BETTER?
    inf = [(key, c) for key, c in sorted(cells.items()) if c["informative"]]
    pos = [k for k, c in inf if c["paired_power_difference"]["mean"] > 0]
    significantly_worse = [k for k, c in inf
                           if c["paired_power_difference"]["ci_hi"] < 0.0]
    significantly_better = [k for k, c in inf
                            if c["paired_power_difference"]["ci_lo"] > 0.0]
    sign_p = binom_sf(len(pos), len(inf))
    out["criterion_c"] = {
        "n_informative_cells": len(inf),
        "n_cells_derived_better": len(pos),
        "n_cells_constant_better": len(inf) - len(pos),
        "sign_test_p_one_sided": sign_p,
        "cells_derived_significantly_better": significantly_better,
        "cells_constant_significantly_better": significantly_worse,
        "median_factor": statistics.median(
            [c["factor"]["mean"] for _, c in inf if c["factor"].get("mean") is not None]),
        "max_factor": max(c["factor"]["mean"] for _, c in inf
                          if c["factor"].get("mean") is not None),
        "min_factor": min(c["factor"]["mean"] for _, c in inf
                          if c["factor"].get("mean") is not None),
    }
    out["criterion_c_met"] = bool(sign_p < 0.05 and len(significantly_worse) == 0)

    # ---- SECONDARY, stricter reading: CI lower bound > 1 in EVERY informative cell
    strict_fails = []
    for key, c in inf:
        f = c["factor"]
        if f.get("mean") is None or not math.isfinite(f["mean"]):
            strict_fails.append("%s: no finite factor" % key)
        elif not (f["ci_lo"] > 1.0):
            strict_fails.append("%s: factor %.4f CI[%.4f,%.4f] low bound <= 1"
                                % (key, f["mean"], f["ci_lo"], f["ci_hi"]))
    out["criterion_c_strict_met"] = (len(strict_fails) == 0)
    out["criterion_c_strict_failures"] = strict_fails
    out["criterion_c_strict_n_failures"] = len(strict_fails)

    out["ALL_PASS"] = bool(out["criterion_c_met"] and out["K1_ok"] and out["K2_ok"]
                           and out["K3_ok"] and out["K4_ok"])
    return out


def main():
    out = run()
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "results_v3.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    cc = out["criterion_c"]
    print("wrote", dest)
    print("PRIMARY criterion (c) met:", out["criterion_c_met"],
          "| informative cells:", cc["n_informative_cells"],
          "| derived better in", cc["n_cells_derived_better"],
          "| sign-test p %.3g" % cc["sign_test_p_one_sided"])
    print("   factor: min %.4f median %.4f max %.4f"
          % (cc["min_factor"], cc["median_factor"], cc["max_factor"]))
    print("   significantly better %d ; significantly WORSE %d"
          % (len(cc["cells_derived_significantly_better"]),
             len(cc["cells_constant_significantly_better"])))
    print("SECONDARY strict reading met:", out["criterion_c_strict_met"],
          "(%d/%d informative cells fail)" % (out["criterion_c_strict_n_failures"],
                                              cc["n_informative_cells"]))
    print("K1 matched budget:", out["K1_ok"], "| unmatched %d/%d | max|z| %.2f"
          % (out["K1_n_unmatched"], out["K1_n_checks"], out["K1_max_abs_z"]))
    print("K2 drawer identity:", out["K2_ok"])
    print("K3 two-sided direction control:", out["K3_ok"])
    print("K4 distribution mechanism:", out["K4_ok"],
          "| max|z| %.2f | unmatched %d" % (out["K4_max_abs_z"], out["K4_n_unmatched"]))
    mo = out["mechanism_gap_ordering"]
    print("MECHANISM (does the mean gap order the factor?):", mo["verdict"],
          "| tau-like %.4f over %d order-free pairs (rises %d, falls %d)"
          % (mo["tau_like"], mo["pairs_compared"], mo["factor_rises_with_gap"],
             mo["factor_falls_with_gap"]))
    print("   ordering is not determination: the factor still spreads %.4f inside one "
          "gap quartile"
          % mo["ordering_is_not_determination"]["max_factor_spread_inside_a_quartile"])
    print()
    print(" n_cal    k  lam  pow_d   pow_c   pow_c_pred  factor [95% CI]          diff [CI]              inf")
    for key, c in sorted(out["cells"].items(),
                         key=lambda kv: (kv[1]["n_cal"], kv[1]["k"], kv[1]["lam"])):
        f = c["factor"]
        d = c["paired_power_difference"]
        if f.get("mean") is not None and math.isfinite(f["mean"]):
            fs = "%.4f [%.4f,%.4f]" % (f["mean"], f["ci_lo"], f["ci_hi"])
        else:
            fs = "        --            "
        print(" %5d %4d %4.0f  %.4f  %.4f   %.4f    %s  %+.4f [%+.4f,%+.4f]  %s"
              % (c["n_cal"], c["k"], c["lam"], c["power_derived"]["mean"],
                 c["power_constant"]["mean"], c["power_constant_predicted"], fs,
                 d["mean"], d["ci_lo"], d["ci_hi"], "Y" if c["informative"] else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
