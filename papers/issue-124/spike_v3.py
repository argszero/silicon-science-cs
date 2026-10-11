#!/usr/bin/env python3
"""Issue #124 -- spike_v3: the ITEM-SIZE axis and the three-knob evaluation budget.

    spike_v0  the repeat-count law, exact, GIVEN p.
    spike_v1  the item-repeat budget, GIVEN (sigma^2, tau^2):  N* = sqrt(a*sigma^2/(b*tau^2)).
    spike_v2  MEASURED p, sigma^2, tau^2 in a DGP, and found the ITEM axis: the population closed
              form drops a per-test-set term whose RMS falls as N_TEST^-0.507.
    spike_v3  WHY it falls, and what follows: the item SIZE -- how many test points an item carries
              -- is a THIRD knob, because the two variances move in OPPOSITE directions with it.

THE MEASURED STRUCTURE (one fixed task; only the test set varies between items).
  An ITEM is a test set of T points drawn from the same task; a REPEAT is one training run scored
  on that item.  Two variances matter, and they are NOT the same object:

      sigma^2(T) = E_item[ Var_run( score | item ) ]   -- the within-item (training) noise
      tau^2(T)   = Var_item[ E_run( score | item ) ]   -- the between-item (test-set) spread

  Measured over T in [125, 16000]:
      ** tau^2(T)   = c_tau / T **                  (log-log slope ~ -1.0; tau^2 * T flat)
      ** sigma^2(T) = sigma_inf^2 + c_sig / T **    (a 1/T part over an irreducible floor)

  The reading is structural, not a fit accident: the between-item spread is carried by the terms
  that are FIXED BY ONE TEST SET (a finite test set is a noisy estimate of the task), so a bigger
  item averages them down; the within-item noise is carried by the TRAINING draw, whose weight
  error is common to every test point of the item, so it does not average away -- it floors.

THE THREE-KNOB BUDGET.
  Knobs: M items, N repeats per item, T points per item.  Estimator variance
      Var = tau^2(T)/M + sigma^2(T)/(M*N),
  budget  B = M*(p(T) + N*q(T)),  p(T) = alpha + beta*T  (item cost),  q(T) = kappa + lambda*T
  (a run's cost grows with T: a run is scored on the whole item).  Two exact reductions:

      (1) for FIXED T the budget-optimal repeat count is  N*(T) = sqrt( sigma^2(T) p(T) / (tau^2(T) q(T)) )
          -- spike_v1's law with a = p(T), b = q(T): the repeat count is the cost-to-variance ratio,
          and its T-dependence is exactly what spike_v1 could not see (it held sigma^2, tau^2 fixed);
      (2) the envelope is  Var*(T) * B = ( sqrt(tau^2(T) p(T)) + sqrt(sigma^2(T) q(T)) )^2  (AM-GM),
          so the item size has an INTERIOR optimum T*: too small and tau^2 explodes, too large and
          the per-run scoring cost does.  The prescription is the triple (M*, N*, T*) at the budget.

Usage:  python3 spike_v3.py            (tables + certificates + controls)
        python3 spike_v3.py --selftest (planted defects; every certificate must fire, healthy holds)
Out:    spike_v3_results.json
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spike_v2 import D, K_INFO, N_TRAIN, S_NOISE, cell_seed, one_run, _mul   # the DGP, imported

import numpy as np

SEED0 = 20261004
T_GRID = [125, 250, 500, 1000, 2000, 4000, 8000, 16000]
K_ITEMS = 192              # test sets measured per T (the tau^2 estimate's own resolution)
R_RUNS = 200               # training runs per item (the sigma^2 estimate)
U_DIFF = 0.80              # the relative difficulty (spike_v2's u), where the axis is lively
HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ the fixed-task item measurement
def task_weights(seed=777):
    """One task = one weight vector, shared by every item.  The item axis is about TEST SETS, so
    the task is held fixed; drawing a new task per item would confound the two axes (spike_v2's
    first attempt, and the reason its tau^2 was not a clean 1/T)."""
    rng = np.random.default_rng(seed)
    w = np.zeros(D)
    w[:K_INFO] = rng.uniform(0.5, 1.5, size=K_INFO) * rng.choice([-1.0, 1.0], size=K_INFO)
    return w


def build_item(rng, T, w_task, u):
    """Draw a test set of T points for the fixed task and fix gamma at u * gamma* for THIS item."""
    Xte = rng.normal(size=(T, D))
    trA = float(np.sum(Xte[:, :K_INFO] ** 2))
    trB = float(np.sum(Xte ** 2))
    Sv = np.sum(Xte[:, K_INFO:], axis=1)
    cA = trA / (T * (N_TRAIN - K_INFO - 1))
    cB = trB / (T * (N_TRAIN - D - 1))
    gstar = math.sqrt(max(S_NOISE ** 2 * (cB - cA) / float(np.mean(Sv ** 2)), 0.0))
    w = w_task.copy()
    w[K_INFO:] = u * gstar
    yte = _mul(Xte, w) + rng.normal(scale=S_NOISE, size=T)
    assert np.isfinite(yte).all(), "the item response is not finite"
    return {"w": w, "Xte": Xte, "yte": yte, "gam": u * gstar}


def _chi2_lo(df):
    """lower 2.5 % quantile of chi-square(df) -- Wilson-Hilferty, adequate for a tolerance band."""
    z = -1.959964
    return df * (1.0 - 2.0 / (9.0 * df) + z * math.sqrt(2.0 / (9.0 * df))) ** 3


def _chi2_hi(df):
    z = 1.959964
    return df * (1.0 - 2.0 / (9.0 * df) + z * math.sqrt(2.0 / (9.0 * df))) ** 3


def measure_axis(T, u=U_DIFF, k_items=K_ITEMS, r_runs=R_RUNS, w_task=None):
    """sigma^2(T) and tau^2(T): the within-item and between-item variance of (mse_B - mse_A)."""
    w_task = task_weights() if w_task is None else w_task
    within, between = [], []
    for k in range(k_items):
        rng = np.random.default_rng(cell_seed("axis", T, k, u))
        item = build_item(rng, T, w_task, u)
        d = np.empty(r_runs)
        for i in range(r_runs):
            mA, mB, _v = one_run(rng, item, N_TRAIN)
            d[i] = mB - mA
        within.append(float(np.var(d, ddof=1)))
        between.append(float(np.mean(d)))
    sigma2 = float(np.mean(within))
    tau2 = float(np.var(between, ddof=1))
    return {"T": T, "sigma2": sigma2, "tau2": tau2,
            "tau2_times_T": tau2 * T, "sigma2_times_T": sigma2 * T,
            "k_items": k_items, "r_runs": r_runs,
            "tau2_lo": tau2 * (k_items - 1) / _chi2_hi(k_items - 1),
            "tau2_hi": tau2 * (k_items - 1) / _chi2_lo(k_items - 1)}


def fit_tau(rows):
    """tau^2(T) = c_tau / T: the log-log slope over the T grid, and c_tau = mean(tau^2 * T)."""
    xs = [math.log(r["T"]) for r in rows]
    ys = [math.log(r["tau2"]) for r in rows]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    c_tau = sum(r["tau2_times_T"] for r in rows) / len(rows)
    return slope, c_tau


def tau_consistency(rows, k_items):
    """Is tau^2 * T the SAME constant at every T?  A tau^2 estimated from k_items items has relative
    sd sqrt(2/(k_items-1)), so the flatness of tau^2*T is a chi-square consistency test against a
    common c_tau -- NOT a range check.  The first version of this certificate used a crude
    max-min range and fired on ordinary sampling scatter (Class 172: a threshold must come from the
    estimator's own distribution).  Returns (c_tau_weighted, chi2, df, crit99)."""
    cs = [r["tau2_times_T"] for r in rows]
    rel = math.sqrt(2.0 / (k_items - 1))
    wts = [1.0 / (rel * c) ** 2 for c in cs]
    c_w = sum(w * c for w, c in zip(wts, cs)) / sum(wts)
    chi2 = sum(w * (c - c_w) ** 2 for w, c in zip(wts, cs))
    df = len(cs) - 1
    return c_w, chi2, df, _chi2_crit(df, 2.326)          # 99 % upper quantile


def _chi2_crit(df, z):
    """upper quantile of chi-square(df) -- Wilson-Hilferty (same family as _chi2_lo/_chi2_hi)."""
    return df * (1.0 - 2.0 / (9.0 * df) + z * math.sqrt(2.0 / (9.0 * df))) ** 3


def fit_sigma(rows):
    """sigma^2(T) = sigma_inf^2 + c_sig / T: linear least squares on the feature 1/T."""
    A = np.array([[1.0, 1.0 / r["T"]] for r in rows])
    y = np.array([r["sigma2"] for r in rows])
    (s_inf, c_sig), *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ np.array([s_inf, c_sig])
    return float(s_inf), float(c_sig), float(np.max(np.abs(resid)))


# ------------------------------------------------------------------ the three-knob budget
def cost_model(alpha, beta, kappa, lam, T):
    return alpha + beta * T, kappa + lam * T          # (item cost p(T), run cost q(T))


def n_star(T, coef, cost):
    """spike_v1's law with the T-dependent cost and variances: sqrt(sigma^2 p / (tau^2 q))."""
    s2, t2 = coef["sigma2_of"](T), coef["tau2_of"](T)
    p, q = cost_model(*cost, T)
    return math.sqrt(s2 * p / (t2 * q))


def var_envelope(T, coef, cost, B=1.0):
    """Var*(T) * B = ( sqrt(tau^2 p) + sqrt(sigma^2 q) )^2 -- the AM-GM envelope over N."""
    s2, t2 = coef["sigma2_of"](T), coef["tau2_of"](T)
    p, q = cost_model(*cost, T)
    return (math.sqrt(t2 * p) + math.sqrt(s2 * q)) ** 2 / B


def var_at(N, T, coef, cost, B=1.0):
    """The actual estimator variance at (N, T) under the budget: Var = (tau^2 + sigma^2/N)/M."""
    s2, t2 = coef["sigma2_of"](T), coef["tau2_of"](T)
    p, q = cost_model(*cost, T)
    M = B / (p + N * q)
    return (t2 + s2 / N) / M


def solve_T(coef, cost, B=1.0, T_lo=1.0, T_hi=1e6):
    """Minimise the envelope over T on a log grid, then refine by golden section (certified against
    a brute-force grid in main())."""
    def f(T):
        return var_envelope(T, coef, cost, B)
    grid = [T_lo * (T_hi / T_lo) ** (i / 400.0) for i in range(401)]
    vals = [f(t) for t in grid]
    i = min(range(len(grid)), key=lambda j: vals[j])
    lo, hi = grid[max(0, i - 1)], grid[min(len(grid) - 1, i + 1)]
    for _ in range(120):                              # golden-section refine
        a = lo + (hi - lo) * 0.382
        b = lo + (hi - lo) * 0.618
        if f(a) < f(b):
            hi = b
        else:
            lo = a
    return 0.5 * (lo + hi), f(0.5 * (lo + hi))


def coefficients_from_rows(rows):
    """The fitted (c_tau, sigma_inf^2, c_sig), as the coef dict the budget functions consume."""
    _, c_tau = fit_tau(rows)
    s_inf, c_sig, _ = fit_sigma(rows)
    return {"c_tau": c_tau, "s_inf": s_inf, "c_sig": c_sig,
            "tau2_of": lambda T: c_tau / T,
            "sigma2_of": lambda T: s_inf + c_sig / T}


# ------------------------------------------------------------------ certificate predicates
def assert_tau_law(slope, chi2, df, crit):
    """tau^2 * T flat over a 128x span in T and the log-log slope at -1.  The slope is the law (a
    tau^2 that does not scale gives slope 0; one that scales as 1/T^2 gives -2); the chi-square
    guards against an intermediate deviation without firing on sampling scatter."""
    assert -1.15 < slope < -0.85, "tau^2 does not fall as 1/T: fitted slope %.3f" % slope
    assert chi2 < crit, \
        "tau^2 * T is not a single constant: chi2 %.2f over %d df (crit %.2f)" % (chi2, df, crit)


def assert_sigma_law(s_inf, c_sig, n_inf, worst_resid):
    """sigma^2 is a floor plus a 1/T part: monotone and small residuals, with a POSITIVE floor."""
    assert s_inf > 0.0, "the sigma^2 floor is not positive: %.3g" % s_inf
    assert c_sig > 0.0, "the sigma^2 1/T coefficient is not positive: %.3g" % c_sig
    assert worst_resid < 0.15 * n_inf, \
        "the two-term sigma^2 model misses by %.3g (>15%% of the range)" % worst_resid


def assert_holdout(pred, obs, tol=0.20):
    """A law fitted on the other sizes predicts a HELD-OUT size (Class 163(d): in-sample agreement
    is a coincidence of points until an unseen reading agrees)."""
    rel = abs(pred - obs) / abs(obs)
    assert rel < tol, "held-out T prediction off by %.1f %% (tol %.0f %%)" % (100 * rel, 100 * tol)
    return rel


# ------------------------------------------------------------------ main
def main():
    out = {"seed0": SEED0, "t_grid": T_GRID, "k_items": K_ITEMS, "r_runs": R_RUNS,
           "u_diff": U_DIFF, "d": D, "k_info": K_INFO, "n_train": N_TRAIN,
           "axis": [], "certificates": {}, "controls": {}, "budget": []}
    w_task = task_weights()

    print("=" * 118)
    print("1. THE ITEM AXIS -- sigma^2 and tau^2 as functions of the item SIZE T (one fixed task)")
    print("   T       sigma^2(within)   tau^2(between)    tau^2*T      sigma^2*T     tau^2 95% band")
    rows = []
    for T in T_GRID:
        r = measure_axis(T, w_task=w_task)
        rows.append(r)
        out["axis"].append({k: r[k] for k in ("T", "sigma2", "tau2", "tau2_times_T",
                                              "sigma2_times_T", "tau2_lo", "tau2_hi")})
        print("   %-7d %-16.4g %-17.4g %-12.4g %-13.4g [%.3g, %.3g]"
              % (T, r["sigma2"], r["tau2"], r["tau2_times_T"], r["sigma2_times_T"],
                 r["tau2_lo"], r["tau2_hi"]))

    slope, c_tau = fit_tau(rows)
    s_inf, c_sig, worst_resid = fit_sigma(rows)
    c_tau_w, chi2, df, crit = tau_consistency(rows, K_ITEMS)
    n_range = max(r["sigma2"] for r in rows) - min(r["sigma2"] for r in rows)
    print()
    print("2. THE TWO LAWS")
    print("   tau^2(T)   = %.5g / T   (log-log slope %.4f; tau^2*T: weighted c_tau %.5g,"
          " chi2 %.2f / %d df vs crit %.2f)" % (c_tau, slope, c_tau_w, chi2, df, crit))
    print("   sigma^2(T) = %.5g + %.5g / T   (worst residual %.3g, %.1f %% of the range)"
          % (s_inf, c_sig, worst_resid, 100 * worst_resid / max(n_range, 1e-30)))
    print("   -> the two axes fight DIFFERENT noise: repeats fight the training floor sigma_inf^2,")
    print("      item SIZE fights the test-set spread c_tau/T.  Only the second is bought by T.")

    # held-out T: refit without the middle of the grid and predict it
    hold = rows[len(rows) // 2]
    rest = [r for r in rows if r is not hold]
    _, c_tau_h = fit_tau(rest)
    s_inf_h, c_sig_h, _ = fit_sigma(rest)
    pred_tau = c_tau_h / hold["T"]
    pred_sig = s_inf_h + c_sig_h / hold["T"]
    print("   held-out T=%d: tau^2 pred %.4g vs %.4g ; sigma^2 pred %.4g vs %.4g"
          % (hold["T"], pred_tau, hold["tau2"], pred_sig, hold["sigma2"]))

    coef = coefficients_from_rows(rows)
    out["certificates"]["tau_loglog_slope"] = slope
    out["certificates"]["tau_c_tau_weighted"] = c_tau_w
    out["certificates"]["tau_chi2"] = chi2
    out["certificates"]["tau_chi2_df"] = df
    out["certificates"]["tau_chi2_crit99"] = crit
    out["certificates"]["sigma_inf"] = s_inf
    out["certificates"]["sigma_c_sig"] = c_sig
    out["certificates"]["sigma_worst_resid"] = worst_resid
    assert_tau_law(slope, chi2, df, crit)
    assert_sigma_law(s_inf, c_sig, n_range, worst_resid)
    rel_tau = assert_holdout(pred_tau, hold["tau2"])
    rel_sig = assert_holdout(pred_sig, hold["sigma2"])
    out["certificates"]["holdout_T"] = hold["T"]
    out["certificates"]["holdout_rel_tau2"] = rel_tau
    out["certificates"]["holdout_rel_sigma2"] = rel_sig
    print("   -> laws hold; held-out prediction within %.1f %% (tau^2) and %.1f %% (sigma^2)"
          % (100 * rel_tau, 100 * rel_sig))

    print()
    print("3. THE THREE-KNOB BUDGET -- the item size has an INTERIOR optimum")
    print("   (cost p(T)=alpha+beta*T per item, q(T)=kappa+lambda*T per repeat; budget B=1)")
    print("   alpha  beta   kappa  lambda |  T*      N*(T*)   M*        Var*")
    ref_cost = (1.0, 1.0, 1.0, 1.0)
    for (al, be, ka, la) in [ref_cost, (1, 0.1, 1, 1), (1, 10, 1, 1), (1, 1, 10, 1),
                             (1, 1, 1, 10), (10, 1, 1, 1)]:
        cost = (al, be, ka, la)
        T_star, v_star = solve_T(coef, cost)
        N_star_v = n_star(T_star, coef, cost)
        p, q = cost_model(al, be, ka, la, T_star)
        M_star = 1.0 / (p + N_star_v * q)
        out["budget"].append({"alpha": al, "beta": be, "kappa": ka, "lambda": la,
                              "T_star": T_star, "N_star": N_star_v, "M_star": M_star,
                              "var_star": v_star})
        print("   %-6.3g %-6.3g %-6.3g %-6.3g |  %-7.4g %-8.4g %-9.4g %.4g"
              % (al, be, ka, la, T_star, N_star_v, M_star, v_star))

    # ---------------- certificates: the closed form vs brute force, and the AM-GM identity
    print()
    print("CERTIFICATE -- N*(T) equals the brute-force integer argmin at fixed T")
    worst_n = 0
    for T in (250, 1000, 4000):
        closed = n_star(T, coef, ref_cost)
        best = min(range(1, 5001), key=lambda n: var_at(n, T, coef, ref_cost))
        worst_n = max(worst_n, abs(round(closed) - best))
        print("   T=%-6d closed N*=%9.5f -> round %d   brute N=%5d" % (T, closed, round(closed), best))
    out["certificates"]["n_star_brute_max_int_gap"] = worst_n
    assert worst_n <= 1, "N*(T) does not round to the brute-force argmin: gap %d" % worst_n

    print()
    print("CERTIFICATE -- the AM-GM envelope equals min_N of the true variance (both sides computed)")
    worst_am = 0.0
    for T in (250, 1000, 4000):
        env = var_envelope(T, coef, ref_cost)
        brute = min(var_at(n, T, coef, ref_cost) for n in range(1, 20001))
        rel = abs(env - brute) / brute
        worst_am = max(worst_am, rel)
        print("   T=%-6d envelope %.6e  brute min %.6e  rel %.2e" % (T, env, brute, rel))
    out["certificates"]["amgm_worst_rel"] = worst_am
    assert worst_am < 0.05, "the AM-GM envelope is not the variance minimum: %.3e" % worst_am

    print()
    print("CERTIFICATE -- (T*, N*) equals the brute-force grid optimum in the JOINT problem")
    T_star, v_star = solve_T(coef, ref_cost)
    N_star_v = n_star(T_star, coef, ref_cost)
    best = (1e30, None, None)
    Tg = [1.0 * (2 ** (i / 3.0)) for i in range(0, 61)]          # ~1 .. 1e6, 3 per doubling
    for T in Tg:
        for n in range(1, 4001):
            v = var_at(n, T, coef, ref_cost)
            if v < best[0]:
                best = (v, T, n)
    rel_T = abs(math.log(T_star / best[1]))
    rel_v = abs(v_star - best[0]) / best[0]
    print("   closed (T*,N*,Var*) = (%.4g, %.4g, %.6e)" % (T_star, N_star_v, v_star))
    print("   brute  (T, N, Var)  = (%.4g, %d, %.6e)   |log T/T*| = %.3f, Var rel %.3f"
          % (best[1], best[2], best[0], rel_T, rel_v))
    out["certificates"]["joint_brute_logT_gap"] = rel_T
    out["certificates"]["joint_brute_var_rel"] = rel_v
    # the closed form is a RELAXATION over integer N and a grid-min over T, so its value is a LOWER
    # bound: it must not EXCEED the brute-force optimum (that would be a relaxation that overshoots).
    assert v_star <= best[0] * 1.0001, "the closed form EXCEEDS the brute-force optimum: overshoot"
    assert rel_T < 0.15 and rel_v < 0.05, "the joint optimum is not the brute-force optimum"

    # ---------------- controls (two-sided on the DGP, not on a certificate)
    print()
    print("CONTROL -- T* is INTERIOR because the item size both helps (variance) and costs (price)")
    # (C1) free item size (beta=0, lambda=0): bigger items are free and reduce variance, so T* runs
    #      to the grid cap; the floor sigma_inf^2 is all that stops the variance falling further.
    T_free, v_free = solve_T(coef, (1.0, 0.0, 1.0, 0.0), T_lo=1.0, T_hi=1e6)
    # (C2) no size-dependent variance (c_tau = 0 AND c_sig = 0): a bigger item costs more and
    #      changes no variance, so T* collapses toward the smallest item.
    coef_nosize = dict(coef, c_tau=1e-12, tau2_of=lambda T: 1e-12 / T,
                       c_sig=0.0, sigma2_of=lambda T: coef["s_inf"])
    T_nosize, _ = solve_T(coef_nosize, ref_cost, T_lo=1.0, T_hi=1e6)
    out["controls"] = {"T_star_free_size": T_free, "T_star_no_size_variance": T_nosize,
                       "sigma_inf_floor_var": math.sqrt(s_inf),
                       "reference_T_star": T_star}
    print("   (C1) free item size (beta=lambda=0):      T* = %.4g  (runs to the cap)" % T_free)
    print("   (C2) no size-dependent variance (c=0):   T* = %.4g  (buy the smallest item)" % T_nosize)
    print("   reference (both effects on):              T* = %.4g  (STRICTLY between)" % T_star)
    assert T_free > 1e4, "with a free item size T* did not run toward the cap"
    assert T_nosize < 2.0, "with no size-dependent variance T* did not collapse small"
    assert T_nosize < T_star < T_free, "the reference T* is not interior to the two controls"

    with open(os.path.join(HERE, "spike_v3_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v3_results.json")
    return 0


# ------------------------------------------------------------------ self-test (planted defects)
def selftest():
    print("=" * 118)
    print("SELFTEST -- plant a defect per certificate and require it to FIRE, and the healthy case")
    print("            to HOLD (a plant that fires on everything is decoration too)")
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
            print("[%-28s] *** FIRED ON A HEALTHY CASE *** %s" % (name, str(e)[:36]))
            ok = False

    # 1. the tau^2 law: a variance that does NOT fall with T (slope ~0) must fire; so must a
    #    chi-square that says tau^2*T is not one constant
    fires("tau-law-slope", lambda: assert_tau_law(-0.05, 5.0, 7, 18.5))
    holds("tau-law-slope/ok", lambda: assert_tau_law(-0.98, 13.6, 7, 18.5))
    fires("tau-law-chi2", lambda: assert_tau_law(-1.00, 40.0, 7, 18.5))
    holds("tau-law-chi2/ok", lambda: assert_tau_law(-1.00, 13.6, 7, 18.5))

    # 2. the sigma^2 model: a floor-free (pure 1/T) reading, or a bad fit, must fire
    fires("sigma-floor-positive", lambda: assert_sigma_law(-1e-4, 0.14, 1e-3, 0.0))
    holds("sigma-floor-positive/ok", lambda: assert_sigma_law(4.3e-4, 0.14, 1.5e-3, 1e-5))
    fires("sigma-residual", lambda: assert_sigma_law(4.3e-4, 0.14, 1.5e-3, 5e-4))
    holds("sigma-residual/ok", lambda: assert_sigma_law(4.3e-4, 0.14, 1.5e-3, 1e-5))

    # 3. the held-out prediction: a law that fits only its own points must miss an unseen size
    fires("heldout-T", lambda: assert_holdout(0.0018, 0.0006))     # 200 % off
    holds("heldout-T/ok", lambda: assert_holdout(0.00062, 0.00060))

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CERTIFICATE IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
