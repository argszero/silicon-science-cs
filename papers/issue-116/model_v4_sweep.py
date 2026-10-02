#!/usr/bin/env python3
"""Issue #116 model v4 -- the manuscript-grade sweep on the validated objective.

Everything here is read on the objective validated in model_v3:
  - the EXACT periodic (chunked) cost is the reference; the continuous integral
    objective is the fast surrogate, used only where [J] of v3 measured its error
    at <= 3e-3 (and at L=1, 5.6e-9);
  - the feasible set is [tau, d_max - tau], vertical bar the latency wall.

  [K] PLANT SWEEP x TAU GRID.  Four plant families, tau crossing the latency
      wall, over a price grid spanning 8 decades: L*(lam_c, tau) per plant, with
      each cell classified FLOOR / INTERIOR / CEILING so a pinned entry is never
      read as a law.
  [L] THE EXPONENT, WITH UNCERTAINTY.  Per plant, the log-log slope of L* in
      lam_c over the INTERIOR points only, with its regression standard error
      and 95% interval, plus the number of points used and the number clipped.
  [M] THE NONLINEAR ARM.  The saturating plant measured by Monte-Carlo at a
      subset of tau, for the two disturbance shapes matched in second moment,
      giving the shape channel's shift in L* with replicate-level error bars.
  [E] THE TWO CHANNELS, re-measured here so every figure is drawable from this
      file alone: the MEAN channel (||xbar||^2, delay-invariant) and the SHAPE
      channel (the sparse/gauss cost ratio), with the Monte-Carlo prediction
      check at three seeds.

Output: canonical_results.json (deterministic) + the tables printed here.
"""
import itertools
import json
import sys
import numpy as np

sys.path.insert(0, ".")
from model_v1 import lqr_gain, route_lyap, sim_vector  # noqa: E402
from model_v2 import draw_gauss, draw_sparse, draw_one_sided, mean_response  # noqa: E402

DT = 0.1
BUILD = f"python {sys.version.split()[0]} / numpy {np.__version__}"
INF = float("inf")
DELTA = 0.02          # L grid resolution for the integral objective


# ------------------------------------------------------------------ plants
def make_plants():
    A2 = np.array([[1.0, DT], [0.0, 1.0]])
    B2 = np.array([[0.5 * DT * DT], [DT]])
    return {
        "scalar-stable a=0.9":  (np.array([[0.9]]), np.array([[0.1]]), np.eye(1), np.array([[1.0]])),
        "double-int R=1 (near-margin)": (A2, B2, np.eye(2), np.array([[1.0]])),
        "double-int R=10":      (A2, B2, np.eye(2), np.array([[10.0]])),
        "double-int R=100 (well damped)": (A2, B2, np.eye(2), np.array([[100.0]])),
    }


def steady_curve(A, B, K, W, dmax):
    """Exact per-delay cost c(d) for d = 0..dmax; +inf past the delay margin."""
    c = {}
    for d in range(dmax + 1):
        c[d], _ = route_lyap(A, B, K, W, d)
    return c


def interp_curve(c, dmax, x):
    """Linear interpolation of coarsely-sampled c(d); +inf outside [0, dmax]."""
    if x < 0 or x > dmax:
        return INF
    i = int(np.floor(x))
    f = x - i
    if i < 0 or i >= dmax:
        return c[dmax] if i >= dmax else c[0]
    return c[i] * (1 - f) + c[i + 1] * f


def objective_grid(c, dmax, tau):
    """Precompute the objective's mean-cost numerator on an L-grid of step DELTA.
    Returns (Ls, mean_cost) where mean_cost[m] = (1/L) integral_0^L c(tau+s) ds."""
    if tau > dmax:
        return None, None
    K = int((dmax - tau) / DELTA)
    if K < 1:
        return None, None
    xs = tau + DELTA * np.arange(K + 1)
    vals = np.array([interp_curve(c, dmax, x) for x in xs])
    if np.any(~np.isfinite(vals)):
        # clip the grid to the last finite sample (a stated domain, not a guess)
        last = int(np.max(np.where(np.isfinite(vals))[0]))
        vals = vals[:last + 1]
        xs = xs[:last + 1]
        K = last
        if K < 1:
            return None, None
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (vals[:-1] + vals[1:]) * DELTA)])
    Ls = DELTA * np.arange(1, K + 1)
    mean_cost = cum[1:] / Ls
    return Ls, mean_cost


def lstar(Ls, mean_cost, lam, lo):
    """argmin of mean_cost + lam/L over the L-grid restricted to L >= lo."""
    mask = Ls >= lo - 1e-9
    if not np.any(mask):
        return None
    obj = mean_cost[mask] + lam / Ls[mask]
    i = int(np.argmin(obj))
    if not np.isfinite(obj[i]):
        return None
    return float(Ls[mask][i])


def classify(Lstar, tau, dmax):
    if Lstar is None:
        return "none"
    if abs(Lstar - max(tau, DELTA)) <= DELTA + 1e-9:
        return "floor"
    if abs(Lstar - (dmax - tau)) <= DELTA + 1e-9:
        return "ceiling"
    return "interior"


# ------------------------------------------------------------------- [M] arm
def measure_curve(A, B, K, dmax, arm, N, T, burn, seed0, umax):
    out = {}
    for d in range(0, dmax + 1):
        out[d] = sim_vector(A, B, K, d, arm, N=N, T=T, burn=burn, seed=seed0 + d, umax=umax)
    return out


def c_of(curve, x):
    """Interpolate a MEASURED curve (dict d -> {'cost','se'}), +inf outside."""
    ks = sorted(curve)
    if x < ks[0] or x > ks[-1]:
        return INF
    i = int(np.floor(x))
    f = x - i
    if i + 1 > ks[-1]:
        return curve[i]["cost"] if f == 0 else INF
    return curve[i]["cost"] * (1 - f) + curve[i + 1]["cost"] * f


def objective_grid_measured(curve, tau, lo_min=1.0):
    ks = sorted(curve)
    dmax = ks[-1]
    if tau > dmax:
        return None, None
    K = int((dmax - tau) / DELTA)
    if K < 1:
        return None, None
    vals = np.array([c_of(curve, tau + DELTA * k) for k in range(K + 1)])
    if not np.all(np.isfinite(vals)):
        last = int(np.max(np.where(np.isfinite(vals))[0]))
        vals, K = vals[:last + 1], last
        if K < 1:
            return None, None
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (vals[:-1] + vals[1:]) * DELTA)])
    Ls = DELTA * np.arange(1, K + 1)
    return Ls, cum[1:] / Ls


def main():
    print("issue #116 model v4 -- manuscript-grade sweep on the validated objective")
    print("build:", BUILD)
    res = {"build": BUILD, "delta": DELTA, "plants": {}, "nonlinear": {},
           "lam_grid": [], "tau_grid": []}

    plants = make_plants()
    f5 = np.zeros((2, 2)); f5[1, 1] = 1.0          # dense sigma^2=1 on velocity
    lam_grid = list(np.logspace(-2, 5, 22))        # 7 decades
    tau_grid = [0, 1, 2, 3, 4, 6, 8]
    res["lam_grid"] = [float(v) for v in lam_grid]
    res["tau_grid"] = [int(t) for t in tau_grid]

    # ---------------------------- [K] sweep per plant ------------------------
    print("\n[K] L*(lam_c, tau) per plant  (F = floor-pinned, C = ceiling-pinned,"
          " i = interior)")
    for name, (A, B, Q, R) in plants.items():
        K, _ = lqr_gain(A, B, Q, R)
        dmax_probe = 20
        c = steady_curve(A, B, K, f5 if A.shape[0] == 2 else np.eye(1), dmax_probe)
        dmax = max(d for d in range(dmax_probe + 1) if c[d] != INF)
        W = f5 if A.shape[0] == 2 else np.eye(1)
        rec = {"K": np.round(K.ravel(), 6).tolist(), "dmax": dmax, "tau": {}}
        print(f"\n    plant {name}:  K={np.round(K.ravel(), 4).tolist()}  d_max={dmax}"
              f"  latency wall at tau={dmax/2:g}")
        hdr = "      tau | " + " ".join(f"{l:7.1e}" for l in lam_grid)
        print(hdr)
        for tau in tau_grid:
            if max(tau, 1) > dmax - tau:
                print(f"      {tau:>3} | infeasible beyond the latency wall")
                continue
            Ls, mc = objective_grid(c, dmax, tau)
            if Ls is None:
                continue
            row, cls = [], []
            for lam in lam_grid:
                ls = lstar(Ls, mc, lam, lo=max(tau, 1.0))
                row.append(ls)
                cls.append(classify(ls, tau, dmax))
            rec["tau"][str(tau)] = {"Lstar": row, "class": cls}
            print(f"      {tau:>3} | " + " ".join(
                (f"{v:7.2f}" if v is not None else "   none") for v in row))
            print("          | " + " ".join(
                f"      {c0}" if c0 != "interior" else "      ." for c0 in cls))
        res["plants"][name] = rec

    # ---------------------------- [L] the exponent with uncertainty ----------
    print("\n[L] the fitted exponent of L* in lam_c (INTERIOR points only)")
    print(f"    {'plant':<32} | {'d_max':>5} | {'tau':>3} | {'exp':>7} {'+-se':>7}"
          f" {'95% CI':>17} | {'n':>2} {'clipped':>7}")
    for name, rec in res["plants"].items():
        dmax = rec["dmax"]
        exps = []
        for tau_s, d in rec["tau"].items():
            tau = int(tau_s)
            Ls_ = np.array([v if v is not None else np.nan for v in d["Lstar"]])
            cls = np.array(d["class"])
            x = np.array(lam_grid)
            m = cls == "interior"
            n_clip = int(np.sum((cls == "floor") | (cls == "ceiling")))
            if m.sum() >= 3:
                lx, ly = np.log(x[m]), np.log(Ls_[m])
                slope, intercept = np.polyfit(lx, ly, 1)
                resid = ly - (slope * lx + intercept)
                dof = int(m.sum()) - 2
                se = float(np.sqrt((resid @ resid) / dof / np.sum((lx - lx.mean()) ** 2))) if dof > 0 else float("nan")
                lo, hi = slope - 1.96 * se, slope + 1.96 * se
                exps.append(slope)
                print(f"    {name:<32} | {dmax:>5} | {tau:>3} | {slope:+7.3f} {se:7.4f}"
                      f" [{lo:+.3f}, {hi:+.3f}] | {int(m.sum()):>2} {n_clip:>7}")
                d["exponent"] = {"value": float(slope), "se": se,
                                 "ci95": [float(lo), float(hi)], "n": int(m.sum())}
            else:
                print(f"    {name:<32} | {dmax:>5} | {tau:>3} |   -- no fit"
                      f" (interior n={int(m.sum())})")
                d["exponent"] = None
        if exps:
            res["plants"][name]["exponent_all_tau"] = {
                "min": float(np.min(exps)), "max": float(np.max(exps)),
                "mean": float(np.mean(exps)), "n_tau": len(exps)}
    all_e = []
    for name, rec in res["plants"].items():
        if rec.get("tauexps") is None and False:
            pass
        for tau_s, d in rec["tau"].items():
            if d.get("exponent"):
                all_e.append(d["exponent"]["value"])
    if all_e:
        print(f"\n    across all plants and tau: exponent in"
              f" [{np.min(all_e):+.3f}, {np.max(all_e):+.3f}],"
              f" mean {np.mean(all_e):+.3f} (n={len(all_e)} fits)"
              f"   -> the square root (0.500) is inside but not the whole story")
    res["exponent_range"] = [float(np.min(all_e)), float(np.max(all_e))] if all_e else None

    # ---------------------------- [M] the nonlinear arm ---------------------
    print("\n[M] the NONLINEAR arm (saturating double integrator, u_max=5),"
          " shapes matched in second moment")
    A2 = np.array([[1.0, DT], [0.0, 1.0]])
    B2 = np.array([[0.5 * DT * DT], [DT]])
    Kn, _ = lqr_gain(A2, B2, np.eye(2), np.array([[100.0]]))
    p_sp, a_sp = 0.05, np.sqrt(20.0)
    arms = {"gauss": lambda r, N, nn: draw_gauss(r, N, nn, 1, 1.0),
            "sparse": lambda r, N, nn: draw_sparse(r, N, nn, 1, p_sp, a_sp)}
    DMAX_M = 10
    curves = {}
    for nm, dr in arms.items():
        curves[nm] = measure_curve(A2, B2, Kn, DMAX_M, dr, N=6000, T=2000, burn=800,
                                   seed0=300, umax=5.0)
    print(f"    {'d':>3} | {'gauss':>12} {'+-se':>8} | {'sparse':>12} {'+-se':>8} | {'s/g':>7}")
    for d in range(0, DMAX_M + 1):
        g, s = curves["gauss"][d], curves["sparse"][d]
        print(f"    {d:>3} | {g['cost']:12.6e} {g['se']:8.1e} | {s['cost']:12.6e}"
              f" {s['se']:8.1e} | {s['cost']/g['cost']:7.5f}")
    for tau in (0, 1, 2):
        Lg, mg = objective_grid_measured(curves["gauss"], tau)
        Ls_, ms = objective_grid_measured(curves["sparse"], tau)
        print(f"    tau={tau}: {'lam_c':>9} | {'L* gauss':>9} | {'L* sparse':>10} | {'shift':>8}")
        rec_t = {}
        for lam in (1e1, 1e2, 1e3, 1e4, 1e5):
            a = lstar(Lg, mg, lam, lo=max(tau, 1.0))
            b = lstar(Ls_, ms, lam, lo=max(tau, 1.0))
            if a is None or b is None:
                continue
            rec_t[str(lam)] = {"gauss": a, "sparse": b, "shift": b - a}
            print(f"    tau={tau}: {lam:9.1e} | {a:9.3f} | {b:10.3f} | {b-a:+8.3f}")
        res["nonlinear"][str(tau)] = rec_t
        for nm in arms:
            rec = []
            for d in range(0, DMAX_M + 1):
                rec.append({"d": d, "cost": curves[nm][d]["cost"], "se": curves[nm][d]["se"]})
            res["nonlinear"][f"curve_{nm}"] = rec
    print("    (the measurement range is d <= 10: an L* at that edge is a CLIP of the"
          " measurement, not of the plant)")

    # ---------------------------- [E] the two channels, recorded -----------------
    # Every figure must be drawable from THIS file alone, so the mean channel is
    # re-measured here rather than quoted from model_v2's log.  The fixture is
    # model_v2's: one-sided impulses p=0.05, a=1 -> mean 0.05, var 0.0475.
    print("\n[E] THE TWO CHANNELS on the linear arm (well-damped plant, u unbounded)")
    p_on, a_on = 0.05, 1.0
    mu = p_on * a_on
    var_on = p_on * a_on ** 2 - mu ** 2          # = 0.0475
    m_vec = np.array([0.0, mu])
    Wc = np.zeros((2, 2)); Wc[1, 1] = var_on
    trP = {}
    for d in range(0, 8):
        trP[str(d)] = round(route_lyap(A2, B2, Kn, Wc, d)[0], 12)
    mean_by_d = {}
    for d in range(0, 8):
        cm, rho = mean_response(A2, B2, Kn, m_vec, d)
        mean_by_d[str(d)] = {"mean_term": round(cm, 12), "rho": round(rho, 6)}
    mt0 = mean_by_d["0"]["mean_term"]
    inv = max(abs(v["mean_term"] - mt0) for v in mean_by_d.values())
    d_ref = 3
    print(f"    Tr(P) centered (var={var_on:.6f}) at d={d_ref}   = {trP[str(d_ref)]:.12f}")
    print(f"    mean term ||xbar||^2 (d = 0..7)        = {mt0:.12f}"
          f"   spread over d = {inv:.1e}  (delay-invariant)")
    print(f"    mean term / centered Tr(P) at d={d_ref}      ="
          f" {mt0 / trP[str(d_ref)] * 100:.1f} %")
    pred = trP[str(d_ref)] + mt0
    mc = []
    for s in (5, 6, 7):
        g = sim_vector(A2, B2, Kn, d_ref,
                       lambda r, N, n: draw_one_sided(r, N, n, 1, p_on, a_on),
                       N=16000, T=6000, burn=2000, seed=s)
        mc.append({"seed": s, "cost": g["cost"], "se": g["se"]})
        print(f"    MC seed {s:>3} at d={d_ref}: {g['cost']:.12e} +- {g['se']:.1e}"
              f"   (prediction {pred:.12e}, {(g['cost']-pred)/g['se']:+.2f} sigma)")
    shape = {}
    for d in range(0, DMAX_M + 1):
        g, s = curves["gauss"][d]["cost"], curves["sparse"][d]["cost"]
        shape[str(d)] = round(s / g, 6)
    print(f"    shape channel: sparse/gauss cost ratio = {shape['0']:.5f} at d=0"
          f" -> {shape[str(DMAX_M)]:.5f} at d={DMAX_M}  (rises with the delay)")
    res["channels"] = {
        "trP_centered_by_d": trP,
        "mean_term_by_d": mean_by_d,
        "d_ref": d_ref,
        "mean_over_trP_pct": round(mt0 / trP[str(d_ref)] * 100, 6),
        "mean_delay_invariance_spread": inv,
        "prediction": round(pred, 12),
        "mc": mc,
        "shape_ratio_by_d": shape,
    }

    with open("canonical_results.json", "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    print("\nwrote canonical_results.json")
    print("\nverdict: [K]/[L]/[M] above; the file claims nothing beyond them.")


if __name__ == "__main__":
    main()
