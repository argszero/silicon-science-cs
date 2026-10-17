#!/usr/bin/env python3
"""Issue #142 / research v1 -- THE SPAN LAW (the registration's P2, untested by v0).

BOUNDED GOAL (one goal, stated before it runs).  v0 established that the sweep's noise-free error
is the SPAN AVERAGE of c (not the point value) and that its noise pays 1/span.  It left the
registration's P2 untested: *the ladder should be spaced so the estimator's MSE is minimal, and that
optimal spacing scales as sigma^{1/3}.*  This instrument measures the two ingredients SEPARATELY --

    bias(a)  ~ a^2      (a centred difference over a half-width a replaces c(x) by its span mean)
    var(a,sigma) ~ sigma^2 / a^2

-- so that the exponent 1/3 is DERIVED from the measured ingredient laws rather than fitted to the
MSE curve alone, and then measures h*(sigma) directly and fits its slope.

Ground truth is exact by construction: c(d) comes from the plant's own augmented Lyapunov solve
(v0's machinery, unchanged), and the estimator's input G(L) = L*C(L) = int_tau^{tau+L} c is exact.

The estimator, written out.  A sweep logs G at operating points L_i on the DELTA grid; a centred
difference at L_i over half-width a = k*DELTA is
    Chat = (G(L_{i+k}) - G(L_{i-k})) / (2a),
whose expectation is the span mean of c over [x_i - a, x_i + a] (so it is biased for c(x_i) by the
span average) and whose noise is, from J = C(L) + lam/L with multiplicative noise sigma,
    Ghat(L) = G(L) + (G(L) + lam(L)) * sigma * eps,     Var[Chat] = sigma^2 * [(G+lam)^2_+ + (G+lam)^2_-] / (4a^2).
Both are exact, so MSE(a, sigma) = mean_i bias_i^2 + sigma^2 * mean_i varcoef_i is exact, and the
argmin over a is a computed quantity.  The instrument certifies the noise model by Monte Carlo.

A CONTROL THAT MUST FIRE.  The same measurement with a ONE-SIDED (forward) difference, whose bias
is FIRST order (a^1) rather than second, must give a different exponent: MSE = A' a^2 + sigma^2 B'/a^2
minimises at a* ~ sigma^{1/2}.  If the centred and one-sided fits agreed, the measurement would be
blind to the thing it claims to measure.

python3 spike_ident_v1.py                (writes spike_ident_v1_results.json)
python3 spike_ident_v1.py --selftest     (plants; must all fire)
"""
import json
import math
import sys

import numpy as np

import spike_ident_v0 as v0

DELTA = v0.DELTA
KMAX = 40                 # half-width a = k*DELTA, k = 1..KMAX
SIGMAS = [10 ** e for e in np.arange(-6.0, -0.5, 0.25)]   # sigma_J/J
BUILD = v0.BUILD


# ------------------------------------------------------------------ blocks (exact ground truth)
def plants_with_curves():
    """Per plant: the exact per-delay cost c(d) and its delay margin.  Computed ONCE per plant --
    c(d) does not depend on tau, which is why v0's per-tau recompute was wasted work."""
    out = {}
    for name, (A, B, Q, R) in v0.make_plants().items():
        K, _ = v0.lqr_gain(A, B, Q, R)
        W = np.eye(A.shape[0])
        c = [v0.steady_cost(A, B, K, W, d) for d in range(v0.DMAX_PROBE + 1)]
        dmax = max(d for d in range(v0.DMAX_PROBE + 1) if c[d] != v0.INF)
        out[name] = (c, dmax)
    return out


def build_block(c, dmax, tau, smooth=False):
    """One (plant, tau) block: the exact operating curve on the DELTA grid, and the price lam(L)
    that makes each grid L the operating point (the continuum first-order condition,
    lam = L*c(tau+L) - G).  A point is USED only if lam really does make it the grid-argmin.

    `smooth=False` reads the model's own ground truth: c(.) defined at INTEGER delays and LINEARLY
    interpolated between them (#116's model).  That curve is C^0 with a kink every 1.0 delay, and a
    kink inside the span is what makes the centred difference's bias FIRST order in a for a < 1 --
    measured, not assumed.  `smooth=True` replaces the interpolation with Catmull-Rom (C^1), the
    same node values with the kinks removed, which is the regime the registered sigma^{1/3} law is
    a statement about."""
    cfn = (lambda x: catmull(c, dmax, x)) if smooth else (lambda x: v0.interp(c, dmax, x))
    Ls, C = objective_grid_fn(cfn, dmax, tau)
    if Ls is None:
        return None
    lo = max(tau, 1.0)
    mask = Ls >= lo - 1e-9
    Ls, C = Ls[mask], C[mask]
    if len(Ls) < 3 * KMAX:
        return None
    G = Ls * C
    cg = np.array([cfn(tau + L) for L in Ls])
    lam = Ls * cg - G
    ok = np.zeros(len(Ls), dtype=bool)
    for i in range(len(Ls)):
        obj = C + lam[i] / Ls
        ok[i] = abs(int(np.argmin(obj)) - i) <= 1      # the lattice's own one-step resolution
    return {"Ls": Ls, "C": C, "G": G, "cg": cg, "lam": lam, "ok": ok,
            "tau": tau, "dmax": dmax, "lo": lo}


def catmull(c, dmax, x):
    """Catmull-Rom through the integer-delay nodes: the same values as `v0.interp`, with the kinks
    removed (C^1).  Used only to separate the kink's first-order bias from the smooth second-order
    one; the model's own curve stays the linearly interpolated one."""
    if x < 0 or x > dmax:
        return v0.INF
    i = int(math.floor(x))
    t = x - i
    def p(j):
        return c[min(max(j, 0), dmax)]
    p0, p1, p2, p3 = p(i - 1), p(i), p(i + 1), p(i + 2)
    return 0.5 * ((2.0 * p1) + (-p0 + p2) * t
                  + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t * t
                  + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t * t * t)


def objective_grid_fn(cfn, dmax, tau):
    """v0's objective grid with the interpolation passed in (so the smooth arm gets the same
    construction): (L grid, C(L)) for C(L) = (1/L) int_0^L c(tau+s) ds."""
    if tau > dmax:
        return None, None
    K = int((dmax - tau) / DELTA)
    if K < 1:
        return None, None
    xs = tau + DELTA * np.arange(K + 1)
    vals = np.array([cfn(x) for x in xs])
    if np.any(~np.isfinite(vals)):
        last = int(np.max(np.where(np.isfinite(vals))[0]))
        vals, xs, K = vals[:last + 1], xs[:last + 1], last
        if K < 1:
            return None, None
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (vals[:-1] + vals[1:]) * DELTA)])
    Ls = DELTA * np.arange(1, K + 1)
    return Ls, cum[1:] / Ls


def blocks_for(c, dmax, taus=(0.0, 2.0, 4.0, 6.0, 8.0), smooth=False):
    out = []
    for tau in taus:
        b = build_block(c, dmax, tau, smooth=smooth)
        if b is not None:
            out.append(b)
    return out


# -------------------------------------------------------------- the estimator's exact law
def accumulate(blocks, one_sided=False):
    """A[k] = mean over used points of bias^2 at half-width k*DELTA; B[k] = mean of the variance
    coefficient (Var = sigma^2 * B[k]).  Everything is EXACT -- G, c and lam are exact, so the
    expectation and variance are computed, not sampled.

    THE TARGET BAND IS FIXED ACROSS k, and that is the whole point.  The bias is a function of the
    point x as well as the half-width a, and c grows with x; averaging over the k-DEPENDENT window
    `i in [k, n-k)` removes more of the large-c points as k grows, which depresses the large-k
    readings and corrupts the exponent toward 1.77 ON AN ANALYTIC CURVE (measured -- c = exp(0.3x)
    is exactly smooth and can have no first-order term, so a sub-2 exponent there is the window's,
    not the estimator's).  Restricting every k to the SAME band makes a the only thing that moves."""
    A, B, nb = {}, {}, {}
    for k in range(1, KMAX + 1):
        bs, vs = [], []
        for b in blocks:
            Ls, G, cg, lam, ok = b["Ls"], b["G"], b["cg"], b["lam"], b["ok"]
            n = len(Ls)
            lo, hi = KMAX, n - KMAX                 # the SAME band for every k
            for i in range(lo, hi):
                if not ok[i]:
                    continue
                if one_sided:
                    j = i + k
                    if j >= n or not ok[j]:
                        continue
                    h = Ls[j] - Ls[i]
                    if h <= 1e-12:
                        continue
                    slope = (G[j] - G[i]) / h
                    vc = ((G[j] + lam[j]) ** 2 + (G[i] + lam[i]) ** 2) / (h * h)
                else:
                    j1, j2 = i - k, i + k
                    if j1 < 0 or j2 >= n or not ok[j1] or not ok[j2]:
                        continue
                    h = Ls[j2] - Ls[i]                  # the half-width a
                    if h <= 1e-12:
                        continue
                    slope = (G[j2] - G[j1]) / (2.0 * h)
                    vc = ((G[j2] + lam[j2]) ** 2 + (G[j1] + lam[j1]) ** 2) / (4.0 * h * h)
                bs.append((slope - cg[i]) ** 2)
                vs.append(vc)
        if bs:
            A[k] = float(np.mean(bs))
            B[k] = float(np.mean(vs))
            nb[k] = len(bs)
    return A, B, nb


def mse(A, B, sigma):
    return {k: A[k] + sigma * sigma * B[k] for k in A}


def argmin_k(A, B, sigma):
    m = mse(A, B, sigma)
    return min(m, key=lambda k: m[k]), m


def argmin_refined(A, B, sigma, kmin=2, kmax=None):
    """The optimal half-width a*, refined off the DELTA lattice.

    `k` is an INTEGER lattice step, so reading h* at the integer argmin leaves a STAIRCASE of
    amplitude ~DELTA in log a* -- measured here: it moved the one-sided fit from 0.50 to 0.4535 and
    the centred fit from 0.333 to 0.3315, i.e. the discretisation, not the law.  The refinement fits
    a parabola through (log a, log MSE) at the argmin and its two neighbours and returns its vertex
    -- the estimator is smooth in a, and this is the standard sub-lattice read of its minimum.
    Returns log a*, or None when the argmin sits at an end of the k range (the claim is an INTERIOR
    optimum; an endpoint minimum measures the range, not the law)."""
    m = mse(A, B, sigma)
    k0 = min(m, key=lambda k: m[k])
    if kmax is None:
        kmax = max(A)
    if k0 <= kmin or k0 >= kmax or k0 - 1 not in m or k0 + 1 not in m:
        return None
    x = [math.log((k0 + d) * DELTA) for d in (-1, 0, 1)]
    y = [math.log(m[k0 + d]) for d in (-1, 0, 1)]
    den = (x[0] - x[1]) * (x[0] - x[2]) * (x[1] - x[2])
    if den == 0:
        return None
    ca = (x[2] * (y[1] - y[0]) + x[1] * (y[0] - y[2]) + x[0] * (y[2] - y[1])) / den
    cb = (x[2] ** 2 * (y[0] - y[1]) + x[1] ** 2 * (y[2] - y[0]) + x[0] ** 2 * (y[1] - y[2])) / den
    if ca <= 0:
        return None
    return -cb / (2.0 * ca)


def logslope(xs, ys):
    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    if x.size < 2:
        return None
    xm, ym = x.mean(), y.mean()
    den = ((x - xm) ** 2).sum()
    if den == 0:
        return None
    return float(((x - xm) * (y - ym)).sum() / den)


def fit_hstar(A, B, sigmas, kmin=2, kmax=None):
    """h*(sigma) = the sub-lattice argmin of MSE(k, sigma) (see `argmin_refined`), restricted to
    sigmas whose minimum is INTERIOR."""
    if kmax is None:
        kmax = max(A)
    pts = []
    for s in sigmas:
        la = argmin_refined(A, B, s, kmin=kmin, kmax=kmax)
        if la is not None:
            pts.append((s, math.exp(la)))
    if len(pts) < 3:
        return None, pts
    return logslope([math.log(s) for s, _ in pts], [math.log(a) for _, a in pts]), pts


def fit_power(xs, ys):
    return logslope([math.log(v) for v in xs], [math.log(v) for v in ys])


def mc_check(blocks, k, sigma, nrep=4000, seed=99):
    """Monte-Carlo confirmation that the analytic MSE is the estimator's MSE, under the same noise
    model v0 used: J is logged with multiplicative noise N(0, sigma*J).

    THE TWO FLANKS GET INDEPENDENT DRAWS, and that is the whole content of the check.  They are two
    different PRICES, so the deployment logs them from two separate observations; sharing one draw
    makes the common part of the noise cancel in the difference and reports a variance ~130x too
    small (measured: analytic 85.0 vs a shared-draw MC's 0.63 at k=10, sigma=1e-3).  The first
    version of this certificate shared the draw and disagreed with the formula it was checking --
    the cause was in the certificate, not the model, and the tell was that the disagreement had the
    EXACT size of the cancelled common term."""
    rng = np.random.default_rng(seed)
    ests = []
    for b in blocks:
        Ls, G, cg, lam, ok = b["Ls"], b["G"], b["cg"], b["lam"], b["ok"]
        n = len(Ls)
        lo, hi = KMAX, n - KMAX                            # the SAME band `accumulate` averages over
        for i in range(lo, hi):
            if not ok[i] or i - k < 0 or i + k >= n or not ok[i - k] or not ok[i + k]:
                continue
            h = Ls[i + k] - Ls[i]
            e1 = rng.standard_normal(nrep)
            e2 = rng.standard_normal(nrep)
            gp = G[i + k] + (G[i + k] + lam[i + k]) * sigma * e1
            gm = G[i - k] + (G[i - k] + lam[i - k]) * sigma * e2
            ests.append((gp - gm) / (2.0 * h) - cg[i])
    if not ests:
        return None
    E = np.array(ests)                                        # points x reps
    return {"n_points": int(E.shape[0]), "n_rep": nrep,
            "mc_bias2": float(np.mean(E.mean(axis=1) ** 2) - np.mean(E.var(axis=1)) / nrep),
            "mc_var": float(np.mean(E.var(axis=1)))}


def selftest():
    ok = True
    def holds(name, cond, info=""):
        nonlocal ok
        print("[%-46s] %s %s" % (name, "ok" if cond else "FIRE", info))
        ok = ok and bool(cond)

    # 1. the estimator's bias on a LINEAR curve is exactly zero (the span mean IS the point value)
    Ls = np.linspace(1.0, 20.0, 200)
    c = None
    lin_c = lambda x: 3.0 + 2.0 * x
    def G_of(L):     # int_0^L (3+2(tau+s)) ds with tau=0
        return 3.0 * L + L * L
    G = np.array([G_of(L) for L in Ls])
    cg = np.array([lin_c(L) for L in Ls])
    for k in (1, 3, 7):
        h = Ls[k] - Ls[0]
        slope = (G[2 * k] - G[0]) / (2 * h)
        holds("plant-linear-curve-centred-bias-zero-k%d" % k, abs(slope - cg[k]) < 1e-9)
    # ... and the ONE-SIDED difference is biased on the same linear curve (the control's premise)
    h = Ls[3] - Ls[0]
    sl1 = (G[3] - G[0]) / h
    holds("plant-linear-curve-one-sided-IS-biased",
          abs(sl1 - cg[0]) > 1e-3, "off by %.4g" % abs(sl1 - cg[0]))

    # 2. the fit routine recovers a planted exponent (a synthetic MSE with a known law)
    xs = [10 ** (-4 + 0.5 * t) for t in range(9)]
    A = {k: (k * DELTA) ** 4 for k in range(1, 41)}          # bias^2 ~ a^4
    B = {k: 1.0 / (k * DELTA) ** 2 for k in range(1, 41)}    # var ~ a^-2
    sl, pts = fit_hstar(A, B, xs, kmin=2)
    holds("plant-fit-recovers-1/3", sl is not None and abs(sl - 1.0 / 3.0) < 0.01,
          "slope=%.4f n=%d" % (sl if sl else float("nan"), len(pts)))
    A1 = {k: (k * DELTA) ** 2 for k in range(1, 41)}         # bias^2 ~ a^2 (one-sided)
    sl1, _ = fit_hstar(A1, B, xs, kmin=2)
    holds("plant-fit-recovers-1/2-for-the-one-sided-law",
          sl1 is not None and abs(sl1 - 0.5) < 0.01, "slope=%.4f" % (sl1 if sl1 else float("nan")))

    # 2b. the refinement is not decoration: on the same synthetic law the RAW lattice argmin is
    #     measurably worse (this is the defect the first run of this instrument had)
    raw = []
    for s in xs:
        k, _ = argmin_k(A1, B, s)
        if 2 <= k <= 39:
            raw.append((s, k * DELTA))
    sl_raw = logslope([math.log(s) for s, _ in raw], [math.log(a) for _, a in raw]) if len(raw) > 2 else None
    holds("plant-refinement-beats-the-raw-lattice-argmin",
          sl_raw is not None and abs(sl1 - 0.5) < abs(sl_raw - 0.5),
          "refined=%.4f raw=%.4f" % (sl1, sl_raw))

    # 3. the argmin is INTERIOR (a monotone MSE would report the range, not a law)
    kk, m = argmin_k(A, B, 1e-3)
    holds("plant-argmin-is-interior", 1 < kk < max(A), "k*=%d" % kk)

    # 4. a FLAT bias has NO interior optimum at all -- the correct negative, and the reason a
    #    "1/6 law" is not a thing: with bias constant, MSE = const + sigma^2 B(a) falls in a.
    Aflat = {k: 1.0 for k in A}
    holds("plant-flat-bias-has-no-interior-optimum",
          argmin_refined(Aflat, B, 1e-3, kmin=2) is None)

    # 5. THE FIXED-BAND RULE, on an ANALYTIC curve, where no first-order term can exist -- this is
    #    the defect the first run of this instrument had: the target window grew with k and removed
    #    the large-c points preferentially, reporting 1.77 on a curve whose exponent is exactly 2.
    def bias_exponent(fixed_band):
        Ls = DELTA * np.arange(1, 1001)
        cg = np.array([math.exp(0.8 * L) for L in Ls])
        Gex = np.array([(math.exp(0.8 * L) - 1.0) / 0.8 for L in Ls])
        ks = [2, 4, 8, 16, 32]
        xs, ys = [], []
        for k in ks:
            lo = (2 * max(ks)) if fixed_band else k
            hi = len(Ls) - lo
            bs = [(((Gex[i + k] - Gex[i - k]) / (2 * k * DELTA)) - cg[i]) ** 2 for i in range(lo, hi)]
            xs.append(math.log(k * DELTA))
            ys.append(math.log(math.sqrt(np.mean(bs))))
        return logslope(xs, ys)
    e_fix = bias_exponent(True)
    e_slide = bias_exponent(False)
    holds("plant-fixed-target-band-recovers-exponent-2", e_fix is not None and abs(e_fix - 2.0) < 0.05,
          "e=%.3f" % (e_fix if e_fix else float("nan")))
    holds("plant-sliding-band-corrupts-the-exponent",
          e_slide is not None and e_slide < e_fix - 0.05, "e=%.3f" % (e_slide if e_slide else float("nan")))
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def analytic_blocks(rates=(0.3, 0.5, 0.8), dmax=20.0, taus=(0.0, 2.0, 4.0, 6.0, 8.0)):
    """The estimator-law control: an EXACTLY smooth ground truth c(x) = exp(r*x), with G its exact
    integral (no lattice quadrature at all), so the only thing left is the estimator's own bias and
    variance.  A plant in the other direction would be pointless here -- this arm is the one place
    where the exponent the law is DERIVED from is known in advance."""
    out = []
    for r in rates:
        cfn = (lambda x, r=r: math.exp(r * x))
        for tau in taus:
            Ls, C = objective_grid_fn(cfn, dmax, tau)
            if Ls is None:
                continue
            lo = max(tau, 1.0)
            mask = Ls >= lo - 1e-9
            Ls, C = Ls[mask], C[mask]
            if len(Ls) < 3 * KMAX:
                continue
            G = np.array([(math.exp(r * (tau + L)) - math.exp(r * tau)) / r for L in Ls])   # exact
            cg = np.array([cfn(tau + L) for L in Ls])
            lam = Ls * cg - G
            ok = np.ones(len(Ls), dtype=bool)
            out.append({"Ls": Ls, "C": C, "G": G, "cg": cg, "lam": lam, "ok": ok,
                        "tau": tau, "dmax": dmax, "lo": lo})
    return out


def measure(blocks, label):
    """Every exponent this instrument reports, for one arm (model curve / smooth curve)."""
    A, B, nb = accumulate(blocks)
    A1, B1, nb1 = accumulate(blocks, one_sided=True)
    if not A or not A1:
        return None
    kmax = max(A)
    ks = [k for k in sorted(A) if nb.get(k, 0) >= 200]
    bias_exp = fit_power([k * DELTA for k in ks], [math.sqrt(A[k]) for k in ks]) if len(ks) > 2 else None
    var_exp = fit_power([k * DELTA for k in ks], [math.sqrt(B[k]) for k in ks]) if len(ks) > 2 else None
    # the LOCAL exponent curve, k -> 2k: the plateau is visible and is where the design lives
    local = {}
    for k in ks:
        if 2 * k in A and k in A:
            b1, b2 = math.sqrt(A[k]), math.sqrt(A[2 * k])
            if b1 > 0:
                local["%d->%d" % (k, 2 * k)] = math.log(b2 / b1) / math.log(2.0)
    slope_c, pts_c = fit_hstar(A, B, SIGMAS, kmin=2, kmax=kmax - 1)
    slope_1, pts_1 = fit_hstar(A1, B1, SIGMAS, kmin=2, kmax=kmax - 1)
    # the exponent DERIVED from the measured ingredient laws: bias ~ a^b, var ~ sigma^2 a^-2
    pred_c = (2.0 / (2.0 * bias_exp + 2.0)) if bias_exp is not None else None
    return {
        "arm": label,
        "k_max": kmax,
        "used_point_spans": int(sum(nb.values())),
        "blocks": len(blocks),
        "cells": {str(k): {"A_bias2": A[k], "B_varcoef": B[k], "n": nb[k]} for k in sorted(A)},
        "cells_one_sided": {str(k): {"A_bias2": A1[k], "B_varcoef": B1[k], "n": nb1[k]}
                            for k in sorted(A1)},
        "law_bias_exponent": bias_exp,
        "law_bias_local_slopes": local,
        "law_var_vs_a_exponent": var_exp,
        "hstar_vs_sigma_slope_centred": slope_c,
        "hstar_vs_sigma_slope_one_sided": slope_1,
        "hstar_predicted_from_ingredients": pred_c,
        "hstar_points_centred": [[float(s), float(a)] for s, a in pts_c],
        "hstar_points_one_sided": [[float(s), float(a)] for s, a in pts_1],
    }


def main():
    curves = plants_with_curves()
    model_blocks, smooth_blocks = [], []
    for name, (c, dmax) in curves.items():
        model_blocks.extend(blocks_for(c, dmax, smooth=False))
        smooth_blocks.extend(blocks_for(c, dmax, smooth=True))
    if not model_blocks:
        print("no blocks")
        return 1

    M = measure(model_blocks, "model curve (c(.) linearly interpolated between integer delays)")
    S = measure(smooth_blocks, "smooth curve (Catmull-Rom through the same integer-delay nodes)")
    X = measure(analytic_blocks(), "exactly smooth control (c = exp(r x), G exact)")

    # MC certificate at a few (k, sigma), on the model arm
    mc = {}
    kmax = max(int(k) for k in M["cells"])
    for k in [max(2, kmax // 4), max(3, kmax // 2)]:
        for s in (1e-3, 1e-2):
            r = mc_check(model_blocks, k, s, nrep=3000)
            if r:
                mc["k=%d,sigma=%g" % (k, s)] = {
                    "analytic_bias2": M["cells"][str(k)]["A_bias2"], "mc_bias2": r["mc_bias2"],
                    "analytic_var": s * s * M["cells"][str(k)]["B_varcoef"], "mc_var": r["mc_var"],
                    "n_points": r["n_points"], "n_rep": r["n_rep"]}

    R = {
        "build": BUILD,
        "goal": "P2 -- the interior MSE-optimal span law, and its two ingredient laws",
        "grid": {"delta_L": DELTA, "k_max": KMAX, "sigmas": SIGMAS},
        "model": M,
        "smooth": S,
        "analytic": X,
        "mc_certificate": mc,
    }
    summary = {k: v for k, v in R.items() if k not in ("model", "smooth", "analytic", "mc_certificate")}
    for arm in ("model", "smooth", "analytic"):
        A = R[arm]
        if A:
            summary[arm] = {k: A[k] for k in ("law_bias_exponent", "law_var_vs_a_exponent",
                                              "hstar_vs_sigma_slope_centred",
                                              "hstar_vs_sigma_slope_one_sided",
                                              "hstar_predicted_from_ingredients",
                                              "used_point_spans", "k_max")}
    print(json.dumps(summary, indent=2, sort_keys=True))
    with open("spike_ident_v1_results.json", "w") as fh:
        json.dump(R, fh, indent=2, sort_keys=True)
    return R


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
