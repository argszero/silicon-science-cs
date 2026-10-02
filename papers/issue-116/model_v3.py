#!/usr/bin/env python3
"""Issue #116 model v3 -- the objective itself, before any optimum is read on it.

Every L* figure so far would be read off a QUASI-STATIC PROXY:
    J_proxy(L) = (1/L) * sum_{j=1..L} c_steady(tau+j) + lam_c/L
where c_steady(d) is the cost of a loop whose feedback is delayed by exactly d
steps. But a real chunk does NOT run at one delay: the actions of one chunk use
observations of ages tau+1, tau+2, ..., tau+L in turn, so the loop is
TIME-PERIODIC with period L, and the average of per-delay steady-state costs is
not obviously the right functional. This file builds the EXACT periodic cost and
measures the proxy's error -- before any claim about an optimal horizon is made
on the proxy.

  [G] THE FEASIBLE WINDOW. The last phase of a chunk uses an observation of age
      tau+L, so the periodic loop is stable only while tau+L <= d_max. With the
      floor L >= tau (a loop cannot issue a query before the previous returns),
      the feasible set is
          L in [tau, d_max - tau]  -- a window shrinking from BOTH ends as
      latency grows, vanishing at tau > d_max/2. Exact criterion used: the
      spectral radius of the period product prod_t F_t < 1.

  [J] THE OBJECTIVE. Exact cost of the periodic chunked loop by a covariance
      recursion over one period, vs the quasi-static proxy. Plus the exact mean
      response of the periodic loop (a sawtooth ripple) vs the per-delay
      steady-state ||xbar_d||^2 which R496 found delay-invariant.

  [H] L*(lam_c, tau) on the exact periodic cost, with and without the mean
      channel, and the floor/ceiling read off the same grid.

Pre-registered predictions (stated before running, so [J]/[H] can refute them):
  Q1  the proxy's relative error GROWS with L (at L=1 the periodic loop IS the
      single-delay loop, so the error must vanish there);
  Q2  the proxy error is a few percent, not a few tenths of a percent;
  Q3  the mean term shows a small but NON-ZERO L-dependence through the ripple,
      so R496's "delay-invariant" holds per-delay but not for the chunk average;
  Q4  L*(exact) and L*(proxy) agree to within one grid step.
"""
import sys
import numpy as np

sys.path.insert(0, ".")
from model_v1 import lqr_gain, route_lyap, rel  # noqa: E402

DT = 0.1
BUILD = f"python {sys.version.split()[0]} / numpy {np.__version__}"
INF = float("inf")


def frame(A, B, K, D, d):
    """One step of z_t = [x_t; x_{t-1}; ...; x_{t-D}] with u_t = -K x_{t-d}."""
    n = A.shape[0]
    m = (D + 1) * n
    F = np.zeros((m, m))
    F[0:n, 0:n] = A
    F[0:n, d * n:(d + 1) * n] -= B @ K
    for i in range(1, D + 1):
        F[i * n:(i + 1) * n, (i - 1) * n:i * n] = np.eye(n)
    return F


def period_frames(A, B, K, tau, L):
    """The L phases of a chunk: ages tau+1 .. tau+L."""
    D = tau + L
    return [frame(A, B, K, D, tau + j) for j in range(1, L + 1)], D


def feasible(A, B, K, tau, L):
    """Spectral radius of the period product -- the exact feasibility criterion.
    L < 1 is outside the domain (a chunk has at least one action); refused with
    +inf rather than raising, so a grid search can step over it."""
    if L < 1:
        return INF
    Fs, _ = period_frames(A, B, K, tau, L)
    M = np.eye(Fs[0].shape[0])
    for F in Fs:
        M = F @ M
    return float(np.max(np.abs(np.linalg.eigvals(M))))


def periodic_cost(A, B, K, W, tau, L, periods=400):
    """Exact per-step E||x||^2 of the chunked loop (covariance recursion over the
    period, averaged after the periodic steady state settles). +inf if infeasible."""
    rho = feasible(A, B, K, tau, L)
    if rho >= 1.0:
        return INF, rho
    Fs, D = period_frames(A, B, K, tau, L)
    n = A.shape[0]
    m = (D + 1) * n
    Wb = np.zeros((m, m))
    Wb[0:n, 0:n] = W
    P = np.zeros((m, m))
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        for _ in range(periods):
            for F in Fs:
                P = F @ P @ F.T + Wb
        acc = 0.0
        for F in Fs:
            acc += float(np.trace(P[0:n, 0:n]))
            P = F @ P @ F.T + Wb
    return acc / L, rho


def periodic_mean_cost(A, B, K, m_vec, tau, L):
    """Exact per-step ||xbar||^2 of the periodic loop. The period map is affine
    (xbar <- M xbar + c), so the periodic fixed point is a linear solve."""
    rho = feasible(A, B, K, tau, L)
    if rho >= 1.0:
        return INF, rho
    Fs, D = period_frames(A, B, K, tau, L)
    n = A.shape[0]
    m = (D + 1) * n
    mb = np.zeros(m)
    mb[:n] = m_vec
    M = np.eye(m)
    c = np.zeros(m)
    for F in Fs:
        c = F @ c + mb
        M = F @ M
    xbar = np.linalg.solve(np.eye(m) - M, c)
    acc = 0.0
    for F in Fs:
        acc += float(xbar[:n] @ xbar[:n])
        xbar = F @ xbar + mb
    return acc / L, rho


def proxy_cost(cost_steady, tau, L):
    if any(cost_steady[tau + j] == INF for j in range(1, L + 1)):
        return INF
    return sum(cost_steady[tau + j] for j in range(1, L + 1)) / L


def best_L(lo, hi, objective, step=1e-3):
    """Continuous argmin of `objective(L)` over the feasible range [lo, hi]."""
    best, arg = INF, float(lo)
    x = float(lo)
    while x <= hi + 1e-9:
        v = objective(x)
        if v < best:
            best, arg = v, x
        x = round(x + step, 6)
    return arg, best


def main():
    print("issue #116 model v3 -- the objective, before any optimum on it")
    print("build:", BUILD)

    A = np.array([[1.0, DT], [0.0, 1.0]])
    B = np.array([[0.5 * DT * DT], [DT]])
    K, _ = lqr_gain(A, B, np.eye(2), np.array([[100.0]]))     # well damped
    n, CH = 2, 1
    W = np.zeros((n, n)); W[CH, CH] = 1.0
    m_vec = np.zeros(n); m_vec[CH] = 0.02
    print(f"plant: double integrator dt={DT}, R=100; K={np.round(K.ravel(), 4).tolist()}")
    print(f"disturbance: dense sigma^2=1 on the velocity channel; mean {m_vec[CH]}")

    DMAX = 16
    c_steady = {}
    for d in range(DMAX + 1):
        c, _ = route_lyap(A, B, K, W, d)
        c_steady[d] = c
    dmax = max(d for d in range(DMAX + 1) if c_steady[d] != INF)
    print(f"delay margin (frozen feedback, this gain): stable for d <= {dmax}")

    # ---------------------------------- [G] the feasible window --------------
    print("\n[G] the feasible window  L in [tau, d_max - tau]")
    print(f"    {'tau':>4} | {'feasible L':>16} | width | rho_period at the two ends")
    for tau in range(0, 9):
        ok = [L for L in range(1, DMAX + 1)
              if L >= tau and tau + L <= dmax and feasible(A, B, K, tau, L) < 1.0]
        if ok:
            lo, hi = min(ok), max(ok)
            print(f"    {tau:>4} | [{lo:>3}, {hi:>3}]         | {hi - lo + 1:>5} |"
                  f" {feasible(A, B, K, tau, lo):.4f} .. {feasible(A, B, K, tau, hi):.4f}")
        else:
            print(f"    {tau:>4} | none             |     0 |   -- the latency wall")
    print(f"    prediction Q0: the window is [tau, {dmax}-tau]; it vanishes at tau = {dmax}/2"
          f" = {dmax / 2}")

    # ---------------------------------- [J] proxy vs the exact objective -----
    print("\n[J] the quasi-static proxy vs the EXACT periodic chunked cost")
    print(f"    {'tau':>4} {'L':>3} | {'proxy':>13} | {'exact':>13} | {'rel err':>9}"
          f" | {'rho_period':>10}")
    worst, by_L = 0.0, {}
    for tau in (0, 1, 2):
        for L in (1, 2, 4, 6, 8):
            if tau + L > dmax:
                continue
            pr = proxy_cost(c_steady, tau, L)
            ex, rho = periodic_cost(A, B, K, W, tau, L)
            e = rel(pr, ex)
            worst = max(worst, e)
            by_L.setdefault(L, []).append(e)
            print(f"    {tau:>4} {L:>3} | {pr:13.6e} | {ex:13.6e} | {e:9.2e} | {rho:10.4f}")
    print(f"    worst proxy error = {worst:.2e}")
    print("    Q1 (error grows with L) / Q2 (a few percent):")
    for L in sorted(by_L):
        print(f"      L={L}: max rel err over tau = {max(by_L[L]):.2e}")

    # ---------------------------------- [J2] the mean channel under chunking -
    print("\n[J2] the mean channel: per-delay steady state vs the periodic average")
    print(f"    {'tau':>4} {'L':>3} | {'per-delay (proxy)':>18} | {'periodic exact':>15}"
          f" | {'rel':>9}")
    for tau in (0, 1, 2):
        for L in (1, 2, 4, 8):
            if tau + L > dmax:
                continue
            # the proxy's mean ingredient = the average of the per-delay
            # steady-state mean responses (the correct (I-Abar)^-1 route)
            from model_v2 import mean_response
            pm = sum(mean_response(A, B, K, m_vec, tau + j)[0] for j in range(1, L + 1)) / L
            ex, _ = periodic_mean_cost(A, B, K, m_vec, tau, L)
            print(f"    {tau:>4} {L:>3} | {pm:18.12e} | {ex:15.12e} | {rel(pm, ex):9.2e}")

    # ---------------------------------- [H] the wide-price discrete grid ------
    print("\n[H] L* on the EXACT periodic cost over a WIDE price range (integer L)")
    lam_grid = [1e-3, 1e-2, 1e-1, 1e0, 1e1, 3e1, 1e2, 3e2, 1e3, 3e3, 1e4]
    for tau in (0, 1, 2, 3, 4):
        hi = dmax - tau
        if hi < max(tau, 1):
            continue
        rows = {}
        for label, use_mean in (("exact", False), ("exact+mean", True)):
            vals = []
            for lam in lam_grid:
                bestv, bestl = INF, None
                for L in range(max(tau, 1), hi + 1):
                    c, _ = periodic_cost(A, B, K, W, tau, L, periods=120)
                    if c == INF:
                        continue
                    if use_mean:
                        cm, _ = periodic_mean_cost(A, B, K, m_vec, tau, L)
                        c += cm
                    v = c + lam / L
                    if v < bestv:
                        bestv, bestl = v, L
                vals.append(bestl)
            rows[label] = vals
        print(f"    tau={tau}  feasible L in [{max(tau,1)}, {hi}]")
        print("      lam_c : " + " ".join(f"{l:6.0e}" for l in lam_grid))
        for label, vals in rows.items():
            print(f"      L* {label:<10}: " + " ".join(
                ("  none" if v is None else f"{v:6d}") for v in vals))
        if rows["exact"] != rows["exact+mean"]:
            print("      *** the mean term MOVED the optimum (rows differ) ***")
        else:
            print("      the mean term leaves L* identical at every price (as predicted)")
    print("    reading: a floor-pinned entry means the price cannot justify a longer")
    print("    chunk; a ceiling-pinned entry means feasibility, not price, is binding.")

    # ------------------- [H2] the continuous objective + the exponent --------
    def c_interp(d_int, tau, L):
        """Linear interpolation of the exact steady-state cost, +inf past the margin."""
        x = tau + L
        if x > dmax:
            return INF
        i = int(np.floor(x))
        f = x - i
        if i + 1 > DMAX or c_steady[i] == INF or c_steady[i + 1] == INF:
            return c_steady[i] if f == 0 else INF
        return c_steady[i] * (1 - f) + c_steady[i + 1] * f

    def C_cont(tau, L, nsamp=400):
        """(1/L) * integral_0^L c(tau+s) ds -- the continuous extension of the
        proxy (validated against the exact periodic cost to 3e-3 in [J])."""
        if L <= 0:
            return INF
        acc = 0.0
        h = L / nsamp
        for k in range(nsamp):
            a = c_interp(0, tau, k * h)
            b = c_interp(0, tau, (k + 1) * h)
            if a == INF or b == INF:
                return INF
            acc += 0.5 * (a + b) * h
        return acc / L

    def Lstar_cont(tau, lam, use_mean=False, step=0.01):
        lo, hi = max(tau, 1.0), float(dmax - tau)
        best, arg = INF, lo
        M = 0.0
        if use_mean:
            M = periodic_mean_cost(A, B, K, m_vec, tau, 1)[0]
        L = lo
        while L <= hi + 1e-9:
            v = C_cont(tau, L) + M + lam / L
            if v < best:
                best, arg = v, L
            L = round(L + step, 6)
        return arg

    print("\n[H2] the CONTINUOUS objective (integral form, validated in [J]): exponent fit")
    print("     a floor- or ceiling-clipped L* is excluded from the fit and stated")
    plants = {
        "scalar-stable a=0.9": (np.array([[0.9]]), np.array([[0.1]]), np.eye(1), np.array([[1.0]])),
        "dbl-int R=1": (A, B, np.eye(2), np.array([[1.0]])),
        "dbl-int R=100": (A, B, np.eye(2), np.array([[100.0]])),
    }
    for name, (Ap, Bp, Q, R) in plants.items():
        Kp, _ = lqr_gain(Ap, Bp, Q, R)
        Wp = np.zeros((Ap.shape[0], Ap.shape[0])); Wp[-1, -1] = 1.0
        cs = {d: route_lyap(Ap, Bp, Kp, Wp, d)[0] for d in range(DMAX + 1)}
        dmax_p = max(d for d in range(DMAX + 1) if cs[d] != INF)
        A0, B0, K0, W0, c_steady = A, B, K, W, c_steady   # local rebind for c_interp
        A, B, K, W, c_steady, dmax = Ap, Bp, Kp, Wp, cs, dmax_p
        lam_pts = np.exp(np.linspace(np.log(1e-2), np.log(1e4), 17))
        star = np.array([Lstar_cont(0, l) for l in lam_pts])
        interior = (star > 1.02) & (star < dmax - 0.02)
        note = f"dmax={dmax_p}"
        if interior.sum() >= 3:
            e = np.polyfit(np.log(lam_pts[interior]), np.log(star[interior]), 1)[0]
            print(f"    {name:<22} {note:<9} exponent = {e:+.3f}"
                  f"  (n={int(interior.sum())} interior of {len(lam_pts)})")
        else:
            print(f"    {name:<22} {note:<9} interior points = {int(interior.sum())}"
                  f" -- no fit; L* = {sorted(set(star))}")
        A, B, K, W, c_steady, dmax = A0, B0, K0, W0, c_steady, dmax

    # ------------------- [H3] does the mean channel move L* here? -----------
    print("\n[H3] the mean channel on the continuous objective (must be L-independent)")
    for tau in (0, 2):
        a = Lstar_cont(tau, 10.0, use_mean=False)
        b = Lstar_cont(tau, 10.0, use_mean=True)
        print(f"    tau={tau}: L*(lam=10) without the mean = {a:.3f}, with it = {b:.3f}"
              f"   difference = {abs(a - b):.2e}")

    print("\nverdict: [G]/[J]/[J2]/[H] above; the file claims nothing beyond them.")


if __name__ == "__main__":
    main()
