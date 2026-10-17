#!/usr/bin/env python3
"""Issue #142 / research v4 -- P4's SECOND HALF: residual-dynamics system identification.

BOUNDED GOAL (one goal, stated before it runs).  The registration's P4 is that the two routes a
practitioner would try instead of a price sweep -- higher moments of the tracking error, and
system identification on the residual dynamics -- **address a different object** and fail on the
same logs.  v3 measured the moments half (verdict: split, route-specific).  This instrument
measures the SYSTEM-IDENTIFICATION half, which the registration states as: *"system identification
on residual dynamics recovers the PLANT and needs excitation a live deployment does not produce --
it does not identify a COST"*.

WHAT THE ROUTE IS.  A deployment that logs its own trajectory records (x_t, u_t) and knows the
delay d_t its chunk is executing.  System identification reads that log and fits
    x_{t+1} = A x_t + B u_t + w_t          (the plant, by ordinary least squares on [x_t; u_t])
    u_t    = -K x_{t-d_t}                  (the deployment's own control law)
    W      = Cov(w_t)                      (the residual covariance of the plant fit)
and the cost is then the SAME closed form the ground truth uses:
    c(d) = trace(P_d[0:n,0:n])  with  P_d = the augmented Lyapunov solve of (A, B, K) driven by W.
That last line is the point.  The truth's own generator is `c(d) = f(A, B, K, W, d)` -- NO cost
weight (Q, R) appears in it (the weights enter only through K, and K is identified from the log).
So the route's falsifiable question is one line: **does the reconstruction from the identified
(A, B, K, W) recover c(d)?**  If it does, the two routes address the SAME object and the
"different object" claim is false for this route too; whatever separates them is not the object.

WHAT IT WOULD COST.  The route's access requirements are different in kind from the sweep's, and
they are what the instrument measures:
  (i)   DATA -- the identification error falls with the log length; the sweep reads one scalar per
        price.  Measured as the error's log-log slope against T.
  (ii)  EXCITATION -- a linear closed loop with no disturbance has a rank-deficient regressor and
        the plant is unidentifiable.  Measured as the reconstruction error against the regressor's
        own condition number, with a no-excitation log as the control that must break it.
  (iii) INTERVENTION -- the sweep needs a price move the operator can run; the identification needs
        the RAW log (state, action, delay), which the sweep does not.

GROUND TRUTH IS EXACT BY CONSTRUCTION: c(d) is the plant's own per-delay cost (v0's augmented
Lyapunov solve).  The identified quantities are compared against the plant parameters themselves,
so there is no fit anywhere in the truth path.

A CONTROL THAT MUST FIRE.  A log with no excitation (the deterministic, decaying closed loop) must
leave the plant unidentified and the reconstruction wrong.  If it did not, the instrument would be
blind to the property it claims to depend on.

python3 spike_ident_v4.py                (writes spike_ident_v4_results.json)
python3 spike_ident_v4.py --selftest     (plants; must all fire)
"""
import json
import os
import sys
import tempfile

import numpy as np

import spike_ident_v0 as v0
import spike_ident_v1 as v1

BUILD = "python %s / numpy %s" % (sys.version.split()[0], np.__version__)
# The interpreter PATH is not in BUILD.  `sys.executable` is an INVOCATION coordinate -- it changes
# with how the interpreter was reached (the /usr/bin/python3 shim reports the shim, the framework
# binary reports itself), so an artefact carrying it is reproduced only under the exact invocation
# that wrote it: measured 2026-10-16, v3/v4/v5 did NOT all reproduce under one command, and v3's
# shipped copy recorded a DIFFERENT interpreter than v4/v5's (Class 297).  Nothing that enters a
# comparison depends on the path, so the path stays out of the artefact; the environment the
# numbers were produced in is stated in README.md instead.
T_GRID = (1000, 10000, 100000)
SEED = 7


# ------------------------------------------------------------------ the deployment's own log
def simulate(A, B, K, W, tau, L, T, burn=5000, seed=SEED):
    """The periodic chunked closed loop, as the deployment would log it: at every step the delay is
    d_t = tau + (t mod L) + 1 and the action is u_t = -K x_{t-d_t}.  Returns
        X (T,n) state, U (T,m) action, Xlag (T,n) = x_{t-d_t}, Xn (T,n) = x_{t+1}.
    The noise is drawn from W, so the log carries exactly the excitation the plant's own
    disturbance supplies -- nothing is injected that a deployment would not have."""
    n = A.shape[0]
    d0 = int(round(tau + L))
    rng = np.random.default_rng(seed)
    ev, V = np.linalg.eigh(W)
    ev = np.clip(ev, 0.0, None)
    Lr = V @ np.diag(np.sqrt(ev))
    hist = np.zeros((d0 + 1, n))
    X, U, Xlag, Xn = [], [], [], []
    for t in range(T + burn):
        j = t % int(L)
        d = int(round(tau + j + 1))
        u = -K @ hist[d]
        xn = A @ hist[0] + B @ u + Lr @ rng.standard_normal(n)
        if t >= burn:
            X.append(hist[0].copy())
            U.append(u.copy())
            Xlag.append(hist[d].copy())
            Xn.append(xn.copy())
        hist = np.vstack([xn, hist[:-1]])
    return (np.array(X), np.array(U).reshape(len(U), -1),
            np.array(Xlag), np.array(Xn))


def identify(X, U, Xlag, Xn):
    """Ordinary least squares for the three objects the route needs -- no cost weight anywhere."""
    n = X.shape[1]
    Phi = np.hstack([X, U])
    Theta, *_ = np.linalg.lstsq(Phi, Xn, rcond=None)
    Ahat = Theta[:n, :].T
    Bhat = Theta[n:, :].T
    res = Xn - Phi @ Theta
    What = res.T @ res / len(res)
    Khat = -np.linalg.lstsq(Xlag, U, rcond=None)[0].T
    # the regressor's own conditioning: the excitation the identification had to work with
    gram = Phi.T @ Phi
    cond = float(np.linalg.cond(gram))
    scale = max(float(np.trace(What) / What.shape[0]), 1e-300)
    return {"Ahat": Ahat, "Bhat": Bhat, "Khat": Khat, "What": What,
            "cond": cond, "n": int(len(X)), "w_scale_log10": float(np.log10(scale))}


def reconstruct(Ahat, Bhat, Khat, What, dmax):
    """c_hat(d) through the SAME closed form the ground truth uses (v0.steady_cost).  The cost
    weights enter nowhere: the generator the truth itself uses takes (A, B, K, W, d) only."""
    out = {}
    for d in range(1, dmax + 1):
        try:
            out[d] = v0.steady_cost(Ahat, Bhat, Khat, What, d)
        except Exception:
            out[d] = v0.INF
    return out


def relerr(a, b):
    if not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return None
    return abs(a - b) / abs(b)


def _nrm(x):
    return float(np.linalg.norm(x))


def param_errors(A, B, K, W, idr):
    return {"A": _nrm(idr["Ahat"] - A) / _nrm(A),
            "B": _nrm(idr["Bhat"] - B) / _nrm(B),
            "K": _nrm(idr["Khat"] - K) / _nrm(K),
            "W": _nrm(idr["What"] - W) / _nrm(W)}


def c_errors(c, idr, dmax):
    """Reconstruction error against the exact per-delay curve, over the delay margin."""
    ch = reconstruct(idr["Ahat"], idr["Bhat"], idr["Khat"], idr["What"], dmax)
    vals = [relerr(ch[d], c[d]) for d in range(1, dmax + 1)
            if np.isfinite(c[d]) and np.isfinite(ch[d])]
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"n": 0}
    a = np.array(vals)
    return {"n": len(a), "median": float(np.median(a)), "worst": float(a.max()),
            "best": float(a.min())}


def curve_correlation(c, idr, dmax):
    """The OBJECT test for this route: does the RECONSTRUCTED curve track the true curve across
    delays?  Pearson r over the finite delays -- a single-figure statement of sameness."""
    ch = reconstruct(idr["Ahat"], idr["Bhat"], idr["Khat"], idr["What"], dmax)
    xs, ys = [], []
    for d in range(1, dmax + 1):
        if np.isfinite(c[d]) and np.isfinite(ch[d]):
            xs.append(c[d])
            ys.append(ch[d])
    if len(xs) < 3:
        return None, len(xs)
    x, y = np.array(xs), np.array(ys)
    if x.std() < 1e-15 or y.std() < 1e-15:
        return None, len(xs)
    return float(np.corrcoef(x, y)[0, 1]), len(xs)


def slope_vs_T(points):
    """log-log slope of the reconstruction error against the log length -- the DATA cost.
    Fitted only where the error is finite and positive; the count is reported."""
    pts = [(np.log10(t), np.log10(e)) for t, e in points
           if e is not None and e > 0 and np.isfinite(e)]
    if len(pts) < 2:
        return None, len(pts)
    x = np.array([p[0] for p in pts])
    y = np.array([p[1] for p in pts])
    return float(np.polyfit(x, y, 1)[0]), len(pts)


# ------------------------------------------------------------------ selftest
def selftest():
    ok, checks = 0, []

    def check(name, cond, detail=""):
        nonlocal ok
        checks.append({"plant": name, "fired": bool(cond), "detail": detail})
        if cond:
            ok += 1

    A, B, Q, R = v0.make_plants()["double-int R=100"]
    K, _ = v0.lqr_gain(A, B, Q, R)
    W = np.eye(A.shape[0])
    n, m = A.shape[0], B.shape[1]

    # 1. the reconstruction pipeline IS the truth's own generator: given the true objects, c_hat
    #    equals c to machine precision.  If this failed the route would be judged against the
    #    wrong target.
    c_true = {d: v0.steady_cost(A, B, K, W, d) for d in range(1, 8)}
    worst = max(relerr(reconstruct(A, B, K, W, 7)[d], c_true[d]) for d in range(1, 8))
    check("plant-reconstruction-pipeline-is-the-truths-own-generator", worst < 1e-12,
          "max rel err=%.2e" % worst)
    # and the weights appear nowhere in it -- the route needs no cost model
    check("plant-reconstruction-needs-no-cost-weights",
          not any("Q" == t or "R" == t for t in reconstruct.__code__.co_names),
          "reconstruct() free names: %s" % sorted(set(reconstruct.__code__.co_names)))

    # 2. with a genuinely EXCITING log the identification is exact.  The log must carry BOTH
    #    structural equations with full-rank regressors: the plant x+ = A x + B u (noiseless), and
    #    the deployment's own control law u = -K x_{t-d}.  A log that excites only the plant leaves
    #    K unidentified -- which is exactly why this route needs the RAW (state, action, delay) log.
    rng = np.random.default_rng(3)
    T = 4000
    Xs = rng.standard_normal((T, n))
    Xlag = rng.standard_normal((T, n))
    Us = -Xlag @ K.T            # the control law, exactly  -> identifies K
    Xns = Xs @ A.T + Us @ B.T   # the plant, noiseless       -> identifies A, B
    idr = identify(Xs, Us, Xlag, Xns)
    pe = param_errors(A, B, K, W, idr)
    check("plant-identification-is-exact-under-an-exciting-log",
          pe["A"] < 1e-8 and pe["B"] < 1e-8 and pe["K"] < 1e-10,
          "A=%.2e B=%.2e K=%.2e" % (pe["A"], pe["B"], pe["K"]))
    # and the same log WITHOUT the control-law equation leaves K unidentified -- the route cannot
    # manufacture K from an action vector that the deployment's law did not produce
    Us_free = rng.standard_normal((T, m))
    idr_nofree = identify(Xs, Us_free, Xlag, Xs @ A.T + Us_free @ B.T)
    k_free = _nrm(idr_nofree["Khat"] - K) / _nrm(K)
    check("plant-a-log-without-the-control-law-leaves-K-unidentified",
          k_free > 0.5,
          "K err with a free action vector = %.3g (exact log: %.2e)" % (k_free, pe["K"]))

    # 3. the closed-loop log the deployment actually has: identified, and the cost recovered
    c, dmax = v1.plants_with_curves()["double-int R=100"]
    X, U, Xlag, Xn = simulate(A, B, K, W, 0.0, 5, 20000, burn=2000)
    idr = identify(X, U, Xlag, Xn)
    ce = c_errors(c, idr, dmax)
    check("plant-closed-loop-log-identifies-the-plant-and-the-cost",
          ce.get("n", 0) >= 5 and ce.get("median") is not None and ce["median"] < 0.2,
          "median c err=%.3g worst=%.3g over %d delays" % (ce.get("median", float("nan")),
                                                           ce.get("worst", float("nan")), ce.get("n", 0)))

    # 4. THE CONTROL THAT MUST FIRE: a log with NO excitation cannot identify the plant.  The
    #    deterministic contractive loop decays to zero, so the regressor is degenerate.
    X0, U0, Xl0, Xn0 = simulate(A, B, K, W * 0.0, 0.0, 5, 20000, burn=2000)
    idr0 = identify(X0, U0, Xl0, Xn0)
    ce0 = c_errors(c, idr0, dmax)
    worse = (ce0.get("median") is None or ce.get("median") is None
             or ce0["median"] > 10 * ce["median"] or idr0["cond"] > 1e6 * idr["cond"])
    check("plant-no-excitation-log-breaks-the-identification", worse,
          "excited cond=%.3g err=%.3g | silent cond=%.3g err=%s" %
          (idr["cond"], ce.get("median", float("nan")), idr0["cond"],
           ("%.3g" % ce0["median"]) if ce0.get("median") is not None else "undefined"))

    # 5. the curve object test is not blind: a STRUCTURAL error in the identified plant must drop
    #    the correlation.  (A mis-scaled W would NOT: the Lyapunov solve is linear in W, so a
    #    rescaled W rescales the whole curve and leaves the correlation at 1 -- a property of the
    #    statistic this plant makes explicit rather than hides.)
    idr_bad = dict(idr, Ahat=A * 1.01)     # finite but wrong: the curve survives, it just tracks worse
    idr_div = dict(idr, Ahat=A * 1.3)      # stronger: the reconstruction diverges (r undefined)
    idr_scale = dict(idr, What=W * 4.0)    # a rescaled W must NOT move it (the solve is linear in W)
    r_ok, n_ok = curve_correlation(c, idr, dmax)
    r_bad, n_bad = curve_correlation(c, idr_bad, dmax)
    r_div, n_div = curve_correlation(c, idr_div, dmax)
    r_scale, n_scale = curve_correlation(c, idr_scale, dmax)

    def _drop(r, base):
        # the object test fires the moment the reconstructed curve stops tracking the true one --
        # a structural error may make the reconstruction diverge (r undefined/NaN) rather than merely
        # decorrelate, and both are the same verdict: not the same object.
        return r is None or not np.isfinite(r) or (base is not None and r < base - 1e-3)

    check("plant-object-test-detects-a-structural-plant-error",
          r_ok is not None and np.isfinite(r_ok) and r_ok > 0.99
          and _drop(r_bad, r_ok) and _drop(r_div, r_ok)
          and not _drop(r_scale, r_ok),
          "r_ok=%.6f | A*1.01 -> %.6f (n=%d) | A*1.3 -> %s | W*4 -> %.6f" %
          (r_ok, r_bad if np.isfinite(r_bad) else float("nan"), n_bad,
           ("%.6f" % r_div) if (r_div is not None and np.isfinite(r_div)) else "undefined",
           r_scale if np.isfinite(r_scale) else float("nan")))

    # 6. the control-law identification is not the plant fit in disguise: perturbing the action
    #    must change Khat and leave a re-fit of the plant traceable to the same A
    X2, U2, Xl2, Xn2 = simulate(A, B, K, W, 0.0, 5, 5000, burn=1000, seed=99)
    idr2 = identify(X2, U2, Xl2, Xn2)
    check("plant-control-law-is-identified-from-its-own-regression",
          _nrm(idr2["Khat"] - K) / _nrm(K) < 0.2 and _nrm(idr2["Ahat"] - A) / _nrm(A) < 0.1,
          "K err=%.3g A err=%.3g" % (_nrm(idr2["Khat"] - K) / _nrm(K),
                                     _nrm(idr2["Ahat"] - A) / _nrm(A)))

    # 7. determinism of the whole path (the log is seeded) -- TWO IDENTICAL runs, same T and burn
    X3, U3, Xl3, Xn3 = simulate(A, B, K, W, 0.0, 5, 5000, burn=1000)
    idr3 = identify(X3, U3, Xl3, Xn3)
    X4, U4, Xl4, Xn4 = simulate(A, B, K, W, 0.0, 5, 5000, burn=1000)
    idr4 = identify(X4, U4, Xl4, Xn4)
    check("plant-identification-is-deterministic",
          all(abs(idr4[k] - idr3[k]).max() < 1e-12 for k in ("Ahat", "Bhat", "Khat", "What")),
          "max|dAhat|=%.2e" % abs(idr4["Ahat"] - idr3["Ahat"]).max())

    # 8. VALUE-LEVEL certification of the identification.  The local BLAS emits a handful of
    #    RuntimeWarnings (divide-by-zero / overflow / invalid in matmul) on these logs although every
    #    operand is finite (max|log| ~ 50) and the curve reconstruction is right to r>0.99 -- the
    #    spurious-FPE pattern.  The warning flag is therefore not a signal; the contract that CAN be
    #    checked is that the identified objects are finite, on the same plant grid the measurement
    #    sweeps.  (If a real overflow occurred, these would be non-finite and this plant would fire.)
    bad = []
    curves_all = v1.plants_with_curves()
    for nm in sorted(curves_all):
        _, dd = curves_all[nm]
        Aa, Bb, Qq, Rr = v0.make_plants()[nm]
        Kk, _ = v0.lqr_gain(Aa, Bb, Qq, Rr)
        XX, UU, Xll, Xnn = simulate(Aa, Bb, Kk, np.eye(Aa.shape[0]), 0.0, min(5, dd), 20000, burn=2000)
        ii = identify(XX, UU, Xll, Xnn)
        for k in ("Ahat", "Bhat", "Khat", "What"):
            if not np.isfinite(ii[k]).all():
                bad.append("%s.%s" % (nm, k))
    check("plant-identified-objects-are-finite-despite-spurious-fpe-warnings",
          not bad, "non-finite objects over %d plants: %s" % (len(curves_all), bad or "none"))

    print(json.dumps({"plants": checks, "passed": ok, "total": len(checks)}, indent=2))
    return 0 if ok == len(checks) else 1


# ------------------------------------------------------------------ main
def measure_all():
    curves = v1.plants_with_curves()
    per_plant, grid = {}, {}
    for name in sorted(curves):
        c, dmax = curves[name]
        A, B, Q, R = v0.make_plants()[name]
        K, _ = v0.lqr_gain(A, B, Q, R)
        W = np.eye(A.shape[0])
        row = {"dmax": dmax, "by_T": [], "exact_truth_check": None}
        for T in T_GRID:
            X, U, Xlag, Xn = simulate(A, B, K, W, 0.0, min(5, dmax), T, burn=min(2000, T // 4))
            idr = identify(X, U, Xlag, Xn)
            ce = c_errors(c, idr, dmax)
            r, nr = curve_correlation(c, idr, dmax)
            row["by_T"].append({"T": T, "param": param_errors(A, B, K, W, idr),
                                "cond": idr["cond"], "c_error": ce, "curve_r": r, "n_r": nr})
        # the reconstruction from the TRUE objects: the pipeline's own zero point
        idr_t = {"Ahat": A, "Bhat": B, "Khat": K, "What": W}
        row["exact_truth_check"] = c_errors(c, idr_t, dmax)
        grid[name] = row
    return grid


def summarize(grid):
    out = {"build": BUILD, "t_grid": list(T_GRID), "seed": SEED, "plants": {}}
    slopes, meds = [], {}
    for name, row in sorted(grid.items()):
        pts = [(e["T"], (e["c_error"].get("median") if e["c_error"].get("n") else None))
               for e in row["by_T"]]
        s, ns = slope_vs_T(pts)
        slopes.append(s)
        meds[name] = pts
        out["plants"][name] = {
            "dmax": row["dmax"],
            "reconstruction_from_true_objects": row["exact_truth_check"],
            "by_T": row["by_T"],
            "median_c_error_vs_T": pts,
            "loglog_slope_vs_T": s,
            "n_points_in_slope": ns,
        }
    ss = [s for s in slopes if s is not None]
    out["slope_summary"] = {"n_plants": len(ss),
                            "median_slope": float(np.median(ss)) if ss else None,
                            "min_slope": float(min(ss)) if ss else None,
                            "max_slope": float(max(ss)) if ss else None}
    return out


def write_json(path, obj):
    """Stage to a temp file and os.replace: a truncate-then-fail write is not atomic."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-v4-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main():
    R = summarize(measure_all())
    print(json.dumps(R, indent=2, sort_keys=True))
    write_json("spike_ident_v4_results.json", R)
    return R


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
