#!/usr/bin/env python3
"""Issue #116 model v2 -- the two ways the linear equivalence breaks.

R495 established that on a LINEAR loop two disturbance processes matched in
per-step second moment are indistinguishable (4.3e-16), so the registered shape
prediction (P3) could not be tested there; it also found a separation once the
loop SATURATES. This file asks: which property of the disturbance carries it,
and what is the SECOND channel the equivalence hides?

  [E] THE MEAN CHANNEL. A non-zero-mean disturbance shifts the operating point.
      For a linear loop   E||x||^2 = ||xbar||^2 + Tr(P)   -- the covariance part
      is the second-moment functional R495 measured, and ||xbar||^2 is a SEPARATE
      term no variance-matched zero-mean process can supply. The mean channel
      therefore breaks the equivalence WITHOUT nonlinearity, unlike the shape
      channel. Exact route: xbar = (I - Abar_d)^-1 mbar, then ||xbar_1||^2.
      (v1 of this file used Wbar = m m^T in the Lyapunov solve, which is the
      covariance of an iid +-m signal and NOT the mean response -- it drops the
      cross terms Abar xbar mbar^T + mbar xbar^T Abar^T. The Monte-Carlo check
      disagreed by 953 sigma, which is how the error was found; the wrong route
      is kept below as a CONTROL that must keep disagreeing.)

  [F] MATCHED MOMENTS, DIFFERENT BURST STRUCTURE. The scale-mixture family
          w = s * z,   s = s1 with prob r, s0 otherwise,  z ~ N(0,1)
      has var = r s1^2 + (1-r) s0^2 and kurt = 3(r s1^4 + (1-r) s0^4)/var^2, so
      for a FIXED kurtosis target the pair (s1, s0) is determined by r and the
      family interpolates at MATCHED variance AND MATCHED kurtosis:
      r = 3/kurt is the sparse endpoint (s0 = 0: exact zeros between bursts) and
      r -> 0 approaches a dense small-noise process with rare large steps.
      Sweeping r at fixed (var, kurt) therefore varies BURST STRUCTURE with the
      second and fourth moments held fixed -- exactly the control needed to ask
      whether the saturated-loop separation is a moment effect or not.

Controls that must be able to fail: the Gaussian arm (kurt 3) must NOT match the
kurtosis-20 arms at the same variance, and the u_max=None rows must reproduce
R495's equality (the mean-zero processes are then indistinguishable).
"""
import sys
import numpy as np

sys.path.insert(0, ".")
from model_v1 import (lqr_gain, aug_matrix, route_lyap,  # noqa: E402
                      sim_vector, rel)

DT = 0.1
BUILD = f"python {sys.version.split()[0]} / numpy {np.__version__}"


# ------------------------------------------------------- marginal generators
def draw_gauss(rng, N, n, ch, sigma):
    w = np.zeros((N, n))
    w[:, ch] = sigma * rng.standard_normal(N)
    return w


def draw_sparse(rng, N, n, ch, p, a):
    """+/-a with prob p/2 each, else 0 (two-sided, zero mean)."""
    fired = rng.random(N) < p
    signs = rng.integers(0, 2, N) * 2.0 - 1.0
    w = np.zeros((N, n))
    w[:, ch] = a * signs * fired
    return w


def draw_scale_mixture(rng, N, n, ch, r, s1, s0):
    """Dense scale mixture: every step gets a draw, 10% of them large."""
    big = rng.random(N) < r
    sd = np.where(big, s1, s0)
    w = np.zeros((N, n))
    w[:, ch] = sd * rng.standard_normal(N)
    return w


def draw_one_sided(rng, N, n, ch, p, a):
    """+a with prob p, else 0 -- mean p*a, so the operating point shifts."""
    fired = rng.random(N) < p
    w = np.zeros((N, n))
    w[:, ch] = a * fired
    return w


def draw_bias_plus_centered(rng, N, n, ch, mu, var):
    """A deterministic bias mu plus centered noise of the given variance:
    matched to a one-sided process in BOTH (mean, variance)."""
    w = np.zeros((N, n))
    w[:, ch] = mu + np.sqrt(var) * rng.standard_normal(N)
    return w


def mixture_pair(r, kurt):
    """Solve for (s1, s0) with var=1 and the given kurtosis.
    From var: (1-r)v = 1 - r u; from kurt: r u^2 + (1-r)v^2 = kurt/3.
    Substituting gives  r u^2 - 2 r u + (1 - kurt(1-r)/3) = 0  ->  closed form."""
    c = 1.0 - kurt * (1.0 - r) / 3.0
    disc = 1.0 - c / r
    assert disc >= 0, f"kurtosis {kurt} is unreachable for r={r} (max is 3/r)"
    u = 1.0 + np.sqrt(disc)              # the + root; the - root is negative
    assert u > 0
    v = (1.0 - r * u) / (1.0 - r)
    assert v >= -1e-12, f"negative small-component variance for r={r}"
    return float(np.sqrt(u)), float(np.sqrt(max(v, 0.0)))


def marginal_stats(x, orders=(2, 4, 6)):
    m, v = float(x.mean()), float(x.var())
    z = (x - m) / np.sqrt(v)
    return m, v, {k: float((z ** k).mean()) for k in orders}


def mean_response(A, B, K, m, d):
    """The deterministic mean response of the delayed loop:
    xbar = (I - Abar_d)^-1 mbar, then ||xbar_1||^2 (the mean channel).
    Also returns rho, so an unstable augmented loop is refused."""
    Aa = aug_matrix(A, B, K, d)
    rho = float(np.max(np.abs(np.linalg.eigvals(Aa))))
    if rho >= 1.0:
        return float("inf"), rho
    n = A.shape[0]
    mb = np.zeros((d + 1) * n)
    mb[:n] = m
    xb = np.linalg.solve(np.eye(Aa.shape[0]) - Aa, mb)
    return float(xb[:n] @ xb[:n]), rho


def main():
    print("issue #116 model v2 -- the two ways the linear equivalence breaks")
    print("build:", BUILD)

    A = np.array([[1.0, DT], [0.0, 1.0]])
    B = np.array([[0.5 * DT * DT], [DT]])
    K, _ = lqr_gain(A, B, np.eye(2), np.array([[100.0]]))
    n, CH = 2, 1
    print(f"plant: double integrator dt={DT}, R=100; K={np.round(K.ravel(), 4).tolist()}")

    # ---------------------- [0] fixtures: are the marginals actually matched? --
    print("\n[0] fixture check -- sample moments of the marginals actually drawn")
    rng = np.random.default_rng(5)
    NBIG = 4_000_000
    p_sp, a_sp = 0.05, np.sqrt(1.0 / 0.05)                  # var = 1, kurt = 20
    s1, s0 = mixture_pair(0.10, 20.0)
    arms0 = [
        ("gauss (kurt 3)", draw_gauss(rng, NBIG, n, CH, 1.0)),
        (f"sparse p=.05 a={a_sp:.3f} (kurt 20)", draw_sparse(rng, NBIG, n, CH, p_sp, a_sp)),
        (f"mixture r=.10 s1={s1:.3f} s0={s0:.3f} (kurt 20)",
         draw_scale_mixture(rng, NBIG, n, CH, 0.10, s1, s0)),
    ]
    for name, w in arms0:
        m, v, ks = marginal_stats(w[:, CH], (2, 4, 6, 8))
        print(f"    {name:<40} mean={m:+.4f} var={v:.4f}"
              f" m4={ks[4]:7.2f} m6={ks[6]:9.2f} m8={ks[8]:11.1f}")
    print("    (2nd and 4th matched between the sparse and mixture arms; the 6th and")
    print("     8th are NOT, so a difference in [F] must be read against this ladder)")

    # ------------------------------ [E] the mean channel, LINEAR loop ---------
    d = 3
    p_on, a_on = 0.05, 1.0
    mu = p_on * a_on
    var_on = p_on * a_on ** 2 - mu ** 2
    print(f"\n[E] the MEAN channel on a linear loop, d={d}"
          f"  (one-sided impulse p={p_on}, a={a_on} -> mean={mu:.4f}, var={var_on:.6f})")

    W_centered = np.zeros((n, n)); W_centered[CH, CH] = var_on
    m_vec = np.zeros(n); m_vec[CH] = mu
    c_centered, _ = route_lyap(A, B, K, W_centered, d)
    c_mean, rho = mean_response(A, B, K, m_vec, d)
    c_wrong, _ = route_lyap(A, B, K, np.outer(m_vec, m_vec), d)
    print(f"    Tr(P) centered (var={var_on:.6f})          = {c_centered:.12e}")
    print(f"    ||xbar||^2 by (I-Abar)^-1 mbar            = {c_mean:.12e}"
          f"   (xbar = {np.round(np.linalg.solve(np.eye(A.shape[0])-A+B@K, m_vec), 4).tolist()} at d=0)")
    print(f"    PREDICTED c(one-sided) = Tr(P) + ||xbar||^2 = {c_centered + c_mean:.12e}")
    print(f"    CONTROL (the wrong route, rank-1 W=mm'):    = {c_centered + c_wrong:.12e}"
          f"   <- {rel(c_centered + c_wrong, c_centered + c_mean):.2f} relative away; MUST keep disagreeing")
    for seed in (5, 6, 7):
        g = sim_vector(A, B, K, d, lambda r, NN, nn: draw_one_sided(r, NN, nn, CH, p_on, a_on),
                       N=16000, T=6000, burn=2000, seed=seed)
        print(f"    MEASURED c(one-sided) seed={seed}          = {g['cost']:.6e}"
              f" +- {g['se']:.1e}   ({(g['cost']-(c_centered+c_mean))/g['se']:+.2f} sigma)"
              f"   diverged={g['n_div']}")
    g0 = sim_vector(A, B, K, d, lambda r, NN, nn: draw_sparse(r, NN, nn, CH, p_on, np.sqrt(var_on / p_on)),
                    N=16000, T=6000, burn=2000, seed=8)
    gb = sim_vector(A, B, K, d, lambda r, NN, nn: draw_bias_plus_centered(r, NN, nn, CH, mu, var_on),
                    N=16000, T=6000, burn=2000, seed=9)
    print(f"    c(centered two-sided, same var)   = {g0['cost']:.6e} +- {g0['se']:.1e}"
          f"   (predicted {c_centered:.6e})")
    print(f"    c(bias mu + centered, same mean+var) = {gb['cost']:.6e} +- {gb['se']:.1e}"
          f"   (predicted {c_centered + c_mean:.6e})")
    print(f"    -> the mean channel adds {c_mean:.3f}, which is {c_mean/c_centered*100:.0f}%"
          f" of the covariance part,")
    print(f"       and {c_mean/max(c_wrong,1e-30):.0f}x what the SAME bias would give if it"
          f" were carried as variance.")
    print("       Neither is visible to any variance-matched zero-mean process on this loop.")

    # ---- [E2] does the mean term move the OPTIMUM, or only the level? -------
    print("\n[E2] the mean term over the delay -- level or optimum?")
    print("      d |   ||xbar_d||^2     | ratio to d=0 | rho(Abar_d)")
    base_m = None
    for dd in range(0, 8):
        cm, rho_d = mean_response(A, B, K, m_vec, dd)
        if base_m is None:
            base_m = cm
        print(f"      {dd} | {cm:.12e} | {cm/base_m:.12f} | {rho_d:.4f}")
    print("    -> the DC gain of a stable linear loop is delay-INVARIANT, so the mean")
    print("       term is a CONSTANT added to J(L) = sum_j c(tau+j)/L + lam_c/L, and a")
    print("       constant does not move the argmin. The mean channel raises the COST")
    print("       LEVEL but not the OPTIMUM -- the opposite of the shape channel, which")
    print("       moves the optimum and (at matched moments) not the level.")

    # ------------------- [F] matched moments, different burst structure -------
    print("\n[F] MATCHED variance AND kurtosis, sweeps of burst structure (d=3, u_max=5)")
    print(f"    {'arm':<34} | {'cost':>13} {'+-se':>8} {'clip':>7} {'div':>4}"
          f" | {'m4':>6} {'m6':>8}")
    NREP = 16000
    KURT = 20.0
    ref = None
    for r in (0.15, 0.10, 0.05, 0.02):
        s1i, s0i = mixture_pair(r, KURT)
        zf = 0.0 if s0i > 0 else (1.0 - r)
        g = sim_vector(A, B, K, d,
                       lambda rr, NN, nn, s1i=s1i, s0i=s0i, r=r:
                       draw_scale_mixture(rr, NN, nn, CH, r, s1i, s0i),
                       N=NREP, seed=51, umax=5.0)
        samp = draw_scale_mixture(np.random.default_rng(3), 400_000, n, CH, r, s1i, s0i)
        _, _, ks = marginal_stats(samp[:, CH], (4, 6))
        if ref is None:
            ref = g
        ratio = g["cost"] / ref["cost"]
        rse = ratio * np.sqrt((g["se"] / g["cost"]) ** 2 + (ref["se"] / ref["cost"]) ** 2)
        print(f"    mixture r={r:<4} s1={s1i:5.3f} s0={s0i:5.3f} (zeros {zf:4.0%})"
              f" | {g['cost']:13.6e} {g['se']:8.1e} {g['clip']:7.5f} {g['n_div']:4d}"
              f" | {ks[4]:6.1f} {ks[6]:8.1f}   ratio {ratio:.4f}+-{rse:.4f}")
    ga = sim_vector(A, B, K, d, lambda rr, NN, nn: draw_gauss(rr, NN, nn, CH, 1.0),
                    N=NREP, seed=52, umax=5.0)
    print(f"    {'gaussian (kurt 3, CONTROL)':<34} | {ga['cost']:13.6e} {ga['se']:8.1e}"
          f" {ga['clip']:7.5f} {ga['n_div']:4d} | {3.0:6.1f} {15.0:8.1f}"
          f"   ratio {ga['cost']/ref['cost']:.4f}")
    print("    every r in the sweep has var=1 and kurt=20 by construction; what changes")
    print("    is how much of the mass sits at zero (85% -> 0%) and how large the bursts are.")

    print("\n[F2] the same arms with NO saturation (must agree: R495's equality)")
    W_one = np.zeros((n, n)); W_one[CH, CH] = 1.0
    c_exact_var1, _ = route_lyap(A, B, K, W_one, d)
    print(f"    exact linear value for var=1, d={d}: {c_exact_var1:.6e}")
    for r in (0.15, 0.10, 0.02):
        s1i, s0i = mixture_pair(r, KURT)
        g = sim_vector(A, B, K, d,
                       lambda rr, NN, nn, s1i=s1i, s0i=s0i, r=r:
                       draw_scale_mixture(rr, NN, nn, CH, r, s1i, s0i),
                       N=NREP, seed=53, umax=None)
        print(f"    r={r:<5} cost={g['cost']:.6e} +- {g['se']:.1e}  clip={g['clip']:.5f}"
              f"  div={g['n_div']}   sigma from exact: {(g['cost']-c_exact_var1)/g['se']:+.2f}")
    gg = sim_vector(A, B, K, d, lambda rr, NN, nn: draw_gauss(rr, NN, nn, CH, 1.0),
                    N=NREP, seed=54, umax=None)
    print(f"    gauss cost={gg['cost']:.6e} +- {gg['se']:.1e}   sigma from exact:"
          f" {(gg['cost']-c_exact_var1)/gg['se']:+.2f}")

    print("\nverdict: [0]/[E]/[F]/[F2] above; the file claims nothing beyond them.")


if __name__ == "__main__":
    main()
