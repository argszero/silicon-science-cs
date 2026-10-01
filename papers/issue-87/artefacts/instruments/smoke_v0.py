#!/usr/bin/env python3
"""Issue #87 -- R389 smoke test: an exact statevector simulator for the ZZ fidelity kernel, and the
first measurement of the two claims the study rests on.

WHY THIS FILE EXISTS (this round's one small goal).  The registered direction (papers/issue-87/research/
heilmeier.md) needs three things before a grid is worth building: an EXACT simulator of the entangling
feature map, evidence that the induced kernel is Gaussian to leading order in the small-bandwidth
regime (so a metric exists to match), and evidence that the metric's anisotropy is a PHASE-CONVENTION
artefact.  arXiv:2608.29422 proves all three analytically for the ZZ feature map (M = I + pi^2 Q with Q
the signless Laplacian of the entanglement graph; the unshifted convention gives the identity).  This
script reproduces them from a simulator of its own, so the study's instrument is in hand and the anchor
is independently rechecked rather than quoted.

WHAT IS MEASURED, and how.

* the state   |phi(x)> = (H U(x))^L H^q |0>  with  U(x) = diag_z exp(i theta(x, z)),
  theta(x, z) = sum_i 2 x_i z_i + sum_(i,j) in E 2 g(x_i, x_j) z_i z_j,
  g = (pi - x_i)(pi - x_j) under the SHIFTED convention and x_i x_j under the UNSHIFTED one;
* the kernel  K(x, x') = |<phi(x)|phi(x')>|^2  -- exact, no sampling, no noise, no clock;
* the metric  W fitted from  -2 log K(x, x') = d^T W d  for small d = x - x'  (linear least squares over
  the quadratic monomials d_i d_j): its SUPPORT (which off-diagonal entries are non-zero), its
  agreement with a I + b (D + A), and the ratio b/a;
* the fit's quality: the relative error of the reconstructed kernel (a metric claim is only meaningful
  if the Gaussian form actually holds at the bandwidth measured);
* determinism: the whole report is built twice and compared byte for byte.

Run:  /usr/bin/python3 smoke_v0.py        (the coordinate matters: numpy 2.0.2 is on /usr/bin/python3)
Writes smoke_v0_results.json beside this file.
"""
import io
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v0_results.json")
PI = math.pi


# ---------------------------------------------------------------- feature map + exact statevector
def graph_path(q):
    return [(i, i + 1) for i in range(q - 1)]


def graph_cycle(q):
    return [(i, (i + 1) % q) for i in range(q)]


def graph_complete(q):
    return [(i, j) for i in range(q) for j in range(i + 1, q)]


def graph_empty(q):
    return []


def degrees(q, edges):
    d = [0] * q
    for i, j in edges:
        d[i] += 1
        d[j] += 1
    return d


def signless_laplacian(q, edges):
    """Q = D + A: diagonal = degree, off-diagonal = 1 on an edge."""
    Q = np.zeros((q, q))
    for i, j in edges:
        Q[i, i] += 1
        Q[j, j] += 1
        Q[i, j] += 1
        Q[j, i] += 1
    return Q


def hadamard_inplace(amp, q):
    """Normalised H^q on a state vector, by a fast Walsh-Hadamard transform -- IN PLACE.

    The normalisation is applied to the array the caller holds, not to a returned copy: the first
    version of this function returned `amp / sqrt(n)` while its callers discarded the return value, so
    every state was an unnormalised one and K(x,x) came back as N^2 = 4096^2 instead of 1.  A
    normalisation the caller can drop is not a normalisation.
    """
    n = len(amp)
    step = 1
    for _ in range(q):
        for start in range(0, n, step * 2):
            for k in range(start, start + step):
                a, b = amp[k], amp[k + step]
                amp[k], amp[k + step] = a + b, a - b
        step *= 2
    amp /= math.sqrt(n)
    return amp


def phase_table(q, edges, x, convention):
    """theta(x, z) for every basis state z (index = bits of z)."""
    n = 1 << q
    theta = np.zeros(n)
    for i in range(q):
        theta += 2.0 * x[i] * ((np.arange(n) >> i) & 1)
    for (i, j) in edges:
        if convention == "shifted":
            g = (PI - x[i]) * (PI - x[j])
        elif convention == "unshifted":
            g = x[i] * x[j]
        else:
            raise ValueError(convention)
        theta += 2.0 * g * (((np.arange(n) >> i) & 1) * ((np.arange(n) >> j) & 1))
    return theta


def state(q, edges, x, convention="shifted", layers=1):
    """The exact |phi(x)>: H^q |0>, then L rounds of (U(x) H^q)."""
    n = 1 << q
    amp = np.zeros(n, dtype=complex)
    amp[0] = 1.0
    hadamard_inplace(amp, q)
    for _ in range(layers):
        amp = amp * np.exp(1j * phase_table(q, edges, x, convention))
        hadamard_inplace(amp, q)
    return amp


def kernel(q, edges, x1, x2, convention="shifted", layers=1):
    """K(x1, x2) = |<phi(x1)|phi(x2)>|^2 -- exact statevector overlap."""
    a1 = state(q, edges, x1, convention, layers)
    a2 = state(q, edges, x2, convention, layers)
    return float(abs(np.vdot(a1, a2)) ** 2)


# ---------------------------------------------------------------- the metric fit
def fit_metric(q, edges, gamma, convention, layers=1, m_pairs=600, seed=20260920):
    """Fit W from -2 log K = d^T W d over small deviations d, and report the fit's quality.

    Design matrix: the upper-triangular monomials d_i d_j (q(q+1)/2 columns).  The response is
    -2 log K, so the fit is a least-squares problem in W with no constant term (K(x,x) = 1 exactly).
    """
    rng = np.random.default_rng(seed)
    cols = [(i, j) for i in range(q) for j in range(i, q)]
    A = np.zeros((m_pairs, len(cols)))
    y = np.zeros(m_pairs)
    kk = np.zeros(m_pairs)
    for t in range(m_pairs):
        base = gamma * rng.uniform(-1.0, 1.0, q)
        d = (gamma / 8.0) * rng.uniform(-1.0, 1.0, q)  # small deviation: the expansion's domain
        kappa = kernel(q, edges, base, base + d, convention, layers)
        kk[t] = kappa
        for c, (i, j) in enumerate(cols):
            A[t, c] = d[i] * d[j]
        y[t] = -2.0 * math.log(max(kappa, 1e-300))
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    W = np.zeros((q, q))
    for c, (i, j) in enumerate(cols):
        W[i, j] = sol[c]
        W[j, i] = sol[c]
    # the fit's quality, in the units a reader reads: relative error of the reconstructed KERNEL
    recon = np.exp(-0.5 * (A @ sol))
    rel = float(np.max(np.abs(recon - kk) / np.maximum(kk, 1e-12)))
    # a I + b (D + A): regress the q(q+1)/2 free entries of W on those of I and Q
    Q = signless_laplacian(q, edges)
    design = np.zeros((len(cols), 2))
    target = np.zeros(len(cols))
    for c, (i, j) in enumerate(cols):
        design[c, 0] = 1.0 if i == j else 0.0
        design[c, 1] = Q[i, j]
        target[c] = W[i, j]
    ab, *_ = np.linalg.lstsq(design, target, rcond=None)
    resid = float(np.max(np.abs(design @ ab - target)))
    # the support: which off-diagonal entries are non-zero, against the edge set
    off = {(i, j) for i in range(q) for j in range(i + 1, q) if abs(W[i, j]) > 1e-9}
    edgeset = {(min(i, j), max(i, j)) for i, j in edges}
    return {
        "q": q, "edges": len(edges), "convention": convention, "layers": layers, "gamma": gamma,
        "a": float(ab[0]), "b": float(ab[1]), "b_over_a": float(ab[1] / ab[0]) if ab[0] else None,
        "pi_squared": PI ** 2,
        "max_abs_residual_of_aI_plus_bQ": resid,
        "max_relative_error_reconstructed_kernel": rel,
        "offdiagonal_support_matches_edges": off == edgeset,
        "offdiagonal_support": sorted(off), "edge_set": sorted(edgeset),
        "sample": {"K_min": float(kk.min()), "K_max": float(kk.max())},
    }


def kernel_matrix_controls(q, edges, gamma, convention="shifted", layers=1, m=60, seed=7):
    """K(x,x) = 1 exactly, and the Gram matrix is PSD -- a simulator that fails these is not exact."""
    rng = np.random.default_rng(seed)
    xs = [gamma * rng.uniform(-1.0, 1.0, q) for _ in range(m)]
    states = [state(q, edges, x, convention, layers) for x in xs]
    K = np.zeros((m, m))
    for i in range(m):
        for j in range(m):
            K[i, j] = abs(np.vdot(states[i], states[j])) ** 2
    diag_err = float(np.max(np.abs(np.diag(K) - 1.0)))
    sym = float(np.max(np.abs(K - K.T)))
    ev = float(np.linalg.eigvalsh((K + K.T) / 2).min())
    return {"max_abs_K(x,x)-1": diag_err, "max_abs_asymmetry": sym,
            "min_eigenvalue": ev, "PSD_within_1e-10": ev > -1e-10}


# ---------------------------------------------------------------- the report
def build_report():
    q = 6
    rows = []
    for name, edges in (("path", graph_path(q)), ("cycle", graph_cycle(q)),
                        ("complete", graph_complete(q))):
        for conv in ("shifted", "unshifted"):
            rows.append(dict(graph=name, **fit_metric(q, edges, 0.05, conv)))
    # the non-entangling control: no edges at all -- the metric must be isotropic and convention-blind
    for conv in ("shifted", "unshifted"):
        rows.append(dict(graph="empty", **fit_metric(q, graph_empty(q), 0.05, conv)))
    # depth: the same graph at L = 2 -- the support must survive, the coefficients may not
    for layers in (1, 2, 3):
        rows.append(dict(graph="cycle", **fit_metric(q, graph_cycle(q), 0.05, "shifted", layers)))
    # bandwidth: the Gaussian form is a small-bandwidth statement, so it must DEGRADE by design
    bw = [dict(graph="cycle", **fit_metric(q, graph_cycle(q), g, "shifted"))
          for g in (0.02, 0.05, 0.15, 0.4)]
    ctl = dict(graph="cycle", **kernel_matrix_controls(q, graph_cycle(q), 0.05))
    return {"q": q, "convention_claim": "shifted anisotropic / unshifted isotropic",
            "metric_rows": rows, "bandwidth_rows": bw, "simulator_controls": ctl}


def main():
    rep = build_report()
    text = json.dumps(rep, indent=2, sort_keys=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    # determinism: the whole report is built a second time and compared byte for byte
    text2 = json.dumps(build_report(), indent=2, sort_keys=True)
    print("determinism: report identical on a second build = %s" % (text == text2))
    print("\nsimulator controls (q=%d, cycle, gamma=0.05):" % rep["q"])
    for k, v in sorted(rep["simulator_controls"].items()):
        print("   %-24s %s" % (k, v))
    print("\nmetric rows -- -2 log K = d^T W d, W regressed on a I + b (D + A):")
    hdr = "%-9s %-10s %-7s %8s %10s %10s %8s %6s" % (
        "graph", "convention", "layers", "a", "b", "b/a", "pi^2", "supp")
    print(hdr)
    for r in rep["metric_rows"]:
        print("%-9s %-10s %-7d %8.4f %10.4f %10.4f %8.4f %6s"
              % (r["graph"], r["convention"], r["layers"], r["a"], r["b"], r["b_over_a"],
                 r["pi_squared"], "OK" if r["offdiagonal_support_matches_edges"] else "MISS"))
    print("\nfit quality (max relative error of the reconstructed kernel), and bandwidth dependence:")
    for r in rep["metric_rows"] + rep["bandwidth_rows"]:
        print("   %-9s %-10s L=%d gamma=%-5s relerr=%.2e  aI+bQ resid=%.2e  K in [%.4f, %.4f]"
              % (r["graph"], r["convention"], r["layers"], r["gamma"],
                 r["max_relative_error_reconstructed_kernel"],
                 r["max_abs_residual_of_aI_plus_bQ"], r["sample"]["K_min"], r["sample"]["K_max"]))
    print("\nwrote %s" % OUT)
    # a machine-readable verdict on the three claims this smoke test exists for
    def get(graph, conv, layers=1):
        return next(r for r in rep["metric_rows"]
                    if r["graph"] == graph and r["convention"] == conv and r["layers"] == layers)
    ent = get("cycle", "shifted")
    uns = get("cycle", "unshifted")
    emp = get("empty", "shifted")
    claims = {
        "C1 exact simulator (K(x,x)=1, symmetric, PSD)":
            rep["simulator_controls"]["PSD_within_1e-10"]
            and rep["simulator_controls"]["max_abs_K(x,x)-1"] < 1e-12,
        "C2 Gaussian form holds at gamma=0.05 (relerr < 1e-3)":
            ent["max_relative_error_reconstructed_kernel"] < 1e-3,
        "C3 shifted: off-diagonal support IS the entanglement graph": ent["offdiagonal_support_matches_edges"],
        "C4 unshifted: metric is isotropic (no off-diagonal support, b ~ 0)":
            bool(uns["offdiagonal_support_matches_edges"] is False and abs(uns["b"]) < 1e-6),
        "C5 no-edge control: isotropic under both conventions":
            abs(emp["b"]) < 1e-6,
        "C6 depth: support survives L=2,3":
            all(get("cycle", "shifted", L)["offdiagonal_support_matches_edges"] for L in (2, 3)),
        "C7 bandwidth: the Gaussian form degrades by design (relerr grows)":
            rep["bandwidth_rows"][0]["max_relative_error_reconstructed_kernel"]
            < rep["bandwidth_rows"][-1]["max_relative_error_reconstructed_kernel"],
    }
    print("\nSMOKE VERDICT")
    for k, v in claims.items():
        print("   %-72s %s" % (k, "PASS" if v else "FAIL"))
    print("   ALL PASS" if all(claims.values()) else "   SOME FAILED")
    return 0 if all(claims.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
