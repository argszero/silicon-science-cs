#!/usr/bin/env python3
"""Issue #87 -- R390: the metric at EVERY depth, as the Fubini-Study metric of the state.

THE OPEN ITEM THIS FILE CLOSES.  R389 derived an exact closed form for the ZZ map's small-bandwidth
metric -- W = 2 Cov_z(f), f_i(z) = 2 z_i (1 - pi m_i(z)) -- and verified it at depth L = 1 to 0.3-0.4% of
scale.  At L = 2 the SAME FORMULA deviated by 60% of scale, and R389 recorded that as an open item ("the
closed form is one-layer; match the rival per depth"), i.e. it assumed the metric itself was a one-layer
object.

THE CORRECTION THIS FILE TESTS.  That reading inverted cause and effect: what failed at L = 2 was the
FORMULA, not the metric.  A parameterised pure state |phi(x)> has a metric at every depth -- the real part
of its quantum geometric tensor, i.e. the Fubini-Study metric

    g_ij(x) = Re[<d_i phi|d_j phi>] - Re[<d_i phi|phi> conj(<d_j phi|phi>)],

and the fidelity of two nearby states obeys 1 - |<phi(x)|phi(x+d)>|^2 = d^T g(x) d + O(|d|^3), so

    -2 log K(x, x+d) = c * d^T g(x) d + O(|d|^3),

with c a convention factor this file MEASURES rather than assumes.  The L = 1 closed form is the special
case in which g happens to be x-independent and equals Cov_z(f).  arXiv:2608.29422 states the general form
("the quadratic structure persists at every circuit depth as a pullback of the Fubini-Study metric"); this
file verifies it independently and turns it into an algorithm -- which is what the study needs, because a
metric-matched classical rival can then be built at ANY depth instead of only at L = 1.

WHAT IS MEASURED, and the controls.

* the state |phi_L(x)> = (H U(x))^L |+> exactly, and its derivative d_i|phi_L> by the product rule over
  the L factors -- NOT by finite differences: T = H U is unitary, d_i T = H (i d_i theta . ), and
  d_i|phi_L> = sum_{k=0}^{L-1} T^(L-1-k) (d_i T) T^k |+>;
* the Fubini-Study metric g(x) from those derivatives, at several BASE POINTS x, so the x-dependence of
  the metric is measured rather than assumed;
* the expansion's truth: the ratio c = (-2 log K) / (d^T g d) over random small deviations, its spread,
  and the SCALING of the residual -- halving |d| must divide the residual by ~8 if the term is genuinely
  cubic, which is the control for "this is the leading order" rather than a fitted coincidence;
* the L = 1 anchor: at L = 1 the exact g must equal the R389 closed form Cov_z(f) (the W = 2 Cov(f)
  statement, with the factor measured here);
* the depth claim: g must hold at L = 2 and L = 3 with the same c and the same residual scaling;
* the convention claim (PB3): the anisotropy of g under the two phase conventions, at L = 1 and L = 2;
* determinism: the whole report is built twice and compared byte for byte.

Run:  /usr/bin/python3 smoke_v4.py      (numpy 2.0.2 -- the coordinate R389 recorded)
Writes smoke_v4_results.json beside this file.
"""
import io
import json
import math
import os
import sys

import numpy as np

import smoke_v0 as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "smoke_v4_results.json")
PI = math.pi


# ------------------------------------------------------------------ the evolution, and its derivative
def hadamard_inplace(amp, q):
    """Normalised H^q, applied to the caller's array (the R389 defect, not repeated)."""
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


def theta_table(q, edges, x, convention):
    """theta(x, z) over all basis states z."""
    n = 1 << q
    bits = ((np.arange(n)[:, None] >> np.arange(q)[None, :]) & 1).astype(float)
    th = 2.0 * (bits @ x)
    for (i, j) in edges:
        if convention == "shifted":
            g = (PI - x[i]) * (PI - x[j])
        elif convention == "unshifted":
            g = x[i] * x[j]
        else:
            raise ValueError(convention)
        th = th + 2.0 * g * bits[:, i] * bits[:, j]
    return th


def dtheta_table(q, edges, x, convention, i):
    """d theta / d x_i over all basis states -- analytic, so the state derivative is exact."""
    n = 1 << q
    bits = ((np.arange(n)[:, None] >> np.arange(q)[None, :]) & 1).astype(float)
    d = 2.0 * bits[:, i]
    for (a, b) in edges:
        if a == i:
            j = b
        elif b == i:
            j = a
        else:
            continue
        if convention == "shifted":
            # d/dx_i [ (pi - x_i)(pi - x_j) ] = -(pi - x_j)
            dg = -(PI - x[j])
        else:
            dg = x[j]
        d = d + 2.0 * dg * bits[:, i] * bits[:, j]
    return d


def apply_T(amp, th, q):
    """T = H U(x): multiply by the phase, then Hadamard.  In place on `amp`."""
    amp *= np.exp(1j * th)
    hadamard_inplace(amp, q)
    return amp


def apply_dT(amp, th, dth, q):
    """(d_i T) = H (i d_theta . ) U(x): U FIRST, then the derivative factor, then Hadamard.

    The U factor is not decoration.  d_i T = H (d_i U) and d_i U = i d_theta U, so the operator
    annihilates U(x) AFTER it has been applied -- not instead of it.  Dropping it is invisible under
    the UNSHIFTED convention at x = 0 (where theta = 0 and U = I, so the wrong helper agreed with a
    central difference to 1e-10 and the whole convention row looked correct) and wrong by 167% under
    the shifted one.  Two independent controls catch it: the central difference, and the
    normalisation identity Re<d_i phi|phi> = 0, which holds for any normalised family and which the
    wrong helper violated by 0.77.
    """
    amp *= np.exp(1j * th)
    amp *= (1j * dth)
    hadamard_inplace(amp, q)
    return amp


def state(q, edges, x, convention="shifted", layers=1):
    """|phi_L(x)> exactly."""
    n = 1 << q
    amp = np.ones(n, dtype=complex) / math.sqrt(n)   # H|0>
    th = theta_table(q, edges, x, convention)
    for _ in range(layers):
        apply_T(amp, th, q)
    return amp


def dstate(q, edges, x, convention, layers, i):
    """d|phi_L>/dx_i exactly, by the product rule over the L factors of T = H U(x)."""
    n = 1 << q
    plus = np.ones(n, dtype=complex) / math.sqrt(n)
    th = theta_table(q, edges, x, convention)
    dth = dtheta_table(q, edges, x, convention, i)
    # forward chain: u[k] = T^k |+> for k = 0..layers
    u = [plus.copy()]
    for _ in range(layers):
        v = u[-1].copy()
        apply_T(v, th, q)
        u.append(v)
    total = np.zeros(n, dtype=complex)
    for k in range(layers):
        v = u[k].copy()
        apply_dT(v, th, dth, q)         # (d_i T) T^k |+>
        for _ in range(layers - 1 - k):
            apply_T(v, th, q)
        total += v
    return total


def fs_metric(q, edges, x, convention="shifted", layers=1):
    """g_ij = Re<d_i|d_j> - Re[<d_i|phi> conj(<d_j|phi>)] -- the Fubini-Study metric of |phi(x)>.

    Also returns the imaginary antisymmetric part's size, as a declared diagnostic: g is the metric only
    if the state is a genuine parameterised family at x (the Berry curvature is the other half of the QGT
    and plays no role in the fidelity expansion, but its size says whether the point is degenerate).
    """
    phi = state(q, edges, x, convention, layers)
    dps = [dstate(q, edges, x, convention, layers, i) for i in range(q)]
    ov = [np.vdot(d, phi) for d in dps]                  # <d_i phi|phi>
    G = np.zeros((q, q), dtype=complex)
    for i in range(q):
        for j in range(q):
            G[i, j] = np.vdot(dps[i], dps[j]) - ov[i] * np.conj(ov[j])
    g = G.real
    berry = 0.5 * (G - G.conj().T) / 1j
    # TWO different quantities, and the check must name the right one: the normalisation identity is
    # d/dx_i <phi|phi> = 2 Re<d_i phi|phi> = 0, so what must vanish is the REAL part of the overlap --
    # its magnitude is the Berry CONNECTION and is legitimately non-zero.  (The first version of this
    # check asserted the magnitude and failed at 2.14: the check's object was not the object it named.)
    ov = np.asarray(ov, dtype=complex)
    return g, float(np.max(np.abs(berry))), float(np.max(np.abs(ov.real)))


def kernel(q, edges, x, xp, convention="shifted", layers=1):
    a = state(q, edges, x, convention, layers)
    b = state(q, edges, xp, convention, layers)
    return float(abs(np.vdot(a, b)) ** 2)


# ------------------------------------------------------------------ the expansion test
def expansion_probe(q, edges, x, gamma, convention, layers, m=400, seed=20260920, scale=1.0):
    """Measure c = (-2 log K)/(d^T g d), its spread, and the residual's scaling in |d|."""
    g, _, _ = fs_metric(q, edges, x, convention, layers)
    rng = np.random.default_rng(seed)
    h = (gamma / 8.0) * scale
    ratios, resid, qf = [], [], []
    for _ in range(m):
        d = h * rng.uniform(-1.0, 1.0, q)
        k = kernel(q, edges, x, x + d, convention, layers)
        y = -2.0 * math.log(max(k, 1e-300))
        quad = float(d @ g @ d)
        ratios.append(y / quad)
        resid.append(abs(y - 2.0 * quad))          # against the measured factor 2
        qf.append(y)
    return {"c_mean": float(np.mean(ratios)), "c_std": float(np.std(ratios)),
            "c_min": float(np.min(ratios)), "c_max": float(np.max(ratios)),
            "resid_norm": float(np.linalg.norm(resid)),
            "y_rms": float(np.sqrt(np.mean(np.square(qf))))}


def fit_W_at_base(q, edges, x, h, convention, layers, m=900, seed=20260920):
    """The metric READ OFF THE SIMULATOR at ONE base point: -2 log K(x, x+d) fitted as d^T W d.

    This is R389's fit with the two defects of that round removed: the base point is FIXED (so the fitted
    matrix is the metric AT a point rather than an average over a neighbourhood -- which matters from
    L = 2 on, where g depends on x), and the symmetric reconstruction places c_ij / 2 off the diagonal.
    The linear monomials are kept: they are the block whose absence the R389 first instrument suffered.
    """
    rng = np.random.default_rng(seed)
    lin = [(i,) for i in range(q)]
    quad = [(i, j) for i in range(q) for j in range(i, q)]
    A = np.zeros((m, len(lin) + len(quad)))
    y = np.zeros(m)
    for t in range(m):
        d = h * rng.uniform(-1.0, 1.0, q)
        k = kernel(q, edges, x, x + d, convention, layers)
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
    return W, float(np.linalg.norm(sol[:len(lin)]))


def fit_row(x, q, edges, gamma, convention, layers, label):
    """The decisive test: the SIMULATOR's metric against 2 x the DERIVED Fubini-Study metric."""
    g, berry, ov = fs_metric(q, edges, x, convention, layers)
    W, lin = fit_W_at_base(q, edges, x, gamma / 8.0, convention, layers)
    scale = float(np.mean(np.abs(np.diag(g))))
    return {"base_point": label, "layers": layers, "convention": convention, "gamma": gamma,
            "max_rel_dev_fit_vs_2g": float(np.max(np.abs(W - 2.0 * g)) / scale),
            "linear_block_norm": lin, "scale": scale,
            "berry_norm": berry,
            "norm_identity_resid": ov,          # Re<d_i phi|phi> must vanish: measured, not assumed
            "g": g.tolist(), "W_fit": W.tolist()}


def row(x, q, edges, gamma, convention, layers, label="x0"):
    g, berry, ov = fs_metric(q, edges, x, convention, layers)
    a = expansion_probe(q, edges, x, gamma, convention, layers)
    b = expansion_probe(q, edges, x, gamma, convention, layers, scale=0.5)   # halve |d|: cubic => /8
    return {"base_point": label, "layers": layers, "convention": convention, "gamma": gamma,
            "c_mean": a["c_mean"], "c_spread": a["c_max"] - a["c_min"],
            "resid_full": a["resid_norm"], "resid_half": b["resid_norm"],
            "resid_ratio_on_halving": a["resid_norm"] / (b["resid_norm"] or 1e-300),
            "berry_norm": berry, "overlap_norm": ov,
            "diag_mean": float(np.mean(np.abs(np.diag(g)))),
            "g": g.tolist()}


def orthonormal_report(q, edges, x, convention, layers):
    """The state is normalised to 1e-15 and the derivative is exact: the two facts g rests on."""
    phi = state(q, edges, x, convention, layers)
    nrm = abs(np.vdot(phi, phi)) ** 0.5
    dp = dstate(q, edges, x, convention, layers, 0)
    # a second, independent route to d_0|phi>: central difference of the exact state
    eps = 1e-5
    fd = (state(q, edges, x + eps * np.eye(q)[0], convention, layers)
          - state(q, edges, x - eps * np.eye(q)[0], convention, layers)) / (2 * eps)
    return {"norm_minus_one": abs(nrm - 1.0),
            "derivative_vs_central_difference_rel": float(np.linalg.norm(dp - fd) / np.linalg.norm(dp))}


def g_spread(q, edges, gamma, convention, layers, n_points=6, seed=11):
    """How much g varies over base points -- the fact that decides whether a rival needs a pointwise match."""
    rng = np.random.default_rng(seed)
    gs = [fs_metric(q, edges, gamma * rng.uniform(-1.0, 1.0, q), convention, layers)[0]
          for _ in range(n_points)]
    ref = gs[0]
    scale = float(np.mean(np.abs(np.diag(ref))))
    return {"max_rel_spread_over_base_points":
            max(float(np.max(np.abs(g - ref)) / scale) for g in gs),
            "scale": scale}


def anisotropy(g, edges):
    q = g.shape[0]
    scale = float(np.mean(np.abs(np.diag(g))))
    es = {(min(i, j), max(i, j)) for i, j in edges}
    on = [abs(g[i, j]) for i in range(q) for j in range(i + 1, q) if (i, j) in es]
    off = [abs(g[i, j]) for i in range(q) for j in range(i + 1, q) if (i, j) not in es]
    return {"aniso_on_edge": (max(on) / scale) if on else 0.0,
            "off_over_on": (max(off) / max(on)) if (on and off and max(on)) else 0.0}


# ------------------------------------------------------------------ the report
def build_report():
    q = 6
    edges = S.graph_cycle(q)
    x0 = np.zeros(q)
    xr = 0.05 * np.array([0.3, -0.7, 0.1, 0.9, -0.4, 0.5])
    rows = []
    for L in (1, 2, 3):
        rows.append(row(x0, q, edges, 0.05, "shifted", L, "x=0"))
        rows.append(row(xr, q, edges, 0.05, "shifted", L, "x=random"))
    fits = [fit_row(x, q, edges, 0.05, "shifted", L, label)
            for L in (1, 2, 3) for x, label in ((x0, "x=0"), (xr, "x=random"))]
    fits += [fit_row(x0, q, edges, 0.05, "unshifted", L, "x=0") for L in (1, 2)]
    conv = [row(x0, q, edges, 0.05, "unshifted", L, "x=0") for L in (1, 2)]
    # the L=1 anchor: the exact g against the R389 closed form Cov_z(f), and the factor it implies
    g1, _, _ = fs_metric(q, edges, x0, "shifted", 1)
    import smoke_v2 as V
    cov_f = V.cov2(V.f_vectors(q, edges)) / 2.0          # Cov_z(f); R389's W = 2 * this
    anchor = {"max_rel_dev_g_vs_Cov_f": float(np.max(np.abs(g1 - cov_f))
                                              / np.mean(np.abs(np.diag(cov_f)))),
              "max_rel_dev_g_vs_W_over_2": float(np.max(np.abs(g1 - cov_f))
                                                 / np.mean(np.abs(np.diag(cov_f)))),
              "measured_factor_on_HALF_d": float(np.mean(
                  [row(x0, q, edges, 0.05, "shifted", 1)["c_mean"]]))}
    return {"q": q, "edges": len(edges), "rows": rows, "convention_rows": conv,
            "fit_rows": fits,
            "anchor_L1": anchor,
            "numerics": orthonormal_report(q, edges, x0, "shifted", 1),
            "spread": {("L=%d" % L): g_spread(q, edges, 0.05, "shifted", L) for L in (1, 2, 3)},
            "anisotropy": {("L=%d_%s" % (L, c)): anisotropy(fs_metric(q, edges, x0, c, L)[0], edges)
                           for L in (1, 2) for c in ("shifted", "unshifted")}}


def main():
    rep = build_report()
    text = json.dumps(rep, indent=2, sort_keys=True)
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print("determinism: identical on a second build = %s"
          % (text == json.dumps(build_report(), indent=2, sort_keys=True)))
    n = rep["numerics"]
    print("numerics: |<phi|phi>-1| = %.2e ; analytic derivative vs central difference = %.2e"
          % (n["norm_minus_one"], n["derivative_vs_central_difference_rel"]))
    print("\n%-12s %-10s %8s %12s %14s %12s %12s" % (
        "base", "conv", "layers", "c_mean", "c_spread", "resid_full", "resid_ratio"))
    for r in rep["rows"] + rep["convention_rows"]:
        print("%-12s %-10s %8d %12.6f %14.2e %12.2e %12.2f"
              % (r["base_point"], r["convention"], r["layers"], r["c_mean"], r["c_spread"],
                 r["resid_full"], r["resid_ratio_on_halving"]))
    print("\nL=1 anchor: exact g vs R389's closed form Cov_z(f): max rel dev = %.2e"
          % rep["anchor_L1"]["max_rel_dev_g_vs_Cov_f"])
    print("\nDECISIVE TEST -- the simulator's metric (fitted at one base point) vs 2 x the DERIVED")
    print("Fubini-Study metric; the linear block is the R389 first-instrument defect, and the")
    print("normalisation identity Re<d_i phi|phi> = 0 is a third, independent check on the derivative:")
    print("%-10s %-10s %6s %14s %14s %14s" % (
        "base", "conv", "layers", "max rel dev", "|linear|", "Re<d|phi>"))
    for r in rep["fit_rows"]:
        print("%-10s %-10s %6d %14.3e %14.3e %14.3e" % (
            r["base_point"], r["convention"], r["layers"], r["max_rel_dev_fit_vs_2g"],
            r["linear_block_norm"], r["norm_identity_resid"]))
    print("spread of g over base points: %s"
          % json.dumps({k: round(v["max_rel_spread_over_base_points"], 8)
                        for k, v in rep["spread"].items()}))
    print("anisotropy: %s" % json.dumps({k: {kk: round(vv, 4) for kk, vv in v.items()}
                                         for k, v in rep["anisotropy"].items()}))
    print("\nwrote %s" % OUT)

    def get(base, L, conv="shifted"):
        return next(r for r in rep["rows"] + rep["convention_rows"]
                    if (r["base_point"], r["layers"], r["convention"]) == (base, L, conv))

    claims = {
        "C1 the state is normalised (exact) and the analytic derivative matches a central "
        "difference (<1e-6)":
            n["norm_minus_one"] < 1e-12 and n["derivative_vs_central_difference_rel"] < 1e-6,
        "C2 DECISIVE: the simulator's metric == 2 x the derived Fubini-Study metric "
        "(<2% of scale) at L = 1, 2, 3 and at two base points":
            all(r["max_rel_dev_fit_vs_2g"] < 2e-2 for r in rep["fit_rows"]
                if r["convention"] == "shifted"),
        "C3 the normalisation identity Re<d_i phi|phi> = 0 holds to 1e-9 (a check on the "
        "derivative that is independent of the central difference)":
            all(r["norm_identity_resid"] < 1e-9 for r in rep["fit_rows"]),
        "C4 the expansion's residual is CUBIC in |d|: halving |d| divides it by 7-9 (so the "
        "quadratic term is genuinely the leading order, not a fitted coincidence)":
            all(7.0 < get(b, L)["resid_ratio_on_halving"] < 9.0
                for L in (1, 2, 3) for b in ("x=0", "x=random")),
        "C5 at L = 1 the derived g IS R389's closed form Cov_z(f), to machine precision (<1e-12)":
            rep["anchor_L1"]["max_rel_dev_g_vs_Cov_f"] < 1e-12,
        "C6 the metric depends on the base point at every depth, and that dependence is at least "
        "5x larger at L = 2, 3 than at L = 1 (so the rival must be matched pointwise from L = 2 on)":
            (rep["spread"]["L=2"]["max_rel_spread_over_base_points"]
             > 5 * rep["spread"]["L=1"]["max_rel_spread_over_base_points"]
             and rep["spread"]["L=3"]["max_rel_spread_over_base_points"]
             > 5 * rep["spread"]["L=1"]["max_rel_spread_over_base_points"]),
        "C7 the unshifted metric's on-edge anisotropy is EXACTLY 0 at L = 1 and L = 2, while the "
        "shifted one is ~0.6-0.7: the PB3 convention gap is present at both depths":
            (rep["anisotropy"]["L=1_unshifted"]["aniso_on_edge"] == 0.0
             and rep["anisotropy"]["L=2_unshifted"]["aniso_on_edge"] == 0.0
             and rep["anisotropy"]["L=1_shifted"]["aniso_on_edge"] > 0.5
             and rep["anisotropy"]["L=2_shifted"]["aniso_on_edge"] > 0.5),
        "C8 the unshifted fit rows agree with 2g too -- the derivation is not a shifted-convention "
        "artefact":
            all(r["max_rel_dev_fit_vs_2g"] < 2e-2 for r in rep["fit_rows"]
                if r["convention"] == "unshifted"),
    }
    print("\nSMOKE VERDICT (v4)")
    for k, v in claims.items():
        print("   %-90s %s" % (k, "PASS" if v else "FAIL"))
    print("   ALL PASS" if all(claims.values()) else "   SOME FAILED (each is read off the tables above)")
    return 0 if all(claims.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
