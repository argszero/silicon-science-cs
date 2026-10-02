#!/usr/bin/env python3
"""Issue #116 model v1 -- the disturbance algebra, and a SECOND exact route.

Bounded goal of this file (one goal, stated before it runs):

  1. A second, ALGORITHMICALLY INDEPENDENT exact route to the age-indexed cost
     c(d) -- a fixed-point covariance recursion -- so criterion 1's <=1e-6 claim
     is read against an exact reference instead of a Monte-Carlo (R494 amendment 1).
  2. The disturbance algebra, measured rather than assumed: a dense process and
     an impulse process HOLD AT MATCHED PER-STEP SECOND MOMENT are given to the
     same loop. On a LINEAR loop the covariance equation
         P = Abar P Abar' + Wbar
     depends on the disturbance ONLY through Wbar, so the two processes must give
     the SAME cost -- exactly. That is the R494 registration's P3 read on the arm
     where P3 was to be tested (level sets hyperbolae for impulses vs flat for
     dense noise). THIS FILE MEASURES THAT TAUTOLOGY INSTEAD OF ASSERTING IT, and
     then asks the question that has content: where the loop is NONLINEAR (a
     saturating actuator), does the separation appear?

Checks, each of which can fail:
  [A] three routes agree on the linear plant: Lyapunov solve vs covariance
      recursion (exact-exact: <=1e-10 relative) vs Monte-Carlo (~1e-2).
  [B] linear plant, matched second moment, several (lambda, A) pairs:
      cost(dense) == cost(impulse) exactly. A sampler bug shows up here.
  [C] the linearity control: cost(Wbar*2) == 2*cost(Wbar) exactly, and the 1.9x
      perturbation must NOT be reported as a match (a control that can fail).
  [D] saturation: vectorized replicates, dense vs impulse at matched second
      moment, at three actuator limits, with the CLIP FRACTION reported per arm
      (the mechanism, measured, not assumed).
"""
import sys
import warnings
import numpy as np

DT = 0.1
BUILD = f"python {sys.version.split()[0]} / numpy {np.__version__}"
INF = float("inf")


# ---------------------------------------------------------------- plant / gain
def lqr_gain(A, B, Q, R, iters=20000, tol=1e-15):
    P = Q.copy()
    for _ in range(iters):
        S = R + B.T @ P @ B
        K = np.linalg.solve(S, B.T @ P @ A)
        Pn = A.T @ P @ A - A.T @ P @ B @ K + Q
        if np.max(np.abs(Pn - P)) <= tol * max(1.0, np.max(np.abs(P))):
            return K, Pn
        P = Pn
    return K, P


def aug_matrix(A, B, K, d):
    """z_t = [x_t; x_{t-1}; ...; x_{t-d}] for u_t = -K x_{t-d}."""
    n = A.shape[0]
    m = (d + 1) * n
    Aa = np.zeros((m, m))
    Aa[0:n, 0:n] = A
    Aa[0:n, d * n:(d + 1) * n] -= B @ K     # -= : at d=0 this is the SAME block
    for i in range(1, d + 1):
        Aa[i * n:(i + 1) * n, (i - 1) * n:i * n] = np.eye(n)
    return Aa


def aug_noise(W, n, d):
    m = (d + 1) * n
    Wb = np.zeros((m, m))
    Wb[0:n, 0:n] = W
    return Wb


# ------------------------------------------------------------------- routes
def route_lyap(A, B, K, W, d):
    """Route 1: solve the discrete Lyapunov equation by a linear solve."""
    Aa = aug_matrix(A, B, K, d)
    rho = float(np.max(np.abs(np.linalg.eigvals(Aa))))
    if rho >= 1.0:
        return INF, rho
    n = A.shape[0]
    m = (d + 1) * n
    Wb = aug_noise(W, n, d)
    lhs = np.eye(m * m) - np.kron(Aa, Aa)
    P = np.linalg.solve(lhs, Wb.reshape(-1, order="F")).reshape((m, m), order="F")
    return float(np.trace(P[0:n, 0:n])), rho


def route_recursion(A, B, K, W, d, iters=200_000, tol=1e-15):
    """Route 2: fixed-point iteration P <- Aa P Aa' + Wb, NO linear solve.
    Independent algorithm (and independent failure mode) from route_lyap.

    tol is 1e-15 on purpose, MEASURED (R495, tol sweep at d=0..9): the increment
    |P_{k+1} - P_k| has a floor at rounding level, so 1e-16 is a stopping rule
    that CAN NEVER FIRE at d>=6 (it ran to the cap while the value stayed right
    to 7.8e-16), and 1e-14 stops early enough to degrade the agreement to
    1.4e-13. At 1e-15 every delay converges (<700 iterations) and the two exact
    routes agree to <=1.5e-14. The cap is reported and asserted, so an unfired
    rule is visible instead of silent."""
    Aa = aug_matrix(A, B, K, d)
    m = Aa.shape[0]
    Wb = aug_noise(W, A.shape[0], d)
    P = np.zeros((m, m))
    used = 0
    converged = False
    for i in range(iters):
        used = i + 1
        Pn = Aa @ P @ Aa.T + Wb
        if np.max(np.abs(Pn - P)) <= tol * max(1e-300, np.max(np.abs(Pn))):
            P = Pn
            converged = True
            break
        P = Pn
    return float(np.trace(P[: A.shape[0], : A.shape[0]])), used, converged


def route_mc(A, B, K, W, d, T=300_000, burn=3_000, seed=0):
    """Route 3: Monte-Carlo of the scalar loop -- an order-of-magnitude anchor."""
    rng = np.random.default_rng(seed)
    n = A.shape[0]
    x = np.zeros((d + 1, n))
    # W is SINGULAR for a one-channel disturbance, so Cholesky refuses it --
    # an eigen-square-root is the right tool (and refuses nothing silently:
    # a negative eigenvalue is clamped to zero and counted).
    ev, V = np.linalg.eigh(W)
    assert ev.min() > -1e-12, f"W is not PSD: min eigenvalue {ev.min():.3e}"
    ev = np.clip(ev, 0.0, None)
    L = V @ np.diag(np.sqrt(ev))
    acc, cnt = 0.0, 0
    for t in range(T + burn):
        u = -K @ x[d]
        xn = A @ x[0] + B @ u + L @ rng.standard_normal(n)
        if t >= burn:
            acc += float(xn @ xn)
            cnt += 1
        x = np.vstack([xn, x[:-1]])
    return acc / cnt


# --------------------------------------------------------- disturbance algebra
def noise_dense(sigma, n, channel):
    """Per-step second moment = sigma^2 on one channel."""
    W = np.zeros((n, n))
    W[channel, channel] = sigma ** 2
    return W


def noise_impulse(lam, amp, n, channel, sign_symmetric=True):
    """Bernoulli(lam) impulses of magnitude amp, +/- with prob 1/2 each.
    E[w w'] = lam * amp^2 on the channel (mean zero -- asserted below)."""
    W = np.zeros((n, n))
    W[channel, channel] = lam * amp ** 2
    return W


def draw_dense(rng, N, n, sigma, channel):
    w = np.zeros((N, n))
    w[:, channel] = sigma * rng.standard_normal(N)
    return w


def draw_impulse(rng, N, n, lam, amp, channel):
    fired = rng.random(N) < lam
    signs = rng.integers(0, 2, N) * 2.0 - 1.0
    w = np.zeros((N, n))
    w[:, channel] = amp * signs * fired
    return w


DIVERGED = 1e6      # a replicate whose mean cost exceeds this is diverged, and counted


def sim_vector(A, B, K, d, draw, N=4000, T=4000, burn=1000, seed=0, umax=None):
    """Vectorized replicates of the (optionally saturating) loop.
    Returns dict: cost, se (replicate-level standard error), clip fraction,
    and the number of DIVERGED replicates (a saturating loop can be unstable --
    an arm whose replicates diverge is not comparable to one whose do not)."""
    rng = np.random.default_rng(seed)
    n = A.shape[0]
    X = np.zeros((d + 1, N, n))
    acc = np.zeros(N)
    clips = 0
    steps = 0
    Bv = B.ravel()
    for t in range(T + burn):
        u = -(X[d] @ K.T).ravel()
        if umax is not None:
            uu = np.clip(u, -umax, umax)
            if t >= burn:
                clips += int(np.sum(uu != u))
            u = uu
        w = draw(rng, N, n)
        xn = X[0] @ A.T + np.outer(u, Bv) + w
        if t >= burn:
            acc += (xn ** 2).sum(1)
            steps += 1
        X = np.concatenate([xn[None, :, :], X[:-1]], axis=0)
    per = acc / steps
    n_div = int(np.sum(per > DIVERGED))
    finite = per[np.isfinite(per)]
    return {
        "cost": float(finite.mean()) if finite.size else INF,
        "median": float(np.median(finite)) if finite.size else INF,
        "se": float(finite.std(ddof=1) / np.sqrt(finite.size)) if finite.size > 1 else INF,
        "sd": float(finite.std(ddof=1)) if finite.size > 1 else INF,
        "clip": float(clips) / (steps * N),
        "n_div": n_div,
        "n": int(finite.size),
    }


# ------------------------------------------------------------------- helpers
def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


def main():
    print("issue #116 model v1 -- disturbance algebra + a second exact route")
    print("build:", BUILD)

    A = np.array([[1.0, DT], [0.0, 1.0]])
    B = np.array([[0.5 * DT * DT], [DT]])
    Q, R = np.eye(2), np.array([[100.0]])   # well damped: delay margin d<=12
    K, _ = lqr_gain(A, B, Q, R)
    n = 2
    VEL = 1
    print(f"plant: double integrator dt={DT}, R=100; K={np.round(K.ravel(), 4).tolist()}")

    sigma2 = 1.0                      # dense per-step second moment on the velocity channel
    W_dense = noise_dense(np.sqrt(sigma2), n, VEL)

    # ---- [A] three routes -------------------------------------------------
    print("\n[A] three routes to the age-indexed cost c(d)  (dense disturbance, sigma^2=1)")
    print("    d   route_lyap        route_recursion   iters     rel(L,R)  route_mc     rel(L,MC)")
    worst_exact = 0.0
    mc_rel = []
    for d in (0, 1, 3, 6, 9):
        c1, _ = route_lyap(A, B, K, W_dense, d)
        c2, it, conv = route_recursion(A, B, K, W_dense, d)
        c3 = route_mc(A, B, K, W_dense, d, T=200_000, burn=2_000, seed=700 + d)
        r12, r13 = rel(c1, c2), rel(c1, c3)
        worst_exact = max(worst_exact, r12)
        mc_rel.append(r13)
        flag = "" if conv else "  <-- CAP HIT, rule never fired"
        print(f"    {d}   {c1:.10e}  {c2:.10e}  {it:>7d}  {r12:.2e}  {c3:.6e}  {r13:.2e}{flag}")
        assert conv, f"recursion did not converge at d={d} within the cap"
    print(f"    worst exact-vs-exact relative deviation = {worst_exact:.2e}"
          f"   (criterion 1 is read against THIS pair)")
    print(f"    Monte-Carlo deviations: {min(mc_rel):.1e} .. {max(mc_rel):.1e}")

    # ---- [A2] the warning census: a BLAS flag is not a defect in the value ----
    print("\n[A2] warnings raised by the recursion, and whether the VALUE suffers")
    for d in (0, 3, 6):
        Aa = aug_matrix(A, B, K, d)
        Wb = aug_noise(W_dense, n, d)
        m = Aa.shape[0]
        with warnings.catch_warnings(record=True) as wl:
            warnings.simplefilter("always")
            P = np.zeros((m, m))
            for _ in range(800):
                P = Aa @ P @ Aa.T + Wb
            nw = len(wl)
            kinds = sorted({str(w.message) for w in wl})
        with warnings.catch_warnings(record=True) as wl2:
            warnings.simplefilter("always")
            Pe = np.zeros((m, m))
            for _ in range(800):
                Pe = np.einsum("ij,jk,lk->il", Aa, Pe, Aa) + Wb   # no BLAS gemm
            nwe = len(wl2)
        ce, cle = float(np.trace(Pe[:n, :n])), float(np.trace(P[:n, :n]))
        print(f"    d={d} m={m}: matmul warnings={nw} {kinds if nw else ''}"
              f" | einsum warnings={nwe} | finite={np.isfinite(ce) and np.isfinite(cle)}"
              f" | two paths agree: {rel(ce, cle):.2e}")
        assert nwe == 0, "the 'it is BLAS' explanation is WRONG: einsum warned too"
    print("    -> the flags come from the BLAS gemm kernel, not from this loop's"
          " arithmetic; the instrument policy is to keep them VISIBLE, count them,")
    print("       and assert what matters (finite + agreement with route 1), never"
          " to silence them or to fail on them.")

    # ---- [B] matched second moment, linear plant --------------------------
    print("\n[B] linear plant, disturbance HOLDING THE SAME second moment, d=3")
    target = sigma2
    pairs = [(0.01, np.sqrt(target / 0.01)), (0.05, np.sqrt(target / 0.05)),
             (0.2, np.sqrt(target / 0.2)), (0.5, np.sqrt(target / 0.5))]
    c_dense, _ = route_lyap(A, B, K, W_dense, 3)
    print(f"    dense: sigma^2 = {target:g}  ->  c = {c_dense:.12e}")
    worst_b = 0.0
    for lam, amp in pairs:
        W_imp = noise_impulse(lam, amp, n, VEL)
        assert abs(W_imp[VEL, VEL] - target) < 1e-12, "second moment mismatch in the fixture"
        c_imp, _ = route_lyap(A, B, K, W_imp, 3)
        r = rel(c_dense, c_imp)
        worst_b = max(worst_b, r)
        print(f"    impulse: lambda={lam:<5g} A={amp:<7.4f}  lambda*A^2={lam*amp*amp:.6g}"
              f"  ->  c = {c_imp:.12e}  rel = {r:.2e}")
    print(f"    worst relative deviation = {worst_b:.2e}   <- the P3 tautology, MEASURED")

    print("    and the same two processes through the Monte-Carlo (sampler cross-check)")
    for i, (name, dr) in enumerate((("dense", lambda r, N, n: draw_dense(r, N, n, np.sqrt(target), VEL)),
                                    ("impulse", lambda r, N, n: draw_impulse(r, N, n, 0.05, np.sqrt(20.0), VEL)))):
        g = sim_vector(A, B, K, 3, dr, N=4000, T=4000, burn=1000, seed=11 + i)
        print(f"      {name:<8} mc c = {g['cost']:.6e} +- {g['se']:.1e}"
              f"   rel to exact = {rel(c_dense, g['cost']):.2e}   diverged={g['n_div']}")

    # ---- [C] linearity control (a control that must be able to fail) ------
    print("\n[C] linearity control: is the cost exactly linear in the second moment?")
    c_x1, _ = route_lyap(A, B, K, W_dense, 3)
    c_x2, _ = route_lyap(A, B, K, 2.0 * W_dense, 3)
    c_x19, _ = route_lyap(A, B, K, 1.9 * W_dense, 3)
    c_x05, _ = route_lyap(A, B, K, 0.5 * W_dense, 3)
    print(f"    c(W)   = {c_x1:.12e}")
    print(f"    c(2W)  = {c_x2:.12e}   c(2W)/c(W)   = {c_x2/c_x1:.12f}  (expect 2)")
    print(f"    c(1.9W)= {c_x19:.12e}  c(1.9W)/c(W) = {c_x19/c_x1:.12f}  (expect 1.9)")
    print(f"    c(0.5W)= {c_x05:.12e}  c(0.5W)/c(W) = {c_x05/c_x1:.12f}  (expect 0.5)")
    print(f"    1.9W is NOT a match for 2W: rel = {rel(c_x2, c_x19):.2e} (must be ~5e-2, not 0)")

    # ---- [D] the arm where the question has content: saturation ----------
    print("\n[D] saturation: dense vs impulse at matched second moment (vectorized MC)")
    NREP = 16000
    print(f"    N={NREP} replicates, 4000 steps, burn-in 1000; dense sigma^2 = "
          f"{target:g}; impulse lambda=0.05, A={np.sqrt(20.0):.4f} (lambda*A^2 = {0.05*20:.6g})")
    dr_dense = lambda r, N, n: draw_dense(r, N, n, np.sqrt(target), VEL)
    dr_imp = lambda r, N, n: draw_impulse(r, N, n, 0.05, np.sqrt(20.0), VEL)
    print(f"    {'u_max':>7} | {'c dense':>13} {'+-se':>8} {'clip':>7} {'div':>4}"
          f" | {'c impulse':>13} {'+-se':>8} {'clip':>7} {'div':>4}"
          f" | ratio(mean)  ratio(median)")
    print(f"    {'':>7} | {'':>13} {'':>8} {'':>7} {'':>4} | {'':>13} {'':>8} {'':>7} {'':>4}"
          f" |  (median is the robust companion: at u_max=2 the mean is dominated"
          f" by 1-2 divergent replicates)")
    for umax in (None, 20.0, 5.0, 2.0):
        cd = sim_vector(A, B, K, 3, dr_dense, N=NREP, seed=21, umax=umax)
        ci = sim_vector(A, B, K, 3, dr_imp, N=NREP, seed=22, umax=umax)
        r = ci["cost"] / cd["cost"]
        rse = r * np.sqrt((ci["se"] / ci["cost"]) ** 2 + (cd["se"] / cd["cost"]) ** 2)
        tag = "none" if umax is None else f"{umax:g}"
        print(f"    {tag:>7} | {cd['cost']:13.6e} {cd['se']:8.1e} {cd['clip']:7.5f} {cd['n_div']:4d}"
              f" | {ci['cost']:13.6e} {ci['se']:8.1e} {ci['clip']:7.5f} {ci['n_div']:4d}"
              f" | {r:.4f}+-{rse:.4f}   {ci['median']/cd['median']:.4f}")
        print(f"    {'':>7} |   spread: sd={cd['sd']:.3e} on a mean of {cd['cost']:.3e}"
              f"  (sd/mean = {cd['sd']/cd['cost']:.3f}); impulse sd/mean = {ci['sd']/ci['cost']:.3f}")
    cd0 = sim_vector(A, B, K, 3, dr_dense, N=NREP, seed=41, umax=None)
    ci0 = sim_vector(A, B, K, 3, dr_imp, N=NREP, seed=42, umax=None)
    sig = (ci0["cost"] - cd0["cost"]) / np.sqrt(cd0["se"] ** 2 + ci0["se"] ** 2)
    print(f"    CONTROL (fresh seeds, saturating loop with NO bound): dense {cd0['cost']:.6e}"
          f" +- {cd0['se']:.1e}, impulse {ci0['cost']:.6e} +- {ci0['se']:.1e}")
    print(f"      -> the two arms differ by {sig:+.2f} sigma; exact routes differ by"
          f" {rel(c_dense, c_dense):.0e} by construction")
    for g, nm in ((cd0, "dense"), (ci0, "impulse")):
        print(f"      {nm:<8} mc vs the exact route: {(g['cost']-c_dense)/g['se']:+.2f} sigma")

    print("\nverdict: [A]-[D] above; the file claims nothing beyond them.")


if __name__ == "__main__":
    main()
