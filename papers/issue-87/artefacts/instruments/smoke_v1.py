"""R389 smoke test, part 2 -- the metric read correctly.

The first run of `smoke_v0.py` (kept beside this file as `smoke_v0.py`, unchanged) measured three
things and got one of them structurally wrong, in a way that is itself a finding:

* it fitted `-2 log K = d^T W d` with **quadratic monomials only**, and the SHIFTED convention does not
  have that form: its pair phase (pi - x_i)(pi - x_j) carries an O(bandwidth) **linear** term in the
  deviation, so the design was missing the monomials that carry the largest part of the response, and
  the quadratic block absorbed them as a spurious anisotropic term with the wrong sign;
* with the linear monomials restored, the anisotropy has the structure of the graph **Laplacian**
  (D - A, negative off-diagonals on the edges), not of the signless Laplacian (D + A) the first run
  regressed against -- so the first run's "support MISS" was a defect of the regression basis, not of
  the simulator;
* the UNSHIFTED convention is isotropic to within 0.6% at bandwidth 0.05, and the ratio between the two
  conventions' anisotropy is ~O(1/bandwidth^2) -- the convention claim of arXiv:2608.29422, measured.

This file re-reads the same simulator with the corrected instrument.  It imports `smoke_v0` (the
simulator and the kernel, unchanged) and re-fits.  Nothing in `smoke_v0.py` is edited: the first run's
output stays as the record of what the first instrument said.

Run:  /usr/bin/python3 smoke_v1.py
Writes smoke_v1_results.json beside this file.
"""
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v0 as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v1_results.json")


def fit_metric_full(q, edges, gamma, convention, layers=1, m_pairs=800, seed=20260920):
    """Fit -2 log K = 2 l^T d + d^T W d (linear AND quadratic), then read the metric W.

    The linear block is not decoration: it is the term the first instrument omitted, and its size is
    what distinguishes the two conventions at leading order.  Columns are d_i then d_i d_j (i <= j);
    the response is -2 log K (K(x,x) = 1 exactly, so there is no constant term).
    """
    rng = np.random.default_rng(seed)
    lin = [(i,) for i in range(q)]
    quad = [(i, j) for i in range(q) for j in range(i, q)]
    A = np.zeros((m_pairs, len(lin) + len(quad)))
    y = np.zeros(m_pairs)
    kk = np.zeros(m_pairs)
    ds = np.zeros((m_pairs, q))
    for t in range(m_pairs):
        base = gamma * rng.uniform(-1.0, 1.0, q)
        d = (gamma / 8.0) * rng.uniform(-1.0, 1.0, q)
        ds[t] = d
        k = S.kernel(q, edges, base, base + d, convention, layers)
        kk[t] = k
        y[t] = -2.0 * math.log(max(k, 1e-300))
        for c, (i,) in enumerate(lin):
            A[t, c] = d[i]
        for c, (i, j) in enumerate(quad):
            A[t, len(lin) + c] = d[i] * d[j]
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    W = np.zeros((q, q))
    for c, (i, j) in enumerate(quad):
        W[i, j] = sol[len(lin) + c]
        W[j, i] = sol[len(lin) + c]
    ell = sol[:len(lin)]
    recon = np.exp(-0.5 * (A @ sol))
    rel = float(np.max(np.abs(recon - kk) / np.maximum(kk, 1e-12)))
    edgeset = {(min(i, j), max(i, j)) for i, j in edges}
    offdiag = {(i, j): W[i, j] for i in range(q) for j in range(i + 1, q)}
    on = [abs(v) for e, v in offdiag.items() if e in edgeset]
    off = [abs(v) for e, v in offdiag.items() if e not in edgeset]
    diag = [abs(W[i, i]) for i in range(q)]
    # two regressions of W on a declared basis, reported with their residuals
    basis = {}
    Qp = S.signless_laplacian(q, edges)                      # D + A
    Ql = np.diag([d for d in S.degrees(q, edges)]) - _adj(q, edges)  # D - A
    for name, M in (("I_and_D+A", [np.eye(q), Qp]), ("I_and_D-A", [np.eye(q), Ql])):
        design = np.array([[1.0 if m is None else 0.0 for m in ()]] * 0)
        rows = [(i, j) for i in range(q) for j in range(i, q)]
        Dm = np.zeros((len(rows), 2))
        target = np.zeros(len(rows))
        for c, (i, j) in enumerate(rows):
            Dm[c, 0] = 1.0 if i == j else 0.0
            Dm[c, 1] = M[1][i, j]
            target[c] = W[i, j]
        coef, *_ = np.linalg.lstsq(Dm, target, rcond=None)
        basis[name] = {"coef": [float(x) for x in coef],
                       "max_abs_residual": float(np.max(np.abs(Dm @ coef - target)))}
    return {
        "q": q, "graph_edges": len(edges), "convention": convention, "layers": layers, "gamma": gamma,
        "linear_block_norm": float(np.linalg.norm(ell)),
        "linear_over_quadratic": float(np.linalg.norm(ell) / (np.linalg.norm(W) or 1.0)),
        "offdiag_on_edges_max_abs": float(max(on)) if on else 0.0,
        "offdiag_off_edges_max_abs": float(max(off)) if off else 0.0,
        "offdiag_on_edges_sign": sorted({int(np.sign(v)) for e, v in offdiag.items() if e in edgeset}),
        "diag_mean_abs": float(np.mean(diag)),
        "anisotropy_ratio": float(max(on) / np.mean(diag)) if on else 0.0,
        "basis_fits": basis,
        "max_relative_error_reconstructed_kernel": rel,
        "K_range": [float(kk.min()), float(kk.max())],
    }


def _adj(q, edges):
    A = np.zeros((q, q))
    for i, j in edges:
        A[i, j] = 1.0
        A[j, i] = 1.0
    return A


def build_report():
    q = 6
    graphs = {"path": S.graph_path(q), "cycle": S.graph_cycle(q),
              "complete": S.graph_complete(q), "empty": S.graph_empty(q)}
    rows = [dict(graph=g, **fit_metric_full(q, e, 0.05, c))
            for g, e in graphs.items() for c in ("shifted", "unshifted")]
    depth = [dict(graph="cycle", **fit_metric_full(q, S.graph_cycle(q), 0.05, "shifted", L))
             for L in (1, 2, 3)]
    bw = [dict(graph="cycle", **fit_metric_full(q, S.graph_cycle(q), g, "shifted"))
          for g in (0.02, 0.05, 0.15)]
    bwu = [dict(graph="cycle", **fit_metric_full(q, S.graph_cycle(q), g, "unshifted"))
           for g in (0.02, 0.05, 0.15)]
    return {"q": q, "rows": rows, "depth_rows": depth, "bandwidth_shifted": bw,
            "bandwidth_unshifted": bwu,
            "simulator_controls": S.kernel_matrix_controls(q, S.graph_cycle(q), 0.05)}


def main():
    rep = build_report()
    text = json.dumps(rep, indent=2, sort_keys=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print("determinism: identical on a second build = %s"
          % (text == json.dumps(build_report(), indent=2, sort_keys=True)))
    print("\nsimulator controls: %s" % json.dumps(rep["simulator_controls"], sort_keys=True))
    print("\n%-9s %-10s %6s %9s %11s %11s %8s %6s %10s" % (
        "graph", "conv", "layers", "gamma", "|lin|", "on-edge", "off-edge", "sign", "aniso"))
    for r in rep["rows"] + rep["depth_rows"] + rep["bandwidth_shifted"] + rep["bandwidth_unshifted"]:
        print("%-9s %-10s %6d %9.3f %11.4f %11.4f %8.2e %6s %10.4f" % (
            r["graph"], r["convention"], r["layers"], r["gamma"], r["linear_block_norm"],
            r["offdiag_on_edges_max_abs"], r["offdiag_off_edges_max_abs"], r["offdiag_on_edges_sign"],
            r["anisotropy_ratio"]))
    print("\nbasis regressions (W on a I + b (D +- A)); residual in the same units as W:")
    for r in rep["rows"]:
        print("   %-9s %-10s  I+D+A coef=%-28s resid=%.3e | I+D-A coef=%-28s resid=%.3e  relerr=%.2e"
              % (r["graph"], r["convention"],
                 "[%.4f, %.4f]" % tuple(r["basis_fits"]["I_and_D+A"]["coef"]),
                 r["basis_fits"]["I_and_D+A"]["max_abs_residual"],
                 "[%.4f, %.4f]" % tuple(r["basis_fits"]["I_and_D-A"]["coef"]),
                 r["basis_fits"]["I_and_D-A"]["max_abs_residual"],
                 r["max_relative_error_reconstructed_kernel"]))
    print("\nconvention contrast, cycle graph, anisotropy = max|off-diag on an edge| / mean|diag|:")
    for a, b in zip(rep["bandwidth_shifted"], rep["bandwidth_unshifted"]):
        print("   gamma=%-6.3f shifted=%.6f  unshifted=%.6f  ratio=%.1f"
              % (a["gamma"], a["anisotropy_ratio"], b["anisotropy_ratio"],
                 a["anisotropy_ratio"] / (b["anisotropy_ratio"] or 1e-30)))
    print("\nwrote %s" % OUT)

    def get(graph, conv, L=1, gamma=0.05):
        for r in rep["rows"] + rep["depth_rows"] + rep["bandwidth_shifted"] + rep["bandwidth_unshifted"]:
            if (r["graph"], r["convention"], r["layers"], r["gamma"]) == (graph, conv, L, gamma):
                return r
        raise KeyError((graph, conv, L, gamma))

    ent = get("cycle", "shifted")
    uns = get("cycle", "unshifted")
    emp = get("empty", "shifted")
    claims = {
        "C1 exact simulator (K(x,x)=1, symmetric, PSD)":
            rep["simulator_controls"]["PSD_within_1e-10"]
            and rep["simulator_controls"]["max_abs_K(x,x)-1"] < 1e-12,
        "C2 the metric form holds at gamma=0.05 (relerr < 1e-3), all four graphs":
            all(r["max_relative_error_reconstructed_kernel"] < 1e-3 for r in rep["rows"]),
        "C3 shifted: off-diagonal support IS the edge set (non-edges < 1e-6 of the diagonal)":
            ent["offdiag_off_edges_max_abs"] < 1e-6 * ent["diag_mean_abs"]
            and ent["offdiag_on_edges_max_abs"] > 1e-2 * ent["diag_mean_abs"],
        "C4 shifted: the on-edge coefficient is NEGATIVE (Laplacian structure, not signless)":
            ent["offdiag_on_edges_sign"] == [-1],
        "C5 unshifted: anisotropy suppressed (ratio < 1e-2) and convention-blind at no edges":
            uns["anisotropy_ratio"] < 1e-2 and emp["anisotropy_ratio"] == 0.0,
        "C6 the shifted convention has an O(bandwidth) LINEAR term, the unshifted does not":
            ent["linear_over_quadratic"] > 0.1 and uns["linear_over_quadratic"] < 0.01,
        "C7 depth: the on-edge structure survives L=2,3 (sign preserved)":
            all(r["offdiag_on_edges_sign"] == [-1] and r["offdiag_off_edges_max_abs"] < 1e-6
                for r in rep["depth_rows"]),
        "C8 the Laplacian basis fits W better than the signless one (shifted)":
            ent["basis_fits"]["I_and_D-A"]["max_abs_residual"]
            < 0.5 * ent["basis_fits"]["I_and_D+A"]["max_abs_residual"],
    }
    print("\nSMOKE VERDICT (v1)")
    for k, v in claims.items():
        print("   %-86s %s" % (k, "PASS" if v else "FAIL"))
    print("   ALL PASS" if all(claims.values()) else "   SOME FAILED")
    return 0 if all(claims.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
