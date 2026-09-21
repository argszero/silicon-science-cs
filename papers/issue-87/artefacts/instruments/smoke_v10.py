#!/usr/bin/env python3
"""Issue #87 -- R396: was R395's PIT audit VALID?  An out-of-sample audit that plugs in parameters estimated
from a DIFFERENT finite sample charges the model for the estimation error of the fit.

WHY THIS ROUND EXISTS.  R395 replaced the empirical band with a fitted smooth null.  Its size was
conservative (3.33 %) and its detector fired, but it failed two audits, and the round reported "the fitted
null's SHAPE is wrong" as a finding (5.0 % above the 95th percentile vs 2.1 % below the 5th, PIT KS 0.1903,
p ~ 0).  This round asked the opposite question about the same evidence: is that audit valid?

The audit fits the null to 40 calibration draws and then takes the probability-integral transform of 20
INDEPENDENT validation draws.  The measured disagreement between those two samples is large: per bandwidth the
calibration MAD-based scale is 0.81x to 3.11x the validation family's, and the locations differ by up to
0.63 of a bandwidth scale.  Both families are heavy-tailed (R393 measured kurtosis 6-30), so at n = 40 the
scale estimator is itself noisy.  An audit that plugs in the estimated parameters therefore tests the model
AND the estimation error together, and at this sample size the second term can dominate.

WHAT IS MEASURED HERE.

  E1  Identity: R395's plug-in PIT statistic is recomputed from the committed draws and must reproduce
      KS = 0.1903 exactly (a new instrument that cannot reproduce the old number is measuring something else).
  E2  The procedure's OWN reference distribution: simulate the whole audit -- draw 40 calibration + 20
      validation cells per bandwidth from a KNOWN null, fit exactly as R395 did, compute the PIT KS -- and
      report where the observed 0.1903 falls in that reference.  Repeated for three candidate truths (the
      fitted shape, a normal, and a heavier-tailed variant), so the reference is not anchored on the fitted
      shape alone.
  E3  The corrected instrument: a PREDICTIVE null, which propagates the estimation error -- bootstrap the
      calibration draws, refit location and scale, then draw a new cell mean from the fitted shape.  A new
      cell IS one draw of this kind, so this is the distribution the band should have been.
  E4  Sizes of the plug-in and predictive instruments on the same 240 validation cells, each judged against
      its own simulated reference.
  E5  The corrected read, and the real-grid table.
  E6  Truth sensitivity for E2/E3.

Run:  /usr/bin/python3 smoke_v10.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Reads smoke_v8_results.json (the null draws) and smoke_v9_results.json (R395's report); writes
smoke_v10_results.json.
"""
import hashlib
import io
import json
import math
import os
import sys
from math import comb

import numpy as np

import smoke_v5 as S5
import smoke_v7 as S7
import smoke_v8 as S8
import smoke_v9 as S9

HERE = os.path.dirname(os.path.abspath(__file__))
SRC8 = os.path.join(HERE, "smoke_v8_results.json")
SRC9 = os.path.join(HERE, "smoke_v9_results.json")
OUT = os.path.join(HERE, "smoke_v10_results.json")

CONVS = ("shifted", "unshifted")
GAMMAS = tuple(g for g in S5.GAMMAS if g > 0.0)
Q_LEVELS = (0.05, 0.10)
N_SIM_PRED = 2000        # predictive draws per bandwidth
N_REP_AUDIT = 100        # repetitions of the simulated audit for the reference distribution
SHAPE_STARTS = (-1.0, -0.5, 0.0, 0.5, 1.0)


# ------------------------------------------------------------------ location/scale given a fixed shape
def fit_loc_scale_quantile(x, shape, qs=(0.25, 0.75)):
    """Robust closed-form location and scale for a FIXED shape, by matching the sample quantiles to the
    shape's own quantiles.  A quantile-matching (L-) estimator: cheap, and it needs no likelihood surface,
    which matters because the predictive null needs thousands of refits per bandwidth."""
    x = np.asarray(x, dtype=float)
    sq = np.quantile(x, qs)
    zq = S9.shash_ppf(np.array(qs), dict(family="shash", eps=shape["eps"], delta=shape["delta"],
                                        mu=0.0, sigma=1.0))
    if zq[1] - zq[0] <= 0:
        return float(np.median(x)), float(x.std(ddof=1)) or 1.0
    sigma = float((sq[1] - sq[0]) / (zq[1] - zq[0]))
    mu = float(sq[0] - sigma * zq[0])
    return mu, (sigma if sigma > 0 else 1.0)


def _negll_shape(z, eps, delta):
    f = dict(family="shash", eps=float(eps), delta=float(delta), mu=0.0, sigma=1.0)
    ll = S9.shash_logpdf(z, f)
    return 1e12 if not np.all(np.isfinite(ll)) else -float(ll.sum())


def fit_shape(z, starts=SHAPE_STARTS):
    """The two shape parameters, fitted to standardised draws (R395's pooled construction)."""
    z = np.asarray(z, dtype=float)

    def negll(theta):
        eps, ld = theta
        if not (-8.0 < eps < 8.0) or not (-3.0 < ld < 3.0):
            return 1e12
        return _negll_shape(z, eps, math.exp(ld))

    best, bestv = None, math.inf
    for e0 in starts:
        th, v = S9._nelder_mead(negll, np.array([e0, 0.0]), step=0.2, tol=1e-11, max_iter=3000)
        if v < bestv:
            best, bestv = th, v
    return dict(eps=float(best[0]), delta=float(math.exp(best[1])), negloglik=bestv, n=int(len(z)))


def alternating_fit(cal_by_band, n_iter=4, starts=SHAPE_STARTS):
    """R395's named plan: stop using median/MAD, and fit the shape and the per-band location+scale jointly by
    alternating: shape from the standardised draws, location+scale from the quantile match given that shape.
    Starts from each band's median/MAD."""
    shape = dict(eps=0.0, delta=1.0)
    loc = {}
    for g in GAMMAS:
        x = np.asarray(cal_by_band[g], dtype=float)
        med, mad = S9.robust_location_scale(x)
        loc[g] = (med, mad)
    for _ in range(n_iter):
        std = []
        for g in GAMMAS:
            mu, sg = loc[g]
            std.extend(((np.asarray(cal_by_band[g], dtype=float) - mu) / sg).tolist())
        shape = fit_shape(std, starts=starts)
        for g in GAMMAS:
            loc[g] = fit_loc_scale_quantile(cal_by_band[g], shape)
    return shape, loc


# ------------------------------------------------------------------ the two nulls and their p-values
def plug_in_fit(cal_by_band, starts=SHAPE_STARTS):
    """R395's instrument, reproduced EXACTLY: per-band median/MAD location and scale, with the shape fitted
    to the standardised draws.  Kept so the old number can be reproduced (E1) rather than described -- the
    first version of this function forgot the shape fit and silently measured a NORMAL, which is exactly the
    kind of thing an identity control exists to catch."""
    loc = {}
    for g in GAMMAS:
        loc[g] = S9.robust_location_scale(np.asarray(cal_by_band[g], dtype=float))
    std = []
    for g in GAMMAS:
        mu, sg = loc[g]
        std.extend(((np.asarray(cal_by_band[g], dtype=float) - mu) / sg).tolist())
    shape = fit_shape(std, starts=starts)
    out = {g: dict(family="shash", eps=shape["eps"], delta=shape["delta"],
                   mu=loc[g][0], sigma=loc[g][1]) for g in GAMMAS}
    return shape, out


def predictive_draws(cal_band, shape, n_sim=N_SIM_PRED, seed=0):
    """The PREDICTIVE null: propagate the estimation error.  Bootstrap the calibration draws, refit location
    and scale, then draw one new cell mean from the fitted shape.  A study cell IS one draw of exactly this
    kind, so this is the distribution its threshold should come from -- not the fitted density with the
    parameters frozen at their estimates."""
    x = np.asarray(cal_band, dtype=float)
    rng = np.random.default_rng(seed)
    n = len(x)
    f = dict(family="shash", eps=shape["eps"], delta=shape["delta"], mu=0.0, sigma=1.0)
    out = np.empty(n_sim)
    for i in range(n_sim):
        mu, sg = fit_loc_scale_quantile(x[rng.integers(0, n, n)], shape)
        out[i] = mu + sg * float(S9.shash_ppf(np.array([rng.random()]), f)[0])
    return out


def pred_pvalue(x, draws):
    """Two-sided empirical p-value against the predictive null, with its resolution floor stated."""
    v = np.asarray(draws, dtype=float)
    n = len(v)
    ge = float(np.sum(v >= x) + 1) / (n + 1)
    le = float(np.sum(v <= x) + 1) / (n + 1)
    return float(min(1.0, 2.0 * min(ge, le)))


def pit_of_predictive(val, draws):
    """PIT under the EMPIRICAL predictive distribution (monotone in x, so it is a genuine CDF)."""
    v = np.sort(np.asarray(draws, dtype=float))
    x = np.asarray(val, dtype=float)
    return np.searchsorted(v, x, side="right") / len(v)


def pit_of_plug_in(val, fit):
    return S9.shash_cdf(np.asarray(val, dtype=float), fit)


def pit_decomposition(cal, val, shape_from_cal):
    """Which source produces the PIT failure?  Three readings, each refitting a different part on the
    VALIDATION family itself:
      (a) as R395 did      -- everything from the calibration family;
      (b) location+scale refitted on the validation family, shape from calibration;
      (c) everything refitted on the validation family.
    Under a correct model all three are uniform in expectation; the one whose KS collapses identifies the
    source.  (b) and (c) are in-sample readings, so they bound the failure from below, and the gap between
    (a) and (b) is the part chargeable to estimating location and scale from a different finite sample."""
    def ks_of(fit_fn):
        ps = []
        for g in GAMMAS:
            fit = fit_fn(g)
            ps.extend(pit_of_plug_in(val[g], fit).tolist())
        return S9.ks_stat(ps, lambda v: np.asarray(v, dtype=float)), float(np.mean(ps))

    def fit_a(g):
        return dict(family="shash", eps=shape_from_cal["eps"], delta=shape_from_cal["delta"],
                    mu=S9.robust_location_scale(np.asarray(cal[g], dtype=float))[0],
                    sigma=S9.robust_location_scale(np.asarray(cal[g], dtype=float))[1])

    def fit_b(g):
        mu, sg = fit_loc_scale_quantile(np.asarray(val[g], dtype=float), shape_from_cal)
        return dict(family="shash", eps=shape_from_cal["eps"], delta=shape_from_cal["delta"], mu=mu, sigma=sg)

    std = []
    for g in GAMMAS:
        mu, sg = fit_loc_scale_quantile(np.asarray(val[g], dtype=float), shape_from_cal)
        std.extend(((np.asarray(val[g], dtype=float) - mu) / sg).tolist())
    shape_val = fit_shape(std)
    loc_val = {g: fit_loc_scale_quantile(np.asarray(val[g], dtype=float), shape_val) for g in GAMMAS}

    def fit_c(g):
        return dict(family="shash", eps=shape_val["eps"], delta=shape_val["delta"],
                    mu=loc_val[g][0], sigma=loc_val[g][1])

    ka, ma = ks_of(fit_a)
    kb, mb = ks_of(fit_b)
    kc, mc = ks_of(fit_c)
    return dict(as_in_r395=dict(ks=ka, pit_mean=ma),
                location_scale_refit_on_validation=dict(ks=kb, pit_mean=mb),
                everything_refit_on_validation=dict(ks=kc, pit_mean=mc),
                shape_refit=dict(eps=round(shape_val["eps"], 6), delta=round(shape_val["delta"], 6)))


# ------------------------------------------------------------------ the simulated audit (E2/E3)
def simulate_audit(truth_shape, truth_sigma_scale=1.0, n_rep=N_REP_AUDIT, seed=555, loc_scale=None):
    """Simulate the WHOLE audit under a known truth and return the reference distribution of the plug-in PIT
    KS and of the predictive PIT KS.  The truth is specified as (shape, per-band location/scale), so the
    reference answers: given a correct model of this shape class, how large a KS does this procedure produce
    by itself?"""
    rng = np.random.default_rng(seed)
    ks_plug, ks_pred, loc_err = [], [], []
    shapes = []
    # every "band" is a (convention, bandwidth) pair, so the reference pools the same 2 x 6 bands -- and
    # therefore the same 240 validation cells -- that the observed statistic pools
    for _ in range(n_rep):
        cal, val = {}, {}
        for c in CONVS:
            for i, g in enumerate(GAMMAS):
                if loc_scale is None:
                    mu = 0.25 * (-1) ** i * (1.0 if c == "shifted" else -1.0)
                    sg = truth_sigma_scale * (0.8 + 0.1 * i)
                else:
                    mu, sg = loc_scale[c][g]
                cal[(c, g)] = (mu + sg * S9.shash_ppf(rng.random(40), truth_shape)).tolist()
                val[(c, g)] = (mu + sg * S9.shash_ppf(rng.random(20), truth_shape)).tolist()
        # R395's instrument, run band by band and pooled exactly as the observed statistic is
        plug_rows = {c: plug_in_fit({g: cal[(c, g)] for g in GAMMAS}) for c in CONVS}
        ps = np.concatenate([pit_of_plug_in(val[(c, g)], plug_rows[c][1][g])
                             for c in CONVS for g in GAMMAS])
        ks_plug.append(S9.ks_stat(ps, lambda v: np.asarray(v, dtype=float)))
        shape_p, _ = alternating_fit({g: cal[("shifted", g)] for g in GAMMAS}, n_iter=1)
        pp = np.concatenate([pit_of_predictive(val[(c, g)],
                                              predictive_draws(cal[(c, g)], shape_p, n_sim=200,
                                                               seed=int(rng.integers(0, 10 ** 6))))
                             for c in CONVS for g in GAMMAS])
        ks_pred.append(S9.ks_stat(pp, lambda v: np.asarray(v, dtype=float)))
        # how far a 40-draw calibration fit sits from the truth it was drawn from
        for c in CONVS:
            for i, g in enumerate(GAMMAS):
                mu, sg = (0.25 * (-1) ** i * (1.0 if c == "shifted" else -1.0),
                          truth_sigma_scale * (0.8 + 0.1 * i)) if loc_scale is None else loc_scale[c][g]
                m_hat, s_hat = S9.robust_location_scale(np.asarray(cal[(c, g)], dtype=float))
                loc_err.append(abs(m_hat - mu) / sg)
        shapes.append(shape_p)
    return dict(n_rep=n_rep, n_bands=2 * len(GAMMAS), n_points=2 * len(GAMMAS) * 20,
                plug_in_ks=dict(median=float(np.median(ks_plug)), p90=float(np.percentile(ks_plug, 90)),
                                frac_above_observed=None, n_above_obs=None, values=[round(v, 4) for v in ks_plug]),
                predictive_ks=dict(median=float(np.median(ks_pred)), p90=float(np.percentile(ks_pred, 90)),
                                   frac_above_observed=None, n_above_obs=None, values=[round(v, 4) for v in ks_pred]),
                location_error=dict(median=float(np.median(loc_err)), p90=float(np.percentile(loc_err, 90)),
                                    max=float(np.max(loc_err))),
                shape_recovered=dict(eps_median=float(np.median([s["eps"] for s in shapes])),
                                     delta_median=float(np.median([s["delta"] for s in shapes]))))


def _sign_test_p(v):
    """Two-sided sign test, exact below n = 60 and normal-with-continuity-correction above -- the exact form
    overflows on the synthetic sample (2**n with n in the thousands), which is how this helper was found."""
    v = np.asarray(v, dtype=float)
    k, n = int(np.sum(v > 1)), len(v)
    if n == 0:
        return 1.0, 0, 0
    if n <= 60:
        upper = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
        lower = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
        return min(1.0, 2.0 * min(upper, lower)), k, n
    z = (abs(k - n / 2.0) - 0.5) / (math.sqrt(n) / 2.0)
    return min(1.0, math.erfc(abs(z) / math.sqrt(2.0))), k, n


def dispersion_homogeneity(cal, val, shape_by_conv, n_rep=500, seed=777):
    """Is the null's dispersion the same in the two seed blocks?  The control that decides whether the audit
    failure is a small-sample property of THIS null or the two blocks genuinely differing.

    Three readings of one quantity -- the ratio of dispersions between a 40-draw and a 20-draw block:
      observed   -- the real calibration (40) vs validation (20) block;
      split-half -- the calibration block cut in two (20 vs 20), so NO size difference; anything there is
                    seed structure, not sample size;
      synthetic  -- 60 i.i.d. draws from the fitted null per band, cut 40/20, repeated; this gives the
                    reference distribution of the ratio -- and of the SIGN TEST itself, which is what the
                    observed count must be judged against.
    """
    rng = np.random.default_rng(seed)
    G = list(GAMMAS)
    obs, half = [], []
    pools = {}
    for c in CONVS:
        sh = shape_by_conv[c]
        for g in G:
            a = np.asarray(cal[c][g], dtype=float)
            b = np.asarray(val[c][g], dtype=float)
            obs.append(float(a.std(ddof=1) / b.std(ddof=1)))
            half.append(float(a[:len(a) // 2].std(ddof=1) / a[len(a) // 2:].std(ddof=1)))
            f = dict(family="shash", eps=sh["eps"], delta=sh["delta"], mu=float(np.median(a)),
                     sigma=float(S9.robust_location_scale(a)[1]))
            # ONE inverse-CDF call per band, reshaped into independent 60-draw blocks
            pools[(c, g)] = (f["mu"] + f["sigma"] * S9.shash_ppf(rng.random(60 * n_rep), f)).reshape(n_rep, 60)

    syn_ratios = np.empty((n_rep, len(G) * len(CONVS)))
    col = 0
    for c in CONVS:
        for g in G:
            d = pools[(c, g)]
            syn_ratios[:, col] = d[:, :40].std(axis=1, ddof=1) / d[:, 40:].std(axis=1, ddof=1)
            col += 1
    flat = syn_ratios.ravel()
    p_obs, k_obs, n_obs = _sign_test_p(obs)
    # the split-half test can fall either side of 1, so its direction is reported with it
    
    p_half, k_half, n_half = _sign_test_p(half)
    per_rep = np.sum(syn_ratios > 1, axis=1)
    p_syn = float(np.mean(per_rep >= k_obs))
    return dict(n_bands=n_obs,
                observed=dict(median=float(np.median(obs)), mean=float(np.mean(obs)),
                              frac_above_1=k_obs / n_obs, sign_test_p=p_obs, max=float(np.max(obs)),
                              log_sd=float(np.std(np.log(obs), ddof=1)), ratios=[round(v, 3) for v in obs]),
                split_half_control=dict(median=float(np.median(half)), frac_above_1=k_half / n_half,
                                        sign_test_p=p_half, ratios=[round(v, 3) for v in half],
                                        log_sd=float(np.std(np.log(half), ddof=1))),
                synthetic_same_null=dict(median=float(np.median(flat)), mean=float(np.mean(flat)),
                                         frac_above_1=float(np.mean(flat > 1)), n_draws=int(len(flat)),
                                         log_sd=float(np.std(np.log(flat), ddof=1)),
                                         sign_test_p=p_syn, k_observed=k_obs,
                                         n_bands_synthetic=k_obs))
# ------------------------------------------------------------------ the report
def load_draws():
    raw = json.loads(io.open(SRC8, encoding="utf-8").read())
    cal = {c: {g: list(raw["cal_means"][c][str(g)]) for g in GAMMAS} for c in CONVS}
    val = {c: {g: list(raw["val_means"][c][str(g)]) for g in GAMMAS} for c in CONVS}
    return raw, cal, val


def build_report():
    raw, cal, val = load_draws()
    r9 = json.loads(io.open(SRC9, encoding="utf-8").read())
    obs_ks = r9["controls"]["C3_pit_uniformity_pooled"]["ks"]

    # ---- E1 identity: reproduce R395's plug-in PIT statistic from the committed draws
    plug = {c: plug_in_fit(cal[c]) for c in CONVS}
    ps_plug = np.concatenate([pit_of_plug_in(val[c][g], plug[c][1][g]) for c in CONVS for g in GAMMAS])
    ks_repro = S9.ks_stat(ps_plug, lambda v: np.asarray(v, dtype=float))

    # ---- E2/E3 the procedure's own reference, under three candidate truths
    alt = {c: alternating_fit(cal[c]) for c in CONVS}
    shape_obs = {c: alt[c][0] for c in CONVS}
    truth_fitted = dict(family="shash", eps=float(np.mean([shape_obs[c]["eps"] for c in CONVS])),
                        delta=float(np.mean([shape_obs[c]["delta"] for c in CONVS])), mu=0.0, sigma=1.0)
    truth_normal = dict(family="shash", eps=0.0, delta=1.0, mu=0.0, sigma=1.0)
    truth_heavy = dict(family="shash", eps=-0.6, delta=1.4, mu=0.0, sigma=1.0)
    # the real per-band locations/scales, so the reference matches the study's own geometry
    real_loc_scale = {c: {g: tuple(S9.robust_location_scale(np.asarray(cal[c][g], dtype=float)))
                          for g in GAMMAS} for c in CONVS}
    refs = {}
    for tag, truth in (("fitted", truth_fitted), ("normal", truth_normal), ("heavy", truth_heavy)):
        refs[tag] = simulate_audit(truth, n_rep=N_REP_AUDIT, seed=555 + 17 * len(tag),
                                   loc_scale=real_loc_scale)

    # ---- E3 the predictive null on the REAL draws, with its own PIT
    pred = {c: {g: predictive_draws(cal[c][g], shape_obs[c], n_sim=N_SIM_PRED,
                                    seed=1000 + 7 * i + 31 * (0 if c == "shifted" else 1))
                for i, g in enumerate(GAMMAS)} for c in CONVS}
    ps_pred = np.concatenate([pit_of_predictive(val[c][g], pred[c][g]) for c in CONVS for g in GAMMAS])
    ks_pred_real = S9.ks_stat(ps_pred, lambda v: np.asarray(v, dtype=float))

    # ---- E6 dispersion homogeneity: is the difference between the two seed blocks real?
    disp = dispersion_homogeneity(cal, val, shape_obs)

    # ---- E3c the decomposition, shifted convention (the one R395's audit ran on)
    decomp = pit_decomposition(cal["shifted"], val["shifted"], shape_obs["shifted"])

    # ---- E4b the predictive instrument must FIRE (a conservative null still needs a power curve)
    fire = []
    for u in (1.0, 2.0, 3.0, 5.0):
        k, n = 0, 0
        for c in CONVS:
            for g in GAMMAS:
                sd = float(np.std(pred[c][g], ddof=1))
                for v in val[c][g]:
                    k += int(pred_pvalue(v + u * sd, pred[c][g]) < 0.05)
                    n += 1
        fire.append(dict(shift_pred_sigma=u, n=n, n_fired=k, rate=k / max(1, n), wilson=S8.wilson(k, n)))

    # ---- E4/E5 the real grid, read under both instruments
    q = S9.QUBITS
    edges = S5.edges_for(S9.EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, S9.LAYERS) for g in S5.GAMMAS} for c in CONVS}
    rows = []
    for conv in CONVS:
        for alpha in S9.ALIGNS:
            key = "%s|alpha=%g" % (conv, alpha)
            cell = S9.cell_runner(q, edges, Z, alpha, conv, metrics[conv], S5.SEED_GEN, S9.matched_w)
            for g in GAMMAS:
                m = cell["rows"][g]["mean"]
                kdiff = cell["rows"][g]["kernel_max_absdiff"]
                src = next(x for x in r9["rows"] if x["cell"] == key and x["gamma"] == g)
                rows.append(dict(cell=key, conv=conv, alpha=alpha, gamma=g, delta_mean=m,
                                 kernel_max_absdiff=kdiff,
                                 degenerate=bool(kdiff < S8.KERNEL_SAME_EPS),
                                 p_plug_in=S9.pvalue(m, plug[conv][1][g]),
                                 p_predictive=pred_pvalue(m, pred[conv][g]),
                                 outside_band_r394=src["outside_band_r394"], sign="loss" if m > 0 else "lead"))
    T = [r for r in rows if not r["degenerate"]]
    for tag in ("plug_in", "predictive"):
        qq, _ = S7.bh_qvalues(np.array([r["p_" + tag] for r in T]), 0.05)
        for i, r in enumerate(T):
            r["q_" + tag] = float(qq[i])
    declared = {tag: [r for r in T if r["q_" + tag] <= 0.05] for tag in ("plug_in", "predictive")}

    # ---- sizes on the independent validation family, each against its own reference
    def size_of(ps):
        return float(np.mean(np.asarray(ps) < 0.05))

    size_plug_val = float(np.mean([S9.pvalue(v, plug[c][1][g]) < 0.05 for c in CONVS for g in GAMMAS
                                   for v in val[c][g]]))
    size_pred_val = float(np.mean([pred_pvalue(v, pred[c][g]) < 0.05 for c in CONVS for g in GAMMAS
                                   for v in val[c][g]]))
    n_val = sum(len(val[c][g]) for c in CONVS for g in GAMMAS)

    # ---- E6 truth sensitivity is inside refs (three truths)
    return dict(
        round="R396",
        settings=dict(q=q, edges=S9.EDGE_KIND, layers=S9.LAYERS, convs=list(CONVS), aligns=list(S9.ALIGNS),
                      gammas=list(GAMMAS), n_sim_pred=N_SIM_PRED, n_rep_audit=N_REP_AUDIT,
                      numpy=np.__version__, source="smoke_v8 null draws + smoke_v9 report"),
        controls=dict(
            E1_reproduces_r395=dict(reported_ks_r395=obs_ks, recomputed_ks=float(ks_repro),
                                    matches=bool(abs(obs_ks - ks_repro) < 1e-9)),
            E2_procedure_reference=refs,
            E2_observed_plug_in_ks=dict(observed=float(ks_repro),
                                        rank_in_fitted_reference=None),
            E3_predictive_null=dict(n_sim=N_SIM_PRED,
                                    pool_median=float(np.median(np.concatenate([pred[c][g] for c in CONVS
                                                                                for g in GAMMAS]))),
                                    real_val_pit_ks=float(ks_pred_real),
                                    real_val_pit_mean=float(np.mean(ps_pred)),
                                    real_val_frac_below_005=float(np.mean(ps_pred < 0.05)),
                                    real_val_frac_above_095=float(np.mean(ps_pred > 0.95))),
            E3b_predictive_rank_in_reference=None,
            E3c_source_decomposition_shifted=decomp,
            E6_dispersion_homogeneity=disp,
            E4_sizes=dict(plug_in=size_plug_val, predictive=size_pred_val, n_val=n_val),
            E4b_predictive_fires=fire,
            E5_shapes=dict(**{c: dict(eps=round(shape_obs[c]["eps"], 6),
                                      delta=round(shape_obs[c]["delta"], 6), n=shape_obs[c]["n"])
                              for c in CONVS}),
            E5b_location_scale_gap=dict(
                **{c: [round(float((S9.robust_location_scale(np.asarray(cal[c][g]))[0]
                                    - S9.robust_location_scale(np.asarray(val[c][g]))[0])
                                   / S9.robust_location_scale(np.asarray(cal[c][g]))[1]), 4)
                       for g in GAMMAS] for c in CONVS}),
        ),
        fdr=dict(m=len(T),
                 plug_in=dict(n_declared=len(declared["plug_in"]),
                              n_leads=int(sum(r["sign"] == "lead" for r in declared["plug_in"]))),
                 predictive=dict(n_declared=len(declared["predictive"]),
                                 n_leads=int(sum(r["sign"] == "lead" for r in declared["predictive"]))),
                 predictive_declared=[[r["cell"], r["gamma"], r["delta_mean"], r["p_predictive"],
                                       r["q_predictive"], r["sign"]] for r in declared["predictive"]]),
        rows=rows,
    )


def dumps(rep):
    return json.dumps(rep, sort_keys=True, indent=1)


def main():
    rep = build_report()
    # ranks against the reference distributions are filled here, where the reference values are to hand
    obs_plug = rep["controls"]["E1_reproduces_r395"]["recomputed_ks"]
    vals = rep["controls"]["E2_procedure_reference"]["fitted"]["plug_in_ks"]["values"]
    rep["controls"]["E2_observed_plug_in_ks"]["rank_in_fitted_reference"] = \
        float(np.mean(np.asarray(vals) < obs_plug))
    rep["controls"]["E2_observed_plug_in_ks"]["p_value_vs_fitted_reference"] = \
        float(np.mean(np.asarray(vals) >= obs_plug))
    obs_pred = rep["controls"]["E3_predictive_null"]["real_val_pit_ks"]
    pvals = rep["controls"]["E2_procedure_reference"]["fitted"]["predictive_ks"]["values"]
    rep["controls"]["E3b_predictive_rank_in_reference"] = float(np.mean(np.asarray(pvals) < obs_pred))
    rep["controls"]["E3b_predictive_p_value"] = float(np.mean(np.asarray(pvals) >= obs_pred))
    a = dumps(rep)
    rep["report_sha256"] = hashlib.sha256(a.encode()).hexdigest()
    io.open(OUT, "w", encoding="utf-8").write(dumps(rep) + "\n")
    write_text(rep)
    return 0


def write_text(rep):
    c = rep["controls"]
    print("=" * 100)
    print("ISSUE #87 -- R396: was the PIT audit VALID?  plug-in parameters vs a PREDICTIVE null")
    print("=" * 100)
    e1 = c["E1_reproduces_r395"]
    print("E1 identity: R395 reported KS=%.4f, recomputed %.4f  match=%s"
          % (e1["reported_ks_r395"], e1["recomputed_ks"], e1["matches"]))
    print()
    print("-- E2 the AUDIT'S OWN reference distribution (simulated under a known truth) ---------------")
    for tag in ("fitted", "normal", "heavy"):
        r = c["E2_procedure_reference"][tag]
        print("   truth=%-7s plug-in PIT KS: median %.3f p90 %.3f | predictive PIT KS: median %.3f p90 %.3f"
              % (tag, r["plug_in_ks"]["median"], r["plug_in_ks"]["p90"],
                 r["predictive_ks"]["median"], r["predictive_ks"]["p90"]))
    print("   observed plug-in KS = %.4f  (R395 read this as 'the shape is wrong')" % e1["recomputed_ks"])
    print("   location error of a 40-draw fit, in bandwidth sigmas: median %.3f p90 %.3f max %.3f"
          % (c["E2_procedure_reference"]["fitted"]["location_error"]["median"],
             c["E2_procedure_reference"]["fitted"]["location_error"]["p90"],
             c["E2_procedure_reference"]["fitted"]["location_error"]["max"]))
    print()
    print("-- E3 the PREDICTIVE null (estimation error propagated) on the REAL draws ------------------")
    e3 = c["E3_predictive_null"]
    print("   PIT of the 240 validation cells under it: KS=%.4f mean=%.4f  frac<0.05=%.4f frac>0.95=%.4f"
          % (e3["real_val_pit_ks"], e3["real_val_pit_mean"], e3["real_val_frac_below_005"],
             e3["real_val_frac_above_095"]))
    print("   rank of that KS inside the simulated reference: %.2f" % c["E3b_predictive_rank_in_reference"])
    print()
    print("-- E3c which source produces the PIT failure (shifted convention) ----------------------")
    d = c["E3c_source_decomposition_shifted"]
    print("   (a) everything from calibration (as R395 did) : KS %.4f  mean PIT %.4f" % (d["as_in_r395"]["ks"], d["as_in_r395"]["pit_mean"]))
    print("   (b) location+scale refit on validation       : KS %.4f  mean PIT %.4f" % (d["location_scale_refit_on_validation"]["ks"], d["location_scale_refit_on_validation"]["pit_mean"]))
    print("   (c) shape refit on validation too            : KS %.4f  mean PIT %.4f" % (d["everything_refit_on_validation"]["ks"], d["everything_refit_on_validation"]["pit_mean"]))
    print("   shape fitted on validation draws: eps=%+.4f delta=%.4f" % (d["shape_refit"]["eps"], d["shape_refit"]["delta"]))
    print()
    print("-- E6 is the difference between the two seed blocks real?  (40-draw vs 20-draw dispersion) --")
    dd = c["E6_dispersion_homogeneity"]
    o, h, s = dd["observed"], dd["split_half_control"], dd["synthetic_same_null"]
    print("   observed   cal(40) vs val(20): median %.2f  frac>1 %.2f  sign-test p=%.3f  log-sd %.3f"
          % (o["median"], o["frac_above_1"], o["sign_test_p"], o["log_sd"]))
    print("   split-half cal(20) vs cal(20): median %.2f  frac>1 %.2f  sign-test p=%.3f  log-sd %.3f"
          % (h["median"], h["frac_above_1"], h["sign_test_p"], h["log_sd"]))
    print("   synthetic 40 vs 20 from the fitted null itself: median %.2f  frac>1 %.2f  sign-test p=%.3f"
          % (s["median"], s["frac_above_1"], s["sign_test_p"]))
    print()
    print("-- E4b the predictive null must still FIRE ----------------------------------------------")
    for r in c["E4b_predictive_fires"]:
        print("   shift %.1f sigma_pred -> %d/%d declared (%.3f) Wilson95 [%.3f,%.3f]"
              % (r["shift_pred_sigma"], r["n_fired"], r["n"], r["rate"], r["wilson"][0], r["wilson"][1]))
    print()
    print("-- E4/E5 sizes and shapes ------------------------------------------------------------------")
    e4 = c["E4_sizes"]
    print("   size on %d independent null cells: plug-in %.4f | predictive %.4f" % (e4["n_val"],
                                                                                    e4["plug_in"], e4["predictive"]))
    for cc, sh in sorted(c["E5_shapes"].items()):
        print("   %-9s pooled shape eps=%+.4f delta=%.4f (n=%d)" % (cc, sh["eps"], sh["delta"], sh["n"]))
    print()
    print("-- the real read --------------------------------------------------------------------------")
    f = rep["fdr"]
    print("   plug-in    declared %d (%d leads) | predictive declared %d (%d leads)"
          % (f["plug_in"]["n_declared"], f["plug_in"]["n_leads"],
             f["predictive"]["n_declared"], f["predictive"]["n_leads"]))
    for row in sorted(f["predictive_declared"], key=lambda r: r[3])[:12]:
        print("     %-18s gamma=%4.2f delta %+0.4f p=%.4f q=%.4f %s"
              % (row[0], row[1], row[2], row[3], row[4], row[5]))
    print()
    print("   report sha256 = %s" % rep["report_sha256"])
    print("   written to %s" % os.path.basename(OUT))


if __name__ == "__main__":
    sys.exit(main())
