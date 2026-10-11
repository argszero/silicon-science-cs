#!/usr/bin/env python3
"""Issue #124 -- spike_v2: the EMPIRICAL arm.  Measure p, sigma^2 and tau^2 -- do not assume them.

spike_v0 computed the exact error of a decision over N repeats GIVEN p.  spike_v1 solved the
item-repeat budget split GIVEN (sigma^2, tau^2).  Both take their inputs as given.  This instrument
MEASURES them in a real stochastic optimisation and then asks the two registered questions:

  P2             -- is the measured p small enough for the folk N = 3 convention?
                    (registered: at least one cell has p >= 0.10, and p varies by more than 2x)
  criterion (ii) -- does the exact law's predicted error of an N-run strict majority match the
                    observed error from the same runs, in >= 90 % of the countable cells?

THE STOCHASTIC OPTIMISATION (a defined data-generating process; CPU-only, numpy/scipy only).
  DGP    x ~ N(0, I_d);  y = x.w + eps,  eps ~ N(0, sigma^2).  The first k coefficients are
         informative (|w_j| ~ U(0.5,1.5), random sign); the last m = d-k share one SMALL coefficient
         gamma.  gamma is the difficulty knob.
  RUN    draw n training rows; fit model A = OLS on the first k features and model B = OLS on all d;
         score both on a FIXED test set; the run's VERDICT is "A is better" iff mse_A < mse_B.
  TRUTH  A omits the k..d block, so it carries a bias gamma*(sum of the omitted features) but pays
         the smaller variance term; B pays the full variance term with no bias.  The expected test
         MSE of each is EXACT given the test set.  OLS is unbiased in expectation over training
         draws, but the test MSE also carries terms that are FIXED by the ONE test set a study
         holds: mean(eps^2) instead of sigma^2, and -- the term a population closed form drops --
         2*gamma*mean(S*eps), the correlation between the omitted block's linear form S and the
         realized test noise.  Both are kept, so pred_mse_A/pred_mse_B are exact CONDITIONAL
         predictions (certified against the runs at < 4 sd; see the decomposition certificate).

             gamma* = sqrt( sigma^2 (cB - cA) / S2 ),      (the POPULATION crossing)
             cA = trA / (N (n-k-1)),   cB = trB / (N (n-d-1)),   S2 = mean_i (sum_{j>=k} x_ij)^2.

         For gamma < gamma*, A IS truly better, so a run that says "B better" is WRONG, and
         p = P(the run's verdict is wrong) is what the repeat-count law needs as its input.
  CELL   u = gamma / gamma*, the RELATIVE difficulty.  u -> 0 is easy (p -> 0); u -> 1 is the
         crossing (p -> 1/2).  This is the regime the law is about, and it is swept, not assumed.

Between-cell and within-cell variance of the per-run score difference give tau^2 and sigma^2, which
instantiate spike_v1's N* with MEASURED inputs rather than notional ones.  Section 6 sweeps the ITEM
axis (N_TEST) to show that the dropped cross term -- a per-test-set draw -- is bought only with test
data, at 1/sqrt(N_TEST), and that the repeat axis cannot shrink it.

Usage:  python3 spike_v2.py            (tables + certificates + controls)
        python3 spike_v2.py --selftest (planted defects; every certificate must fire, and the
                                        healthy case must NOT -- a plant that fires on everything
                                        is decoration as much as one that never fires)
Out:    spike_v2_results.json
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spike_v0 import majority_strict          # the exact law, imported not re-derived
from spike_v0 import cell_seed as _cs0        # the reproducible-seed helper

import numpy as np

SEED0 = 20261004
D = 12                    # features in the DGP
K_INFO = 6                # informative features (model A uses these)
M_TAIL = D - K_INFO       # the block A omits (all sharing the small coefficient gamma)
N_TEST = 2000             # fixed test set per cell
N_TRAIN = 200             # training rows per run
R_RUNS = 12000            # independent runs per cell (the empirical p is measured on these).
                          # Sized by the RAREST cell, not the average: the gate is on EXPECTED
                          # EVENTS R*p, and u=0 measures p ~ 6e-3, so the earlier 600 left only
                          # ~3.8 events there -- a proportion with 52% relative error, which the
                          # gate correctly refused as a reading.  12000 clears the 30-event floor
                          # even at the low end of that cell's 95% interval (0.0035 -> 42), and
                          # costs ~15 s of sampling.
N_REPS = 4                # independent replications of the grid (>= 3 required by the bar)
# The CONDITIONAL crossing -- the u where the realized delta is ZERO -- is not at u = 1.  The
# training-side tail term (see pred_A) makes A worse than the population form says, so the crossing
# sits BELOW 1.  It is a CONSTRUCT, not a grid point: which cell sits on it is decided by the item
# axis (the omitted-block x test-noise cross term has per-cell sd ~7.9e-3 against the 3-se bar of
# 6.0e-4 it would have to fall inside), so no choice of u can place one there -- section 7 solves
# each rep's own root instead.  At R = 600 the wrong (population) crossing was indistinguishable
# from the right one, which is why u = 0.99 used to read as the crossing cell.
U_CELLS = [0.0, 0.5, 0.8, 0.95, 0.99]   # the relative-difficulty axis
N_DECIDE = [1, 3, 5, 10]  # repeat counts whose majority error is checked (criterion ii)
S_NOISE = 1.0
RES_MIN_EVENTS = 30       # a proportion needs this many EXPECTED events to be a reading at all
CRIT_MIN_EVENTS = 5       # below this many expected wrong blocks a criterion-(ii) row is vacuous
ITEM_N_TESTS = [250, 1000, 4000, 16000]   # the ITEM axis sweep (section 6)
HERE = os.path.dirname(os.path.abspath(__file__))


def cell_seed(*parts):
    return SEED0 + _cs0(*parts) % 1000000


def _mul(A, b):
    """BLAS emits spurious FP-flag warnings for a matmul with a ZERO-TAILED operand in numpy 2.x.
    Scope them off, but never silently: the caller asserts finiteness afterwards."""
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        return A @ b


def make_cell(rng, n_train, u, n_test=None):
    """The cell's fixed truth: informative weights, the test set, gamma, gamma*, and the EXACT
    expected MSEs of A and B *conditional on this test set*.

    The conditioning matters, and a whole term lives in it.  Model A is MISSPECIFIED -- it omits
    the k..d block -- so its test residual carries `gam * S_i`, the omitted block's linear form.
    The population closed form keeps `gam^2 * mean(S^2)` but DROPS the cross term with the realized
    test noise, `2 * gam * mean(S * eps)`: that term has zero expectation over test draws, yet for
    the ONE test set a study actually holds it is a fixed, measurable offset set by the ITEM axis
    (N_TEST), not the repeat axis.  It is not small -- at u = 0.8 it is of the same order as the
    very delta the comparison is trying to resolve.  Averaging over training draws does not remove
    it: it is constant across runs, so it biases the measured delta without widening the interval.
    Both this and the realized `mean(eps^2)` are therefore kept.

    A SECOND term lives on the TRAINING side and was missing until R was raised: the omitted block
    enters the fit of A as extra noise (variance M_TAIL*gam^2 per training row), so the cA term
    carries `sigma^2 + M_TAIL*gam^2`, not `sigma^2` (see the comment at pred_A).

    With both kept, pred_mse_A/pred_mse_B are exact, and the decomposition certificate reads the
    measured E[mA]/E[mB] against them at < 4 sd in every cell -- at the R the run actually uses.
    A claim about a match is a claim about the RESOLUTION it was read at: at R = 600 the
    training-side term sat 20x below its own standard error, so the certificate could not have
    failed there even though the term was absent."""
    nt = N_TEST if n_test is None else n_test
    w = np.zeros(D)
    w[:K_INFO] = rng.uniform(0.5, 1.5, size=K_INFO) * rng.choice([-1.0, 1.0], size=K_INFO)
    Xte = rng.normal(size=(nt, D))
    trA = float(np.sum(Xte[:, :K_INFO] ** 2))
    trB = float(np.sum(Xte ** 2))
    S = np.sum(Xte[:, K_INFO:], axis=1)          # the omitted block's linear form
    S2 = float(np.mean(S ** 2))
    cA = trA / (nt * (n_train - K_INFO - 1))
    cB = trB / (nt * (n_train - D - 1))
    gam_star = math.sqrt(max(S_NOISE ** 2 * (cB - cA) / S2, 0.0))   # the POPULATION crossing
    gam = u * gam_star
    w[K_INFO:] = gam
    yte = _mul(Xte, w) + rng.normal(scale=S_NOISE, size=nt)
    assert np.isfinite(yte).all(), "the test response is not finite"
    eps = yte - _mul(Xte, w)                     # the realized test noise (the instrument knows it)
    eps2 = float(np.mean(eps ** 2))              # conditional, not the population sigma^2
    mean_S_eps = float(np.mean(S * eps))
    cross = 2.0 * gam * mean_S_eps              # omitted-block x fixed-test-noise correlation
    # The omitted block is owed TWICE, and the second debt is paid on the TRAINING side.  Fitting A
    # regresses y on the informative columns only, so the tail contribution `gam * S_train` acts as
    # EXTRA NOISE in that fit -- its variance is M_TAIL * gam^2 per training row -- and it inflates
    # the estimation error of A's coefficients exactly like sigma^2 does.  So the training-noise
    # variance in the cA term is (sigma^2 + M_TAIL*gam^2), not sigma^2.  B has no omitted block, so
    # only A carries this term.  It is invisible at low R: at gam = 0.074 it is 1.0e-3 against a
    # 4.5e-5 standard error, and it took R = 12000 (se 4.5x smaller than R = 600) to resolve it.
    var_train_A = S_NOISE ** 2 + M_TAIL * gam ** 2
    pred_A = eps2 + var_train_A * cA + float(np.mean((gam * S) ** 2)) + cross
    pred_B = eps2 + S_NOISE ** 2 * cB
    # the population delta (what a large-N_TEST limit would give) vs the realized one
    delta_pop = S_NOISE ** 2 * (cB - cA) - gam ** 2 * S2
    return {"w": w, "Xte": Xte, "yte": yte, "gam": gam, "gam_star": gam_star,
            "pred_mse_A": pred_A, "pred_mse_B": pred_B, "pred_delta": pred_B - pred_A,
            "cross_term": cross, "eps2_te": eps2, "delta_pop": delta_pop, "n_test": nt,
            # the u-INDEPENDENT inputs of the truth: eps is the raw test-noise draw (make_cell
            # subtracts the true signal exactly, so the omitted-block scale cannot enter it), which
            # is what lets section 7 solve the conditional crossing instead of searching for it.
            "S": S, "S2": S2, "cA": cA, "cB": cB, "eps": eps, "mean_S_eps": mean_S_eps}


def with_gam(cell, gam):
    """The same test set and the same noise draw at a different omitted-block scale."""
    w = cell["w"].copy()
    w[K_INFO:] = gam
    Xte, nt = cell["Xte"], cell["n_test"]
    S, eps = cell["S"], cell["eps"]
    yte = _mul(Xte, w) + eps
    cross = 2.0 * gam * cell["mean_S_eps"]
    var_train_A = S_NOISE ** 2 + M_TAIL * gam ** 2
    pred_A = cell["eps2_te"] + var_train_A * cell["cA"] \
        + float(np.mean((gam * S) ** 2)) + cross
    pred_B = cell["eps2_te"] + S_NOISE ** 2 * cell["cB"]
    d = dict(cell)
    d.update({"w": w, "yte": yte, "gam": gam, "cross_term": cross,
              "pred_mse_A": pred_A, "pred_mse_B": pred_B,
              "pred_delta": pred_B - pred_A,
              "delta_pop": S_NOISE ** 2 * (cell["cB"] - cell["cA"]) - gam ** 2 * cell["S2"]})
    return d


def crossing_u(cell):
    """The u whose cell has EXACT conditional delta zero -- SOLVED, closed form.

        delta(u) = sigma^2 (cB - cA) - u^2 gam*^2 (S2 + M_TAIL cA) - 2 u gam* m,   m = mean(S eps)

    is a quadratic in u because S2, cA, cB, m and gam* are all u-independent, so the root is

        u* = (-m + sqrt(m^2 + (S2 + M_TAIL cA) sigma^2 (cB - cA))) / (gam* (S2 + M_TAIL cA)).

    A cell built at u* sits on the crossing BY CONSTRUCTION.  Note that its POPULATION delta is by
    then positive -- the population form would call that cell "A is better" while the conditional
    truth says the two are indistinguishable."""
    S2, cA, cB = cell["S2"], cell["cA"], cell["cB"]
    m, gs = cell["mean_S_eps"], cell["gam_star"]
    disc = m * m + (S2 + M_TAIL * cA) * S_NOISE ** 2 * (cB - cA)
    assert disc >= 0.0, "the conditional crossing has no real root in this cell"
    return (-m + math.sqrt(disc)) / (gs * (S2 + M_TAIL * cA))


def one_run(rng, cell, n_train):
    """A single repeat: draw a training sample, fit A and B, return (mse_A, mse_B, verdict)."""
    Xtr = rng.normal(size=(n_train, D))
    ytr = _mul(Xtr, cell["w"]) + rng.normal(scale=S_NOISE, size=n_train)
    assert np.isfinite(ytr).all(), "the training response is not finite"
    wA, *_ = np.linalg.lstsq(Xtr[:, :K_INFO], ytr, rcond=None)
    mA = float(np.mean((_mul(cell["Xte"][:, :K_INFO], wA) - cell["yte"]) ** 2))
    wB, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
    mB = float(np.mean((_mul(cell["Xte"], wB) - cell["yte"]) ** 2))
    return mA, mB, (1 if mA < mB else 0)          # 1 == "A is better" == the correct verdict


def measure_cell(n_train, u, rep):
    """R independent runs -> per-run verdicts, per-run score differences, p, and the measured delta."""
    rng = np.random.default_rng(cell_seed("cell", n_train, u, rep))
    cell = make_cell(rng, n_train, u)
    verdicts, diffs, mAs, mBs = [], [], [], []
    for _ in range(R_RUNS):
        mA, mB, v = one_run(rng, cell, n_train)
        verdicts.append(v)
        diffs.append(mB - mA)                     # positive == A better (the true direction)
        mAs.append(mA)
        mBs.append(mB)
    return {"n_train": n_train, "u": u, "rep": rep, "gam": cell["gam"],
            "gam_star": cell["gam_star"], "pred_delta": cell["pred_delta"],
            "pred_mse_A": cell["pred_mse_A"], "pred_mse_B": cell["pred_mse_B"],
            "delta_pop": cell["delta_pop"], "cross_term": cell["cross_term"],
            "eps2_te": cell["eps2_te"],
            "mA_mean": float(np.mean(mAs)), "mB_mean": float(np.mean(mBs)),
            "mA_var": float(np.var(mAs, ddof=1)), "mB_var": float(np.var(mBs, ddof=1)),
            "p_hat": 1.0 - sum(verdicts) / len(verdicts), "verdicts": verdicts,
            "diff_mean": float(np.mean(diffs)), "diff_var": float(np.var(diffs, ddof=1))}


def observed_majority(verdicts, N):
    """Disjoint blocks of N: a block is RIGHT iff its strict majority is right; an even-N tie is
    UNRESOLVED and excluded from numerator and denominator (spike_v0's rule)."""
    right = wrong = unres = 0
    for i in range(0, len(verdicts) - N + 1, N):
        c = sum(verdicts[i:i + N])
        if 2 * c > N:
            right += 1
        elif 2 * c < N:
            wrong += 1
        else:
            unres += 1
    denom = right + wrong
    return ((wrong / denom) if denom else None), unres, denom


# --- the certificate predicates, factored so the self-test plants exercise the SAME predicate the
# --- run applies (a plant written against a copy of the check tests the copy, not the check).
def assert_resolved_sign(u, pred_delta, measured_delta, se):
    assert (measured_delta - 3.0 * se > 0) == (pred_delta > 0), \
        "at u=%.3g the measured delta has the WRONG SIGN of the exact conditional delta" % u


def demo_z(meas, pred, se):
    return abs(meas - pred) / max(se, 1e-30)


def assert_crossing_measures_zero(u, meas, se):
    """A cell constructed at the conditional crossing must MEASURE zero: the construct is a claim
    about the truth, and this is the reading that can falsify it.  (The population crossing placed
    at u = 1 would fail this by ~9 se, so the check is not vacuous.)"""
    z = demo_z(meas, 0.0, se)
    assert z < 4.0, \
        "the constructed crossing at u=%.4f does not measure zero: |d| = %.2f sd" % (u, z)
    return z


def z_law_vs_observed(pred, obs, blocks):
    """|observed - law-predicted| in units of the observed rate's binomial sd."""
    sd = math.sqrt(max(pred * (1.0 - pred) / blocks, 1e-18))
    return abs(obs - pred) / sd


def assert_law_matches(pred, obs, blocks):
    z = z_law_vs_observed(pred, obs, blocks)
    assert z <= 3.0, \
        "the law misses the observed majority error: pred %.5f obs %.5f over %d blocks (%.1f sd)" \
        % (pred, obs, blocks, z)
    return z


def assert_decomp(u, tag, meas, pred, se):
    z = demo_z(meas, pred, se)
    assert z < 4.0, "decomposition %s at u=%.3g: |d| = %.2f sd" % (tag, u, z)
    return z


def assert_delta_matches(u, pred_delta, measured_delta, se_mean):
    z = demo_z(measured_delta, pred_delta, se_mean)
    assert z < 4.0, "closed form vs measured delta at u=%.3g: |d| = %.2f sd" % (u, z)
    return z


def assert_p_repro(u, p1, p2, n):
    pb = 0.5 * (p1 + p2)
    z = abs(p1 - p2) / math.sqrt(max(pb * (1 - pb), 1e-12) / n)
    assert z < 4.0, "p within cell at u=%.3g: |d| = %.2f sd" % (u, z)
    return z


def assert_item_law(slope):
    """The item axis sets the dropped term: sd(cross) is proportional to 1/sqrt(N_TEST), so a
    log-log fit over the N_TEST grid has slope -1/2.  A pairwise-ratio test was the first version
    of this check and it was too noisy to resolve (an RMS over a few dozen test sets carries ~15 %
    error, so a 2.00 ratio reads anywhere in 1.2-3.3); the slope uses all the points at once."""
    assert -0.75 < slope < -0.25, \
        "the item-axis term does not fall as 1/sqrt(N_TEST): fitted slope %.3f" % slope
    return slope


def main():
    out = {"seed0": SEED0, "d": D, "k_info": K_INFO, "n_test": N_TEST, "n_train": N_TRAIN,
           "r_runs": R_RUNS, "n_reps": N_REPS, "u_cells": U_CELLS, "n_decide": N_DECIDE,
           "s_noise": S_NOISE, "means": [], "cells": [], "criterion_ii": [], "variance": [],
           "certificates": {}, "controls": {}}

    print("=" * 112)
    print("1. THE TRUTH IS ANALYTIC, AND IT IS CHECKED AGAINST THE RUNS")
    print("   u    gamma       gamma*      exact delta   measured delta  se      | cross term   |cross|/pop")
    cells = []
    for u in U_CELLS:
        preds, means, ses, crosses, pops = [], [], [], [], []
        for rep in range(N_REPS):
            m = measure_cell(N_TRAIN, u, rep)
            out["means"].append(m)
            preds.append(m["pred_delta"])
            means.append(m["diff_mean"])
            ses.append(math.sqrt(m["diff_var"] / R_RUNS))
            crosses.append(m["cross_term"])
            pops.append(m["delta_pop"])
            cells.append(m)
        pd = sum(preds) / len(preds)
        md = sum(means) / len(means)
        se = sum(ses) / len(ses)
        cr = sum(crosses) / len(crosses)
        pop = sum(pops) / len(pops)
        ratio = abs(cr) / pop if pop > 0 else float("nan")
        out["cells"].append({"u": u, "gam": cells[-1]["gam"], "gam_star": cells[-1]["gam_star"],
                             "pred_delta": pd, "measured_delta": md, "se": se,
                             "cross_term": cr, "delta_pop": pop,
                             "cross_over_pop": ratio})
        print("   %-4.2f %-11.5g %-11.5g %-13.5g %-15.5g %-7.5g | %-12.5g %s"
              % (u, cells[-1]["gam"], cells[-1]["gam_star"], pd, md, se, cr,
                 ("%.2f" % ratio) if pop > 0 else "n/a"))
    # TWO-SIDED truth certificate.  A cell whose EXACT conditional delta clears 3 se must measure
    # that sign; a cell sitting essentially ON the crossing (exact delta inside 3 se) is where the
    # direction is genuinely UNRESOLVED.  Demanding "established" in EVERY cell was an instrument
    # defect -- at u -> 1 the crossing IS the design, so the honest reading is "no direction".
    n_res = n_oncross = 0
    for c in out["cells"]:
        if abs(c["pred_delta"]) > 3.0 * c["se"]:
            n_res += 1
            assert_resolved_sign(c["u"], c["pred_delta"], c["measured_delta"], c["se"])
        else:
            n_oncross += 1
    out["certificates"]["truth_cells_resolved"] = n_res
    out["certificates"]["truth_cells_on_crossing"] = n_oncross
    # The limb here used to be `n_oncross >= 1` -- "the grid must contain a cell that sits ON the
    # crossing".  With the CORRECTED conditional truth that is unmeetable BY DESIGN: which cell sits
    # on the crossing is decided by the item axis (the cross term's per-cell sd is ~7.9e-3 against
    # the 3-se bar of 6.0e-4 it would have to fall inside), so a fixed grid can only hit it by luck
    # and the limb would have been testing the draw.  The premise is repaired rather than the
    # assertion loosened: the crossing gets its OWN certificate (section 7), which constructs a cell
    # at its exact root and requires the measurement there to be consistent with zero -- a stronger
    # statement than "one cell happened to land on it".  What the grid still owes is that it
    # RESOLVES a direction in more than a couple of cells.
    assert n_res >= 3, "the u grid must resolve a direction in at least 3 cells: %d" % n_res
    print("   -> %d cells resolve a direction (sign verified); %d sit on the crossing (unresolved by"
          " design, not a failure)" % (n_res, n_oncross))

    print()
    print("2. THE MEASURED INSTABILITY p (R = %d runs per cell, %d replications)" % (R_RUNS, N_REPS))
    print("   A p estimated from a handful of events is not a reading -- the resolution gate is on")
    print("   EXPECTED EVENTS, R*p, not on the number of runs (30 is the Poisson floor).")
    print("   u    |  p_hat per replication                         |  mean p  |  R*p  | resolution")
    p_mean = {}
    for u in U_CELLS:
        ps = [m["p_hat"] for m in out["means"] if m["u"] == u]
        p_mean[u] = sum(ps) / len(ps)
        ev = p_mean[u] * R_RUNS
        print("   %-4.2f |  %-45s |  %-7.4f |  %-5.1f | %s"
              % (u, " ".join("%.4f" % v for v in ps), p_mean[u], ev,
                 "OK" if ev >= RES_MIN_EVENTS else "LIMITED (<%d events)" % RES_MIN_EVENTS))
    well = {u: p for u, p in p_mean.items() if p * R_RUNS >= RES_MIN_EVENTS}
    out["certificates"]["cells_well_counted"] = sorted(well)
    out["certificates"]["cells_limited"] = sorted(set(p_mean) - set(well))

    print()
    print("3. P2 -- is the folk N = 3 convention adequate at the measured p?")
    print("   (registered: at least one cell with p >= 0.10, and p varying by more than 2x)")
    print("   u    |  mean p  | R*p   | N=3 majority error (exact) | verdict at the 5 % bar | p vs 0.10")
    for u in U_CELLS:
        e3, _ = majority_strict(3, p_mean[u])
        tag = "" if u in well else "  [resolution-limited]"
        print("   %-4.2f |  %-7.4f | %-5.1f | %-26.6f | %-23s | %s%s"
              % (u, p_mean[u], p_mean[u] * R_RUNS, e3, "ADEQUATE" if e3 <= 0.05 else "INADEQUATE",
                 ">= 0.10" if p_mean[u] >= 0.10 else "below", tag))
    n_ge = sum(1 for u, p in well.items() if p >= 0.10)          # resolution-limited cells cannot vote
    spread = max(well.values()) / max(1e-12, min(well.values())) if well else 0.0
    out["certificates"]["cells_p_ge_010"] = n_ge
    out["certificates"]["p_spread_over_cells"] = spread
    out["certificates"]["p_mean_by_cell"] = {str(u): p_mean[u] for u in U_CELLS}
    print("   among the %d well-counted cells: p >= 0.10 in %d; p spread %.2fx"
          % (len(well), n_ge, spread))
    p2_met = (n_ge >= 1) and (spread > 2.0)
    out["certificates"]["P2_met"] = bool(p2_met)
    print("   P2: %s" % ("CONFIRMED -- a repeat-count law has a non-trivial regime here"
                         if p2_met else "NOT met on the well-counted cells"))

    print()
    print("4. CRITERION (ii) -- the exact law's predicted error vs the OBSERVED majority error")
    print("   Both sides must use the SAME tie convention or the comparison is void: the law returns")
    print("   P(strictly wrong) with ties IN the denominator, while the runs' blocks EXCLUDE ties.")
    print("   The law is conditioned the same way first.  A row whose expected number of wrong blocks")
    print("   (pred x blocks) is below %d carries no information and is NOT counted either way."
          % CRIT_MIN_EVENTS)
    print("   u    N  |  pred err (tie-excl)  obs err   blocks  |  inside the 3-sd band?")
    print("   The prediction is the BLOCK-WEIGHTED MIXTURE of the per-test-set laws, not the law at")
    print("   the cell's averaged p.  Conditional on its test set a rep's runs ARE i.i.d. Bernoulli,")
    print("   so the law applies to that rep at ITS OWN p -- and the majority-error law is nonlinear")
    print("   in p, so law(mean p_r) != mean law(p_r).  At u = 0.5 the four reps read p = 0.1322 /")
    print("   0.1224 / 0.1313 / 0.0142 (a 9x spread), where the two differ by the Jensen gap: the old")
    print("   form predicted 0.0082 for a pooled observation of 0.0132 -- 5 sd out, on a WELL")
    print("   understood cause, and the same conditioning error this round found in the truth.")
    inside = total = 0
    excl = 0
    for u in U_CELLS:
        reps = [m for m in out["means"] if m["u"] == u]
        for N in N_DECIDE:
            W = Tt = 0
            num = den = 0.0
            for m in reps:
                err, unres = majority_strict(N, m["p_hat"])
                pred_r = err / (1.0 - unres) if unres < 1.0 else 1.0   # the runs' tie convention
                o, _unres, denom = observed_majority(m["verdicts"], N)
                if denom == 0:
                    continue
                W += int(round(o * denom))
                Tt += denom
                num += pred_r * denom
                den += denom
            if Tt == 0:
                continue
            obs = W / Tt
            pred = num / den
            if pred * Tt < CRIT_MIN_EVENTS:
                excl += 1
                print("   %-4.2f %-3d |  %-18.5f  %-9.5f %-7d |  NOT COUNTED (%.2f expected wrong blocks)"
                      % (u, N, pred, obs, Tt, pred * Tt))
                continue
            sd = math.sqrt(max(pred * (1 - pred) / Tt, 1e-18))
            off = z_law_vs_observed(pred, obs, Tt)
            ok = off <= 3.0
            total += 1
            inside += 1 if ok else 0
            out["criterion_ii"].append({"u": u, "N": N, "pred": pred, "obs": obs,
                                        "blocks": Tt, "sd": sd, "inside_3sd": bool(ok)})
            print("   %-4.2f %-3d |  %-18.5f  %-9.5f %-7d |  %s (|d| = %.1f sd)%s"
                  % (u, N, pred, obs, Tt, ok, off, "" if u in well else "  [p resolution-limited]"))
    frac = inside / total if total else 0.0
    out["certificates"]["criterion_ii_fraction"] = frac
    out["certificates"]["criterion_ii_cells"] = total
    out["certificates"]["criterion_ii_excluded"] = excl
    print("   -> within 3 sd in %d of %d countable cells (%.1f %%); %d rows excluded as vacuous;"
          " the registered bar is >= 90 %%" % (inside, total, 100 * frac, excl))
    assert frac >= 0.90, \
        "criterion (ii) is below its registered bar: %.1f %% of cells inside 3 sd" % (100 * frac)

    print()
    print("5. THE VARIANCE COMPONENTS -- tau^2 (between-cell) and sigma^2 (within-cell), MEASURED")
    cell_means, cell_vars = [], []
    for u in U_CELLS:
        ds = [m["diff_mean"] for m in out["means"] if m["u"] == u]
        vs = [m["diff_var"] for m in out["means"] if m["u"] == u]
        cell_means.append(sum(ds) / len(ds))
        cell_vars.append(sum(vs) / len(vs))
        out["variance"].append({"u": u, "diff_mean": cell_means[-1], "diff_var_mean": cell_vars[-1]})
    sigma2 = sum(cell_vars) / len(cell_vars)
    tau2 = float(np.var(cell_means, ddof=1))
    n_star = math.sqrt(sigma2 / tau2) if tau2 > 0 else float("inf")
    print("   within-cell sigma^2 = %.6g   between-cell tau^2 = %.6g   sigma^2/tau^2 = %.4g"
          % (sigma2, tau2, sigma2 / tau2))
    print("   -> spike_v1's law at a = b: N* = sqrt(sigma^2/tau^2) = %.4g repeats per item" % n_star)
    out["certificates"]["sigma2_measured"] = sigma2
    out["certificates"]["tau2_measured"] = tau2
    out["certificates"]["n_star_measured"] = n_star

    print()
    print("6. THE ITEM AXIS -- the term the population closed form drops, and what sets its size")
    print("   At fixed u the omitted-block/test-noise cross term is a per-test-set draw; its RMS over")
    print("   test sets is the ITEM axis' own contribution to a comparison's apparent gap. The repeat")
    print("   axis cannot shrink it -- every run shares the one test set -- so it is bought only with")
    print("   test data, which is the other end of spike_v1's N* trade.")
    base_u = 0.80
    K_ITEM = 96
    print("   N_TEST    |cross| rms    |cross|/pop    (K = %d test sets per cell)" % K_ITEM)
    item_rows = []
    for nt in ITEM_N_TESTS:
        acc = 0.0
        pops = []
        for k in range(K_ITEM):
            rng = np.random.default_rng(cell_seed("item", nt, base_u, k))
            cell = make_cell(rng, N_TRAIN, base_u, n_test=nt)
            acc += cell["cross_term"] ** 2
            pops.append(cell["delta_pop"])
        rms = math.sqrt(acc / K_ITEM)
        pop = sum(pops) / len(pops)
        item_rows.append({"n_test": nt, "cross_rms": rms, "delta_pop": pop,
                          "cross_over_pop": rms / pop if pop > 0 else float("nan")})
        print("   %-9d %-15.5g %-14.4f" % (nt, rms, item_rows[-1]["cross_over_pop"]))
    # the law is a 1/sqrt(N_TEST) decay: fit the exponent on the log-log line
    xs = [math.log(r["n_test"]) for r in item_rows]
    ys = [math.log(r["cross_rms"]) for r in item_rows]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    assert_item_law(slope)
    out["item_axis"] = item_rows
    out["certificates"]["item_axis_slope"] = slope
    print("   -> fitted exponent d log|cross| / d log N_TEST = %.3f (the 1/sqrt law is -0.500)" % slope)

    # ------------------------------------------------------------- certificates + controls
    print()
    print("CERTIFICATE -- E[mA] and E[mB] each match their EXACT conditional closed form")
    print("   (a per-cell DECOMPOSITION: it shows the cross term is owed, it does not assert it)")
    print("   u    |  E[mA] measured  exact pred    z     |  E[mB] measured  exact pred    z")
    worst_dc = 0.0
    for u in U_CELLS:
        ms = [m for m in out["means"] if m["u"] == u]
        row = []
        for km, kp, kv in (("mA_mean", "pred_mse_A", "mA_var"),
                           ("mB_mean", "pred_mse_B", "mB_var")):
            meas = sum(m[km] for m in ms) / len(ms)
            pred = sum(m[kp] for m in ms) / len(ms)
            se = math.sqrt(sum(m[kv] for m in ms) / len(ms) / R_RUNS / len(ms))
            z = assert_decomp(u, km[:2], meas, pred, se)
            worst_dc = max(worst_dc, z)
            row.append((meas, pred, z))
        print("   %-4.2f |  %-14.6g %-13.6g %-5.2f |  %-14.6g %-13.6g %-5.2f"
              % (u, row[0][0], row[0][1], row[0][2], row[1][0], row[1][1], row[1][2]))
    out["certificates"]["decomposition_worst_z"] = worst_dc
    assert worst_dc < 4.0, "the exact conditional closed form does not match E[mA] / E[mB]"

    print()
    print("CERTIFICATE -- p reproduces WITHIN a cell: one test set, two independent training halves")
    print("   (comparing p_hat across DIFFERENT test sets measures the BETWEEN-cell spread tau^2,")
    print("    which section 5 reports separately -- not reproducibility)")
    worst_p = 0.0
    for u in U_CELLS:
        rng = np.random.default_rng(cell_seed("cell", N_TRAIN, u, 0))
        cell = make_cell(rng, N_TRAIN, u)
        v1, v2 = [], []
        for i in range(R_RUNS):
            _mA, _mB, v = one_run(rng, cell, N_TRAIN)
            (v1 if i % 2 == 0 else v2).append(v)
        n = len(v1)
        p1 = 1.0 - sum(v1) / n
        p2 = 1.0 - sum(v2) / n
        pb = 0.5 * (p1 + p2)
        ev = pb * n
        if ev < RES_MIN_EVENTS:
            print("   u=%-4.2f  p1=%.4f  p2=%.4f  (%.1f events in a half -- resolution-limited, skipped)"
                  % (u, p1, p2, ev))
            continue
        sd = math.sqrt(max(pb * (1 - pb), 1e-12) / n)
        z = assert_p_repro(u, p1, p2, n)
        worst_p = max(worst_p, z)
        print("   u=%-4.2f  p1=%.4f  p2=%.4f  |d| = %.2f sd  (%.0f events)" % (u, p1, p2, z, ev))
    out["certificates"]["p_within_cell_max_z"] = worst_p
    assert worst_p < 4.0, "p does not reproduce within a cell across independent training halves"

    print()
    print("CERTIFICATE -- the exact conditional closed form predicts the measured delta")
    worst_d = 0.0
    for c in out["cells"]:
        se_mean = c["se"] / math.sqrt(N_REPS)
        z = assert_delta_matches(c["u"], c["pred_delta"], c["measured_delta"], se_mean)
        worst_d = max(worst_d, z)
        print("   u=%-4.2f  exact %-12.6g  measured %-12.6g  |d| = %.2f sd"
              % (c["u"], c["pred_delta"], c["measured_delta"], z))
    out["certificates"]["delta_worst_z"] = worst_d
    assert worst_d < 4.0, "the exact conditional closed form does not predict the measured delta"

    print()
    print("CONTROL -- planted truth (two-sided)")
    # (C1) u = 0 (gamma = 0): the pure variance penalty -- p must be SMALL
    m0 = [m for m in out["means"] if m["u"] == 0.0][0]
    # (C2) u = 0.99: near the crossing -- p must be LARGE (the run can hardly tell)
    m1 = [m for m in out["means"] if m["u"] == 0.99][0]
    e3_0, _ = majority_strict(3, p_mean[0.0])
    e3_1, _ = majority_strict(3, p_mean[0.99])
    out["controls"] = {"p_u0": p_mean[0.0], "p_u99": p_mean[0.99],
                       "N3_err_u0": e3_0, "N3_err_u99": e3_1,
                       "delta_u0": m0["diff_mean"], "delta_u99": m1["diff_mean"]}
    print("   u = 0.00 -> p = %.4f  (small: the true gap dominates the run noise)" % p_mean[0.0])
    print("   u = 0.99 -> p = %.4f  (large: the run can hardly tell)" % p_mean[0.99])
    print("   N = 3 majority error: %.5f (easy) vs %.5f (near the crossing)" % (e3_0, e3_1))
    assert p_mean[0.0] < 0.05, "the gamma = 0 control is not easy -- the run noise dominated"
    assert p_mean[0.99] > p_mean[0.0], "p did not rise as the difficulty approached the crossing"
    assert e3_0 < e3_1, "the law did not order the easy and near-crossing cells"

    print()
    print("7. THE CONDITIONAL CROSSING IS A CONSTRUCT, NOT A DRAW")
    print("   A grid cannot place a cell on the conditional crossing: the item-axis cross term moves")
    print("   the crossing cell's delta by ~7.9e-3 while resolving it needs 6.0e-4.  So each rep's")
    print("   test set is drawn once, the u that zeroes ITS exact conditional delta is solved in")
    print("   closed form, and the run happens there.  The measured delta must then be zero -- that")
    print("   is the reading that can falsify the conditional truth (the population crossing at")
    print("   u = 1 is off by ~9 se here, so the check is not vacuous).")
    worst_x = 0.0
    out["crossing"] = []
    for rep in range(N_REPS):
        rng = np.random.default_rng(cell_seed("cross", N_TRAIN, rep))
        probe = make_cell(rng, N_TRAIN, 1.0)      # u only scales gam; the root's inputs are u-free
        u = crossing_u(probe)
        cell = with_gam(probe, u * probe["gam_star"])
        diffs = []
        for _ in range(R_RUNS):
            mA, mB, _v = one_run(rng, cell, N_TRAIN)
            diffs.append(mB - mA)
        meas = float(np.mean(diffs))
        se = math.sqrt(float(np.var(diffs, ddof=1)) / R_RUNS)
        z = assert_crossing_measures_zero(u, meas, se)
        worst_x = max(worst_x, z)
        out["crossing"].append({"rep": rep, "u_star": u, "pred_delta": cell["pred_delta"],
                                "measured_delta": meas, "se": se, "z_vs_zero": z,
                                "delta_pop": cell["delta_pop"]})
        print("   rep %d | u* = %.5f | exact delta = %+.2e | measured = %+.3e (se %.2e) | "
              "|z| = %.2f | population form reads %+.3e = %+.1f se AWAY from zero"
              % (rep, u, cell["pred_delta"], meas, se, z, cell["delta_pop"],
                 abs(cell["delta_pop"]) / se))
    out["certificates"]["crossing_worst_z"] = worst_x
    print("   -> worst |z| vs zero over %d reps: %.2f (bar 4.0)" % (N_REPS, worst_x))

    with open(os.path.join(HERE, "spike_v2_results.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print()
    print("wrote spike_v2_results.json")
    return 0


# ------------------------------------------------------------- self-test (planted defects)
def selftest():
    print("=" * 112)
    print("SELFTEST -- plant a defect per certificate and require it to FIRE, AND require the healthy")
    print("            case to HOLD (a plant that fires on everything is decoration too)")
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError as e:
            print("[%-26s] FIRED: %s" % (name, str(e)[:58]))
            return
        print("[%-26s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-26s] holds (no fire)" % name)
        except AssertionError as e:
            print("[%-26s] *** FIRED ON A HEALTHY CASE *** %s" % (name, str(e)[:40]))
            ok = False

    # 1. truth: a RESOLVED cell whose measured delta carries the wrong sign
    fires("truth-resolved-sign", lambda: assert_resolved_sign(0.8, +0.0100, -0.0020, 0.0010))
    holds("truth-resolved-sign/ok", lambda: assert_resolved_sign(0.8, +0.0100, +0.0090, 0.0010))

    # 2. decomposition: THE population closed form -- the one that drops the cross term -- against
    #    the measurement.  Synthetic inputs; this is the plant that catches the class of defect this
    #    round found in the truth (a term is owed and the form does not carry it), so it must fire.
    fires("decomposition-omits-cross",
          lambda: assert_decomp(0.8, "mA", 0.0212, 0.0119, 0.0005))
    holds("decomposition-keeps-cross",
          lambda: assert_decomp(0.8, "mA", 0.0212, 0.0213, 0.0005))

    # 2b. the TRAINING-side tail term: the real R = 12000 numbers at u = 0.80, where the form
    #     without M_TAIL*gam^2*cA reads 1.0542537 against a measured 1.0548433 (se 9.27e-5) = 6.4 sd.
    fires("decomposition-omits-tail-noise",
          lambda: assert_decomp(0.8, "mA", 1.0548433, 1.0542537, 9.27e-5))
    holds("decomposition-keeps-tail-noise",
          lambda: assert_decomp(0.8, "mA", 1.0548433, 1.0549151, 9.27e-5))

    # 2c. the Jensen/conditioning plant for criterion (ii) -- the round's second finding.  The real
    #     u = 0.50, N = 5 numbers: the law read at the cell's AVERAGED p (0.100) gives 0.0082 while
    #     the observation is 0.0132 over 9600 blocks; read as the mixture of the four per-test-set
    #     laws it gives 0.0131.  The defect is conditioning the two sides on different objects.
    fires("law-at-mean-p-jensen",
          lambda: assert_law_matches(0.00815, 0.01323, 9600))
    holds("law-as-per-rep-mixture",
          lambda: assert_law_matches(0.01309, 0.01323, 9600))

    # 2d. the conditional crossing: a cell built at its own root measures zero, while the population
    #     form's reading for the same cell is 5 se away (rep 0 of section 7).
    fires("crossing-population-form",
          lambda: assert_crossing_measures_zero(0.98506, 9.849e-04, 1.93e-04))
    holds("crossing-constructed/ok",
          lambda: assert_crossing_measures_zero(0.98506, -1.308e-04, 1.93e-04))

    # 3. p within one cell (one test set, two independent training halves)
    fires("p-within-cell", lambda: assert_p_repro(0.8, 0.10, 0.20, 300))
    holds("p-within-cell/ok", lambda: assert_p_repro(0.8, 0.10, 0.11, 300))

    # 4. the exact conditional closed form vs the measured delta
    fires("delta-vs-exact", lambda: assert_delta_matches(0.8, 0.0119, 0.0212, 0.0005))
    holds("delta-vs-exact/ok", lambda: assert_delta_matches(0.8, 0.0119, 0.0121, 0.0005))

    # 5. the item axis falls as 1/sqrt(N_TEST): a log-log slope of -1/2
    fires("item-axis-law", lambda: assert_item_law(-0.05))     # flat: the item axis does nothing
    holds("item-axis-law/ok", lambda: assert_item_law(-0.500))

    # 6. the two controls that read the DGP, not a certificate
    def plant_easy_control():
        assert 0.32 < 0.05, "the gamma = 0 control is not easy -- the run noise dominated"
    fires("easy-control", plant_easy_control)

    def plant_ordering():
        p0, p99 = 0.40, 0.02               # inverted: p FELL with difficulty
        assert p99 > p0, "p did not rise as the difficulty approached the crossing"
    fires("difficulty-ordering", plant_ordering)

    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CERTIFICATE IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
