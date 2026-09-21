#!/usr/bin/env python3
"""Issue #87 -- R398 second instrument: is the "metric-matched" rival anything other than the plain
isotropic RBF baseline?

WHY THIS EXISTS.  R398's audit found the registered handicap axis (A: withhold the off-diagonal of the map's
mean metric) to be nearly inert -- median dR = +0.0074 of a variance over 24 cells, 19 of them with the six
target draws disagreeing in sign -- and axis D (flatten the diagonal heterogeneity) to be EXACTLY inert
(|dR| ~ 1e-13 in every cell, i.e. floating-point zero).  A floating-point-zero effect has a mechanism, not a
small-sample explanation: it means the quantity being manipulated was zero to begin with -- the mean metric's
diagonal is UNIFORM.  If that is right, then two further statements follow, and both are checkable here:

  (1) the study graph is a cycle, which is vertex-transitive, so every qubit carries the same scale and
      diag(W) = c * I.  Axis A's t = 1 endpoint is then W -> c * I, and the rival's kernel becomes
      exp(-s c gamma^2 ||z - z'||^2 / 2) -- the ISOTROPIC RBF family in Hamming distance, with the envelope
      the protocol tunes anyway;
  (2) if so, the entire metric-matching construction buys the rival nothing over the plain isotropic
      baseline the field compares against -- which is a claim about the study's own control, not about the
      quantum kernel, and it must be measured, not inferred.

WHAT THIS FILE MEASURES.  Per band, per planted alignment, per draw, on the SAME seeds as smoke_v12.py:
   * max |diag(W) - mean(diag(W))| / mean(diag(W))     -- the uniformity claim behind (1);
   * the paired difference R_matched - R_rbf_iso       -- the claim in (2), with its per-draw signs.
Two kernels, one protocol (krr_tuned for both), so the comparison is about the kernel family and not about
the tuning.  This is an INDEPENDENT instrument for the same conclusion: axis A's t = 1 endpoint reaches the
same family through the mixture machinery, the RBF arm reaches it directly.

Reads nothing; writes r398_rbf_check_results.json.  Run: /usr/bin/python3 r398_rbf_check.py
"""
import hashlib
import io
import json
import os
import sys

import numpy as np

import smoke_v0 as S0
import smoke_v5 as S5
import smoke_v9 as S9

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "r398_rbf_check_results.json")

QUBITS = S9.QUBITS
LAYERS = S9.LAYERS
EDGE_KIND = S9.EDGE_KIND
CONVS = ("shifted", "unshifted")
GAMMAS = tuple(g for g in S5.GAMMAS if g > 0.0)
ALPHAS = (1.0, -1.0)
N_TARGET = 6
N_SPLITS = 50
SEED_T0 = 500000


def main():
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    n = len(Z)
    half = n // 2
    rows = {}
    diag_uniformity = {}
    idx = 0
    for conv in CONVS:
        for gamma in GAMMAS:
            _, W, _ = S5.metric_field(q, edges, Z, gamma, conv, LAYERS)
            d = np.diag(W)
            diag_uniformity["%s|%g" % (conv, gamma)] = dict(
                mean_diag=float(d.mean()), max_abs_dev=float(np.max(np.abs(d - d.mean()))),
                relative_max_abs_dev=float(np.max(np.abs(d - d.mean())) / abs(float(d.mean()))))
            K_m = {s: S5.k_mahalanobis(Z, W, gamma, s) for s in S5.S_GRID}
            K_r = {e: S5.k_rbf_iso(Z, e) for e in S5.ELL2_GRID}
            for alpha in ALPHAS:
                diffs, q_risk = [], []
                for k in range(N_TARGET):
                    seed = SEED_T0 + 10007 * k + 101 * idx
                    A = S5.make_interaction(q, S5.offdiag(S0.signless_laplacian(q, edges)), alpha, seed)
                    f = S5.standardise(S5.target_raw(Z, A))
                    var_f = float(f.var(ddof=0))
                    rng = np.random.default_rng(seed + 7)
                    sigma = S5.NOISE_FRAC * float(f.std(ddof=0))
                    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
                    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
                    rm, rr = [], []
                    for si, perm in enumerate(splits):
                        tr, te = perm[:half], perm[half:]
                        y = y_splits[si]
                        ytr, yte, fte = y[tr], y[te], f[te]
                        pm, _, _ = S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in K_m.items()}, ytr,
                                                {s: K[np.ix_(te, tr)] for s, K in K_m.items()})
                        pr, _, _ = S5.krr_tuned({e: K[np.ix_(tr, tr)] for e, K in K_r.items()}, ytr,
                                                {e: K[np.ix_(te, tr)] for e, K in K_r.items()})
                        rm.append(S5.excess_risk(pm, yte, fte, var_f))
                        rr.append(S5.excess_risk(pr, yte, fte, var_f))
                    diffs.append(float(np.mean(rm) - np.mean(rr)))
                    q_risk.append(float(np.mean(rm)))
                key = "%s|%g|a=%+g" % (conv, gamma, alpha)
                rows[key] = dict(band="%s|%g" % (conv, gamma), alpha=alpha,
                                 r_matched=float(np.mean(q_risk)),
                                 diff_matched_minus_rbf_mean=float(np.mean(diffs)),
                                 diff_draws=[float(x) for x in diffs],
                                 diff_draw_gt0=int(sum(1 for x in diffs if x > 0)),
                                 diff_draw_lt0=int(sum(1 for x in diffs if x < 0)))
                print("%-26s R_matched %.4f   R_matched - R_rbf_iso: mean %+0.4f   draws(+-): %d/%d"
                      % (key, np.mean(q_risk), np.mean(diffs),
                         sum(1 for x in diffs if x > 0), sum(1 for x in diffs if x < 0)))
            idx += 1

    allsq = [r["diff_matched_minus_rbf_mean"] for r in rows.values()]
    signs = [r["diff_draws"] for r in rows.values()]
    flat = [x for ds in signs for x in ds]
    rep = dict(round="R398b", n_target=N_TARGET, n_splits=N_SPLITS,
               diag_uniformity_of_mean_metric=diag_uniformity,
               max_relative_diag_deviation=float(max(v["relative_max_abs_dev"]
                                                     for v in diag_uniformity.values())),
               cells=rows,
               summary=dict(n_cells=len(allsq), mean_of_cell_means=float(np.mean(allsq)),
                            median_of_cell_means=float(np.median(allsq)),
                            min_cell=float(np.min(allsq)), max_cell=float(np.max(allsq)),
                            n_cells_all_draws_positive=int(sum(1 for ds in signs
                                                               if all(x > 0 for x in ds))),
                            n_cells_all_draws_negative=int(sum(1 for ds in signs
                                                               if all(x < 0 for x in ds))),
                            n_draws=len(flat), n_draws_positive=int(sum(1 for x in flat if x > 0)),
                            n_draws_negative=int(sum(1 for x in flat if x < 0))))
    txt = json.dumps(rep, indent=1, sort_keys=True, default=float)
    io.open(OUT, "w", encoding="utf-8").write(txt)
    rep["report_sha256"] = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    print()
    print("diag(W) uniformity across all 12 bands: max relative deviation from uniform = %.3e"
          % rep["max_relative_diag_deviation"])
    s = rep["summary"]
    print("R_matched - R_rbf_iso over %d cells: mean %+0.4f  median %+0.4f  range [%+0.4f, %+0.4f]"
          % (s["n_cells"], s["mean_of_cell_means"], s["median_of_cell_means"], s["min_cell"], s["max_cell"]))
    print("cells where all %d draws agree positive: %d ; all negative: %d"
          % (N_TARGET, s["n_cells_all_draws_positive"], s["n_cells_all_draws_negative"]))
    print("draws: %d, positive %d, negative %d" % (s["n_draws"], s["n_draws_positive"], s["n_draws_negative"]))
    print("report sha256 = %s" % rep["report_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
