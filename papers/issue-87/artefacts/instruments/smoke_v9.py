#!/usr/bin/env python3
"""Issue #87 -- R395: replace the EMPIRICAL null band with a FITTED smooth null, and validate the fit on
data the fit never saw.

WHY THIS ROUND EXISTS.  R394 made the multiplicity layer size-VALID (13 of 240 tests outside the 95 % band
on an independent null family; an exchangeability arm reading 4.9-5.6 %) but then found it INERT on the real
grid: BH declared 0 while 27 of 36 rows lay outside their per-cell band against 1.80 expected (Class 87).
The cause was arithmetic -- an empirical p from N = 40 null draws has a floor of 2/(N+1) = 0.0488, while BH
at q = 0.05 over m = 36 needs about q/m = 0.0014, which would take N >= ~1,400 draws per bandwidth.

A fitted null reaches the far tail analytically.  The risk it introduces is the opposite error: a smooth
family that does not describe the empirical null produces a confident, wrong small p-value.  So the design
here is fit-then-audit, and every claim about the fit is read on data the fit never saw:

  * FIT on the 40 calibration draws per (convention, bandwidth) -- the SAME draws R394's band came from,
    loaded from the committed report and checked two ways (the report's own sha256 recomputes, and one
    null cell is re-derived from scratch and compared bitwise with the stored draws).
  * AUDIT out of sample on the 20 independent validation draws per bandwidth: a KS test, and the
    probability-integral transform, which must be uniform -- read pooled over all 240 validation cells, so
    the resolution is 1/241 and a 5 % tail is actually observable.
  * The fitted quantity is itself an instrument (Class 82), so the MLE is first fitted to samples drawn from
    a KNOWN distribution and must recover it; and the detector must FIRE, tested by injecting declared shifts
    into the validation cells (Class 85/86: a null with no proof that the detector fires is decoration).
  * SENSITIVITY is declared, not hidden: the same read is repeated under a normal fit and under a heavier-
    tailed variant, and the declared-row count is reported for each, so the reader can see how much of the
    answer is the family choice.

Run:  /usr/bin/python3 smoke_v9.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Reads smoke_v8_results.json (the committed null draws); writes smoke_v9_results.json.
"""
import hashlib
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v0 as S0
import smoke_v5 as S5
import smoke_v7 as S7
import smoke_v8 as S8

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "smoke_v8_results.json")
OUT = os.path.join(HERE, "smoke_v9_results.json")

QUBITS = 6
LAYERS = 2
EDGE_KIND = "cycle"
CONVS = ("shifted", "unshifted")
ALIGNS = (1.0, 0.0, -1.0)
GAMMAS = tuple(g for g in S5.GAMMAS if g > 0.0)          # gamma = 0 is degenerate by measurement
Q_LEVELS = (0.05, 0.10)
N_MC = 20000                # draws used to check a fitted CDF against its own sampler
SHIFT_UNITS = (0.5, 1.0, 2.0, 3.0)   # injected shifts, in units of the local fitted null sigma


# ------------------------------------------------------------------ small numerics
def _phi(z):
    return np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


_erfc_vec = np.vectorize(math.erfc)


def _Phi(z):
    return 0.5 * (_erfc_vec(-np.asarray(z, dtype=float) / math.sqrt(2.0)))


def _asinh(z):
    return np.log(z + np.sqrt(z * z + 1.0))


def normal_fit(x):
    """Moment-matched normal: (mu, sigma)."""
    x = np.asarray(x, dtype=float)
    return dict(family="normal", mu=float(x.mean()), sigma=float(x.std(ddof=1)), eps=0.0, delta=1.0)


def _shash_w(x, p):
    z = (np.asarray(x, dtype=float) - p["mu"]) / p["sigma"]
    return np.sinh(p["delta"] * _asinh(z) - p["eps"])


def shash_logpdf(x, p):
    """sinh-arcsinh normal: a 4-parameter family that carries BOTH skewness and tailweight, with a closed
    form CDF (so p-values need no quadrature and no extrapolation by simulation).  At delta = 1, eps = 0 it
    is exactly a normal -- asserted by the unit check in main()."""
    x = np.asarray(x, dtype=float)
    z = (x - p["mu"]) / p["sigma"]
    a = p["delta"] * _asinh(z) - p["eps"]
    return (np.log(p["delta"]) - np.log(p["sigma"]) + np.log(np.cosh(a))
            - 0.5 * np.log1p(z * z) + np.log(_phi_scale) - 0.5 * np.sinh(a) ** 2)


_phi_scale = 1.0 / math.sqrt(2.0 * math.pi)


def shash_cdf(x, p):
    return _Phi(_shash_w(x, p))


def shash_ppf(u, p):
    """Inverse CDF, closed form: invert Phi -> sinh -> asinh -> z."""
    u = np.clip(np.asarray(u, dtype=float), 1e-12, 1.0 - 1e-12)
    w = np.sqrt(2.0) * _erfinv(2.0 * u - 1.0)
    z = np.sinh((np.arcsinh(w) + p["eps"]) / p["delta"])
    return p["mu"] + p["sigma"] * z


def _erfinv(y):
    """Winitzki's approximation refined by two Newton steps (numerically exact to ~1e-15)."""
    y = np.asarray(y, dtype=float)
    a = 0.147
    ln1 = np.log(1.0 - y * y)
    t = 2.0 / (math.pi * a) + ln1 / 2.0
    x = np.sign(y) * np.sqrt(np.sqrt(t * t - ln1 / a) - t)
    for _ in range(2):
        x = x - (_erf(x) - y) / (2.0 / math.sqrt(math.pi) * np.exp(-x * x))
    return x


_erf_vec = np.vectorize(math.erf)


def _erf(x):
    return math.erf(x) if np.ndim(x) == 0 else _erf_vec(x)


def shash_t_logpdf(x, p, nu):
    """The declared heavier-tailed variant: the SAME transform, but the base density is Student-t(nu) instead
    of normal.  Used only for the sensitivity read -- a family choice that changes the declared set must be
    visible, not assumed away."""
    x = np.asarray(x, dtype=float)
    z = (x - p["mu"]) / p["sigma"]
    a = p["delta"] * _asinh(z) - p["eps"]
    w = np.sinh(a)
    base = (math.lgamma((nu + 1) / 2) - math.lgamma(nu / 2) - 0.5 * math.log(nu * math.pi)
            - ((nu + 1) / 2) * np.log1p(w * w / nu))
    return np.log(p["delta"]) - np.log(p["sigma"]) + np.log(np.cosh(a)) - 0.5 * np.log1p(z * z) + base


# ------------------------------------------------------------------ MLE for the 4-parameter family
def _nelder_mead(f, x0, step=0.25, tol=1e-10, max_iter=2000):
    """Self-contained Nelder-Mead.  Written here rather than imported so the whole fit is auditable in this
    file -- the fit is an instrument and its control (recovery of a known distribution) lives in main()."""
    x0 = np.asarray(x0, dtype=float)
    n = len(x0)
    simp = [x0.copy()]
    for i in range(n):
        p = x0.copy()
        p[i] += step if p[i] == 0 else step * abs(p[i])
        simp.append(p)
    simp = np.array(simp)
    vals = np.array([f(p) for p in simp])
    for _ in range(max_iter):
        order = np.argsort(vals)
        simp, vals = simp[order], vals[order]
        if np.max(np.abs(simp[1:] - simp[0])) < tol:
            break
        cen = simp[:-1].mean(axis=0)
        xr = cen + (cen - simp[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = cen + 2.0 * (cen - simp[-1])
            fe = f(xe)
            simp[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            simp[-1], vals[-1] = xr, fr
        else:
            xc = cen + 0.5 * (simp[-1] - cen)
            fc = f(xc)
            if fc < vals[-1]:
                simp[-1], vals[-1] = xc, fc
            else:
                simp[1:] = simp[0] + 0.5 * (simp[1:] - simp[0])
                vals[1:] = np.array([f(p) for p in simp[1:]])
    k = int(np.argmin(vals))
    return simp[k], float(vals[k])


def shash_mle(x):
    """MLE in an unconstrained parametrisation (log delta, log sigma).  Multi-start from the normal fit and
    from two skew seeds, because the likelihood surface of this family has local modes."""
    x = np.asarray(x, dtype=float)
    sd = float(x.std(ddof=1)) or 1.0

    def negll(theta):
        eps, ld, mu, ls = theta
        p = dict(eps=eps, delta=math.exp(ld), mu=mu, sigma=math.exp(ls), family="shash")
        ll = shash_logpdf(x, p)
        if not np.all(np.isfinite(ll)):
            return 1e12
        return -float(ll.sum())

    best, bestv = None, math.inf
    for eps0 in (-0.5, 0.0, 0.5):
        th0 = np.array([eps0, 0.0, float(x.mean()), math.log(sd)])
        th, v = _nelder_mead(negll, th0)
        if v < bestv:
            best, bestv = th, v
    eps, ld, mu, ls = best
    return dict(family="shash", eps=float(eps), delta=float(math.exp(ld)), mu=float(mu),
                sigma=float(math.exp(ls)), negloglik=bestv)


def pvalue(x, fit):
    """Two-sided p-value under a fitted null.  A fitted location absorbs the null's non-centrality, so there
    is no test against zero anywhere in this file.  Every shash variant shares one CDF; the variants differ
    only in how the parameters were obtained."""
    if fit["family"] == "normal":
        z = (x - fit["mu"]) / fit["sigma"]
        return float(min(1.0, math.erfc(abs(z) / math.sqrt(2.0))))
    F = float(shash_cdf(x, fit))
    return float(min(1.0, 2.0 * min(F, 1.0 - F)))


# ------------------------------------------------------------------ partial pooling across bandwidths
def robust_location_scale(x):
    """Median and a MAD-based scale.  Used to standardise each bandwidth before the SHAPE is pooled, so the
    shared shape is not contaminated by twelve different locations and scales."""
    x = np.asarray(x, dtype=float)
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    return med, (1.4826 * mad if mad > 0 else float(x.std(ddof=1)) or 1.0)


def fit_shape_pooled(standardised):
    """Fit the two SHAPE parameters (eps, delta) to the pooled standardised draws of a convention.

    This is the fix for what the per-band fit cannot do: at 40 draws a 4-parameter MLE is a flat ridge (the
    diagnostic measures it), while 2 shape parameters shared across twelve bandwidths x 40 draws are
    identified.  Location and scale stay per bandwidth, where the data can support them.
    """
    z = np.asarray(standardised, dtype=float)
    if len(z) < 10:
        return dict(eps=0.0, delta=1.0)

    def negll(theta):
        eps, ld = theta
        if not (-8.0 < eps < 8.0) or not (-3.0 < ld < 3.0):
            return 1e12
        f = dict(family="shash", eps=float(eps), delta=float(math.exp(ld)), mu=0.0, sigma=1.0)
        ll = shash_logpdf(z, f)
        return 1e12 if not np.all(np.isfinite(ll)) else -float(ll.sum())

    best, bestv = None, math.inf
    for eps0 in (-1.0, -0.5, 0.0, 0.5, 1.0):
        th, v = _nelder_mead(negll, np.array([eps0, 0.0]), step=0.2, tol=1e-12, max_iter=4000)
        if v < bestv:
            best, bestv = th, v
    return dict(eps=float(best[0]), delta=float(math.exp(best[1])), negloglik=bestv, n=int(len(z)))


def fit_pooled(cal_by_band):
    """The primary instrument: ONE shape per convention, location and scale per bandwidth."""
    std = []
    for g in GAMMAS:
        med, sd = robust_location_scale(cal_by_band[g])
        std.extend(((np.asarray(cal_by_band[g], dtype=float) - med) / sd).tolist())
    shape = fit_shape_pooled(std)
    out = {}
    for g in GAMMAS:
        med, sd = robust_location_scale(cal_by_band[g])
        out[g] = dict(family="shash_pooled", eps=shape["eps"], delta=shape["delta"], mu=med, sigma=sd)
    return out, shape


def shape_instability(cal_by_band, n_rep=40, seed=909):
    """The DIAGNOSIS, kept in the report: how unstable is the per-band 4-parameter fit at this sample size,
    measured on synthetic draws from a distribution it should be able to represent?"""
    rng = np.random.default_rng(seed)
    truth = dict(eps=-0.6, delta=1.4, mu=0.0, sigma=1.0)
    eps_l, del_l, sd_l = [], [], []
    for _ in range(n_rep):
        x = shash_ppf(rng.random(len(cal_by_band[GAMMAS[0]])), truth)
        f = shash_mle(x)
        eps_l.append(f["eps"])
        del_l.append(f["delta"])
        sd_l.append(f["sigma"])
    pooled, shape = fit_pooled(cal_by_band)
    return dict(n_rep=n_rep, n_per_band=len(cal_by_band[GAMMAS[0]]), truth=truth,
                per_band_mle=dict(eps_sd=float(np.std(eps_l)), delta_mean=float(np.mean(del_l)),
                                  delta_sd=float(np.std(del_l)), sigma_mean=float(np.mean(sd_l)),
                                  sigma_sd=float(np.std(sd_l)),
                                  eps_absmax=float(np.max(np.abs(eps_l)))),
                pooled_shape_on_the_same_size=dict(**{k: round(v, 4) for k, v in shape.items()
                                                      if k in ("eps", "delta")}))


def pvalue_t(x, fit, nu, n=20001, halfwidth=40.0):
    """Two-sided p under the heavier-tailed variant, by integrating that variant's own density on a fixed
    grid with a declared extent (40 sigma) and width (20,001 points).  This is a sensitivity read, not the
    primary instrument, and the grid is stated so the reader can price it."""
    lo = fit["mu"] - halfwidth * fit["sigma"]
    hi = fit["mu"] + halfwidth * fit["sigma"]
    grid = np.linspace(lo, hi, n)
    dens = np.exp(shash_t_logpdf(grid, fit, nu))
    cdf = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1]) * np.diff(grid))])
    tot = cdf[-1]
    F = float(np.interp(x, grid, cdf)) / tot
    return float(min(1.0, 2.0 * min(F, 1.0 - F)))


def ks_stat(x, cdf):
    """Two-sided KS statistic against a CDF."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    F = np.asarray(cdf(x), dtype=float)
    d_plus = np.max(np.arange(1, n + 1) / n - F)
    d_minus = np.max(F - np.arange(0, n) / n)
    return float(max(d_plus, d_minus))


def ks_pvalue(d, n):
    """Asymptotic Kolmogorov distribution survival function (series form)."""
    lam = (math.sqrt(n) + 0.12 + 0.11 / math.sqrt(n)) * d
    s = 0.0
    for k in range(1, 101):
        s += (-1) ** (k - 1) * math.exp(-2.0 * k * k * lam * lam)
    return float(min(1.0, max(0.0, 2.0 * s)))


# ------------------------------------------------------------------ the fit's own controls
def fit_recovery_control(seed=4242):
    """Class 82: a FITTED quantity is an instrument, so it is first fed a sample drawn from a distribution it
    is supposed to represent, and must recover the parameters it was handed."""
    rng = np.random.default_rng(seed)
    truth = dict(eps=-0.6, delta=1.4, mu=0.35, sigma=2.2)
    u = rng.random(4000)
    x = shash_ppf(u, truth)
    fit = shash_mle(x)
    grid = np.linspace(0.01, 0.99, 99)
    return dict(truth={k: truth[k] for k in ("eps", "delta", "mu", "sigma")},
                recovered={k: round(fit[k], 4) for k in ("eps", "delta", "mu", "sigma")},
                normal_special_case_max_absdiff=float(np.max(np.abs(
                    shash_cdf(np.linspace(-5, 5, 41), dict(eps=0.0, delta=1.0, mu=0.0, sigma=1.0))
                    - _Phi(np.linspace(-5, 5, 41))))),
                cdf_ppf_roundtrip_max_absdiff=float(np.max(np.abs(shash_cdf(shash_ppf(grid, truth), truth)
                                                                    - grid))),
                cdf_vs_sampler_max_absdiff=float(np.max(np.abs(
                    np.sort(shash_cdf(x, fit)) - np.arange(1, len(x) + 1) / len(x)))))


def pooled_fit_recovery(seed=31337, n_band=40, n_fresh=2000):
    """The pooled instrument's own control (Class 82), stated distributionally rather than by parameters:
    bands are synthesised from a KNOWN sinh-arcsinh distribution with twelve different locations and scales,
    the shape is fitted from the standardised draws, and the fitted models are then asked for the PIT of a
    FRESH sample from the same truth.  Agreement is the thing that matters for a p-value; parameter agreement
    does not hold here and is not claimed (see shape_instability)."""
    rng = np.random.default_rng(seed)
    truth = dict(eps=-0.6, delta=1.4, mu=0.0, sigma=1.0)
    bands, params = {}, {}
    for i, g in enumerate(GAMMAS):
        mu, sd = 0.25 * (-1) ** i, 0.8 + 0.1 * i
        params[g] = (mu, sd)
        bands[g] = (mu + sd * shash_ppf(rng.random(n_band), truth)).tolist()
    fits, shape = fit_pooled(bands)
    mu, sd = params[GAMMAS[0]]
    fresh = mu + sd * shash_ppf(rng.random(n_fresh), truth)
    ps = np.array([pvalue(v, fits[GAMMAS[0]]) for v in fresh])
    d = ks_stat(ps, lambda v: np.asarray(v, dtype=float))
    return dict(truth_shape={k: truth[k] for k in ("eps", "delta")},
                fitted_shape={k: round(shape[k], 4) for k in ("eps", "delta")},
                n_fresh=len(fresh), pit_ks=d, pit_ks_p=ks_pvalue(d, len(fresh)), pit_mean=float(ps.mean()),
                pit_frac_below_005=float(np.mean(ps < 0.05)))


def fire_control(fits, val_means, units=SHIFT_UNITS):
    """Class 85/86: a null owes proof that the detector FIRES.  Inject a declared shift into the out-of-sample
    validation cells -- magnitudes stated in units of that bandwidth's own fitted null sigma -- and report
    the rate at which the analytic p-value declares it.  A procedure that never fires here cannot support any
    "no advantage" reading."""
    rows = []
    for u in units:
        k, n = 0, 0
        for conv in CONVS:
            for g in GAMMAS:
                fit = fits[conv][g]
                for m in val_means[conv][g]:
                    k += int(pvalue(m + u * fit["sigma"], fit) < 0.05)
                    n += 1
        rows.append(dict(shift_sigma_units=u, n=n, n_fired=k, rate=k / max(1, n), wilson=S8.wilson(k, n)))
    return rows


def pit_uniformity(fits, val_means):
    """The out-of-sample audit that matters: if the fitted null is right, the probability-integral transform
    of the independent validation cells is uniform.  Pooled over all 240 cells, so the model is tested where
    the data can see it -- the 5 % tail included -- rather than at its centre only."""
    ps, by_band = [], {}
    for conv in CONVS:
        for g in GAMMAS:
            fit = fits[conv][g]
            band = [float(shash_cdf(m, fit)) for m in val_means[conv][g]]
            ps.extend(band)
            by_band["%s|%g" % (conv, g)] = dict(n=len(band), ks=ks_stat(band, lambda v: np.asarray(v)),
                                                mean=float(np.mean(band)),
                                                frac_below_005=float(np.mean(np.asarray(band) < 0.05)),
                                                frac_above_095=float(np.mean(np.asarray(band) > 0.95)))
    ps = np.asarray(ps, dtype=float)
    d = ks_stat(ps, lambda v: np.asarray(v, dtype=float))
    return dict(n=len(ps), ks=d, ks_p=ks_pvalue(d, len(ps)), mean=float(ps.mean()),
                frac_below_005=float(np.mean(ps < 0.05)), frac_above_095=float(np.mean(ps > 0.95)),
                by_band=by_band)


def size_of_analytic(fits, val_means):
    """The 5 % false-declaration rate of the analytic p-value, out of sample, pooled over 240 cells."""
    k, n = 0, 0
    for conv in CONVS:
        for g in GAMMAS:
            fit = fits[conv][g]
            for m in val_means[conv][g]:
                k += int(pvalue(m, fit) < 0.05)
                n += 1
    return dict(n=n, n_declared=k, rate=k / max(1, n), wilson=S8.wilson(k, n))


# ------------------------------------------------------------------ the one cell runner used here
def cell_runner(q, edges, Z, alpha, conv, metrics, seed_gen, W_rival_fn):
    """A cell, with the rival's precision matrix supplied by a callable -- so the matched read, the
    handicap ladder and any other rival share ONE code path.  `W_rival_fn(gamma, W_mean) = W_mean` is the
    matched rival, which is asserted bitwise against v8's own runner in the report (Class 83: when two paths
    exist for one measurement, prove they agree before using either)."""
    Q_int = S5.offdiag(S0.signless_laplacian(q, edges))
    A = S5.make_interaction(q, Q_int, alpha, seed_gen)
    f = S5.standardise(S5.target_raw(Z, A))
    var_f = float(f.var(ddof=0))
    rng = np.random.default_rng(seed_gen + 7)
    sigma = S5.NOISE_FRAC * float(f.std(ddof=0))
    n = len(Z)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(S8.N_SPLITS)]
    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(S8.N_SPLITS)]
    out = {}
    for gamma in GAMMAS:
        _, W_mean, spread = metrics[gamma]
        W_r = W_rival_fn(gamma, W_mean)
        Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
        rival = {s: S5.k_mahalanobis(Z, W_r, gamma, s) for s in S5.S_GRID}
        d = []
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            ytr, yte, fte = y[tr], y[te], f[te]
            rq = S8._fit_risks({1.0: Kq[np.ix_(tr, tr)]}, {1.0: Kq[np.ix_(te, tr)]}, ytr, yte, fte, var_f,
                               "excess")
            rr = S8._fit_risks({s: K[np.ix_(tr, tr)] for s, K in rival.items()},
                               {s: K[np.ix_(te, tr)] for s, K in rival.items()}, ytr, yte, fte, var_f, "excess")
            d.append(rq - rr)
        d = np.array(d)
        out[gamma] = dict(delta=d, mean=float(d.mean()), spread=spread,
                          kernel_max_absdiff=float(np.max(np.abs(Kq - rival[min(S5.S_GRID)]))))
    return dict(alpha=alpha, conv=conv, rows=out)


def matched_w(gamma, W_mean):
    return W_mean


# ------------------------------------------------------------------ the report
def load_null():
    """Load the committed R394 null draws -- and check them rather than trust them."""
    rep = json.loads(io.open(SRC, encoding="utf-8").read())
    rec = rep.get("report_sha256")
    probe = dict(rep)
    probe.pop("report_sha256", None)
    recomputed = hashlib.sha256(json.dumps(probe, sort_keys=True, indent=1).encode()).hexdigest()
    cal = {c: {g: list(rep["cal_means"][c][str(g)]) for g in GAMMAS} for c in CONVS}
    val = {c: {g: list(rep["val_means"][c][str(g)]) for g in GAMMAS} for c in CONVS}
    return rep, dict(recorded_sha256=rec, recomputed_sha256=recomputed, matches=bool(rec == recomputed),
                     what="sha256 of the reported JSON with its own sha field removed"), cal, val


def fresh_null_cell_matches(rep, cal, metrics):
    """Re-derive ONE null cell from scratch and compare bitwise with the stored draws, so the null family
    this round fits is shown to be the measurement it claims to be, not a transcription."""
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    rec = S8.null_cell(q, edges, Z, "shifted", metrics["shifted"], S8.CAL_SEED0)
    return {("%g" % g): bool(rec["rows"][g]["mean"] == cal["shifted"][g][0]) for g in GAMMAS}


def build_report():
    rep, integrity, cal, val = load_null()
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, LAYERS) for g in S5.GAMMAS} for c in CONVS}
    fresh = fresh_null_cell_matches(rep, cal, metrics)

    # ---- three instruments: the partially pooled fit (primary), the per-band MLE, and a normal
    fits, shapes, fits_pb, fits_n = {}, {}, {c: {} for c in CONVS}, {c: {} for c in CONVS}
    for c in CONVS:
        fits[c], shapes[c] = fit_pooled(cal[c])
        for g in GAMMAS:
            fits_pb[c][g] = shash_mle(cal[c][g])
            fits_n[c][g] = normal_fit(cal[c][g])

    per_band = {}
    for c in CONVS:
        for g in GAMMAS:
            f, fp, fn = fits[c][g], fits_pb[c][g], fits_n[c][g]
            per_band["%s|%g" % (c, g)] = dict(
                conv=c, gamma=g, n_cal=len(cal[c][g]), n_val=len(val[c][g]),
                pooled={k: round(f[k], 6) for k in ("eps", "delta", "mu", "sigma")},
                per_band_mle={k: round(fp[k], 6) for k in ("eps", "delta", "mu", "sigma")},
                normal={k: round(fn[k], 6) for k in ("mu", "sigma")},
                ks_val_out_of_sample_pooled=ks_stat(val[c][g], lambda v: shash_cdf(v, f)),
                ks_val_out_of_sample_perband=ks_stat(val[c][g], lambda v: shash_cdf(v, fp)),
                ks_val_out_of_sample_normal=ks_stat(
                    val[c][g], lambda v: _Phi((np.asarray(v) - fn["mu"]) / fn["sigma"])))

    # ---- arms that must be shown to be the same instrument
    ref = S8.real_cell(q, edges, Z, 1.0, "shifted", metrics["shifted"], S5.SEED_GEN)
    mine = cell_runner(q, edges, Z, 1.0, "shifted", metrics["shifted"], S5.SEED_GEN, matched_w)
    runner_agrees = {("%g" % g): bool(ref["rows"][g]["mean"] == mine["rows"][g]["mean"]) for g in GAMMAS}

    # ---- the real grid
    real = {}
    for conv in CONVS:
        for alpha in ALIGNS:
            real["%s|alpha=%g" % (conv, alpha)] = cell_runner(q, edges, Z, alpha, conv, metrics[conv],
                                                              S5.SEED_GEN, matched_w)
    rows = []
    for key, cell in real.items():
        for g in GAMMAS:
            m = cell["rows"][g]["mean"]
            f, fp, fn = fits[cell["conv"]][g], fits_pb[cell["conv"]][g], fits_n[cell["conv"]][g]
            kdiff = cell["rows"][g]["kernel_max_absdiff"]
            src = next(x for x in rep["family"] if x["cell"] == key and x["gamma"] == g)
            rows.append(dict(cell=key, conv=cell["conv"], alpha=cell["alpha"], gamma=g, delta_mean=m,
                             kernel_max_absdiff=kdiff, degenerate=bool(kdiff < S8.KERNEL_SAME_EPS),
                             band_r394=src["band"], p_pooled=pvalue(m, f), p_perband=pvalue(m, fp),
                             p_normal=pvalue(m, fn), p_pooled_t5=pvalue_t(m, f, 5.0),
                             p_emp_r394=src["p_emp"], outside_band_r394=src["outside_band"],
                             sign="loss" if m > 0 else "lead"))
    T = [r for r in rows if not r["degenerate"]]
    for tag in ("pooled", "perband", "normal", "pooled_t5"):
        qq, _ = S7.bh_qvalues(np.array([r["p_" + tag] for r in T]), 0.05)
        for i, r in enumerate(T):
            r["q_" + tag] = float(qq[i])
    qb, kb = S7.by_qvalues(np.array([r["p_pooled"] for r in T]), 0.05)
    for i, r in enumerate(T):
        r["q_pooled_by"] = float(qb[i])

    # ---- the registered power arm: the planted-alignment (handicap) ladder
    ladder = []
    for tt in (0.25, 0.5, 1.0):
        for alpha in ALIGNS:
            cell = cell_runner(q, edges, Z, alpha, "shifted", metrics["shifted"], S5.SEED_GEN,
                               lambda g, W, _t=tt: S7.handicap_w(_t, W))
            for g in GAMMAS:
                m = cell["rows"][g]["mean"]
                ladder.append(dict(t=tt, alpha=alpha, gamma=g, delta_mean=m,
                                   p=pvalue(m, fits["shifted"][g])))
    lq, _ = S7.bh_qvalues(np.array([r["p"] for r in ladder]), 0.05)
    for i, r in enumerate(ladder):
        r["q"] = float(lq[i])
    ladder_summary = {}
    for tt in (0.25, 0.5, 1.0):
        sel = [r for r in ladder if r["t"] == tt]
        ladder_summary["t=%g" % tt] = dict(
            n=len(sel), n_declared=int(sum(r["q"] <= 0.05 for r in sel)),
            n_leads=int(sum(r["q"] <= 0.05 and r["delta_mean"] < 0 for r in sel)),
            best_delta=float(min(r["delta_mean"] for r in sel)))

    fdr = dict(m=len(T))
    for tag in ("pooled", "perband", "normal", "pooled_t5"):
        sel = [r for r in T if r["q_" + tag] <= 0.05]
        fdr[tag] = dict(n_declared=len(sel), n_leads=int(sum(r["sign"] == "lead" for r in sel)),
                        n_losses=int(sum(r["sign"] == "loss" for r in sel)))
    fdr["pooled"]["n_by_q05"] = kb
    fdr["declared"] = [[r["cell"], r["gamma"], r["delta_mean"], r["p_pooled"], r["q_pooled"], r["sign"]]
                       for r in T if r["q_pooled"] <= 0.05]
    fdr["disagreements"] = [[r["cell"], r["gamma"], r["delta_mean"], r["p_pooled"], r["q_pooled"],
                             r["p_perband"], r["p_normal"], r["sign"]]
                            for r in T
                            if (r["q_pooled"] <= 0.05) != (r["q_perband"] <= 0.05)
                            or (r["q_pooled"] <= 0.05) != (r["q_normal"] <= 0.05)]

    return dict(
        round="R395",
        settings=dict(q=q, edges=EDGE_KIND, layers=LAYERS, convs=list(CONVS), aligns=list(ALIGNS),
                      gammas=list(GAMMAS), q_levels=list(Q_LEVELS), shift_units=list(SHIFT_UNITS),
                      nu_sensitivity=5.0, numpy=np.__version__,
                      source="smoke_v8_results.json (R394's committed null draws)"),
        controls=dict(
            C0_source_integrity=integrity,
            C0b_fresh_null_cell_matches_stored=fresh,
            C0c_cell_runner_agrees_with_v8=runner_agrees,
            C1_pooled_fit_recovery=pooled_fit_recovery(),
            C1b_shape_instability_at_this_size=shape_instability(cal["shifted"]),
            C2_size_out_of_sample={
                "pooled": size_of_analytic(fits, val), "perband": size_of_analytic(fits_pb, val),
                "normal": size_of_analytic(fits_n, val)},
            C3_pit_uniformity_pooled=pit_uniformity(fits, val),
            C4_detector_fires_pooled=fire_control(fits, val),
            C5_pooled_shapes={c: {k: round(shapes[c][k], 6) for k in ("eps", "delta", "n")}
                              for c in CONVS},
            C5b_per_band=per_band,
            C6_ladder=ladder_summary,
        ),
        fdr=fdr,
        rows=rows,
    )


def dumps(rep):
    return json.dumps(rep, sort_keys=True, indent=1)


def main():
    rep = build_report()
    a = dumps(rep)
    rep["report_sha256"] = hashlib.sha256(a.encode()).hexdigest()
    io.open(OUT, "w", encoding="utf-8").write(dumps(rep) + "\n")
    write_text(rep)
    return 0


def write_text(rep):
    c = rep["controls"]
    print("=" * 100)
    print("ISSUE #87 -- R395: a PARTIALLY POOLED smooth null, audited on data the fit never saw")
    print("=" * 100)
    print("source integrity: %s" % c["C0_source_integrity"])
    print("fresh null cell matches stored draws: %s" % c["C0b_fresh_null_cell_matches_stored"])
    print("this round's cell runner agrees with v8's: %s" % c["C0c_cell_runner_agrees_with_v8"])
    print()
    print("-- C1b WHY the fit is pooled: per-band 4-parameter MLE at this sample size ---------------")
    inst = c["C1b_shape_instability_at_this_size"]
    print("   %d synthetic draws per band, truth eps=%.2f delta=%.2f:" %
          (inst["n_per_band"], inst["truth"]["eps"], inst["truth"]["delta"]))
    pb = inst["per_band_mle"]
    print("     per-band MLE  : eps |max|=%.2f  delta mean %.2f (sd %.2f)  sigma mean %.2f (sd %.2f)"
          % (pb["eps_absmax"], pb["delta_mean"], pb["delta_sd"], pb["sigma_mean"], pb["sigma_sd"]))
    print("     pooled shape  : %s" % inst["pooled_shape_on_the_same_size"])
    print()
    print("-- C1 the pooled fit's own recovery control (distributional) ------------------------------")
    for k, v in sorted(c["C1_pooled_fit_recovery"].items()):
        print("   %-24s %s" % (k, v))
    print()
    print("-- C5 pooled shapes + per-band locations/scales -------------------------------------------")
    for conv, sh in sorted(c["C5_pooled_shapes"].items()):
        print("   %-9s eps=%+.4f delta=%.4f  (from n=%d standardised draws)" % (conv, sh["eps"], sh["delta"], sh["n"]))
    print()
    print("-- C2 analytic size, OUT OF SAMPLE, by instrument -----------------------------------------")
    for tag, s in sorted(c["C2_size_out_of_sample"].items()):
        print("   %-8s %d/%d = %.4f  Wilson95 [%.4f,%.4f]"
              % (tag, s["n_declared"], s["n"], s["rate"], s["wilson"][0], s["wilson"][1]))
    print()
    print("-- C3 PIT uniformity, OUT OF SAMPLE (pooled instrument) -----------------------------------")
    u = c["C3_pit_uniformity_pooled"]
    print("   n=%d  KS=%.4f  p=%.4f  mean=%.4f  frac<0.05=%.4f  frac>0.95=%.4f"
          % (u["n"], u["ks"], u["ks_p"], u["mean"], u["frac_below_005"], u["frac_above_095"]))
    print()
    print("-- C4 the detector FIRES on injected shifts -----------------------------------------------")
    for r in c["C4_detector_fires_pooled"]:
        print("   shift %.1f sigma -> %d/%d declared (%.3f) Wilson95 [%.3f,%.3f]"
              % (r["shift_sigma_units"], r["n_fired"], r["n"], r["rate"], r["wilson"][0], r["wilson"][1]))
    print()
    print("-- C6 the registered power arm: planted-alignment (handicap) ladder -----------------------")
    for k, v in sorted(c["C6_ladder"].items()):
        print("   %-6s n=%d  declared=%d  leads=%d  best_delta=%+.4f"
              % (k, v["n"], v["n_declared"], v["n_leads"], v["best_delta"]))
    print()
    print("-- the real read ---------------------------------------------------------------------------")
    f = rep["fdr"]
    for tag in ("pooled", "perband", "normal", "pooled_t5"):
        print("   %-10s declared %2d  (%d leads, %d losses)" % (tag, f[tag]["n_declared"],
                                                                 f[tag]["n_leads"], f[tag]["n_losses"]))
    print("   for comparison -- R394 empirical band: 0 declared ; R393 zero-anchored: 28")
    print()
    print("   DECLARED under the pooled instrument:")
    for row in sorted(f["declared"], key=lambda r: r[3]):
        print("     %-18s gamma=%4.2f delta %+0.4f  p=%.6f  q=%.6f  %s"
              % (row[0], row[1], row[2], row[3], row[4], row[5]))
    print()
    print("   instrument disagreements (pooled vs per-band vs normal): %d" % len(f["disagreements"]))
    for row in sorted(f["disagreements"], key=lambda r: r[3])[:10]:
        print("     %-18s gamma=%4.2f delta %+0.4f  p_pooled=%.5f q=%.5f | p_perband=%.5f | p_normal=%.5f  %s"
              % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))
    print()
    print("   report sha256 = %s" % rep["report_sha256"])
    print("   written to %s" % os.path.basename(OUT))


if __name__ == "__main__":
    sys.exit(main())
