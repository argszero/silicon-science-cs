#!/usr/bin/env python3
"""Issue #116 model v3b -- the SHAPE channel folded into the validated objective.

R496 showed that at matched variance the kurtotic (sparse-impulse) disturbance
costs more than the Gaussian one on a SATURATING loop, and that at matched
variance AND kurtosis the residual is ordered by the sixth moment. This file asks
the question that the objective makes answerable: does the shape channel MOVE the
optimal execution horizon, and in which direction?

Design: measure the age-indexed cost curve c_arm(d) of a loop whose feedback is
delayed by exactly d steps -- on the saturated plant, for two disturbance arms
matched in per-step second moment (Gaussian vs sparse +/- impulses) -- then run
the objective validated in model_v3 (integral form, 0.3% from the exact periodic
cost) on each curve and read L*(lam_c).

  Linear arms are included as the CONTROL: there, the two disturbance shapes must
  give the same curve and the same L* (R495's equality), so a difference on the
  saturated arms is attributable to the nonlinearity and not to the sampler.

PRE-REGISTERED PREDICTIONS (stated before running; [I3]/[I4] can refute them):
  S1  on the LINEAR arms the two shapes give the same c(d) curve (rel <= 5e-3,
      i.e. within Monte-Carlo error) and the same L*;
  S2  on the SATURATED arms the kurtotic curve is everywhere above the Gaussian
      one (already measured at u_max=5 for one delay; here for every d);
  S3  the kurtotic curve is STEEPER in d, so its optimal horizon is SHORTER:
      L*_kurt <= L*_gauss at every price, with a strict inequality somewhere;
  S4  the gap in L* grows with the price lam_c (a steeper curve trades off against
      the same amortization benefit).
"""
import sys
import numpy as np

sys.path.insert(0, ".")
from model_v1 import lqr_gain, route_lyap, rel  # noqa: E402
from model_v2 import draw_gauss, draw_sparse    # noqa: E402
from model_v1 import sim_vector                 # noqa: E402

DT = 0.1
BUILD = f"python {sys.version.split()[0]} / numpy {np.__version__}"
INF = float("inf")


def measure_curve(A, B, K, dmax, arm, N=8000, T=3000, burn=1000, seed0=100, umax=None):
    """c(d) for a steady loop whose feedback is delayed by exactly d steps."""
    out = {}
    for d in range(0, dmax + 1):
        g = sim_vector(A, B, K, d, arm, N=N, T=T, burn=burn, seed=seed0 + d, umax=umax)
        out[d] = g
    return out


def c_interp(curve, dmax, x):
    """Linear interpolation of a measured curve, +inf outside the MEASURED range.
    x < 0 is refused: an age cannot be negative, and silently extrapolating there
    is how a whole objective became +inf without saying so (see Lstar)."""
    if x < 0 or x > dmax:
        return INF
    i = int(np.floor(x))
    f = x - i
    if i < 0 or i + 1 > dmax:
        return curve[i]["cost"] if f == 0 else INF
    return curve[i]["cost"] * (1 - f) + curve[i + 1]["cost"] * f


def C_cont(curve, dmax, tau, L, nsamp=200):
    """(1/L) * integral_0^L c(tau+s) ds -- the objective validated in model_v3."""
    if L <= 0 or tau + L > dmax:
        return INF
    acc, h = 0.0, L / nsamp
    for k in range(nsamp):
        a = c_interp(curve, dmax, tau + k * h)
        b = c_interp(curve, dmax, tau + (k + 1) * h)
        if a == INF or b == INF:
            return INF
        acc += 0.5 * (a + b) * h
    return acc / L


def Lstar(curve, dmax, tau, lam, step=0.01, lo=None):
    lo = max(tau, 1.0) if lo is None else lo
    hi = float(dmax - tau)
    if hi < lo:
        return None
    best, arg, L = INF, None, lo
    while L <= hi + 1e-9:
        v = C_cont(curve, dmax, tau, L) + lam / L
        if v < best:
            best, arg = v, L
        L = round(L + step, 6)
    # an all-INF objective returns None, never the starting point: the previous
    # version returned `lo` and printed a confident "+1.000" for a broken integral
    return arg


def curve_slope(curve, dmax):
    """Local log-log slope of the measured curve (a 'staleness slope' proxy)."""
    ds = np.array([d for d in range(2, dmax + 1) if curve[d]["cost"] < INF], float)
    cs = np.array([curve[int(d)]["cost"] for d in ds])
    if len(ds) < 3:
        return float("nan")
    return float(np.polyfit(np.log(ds), np.log(cs), 1)[0])


def main():
    print("issue #116 model v3b -- the shape channel in the validated objective")
    print("build:", BUILD)

    A = np.array([[1.0, DT], [0.0, 1.0]])
    B = np.array([[0.5 * DT * DT], [DT]])
    K, _ = lqr_gain(A, B, np.eye(2), np.array([[100.0]]))
    n, CH = 2, 1
    DMAX = 12
    UMAX = 5.0
    print(f"plant: double integrator dt={DT}, R=100; K={np.round(K.ravel(), 4).tolist()}")
    print(f"arms matched in per-step second moment (sigma^2 = 1) on the velocity channel:")
    print(f"  gaussian (kurt 3) and sparse +/- (p=0.05, A={np.sqrt(20):.3f}, kurt 20)")

    p_sp, a_sp = 0.05, np.sqrt(1.0 / 0.05)
    arms = {
        "gauss": lambda r, N, nn: draw_gauss(r, N, nn, CH, 1.0),
        "sparse": lambda r, N, nn: draw_sparse(r, N, nn, CH, p_sp, a_sp),
    }

    # ------------------------------- [I1] the measured curves ----------------
    print(f"\n[I1] measured c_arm(d), linear loop (u_max=None, the CONTROL)")
    lin = {}
    for name, dr in arms.items():
        lin[name] = measure_curve(A, B, K, DMAX, dr, umax=None, seed0=100)
    exact = {d: route_lyap(A, B, K, np.array([[0, 0], [0, 1.0]]), d)[0] for d in range(0, DMAX + 1)}
    print(f"    {'d':>3} | {'exact':>12} | {'gauss':>12} {'sigma':>7} | {'sparse':>12}"
          f" {'sigma':>7} | {'g/s':>8}")
    for d in range(0, DMAX + 1):
        g, s = lin["gauss"][d], lin["sparse"][d]
        print(f"    {d:>3} | {exact[d]:12.6e} | {g['cost']:12.6e}"
              f" {(g['cost']-exact[d])/g['se']:+7.2f} | {s['cost']:12.6e}"
              f" {(s['cost']-exact[d])/s['se']:+7.2f} | {g['cost']/s['cost']:8.5f}")
    gmax = max(abs(lin['gauss'][d]['cost'] / lin['sparse'][d]['cost'] - 1.0)
               for d in range(0, DMAX + 1))
    print(f"    S1: largest gauss/sparse disagreement on the linear arms = {gmax:.2e}"
          f"  ('within Monte-Carlo error' means <= ~5e-3)")

    print(f"\n[I2] measured c_arm(d), SATURATED loop (u_max={UMAX:g})")
    sat = {}
    for name, dr in arms.items():
        sat[name] = measure_curve(A, B, K, DMAX, dr, umax=UMAX, seed0=200)
    print(f"    {'d':>3} | {'gauss':>12} {'+-se':>8} {'clip':>7} {'div':>4} |"
          f" {'sparse':>12} {'+-se':>8} {'clip':>7} {'div':>4} | {'s/g':>8}")
    for d in range(0, DMAX + 1):
        g, s = sat["gauss"][d], sat["sparse"][d]
        print(f"    {d:>3} | {g['cost']:12.6e} {g['se']:8.1e} {g['clip']:7.5f} {g['n_div']:4d} |"
              f" {s['cost']:12.6e} {s['se']:8.1e} {s['clip']:7.5f} {s['n_div']:4d} |"
              f" {s['cost']/g['cost']:8.5f}")
    print(f"    S2 (kurtotic strictly above at every d): "
          f"{all(sat['sparse'][d]['cost'] > sat['gauss'][d]['cost'] for d in range(0, DMAX + 1))}")
    print(f"    staleness slope (log-log) : gauss {curve_slope(sat['gauss'], DMAX):.3f},"
          f" sparse {curve_slope(sat['sparse'], DMAX):.3f}"
          f"   -> S3 predicts sparse > gauss")

    # ------------------------------- [I2b] the linear-arm control for L* -----
    print("\n[I2b] CONTROL: L*(lam_c) on the LINEAR arms (must be the same curve,"
          " so the same L*)")
    lam_grid = [1e1, 1e2, 1e3, 1e4]
    for lam in lam_grid:
        lg = Lstar(lin["gauss"], DMAX, 0, lam)
        ls = Lstar(lin["sparse"], DMAX, 0, lam)
        if lg is None or ls is None:
            print(f"    lam_c={lam:8.1f}: NO FINITE CANDIDATE (objective all +inf)")
        else:
            print(f"    lam_c={lam:8.1f}: L* gauss={lg:.3f}  sparse={ls:.3f}"
                  f"  (difference {abs(lg-ls):.3f})")

    # ------------------------------- [I3] L* per arm, saturated --------------
    print("\n[I3] L*(lam_c) on the SATURATED arms")
    print(f"    {'lam_c':>8} | {'L* gauss':>9} | {'L* sparse':>10} | {'shift':>9}")
    for lam in lam_grid:
        lg = Lstar(sat["gauss"], DMAX, 0, lam)
        ls = Lstar(sat["sparse"], DMAX, 0, lam)
        if lg is None or ls is None:
            print(f"    {lam:8.1f} | {'none':>9} | {'none':>10} |")
            continue
        print(f"    {lam:8.1f} | {lg:9.3f} | {ls:10.3f} | {ls-lg:+9.3f}")
    shifts = []
    for l in lam_grid:
        lg = Lstar(sat["gauss"], DMAX, 0, l)
        ls = Lstar(sat["sparse"], DMAX, 0, l)
        if lg is not None and ls is not None:
            shifts.append(ls - lg)
    print(f"    finite comparisons: {len(shifts)}; S3 (shift <= 0 everywhere):"
          f" {bool(shifts) and all(s <= 0 for s in shifts)}")

    # ------------------------------- [I4] the price dependence of the gap ----
    print("\n[I4] the gap in L* as a function of price")
    print(f"    {'lam_c':>9} | {'L* gauss':>9} | {'L* sparse':>10} | {'shift':>9}"
          f" |  (a value equal to the measured range is a CLIP, not an optimum)")
    for lam in (1e1, 3e1, 1e2, 3e2, 1e3, 3e3, 1e4, 3e4, 1e5):
        lg = Lstar(sat["gauss"], DMAX, 0, lam)
        ls = Lstar(sat["sparse"], DMAX, 0, lam)
        print(f"    {lam:9.1f} | {lg:9.3f} | {ls:10.3f} | {ls-lg:+9.3f}")
    print("    S4 (the gap grows with price): read the shift column")
    print(f"    the measured range is d <= {DMAX}: any L* equal to {DMAX} is clipped by"
          f" the MEASUREMENT, not by the plant")
    for name in ("gauss", "sparse"):
        nd = [d for d in range(1, DMAX + 1) if sat[name][d]["n_div"] > 0]
        print(f"    diverged replicates with {name}: {len(nd)} delays"
              + (f" (d = {nd})" if nd else ""))

    print("\nverdict: [I1]/[I2]/[I2b]/[I3]/[I4] above; the file claims nothing beyond them.")


if __name__ == "__main__":
    main()
