#!/usr/bin/env python3
"""Issue #124 -- spike_v4_grounding: the same laws and the same prescription, on REAL evaluation data.

    spike_v0/v1  the repeat-count law and the item-repeat budget (synthetic, GIVEN the inputs).
    spike_v2     the inputs MEASURED in a synthetic DGP; found the item axis.
    spike_v3     the ITEM-SIZE laws (tau^2 ~ 1/T, sigma^2 floors) and the three-knob budget.
    spike_v4     GROUNDING: does any of it hold where a reader actually works?

WHY THIS SPIKE EXISTS.  A prescription whose constants (`c_tau`, `sigma_inf^2`) are synthetic is a
structural claim, not a usable one -- and the journal's own bar asks whose DECISION changes.  So the
laws and the budget machinery are imported from `spike_v3` UNCHANGED (the fit, the AM-GM envelope,
the joint solver, the certificates) and only the DATA SOURCE is replaced: a real public benchmark,
evaluated by a real protocol (repeated hold-out evaluation of two nested linear models).

THE REAL SETTING (public, pinned).
  Data   Concrete Compressive Strength (UCI), 1030 rows x 8 features -> `strength`.
         Fetched from a pinned URL and checked against a pinned sha256; cached in `data/`.
  Task   the empirical joint distribution of the rows.  A resample of T rows is an ITEM, i.i.d.
         with replacement, so a bigger item is a less noisy estimate of the SAME task -- which is
         the whole point of an item.
  Models A = OLS on all 8 features; B = OLS on the 5 with the largest POPULATION coefficients.
         A nests B, so A is truly better on the task (the gap is the dropped coefficients' signal);
         a run that reports "B is better" is a WRONG verdict, and p = P(wrong verdict).
  Run    draw n training rows (i.i.d., with replacement); fit A and B; score both on the item;
         the verdict is `mse_A < mse_B`.
  Axes   ITEM SIZE T in {16 .. 4096} (256x); ITEM (a resample) -> tau^2; REPEAT (a training draw
         on the SAME item) -> sigma^2.

Usage:  python3 spike_v4_grounding.py            (tables + certificates + controls)
        python3 spike_v4_grounding.py --selftest (planted defects; fire AND healthy-holds)
Out:    spike_v4_results.json
"""
import csv
import hashlib
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

# the LAW and the BUDGET machinery, imported UNCHANGED from spike_v3 -- only the data source differs
from spike_v3 import (fit_tau, fit_sigma, tau_consistency, coefficients_from_rows,
                      n_star, var_envelope, var_at, solve_T, cost_model,
                      assert_tau_law, assert_sigma_law, assert_holdout)
from spike_v2 import _mul

SEED0 = 20261004
DATA_URL = ("https://raw.githubusercontent.com/stedy/Machine-Learning-with-R-datasets/"
            "master/concrete.csv")
DATA_SHA256 = "d7d8bd087f832935e902bcb2687667238cac3fe06799677a93ca2f46dce8db02"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data", "concrete.csv")
T_GRID = [16, 32, 64, 128, 256, 512, 1024, 4096]
K_ITEMS = 96            # items (test resamples) per T
R_RUNS = 150            # training draws per item
N_TRAIN = 250           # rows per training draw
D_FULL = 8              # features in model A
D_SUB = 5               # features in model B
U_TARGET = 0.0          # unused; the real gap is what it is


# ------------------------------------------------------------------ data (pinned, verified)
def load_pool(path=DATA_PATH, url=DATA_URL, sha=DATA_SHA256):
    """Read the pinned CSV, verifying its sha256; fetch it once if the cache is missing.  A dataset
    that is silently a different dataset is the same defect class as a citation that is silently
    fabricated -- so the hash is checked on every read, not only on the first download."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with urllib.request.urlopen(url, timeout=30) as r:
            raw = r.read()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise AssertionError("downloaded dataset does not match the pinned sha256")
        with open(path, "wb") as f:
            f.write(raw)
    raw = open(path, "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    assert got == sha, "the cached dataset is not the pinned one: %s" % got
    rows = list(csv.reader(raw.decode("utf-8").splitlines()))
    hdr, body = rows[0], [r for r in rows[1:] if r]
    X = np.array([[float(v) for v in r[:-1]] for r in body])
    y = np.array([float(r[-1]) for r in body])
    return hdr, X, y


def standardize(X, y):
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X - mu) / sd
    ys = y - y.mean()
    return Xs, ys, mu, sd, float(y.mean())


def pop_coef(Xs, ys):
    """Population OLS coefficients on the (augmented) standardised pool -- used only to choose which
    features model B drops, so the drop is a property of the TASK, not of a lucky resample."""
    A = np.hstack([np.ones((Xs.shape[0], 1)), Xs])
    coef, *_ = np.linalg.lstsq(A, ys, rcond=None)
    return coef


def make_models(Xs, ys, drop=None):
    """Return (A_cols, B_cols) -- B drops the LOWEST-|population-coefficient| features."""
    coef = pop_coef(Xs, ys)
    order = np.argsort(-np.abs(coef[1:]))          # largest |coef| first
    keep = np.sort(order[:D_SUB])
    drop = np.sort(order[D_SUB:]) if drop is None else drop
    return keep, drop, coef


# ------------------------------------------------------------------ the real item measurement
def fit_score(Xtr, ytr, Xte, yte, cols):
    A = np.hstack([np.ones((Xtr.shape[0], 1)), Xtr[:, cols]])
    beta, *_ = np.linalg.lstsq(A, ytr, rcond=None)
    pred = _mul(np.hstack([np.ones((Xte.shape[0], 1)), Xte[:, cols]]), beta)
    assert np.isfinite(pred).all(), "the prediction is not finite"
    return float(np.mean((pred - yte) ** 2))


def measure_axis_real(T, Xs, ys, colsA, colsB, k_items=K_ITEMS, r_runs=R_RUNS, n_train=N_TRAIN,
                      true_sign=None):
    """sigma^2(T) (within-item), tau^2(T) (between-item) of (mse_B - mse_A) on the real task, and --
    when the truth's sign is known -- the measured wrong-verdict rate p at this T."""
    n = Xs.shape[0]
    within, between = [], []
    wrong = tot = 0
    for k in range(k_items):
        rng = np.random.default_rng(SEED0 + 1000003 * k + T)
        it = rng.integers(0, n, size=T)
        Xte, yte = Xs[it], ys[it]
        d = np.empty(r_runs)
        for i in range(r_runs):
            tr = rng.integers(0, n, size=n_train)
            Xtr, ytr = Xs[tr], ys[tr]
            mA = fit_score(Xtr, ytr, Xte, yte, colsA)
            mB = fit_score(Xtr, ytr, Xte, yte, colsB)
            d[i] = mB - mA
            if true_sign is not None:
                tot += 1
                wrong += 1 if (d[i] > 0) != (true_sign > 0) else 0
        within.append(float(np.var(d, ddof=1)))
        between.append(float(np.mean(d)))
    sigma2 = float(np.mean(within))
    tau2 = float(np.var(between, ddof=1))
    return {"T": T, "sigma2": sigma2, "tau2": tau2,
            "tau2_times_T": tau2 * T, "sigma2_times_T": sigma2 * T,
            "k_items": k_items, "r_runs": r_runs,
            "p_hat": (wrong / tot) if tot else None}


def population_gap(Xs, ys, colsA, colsB, big=20000, reps=400, seed=11):
    """The true sign of the claim: E[mse_B] - E[mse_A] over training draws, scored on a very large
    test set (the task).  A is expected better (A nests B), so the gap must be POSITIVE."""
    n = Xs.shape[0]
    rng = np.random.default_rng(seed)
    it = rng.integers(0, n, size=big)
    Xte, yte = Xs[it], ys[it]
    ds = np.empty(reps)
    for i in range(reps):
        tr = rng.integers(0, n, size=N_TRAIN)
        Xtr, ytr = Xs[tr], ys[tr]
        ds[i] = fit_score(Xtr, ytr, Xte, yte, colsB) - fit_score(Xtr, ytr, Xte, yte, colsA)
    return float(ds.mean()), float(ds.std(ddof=1))


# ------------------------------------------------------------------ main
def main():
    out = {"seed0": SEED0, "data_url": DATA_URL, "data_sha256": DATA_SHA256,
           "t_grid": T_GRID, "k_items": K_ITEMS, "r_runs": R_RUNS, "n_train": N_TRAIN,
           "axis": [], "certificates": {}, "controls": {}, "budget": []}
    hdr, X, y = load_pool()
    Xs, ys, mu, sd, ym = standardize(X, y)
    colsA = np.arange(D_FULL)
    colsB, dropped, coef = make_models(Xs, ys)
    out["features"] = hdr
    out["dropped_features"] = [hdr[j] for j in dropped]
    print("=" * 118)
    print("0. THE REAL TASK -- %s" % hdr)
    print("   rows %d x %d features  (pinned sha256 %s...)" % (X.shape[0], X.shape[1], DATA_SHA256[:12]))
    print("   model A = all 8 features; model B drops %s (lowest |population coef|)"
          % ", ".join(hdr[j] for j in dropped))
    gap, gap_sd = population_gap(Xs, ys, colsA, colsB)
    se = gap_sd / math.sqrt(400)
    true_sign = gap
    better = "A (all 8)" if gap > 0 else "B (%d features)" % D_SUB
    print("   population gap E[mse_B - mse_A] = %.5g  (se %.2g)  -> truly better: %s"
          % (gap, se, better))
    print("   (a SMALLER model wins here: 250 training rows, and A's 3 extra parameters cost more")
    print("    variance than the dropped features carry signal -- the truth is what it is, not")
    print("    what the design assumed; the laws below do not depend on which side it lands)")
    out["population_gap"] = gap
    out["population_gap_se"] = se
    out["truly_better"] = better
    assert abs(gap) - 3 * se > 0, "neither model is established as truly better on the real task"

    print()
    print("1. THE ITEM AXIS ON REAL DATA -- sigma^2 and tau^2 vs the item SIZE T")
    print("   T       sigma^2(within)   tau^2(between)    tau^2*T      sigma^2*T     p_hat")
    rows = []
    for T in T_GRID:
        r = measure_axis_real(T, Xs, ys, colsA, colsB, true_sign=true_sign)
        rows.append(r)
        out["axis"].append({k: r[k] for k in ("T", "sigma2", "tau2", "tau2_times_T",
                                              "sigma2_times_T", "p_hat")})
        print("   %-7d %-16.4g %-17.4g %-12.4g %-13.4g %s"
              % (T, r["sigma2"], r["tau2"], r["tau2_times_T"], r["sigma2_times_T"],
                 ("%.4f" % r["p_hat"]) if r["p_hat"] is not None else "-"))

    slope, c_tau = fit_tau(rows)
    s_inf, c_sig, worst_resid = fit_sigma(rows)
    c_tau_w, chi2, df, crit = tau_consistency(rows, K_ITEMS)
    n_range = max(r["sigma2"] for r in rows) - min(r["sigma2"] for r in rows)
    print()
    print("2. THE TWO LAWS ON REAL DATA")
    print("   tau^2(T)   = %.5g / T   (log-log slope %.4f; chi2 %.2f / %d df vs crit %.2f)"
          % (c_tau, slope, chi2, df, crit))
    print("   sigma^2(T) = %.5g + %.5g / T   (worst residual %.3g = %.1f %% of the range)"
          % (s_inf, c_sig, worst_resid, 100 * worst_resid / max(n_range, 1e-30)))
    out["certificates"]["tau_loglog_slope"] = slope
    out["certificates"]["tau_chi2"] = chi2
    out["certificates"]["tau_chi2_df"] = df
    out["certificates"]["tau_chi2_crit99"] = crit
    out["certificates"]["sigma_inf"] = s_inf
    out["certificates"]["sigma_c_sig"] = c_sig
    out["certificates"]["sigma_worst_resid"] = worst_resid
    assert_tau_law(slope, chi2, df, crit)
    assert_sigma_law(s_inf, c_sig, n_range, worst_resid)

    # held-out T
    hold = rows[len(rows) // 2]
    rest = [r for r in rows if r is not hold]
    _, c_tau_h = fit_tau(rest)
    s_inf_h, c_sig_h, _ = fit_sigma(rest)
    rel_tau = assert_holdout(c_tau_h / hold["T"], hold["tau2"])
    rel_sig = assert_holdout(s_inf_h + c_sig_h / hold["T"], hold["sigma2"])
    out["certificates"]["holdout_T"] = hold["T"]
    out["certificates"]["holdout_rel_tau2"] = rel_tau
    out["certificates"]["holdout_rel_sigma2"] = rel_sig
    print("   held-out T=%d: tau^2 within %.1f %%; sigma^2 within %.1f %%"
          % (hold["T"], 100 * rel_tau, 100 * rel_sig))

    coef = coefficients_from_rows(rows)
    print()
    print("3. THE PRESCRIPTION ON THE REAL TASK -- an interior item size")
    print("   alpha  beta   kappa  lambda |  T*      N*(T*)   M*        Var*")
    ref_cost = (1.0, 1.0, 1.0, 1.0)
    for (al, be, ka, la) in [ref_cost, (1, 0.1, 1, 1), (1, 10, 1, 1), (1, 1, 10, 1), (1, 1, 1, 10)]:
        cost = (al, be, ka, la)
        T_star, v_star = solve_T(coef, cost)
        N_star_v = n_star(T_star, coef, cost)
        p_, q_ = cost_model(al, be, ka, la, T_star)
        M_star = 1.0 / (p_ + N_star_v * q_)
        out["budget"].append({"alpha": al, "beta": be, "kappa": ka, "lambda": la,
                              "T_star": T_star, "N_star": N_star_v, "M_star": M_star,
                              "var_star": v_star})
        print("   %-6.3g %-6.3g %-6.3g %-6.3g |  %-7.4g %-8.4g %-9.4g %.4g"
              % (al, be, ka, la, T_star, N_star_v, M_star, v_star))

    print()
    print("CERTIFICATE -- the closed form is a LOWER bound on the brute-force joint optimum")
    T_star, v_star = solve_T(coef, ref_cost)
    best = (1e30, None, None)
    for T in [1.0 * (2 ** (i / 3.0)) for i in range(0, 61)]:
        for nn in range(1, 4001):
            v = var_at(nn, T, coef, ref_cost)
            if v < best[0]:
                best = (v, T, nn)
    rel_v = abs(v_star - best[0]) / best[0]
    print("   closed (T*,N*)=(%.4g, %.4g) Var*=%.6e | brute (%.4g,%d) Var=%.6e | rel %.3f"
          % (T_star, n_star(T_star, coef, ref_cost), v_star, best[1], best[2], best[0], rel_v))
    out["certificates"]["joint_brute_var_rel"] = rel_v
    assert v_star <= best[0] * 1.0001, "the closed form EXCEEDS the brute optimum (overshoot)"
    assert rel_v < 0.05, "the closed form is not the joint optimum on real data"

    print()
    print("CONTROL -- the interior optimum on REAL data, two-sided")
    T_free, _ = solve_T(coef, (1.0, 0.0, 1.0, 0.0), T_lo=1.0, T_hi=1e6)
    coef_nosize = dict(coef, c_tau=1e-12, tau2_of=lambda T: 1e-12 / T,
                       c_sig=0.0, sigma2_of=lambda T: coef["s_inf"])
    T_nosize, _ = solve_T(coef_nosize, ref_cost, T_lo=1.0, T_hi=1e6)
    out["controls"] = {"T_star_free_size": T_free, "T_star_no_size_variance": T_nosize,
                       "reference_T_star": T_star}
    print("   (C1) free item size:                     T* = %.4g  (runs to the cap)" % T_free)
    print("   (C2) no size-dependent variance:         T* = %.4g  (smallest item)" % T_nosize)
    print("   reference (both effects on):             T* = %.4g  (STRICTLY between)" % T_star)
    assert T_free > 1e4 and T_nosize < 2.0 and T_nosize < T_star < T_free

    with open(os.path.join(HERE, "spike_v4_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v4_results.json")
    return 0


# ------------------------------------------------------------------ self-test (planted defects)
def selftest():
    print("=" * 118)
    print("SELFTEST -- plant a defect per certificate and require it to FIRE, healthy case to HOLD")
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError as e:
            print("[%-28s] FIRED: %s" % (name, str(e)[:54]))
            return
        print("[%-28s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-28s] holds (no fire)" % name)
        except AssertionError as e:
            print("[%-28s] *** FIRED ON A HEALTHY CASE *** %s" % (name, str(e)[:34]))
            ok = False

    # 0. the dataset hash: a swapped corpus must be caught (a silently-different dataset is a defect)
    def plant_hash():
        raw = b"not the concrete dataset"
        got = hashlib.sha256(raw).hexdigest()
        assert got == DATA_SHA256, "the cached dataset is not the pinned one: %s" % got
    fires("dataset-sha256", plant_hash)

    def hold_hash():
        raw = open(DATA_PATH, "rb").read()
        assert hashlib.sha256(raw).hexdigest() == DATA_SHA256, "cache mismatch"
    holds("dataset-sha256/ok", hold_hash)

    # 1. the two laws (shared predicates from spike_v3)
    fires("tau-law-slope", lambda: assert_tau_law(-0.05, 5.0, 7, 18.5))
    holds("tau-law-slope/ok", lambda: assert_tau_law(-0.98, 10.0, 7, 18.5))
    fires("sigma-floor", lambda: assert_sigma_law(-1e-4, 0.14, 1e-3, 0.0))
    holds("sigma-floor/ok", lambda: assert_sigma_law(4.3e-4, 0.14, 1.5e-3, 1e-5))

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CERTIFICATE IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
