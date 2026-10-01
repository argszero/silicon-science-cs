#!/usr/bin/env python3
"""Issue #87 -- R399: the SECOND GRAPH.  R398 explained the registered power arm's inertness with a
mechanism that makes a falsifiable prediction; this file tests it on the one graph in this study's reach
that is NOT vertex-transitive -- and it also delivers the stratum extension the map needed.

THE PREDICTION, WRITTEN BEFORE THE RUN (from R398's measured mechanism, not from this round's data):

  R398 measured diag(W) uniform to 8.2e-16 on the cycle graph and concluded that the registered handicap
  axis (A: withhold the off-diagonal) and the diagonal-flattening axis (D) are no-ops BY SYMMETRY: on a
  vertex-transitive graph every qubit carries the same scale, so "flatten the scales" is the identity map
  and A's t = 1 endpoint is c*I, i.e. the ordinary isotropic RBF family.  That mechanism names its own
  boundary.  On a graph that is NOT vertex-transitive the diagonal is NOT uniform, so:

    P1  diag(W) is measurably non-uniform on the PATH graph (endpoint qubits have degree 1, interior
        qubits degree 2), by a margin orders of magnitude above the cycle's floating-point noise;
    P2  axis D stops being the identity map and axis A's t = 1 endpoint stops being c*I, so BOTH axes
        should handicap the rival by materially more than on the cycle.

  Both are read as numbers against the cycle's own R398 values: the draw seed does not depend on the graph,
  so the two runs are paired by construction.

A DEFECT FOUND BY THE PRE-RUN PROBE, and what it changed.  On the path graph, axis D's straightforward
mixture is not even a valid precision matrix: flattening the diagonal of a metric whose diagonal is
[10.4, 30.1, 30.4, 30.4, 30.1, 10.4] drives the smallest eigenvalue to -2.6, so `exp(-s q)` is not a kernel.
The axis therefore needs a REPAIR, and the repair is not cosmetic: it is the same class of defect R393
recorded for the registered flag (a manipulation that leaves the spectrum unfloored is not a mixable
object).  This file applies a minimal, reported repair -- add (|ev_min| + eps) * I when the matrix is not
PD, then rescale so the trace is preserved exactly -- and reports the added amount in units of the mean
diagonal for every (band, axis, level).  Where the added amount is a large fraction, the axis's own content
is partly undone by the repair, and that is stated rather than hidden.

THE HARNESS IS R398's, unchanged except for that repair wrapper.  The wrapper is applied on BOTH graphs, so
  C7 becomes a real control: on the CYCLE graph nothing needs repair, and every one of R398's cells must
  reproduce EXACTLY (compared cell by cell against smoke_v12_results.json, same seeds).  That is what makes
  the path numbers attributable to the graph rather than to the harness.

Also read: the path graph's own t = 0 cells -- the quantum kernel's excess risk against the fully matched
rival, 24 cells -- so every number in the map stops resting on a single graph.

Run:  /usr/bin/python3 smoke_v13.py     (numpy 2.0.2; the daemon interpreter has no numpy)
Reads smoke_v12_results.json (the cycle reference, compared cell by cell); writes smoke_v13_results.json.
"""
import hashlib
import io
import json
import os
import sys

import numpy as np

import smoke_v5 as S5
import smoke_v9 as S9
import smoke_v12 as S12

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v13_results.json")
CYCLE_REF = os.path.join(HERE, "smoke_v12_results.json")

GRAPH = "path"                       # this round's stratum
OTHER_GRAPH = "cycle"                # what axis B's rival models here
AXES = S12.AXES
LEVELS = S12.LEVELS
CONVS = S12.CONVS
GAMMAS = S12.GAMMAS
ALPHAS = S12.ALPHAS
N_TARGET = S12.N_TARGET
N_SPLITS = S12.N_SPLITS

BASE_AXIS_MATRIX = S12.axis_matrix    # R398's, kept untouched so the cycle reproduction stays checkable
REPAIRS = []                          # one record per (band, axis, level) that needed the floor


def mk_context(q, edges, Z, conv, gamma, W):
    """R398's context, with the wrong-graph axis pointed at THIS ROUND's other graph."""
    Wp_full = S5.metric_field(q, S5.edges_for(OTHER_GRAPH, q), Z, gamma, conv, S12.LAYERS)[1]
    rng = np.random.default_rng(987654321 + int(round(1000 * gamma)) + (0 if conv == "shifted" else 7))
    G = rng.normal(size=(q, q))
    Wr = G.T @ G
    perm = rng.permutation(q)
    return dict(W_path=S12.trace_match(Wp_full, W), R_rand=S12.trace_match(Wr, W),
                W_perm=W[np.ix_(perm, perm)], perm=[int(i) for i in perm])


def axis_matrix_v13(axis, t, W, ctx):
    """R398's axis matrix, with a minimal PSD repair that preserves symmetry and trace exactly.

    The repair is recorded, never silent: `added` is compared against the mean diagonal, and `scale` (the
    trace-restoring factor) against 1.  A large `added` means the mixture left the PSD cone and the repair,
    not the axis, is doing part of the work.
    """
    W_t = BASE_AXIS_MATRIX(axis, t, W, ctx)
    W_t = 0.5 * (W_t + W_t.T)
    ev = float(np.linalg.eigvalsh(W_t).min())
    tr_ref = float(np.trace(W))
    rec = dict(axis=axis, t=float(t), min_eig_before=ev, added=0.0, added_rel_mean_diag=0.0, scale=1.0,
               repaired=False, min_eig_after=ev)
    if ev <= 0.0:
        c = abs(ev) + 1e-9
        W_r = W_t + c * np.eye(W.shape[0])
        tr_r = float(np.trace(W_r))
        s = tr_ref / tr_r
        W_t = s * W_r
        rec.update(added=float(c), added_rel_mean_diag=float(c / (tr_ref / W.shape[0])), scale=float(s),
                   repaired=True, min_eig_after=float(np.linalg.eigvalsh(W_t).min()))
        REPAIRS.append(rec)
    return W_t


def build_graph(graph, other, block_seed_shift=0, emit=False):
    """R398's build loop, unchanged, with the repair wrapper active and the repair log returned."""
    global OTHER_GRAPH
    OTHER_GRAPH = other
    q = S12.QUBITS
    edges = S5.edges_for(graph, q)
    Z = S5.bits_of(q)
    S12.axis_matrix = axis_matrix_v13
    S12.mk_context = mk_context
    metrics = {c: {g: S5.metric_field(q, edges, Z, g, c, S12.LAYERS) for g in GAMMAS} for c in CONVS}
    rows, ident, repairs = {}, {"c1_max_abs_kernel_diff_at_t0": 0.0}, []
    idx = 0
    for c in CONVS:
        for g in GAMMAS:
            REPAIRS.clear()
            r, idb = S12.run_band(q, edges, Z, metrics[c], c, g, idx)
            rows.update(r)
            seen = set()
            for rec in REPAIRS:
                # the C2 control re-derives axis D at t = 1 through the same wrapper, so the same matrix is
                # recorded twice; dedupe on the identical record (it is the same object, not a second event)
                key = (rec["axis"], round(rec["t"], 9), round(rec["min_eig_before"], 12))
                if key in seen:
                    continue
                seen.add(key)
                repairs.append(dict(band="%s|%g" % (c, g), **rec))
            ident["c1_max_abs_kernel_diff_at_t0"] = max(ident["c1_max_abs_kernel_diff_at_t0"],
                                                      idb["c1_max_abs_kernel_diff_at_t0"])
            ident["c2_axis_t1_exact"] = idb["c2_axis_t1_exact"]
            ident["c3_permutation_is_nontrivial"] = idb["c3_permutation_is_nontrivial"]
            idx += 1
            if emit:
                print("   band %-16s done (%d/%d)  repairs this band: %d"
                      % ("%s|%g" % (c, g), idx, len(CONVS) * len(GAMMAS), len(repairs)))
    c5 = all(abs(row["cells"]["F_identity|t=1.000"]["dr_mean"]) == 0.0 for row in rows.values())
    audit = dict(round="R399", graph=graph, other_graph=other, n_target=N_TARGET, n_splits=N_SPLITS,
                 levels=list(LEVELS), alphas=list(ALPHAS), axes=list(AXES), gammas=list(GAMMAS),
                 convs=list(CONVS),
                 controls=dict(c1_identity_max_abs_kernel_diff=ident["c1_max_abs_kernel_diff_at_t0"],
                               c2_axis_t1_exact=ident["c2_axis_t1_exact"],
                               c3_permutation_is_nontrivial=ident["c3_permutation_is_nontrivial"],
                               c5_negative_axis_exactly_zero=bool(c5)),
                 psd_repairs=repairs, verdicts=S12.verdicts(rows), rows=rows)
    return audit


def diag_table(q, Z):
    """The mechanism's own table: is diag(W) uniform, per graph, per band?  This is P1."""
    out = {}
    for kind in ("cycle", "path", "complete"):
        edges = S5.edges_for(kind, q)
        for c in CONVS:
            for g in GAMMAS:
                _, W, spread = S5.metric_field(q, edges, Z, g, c, S12.LAYERS)
                d = np.diag(W)
                out["%s|%s|%g" % (kind, c, g)] = dict(
                    diag=[float(x) for x in d], mean=float(d.mean()),
                    max_abs_dev=float(np.max(np.abs(d - d.mean()))),
                    relative_max_abs_dev=float(np.max(np.abs(d - d.mean())) / abs(float(d.mean()))),
                    spread=float(spread))
    return out


def compare_to_reference(rows, ref_rows):
    """C7: cell-by-cell comparison against R398's committed cycle numbers."""
    worst, n, mismatched = 0.0, 0, []
    for k in sorted(ref_rows):
        for ck in sorted(ref_rows[k]["cells"]):
            a = ref_rows[k]["cells"][ck]["delta_mean"]
            b = rows[k]["cells"][ck]["delta_mean"]
            worst = max(worst, abs(a - b))
            n += 1
            if a != b:
                mismatched.append((k, ck, a, b))
    return dict(n_cells_compared=n, max_abs_delta_difference=float(worst),
                n_exact=int(n - len(mismatched)), n_mismatched=len(mismatched),
                mismatched_repair_affected=sum(1 for m in mismatched if m[1].startswith("D_flat")),
                examples=mismatched[:6])


def dumps(rep):
    return json.dumps(rep, indent=1, sort_keys=True, default=float)


def main():
    print("=" * 100)
    print("ISSUE #87 -- R399: the second graph.  Does the path graph's non-uniform diagonal wake the")
    print("             registered handicap axis up, as R398's mechanism predicts?")
    print("=" * 100)
    q = S12.QUBITS
    Z = S5.bits_of(q)
    dtab = diag_table(q, Z)
    print("-- P1: is diag(W) uniform?  (relative deviation from the mean, max over the 12 bands) ---------")
    p1 = {}
    for kind in ("cycle", "path", "complete"):
        rel = [v["relative_max_abs_dev"] for k, v in dtab.items() if k.startswith(kind + "|")]
        p1[kind] = float(max(rel))
        print("   %-9s max over bands: %.3e" % (kind, max(rel)))
    print("   path / cycle = %.3e  (P1 predicts orders of magnitude)"
          % (p1["path"] / max(p1["cycle"], 1e-300)))

    print()
    print("-- C7 first: the CYCLE graph through THIS harness must reproduce R398's committed cells ------")
    cyc_ref = json.loads(io.open(CYCLE_REF, encoding="utf-8").read())
    audit_cycle = build_graph("cycle", "path", emit=False)
    c7 = compare_to_reference(audit_cycle["rows"], cyc_ref["rows"])
    print("   cells compared %d, exact %d, mismatched %d (of which axis-D: %d), max |delta diff| %.3e"
          % (c7["n_cells_compared"], c7["n_exact"], c7["n_mismatched"],
             c7["mismatched_repair_affected"], c7["max_abs_delta_difference"]))
    print("   repairs needed on the cycle: %d" % len(audit_cycle["psd_repairs"]))

    print()
    print("-- the PATH graph (this round's stratum) ------------------------------------------------------")
    audit_path = build_graph("path", "cycle", emit=True)
    audit_path2 = build_graph("path", "cycle", emit=False)
    det = bool(dumps(audit_path["rows"]) == dumps(audit_path2["rows"]))
    sizes = sorted({r["added_rel_mean_diag"] for r in audit_path["psd_repairs"] if r["repaired"]})
    print("   PSD repairs on the path graph: %d records; added (rel. mean diagonal) range %s"
          % (len(audit_path["psd_repairs"]),
             ("[%.3f, %.3f]" % (sizes[0], sizes[-1])) if sizes else "none"))
    print("   axes repaired: %s" % sorted({r["axis"] for r in audit_path["psd_repairs"] if r["repaired"]}))
    print("   C1 %.3e  C3 %s  C5 %s  C6 %s"
          % (audit_path["controls"]["c1_identity_max_abs_kernel_diff"],
             audit_path["controls"]["c3_permutation_is_nontrivial"],
             audit_path["controls"]["c5_negative_axis_exactly_zero"], det))

    print()
    print("-- P2: what the handicap does to the rival at t = 1, path vs cycle (median dR, one variance) --")
    p2 = {}
    print("   %-18s %24s %24s" % ("axis", "cycle (R398)", "path (this round)"))
    for ax in AXES:
        v, c = audit_path["verdicts"][ax], audit_cycle["verdicts"][ax]
        p2[ax] = dict(cycle_median=c["dr_median"], path_median=v["dr_median"], cycle_valid=c["valid"],
                      path_valid=v["valid"], path_reversed=v["reversed_"], path_mixed=v["mixed"])
        print("   %-18s  %+9.4f  %2d/%2d/%-2d     %+9.4f  %2d/%2d/%-2d"
              % (ax, c["dr_median"], c["valid"], c["reversed_"], c["mixed"],
                 v["dr_median"], v["valid"], v["reversed_"], v["mixed"]))
    print("   (valid/reversed/mixed over 24 cells; 'valid' = all six draws agree the rival got worse)")
    print()
    print("-- the path stratum's own cells at t = 0 (delta = R_quantum - R_matched_rival) ----------------")
    for k in sorted(audit_path["rows"]):
        row = audit_path["rows"][k]
        c = row["cells"]["A_registered|t=0.000"]
        print("   %-26s delta %+0.4f   R_quantum %.4f" % (k, c["delta_mean"], row["r_quantum"]))
    print()
    rep = dict(round="R399", graph=GRAPH, other_graph=OTHER_GRAPH, p1_diag_uniformity=p1,
               p2_axis_effect=p2, c7_cycle_reproduction=c7, cycle_audit=audit_cycle,
               path_audit=audit_path, path_determinism=dumps(audit_path["rows"]) == dumps(audit_path2["rows"]),
               diag_table=dtab)
    fine = dumps(rep)
    print("   report sha256 = %s" % hashlib.sha256(fine.encode("utf-8")).hexdigest())
    io.open(OUT, "w", encoding="utf-8").write(fine)
    print("   written to %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
