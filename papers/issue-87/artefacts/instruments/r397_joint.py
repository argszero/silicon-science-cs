#!/usr/bin/env python3
"""Issue #87 -- R397 side-check F8: the twelve bands are NOT twelve independent reads.

WHY THIS EXISTS.  R397's F3 counted 11 of 12 bands with a cal/val dispersion ratio above 1 and priced that
count under INDEPENDENCE across bands (sign test p=0.0063; supremum-of-independent-bands p=0.0067).  But the
generator draws one split permutation and one noise vector per SEED, and every band was built from the SAME
seed sequence (cal: 7000+37i, val: 9000+53i, fresh: 30000+97i).  A seed whose realised cell is unusually
wide contributes that width to ALL TWELVE bands at once, so the count has far fewer independent units than
its face value.  This script prices the count under the dependence that actually exists, by permuting the
sixty per-seed profiles CONSISTENTLY ACROSS ALL BANDS -- the only permutation that respects the design.

  test A  cal/val: observed count 11 of 12, read against a profile-permutation null.
  test B  fresh: the same statistic on a single stream (no block difference by construction), where the
          profile permutation is the exact exchangeable null -- this calibrates the count statistic itself.
  test C  the contrast: the independent-band p from F3 next to the profile-permutation p.

Reads smoke_v8_results.json + smoke_v11_fresh_cache.json; writes r397_joint_results.json.
Run: /usr/bin/python3 r397_joint.py
"""
import hashlib
import io
import json
import os
import sys

import numpy as np

import smoke_v5 as S5
import smoke_v9 as S9
import smoke_v11 as S11

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "r397_joint_results.json")
N_PERM = 40000
CONVS = S11.CONVS
GAMMAS = S11.GAMMAS


def sd_rows(X):
    """sd with ddof=1 down the columns of X (rows = bands, cols = cells)."""
    return np.std(X, axis=1, ddof=1)


def count_null(X, n_big=40, n_small=20, n_perm=N_PERM, seed=20260921, fixed_split=False):
    """Draw n_big + n_small cell PROFILES, apply the SAME assignment to every band, and count how many bands
    show sd(big)/sd(small) > 1.

    The assignment is drawn once per permutation and shared across all bands, which is the only permutation
    that respects the design (one split permutation and one noise vector per seed, reused by every band).
    fixed_split=True reads the FIRST n_big columns as the observed block and the next n_small as the second
    block (the natural cal/val order); with nc == n_big + n_small the null is then a full profile permutation.
    """
    nb, nc = X.shape
    assert nc >= n_big + n_small, "need at least %d profiles, got %d" % (n_big + n_small, nc)
    X2 = X ** 2
    cnt = np.empty(n_perm, dtype=int)
    rng = np.random.default_rng(seed)
    chunk = 2000
    done = 0
    while done < n_perm:
        m = min(chunk, n_perm - done)
        if fixed_split and nc == n_big + n_small:
            idx = np.tile(np.arange(nc), (m, 1))
            for r in range(m):
                idx[r] = rng.permutation(nc)
        else:
            idx = np.argsort(rng.random((m, nc)), axis=1)
        Mp = np.zeros((m, nc))
        Mn = np.zeros((m, nc))
        rows = np.arange(m)[:, None]
        Mp[rows, idx[:, :n_big]] = 1.0
        Mn[rows, idx[:, n_big:n_big + n_small]] = 1.0
        S1 = Mp @ X.T
        Q1 = Mp @ X2.T
        S2 = Mn @ X.T
        Q2 = Mn @ X2.T
        v1 = (Q1 - S1 * S1 / n_big) / (n_big - 1)
        v2 = (Q2 - S2 * S2 / n_small) / (n_small - 1)
        ratio = np.sqrt(np.maximum(v1, 0.0)) / np.sqrt(np.maximum(v2, 1e-300))
        cnt[done:done + m] = (ratio > 1.0).sum(axis=1)
        done += m
    obs_ratio = sd_rows(X[:, :n_big]) / sd_rows(X[:, n_big:n_big + n_small])
    return cnt, int((obs_ratio > 1.0).sum()), obs_ratio


def main():
    raw = json.loads(io.open(S11.SRC8, encoding="utf-8").read())
    bands = [(c, g) for c in CONVS for g in GAMMAS]

    # ---- cal/val profiles: 60 cells per band, all twelve bands from the SAME seed sequence
    Xcv = np.array([[float(x) for x in raw["cal_means"][c][str(g)]] +
                    [float(x) for x in raw["val_means"][c][str(g)]] for c, g in bands])
    assert Xcv.shape == (12, 60), Xcv.shape
    cnt_cv, obs_cv, ratio_cv = count_null(Xcv, fixed_split=True)

    # ---- fresh profiles: the same layout (60 cells per band), one stream, no block difference by construction
    cached = json.loads(io.open(S11.FRESH_CACHE, encoding="utf-8").read())
    Xf = np.array([[float(x) for x in cached["fresh"][c][str(g)]] for c, g in bands])
    assert Xf.shape == (12, 60), Xf.shape
    cnt_f, obs_f, ratio_f = count_null(Xf, seed=777, fixed_split=True)

    p_cv = float(np.mean(cnt_cv >= obs_cv))
    p_f = float(np.mean(cnt_f >= obs_f))
    # both blocks pooled (cal+val+fresh, 180 cells), 40 vs 20 profiles -- the whole population
    Xall = np.concatenate([Xcv, Xf], axis=1)
    cnt_all, obs_all, ratio_all = count_null(Xall, seed=31337)

    print("test A  cal/val : observed count %2d/12  (median ratio %.3f)  PROFILE-permutation p = %.4f"
          % (obs_cv, float(np.median(ratio_cv)), p_cv))
    print("        null count distribution: mean %.2f  sd %.2f  5-95%% [%d, %d]  (independence would say 6.0/1.73)"
          % (cnt_cv.mean(), cnt_cv.std(ddof=1), int(np.percentile(cnt_cv, 5)), int(np.percentile(cnt_cv, 95))))
    print("test B  fresh   : observed count %2d/12  (median ratio %.3f)  PROFILE-permutation p = %.4f"
          % (obs_f, float(np.median(ratio_f)), p_f))
    print("        null count distribution: mean %.2f  sd %.2f  5-95%% [%d, %d]"
          % (cnt_f.mean(), cnt_f.std(ddof=1), int(np.percentile(cnt_f, 5)), int(np.percentile(cnt_f, 95))))
    print("test C  pooled 180-cell population: observed count %2d/12  p = %.4f"
          % (obs_all, float(np.mean(cnt_all >= obs_all))))
    print()
    print("        F3 priced the SAME observed count under independent bands -> p = 0.0067")

    # ---- how dependent are the bands, measured directly: cross-band correlation of the per-cell
    #      |deviation from the band median| profile, within each block
    def mean_pairwise_rho(X):
        A = np.abs(X - np.median(X, axis=1, keepdims=True))
        R = np.corrcoef(A)
        iu = np.triu_indices(R.shape[0], 1)
        return float(np.mean(R[iu]))

    dep = dict(cal_val_mean_pairwise_rho_of_absdev=mean_pairwise_rho(Xcv),
               fresh_mean_pairwise_rho_of_absdev=mean_pairwise_rho(Xf),
               independent_bands_would_be=0.0)
    print("        cross-band mean pairwise rank of |dev| profiles: cal/val %.3f   fresh %.3f   (independent = 0)"
          % (dep["cal_val_mean_pairwise_rho_of_absdev"], dep["fresh_mean_pairwise_rho_of_absdev"]))

    rep = dict(n_perm=N_PERM, cv=dict(observed_count=obs_cv, p=p_cv, ratios=[float(x) for x in ratio_cv],
                                      null_mean=float(cnt_cv.mean()), null_sd=float(cnt_cv.std(ddof=1)),
                                      null_p05=int(np.percentile(cnt_cv, 5)),
                                      null_p95=int(np.percentile(cnt_cv, 95))),
               fresh=dict(observed_count=obs_f, p=p_f, ratios=[float(x) for x in ratio_f],
                          null_mean=float(cnt_f.mean()), null_sd=float(cnt_f.std(ddof=1)),
                          null_p05=int(np.percentile(cnt_f, 5)), null_p95=int(np.percentile(cnt_f, 95))),
               pooled=dict(observed_count=obs_all, p=float(np.mean(cnt_all >= obs_all)),
                           ratios=[float(x) for x in ratio_all]),
               f3_independent_p=0.0067, dependence=dep, bands=["%s|%g" % b for b in bands])
    txt = json.dumps(rep, indent=1, sort_keys=True, default=float)
    io.open(OUT, "w", encoding="utf-8").write(txt)
    rep["report_sha256"] = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    print("\nreport sha256 = %s" % rep["report_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
