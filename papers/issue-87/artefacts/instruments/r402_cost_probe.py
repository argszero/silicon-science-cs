#!/usr/bin/env python3
"""R402 cost probe: measure the RIGHT term before sizing a multi-stream replication.

R401's lesson: a one-band probe at (N_TARGET=1, N_SPLITS=5) was dominated by the per-band METRIC
construction, not by the fits, and overestimated the full-run cost by 4x.  So this probe times the two
terms separately, at both qubit counts:

  t_setup(q)  = metric_field + the 5 arm kernels for one band (independent of draws/splits)
  t_fits(q)   = the 5-arm tuning fits for N_TARGET targets x N_SPLITS splits, one alpha

Then: cost_per_stream(q) = 12 * t_setup(q) + 12 * 2 * (N_TARGET/1) * (N_SPLITS/N_SPLITS_PROBE) * t_fits(q)
(the probe's N_TARGET and N_SPLITS are printed so the scaling is explicit, not assumed).
"""
import time

import numpy as np

import smoke_v0 as S0
import smoke_v5 as S5
import smoke_v9 as S9
import smoke_v12 as S12
import smoke_v15 as S15

N_TARGET, N_SPLITS = 1, 5          # probe settings
FULL_TARGET, FULL_SPLITS = 6, 40   # the round's settings


def probe(q):
    edges = S5.edges_for("cycle", q)
    Z = S5.bits_of(q)
    n = len(Z)
    half = n // 2
    Q_int = S5.offdiag(S0.signless_laplacian(q, edges))
    conv, gamma, alpha = "shifted", 0.5, 1.0
    t0 = time.perf_counter()
    _, W, _ = S5.metric_field(q, edges, Z, gamma, conv, S9.LAYERS)
    ctx = S15.mk_context(q, edges, conv, gamma, W)
    W_c1 = S15.axis_c_matrix(W, ctx, 1.0)
    q_kern = {s: S5.k_mahalanobis(Z, W, gamma, s) for s in S5.S_GRID}
    c_kern = {s: S5.k_mahalanobis(Z, W_c1, gamma, s) for s in S5.S_GRID}
    rbf = {e: S5.k_rbf_iso(Z, e) for e in S5.ELL2_GRID}
    Kq = S5.k_quantum(q, edges, Z, gamma, conv, S9.LAYERS)
    lin = S5.k_linear(Z)
    t_setup = time.perf_counter() - t0
    t1 = time.perf_counter()
    nfit = 0
    for k in range(N_TARGET):
        seed = 700000 + 10007 * k
        A = S5.make_interaction(q, Q_int, alpha, seed)
        f = S5.standardise(S5.target_raw(Z, A))
        var_f = float(f.var(ddof=0))
        rng = np.random.default_rng(seed + 7)
        sigma = S5.NOISE_FRAC * float(f.std(ddof=0))
        splits = [rng.permutation(n) for _ in range(N_SPLITS)]
        y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
        arms = dict(q={1.0: Kq}, rr=q_kern, rbf=rbf, lin={1.0: lin}, rc=c_kern)
        for si, perm in enumerate(splits):
            tr, te = perm[:half], perm[half:]
            y = y_splits[si]
            for name, Ks in arms.items():
                S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in Ks.items()}, y[tr],
                             {s: K[np.ix_(te, tr)] for s, K in Ks.items()})
                nfit += 1
    t_fits = time.perf_counter() - t1
    per_fit = t_fits / nfit
    setup_all = 12 * t_setup
    fits_all = 12 * 2 * (FULL_TARGET / N_TARGET) * (FULL_SPLITS / N_SPLITS) * t_fits
    return dict(q=q, t_setup=t_setup, t_fits=t_fits, n_fits=nfit, per_fit=per_fit,
                setup_all_bands=setup_all, fits_all_bands=2 * 12 * FULL_TARGET * FULL_SPLITS / N_TARGET / N_SPLITS * t_fits,
                est_map_seconds=setup_all + fits_all,
                est_map_minutes=(setup_all + fits_all) / 60.0)


if __name__ == "__main__":
    for q in (6, 8):
        r = probe(q)
        print("q=%d  setup/band %.2fs  fits(%d) %.2fs  per-fit %.4fs  | est map %.1f min"
              % (q, r["t_setup"], r["n_fits"], r["t_fits"], r["per_fit"], r["est_map_minutes"]))
