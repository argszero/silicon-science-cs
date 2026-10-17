#!/usr/bin/env python3
"""Issue #142 / research v5 -- the SECOND priced system: does the instrument transfer off the
robotics plant?

BOUNDED GOAL (one goal, stated before it runs).  v0-v4 built and tested the identification
instrument on ONE priced system: #116's chunked-policy execution horizon, whose per-delay cost
c(d) comes from an augmented Lyapunov solve of an LQR plant.  The registration's upgrade path says
the direction "generalises across PRICED SYSTEMS (a second, non-robotic instantiation is planned),
which is what makes the level theory+empirics".  This instrument builds that second system and asks
the SAME falsifiable questions against a ground truth that is exact by construction AND cross-checked
by Monte-Carlo.

THE SECOND SYSTEM -- a data-freshness (age-of-information) SAMPLER.  A source emits a value that
drifts as an Ornstein-Uhlenbeck process X (stationary variance s2, rate theta).  A telemetry pipeline
serves the LAST SAMPLED value, so the value a consumer reads has AGE s = (now - last sample).  An
operator chooses the SAMPLING INTERVAL L and pays a PRICE lam per sample (bandwidth/energy), and pays a
STALENESS cost c(s) = E[(X_t - X_{t-s})^2] for the age the consumer reads.  With periodic sampling the
age is uniform on [0, L), so the time-average cost is
    C(L) = (1/L) int_0^L c(s) ds ,     c(s) = 2 s2 (1 - e^{-theta s})   (exact, closed form)
and the objective the operator faces is  J(L) = C(L) + lam/L  -- the SAME priced-objective form as
#116, with lam/L the per-unit-time price of sampling.

WHY IT IS A DIFFERENT MECHANISM, NOT A PARAMETER SWAP.  c(s) here is a SATURATING exponential (bounded,
no wall, an interior optimum that vanishes for large lam), not the LQR curve's near-linear-then-wall
shape; the state is OBSERVED, not controlled; there is no LQR plant, no control law, and no stability
margin.  The horizon's bound is a HARDWARE MINIMUM INTERVAL (floor) and a STALENESS TOLERANCE (ceiling)
-- a different boundary mechanism from a stability margin.

WHAT IS MEASURED (the same questions the first system was asked):
  [A] the envelope identity   G := L* J - lam = int_0^{L*} c   (with J = C(L*) + lam/L*)
  [B] the price sweep recovers c pointwise; its error is a SPAN (quadrature) error, so its target is
      the span MEAN of c, not the point     (this is P1, tested on the second system)
  [C] the identifiability boundary (P3): at an interior optimum the single-point marginal identity
      c(L*) = J holds (no differencing); at a floor/ceiling-pinned cell it does not
  [D] the system-identification route (v4): the raw SOURCE log identifies (theta, s2), and c(s) is a
      deterministic functional of them -- does the route reach the same object on THIS system?

GROUND TRUTH IS EXACT BY CONSTRUCTION (the closed forms above) and is cross-checked by simulating the
actual sampler (Monte-Carlo), so the truth is not assumed.

CONTROLS THAT MUST FIRE: (i) a 1% perturbation of lam must break [A]; (ii) a cell pinned at the floor or
ceiling must not satisfy [C]'s single-point identity.

python3 spike_ident_v5.py                 (writes spike_ident_v5_results.json)
python3 spike_ident_v5.py --selftest      (plants; must all fire)
"""
import json
import math
import os
import sys
import tempfile

import numpy as np
from scipy.signal import lfilter

DELTA = 0.05                 # L-grid resolution (the instrument's own resolution)
LMIN, LMAX = 0.5, 20.0       # hardware minimum interval (floor) / staleness tolerance (ceiling)
N_PRICES = 40
SEED = 11
BUILD = "python %s / numpy %s" % (sys.version.split()[0], np.__version__)
# The interpreter PATH is not in BUILD.  `sys.executable` is an INVOCATION coordinate -- it changes
# with how the interpreter was reached (the /usr/bin/python3 shim reports the shim, the framework
# binary reports itself), so an artefact carrying it is reproduced only under the exact invocation
# that wrote it: measured 2026-10-16, v3/v4/v5 did NOT all reproduce under one command, and v3's
# shipped copy recorded a DIFFERENT interpreter than v4/v5's (Class 297).  Nothing that enters a
# comparison depends on the path, so the path stays out of the artefact; the environment the
# numbers were produced in is stated in README.md instead.

SOURCES = {
    "ou theta=1.0 s2=1.0": (1.0, 1.0),
    "ou theta=3.0 s2=1.0": (3.0, 1.0),
    "ou theta=0.5 s2=2.0": (0.5, 2.0),
}


# ------------------------------------------------------- the second system's exact ground truth
def c_exact(theta, s2, s):
    """The staleness cost of acting on a value of age s: E[(X_t - X_{t-s})^2] for an OU source."""
    return 2.0 * s2 * (1.0 - math.exp(-theta * s))


def C_exact(theta, s2, L):
    """(1/L) int_0^L c(s) ds -- the time-average staleness cost under periodic sampling of interval L."""
    if L <= 0:
        return 0.0
    return 2.0 * s2 * (1.0 - (1.0 - math.exp(-theta * L)) / (theta * L))


def G_exact(theta, s2, L):
    """L * C(L) = int_0^L c(s) ds -- the envelope quantity's exact target."""
    return 2.0 * s2 * (L - (1.0 - math.exp(-theta * L)) / theta)


def span_mean(theta, s2, a, b):
    """(1/(b-a)) int_a^b c -- the sweep's CORRECT target (the point value is the biased one)."""
    if b <= a:
        return c_exact(theta, s2, a)
    return 2.0 * s2 * (1.0 - (math.exp(-theta * a) - math.exp(-theta * b)) / (theta * (b - a)))


# ------------------------------------------------------------------ the priced objective + the log
def make_system(theta, s2, delta=DELTA):
    K = int(round((LMAX - LMIN) / delta))
    Ls = LMIN + delta * np.arange(K + 1)
    Cs = np.array([C_exact(theta, s2, float(L)) for L in Ls])
    lam_c = 2.0 * s2 / theta                     # the price above which the optimum runs to the ceiling
    lams = lam_c * np.logspace(-2.0, 2.0, N_PRICES)
    return Ls, Cs, lams, lam_c


def classify(Lstar, delta=DELTA):
    if abs(Lstar - LMIN) <= delta + 1e-9:
        return "floor"
    if abs(Lstar - LMAX) <= delta + 1e-9:
        return "ceiling"
    return "interior"


def run(theta, s2, lam_perturb=1.0, delta=DELTA):
    """One cell per price: the operator's chosen interval L*, the achieved average cost J, and the
    envelope quantity G = L*J - lam the deployment's dashboard already shows."""
    Ls, Cs, lams, lam_c = make_system(theta, s2, delta)
    rows = []
    for lam in lams:
        obj = Cs + lam / Ls
        i = int(np.argmin(obj))
        Lstar = float(Ls[i])
        J = float(Cs[i] + lam / Lstar)
        G = Lstar * J - lam * lam_perturb
        rows.append({"lam": float(lam), "Lstar": Lstar, "J": J, "G": G,
                     "class": classify(Lstar, delta),
                     "c_true": c_exact(theta, s2, Lstar),
                     "span_true": span_mean(theta, s2, 0.0, Lstar),
                     "I_true": G_exact(theta, s2, Lstar)})
    return rows, lam_c


def rel(a, b):
    if not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return math.inf
    return abs(a - b) / abs(b)


def summarize(cells):
    """[A] identity error; [C] the single-point marginal identity, interior vs pinned apart; [B] sweep."""
    res = {"identity": [], "marginal_interior": [], "marginal_pinned": [], "sweep": []}
    interior = [r for r in cells if r["class"] == "interior"]
    for r in cells:
        res["identity"].append(rel(r["G"], r["I_true"]))
        e = rel(r["J"], r["c_true"])
        (res["marginal_interior"] if r["class"] == "interior" else res["marginal_pinned"]).append(e)
    interior = sorted(interior, key=lambda r: r["Lstar"])
    for k in range(1, len(interior) - 1):
        a, m, b = interior[k - 1], interior[k], interior[k + 1]
        if b["Lstar"] - a["Lstar"] < 1e-9:
            continue
        slope = (b["G"] - a["G"]) / (b["Lstar"] - a["Lstar"])
        tgt_span = (b["I_true"] - a["I_true"]) / (b["Lstar"] - a["Lstar"])
        res["sweep"].append({"err_vs_spanmean": rel(slope, tgt_span),
                             "err_vs_point": rel(slope, m["c_true"]),
                             "span": b["Lstar"] - a["Lstar"]})
    return res


def stat(v):
    v = [x for x in v if x != math.inf]
    if not v:
        return None
    v = np.array(v)
    return {"n": int(v.size), "median": float(np.median(v)), "worst": float(v.max())}


# ------------------------------------------------------------------ the second system's OWN sampler (MC)
def ou_path(theta, s2, n, dt, seed, burn_mult=40):
    """An EXACT OU discretisation, vectorised: x_k = a x_{k-1} + q z_k is an AR(1), so it is an
    lfilter (the naive python loop over 10^5-10^6 steps is what made an earlier draft time out)."""
    rng = np.random.default_rng(seed)
    a = math.exp(-theta * dt)
    q = math.sqrt(s2 * (1.0 - a * a))
    burn = int(burn_mult / max(theta * dt, 1e-9))
    z = rng.standard_normal(n + burn)
    return lfilter([q], [1.0, -a], z)[burn:]


def simulate_sampler(theta, s2, L, dt=0.005, n=2000000, seed=SEED):
    """THE ACTUAL SAMPLER, simulated: an exact OU source, sampled every L, with the consumer reading
    the stale value.  Returns the time-average staleness error -- C(L)'s independent value.  n is set so
    the EFFECTIVE sample size (n * theta * dt, the number of correlation times) is large enough that the
    Monte-Carlo error is well under the bar -- the pairs are far from independent."""
    y = ou_path(theta, s2, n, dt, seed)
    step = max(1, int(round(L / dt)))
    k = np.arange(n)
    served_idx = k - (k % step)                       # index of the last sample at or before k
    err = (y - y[served_idx]) ** 2
    return float(np.mean(err))


def mc_c(theta, s2, s, dt=0.01, n=300000, seed=SEED):
    """E[(X_t - X_{t-s})^2] measured, for the closed form's independent check."""
    y = ou_path(theta, s2, n, dt, seed)
    back = int(round(s / dt))
    if back >= n:
        return float("nan")
    d = y[back:] - y[:-back]
    return float(np.mean(d * d))


def identify_source(X, dt):
    """[D] the system-identification route on the SECOND system: fit an AR(1) to the raw source log,
    recover (theta, s2) -- and c(s) is then a deterministic functional of them.  The AR(1) here is the
    exact OU discretisation with innovation variance q^2 = s2(1-a^2), so the STATIONARY variance is s2
    itself -- dividing by (1-a^2) again inflates it by 1/(1-a^2) (measured 50x before this was caught)."""
    x0, x1 = X[:-1], X[1:]
    ahat = float(np.dot(x0, x1) / np.dot(x0, x0))
    theta_hat = -math.log(ahat) / dt
    s2_hat = float(np.var(x1))
    return theta_hat, s2_hat


# ------------------------------------------------------------------ selftest
def selftest():
    ok, checks = 0, []

    def check(name, cond, detail=""):
        nonlocal ok
        checks.append({"plant": name, "fired": bool(cond), "detail": detail})
        if cond:
            ok += 1

    theta, s2 = SOURCES["ou theta=1.0 s2=1.0"]

    # 1. the closed-form staleness curve matches the SIMULATED source (truth not assumed)
    e = []
    for s in (0.5, 1.0, 2.0, 4.0):
        e.append(rel(mc_c(theta, s2, s), c_exact(theta, s2, s)))
    check("plant-closed-form-c-matches-the-simulated-source", max(e) < 5e-2,
          "max rel err over 4 ages = %.3g" % max(e))

    # 2. the closed-form objective matches the SIMULATED sampler (the system, not just its formula)
    e = []
    for L in (1.0, 2.0, 5.0):
        e.append(rel(simulate_sampler(theta, s2, L), C_exact(theta, s2, L)))
    check("plant-closed-form-C-matches-the-simulated-sampler", max(e) < 5e-2,
          "max rel err over 3 intervals = %.3g" % max(e))

    rows, lam_c = run(theta, s2)
    S = summarize(rows)
    ident = stat(S["identity"])

    # 3. [A] the envelope identity holds exactly on the second system
    check("plant-envelope-identity-holds-on-the-second-system",
          ident is not None and ident["worst"] < 1e-12,
          "identity median=%.3g worst=%.3g" % (ident["median"], ident["worst"]))

    # 4. [A] the control that must fire: a 1% perturbation of lam breaks the identity
    rows_p, _ = run(theta, s2, lam_perturb=1.01)
    ident_p = stat(summarize(rows_p)["identity"])
    check("plant-envelope-identity-control-fires-under-lam-1pct",
          ident_p is not None and ident_p["median"] > 1e-3,
          "perturbed identity median=%.3g (0 means an INERT control)" % ident_p["median"])

    # 5. [C] the single-point marginal identity reads c at an INTERIOR optimum -- to the grid's own FOC
    #    resolution (an O(delta) residual), and it SHRINKS as the grid is refined: the identity is a
    #    CONTINUOUS-optimum statement, and the grid step is the only error it carries here.
    mi = stat(S["marginal_interior"])
    rows_f, _ = run(theta, s2, delta=DELTA / 4.0)
    mi_f = stat(summarize(rows_f)["marginal_interior"])
    check("plant-marginal-identity-reads-c-at-an-interior-optimum-and-refines-with-the-grid",
          mi is not None and mi["median"] < 5 * DELTA and mi_f is not None
          and mi_f["median"] < mi["median"],
          "interior marginal median=%.3g worst=%.3g (delta=%.3g -> refined median=%.3g)" %
          (mi["median"], mi["worst"], DELTA, mi_f["median"]))

    # 6. [C] and it FAILS at a pinned cell (the boundary) -- the control that must fire
    mp = stat(S["marginal_pinned"])
    check("plant-marginal-identity-fails-at-a-pinned-cell",
          mp is not None and mi is not None and mp["median"] > 10 * max(mi["median"], 1e-15),
          "pinned marginal median=%.3g vs interior %.3g (n_pinned=%d)" %
          (mp["median"], mi["median"], mp["n"]))

    # 7. [B] the sweep's error is a SPAN error: its target is the span MEAN, not the point
    ev_s = stat([d["err_vs_spanmean"] for d in S["sweep"]])
    ev_p = stat([d["err_vs_point"] for d in S["sweep"]])
    check("plant-sweep-targets-the-span-mean-not-the-point",
          ev_s is not None and ev_p is not None and ev_p["median"] > 100 * ev_s["median"],
          "sweep median err: span-mean=%.3g point=%.3g (ratio %.3g)" %
          (ev_s["median"], ev_p["median"], ev_p["median"] / max(ev_s["median"], 1e-300)))

    # 8. the system has BOTH regimes (interior optima AND a ceiling), i.e. the boundary is reachable
    n_int = sum(1 for r in rows if r["class"] == "interior")
    n_ceil = sum(1 for r in rows if r["class"] == "ceiling")
    check("plant-both-regimes-exist-interior-and-pinned",
          n_int > 0 and n_ceil > 0, "interior=%d ceiling=%d floor=%d" %
          (n_int, n_ceil, sum(1 for r in rows if r["class"] == "floor")))

    # 9. [D] the system-identification route reaches the SAME object on the second system:
    #    fit (theta, s2) from the raw source log, reconstruct c(s), compare to the closed form.
    dt = 0.01
    X = ou_path(theta, s2, 400000, dt, SEED)
    th_hat, s2_hat = identify_source(X, dt)
    ce = [rel(c_exact(th_hat, s2_hat, s), c_exact(theta, s2, s)) for s in (0.5, 1.0, 2.0, 4.0)]
    check("plant-system-identification-reaches-the-same-object-on-the-second-system",
          max(ce) < 5e-2 and abs(th_hat - theta) / theta < 5e-2,
          "theta=%.4f (true %.2f) s2=%.4f (true %.2f); max c rel err=%.3g" %
          (th_hat, theta, s2_hat, s2, max(ce)))

    # 10. determinism of the measurement path
    r1, _ = run(theta, s2)
    r2, _ = run(theta, s2)
    same = all(abs(a_["G"] - b_["G"]) < 1e-15 and abs(a_["J"] - b_["J"]) < 1e-15
               for a_, b_ in zip(r1, r2))
    check("plant-measurement-is-deterministic", same, "two identical runs agree to <1e-15")

    # 11. the pooling trap (Class 269): G's slope is defined over the L* of ONE curve, so pooling the
    #     ROWS of two sources and re-differencing subtracts two different curves' G.  Measured as the
    #     control that must fire: the wrong pooling's error is far larger than the correct per-source one.
    r1b, _ = run(*SOURCES["ou theta=1.0 s2=1.0"])
    r2b, _ = run(*SOURCES["ou theta=0.5 s2=2.0"])
    wrong = summarize(r1b + r2b)                       # pools the rows -> cross-source differencing
    right = summarize(r1b)["sweep"] + summarize(r2b)["sweep"]
    w_worst = stat([d["err_vs_point"] for d in wrong["sweep"]])
    r_worst = stat([d["err_vs_point"] for d in right])
    check("plant-pooled-sweep-must-not-difference-across-sources",
          w_worst is not None and r_worst is not None and w_worst["worst"] > 3 * r_worst["worst"],
          "wrong pooled worst=%.3g vs correct per-source worst=%.3g" %
          (w_worst["worst"], r_worst["worst"]))

    print(json.dumps({"plants": checks, "passed": ok, "total": len(checks)}, indent=2))
    return 0 if ok == len(checks) else 1


# ------------------------------------------------------------------ main
def measure_all():
    per_source = {}
    pool = {"identity": [], "marginal_interior": [], "marginal_pinned": [],
            "sweep_vs_spanmean": [], "sweep_vs_point": []}
    for name in sorted(SOURCES):
        theta, s2 = SOURCES[name]
        rows, lam_c = run(theta, s2)
        S = summarize(rows)          # the sweep is differenced WITHIN this source only -- see below
        per_source[name] = {
            "theta": theta, "s2": s2, "lam_critical": lam_c,
            "cells": {"total": len(rows),
                      "interior": sum(1 for r in rows if r["class"] == "interior"),
                      "floor": sum(1 for r in rows if r["class"] == "floor"),
                      "ceiling": sum(1 for r in rows if r["class"] == "ceiling")},
            "identity": stat(S["identity"]),
            "marginal_interior": stat(S["marginal_interior"]),
            "marginal_pinned": stat(S["marginal_pinned"]),
            "sweep_vs_spanmean": stat([d["err_vs_spanmean"] for d in S["sweep"]]),
            "sweep_vs_point": stat([d["err_vs_point"] for d in S["sweep"]]),
            "controls": {},
        }
        # the pool takes each source's OWN sweep, never a pooled re-difference: G's slope is defined
        # across the L* of ONE curve, so pooling the ROWS and re-differencing (the first draft's
        # sketch -- Class 269, a group-by that drops a key) would subtract two different sources' G.
        pool["identity"] += S["identity"]
        pool["marginal_interior"] += S["marginal_interior"]
        pool["marginal_pinned"] += S["marginal_pinned"]
        pool["sweep_vs_spanmean"] += [d["err_vs_spanmean"] for d in S["sweep"]]
        pool["sweep_vs_point"] += [d["err_vs_point"] for d in S["sweep"]]
        # controls, reported as measured
        rp, _ = run(theta, s2, lam_perturb=1.01)
        per_source[name]["controls"]["lam_1pct_identity"] = stat(summarize(rp)["identity"])
        # [D] on this source
        dt = 0.01
        X = ou_path(theta, s2, 400000, dt, SEED)
        th_hat, s2_hat = identify_source(X, dt)
        per_source[name]["system_id"] = {
            "theta_hat": th_hat, "s2_hat": s2_hat,
            "theta_rel_err": abs(th_hat - theta) / theta,
            "max_c_rel_err": max(rel(c_exact(th_hat, s2_hat, s), c_exact(theta, s2, s))
                                 for s in (0.5, 1.0, 2.0, 4.0)),
        }
    return {"per_source": per_source,
            "pooled": {k: stat(v) for k, v in pool.items()}}


def write_json(path, obj):
    """Stage to a temp file and os.replace: a truncate-then-fail write is not atomic."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-v5-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main():
    R = {"build": BUILD, "grid": {"delta_L": DELTA, "L_min": LMIN, "L_max": LMAX,
                                  "n_prices": N_PRICES, "seed": SEED}}
    R.update(measure_all())
    print(json.dumps(R, indent=2, sort_keys=True))
    write_json("spike_ident_v5_results.json", R)
    return R


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
