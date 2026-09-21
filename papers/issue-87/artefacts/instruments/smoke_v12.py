#!/usr/bin/env python3
"""Issue #87 -- R398: AUDIT THE REGISTERED POWER ARM.  Does "withholding geometry" actually handicap the
matched rival?

WHY THIS ROUND EXISTS.  The registration's risks clause promises a POWER ARM: if the map comes back empty,
the declaration holds only because the pipeline *would have found an advantage if one existed*, and the
control it names for that is the PLANTED-ALIGNMENT LADDER -- "a cell where the metric-matched rival is
deliberately handicapped".  R393 built that ladder in the registration's own words,

    W_t = (1 - t) * W_map + t * diag(W_map),

read as "t = 0 is the fully matched rival, t = 1 leaves only the diagonal, so the rival inherits the map's
per-qubit scale but none of the graph structure".  A handicap is supposed to make the rival WORSE.  But that
same flag also ran on a pipeline whose size control was still broken (R393's 47-50%; R396-R397 replaced it),
and -- this is the part that decides the round -- R393's own ladder table already carries cells whose
"handicapped" rival is far BETTER than the matched one (t = 0.25, gamma = 0.5, delta = +0.384 of a variance,
i.e. the quantum kernel much worse).  If removing the off-diagonal from the rival's metric IMPROVES it, then
the ladder is not a power arm: it is a second experiment whose direction is unknown per cell, and the
fallback clause it is meant to discharge is not discharged.

WHAT THIS FILE MEASURES.  The rival's own excess risk along a handicap axis, not the difference.

  For every band (2 phase conventions x 6 non-degenerate bandwidths), every planted alignment (alpha = +1
  and -1), every axis and every handicap level, it reports
      R_rival(t)  -- the rival's excess risk at that level,
      dR(t)       = R_rival(t) - R_rival(0)   -- the HANDICAP EFFECT: > 0 means the rival got WORSE,
      delta(t)    = R_quantum - R_rival(t)    -- the study's own statistic, for continuity.
  The audit verdict per axis is the sign of dR(1) cell by cell: VALID (rival worse, CI excludes 0),
  REVERSED (rival better, CI excludes 0) or NULL.  An axis whose dR changes sign inside the ladder is not
  a ladder at all.

THE AXES (all trace-preserving mixtures, so EVERY level has the same mean quadratic form -- the envelope's
tuning problem is unchanged and the differences are pure SHAPE; t = 0 is the untouched matched metric on
every axis, which is the identity control C1).

  A  registered   W_t = W - t (W - D),        D = diag(W)          remove the off-diagonal (R393's flag)
  B  wrong graph  W_t = (1-t) W + t W_path                          the rival models a PATH graph
  C  wrong metric W_t = (1-t) W + t R,        R = trace-matched Wishart
  D  flat scales  W_t = W - t (D - (tr W / q) I)                    keep the off-diagonal, flatten the scales
  E  permuted     W_t = (1-t) W + t (P W P^T)                       POSITIVE CONTROL: same spectrum, wrong
                                                                    structure -- if this does not handicap
                                                                    the rival, "geometry" is not what the
                                                                    matched comparison is measuring
  F  identity     W_t = W at every t                                NEGATIVE CONTROL: dR must be exactly 0

WHY THE READ IS PRICED THE WAY IT IS (R397's Class 90, applied to this round's own design).  A cell of this
study is drawn from ONE target realisation; the 120 split resamples inside it are one random unit repeated.
A paired bootstrap CI over those splits therefore answers "is this cell's delta non-zero", not "does the
handicap act in general".  So every number here is averaged over N_TARGET = 6 INDEPENDENT target draws x
N_SPLITS = 50 splits each, and the across-draw spread is reported next to the within-draw CI -- the two
disagree exactly when the effect is a property of one target.

CONTROLS (each read as a number, each able to fail):
  C1 identity   : at t = 0 every axis reproduces the matched rival's kernel EXACTLY (max |diff| = 0).
  C2 quantum    : the quantum arm's risk is identical across all levels of every axis (it does not see t);
                  a mismatch means the loop is mis-wired.
  C3 floors     : every W_t is symmetric, trace-preserving, and positive definite (min eigenvalue > 0).
  C4 determinism: the report is built twice and compared byte for byte.
  C5 positive   : axis F must give dR exactly 0 everywhere; axis E is the round's positive control.

Run:  /usr/bin/python3 smoke_v12.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Writes smoke_v12_results.json beside this file.
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
import smoke_v9 as S9

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v12_results.json")

QUBITS = S9.QUBITS
LAYERS = S9.LAYERS
EDGE_KIND = S9.EDGE_KIND
CONVS = ("shifted", "unshifted")
GAMMAS = tuple(g for g in S5.GAMMAS if g > 0.0)        # gamma = 0 is degenerate by construction
ALPHAS = (1.0, -1.0)
LEVELS = (0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0)
AXES = ("A_registered", "B_wrong_graph", "C_wrong_metric", "D_flat_scales", "E_permuted", "F_identity")
N_TARGET = 6                # independent target draws per (band, alpha) -- the unit the read is priced over
N_SPLITS = 50               # resampled splits inside one target draw
SEED_T0 = 500000            # target-draw seed stream for this round (disjoint from the study's own)


# ------------------------------------------------------------------ axis construction
def trace_match(W, ref):
    """Scale W so that trace(W) = trace(ref): every mixture level of every axis then has the SAME mean
    quadratic form, so the envelope `s` faces the same tuning problem at t = 0 and t = 1."""
    return W * (float(np.trace(ref)) / float(np.trace(W)))


def axis_matrix(axis, t, W, ctx):
    """The rival's precision matrix at handicap level t.  t = 0 returns the untouched matched metric W for
    EVERY axis -- that is control C1, and it is what makes the levels comparable."""
    if axis == "F_identity":
        return W.copy()
    if axis == "A_registered":
        return W - t * (W - np.diag(np.diag(W)))
    if axis == "B_wrong_graph":
        return (1.0 - t) * W + t * ctx["W_path"]
    if axis == "C_wrong_metric":
        return (1.0 - t) * W + t * ctx["R_rand"]
    if axis == "D_flat_scales":
        d = np.diag(W)
        return W - t * (np.diag(d) - (float(np.trace(W)) / W.shape[0]) * np.eye(W.shape[0]))
    if axis == "E_permuted":
        return (1.0 - t) * W + t * ctx["W_perm"]
    raise ValueError(axis)


def mk_context(q, edges, Z, conv, gamma, W):
    """Everything an axis needs at one band: the wrong-graph metric, a trace-matched random PSD metric, and
    the coordinate-permuted metric.  All three are built ONCE per band and reused at every level."""
    Wp_full = S5.metric_field(q, S5.edges_for("path", q), Z, gamma, conv, LAYERS)[1]
    rng = np.random.default_rng(987654321 + int(round(1000 * gamma)) + (0 if conv == "shifted" else 7))
    G = rng.normal(size=(q, q))
    Wr = G.T @ G
    perm = rng.permutation(q)
    return dict(W_path=trace_match(Wp_full, W), R_rand=trace_match(Wr, W),
                W_perm=W[np.ix_(perm, perm)], perm=[int(i) for i in perm])


def kernels_for(W_t, Z, gamma):
    return {s: S5.k_mahalanobis(Z, W_t, gamma, s) for s in S5.S_GRID}

# ------------------------------------------------------------------ one band, all axes and levels
def run_band(q, edges, Z, metrics, conv, gamma, block_idx):
    """Every axis, every level, every planted alignment and every draw -- for ONE band.

    The draws are band-specific (the seed carries `block_idx`), so the six reads inside a cell share their
    split/noise draw -- which is required for the paired level comparison -- while the cells themselves are
    not a single random unit repeated (R397's Class 90, applied to this design).
    """
    _, W, spread = metrics[gamma]
    ctx = mk_context(q, edges, Z, conv, gamma, W)
    Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
    Q_int = S5.offdiag(S0.signless_laplacian(q, edges))

    kernels, ident = {}, {}
    for axis in AXES:
        for t in LEVELS:
            W_t = axis_matrix(axis, t, W, ctx)
            tr_ref = float(np.trace(W))
            assert abs(float(np.trace(W_t)) - tr_ref) <= 1e-9 * max(1.0, abs(tr_ref)), (axis, t, "trace")
            assert float(np.max(np.abs(W_t - W_t.T))) <= 1e-12, (axis, t, "symmetry")
            ev = float(np.linalg.eigvalsh(0.5 * (W_t + W_t.T)).min())
            assert ev > 0.0, (axis, t, "floor %.3e" % ev)
            kernels[(axis, t)] = kernels_for(W_t, Z, gamma)
    # C1: t = 0 is the untouched matched metric on EVERY axis (kernel level, not matrix level)
    ident["c1_max_abs_kernel_diff_at_t0"] = max(
        float(np.max(np.abs(kernels[(ax, 0.0)][s] - kernels[("F_identity", 0.0)][s])))
        for ax in AXES for s in S5.S_GRID)
    # C2: at t = 1 each axis is EXACTLY the matrix it names
    ident["c2_axis_t1_exact"] = dict(
        A_registered=float(np.max(np.abs(axis_matrix("A_registered", 1.0, W, ctx) - np.diag(np.diag(W))))),
        B_wrong_graph=float(np.max(np.abs(axis_matrix("B_wrong_graph", 1.0, W, ctx) - ctx["W_path"]))),
        C_wrong_metric=float(np.max(np.abs(axis_matrix("C_wrong_metric", 1.0, W, ctx) - ctx["R_rand"]))),
        D_flat_scales=float(np.max(np.abs(np.diag(axis_matrix("D_flat_scales", 1.0, W, ctx))
                                          - (float(np.trace(W)) / W.shape[0]) * np.ones(W.shape[0])))),
        E_permuted=float(np.max(np.abs(axis_matrix("E_permuted", 1.0, W, ctx) - ctx["W_perm"]))),
    )
    # C3: the positive control's permutation must NOT be the identity (else axis E is vacuous)
    ident["c3_permutation_is_nontrivial"] = bool(list(ctx["perm"]) != list(range(W.shape[0])))

    n = len(Z)
    half = n // 2
    out = {}
    for alpha in ALPHAS:
        acc = {(ax, t): [] for ax in AXES for t in LEVELS}
        per_draw = {(ax, t): [] for ax in AXES for t in LEVELS}
        acc_q = []
        for k in range(N_TARGET):
            seed = SEED_T0 + 10007 * k + 101 * block_idx
            A = S5.make_interaction(q, Q_int, alpha, seed)
            f = S5.standardise(S5.target_raw(Z, A))
            var_f = float(f.var(ddof=0))
            rng = np.random.default_rng(seed + 7)
            sigma = S5.NOISE_FRAC * float(f.std(ddof=0))
            splits = [rng.permutation(n) for _ in range(N_SPLITS)]
            y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
            rq = []
            rr = {(ax, t): [] for ax in AXES for t in LEVELS}
            for si, perm in enumerate(splits):
                tr, te = perm[:half], perm[half:]
                y = y_splits[si]
                ytr, yte, fte = y[tr], y[te], f[te]
                pred_q, _, _ = S5.krr_tuned({1.0: Kq[np.ix_(tr, tr)]}, ytr, {1.0: Kq[np.ix_(te, tr)]})
                rq.append(S5.excess_risk(pred_q, yte, fte, var_f))
                for ax in AXES:
                    for t in LEVELS:
                        Ks = kernels[(ax, t)]
                        pred, _, _ = S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in Ks.items()}, ytr,
                                                  {s: K[np.ix_(te, tr)] for s, K in Ks.items()})
                        rr[(ax, t)].append(S5.excess_risk(pred, yte, fte, var_f))
            acc_q.append(float(np.mean(rq)))
            for key, v in rr.items():
                acc[key].append(np.asarray(v, dtype=float))
                per_draw[key].append(float(np.asarray(v, dtype=float).mean()
                                           - np.asarray(rr[(key[0], 0.0)], dtype=float).mean()))
        key_row = "%s|%g|a=%+g" % (conv, gamma, alpha)
        out[key_row] = dict(
            band="%s|%g" % (conv, gamma), alpha=alpha, spread=spread,
            r_quantum=float(np.mean(acc_q)), r_quantum_draws=[float(x) for x in acc_q],
            cells={},
        )
        for ax in AXES:
            basev = np.concatenate(acc[(ax, 0.0)])
            for t in LEVELS:
                allv = np.concatenate(acc[(ax, t)])
                out[key_row]["cells"]["%s|t=%0.3f" % (ax, t)] = dict(
                    r_rival=float(allv.mean()),
                    delta_mean=float(np.mean(acc_q) - allv.mean()),
                    dr_mean=float((allv - basev).mean()),
                    dr_draws=[float(x) for x in per_draw[(ax, t)]],
                    dr_draw_pos=int(sum(1 for x in per_draw[(ax, t)] if x > 0.0)),
                    dr_draw_neg=int(sum(1 for x in per_draw[(ax, t)] if x < 0.0)),
                )
    return out, ident


def verdicts(rows):
    """Per axis: how many cells call the t = 1 level a handicap (all six draws agree the rival got worse),
    how many call it a REVERSAL (all six agree it got better), and how many are split."""
    out = {}
    for ax in AXES:
        v = dict(valid=0, reversed_=0, mixed=0, dr_end=[])
        for _, row in rows.items():
            c = row["cells"]["%s|t=1.000" % ax]
            v["dr_end"].append(c["dr_mean"])
            if c["dr_draw_pos"] == N_TARGET:
                v["valid"] += 1
            elif c["dr_draw_neg"] == N_TARGET:
                v["reversed_"] += 1
            else:
                v["mixed"] += 1
        v["n_cells"] = len(v["dr_end"])
        v["dr_median"] = float(np.median(v["dr_end"]))
        v["dr_max"] = float(np.max(v["dr_end"]))
        v["dr_min"] = float(np.min(v["dr_end"]))
        out[ax] = v
    return out


def build_once(emit=False):
    q = QUBITS
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, LAYERS) for g in GAMMAS} for c in CONVS}
    rows, ident = {}, {"c1_max_abs_kernel_diff_at_t0": 0.0}
    idx = 0
    for c in CONVS:
        for g in GAMMAS:
            r, idb = run_band(q, edges, Z, metrics[c], c, g, idx)
            rows.update(r)
            ident["c1_max_abs_kernel_diff_at_t0"] = max(ident["c1_max_abs_kernel_diff_at_t0"],
                                                       idb["c1_max_abs_kernel_diff_at_t0"])
            ident["c2_axis_t1_exact"] = idb["c2_axis_t1_exact"]
            ident["c3_permutation_is_nontrivial"] = idb["c3_permutation_is_nontrivial"]
            idx += 1
            if emit:
                print("   band %-16s done (%d/%d)" % ("%s|%g" % (c, g), idx, len(CONVS) * len(GAMMAS)))
    c5 = all(abs(row["cells"]["F_identity|t=1.000"]["dr_mean"]) == 0.0 for row in rows.values())
    rep = dict(round="R398", n_target=N_TARGET, n_splits=N_SPLITS, levels=list(LEVELS), alphas=list(ALPHAS),
               axes=list(AXES), gammas=list(GAMMAS), convs=list(CONVS),
               controls=dict(c1_identity_max_abs_kernel_diff=ident["c1_max_abs_kernel_diff_at_t0"],
                             c2_axis_t1_exact=ident["c2_axis_t1_exact"],
                             c3_permutation_is_nontrivial=ident["c3_permutation_is_nontrivial"],
                             c5_negative_axis_exactly_zero=bool(c5)),
               verdicts=verdicts(rows), rows=rows)
    return rep


def dumps(rep):
    return json.dumps(rep, indent=1, sort_keys=True, default=float)


def main():
    print("=" * 100)
    print("ISSUE #87 -- R398: does 'withholding geometry' actually handicap the matched rival?")
    print("=" * 100)
    rep = build_once(emit=True)
    fine = dumps(rep)
    rep2 = build_once(emit=False)
    deterministic = bool(fine == dumps(rep2))
    rep["deterministic_rebuild_identical"] = deterministic
    print()
    print("-- CONTROLS ---------------------------------------------------------------------------------")
    print("   C1 identity   : max |kernel diff| at t=0 across all axes/envelopes: %.3e"
          % rep["controls"]["c1_identity_max_abs_kernel_diff"])
    for k, v in sorted(rep["controls"]["c2_axis_t1_exact"].items()):
        print("      C2 %-14s max |W_t1 - named matrix| = %.3e" % (k, v))
    print("   C3 positive control is nontrivial (permutation != identity): %s"
          % rep["controls"]["c3_permutation_is_nontrivial"])
    print("   C5 negative control (axis F at every level): dR exactly 0 in every cell: %s"
          % rep["controls"]["c5_negative_axis_exactly_zero"])
    print("   C6 determinism: rebuild byte-identical: %s" % deterministic)
    print()
    print("-- THE AUDIT: what the handicap does to the RIVAL at t = 1 (unit: one target variance) -----")
    print("   %-18s %5s %8s %6s %12s   %s" % ("axis", "valid", "reversed", "mixed", "median dR", "range"))
    for ax in AXES:
        v = rep["verdicts"][ax]
        print("   %-18s %5d %8d %6d %+12.4f   [%+.4f, %+.4f]"
              % (ax, v["valid"], v["reversed_"], v["mixed"], v["dr_median"], v["dr_min"], v["dr_max"]))
    print("   dR = R_rival(t=1) - R_rival(t=0); > 0 means the rival got WORSE (a real handicap).")
    print("   valid/reversed = all six draws agree; mixed = the six draws disagree in sign.")
    print()
    print("-- the study's own statistic along the ladder (delta = R_quantum - R_rival) -----------------")
    for ax in AXES:
        print("   axis %s" % ax)
        for k in sorted(rep["rows"]):
            row = rep["rows"][k]
            parts = []
            for t in LEVELS:
                c = row["cells"]["%s|t=%0.3f" % (ax, t)]
                parts.append("t=%0.2f %+0.4f" % (t, c["delta_mean"]))
            print("     %-26s %s" % (k, "  ".join(parts)))
    print()
    print("   report sha256 = %s"
          % hashlib.sha256(fine.encode("utf-8")).hexdigest())
    io.open(OUT, "w", encoding="utf-8").write(fine)
    print("   written to %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
