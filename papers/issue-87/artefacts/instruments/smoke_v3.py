"""R389 smoke test, part 4 -- the closed form, verified after the regression's own factor-2 defect.

Three defects were found and each is recorded where it was found rather than repaired in place:
`smoke_v0.py` returned a normalisation its caller dropped (K(x,x) = N^2 instead of 1); `smoke_v1.py`
regressed against the signless Laplacian (D + A) where the structure is the opposite sign; and THIS
file's predecessor read a symmetric matrix out of a design whose monomials are `d_i d_j` with `i <= j`
and then placed each coefficient in BOTH `W[i,j]` and `W[j,i]` -- which doubles every off-diagonal
(the reconstruction of `d^T W d = sum_ii W_ii d_i^2 + 2 sum_{i<j} W_ij d_i d_j` puts `c_ij / 2` in the
matrix, not `c_ij`).  The sign is unmistakable in the numbers: with the doubled read, the off-edges
were 36.78 against a diagonal of 28.91, and the closed form says 18.39 -- EXACTLY half.

With the reconstruction fixed, the meter runs both ways: a synthetic response `d^T W_closed d` returns
W_closed, the exact `2 Var(dtheta)` returns it, and the SIMULATOR's `-2 log K` returns it.  So:

    the ZZ map's small-bandwidth metric has an exact closed form,  W = 2 Cov_z(f),
    f_i(z) = 2 z_i (1 - pi * m_i(z)),  m_i(z) = number of excited neighbours of i,

computable by enumerating the 2^q basis states -- no simulation, no fit.  Its support is NOT the edge
set (two vertices at graph distance 2 are correlated through shared neighbours), so a metric-matched
classical rival must carry the whole covariance, not the graph Laplacian.  This is the instrument the
registered study needs, and it is now verified to the fit's precision.

Run:  /usr/bin/python3 smoke_v3.py
Writes smoke_v3_results.json beside this file.
"""
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v0 as S
import smoke_v2 as V

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v3_results.json")


def fit_W_fixed(q, edges, gamma, convention, layers=1, m_pairs=800, seed=20260920):
    """The metric, read with the symmetric reconstruction CORRECT: W[i,j] = W[j,i] = c_ij / 2."""
    rng = np.random.default_rng(seed)
    lin = [(i,) for i in range(q)]
    quad = [(i, j) for i in range(q) for j in range(i, q)]
    A = np.zeros((m_pairs, len(lin) + len(quad)))
    y = np.zeros(m_pairs)
    for t in range(m_pairs):
        base = gamma * rng.uniform(-1.0, 1.0, q)
        d = (gamma / 8.0) * rng.uniform(-1.0, 1.0, q)
        k = S.kernel(q, edges, base, base + d, convention, layers)
        y[t] = -2.0 * math.log(max(k, 1e-300))
        for c, (i,) in enumerate(lin):
            A[t, c] = d[i]
        for c, (i, j) in enumerate(quad):
            A[t, len(lin) + c] = d[i] * d[j]
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    W = np.zeros((q, q))
    for c, (i, j) in enumerate(quad):
        v = sol[len(lin) + c] / (1.0 if i == j else 2.0)
        W[i, j] = v
        W[j, i] = v
    return W, sol[:len(lin)]


def rel_dev(A, B):
    scale = float(np.mean(np.abs(np.diag(B))))
    return float(np.max(np.abs(A - B)) / scale)


def anisotropy(W, edges):
    """max |off-diagonal| over the DIAGONAL scale -- with the reconstruction fixed."""
    q = W.shape[0]
    scale = float(np.mean(np.abs(np.diag(W))))
    edgeset = {(min(i, j), max(i, j)) for i, j in edges}
    on = [abs(W[i, j]) for i in range(q) for j in range(i + 1, q) if (i, j) in edgeset]
    off = [abs(W[i, j]) for i in range(q) for j in range(i + 1, q) if (i, j) not in edgeset]
    return {"scale": scale, "max_on_edge": max(on) if on else 0.0,
            "max_off_edge": max(off) if off else 0.0,
            "anisotropy_on_edge": (max(on) / scale) if on else 0.0,
            "anisotropy_off_edge": (max(off) / scale) if off else 0.0,
            "off_edge_over_on_edge": (max(off) / max(on)) if (on and off and max(on)) else 0.0}


def row(graph, q, edges, gamma=0.05, convention="shifted", layers=1):
    Wfit, ell = fit_W_fixed(q, edges, gamma, convention, layers)
    if convention == "shifted":
        Wpred = V.cov2(V.f_vectors(q, edges))
    else:
        Wpred = V.cov2(V.f_vectors_unshifted(q, edges, np.zeros(q)))
    Wb, _ = fit_W_fixed(q, edges, gamma, convention, layers, seed=99991)
    an = anisotropy(Wfit, edges)
    return {"graph": graph, "gamma": gamma, "convention": convention, "layers": layers,
            "max_rel_deviation_fit_vs_closed_form": rel_dev(Wfit, Wpred),
            "max_rel_deviation_between_two_disjoint_samples": rel_dev(Wb, Wfit),
            "linear_block_norm": float(np.linalg.norm(ell)),
            **an, "W_fit": Wfit.tolist(), "W_pred": Wpred.tolist()}


def build_report():
    q = 6
    graphs = (("path", S.graph_path(q)), ("cycle", S.graph_cycle(q)),
              ("complete", S.graph_complete(q)), ("empty", S.graph_empty(q)))
    rows = [row(g, q, e, 0.05, "shifted") for g, e in graphs]
    rows += [row(g, q, e, 0.05, "unshifted") for g, e in graphs]
    depth = [row("cycle", q, S.graph_cycle(q), 0.05, "shifted", L) for L in (2, 3)]
    bw = [row("cycle", q, S.graph_cycle(q), g, "shifted") for g in (0.01, 0.02, 0.05)]
    return {"q": q, "rows": rows, "depth_rows": depth, "bandwidth_rows": bw,
            "simulator_controls": S.kernel_matrix_controls(q, S.graph_cycle(q), 0.05),
            "synthetic_recovery_control": _synthetic_control(q, S.graph_cycle(q))}


def _synthetic_control(q, edges):
    """A response built FROM the closed form must be recovered exactly by the same regression.

    This is the control for the factor-2 defect: if the regression cannot recover a matrix it was
    handed, every "the fit matches the closed form" statement is a statement about the regression.
    """
    Wt = V.cov2(V.f_vectors(q, edges))
    rng = np.random.default_rng(20260920)
    lin = [(i,) for i in range(q)]
    quad = [(i, j) for i in range(q) for j in range(i, q)]
    A = np.zeros((400, len(lin) + len(quad)))
    y = np.zeros(400)
    for t in range(400):
        d = (0.05 / 8.0) * rng.uniform(-1.0, 1.0, q)
        y[t] = d @ Wt @ d
        for c, (i,) in enumerate(lin):
            A[t, c] = d[i]
        for c, (i, j) in enumerate(quad):
            A[t, len(lin) + c] = d[i] * d[j]
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    W = np.zeros((q, q))
    for c, (i, j) in enumerate(quad):
        v = sol[len(lin) + c] / (1.0 if i == j else 2.0)
        W[i, j] = v
        W[j, i] = v
    return {"max_rel_deviation_synthetic_response_recovered": rel_dev(W, Wt)}


def main():
    rep = build_report()
    text = json.dumps(rep, indent=2, sort_keys=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print("determinism: identical on a second build = %s"
          % (text == json.dumps(build_report(), indent=2, sort_keys=True)))
    print("simulator controls : %s" % json.dumps(rep["simulator_controls"], sort_keys=True))
    print("synthetic control  : %s" % json.dumps(rep["synthetic_recovery_control"], sort_keys=True))
    print("\n%-9s %-10s %5s %11s %10s %10s %10s %10s %11s" % (
        "graph", "conv", "L", "fit/closed", "samp-samp", "on-edge", "off-edge", "off/on", "anisotropy"))
    for r in rep["rows"] + rep["depth_rows"] + rep["bandwidth_rows"]:
        print("%-9s %-10s %5d %11.2e %10.2e %10.4f %10.4f %10.4f %11.4f"
              % (r["graph"], r["convention"], r["layers"],
                 r["max_rel_deviation_fit_vs_closed_form"],
                 r["max_rel_deviation_between_two_disjoint_samples"],
                 r["max_on_edge"], r["max_off_edge"], r["off_edge_over_on_edge"],
                 r["anisotropy_on_edge"]))
    print("\nwrote %s" % OUT)

    def get(graph, conv, L=1, gamma=0.05):
        return next(r for r in rep["rows"] + rep["depth_rows"] + rep["bandwidth_rows"]
                    if (r["graph"], r["convention"], r["layers"], r["gamma"]) == (graph, conv, L, gamma))

    ent, uns, emp = get("cycle", "shifted"), get("cycle", "unshifted"), get("empty", "shifted")
    claims = {
        "C1 the regression recovers a matrix it was handed (factor-2 fixed)":
            rep["synthetic_recovery_control"]["max_rel_deviation_synthetic_response_recovered"] < 1e-9,
        "C2 exact simulator (K(x,x)=1, symmetric, PSD)":
            rep["simulator_controls"]["PSD_within_1e-10"]
            and rep["simulator_controls"]["max_abs_K(x,x)-1"] < 1e-12,
        "C3 shifted: fitted metric == closed form 2Cov(f) to <1% of scale, every graph":
            all(get(g, "shifted")["max_rel_deviation_fit_vs_closed_form"] < 1e-2
                for g in ("path", "cycle", "complete", "empty")),
        "C4 no-edge control: metric is exactly 2 I":
            emp["max_rel_deviation_fit_vs_closed_form"] < 1e-5,
        "C5 the closed form is NOT edge-supported (off-edge reaches >10% of the on-edge value)":
            ent["off_edge_over_on_edge"] > 0.1,
        "C6 shifted: off-edge/anisotropy survives, i.e. the metric is a property of the graph":
            ent["anisotropy_on_edge"] > 0.5 and ent["max_rel_deviation_between_two_disjoint_samples"] < 1e-2,
        "C7 unshifted: anisotropy suppressed >=10x and less stable than shifted":
            uns["anisotropy_on_edge"] < 0.1 * ent["anisotropy_on_edge"]
            and uns["max_rel_deviation_between_two_disjoint_samples"]
            > ent["max_rel_deviation_between_two_disjoint_samples"],
        "C8 the closed form still holds at depth L=2 (deviation < 5% of scale)":
            get("cycle", "shifted", 2)["max_rel_deviation_fit_vs_closed_form"] < 5e-2,
    }
    print("\nSMOKE VERDICT (v3)")
    for k, v in claims.items():
        print("   %-88s %s" % (k, "PASS" if v else "FAIL"))
    print("   ALL PASS" if all(claims.values()) else "   SOME FAILED (each is read off the table above)")
    return 0 if all(claims.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
