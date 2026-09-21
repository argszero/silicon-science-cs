#!/usr/bin/env python3
"""Issue #87 -- R400: THE FALLBACK CLAUSE, DISCHARGED.  Read the registration's own power arm through the
study's CALIBRATED declaration procedure, so the clause gets its answer in the study's own currency.

WHERE THIS SITS.  R398 audited the registered handicap ladder and found it nearly inert; it named a VALID
handicap instead -- axis C, replacing the rival's metric with a trace-matched random PSD matrix (24/24 cells
valid, median dR = +0.126 of a variance).  R399 confirmed both readings on a second graph and separated the
two mechanisms ("exactly inert" vs "absorbed by the tuning grid").  None of that yet answers the question the
registration actually promises to answer if the map comes back near-empty:

    WOULD THIS PIPELINE HAVE FOUND AN ADVANTAGE IF ONE EXISTED?

A handicap magnitude is not an answer to that question.  The answer is a DECLARATION COUNT under the
procedure the study itself uses -- the calibrated predictive null of R396/R397 -- as the rival is progressively
damaged.  That is what this round measures, and it is the last piece of the fallback clause.

THE PROCEDURE (R396's instrument, unchanged):
  * per bandwidth, a NULL population of cells built by the SAME generator with A = 0 (pure noise), 60 cells
    per bandwidth at the SAME split count the observed cells use;
  * a PREDICTIVE null per bandwidth: bootstrap the null cells, refit location+scale, draw a new cell value --
    the distribution a study cell would have if nothing were there;
  * a two-sided empirical p-value per observed cell with its resolution floor stated;
  * Benjamini-Hochberg at q = 0.05 across the round's declared family (the 24 cells at one handicap level).
  * The instrument's SIZE is validated on a holdout: fit the null on half the null cells, then count
    declarations among the other half -- cells that are null BY CONSTRUCTION.  A procedure that declares
    those is broken, and its declaration counts below would be meaningless.

THE FAMILY AND THE READ.  12 bands (2 phase conventions x 6 non-degenerate bandwidths) x 2 planted alignments
= 24 cells, at each of axis C's four handicap levels t = 0, 1/3, 2/3, 1.  t = 0 is the rival exactly as the
study matched it -- so the t = 0 row IS the study's own calibrated answer, reported here for the first time
under this procedure.  The power curve is the declaration count as a function of the handicap actually
applied (median dR, measured in R398).

WHAT IS PRE-REGISTERED HERE, BEFORE THE RUN (so the result can contradict it):
  Q1  the instrument's size on the holdout is ~5 % or below (R396 measured 2.08 %);
  Q2  at t = 0 the procedure declares the cells whose |delta| is large (the middle band, |delta| >= 0.1) and
      NOT the ones whose |delta| is small (|delta| < 0.05) -- i.e. between 8 and 16 of 24 declared;
  Q3  the count is non-decreasing in t, and at t = 1 (where the rival is damaged by ~0.12 of a variance) it
      is MATERIALLY higher than at t = 0 -- the fallback clause needs a non-trivial gap, and a gap of 0-1
      cells would leave it un-discharged even though the handicap is real.
  Q4  the honest boundary: with 24 cells and BH at q = 0.05 the smallest threshold is 0.05/24 = 0.00208, so
      the predictive null's resolution must be finer than ~1e-4; if it is not, the count is floor-limited and
      that must be reported as the instrument's limit rather than as a property of the map.

Run:  /usr/bin/python3 smoke_v14.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Reads smoke_v12_results.json (identity control); writes smoke_v14_results.json.
"""
import hashlib
import io
import json
import os
import sys
import zlib

import numpy as np

import smoke_v0 as S0
import smoke_v5 as S5
import smoke_v9 as S9
import smoke_v10 as S10
import smoke_v12 as S12

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v14_results.json")
REF12 = os.path.join(HERE, "smoke_v12_results.json")

GRAPH = "cycle"
QUBITS = S12.QUBITS
LAYERS = S12.LAYERS
CONVS = S12.CONVS
GAMMAS = S12.GAMMAS
ALPHAS = S12.ALPHAS
LEVELS = S12.LEVELS
N_TARGET = S12.N_TARGET
N_SPLITS = S12.N_SPLITS
SEED_T0 = S12.SEED_T0
N_NULL = 60                 # null cells per bandwidth
SEED_NULL0 = 800000         # a seed stream disjoint from the study's draws
N_SIM_PRED = 20000          # predictive draws: resolution 1/(N+1) = 5.0e-5, finer than BH's 0.00208
Q_LEVEL = 0.05
AXIS = "C_wrong_metric"


def band_kernels(q, edges, Z, conv, gamma, W, ctx):
    """The quantum kernel and the rival kernels at every handicap level of axis C."""
    Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
    out = {}
    for t in LEVELS:
        W_t = S12.axis_matrix(AXIS, t, W, ctx)
        ev = float(np.linalg.eigvalsh(0.5 * (W_t + W_t.T)).min())
        assert ev > 0.0, ("axis C left the PSD cone", t, ev)
        out[t] = {s: S5.k_mahalanobis(Z, W_t, gamma, s) for s in S5.S_GRID}
    return Kq, out


def cell_value(q, edges, Z, Kq, Ks_by_level, f, seed, var_f, sigma):
    """One cell: the same (split, noise) draw evaluated for the quantum arm and at every handicap level.

    Paired BY CONSTRUCTION -- the quantum risk comes from the same splits and the same noise as the rival's,
    so delta is a within-draw difference and its variance is the paired one.
    """
    rng = np.random.default_rng(seed + 7)
    n = len(Z)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
    rq = np.empty(N_SPLITS)
    rr = {t: np.empty(N_SPLITS) for t in LEVELS}
    for si, perm in enumerate(splits):
        tr, te = perm[:half], perm[half:]
        y = y_splits[si]
        ytr, yte, fte = y[tr], y[te], f[te]
        pred_q, _, _ = S5.krr_tuned({1.0: Kq[np.ix_(tr, tr)]}, ytr, {1.0: Kq[np.ix_(te, tr)]})
        rq[si] = S5.excess_risk(pred_q, yte, fte, var_f)
        for t in LEVELS:
            Ks = Ks_by_level[t]
            pred, _, _ = S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in Ks.items()}, ytr,
                                      {s: K[np.ix_(te, tr)] for s, K in Ks.items()})
            rr[t][si] = S5.excess_risk(pred, yte, fte, var_f)
    return rq.mean(), {t: float(rq.mean() - rr[t].mean()) for t in LEVELS}, float(rr[0.0].mean())


def observed_cells(q, edges, Z, metrics, emit=False):
    """The observed grid: for every band and planted alignment, one cell value per DRAW at every level."""
    rows = {}
    idx = 0
    for conv in CONVS:
        for gamma in GAMMAS:
            _, W, _ = metrics[conv][gamma]
            ctx = S12.mk_context(q, edges, Z, conv, gamma, W)
            Kq, Ks = band_kernels(q, edges, Z, conv, gamma, W, ctx)
            Q_int = S5.offdiag(S0.signless_laplacian(q, edges))
            for alpha in ALPHAS:
                deltas = {t: [] for t in LEVELS}
                rq_vals, rr0 = [], []
                for k in range(N_TARGET):
                    seed = SEED_T0 + 10007 * k + 101 * idx
                    A = S5.make_interaction(q, Q_int, alpha, seed)
                    f = S5.standardise(S5.target_raw(Z, A))
                    var_f = float(f.var(ddof=0))
                    mq, d, r0 = cell_value(q, edges, Z, Kq, Ks, f, seed, var_f,
                                           S5.NOISE_FRAC * float(f.std(ddof=0)))
                    rq_vals.append(mq)
                    rr0.append(r0)
                    for t in LEVELS:
                        deltas[t].append(d[t])
                key = "%s|%g|a=%+g" % (conv, gamma, alpha)
                rows[key] = dict(band="%s|%g" % (conv, gamma), conv=conv, gamma=gamma, alpha=alpha,
                                 r_quantum_draws=[float(x) for x in rq_vals],
                                 r_rival_t0_draws=[float(x) for x in rr0],
                                 cells={t: dict(draws=[float(x) for x in deltas[t]],
                                                mean=float(np.mean(deltas[t]))) for t in LEVELS})
            idx += 1
            if emit:
                print("   observed band %-16s done (%d/%d)" % ("%s|%g" % (conv, gamma), idx,
                                                               len(CONVS) * len(GAMMAS)))
    return rows


def null_cells(q, edges, Z, metrics, emit=False):
    """The null population: A = 0 (pure noise) through the SAME generator, per bandwidth."""
    out = {}
    idx = 0
    for conv in CONVS:
        for gamma in GAMMAS:
            _, W, _ = metrics[conv][gamma]
            ctx = S12.mk_context(q, edges, Z, conv, gamma, W)
            Kq, Ks = band_kernels(q, edges, Z, conv, gamma, W, ctx)
            vals = []
            for k in range(N_NULL):
                seed = SEED_NULL0 + 10007 * k + 101 * idx
                f = np.zeros(len(Z))                      # the Bayes predictor is the zero function
                vals.append(cell_value(q, edges, Z, Kq, Ks, f, seed, 1.0, S5.NOISE_FRAC)[1][0.0])
            out["%s|%g" % (conv, gamma)] = [float(x) for x in vals]
            idx += 1
            if emit:
                print("   null band %-16s done (%d/%d)" % ("%s|%g" % (conv, gamma), idx,
                                                           len(CONVS) * len(GAMMAS)))
    return out


def fit_null_instrument(null_by_band):
    """Per bandwidth: a shape fitted on the pooled standardised null draws (shared across the bandwidths of
    one convention, as R395 showed is what the data supports) and location+scale per bandwidth."""
    shapes, fits = {}, {}
    for conv in CONVS:
        bands = {g: list(null_by_band["%s|%g" % (conv, g)]) for g in GAMMAS}
        allz = []
        for g in GAMMAS:
            x = np.asarray(bands[g], dtype=float)
            mu, sg = float(np.median(x)), float(np.std(x, ddof=1))
            allz.extend(list((x - mu) / sg))
        shape = S10.fit_shape(np.asarray(allz, dtype=float))
        shapes[conv] = shape
        for g in GAMMAS:
            x = np.asarray(bands[g], dtype=float)
            mu, sg = S10.fit_loc_scale_quantile(x, shape)
            fits["%s|%g" % (conv, g)] = dict(mu=mu, sigma=sg, n=len(x), shape=shape)
    return shapes, fits


def bh(p, q=Q_LEVEL):
    p = np.asarray(p, dtype=float)
    m = len(p)
    order = np.argsort(p)
    ps = p[order]
    thr = q * (np.arange(1, m + 1)) / m
    below = np.where(ps <= thr)[0]
    k = int(below.max() + 1) if len(below) else 0
    rej = np.zeros(m, dtype=bool)
    if k:
        rej[order[:k]] = True
    return rej, k, thr


def predictive_pvalues(obs_rows, null_by_band, fits, seed=20260921):
    """One p-value per (cell, level) against the predictive null of that cell's bandwidth."""
    draws_cache = {}
    for key, fit in fits.items():
        draws_cache[key] = S10.predictive_draws(np.asarray(null_by_band[key], dtype=float), fit["shape"],
                                                n_sim=N_SIM_PRED, seed=seed + int(zlib.crc32(key.encode("utf-8")) % 100000))
    pv, floor = {}, {}
    for ck, row in obs_rows.items():
        band = "%s|%g" % (row["conv"], row["gamma"])
        for t in LEVELS:
            v = row["cells"][t]["mean"]
            d = draws_cache[band]
            pv[(ck, t)] = S10.pred_pvalue(v, d)
        floor[band] = 2.0 / (N_SIM_PRED + 1)
    return pv, floor


def holdout_size(null_by_band, seed=777):
    """The instrument's SIZE: fit the null on half the null cells, then declare among cells that are null BY
    CONSTRUCTION.  This is the only read that can say the counts below mean anything."""
    fit_cells, test_cells = {}, {}
    for key, vals in null_by_band.items():
        v = np.asarray(vals, dtype=float)
        half = len(v) // 2
        fit_cells[key] = list(v[:half])
        test_cells[key] = list(v[half:])
    shapes, fits = fit_null_instrument(fit_cells)
    ps, keys = [], []
    for key, vals in sorted(test_cells.items()):
        fit = fits[key]
        d = S10.predictive_draws(np.asarray(fit_cells[key], dtype=float), fit["shape"], n_sim=N_SIM_PRED,
                                 seed=seed + int(zlib.crc32(key.encode("utf-8")) % 100000))
        for x in vals:
            ps.append(S10.pred_pvalue(float(x), d))
            keys.append(key)
    ps = np.asarray(ps, dtype=float)
    rej, k, _ = bh(ps)
    return dict(n_null_cells=len(ps), n_declared=int(k), rate=float(k) / max(1, len(ps)),
                p_min=float(ps.min()), p_median=float(np.median(ps)),
                resolution=2.0 / (N_SIM_PRED + 1))


def dumps(rep):
    return json.dumps(rep, indent=1, sort_keys=True, default=float)


def build_once(emit=False):
    q = QUBITS
    edges = S5.edges_for(GRAPH, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, LAYERS) for g in GAMMAS} for c in CONVS}
    obs = observed_cells(q, edges, Z, metrics, emit=emit)
    nul = null_cells(q, edges, Z, metrics, emit=emit)
    shapes, fits = fit_null_instrument(nul)
    pv, floor = predictive_pvalues(obs, nul, fits)
    size = holdout_size(nul)
    keys = sorted(obs)
    power = {}
    for t in LEVELS:
        p = [pv[(ck, t)] for ck in keys]
        rej, k, thr = bh(p)
        power["t=%0.3f" % t] = dict(
            n_declared=int(k), n_cells=len(keys),
            declared=[ck for ck, r in zip(keys, rej) if r],
            p_values={ck: float(x) for ck, x in zip(keys, p)},
            bh_threshold_min=float(thr.min()),
            median_delta=float(np.median([obs[ck]["cells"][t]["mean"] for ck in keys])),
            max_p_declared=float(max([x for x, r in zip(p, rej) if r], default=float("nan"))),
        )
    return dict(round="R400", graph=GRAPH, axis=AXIS, levels=list(LEVELS), q_level=Q_LEVEL,
                n_target=N_TARGET, n_splits=N_SPLITS, n_null=N_NULL, n_sim_pred=N_SIM_PRED,
                shapes={c: shapes[c] for c in CONVS}, fits=fits, null_by_band=nul,
                observed=obs, p_values={"%s|t=%0.3f" % (k[0], k[1]): v for k, v in pv.items()},
                power=power, size_holdout=size, resolution_floor=floor), obs, nul


def main():
    print("=" * 100)
    print("ISSUE #87 -- R400: the fallback clause read through the study's own calibrated declaration")
    print("             procedure, along the VALID handicap axis (C: random-PSD metric).")
    print("=" * 100)
    rep, obs, nul = build_once(emit=True)
    fine = dumps(rep)
    rep2, _, _ = build_once(emit=False)
    deterministic = bool(fine == dumps(rep2))
    rep["deterministic_rebuild_identical"] = deterministic

    # C1 identity: this round's t = 0 cells must reproduce R398's committed axis-C t = 0 numbers exactly
    ref = json.loads(io.open(REF12, encoding="utf-8").read())
    worst, n = 0.0, 0
    for ck, row in obs.items():
        a = ref["rows"][ck]["cells"]["%s|t=0.000" % AXIS]["delta_mean"]
        worst = max(worst, abs(a - row["cells"][0.0]["mean"]))
        n += 1
    rep["c1_identity_vs_R398"] = dict(cells=n, max_abs_delta_diff=float(worst))

    print()
    print("-- CONTROLS ---------------------------------------------------------------------------------")
    print("   C1 identity vs R398's committed t=0 cells: %d cells, max |diff| %.3e" % (n, worst))
    print("   C4 determinism (byte-identical rebuild): %s" % deterministic)
    print("   C5 instrument resolution floor: %.2e  (BH's smallest threshold at m=24: %.2e)"
          % (2.0 / (N_SIM_PRED + 1), Q_LEVEL / 24))
    print()
    print("-- SIZE on the holdout (null cells that are null BY CONSTRUCTION) ---------------------------")
    s = rep["size_holdout"]
    print("   %d null cells: %d declared, rate %.2f%%   p_min %.4f  p_median %.3f"
          % (s["n_null_cells"], s["n_declared"], 100 * s["rate"], s["p_min"], s["p_median"]))
    print()
    print("-- THE POWER CURVE (BH q=0.05 across the 24-cell family, per handicap level) ----------------")
    print("   %-12s %9s %9s %10s" % ("level", "declared", "median dR", "median |delta|"))
    for t in LEVELS:
        pw = rep["power"]["t=%0.3f" % t]
        print("   t=%-9.2f %6d/24 %9s %10s" % (t, pw["n_declared"], "n/a" if t == 0 else "(see R398)",
                                               "%+.4f" % pw["median_delta"]))
    print()
    for t in LEVELS:
        pw = rep["power"]["t=%0.3f" % t]
        print("   t=%.2f not declared: %s" % (t, [k for k in sorted(obs) if k not in pw["declared"]]))
    print()
    print("   report sha256 = %s" % hashlib.sha256(fine.encode("utf-8")).hexdigest())
    io.open(OUT, "w", encoding="utf-8").write(fine)
    print("   written to %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
