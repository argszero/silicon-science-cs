"""R389 smoke test, part 3 -- the metric DERIVED, not just fitted.

What parts 1 and 2 established, in order:

* `smoke_v0.py`  built the exact simulator and read the metric with a quadratic-only design; it found
  * K(x,x) != 1 (its Hadamard normalisation was returned, not applied -- the whole report was off by
  a constant exp(2 log N), which a design with no intercept turns into spurious coefficients), and
  * the fitted quadratic block did not match any declared basis.  Both are defects OF THE INSTRUMENT,
  recorded rather than repaired in place: `smoke_v0.py` is unchanged.
* `smoke_v1.py`  added the linear block and two bases.  It measured a huge on-edge off-diagonal that
  was NOT confined to the edge set, and mixed signs -- so the "the metric's support is the edge set"
  reading was wrong too.  It also confirmed the convention contrast (shifted anisotropy ~1.27,
  unshifted ~0.009 at bandwidth 0.05).
* a one-off measurement (in the session record) showed -2 log K = 2 Var(theta(x) - theta(x')) to five
  to six significant digits at this bandwidth.  That identity is the whole instrument: it turns the
  metric into the covariance of a computable random vector, and the vector is READ OFF the map.

THE DERIVATION, which this file tests.  For the ZZ map with pair phase 2 g(x_i, x_j),

    theta(x, z) = sum_i 2 x_i z_i + sum_edges 2 g(x_i, x_j) z_i z_j,

and for the SHIFTED convention g = (pi - x_i)(pi - x_j), whose difference between two inputs is
- pi (d_i + d_j) + O(x^2).  So, to leading order in the deviation,

    dtheta = sum_i d_i * f_i(z),     f_i(z) = 2 z_i (1 - pi * m_i(z)),   m_i(z) = sum_{j in N(i)} z_j,

and therefore

    -2 log K  =  2 Var(dtheta)  =  d^T W d,      W = 2 Cov_z(f).

**W has an exact closed form as a function of the entanglement graph alone** -- no simulation, no fit --
and it is NOT confined to the edge set: two non-adjacent vertices are correlated through the shared
neighbours in m_i.  That is the reading the first two parts could not reach by fitting.

For the UNSHIFTED convention g = x_i x_j, the same expansion gives

    f_i(z) = 2 z_i (1 - (1/2) sum_{j in N(i)} x_j),

which depends on the EVALUATION POINT x, not only on the graph: the "metric" there is a random
quantity of O(bandwidth) scale rather than a property of the map.  That is a measurable difference
between the conventions, and it is measured here as well.

Run:  /usr/bin/python3 smoke_v2.py
Writes smoke_v2_results.json beside this file.
"""
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v0 as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v2_results.json")
PI = math.pi


def f_vectors(q, edges):
    """f(z) for every basis state z, for the shifted convention -- the vector the map implies.

    For the UNSHIFTED convention see `f_vectors_unshifted`, which needs the evaluation point.
    """
    n = 1 << q
    bits = np.array([[(k >> i) & 1 for i in range(q)] for k in range(n)], dtype=float)
    f = np.zeros((n, q))
    for k in range(n):
        for i in range(q):
            m_i = sum(bits[k][j] for j in [b for a, b in edges if a == i] +
                      [a for a, b in edges if b == i])
            f[k, i] = 2.0 * bits[k][i] * (1.0 - PI * m_i)
    return f


def f_vectors_unshifted(q, edges, x):
    """f(z) for the unshifted convention at evaluation point x -- point-dependent by construction."""
    n = 1 << q
    bits = np.array([[(k >> i) & 1 for i in range(q)] for k in range(n)], dtype=float)
    f = np.zeros((n, q))
    for k in range(n):
        for i in range(q):
            nb = [j for a, j in edges if a == i] + [a for a, b in edges if b == i]
            f[k, i] = 2.0 * bits[k][i] * (1.0 - 0.5 * sum(x[j] for j in nb))
    return f


def cov2(f):
    """2 Cov_z(f) over the uniform distribution on z -- the predicted metric."""
    fc = f - f.mean(axis=0, keepdims=True)
    return 2.0 * (fc.T @ fc) / f.shape[0]


def fit_W(q, edges, gamma, convention, layers=1, m_pairs=800, seed=20260920):
    """The fitted metric (linear + quadratic blocks), as in smoke_v1 -- returned as a matrix."""
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
        W[i, j] = sol[len(lin) + c]
        W[j, i] = sol[len(lin) + c]
    return W


def rel_dev(A, B):
    """max |A - B| relative to the mean |diagonal| of B -- the scale a reader reads."""
    scale = float(np.mean(np.abs(np.diag(B))))
    return float(np.max(np.abs(A - B)) / scale), scale


def row(graph, q, edges, gamma=0.05, convention="shifted", layers=1):
    Wfit = fit_W(q, edges, gamma, convention, layers)
    if convention == "shifted":
        Wpred = cov2(f_vectors(q, edges))
    else:
        Wpred = cov2(f_vectors_unshifted(q, edges, np.zeros(q)))
    dev, scale = rel_dev(Wfit, Wpred)
    Wfit_b = fit_W(q, edges, gamma, convention, layers, seed=99991)  # a disjoint sample
    stab, _ = rel_dev(Wfit_b, Wfit)
    return {
        "graph": graph, "gamma": gamma, "convention": convention, "layers": layers,
        "scale_of_W_pred": scale,
        "max_rel_deviation_fit_vs_closed_form": dev,
        "max_rel_deviation_between_two_disjoint_samples": stab,
        "W_fit": Wfit.tolist(), "W_pred": Wpred.tolist(),
        "offdiag_support_beyond_edges":
            bool(np.max(np.abs(Wpred - np.diag(np.diag(Wpred)))) > 0.05 * scale),
        "edges": len(edges),
    }


def build_report():
    q = 6
    graphs = (("path", S.graph_path(q)), ("cycle", S.graph_cycle(q)),
              ("complete", S.graph_complete(q)), ("empty", S.graph_empty(q)))
    rows = [row(g, q, e, 0.05, "shifted") for g, e in graphs]
    rows += [row(g, q, e, 0.05, "unshifted") for g, e in graphs]
    depth = [row("cycle", q, S.graph_cycle(q), 0.05, "shifted", L) for L in (1, 2, 3)]
    ctl = S.kernel_matrix_controls(q, S.graph_cycle(q), 0.05)
    return {"q": q, "rows": rows, "depth_rows": depth, "simulator_controls": ctl}


def main():
    rep = build_report()
    text = json.dumps(rep, indent=2, sort_keys=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print("determinism: identical on a second build = %s"
          % (text == json.dumps(build_report(), indent=2, sort_keys=True)))
    print("simulator controls: %s" % json.dumps(rep["simulator_controls"], sort_keys=True))
    print("\n%-9s %-10s %6s %12s %16s %14s %10s" % (
        "graph", "conv", "layers", "scale", "fit vs closed", "sample-to-samp", "support>edges"))
    for r in rep["rows"] + rep["depth_rows"]:
        print("%-9s %-10s %6d %12.4f %16.3e %14.3e %10s"
              % (r["graph"], r["convention"], r["layers"], r["scale_of_W_pred"],
                 r["max_rel_deviation_fit_vs_closed_form"],
                 r["max_rel_deviation_between_two_disjoint_samples"],
                 r["offdiag_support_beyond_edges"]))
    print("\nwrote %s" % OUT)

    def get(graph, conv, L=1):
        return next(r for r in rep["rows"] + rep["depth_rows"]
                    if (r["graph"], r["convention"], r["layers"]) == (graph, conv, L))

    cyc, uns, emp = get("cycle", "shifted"), get("cycle", "unshifted"), get("empty", "shifted")
    claims = {
        "C1 exact simulator (K(x,x)=1, symmetric, PSD)":
            rep["simulator_controls"]["PSD_within_1e-10"]
            and rep["simulator_controls"]["max_abs_K(x,x)-1"] < 1e-12,
        "C2 shifted: the FITTED metric equals the closed form 2Cov(f) to <1% of scale":
            cyc["max_rel_deviation_fit_vs_closed_form"] < 1e-2,
        "C3 the closed form is not edge-supported (the map's metric is denser than its graph)":
            cyc["offdiag_support_beyond_edges"],
        "C4 no-edge control: W = 2 I exactly (relerr < 1e-6)":
            emp["max_rel_deviation_fit_vs_closed_form"] < 1e-6,
        "C5 shifted metric is STABLE across disjoint samples (<1% of scale)":
            cyc["max_rel_deviation_between_two_disjoint_samples"] < 1e-2,
        "C6 unshifted: scale suppressed by >=10x AND less stable than shifted":
            (uns["scale_of_W_pred"] < 0.1 * cyc["scale_of_W_pred"]
             and uns["max_rel_deviation_between_two_disjoint_samples"]
             > cyc["max_rel_deviation_between_two_disjoint_samples"]),
        "C7 the closed form survives depth (L=2,3 fit < 5% of scale)":
            all(get("cycle", "shifted", L)["max_rel_deviation_fit_vs_closed_form"] < 5e-2
                for L in (2, 3)),
    }
    print("\nSMOKE VERDICT (v2)")
    for k, v in claims.items():
        print("   %-84s %s" % (k, "PASS" if v else "FAIL"))
    print("   ALL PASS" if all(claims.values()) else "   SOME FAILED")
    return 0 if all(claims.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
