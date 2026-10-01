#!/usr/bin/env python3
"""Issue #87 -- R397: settle the seed-block dispersion question with a NON-PARAMETRIC test and a fresh
population.

WHY THIS ROUND EXISTS.  R396 found that the null's dispersion differs between the 40-draw calibration block
and the 20-draw validation block (ratio 1.44, 11 of 12 bands above 1, sign test p = 0.006) and judged it
against a SYNTHETIC reference that drew from the fitted null.  That reference carries the fitted family's tail
weight by construction, so it cannot say whether the observed gap is real heterogeneity or the fitted family
being too light-tailed.  A reconnaissance on the most extreme band pointed the other way: 24 fresh cells at a
third seed stream had sd 0.01768, i.e. 0.83x the calibration block and 1.40x the validation block -- so it may
be the VALIDATION block that is unusually tight, not the calibration block that is wide.

WHAT THIS ROUND MEASURES, with no parametric assumption anywhere in the test.

  F1  Identity: the fresh generator must reproduce a stored R396-block cell exactly (same seed).
  F2  A FRESH population -- new cells for all 12 (convention, bandwidth) bands at a third seed stream -- so
      the reference no longer depends on the fitted family.
  F3  The NON-PARAMETRIC reference for the 40-vs-20 dispersion ratio: pool the 120 available cells per band
      and compute the ratio for many random 40/20 partitions.  Exchangeability is then tested directly: the
      observed calibration-vs-validation ratio is read against that reference.
  F4  Independent block ratios from the fresh stream alone (three 20-cell blocks -> three pairwise ratios per
      band), so the block-to-block spread is measured on data that took no part in the original finding.
  F5  Does dispersion drift with the seed index?  Rank correlation and a first-half/second-half comparison
      inside the fresh stream (the leading candidate mechanism from R396).
  F6  How many draws does a stable dispersion estimate need -- the transferability question in its usable form.
  F7  Consequence: rebuild the predictive null from the POOLED population and re-read the grid, so the effect
      on what the study declares is reported rather than implied.

Run:  /usr/bin/python3 smoke_v11.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Reads smoke_v8_results.json (the two original null blocks); writes smoke_v11_results.json.
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
import smoke_v10 as S10

HERE = os.path.dirname(os.path.abspath(__file__))
SRC8 = os.path.join(HERE, "smoke_v8_results.json")
OUT = os.path.join(HERE, "smoke_v11_results.json")
FRESH_CACHE = os.path.join(HERE, "smoke_v11_fresh_cache.json")

CONVS = ("shifted", "unshifted")
GAMMAS = tuple(g for g in S5.GAMMAS if g > 0.0)
N_FRESH = 60                # fresh cells per band (paid for below: ~0.37 s per cell)
FRESH_SEED0 = 30000         # third seed stream, disjoint from 7000 (cal) and 9000 (val)
N_PARTITION = 4000          # random 40/20 partitions for the non-parametric reference
N_BLOCK_BOOT = 4000         # bootstrap draws for the dispersion-stability curve
SHAPE_STARTS = (-1.0, -0.5, 0.0, 0.5, 1.0)


# ------------------------------------------------------------------ one null cell, one gamma
def null_cell_means(q, edges, Z, conv, gamma, W_mean, Kq, rival, seed_gen, n_splits=S8.N_SPLITS):
    """The v8 null cell's delta, for ONE bandwidth -- same construction, so the fresh population is drawn from
    the same pipeline (identity is asserted against a stored cell in the report)."""
    rng = np.random.default_rng(seed_gen + 7)
    n = len(Z)
    half = n // 2
    splits = [rng.permutation(n) for _ in range(n_splits)]
    y_splits = [rng.normal(scale=S5.NOISE_FRAC, size=n) for _ in range(n_splits)]
    d = []
    for si, perm in enumerate(splits):
        tr, te = perm[:half], perm[half:]
        y = y_splits[si]
        rq = S8._fit_risks({1.0: Kq[np.ix_(tr, tr)]}, {1.0: Kq[np.ix_(te, tr)]}, y[tr], y[te], None, None,
                           "noise")
        rr = S8._fit_risks({s: K[np.ix_(tr, tr)] for s, K in rival.items()},
                           {s: K[np.ix_(te, tr)] for s, K in rival.items()}, y[tr], y[te], None, None, "noise")
        d.append(rq - rr)
    d = np.array(d)
    return dict(delta=d, mean=float(d.mean()))


def band_kernels(q, edges, Z, conv, gamma, metrics):
    """The kernels a band needs, built once and reused across seeds -- the expensive part is per SPLIT, not
    per seed, but the state matrix is shared."""
    _, W_mean, _ = metrics[gamma]
    Kq = S5.k_quantum(q, edges, Z, gamma, conv, S9.LAYERS)
    rival = {s: S5.k_mahalanobis(Z, W_mean, gamma, s) for s in S5.S_GRID}
    return Kq, rival


# ------------------------------------------------------------------ statistics used by the controls
def sd(v):
    return float(np.std(np.asarray(v, dtype=float), ddof=1))


def wilson(k, n, z=1.96):
    return S8.wilson(k, n)


def ratio_ref(pooled, n_big=40, n_small=20, n_rep=N_PARTITION, seed=12345):
    """The NON-PARAMETRIC reference for the dispersion ratio: choose n_big cells and n_small other cells from
    the pooled population at random and take sd(big)/sd(small).  Under exchangeability this is exactly the
    distribution the observed ratio is a draw from, and it carries the data's own tail weight -- which the
    synthetic reference of R396 could not."""
    x = np.asarray(pooled, dtype=float)
    N = len(x)
    rng = np.random.default_rng(seed)
    out = np.empty(n_rep)
    for i in range(n_rep):
        idx = rng.permutation(N)
        out[i] = sd(x[idx[:n_big]]) / sd(x[idx[n_big:n_big + n_small]])
    return out


def spearman_two_sided(v, seed_index):
    """Rank correlation with a permutation p-value (no distributional assumption), for the drift question."""
    v = np.asarray(v, dtype=float)
    r = np.asarray(seed_index, dtype=float)
    n = len(v)
    rv = np.argsort(np.argsort(v)).astype(float)
    rr = np.argsort(np.argsort(r)).astype(float)
    obs = float(np.corrcoef(rv, rr)[0, 1])
    rng = np.random.default_rng(4242)
    cnt = 0
    for _ in range(4000):
        if abs(float(np.corrcoef(rv, rng.permutation(rr))[0, 1])) >= abs(obs) - 1e-12:
            cnt += 1
    return obs, (cnt + 1) / 4001.0


def dispersion_stability(pooled, sizes=(10, 20, 40, 80, 160), n_rep=N_BLOCK_BOOT, seed=99):
    """How variable is a dispersion estimate at each sample size -- the transferability question in the form
    the study can act on."""
    x = np.asarray(pooled, dtype=float)
    rng = np.random.default_rng(seed)
    out = {}
    for n in sizes:
        if n > len(x):
            continue
        vals = np.array([sd(x[rng.integers(0, len(x), n)]) for _ in range(n_rep)])
        out["n=%d" % n] = dict(median=float(np.median(vals)), p05=float(np.percentile(vals, 5)),
                               p95=float(np.percentile(vals, 95)),
                               relative_p05_p95_width=float((np.percentile(vals, 95)
                                                             - np.percentile(vals, 5)) / np.median(vals)))
    return out


# ------------------------------------------------------------------ the report
def load_blocks():
    raw = json.loads(io.open(SRC8, encoding="utf-8").read())
    cal = {c: {g: list(raw["cal_means"][c][str(g)]) for g in GAMMAS} for c in CONVS}
    val = {c: {g: list(raw["val_means"][c][str(g)]) for g in GAMMAS} for c in CONVS}
    return raw, cal, val


def build_report():
    prev_path = os.path.join(HERE, "smoke_v10_results.json")
    PREV = json.loads(io.open(prev_path, encoding="utf-8").read()) if os.path.exists(prev_path) else {"rows": []}
    q = S9.QUBITS
    edges = S5.edges_for(S9.EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, S9.LAYERS) for g in S5.GAMMAS} for c in CONVS}
    raw, cal, val = load_blocks()

    # ---- F1 identity: one stored cell reproduced exactly through THIS generator
    Kq, rival = band_kernels(q, edges, Z, "shifted", 0.5, metrics["shifted"])
    idc = null_cell_means(q, edges, Z, "shifted", 0.5, None, Kq, rival, S8.CAL_SEED0)
    identity = dict(stored=cal["shifted"][0.5][0], reproduced=idc["mean"],
                    matches=bool(idc["mean"] == cal["shifted"][0.5][0]))

    # ---- F2 the fresh population
    fresh = {c: {} for c in CONVS}
    if os.path.exists(FRESH_CACHE):
        cached = json.loads(io.open(FRESH_CACHE, encoding="utf-8").read())
        assert cached["n_fresh"] == N_FRESH and cached["seed0"] == FRESH_SEED0, "cache does not match this run"
        for c in CONVS:
            for g in GAMMAS:
                fresh[c][g] = [float(x) for x in cached["fresh"][c][str(g)]]
        fresh_from_cache = True
    else:
        for c in CONVS:
            for g in GAMMAS:
                Kq, rival = band_kernels(q, edges, Z, c, g, metrics[c])
                fresh[c][g] = [null_cell_means(q, edges, Z, c, g, None, Kq, rival,
                                               FRESH_SEED0 + 97 * i)["mean"] for i in range(N_FRESH)]
        io.open(FRESH_CACHE, "w", encoding="utf-8").write(json.dumps(
            dict(n_fresh=N_FRESH, seed0=FRESH_SEED0, fresh={c: {str(g): fresh[c][g] for g in GAMMAS}
                                                            for c in CONVS}, sort_keys=True)))
        fresh_from_cache = False

    # ---- F3/F4 the ratios, all read against the non-parametric reference
    obs_ratio, obs_ref_rank, obs_ref_p = {}, {}, {}
    fresh_block, fresh_ref, pooled_n = {}, {}, {}
    for c in CONVS:
        for g in GAMMAS:
            key = "%s|%g" % (c, g)
            pooled = list(cal[c][g]) + list(val[c][g]) + list(fresh[c][g])
            pooled_n[key] = len(pooled)
            ref = ratio_ref(pooled, seed=12345 + 7 * len(key))
            o = sd(cal[c][g]) / sd(val[c][g])
            obs_ratio[key] = float(o)
            obs_ref_rank[key] = float(np.mean(ref < o))
            obs_ref_p[key] = float(2.0 * min(np.mean(ref <= o), np.mean(ref >= o)))
            # three 20-cell blocks from the fresh stream -> three pairwise ratios
            b = [np.asarray(fresh[c][g][i * 20:(i + 1) * 20], dtype=float) for i in range(3)]
            rb = [sd(b[0]) / sd(b[1]), sd(b[0]) / sd(b[2]), sd(b[1]) / sd(b[2])]
            fresh_block[key] = [float(x) for x in rb]
            fresh_ref[key] = float(np.mean([np.mean(ref < x) for x in rb]))

    obs_vals = np.array(list(obs_ratio.values()))
    sign_k = int(np.sum(obs_vals > 1))
    sign_p = min(1.0, 2.0 * sum(comb(len(obs_vals), i) for i in range(sign_k, len(obs_vals) + 1))
                 / 2 ** len(obs_vals))
    # the twelve observed ratios taken together: is the whole PATTERN above 1 explainable?
    keys = sorted(obs_ratio)
    band_refs = {}
    for i, k in enumerate(keys):
        c, g = k.split("|")
        g = float(g)
        band_refs[k] = ratio_ref(list(cal[c][g]) + list(val[c][g]) + list(fresh[c][g]), n_rep=1500,
                                seed=987 + i)
    rng2 = np.random.default_rng(555)
    sup_ref = np.empty(3000, dtype=int)
    for j in range(3000):
        sup_ref[j] = int(np.sum(np.array([band_refs[k][rng2.integers(0, len(band_refs[k]))] for k in keys]) > 1))
    sup_p = float(np.mean(sup_ref >= sign_k))

    # ---- F5 drift with the seed index, inside the fresh stream
    drift = {}
    for c in CONVS:
        for g in GAMMAS:
            v = np.asarray(fresh[c][g], dtype=float)
            idx = np.array([FRESH_SEED0 + 97 * i for i in range(N_FRESH)])
            rho, p = spearman_two_sided(np.abs(v - np.median(v)), idx)
            h = N_FRESH // 2
            drift["%s|%g" % (c, g)] = dict(spearman_abs_dev_vs_seed=rho, permutation_p=p,
                                           first_half_sd=sd(v[:h]), second_half_sd=sd(v[h:]),
                                           ratio=sd(v[:h]) / sd(v[h:]))

    # ---- F6 how many draws for a stable dispersion
    stab = {c: dispersion_stability(list(cal[c][g]) + list(val[c][g]) + list(fresh[c][g]))
            for c in CONVS for g in GAMMAS}

    # ---- F7 consequence: a predictive null from the POOLED population, and the re-read grid
    shapes, pooled_fits = {}, {}
    for c in CONVS:
        bands = {g: list(cal[c][g]) + list(val[c][g]) + list(fresh[c][g]) for g in GAMMAS}
        shape = S9.fit_shape_pooled(_standardise_all(bands))
        shapes[c] = shape
        pooled_fits[c] = {g: dict(family="shash", eps=shape["eps"], delta=shape["delta"],
                                  mu=float(np.median(bands[g])),
                                  sigma=float(S9.robust_location_scale(np.asarray(bands[g]))[1]))
                          for g in GAMMAS}
    pred = {c: {g: S10.predictive_draws(list(cal[c][g]) + list(val[c][g]) + list(fresh[c][g]),
                                       shapes[c], n_sim=S10.N_SIM_PRED, seed=4321 + i + (0 if c == "shifted"
                                                                                        else 17))
                for i, g in enumerate(GAMMAS)} for c in CONVS}

    rows = []
    for conv in CONVS:
        for alpha in S9.ALIGNS:
            key = "%s|alpha=%g" % (conv, alpha)
            cell = S9.cell_runner(q, edges, Z, alpha, conv, metrics[conv], S5.SEED_GEN, S9.matched_w)
            for g in GAMMAS:
                m = cell["rows"][g]["mean"]
                kd = cell["rows"][g]["kernel_max_absdiff"]
                old = next((x for x in PREV["rows"] if x["cell"] == key and x["gamma"] == g), None)
                rows.append(dict(cell=key, conv=conv, alpha=alpha, gamma=g, delta_mean=m,
                                 kernel_max_absdiff=kd, degenerate=bool(kd < S8.KERNEL_SAME_EPS),
                                 p_predictive_pooled=S10.pred_pvalue(m, pred[conv][g]),
                                 p_predictive_r396=(old or {}).get("p_predictive"),
                                 sign="loss" if m > 0 else "lead"))
    T = [r for r in rows if not r["degenerate"]]
    qq, _ = S7bh(np.array([r["p_predictive_pooled"] for r in T]))
    for i, r in enumerate(T):
        r["q_pooled"] = float(qq[i])
    declared = [r for r in T if r["q_pooled"] <= 0.05]

    return dict(
        round="R397",
        settings=dict(q=q, edges=S9.EDGE_KIND, layers=S9.LAYERS, convs=list(CONVS), gammas=list(GAMMAS),
                      n_fresh=N_FRESH, fresh_seed0=FRESH_SEED0, n_partition=N_PARTITION,
                      numpy=np.__version__, source="smoke_v8 null blocks + a fresh third stream"),
        controls=dict(
            F1_identity=identity,
            F2_population=dict(n_fresh_per_band=N_FRESH, n_pooled_per_band=pooled_n,
                               seed_streams=dict(cal=S8.CAL_SEED0, val=S8.VAL_SEED0, fresh=FRESH_SEED0)),
            F3_observed_ratio_vs_nonparametric=dict(
                per_band=obs_ratio, rank=obs_ref_rank, p=obs_ref_p,
                median_ratio=float(np.median(obs_vals)), n_above_1=sign_k, n_bands=len(obs_vals),
                sign_test_p=sign_p,
                twelve_band_supremum_p=sup_p,
                note="rank/p are read against random 40/20 partitions of the pooled 120 cells per band"),
            F4_fresh_block_ratios=dict(per_band=fresh_block, mean_ref_percentile=fresh_ref),
            F5_seed_drift=drift,
            F6_dispersion_stability=stab,
            F7_shapes={c: dict(eps=round(shapes[c]["eps"], 6), delta=round(shapes[c]["delta"], 6))
                       for c in CONVS},
        ),
        fdr=dict(m=len(T), pooled_predictive=dict(n_declared=len(declared),
                                                  n_leads=int(sum(r["sign"] == "lead" for r in declared))),
                 declared=[[r["cell"], r["gamma"], r["delta_mean"], r["p_predictive_pooled"], r["q_pooled"],
                            r["sign"]] for r in declared]),
        rows=rows,
    )


def _standardise_all(bands):
    std = []
    for g, x in bands.items():
        med, sc = S9.robust_location_scale(np.asarray(x, dtype=float))
        std.extend(((np.asarray(x, dtype=float) - med) / sc).tolist())
    return std


def S7bh(p):
    return S7.bh_qvalues(np.asarray(p, dtype=float), 0.05)


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
    print("ISSUE #87 -- R397: is the null's dispersion transferable across seed blocks?")
    print("=" * 100)
    print("F1 identity: stored %.12f reproduced %.12f  match=%s"
          % (c["F1_identity"]["stored"], c["F1_identity"]["reproduced"], c["F1_identity"]["matches"]))
    print("F2 population: %d fresh cells per band at seed0=%d, pooled %s per band"
          % (c["F2_population"]["n_fresh_per_band"], FRESH_SEED0,
             sorted(set(c["F2_population"]["n_pooled_per_band"].values()))))
    print()
    print("-- F3 the observed cal/val dispersion ratio against a NON-PARAMETRIC reference ---------------")
    f3 = c["F3_observed_ratio_vs_nonparametric"]
    print("   median ratio %.2f   above 1: %d/%d   sign test p=%.4f   twelve-band supremum p=%.4f"
          % (f3["median_ratio"], f3["n_above_1"], f3["n_bands"], f3["sign_test_p"],
             f3["twelve_band_supremum_p"]))
    print("   per band (ratio, percentile in its own pooled reference, p):")
    for k in sorted(f3["per_band"]):
        print("     %-16s %6.2f   rank %.3f   p %.3f" % (k, f3["per_band"][k], f3["rank"][k], f3["p"][k]))
    print()
    print("-- F4 the same question on FRESH blocks only (no part in R396's finding) --------------------")
    for k in sorted(c["F4_fresh_block_ratios"]["per_band"]):
        print("     %-16s ratios %s   mean percentile %.3f"
              % (k, ["%.2f" % x for x in c["F4_fresh_block_ratios"]["per_band"][k]],
                 c["F4_fresh_block_ratios"]["mean_ref_percentile"][k]))
    print()
    print("-- F5 does dispersion drift with the SEED index? --------------------------------------------")
    for k in sorted(c["F5_seed_drift"]):
        d = c["F5_seed_drift"][k]
        print("     %-16s spearman %+0.3f (p %.3f)  first/second half sd ratio %.2f"
              % (k, d["spearman_abs_dev_vs_seed"], d["permutation_p"], d["ratio"]))
    print()
    print("-- F6 how many draws does a stable dispersion estimate need? ---------------------------------")
    for k in sorted(c["F6_dispersion_stability"]):
        print("   %s" % k)
        for n in sorted(c["F6_dispersion_stability"][k], key=lambda s: int(s.split("=")[1])):
            v = c["F6_dispersion_stability"][k][n]
            print("     %-7s median %.5f  5-95%% width %.2fx of median" % (n, v["median"],
                                                                            v["relative_p05_p95_width"]))
        break
    print()
    print("-- F7 consequence: predictive null from the POOLED population -------------------------------")
    print("   pooled predictive declared %d (%d leads)   [R396's 80-cell instrument declared 24]"
          % (rep["fdr"]["pooled_predictive"]["n_declared"], rep["fdr"]["pooled_predictive"]["n_leads"]))
    print()
    print("   report sha256 = %s" % rep["report_sha256"])
    print("   written to %s" % os.path.basename(OUT))


if __name__ == "__main__":
    sys.exit(main())
