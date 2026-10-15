#!/usr/bin/env python3
"""Issue #142 / research v0 -- is the cost curvature readable from the logs, and by which route?

BOUNDED GOAL (one goal, stated before it runs): take the price-sweep design that is public in our
own Post-27 thread (and named as an OPEN ITEM in the published #116) and measure, against an EXACT
ground-truth curve, three things the design never measured:

  [A] THE IDENTITY, as an identity.  From one interior operating point the deployment logs
      (L*, J, lam) with J = C(L*) + lam/L*, and the claim is
          G := L* J - lam = L* C(L*) = int_tau^{tau+L*} c(s) ds.
      Tested against the exact quadrature of the plant's own c(--), not against a fit.
  [B] THE SINGLE-POINT MARGINAL IDENTITY.  At a CONTINUOUS interior optimum the first-order
      condition gives, for the objective C(L) + lam/L,
          C'(L) = (c(tau+L) - C(L))/L = lam/L^2   =>   c(tau+L*) = C(L*) + lam/L* = J.
      So the curvature at the visited point may be READ OFF THE LOG with NO differencing at all --
      which is a different route from the sweep, with a different error term.  Measured.
  [C] THE SWEEP.  Differencing G against L across the ladder recovers c pointwise; its target is
      the SPAN MEAN of c, and it pays 1/span.  Measured against its own correct target.
  [D] THE IDENTIFIABILITY BOUNDARY (the direction's P3).  At a floor- or ceiling-pinned cell the
      first-order condition does not hold, so neither route should work.  Measured per class --
      the negative is the result, and it is counted.

A control that can fail: [A] is re-run with lam perturbed by 1%, and must then FAIL.

Ground truth is exact by construction: c(d) comes from the plant's own augmented Lyapunov solve.

python3 spike_ident_v0.py            (writes spike_ident_v0_results.json)
"""
import json
import math
import sys

import numpy as np

DT = 0.1
INF = float("inf")
DELTA = 0.02          # L-grid resolution, as in #116's model_v4_sweep
DMAX_PROBE = 20       # as in #116
N_PRICES = 22
LAM_GRID = list(np.logspace(-2, 5, N_PRICES))     # #116's ladder: 7 decades, 22 prices
BUILD = "python %s / numpy %s" % (sys.version.split()[0], np.__version__)


# ------------------------------------------------------------------ plant machinery (from #116)
def lqr_gain(A, B, Q, R, iters=20000, tol=1e-15):
    P = Q.copy()
    for _ in range(iters):
        S = R + B.T @ P @ B
        K = np.linalg.solve(S, B.T @ P @ A)
        Pn = A.T @ P @ A - A.T @ P @ B @ K + Q
        if np.max(np.abs(Pn - P)) <= tol * max(1.0, np.max(np.abs(P))):
            return K, Pn
        P = Pn
    return K, P


def _aug(A, B, K, d):
    n = A.shape[0]
    m = (d + 1) * n
    Aa = np.zeros((m, m))
    Aa[0:n, 0:n] = A
    Aa[0:n, d * n:(d + 1) * n] -= B @ K
    for i in range(1, d + 1):
        Aa[i * n:(i + 1) * n, (i - 1) * n:i * n] = np.eye(n)
    return Aa


def steady_cost(A, B, K, W, d):
    """Exact per-delay cost c(d) by the augmented Lyapunov solve; +inf past the margin."""
    Aa = _aug(A, B, K, d)
    if float(np.max(np.abs(np.linalg.eigvals(Aa)))) >= 1.0:
        return INF
    n = A.shape[0]
    m = (d + 1) * n
    Wb = np.zeros((m, m))
    Wb[0:n, 0:n] = W
    lhs = np.eye(m * m) - np.kron(Aa, Aa)
    P = np.linalg.solve(lhs, Wb.reshape(-1, order="F")).reshape((m, m), order="F")
    return float(np.trace(P[0:n, 0:n]))


def make_plants():
    A2 = np.array([[1.0, DT], [0.0, 1.0]])
    B2 = np.array([[0.5 * DT * DT], [DT]])
    return {
        "scalar-stable a=0.9": (np.array([[0.9]]), np.array([[0.1]]), np.eye(1), np.array([[1.0]])),
        "double-int R=1": (A2, B2, np.eye(2), np.array([[1.0]])),
        "double-int R=10": (A2, B2, np.eye(2), np.array([[10.0]])),
        "double-int R=100": (A2, B2, np.eye(2), np.array([[100.0]])),
    }


def interp(c, dmax, x):
    """Linear interpolation of the exact integer-delay curve (the instrument's own resolution)."""
    if x < 0 or x > dmax:
        return INF
    i = int(math.floor(x))
    f = x - i
    if i >= dmax:
        return c[dmax]
    return c[i] * (1 - f) + c[i + 1] * f


def quadrature(c, dmax, tau, L, n=2000):
    """int_tau^{tau+L} c(s) ds, Simpson on the interpolated curve (the identity's exact target)."""
    if L <= 0:
        return 0.0
    xs = np.linspace(tau, tau + L, n + 1)
    ys = np.array([interp(c, dmax, x) for x in xs])
    h = (tau + L - tau) / n
    return float(h / 3.0 * (ys[0] + ys[-1] + 4 * ys[1:-1:2].sum() + 2 * ys[2:-2:2].sum()))


# --------------------------------------------------------------------- the priced objective
def objective_grid(c, dmax, tau):
    """(L grid, C(L)) for C(L) = (1/L) int_0^L c(tau+s) ds, L on the DELTA grid."""
    if tau > dmax:
        return None, None
    K = int((dmax - tau) / DELTA)
    if K < 1:
        return None, None
    xs = tau + DELTA * np.arange(K + 1)
    vals = np.array([interp(c, dmax, x) for x in xs])
    if np.any(~np.isfinite(vals)):
        last = int(np.max(np.where(np.isfinite(vals))[0]))
        vals, xs, K = vals[:last + 1], xs[:last + 1], last
        if K < 1:
            return None, None
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (vals[:-1] + vals[1:]) * DELTA)])
    Ls = DELTA * np.arange(1, K + 1)
    return Ls, cum[1:] / Ls


def classify(Lstar, tau, dmax, lo):
    if abs(Lstar - lo) <= DELTA + 1e-9:
        return "floor"
    if abs(Lstar - (dmax - tau)) <= DELTA + 1e-9:
        return "ceiling"
    return "interior"


def run(lam_perturb=1.0, target_scale=1.0, noise_sigma=0.0, seed=0):
    """Return the per-cell records.

    lam_perturb != 1  -- breaks the identity's own input (a control that must fire).
    target_scale != 1 -- scales ONLY the comparison target `I_true`, leaving every number the log
        carries on the true curve.  This is the control the first run got WRONG: scaling the plant
        consistently scales both sides, so the check cannot fire and reads as a passing one
        (an INERT control is a defective check).
    noise_sigma       -- adds N(0, noise_sigma * J) to every logged J (the deployment's own noise).
    """
    rng = np.random.default_rng(seed)
    out = []
    for name, (A, B, Q, R) in make_plants().items():
        K, _ = lqr_gain(A, B, Q, R)
        W = np.eye(A.shape[0])
        c = [steady_cost(A, B, K, W, d) for d in range(DMAX_PROBE + 1)]
        dmax = max(d for d in range(DMAX_PROBE + 1) if c[d] != INF)
        taus = [t for t in (0.0, 2.0, 4.0, 6.0, 8.0) if max(t, 1) <= dmax - t and dmax - t >= 1]
        for tau in taus:
            Ls, C = objective_grid(c, dmax, tau)
            if Ls is None:
                continue
            lo = max(tau, 1.0)
            rows = []
            for lam in LAM_GRID:
                mask = Ls >= lo - 1e-9
                if not np.any(mask):
                    continue
                Li, Ci = Ls[mask], C[mask]
                obj = Ci + lam / Li
                i = int(np.argmin(obj))
                Lstar = float(Li[i])
                J_true = float(Ci[i] + lam / Lstar)
                J = J_true * (1.0 + noise_sigma * rng.standard_normal()) if noise_sigma else J_true
                G = Lstar * J - lam * lam_perturb
                rows.append({"lam": float(lam), "Lstar": Lstar, "J": J, "J_true": J_true, "G": G,
                             "class": classify(Lstar, tau, dmax, lo),
                             "x": tau + Lstar,
                             "c_true": interp(c, dmax, tau + Lstar),
                             "I_true": quadrature(c, dmax, tau, Lstar) * target_scale})
            out.append({"plant": name, "tau": tau, "dmax": dmax, "lo": lo, "cells": rows})
    return out


def rel(a, b):
    if not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return INF
    return abs(a - b) / abs(b)


def summarize(cells, c_key="c_true"):
    """[A] identity error, [B] marginal-identity error -- interior and pinned reported apart."""
    res = {"identity": [], "marginal_interior": [], "marginal_pinned": [], "sweep": []}
    interior = [r for r in cells if r["class"] == "interior"]
    for r in cells:
        res["identity"].append(rel(r["G"], r["I_true"]))
        e = rel(r["J"], r[c_key])
        (res["marginal_interior"] if r["class"] == "interior" else res["marginal_pinned"]).append(e)
    # [C] the sweep: a CENTRED difference needs the neighbours; its target is the span mean of c.
    for k in range(1, len(interior) - 1):
        a, m, b = interior[k - 1], interior[k], interior[k + 1]
        if b["Lstar"] - a["Lstar"] < 1e-9:
            continue
        slope = (b["G"] - a["G"]) / (b["Lstar"] - a["Lstar"])
        target = (b["I_true"] - a["I_true"]) / (b["Lstar"] - a["Lstar"])   # span mean of c
        res["sweep"].append({"err_vs_spanmean": rel(slope, target),
                             "span": b["Lstar"] - a["Lstar"],
                             "err_vs_point": rel(slope, m[c_key])})
    return res


def stat(v):
    v = [x for x in v if x != INF]
    if not v:
        return None
    v = np.array(v)
    return {"n": int(v.size), "median": float(np.median(v)), "worst": float(v.max())}


def main():
    cells_all, base = [], run()
    for blk in base:
        cells_all.extend(blk["cells"])
    S = summarize(cells_all)

    # the control: a 1% perturbation of lam must break [A]
    ctrl = []
    for blk in run(lam_perturb=1.01):
        ctrl.extend(blk["cells"])
    Sc = summarize(ctrl)

    # the control the FIRST run got wrong: scale only the comparison target, never the log
    wrong = []
    for blk in run(target_scale=1.3):
        wrong.extend(blk["cells"])
    Sw = summarize(wrong)

    # --- the noise arm: which route pays for the noise, and how much ---------------------------
    # [B] reads c off J directly (noise enters once); [C] differences G (noise enters as 1/span,
    # and G carries the factor L*).  Same cells, same draws.
    NREP = 200
    noise = {}
    for sigma in (1e-5, 1e-4, 1e-3, 1e-2):
        eb, ec = [], []
        for rep in range(NREP):
            cc = []
            for blk in run(noise_sigma=sigma, seed=1000 + rep):
                cc.extend(blk["cells"])
            Srep = summarize(cc)
            eb.extend(Srep["marginal_interior"])
            ec.extend([d["err_vs_spanmean"] for d in Srep["sweep"]])
        eb, ec = [e for e in eb if e != INF], [e for e in ec if e != INF]
        noise["%g" % sigma] = {
            "B_marginal_median": float(np.median(eb)),
            "C_sweep_median": float(np.median(ec)),
            "ratio_C_over_B": float(np.median(ec) / np.median(eb)),
        }

    n_int = sum(1 for r in cells_all if r["class"] == "interior")
    n_floor = sum(1 for r in cells_all if r["class"] == "floor")
    n_ceil = sum(1 for r in cells_all if r["class"] == "ceiling")

    R = {
        "build": BUILD,
        "ladder": {"n_prices": N_PRICES, "decades": "1e-2..1e5", "delta_L": DELTA},
        "cells": {"total": len(cells_all), "interior": n_int, "floor": n_floor, "ceiling": n_ceil},
        "A_identity": stat(S["identity"]),
        "A_identity_control_lam_1pct": stat(Sc["identity"]),
        "B_marginal_interior": stat(S["marginal_interior"]),
        "B_marginal_pinned": stat(S["marginal_pinned"]),
        "C_sweep_vs_spanmean": stat([d["err_vs_spanmean"] for d in S["sweep"]]),
        "C_sweep_vs_point": stat([d["err_vs_point"] for d in S["sweep"]]),
        "control_target_only_1.3x_identity": stat(Sw["identity"]),
        "control_target_only_1.3x_sweep_vs_spanmean": stat([d["err_vs_spanmean"] for d in Sw["sweep"]]),
        "D_noise_arm": noise,
    }
    print(json.dumps(R, indent=2, sort_keys=True))
    with open("spike_ident_v0_results.json", "w") as fh:
        json.dump(R, fh, indent=2, sort_keys=True)
    return R


if __name__ == "__main__":
    main()
