#!/usr/bin/env python3
"""Issue #87 -- R401: the q = 8 cell.  Every number in the advantage map so far rests on ONE qubit count
(q = 6, two graphs, one seed stream).  This round puts the map's own claims on a second qubit count and asks
which of them survive the change.

WHAT IS MEASURED.

  A  Qubit-count reach: diag(W) uniformity at q = 8 for the three graphs (the cheap mechanism table), so the
     symmetry argument of R398/R399 is read at a second dimension rather than assumed to carry over.
  B  THE MAP at q = 8: the study's own grid -- 12 bands (2 phase conventions x 6 non-degenerate bandwidths) x
     2 planted alignments (alpha = +-1) -- with the paired difference
         delta = R_quantum - R_matched
     exactly as R391-R400 computed it (6 independent target draws x 50 splits), so the q = 8 column is
     directly comparable to the q = 6 column of the committed record.
  C  A degeneracy diagnostic the earlier rounds did not report per cell: the quantum kernel's ALIVENESS
     (mean off-diagonal) and the metric's SPREAD at both qubit counts.  The map's central pattern -- the
     matched rival dominating a middle band -- could in principle be a degeneracy artefact of the kernel
     flattening, and if the pattern tracks the KERNEL'S HEALTH rather than the alignment structure, the map
     means something different from what the registration asked.  Reported as a number, at both q.
  D  The two baseline arms that make "matched" meaningful here: the plain isotropic RBF and the linear floor.
     R398 showed the matched rival and the isotropic baseline are within ~0.005 of a variance at q = 6; this
     round checks that this holds at the second qubit count too, because it is a property of the CONTRAST the
     paper draws between its rival families, not of the graph.
  E  The headline's robustness at q = 8: replace the matched rival's metric with a trace-matched random PSD
     matrix (R398/R399's valid handicap axis C) and re-read the same cells, so "the rival wins even when badly
     matched" is checked at the second qubit count too.

WHAT IS PRE-REGISTERED HERE, BEFORE THE RUN (so the result can contradict it):
  Q1  the map's SIGN PATTERN is the same at q = 8 as at q = 6 in at least 20 of the 24 cells (the patterns
      being: matched rival dominates the middle band; the quantum kernel leads at the extremes);
  Q2  the quantum kernel's aliveness at q = 8 is lower than at q = 6 in every band (more qubits, same layers,
      so the fidelity kernel concentrates), and the aliveness drop is LARGEST in the middle band;
  Q3  the matched-vs-isotropic-RBF separation stays small at q = 8 (|median| <= 0.02 of a variance), as at q = 6;
  Q4  the four bandwidth cells that carry the main claim (matched rival ahead by >= 0.25 of a variance at
      q = 6) are still ahead by >= 0.25 at q = 8 -- i.e. the claim is not a small-q coincidence.

Run:  /usr/bin/python3 smoke_v15.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Reads smoke_v5_results.json (the q = 6 map) and smoke_v12_results.json (the q = 6 axis-C cells); writes
smoke_v15_results.json.
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
import smoke_v12 as S12

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v15_results.json")
REF_MAP = os.path.join(HERE, "smoke_v5_results.json")
REF_AXISC = os.path.join(HERE, "smoke_v12_results.json")

Q6 = 6
QUBITS = 8                  # this round's qubit count
LAYERS = S9.LAYERS
EDGE_KIND = "cycle"
CONVS = S12.CONVS
GAMMAS = S12.GAMMAS
ALPHAS = S12.ALPHAS
N_TARGET = 6
N_SPLITS = 40                  # S5.N_SPLITS: the same split count R391 used, so the q = 6 and q = 8 columns are like-for-like
SEED_T0 = 900000            # a seed stream disjoint from every earlier round's

MAIN_CLAIM_CELLS_Q6 = [("shifted", 0.5), ("shifted", 1.0), ("unshifted", 1.0), ("unshifted", 2.0)]


def axis_c_matrix(W, ctx, t):
    """R398's valid handicap axis: the rival's metric mixed towards a trace-matched random PSD matrix."""
    return (1.0 - t) * W + t * ctx["R_rand"]


def mk_context(q, edges, conv, gamma, W):
    """The random PSD metric of axis C, built per band exactly as R398/R399 built it."""
    rng = np.random.default_rng(987654321 + int(round(1000 * gamma)) + (0 if conv == "shifted" else 7))
    G = rng.normal(size=(q, q))
    Wr = G.T @ G
    return dict(R_rand=S12.trace_match(Wr, W))


def diag_table(q):
    """A: the measurement that made R398's mechanism falsifiable, at this round's qubit count."""
    Z = S5.bits_of(q)
    out = {}
    for kind in ("cycle", "path", "complete"):
        edges = S5.edges_for(kind, q)
        for conv in CONVS:
            for g in GAMMAS:
                _, W, spread = S5.metric_field(q, edges, Z, g, conv, LAYERS)
                d = np.diag(W)
                out["%s|%s|%g" % (kind, conv, g)] = dict(
                    mean=float(d.mean()), max_abs_dev=float(np.max(np.abs(d - d.mean()))),
                    relative_max_abs_dev=float(np.max(np.abs(d - d.mean())) / abs(float(d.mean()))),
                    spread=float(spread))
    return out


def run_map(q, emit=False, only=None):
    """B/C/D/E: the map at this qubit count, with the aliveness diagnostic, the two baseline arms and the
    axis-C handicap."""
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    n = len(Z)
    half = n // 2
    Q_int = S5.offdiag(S0.signless_laplacian(q, edges))
    rows = {}
    # the band index is the POSITION IN THE FULL LIST, not in the filtered one: it feeds the seed, so a
    # single-band rebuild must reproduce the same cells as the full run (a filtered index would silently
    # produce a different target and make the determinism control vacuous).
    bands_all = [(c, g) for c in CONVS for g in GAMMAS]
    bands = [(i, c, g) for i, (c, g) in enumerate(bands_all) if only is None or (c, g) in only]
    for idx, conv, gamma in bands:
        if True:
            _, W, spread = S5.metric_field(q, edges, Z, gamma, conv, LAYERS)
            ctx = mk_context(q, edges, conv, gamma, W)
            W_c1 = axis_c_matrix(W, ctx, 1.0)
            q_kern = {s: S5.k_mahalanobis(Z, W, gamma, s) for s in S5.S_GRID}
            c_kern = {s: S5.k_mahalanobis(Z, W_c1, gamma, s) for s in S5.S_GRID}
            rbf = {e: S5.k_rbf_iso(Z, e) for e in S5.ELL2_GRID}
            Kq = S5.k_quantum(q, edges, Z, gamma, conv, LAYERS)
            lin = S5.k_linear(Z)
            aliveness = float((Kq.sum() - n) / (n * (n - 1)))
            for alpha in ALPHAS:
                acc = {k: [] for k in ("q", "rr", "rbf", "lin", "rc")}
                for k in range(N_TARGET):
                    seed = SEED_T0 + 10007 * k + 101 * idx
                    A = S5.make_interaction(q, Q_int, alpha, seed)
                    f = S5.standardise(S5.target_raw(Z, A))
                    var_f = float(f.var(ddof=0))
                    rng = np.random.default_rng(seed + 7)
                    sigma = S5.NOISE_FRAC * float(f.std(ddof=0))
                    splits = [rng.permutation(n) for _ in range(N_SPLITS)]
                    y_splits = [f + rng.normal(scale=sigma, size=n) for _ in range(N_SPLITS)]
                    per = {k2: [] for k2 in acc}
                    for si, perm in enumerate(splits):
                        tr, te = perm[:half], perm[half:]
                        y = y_splits[si]
                        ytr, yte, fte = y[tr], y[te], f[te]
                        arms = dict(q={1.0: Kq}, rr=q_kern, rbf=rbf, lin={1.0: lin}, rc=c_kern)
                        for name, Ks in arms.items():
                            pred, _, _ = S5.krr_tuned({s: K[np.ix_(tr, tr)] for s, K in Ks.items()}, ytr,
                                                      {s: K[np.ix_(te, tr)] for s, K in Ks.items()})
                            per[name].append(S5.excess_risk(pred, yte, fte, var_f))
                    for name in acc:
                        acc[name].append(float(np.mean(per[name])))
                key = "%s|%g|a=%+g" % (conv, gamma, alpha)
                rows[key] = dict(band="%s|%g" % (conv, gamma), conv=conv, gamma=gamma, alpha=alpha,
                                 spread=spread, aliveness_q8=aliveness, n_points=n,
                                 r_quantum=float(np.mean(acc["q"])), r_matched=float(np.mean(acc["rr"])),
                                 r_rbf=float(np.mean(acc["rbf"])), r_linear=float(np.mean(acc["lin"])),
                                 r_matched_random_metric=float(np.mean(acc["rc"])),
                                 delta_vs_matched=float(np.mean(acc["q"]) - np.mean(acc["rr"])),
                                 delta_vs_rbf=float(np.mean(acc["q"]) - np.mean(acc["rbf"])),
                                 delta_vs_linear=float(np.mean(acc["q"]) - np.mean(acc["lin"])),
                                 delta_vs_matched_random_metric=float(np.mean(acc["q"]) - np.mean(acc["rc"])),
                                 draw_spread_delta=float(np.std(np.array(acc["q"]) - np.array(acc["rr"]),
                                                               ddof=1)))
            if emit:
                print("   band %-16s done (%d/%d)  aliveness %.4f" %
                      ("%s|%g" % (conv, gamma), idx + 1, len(bands_all), aliveness))
    return rows


def q6_reference():
    """The two committed q = 6 reads, KEPT APART because they are not the same object.

    * R391 (smoke_v5_results.json) was run under ONE phase convention (its settings say
      `convention: shifted`) and with a SINGLE target per cell x 40 splits.  Its report carries no
      per-convention column, so a reader that loops over both conventions and reads the same rows twice
      INVENTs an unshifted column -- my first version of this function did exactly that, and the
      duplicate is what made the aliveness comparison (Q2) and the matched-vs-RBF column (D) invalid.
    * R398 (smoke_v12_results.json) is the like-for-like reference: 6 independent draws x 50 splits, both
      conventions built per cell, the same construction this round uses (only the seed stream differs).
    """
    raw = json.loads(io.open(REF_MAP, encoding="utf-8").read())
    shifted_only = {}
    for cell in raw["cells"]:
        alpha = cell["alpha"]
        for row in cell["rows"]:
            g = row["gamma"]
            if g <= 0.0 or g not in GAMMAS:
                continue
            dm = row["delta_vs_matched"]
            shifted_only["shifted|%g|a=%+g" % (g, alpha)] = dict(
                delta_vs_matched=float(dm["quantum"]["mean"]),
                rbf_minus_matched=float(dm["rbf"]["mean"]),
                aliveness=float(row["aliveness"]["mean_offdiag"]))
    r398 = json.loads(io.open(REF_AXISC, encoding="utf-8").read())
    like_for_like = {k: dict(delta_vs_matched=float(v["cells"]["A_registered|t=0.000"]["delta_mean"]),
                             r_matched=float(v["cells"]["A_registered|t=0.000"]["r_rival"]))
                     for k, v in r398["rows"].items()}
    rbf = json.loads(io.open(os.path.join(HERE, "r398_rbf_check_results.json"), encoding="utf-8").read())
    return dict(shifted_only=shifted_only, like_for_like=like_for_like, rbf_instrument=rbf)


def q6_aliveness(q=Q6):
    """C2/Q2's reference, measured by THIS round's own code path: R391's report cannot answer it (one
    convention only) and the aliveness is convention-dependent, so it is measured here per convention."""
    edges = S5.edges_for(EDGE_KIND, q)
    Z = S5.bits_of(q)
    n = len(Z)
    out = {}
    for conv in CONVS:
        for g in GAMMAS:
            Kq = S5.k_quantum(q, edges, Z, g, conv, LAYERS)
            out["%s|%g" % (conv, g)] = float((Kq.sum() - n) / (n * (n - 1)))
    return out


def dumps(rep):
    return json.dumps(rep, indent=1, sort_keys=True, default=float)


def build_once(emit=False):
    return run_map(QUBITS, emit=emit), diag_table(QUBITS)


def main():
    print("=" * 100)
    print("ISSUE #87 -- R401: the q = 8 cell.  Which of the map's claims survive the qubit count?")
    print("=" * 100)
    D8 = diag_table(QUBITS)
    ref = q6_reference()
    alive6 = q6_aliveness()
    print("-- A  diag(W) uniformity at q = 8 (relative deviation from the mean, worst over 12 bands) -------")
    p1 = {}
    for kind in ("cycle", "path", "complete"):
        rel = [v["relative_max_abs_dev"] for k, v in D8.items() if k.startswith(kind + "|")]
        p1[kind] = float(max(rel))
        print("   %-9s %.3e" % (kind, max(rel)))

    rows, _ = build_once(emit=True)
    DET_BANDS = [("shifted", 0.5), ("unshifted", 2.0)]
    rows_det = run_map(QUBITS, only=DET_BANDS)
    det_fields = ("r_quantum", "r_matched", "r_rbf", "delta_vs_matched", "delta_vs_matched_random_metric")
    det_worst, det_n, det_mismatch = 0.0, 0, []
    for key, r in sorted(rows_det.items()):
        for f in det_fields:
            a, b = rows[key][f], r[f]
            det_worst = max(det_worst, abs(a - b))
            det_n += 1
            if a != b:
                det_mismatch.append((key, f, a, b))
    det = (len(det_mismatch) == 0)

    print()
    print("-- B  the map at q = 8 vs the LIKE-FOR-LIKE q = 6 stream (R398: 6 draws x 50 splits, both conv) --")
    print("   %-24s %11s %11s %11s   %s" % ("cell", "q6 (R398)", "q8", "q8 vs rbf", "q8 draw sd"))
    agree, n_cmp, lead = 0, 0, 0
    agree_struct, n_struct, agree_tie, n_tie = 0, 0, 0, 0
    fails = []
    for k in sorted(rows):
        r6 = ref["like_for_like"].get(k)
        r8 = rows[k]
        d8 = r8["delta_vs_matched"]
        if r6 is None:
            continue
        d6 = r6["delta_vs_matched"]
        n_cmp += 1
        same = (d6 > 0) == (d8 > 0)
        agree += int(same)
        if abs(d6) >= 0.1:
            n_struct += 1
            agree_struct += int(same)
        else:
            n_tie += 1
            agree_tie += int(same)
        if not same:
            fails.append((k, d6, d8))
        if d8 < 0:
            lead += 1
        print("   %-24s %+11.4f %+11.4f %+11.4f   %.4f"
              % (k, d6, d8, r8["delta_vs_rbf"], r8["draw_spread_delta"]))
    print("   sign agreement: %d/%d overall -- structure cells (|q6 delta| >= 0.1): %d/%d;  near-zero "
          "cells: %d/%d" % (agree, n_cmp, agree_struct, n_struct, agree_tie, n_tie))
    print("   cells that flipped sign: %s" % ["%s (%+.4f -> %+.4f)" % f for f in fails])
    print("   cells where the quantum kernel LEADS at q = 8: %d of %d" % (lead, n_cmp))

    print()
    print("-- C  aliveness, measured by THIS round's code at both qubit counts (R391's report is one")
    print("      convention only and cannot answer this) --------------------------------------------")
    print("   %-16s %10s %10s   %s" % ("band", "alive q6", "alive q8", "delta q8 (both alphas)"))
    lower, higher, drops = 0, 0, []
    for conv in CONVS:
        for g in GAMMAS:
            a6, a8 = alive6["%s|%g" % (conv, g)], rows["%s|%g|a=+1" % (conv, g)]["aliveness_q8"]
            if a8 < a6:
                lower += 1
            else:
                higher += 1
            drops.append((a6 - a8, "%s|%g" % (conv, g)))
            print("   %-16s %10.4f %10.4f   %s" % ("%s|%g" % (conv, g), a6, a8,
                                                    " ".join("%+.4f" % rows["%s|%g|a=%+g" % (conv, g, x)]
                                                             ["delta_vs_matched"] for x in ALPHAS)))
    print("   aliveness lower at q = 8 in %d of %d bands; higher in %d" % (lower, lower + higher, higher))
    print("   largest drop: %s (%.4f); smallest drop: %s (%.4f)"
          % (max(drops)[1], max(drops)[0], min(drops)[1], min(drops)[0]))

    print()
    print("-- D  the matched rival vs the isotropic baseline --------------------------------------------")
    rbfi = ref["rbf_instrument"]["summary"]
    print("   q = 6, R391 (SHIFTED convention only, single target): R_matched - R_rbf over 12 alpha=+-1 "
          "cells: median %+.4f"
          % float(np.median([-v["rbf_minus_matched"] for k, v in ref["shifted_only"].items()
                             if k.startswith("shifted") and abs(abs(float(k.split("a=")[1])) - 1.0) < 1e-9])))
    print("   q = 6, R398's independent instrument (both conventions, its own seeds): median %+.4f "
          "(range [%+.4f, %+.4f])" % (rbfi["median_of_cell_means"], rbfi["min_cell"], rbfi["max_cell"]))
    dm8 = [rows[k]["r_matched"] - rows[k]["r_rbf"] for k in sorted(rows)]
    print("   q = 8, this round: median %+.4f  mean %+.4f  range [%+.4f, %+.4f]"
          % (np.median(dm8), np.mean(dm8), min(dm8), max(dm8)))

    print()
    print("-- E  the headline under the valid handicap (rival's metric -> trace-matched random PSD) ------")
    still = 0
    for conv, g in MAIN_CLAIM_CELLS_Q6:
        for a in ALPHAS:
            r = rows["%s|%g|a=%+g" % (conv, g, a)]
            ok = r["delta_vs_matched_random_metric"] >= 0.25
            still += int(ok)
            print("   %-24s matched %+8.4f  random %+8.4f  %s" % ("%s|%g|a=%+g" % (conv, g, a),
                                                                  r["delta_vs_matched"],
                                                                  r["delta_vs_matched_random_metric"],
                                                                  ">=0.25" if ok else "below"))
    print("   of the %d main-claim readings: %d still ahead by >= 0.25 with a randomly-matched rival"
          % (len(MAIN_CLAIM_CELLS_Q6) * len(ALPHAS), still))

    rep = dict(round="R401", qubits=QUBITS, layers=LAYERS, graph=EDGE_KIND, n_target=N_TARGET,
               n_splits=N_SPLITS, gammas=list(GAMMAS), alphas=list(ALPHAS), convs=list(CONVS),
               diag_table_q8=D8, diag_uniformity_q8=p1, rows=rows, aliveness_q6=alive6,
               reference_notes=dict(
                   primary="smoke_v12_results.json (R398): 6 draws x 50 splits, both conventions",
                   secondary="smoke_v5_results.json (R391): SHIFTED convention only, single target x 40 "
                             "splits -- read deliberately NOT duplicated into an unshifted column"),
               sign_agreement=dict(overall=[agree, n_cmp], structure=[agree_struct, n_struct],
                                   near_zero=[agree_tie, n_tie], flipped=fails),
               quantum_leads_at_q8=int(lead),
               aliveness=dict(lower=int(lower), higher=int(higher),
                              largest_drop=[max(drops)[1], max(drops)[0]],
                              smallest_drop=[min(drops)[1], min(drops)[0]]),
               matched_minus_rbf=dict(q8=dict(median=float(np.median(dm8)), mean=float(np.mean(dm8)),
                                              min=float(min(dm8)), max=float(max(dm8))),
                                      q6_r398_instrument=rbfi),
               main_claim_cells_still_ahead_random_metric=int(still),
               determinism=dict(identical=bool(det), scope_bands=[list(b) for b in DET_BANDS],
                                fields_compared=list(det_fields), n_values=det_n,
                                max_abs_diff=float(det_worst), n_mismatched=len(det_mismatch)))
    fine = dumps(rep)
    print()
    print("   determinism (scoped rebuild of %s, %d values, max |diff| %.3e): %s"
          % (DET_BANDS, det_n, det_worst, det))
    print("   report sha256 = %s" % hashlib.sha256(fine.encode("utf-8")).hexdigest())
    io.open(OUT, "w", encoding="utf-8").write(fine)
    print("   written to %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
