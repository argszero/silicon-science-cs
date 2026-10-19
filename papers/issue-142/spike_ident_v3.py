#!/usr/bin/env python3
"""Issue #142 / research v3 -- P4's FIRST HALF: the moments route a practitioner would try.

BOUNDED GOAL (one goal, stated before it runs).  The registration's P4 is that the two routes
a practitioner would try instead of a price sweep -- higher moments of the tracking error, and
system identification on the residual dynamics -- **address a different object** and fail on the
same logs.  v0/v1/v2 never tested it.  This instrument tests the MOMENTS half, on the same cells
v2 already uses, against exact ground truth by construction.

WHY THE MOMENTS ROUTE HAS EXACTLY TWO MODEL-FREE READINGS, and what each estimates.
A deployment that logs its own trajectory can form, at its visited operating point L*:
  (M1) the MEAN tracking cost over the chunk,  C(L*) = (1/L*) int_0^{L*} c(tau+s) ds.
       On the deployment's own log this is a logged number:  J = C(L*) + lam/L*, so
       M1 := J - lam/L*  reads the mean cost with no model and no sweep.
  (M2) the WITHIN-CHUNK PROFILE: the mean cost of each phase j = 1..L* of the chunk, i.e. the
       per-step telemetry bucketed by the chunk phase, differenced:
       M2 := (p(L*) - p(1)) / (L* - 1).
Both are functionals of the SAME object the deployment is already producing -- a cost level at the
visited point -- and M2 additionally assumes that the per-phase profile is, up to an additive
constant, the frozen-delay cost curve c(tau+j).  The sweep's claim is different in kind: by
Leibniz dG/dL = c(tau+L), i.e. the curvature is a DERIVATIVE with respect to the operating point.
So P4's M half is falsifiable in one line: if either model-free reading recovers c(tau+L*), P4 is
refuted for the moments route; if neither does, the route addresses a level, not the curvature.

WHAT THE PROFILE ACTUALLY IS (pre-registered here because it decides the verdict).  The periodic
orbit's per-phase cost is not the frozen-delay steady cost: at each chunk boundary the loop is
re-planned, so the state is largest right after the boundary and smallest around the middle -- the
profile is U-SHAPED where c(tau+j) rises monotonically (measured: 55.2 -> 38.3 -> 48.9 against
c rising 21.3 -> 78.6 on the near-margin plant; only the well-damped plant is near-constant).
M2 therefore has the WRONG SIGN wherever the U is pronounced, and the instrument reports the
sign agreement as a countable fraction -- a direction claim, not a magnitude claim, so it does not
depend on a threshold of ours.

THE PROFILE IS COMPUTED, NOT APPROXIMATED.  p(j) is the exact mean of ||x||^2 over phase j of the
periodic chunked loop (delay tau+j within the chunk), by the covariance recursion over the period
-- the same quantity #116's model_v3 calls its "exact periodic (chunked) cost", read per phase
instead of averaged.  Its mean is certified against an INDEPENDENT route (a seeded Monte-Carlo
simulation of the same loop) and against the quasi-static proxy whose <=3e-3 agreement #116
measured.  Nothing here is fitted.

GROUND TRUTH IS EXACT BY CONSTRUCTION: c(d) is the plant's own per-delay cost from the augmented
Lyapunov solve (v0's machinery, unchanged); the target is c(tau+L*), the point value.

A CONTROL THAT MUST FIRE.  A CENTRED DIFFERENCE OF G across the same price ladder (the sweep) is
carried as the control route: it must track c across the block's interior cells.  If the object
statistic were blind, the sweep's reading would look like the moments routes' and the test would
prove nothing.

python3 spike_ident_v3.py                (writes spike_ident_v3_results.json)
python3 spike_ident_v3.py --selftest     (plants; must all fire)
"""
import json
import os
import sys
import tempfile

import numpy as np

import spike_ident_v0 as v0
import spike_ident_v1 as v1
import spike_ident_v2 as v2

DELTA = v0.DELTA
BUILD = "python %s / numpy %s" % (sys.version.split()[0], np.__version__)
# The interpreter PATH is not in BUILD.  `sys.executable` is an INVOCATION coordinate -- it changes
# with how the interpreter was reached (the /usr/bin/python3 shim reports the shim, the framework
# binary reports itself), so an artefact carrying it is reproduced only under the exact invocation
# that wrote it: measured 2026-10-16, v3/v4/v5 did NOT all reproduce under one command, and v3's
# shipped copy recorded a DIFFERENT interpreter than v4/v5's (Class 297).  Nothing that enters a
# comparison depends on the path, so the path stays out of the artefact; the environment the
# numbers were produced in is stated in README.md instead.
PERIODS = 400          # covariance-recursion passes over the period (converged long before)
MIN_N = 3              # a correlation over fewer than 3 cells is UNDEFINED, not zero
TOLERANCE = 1e-12      # determinism: two runs must agree bit-for-bit
_CURVE = {}            # plant name -> (c, dmax), filled by cells_for_plant / measure_all


# ------------------------------------------------------------------ the periodic chunked loop
def _frame(A, B, K, D, d):
    """One step of z_t = [x_t; x_{t-1}; ...; x_{t-D}] with u_t = -K x_{t-d}  (#116's model_v3)."""
    n = A.shape[0]
    m = (D + 1) * n
    F = np.zeros((m, m))
    F[0:n, 0:n] = A
    F[0:n, d * n:(d + 1) * n] -= B @ K
    for i in range(1, D + 1):
        F[i * n:(i + 1) * n, (i - 1) * n:i * n] = np.eye(n)
    return F


def period_frames(A, B, K, tau, L):
    """The L phases of a chunk of length L at latency tau: ages tau+1 .. tau+L."""
    D = int(round(tau + L))
    return [_frame(A, B, K, D, int(round(tau + j))) for j in range(1, int(L) + 1)], D


def spectral_radius(A, B, K, tau, L):
    """The EXACT feasibility criterion: the spectral radius of the period product."""
    Fs, D = period_frames(A, B, K, tau, L)
    m = Fs[0].shape[0]
    M = np.eye(m)
    for F in Fs:
        M = F @ M
    return float(np.max(np.abs(np.linalg.eigvals(M))))


def phase_profile(A, B, K, W, tau, L, periods=PERIODS):
    """The exact mean of ||x||^2 at each phase of the periodic chunked loop.

    Returns (profile, rho) with profile of length L, or (None, rho) where rho >= 1 (infeasible).
    NOTE ON A PLATFORM CERTIFICATE: this build's BLAS raises a SPURIOUS FPE warning
    ("divide by zero encountered in matmul") for some matrix sizes even when every operand is
    finite -- measured, with max|P| = 0 in the raising call.  So finiteness is certified BY VALUE
    below, never by a warning flag, which a platform can raise with nothing behind it.
    """
    L = int(L)
    if L < 1:
        return None, float("inf")
    rho = spectral_radius(A, B, K, tau, L)
    if not np.isfinite(rho) or rho >= 1.0:
        return None, rho
    Fs, D = period_frames(A, B, K, tau, L)
    n = A.shape[0]
    m = (D + 1) * n
    Wb = np.zeros((m, m))
    Wb[0:n, 0:n] = W
    P = np.zeros((m, m))
    for _ in range(periods):
        for F in Fs:
            P = F @ P @ F.T + Wb
    prof = []
    for F in Fs:
        prof.append(float(np.trace(P[0:n, 0:n])))
        P = F @ P @ F.T + Wb
    if not all(np.isfinite(v) and v >= 0 for v in prof):
        return None, rho
    return prof, rho


def mc_chunked(A, B, K, W, tau, L, T=200000, burn=20000, seed=0):
    """An ALGORITHMICALLY INDEPENDENT route to the phase profile: a Monte-Carlo simulation of the
    same loop (u_t = -K x_{t-d}, d cycling tau+1..tau+L).  Used only as the certificate."""
    L = int(L)
    D = int(round(tau + L))
    n = A.shape[0]
    rng = np.random.default_rng(seed)
    ev, V = np.linalg.eigh(W)
    ev = np.clip(ev, 0.0, None)
    Lr = V @ np.diag(np.sqrt(ev))
    hist = np.zeros((D + 1, n))
    acc = np.zeros(L)
    cnt = np.zeros(L)
    for t in range(T + burn):
        j = t % L                      # phase 0..L-1  -> delay tau+j+1
        d = int(round(tau + j + 1))
        u = -K @ hist[d]
        xn = A @ hist[0] + B @ u + Lr @ rng.standard_normal(n)
        if t >= burn:
            acc[j] += float(xn @ xn)
            cnt[j] += 1
        hist = np.vstack([xn, hist[:-1]])
    return list(acc / np.maximum(cnt, 1))


# ------------------------------------------------------------------ the cells and the routes
def cells_for_plant(name, c, dmax):
    """The same cells v2 uses (its predictor's labels included), with the plant's dynamics attached
    so the phase profile can be computed at the visited operating point."""
    A, B, Q, R = v0.make_plants()[name]
    K, _ = v0.lqr_gain(A, B, Q, R)
    W = np.eye(A.shape[0])
    _CURVE[name] = (c, dmax)
    cs = v2.price_cells(c, dmax)
    for x in cs:
        x["plant"] = name
    return cs, (A, B, K, W)


def profile_at(A, B, K, W, tau, L, cache):
    key = (id(A), float(tau), int(L))
    if key not in cache:
        cache[key] = phase_profile(A, B, K, W, tau, L)
    return cache[key]


def route_estimates(cells, dyn, cache):
    """Attach to every cell the three estimates that claim to be c(tau+L*):
       M1  the logged mean cost        J - lam/L*
       M2  the within-chunk slope      (p(L*) - p(1)) / (L*-1)          [None if infeasible/short]
       SW  the sweep (control)         a centred difference of G across neighbouring prices
    """
    A, B, K, W = dyn
    for x in cells:
        L = int(round(x["Lstar"]))
        x["M1"] = x["J"] - x["lam"] / x["Lstar"]
        prof, rho = profile_at(A, B, K, W, x["tau"], L, cache)
        x["rho"] = rho
        if prof is None or L < 2:
            x["M2"] = None
            x["profile_rho"] = None
            x["profile_flatness"] = None
        else:
            x["M2"] = (prof[-1] - prof[0]) / (L - 1.0)
            x["profile_rho"] = float(sum(prof) / len(prof)) / x["c_true"] if x["c_true"] > 0 else None
            x["profile_flatness"] = float(max(prof) / min(prof)) if min(prof) > 0 else None
            x["profile"] = [float(v) for v in prof]
        # the LOCAL slope of the ground truth at the visited point: the direction the estimate is
        # claiming.  Compared against sign(M2) cell by cell -- a direction test, not a magnitude one.
        x1 = v0.interp(_CURVE[x["plant"]][0], _CURVE[x["plant"]][1], x["tau"] + x["Lstar"])
        x0 = v0.interp(_CURVE[x["plant"]][0], _CURVE[x["plant"]][1], x["tau"] + x["Lstar"] - 1.0)
        x["c_slope"] = (x1 - x0) if np.isfinite(x1) and np.isfinite(x0) else None
        x["M2_sign_agrees"] = (None if x.get("M2") is None or x["c_slope"] in (None, 0.0)
                               else bool(np.sign(x["M2"]) == np.sign(x["c_slope"])))
    # the sweep control: G differenced across the block's own ladder, at the MIDDLE cell
    by_block = {}
    for x in cells:
        by_block.setdefault((x["plant"], x["tau"]), []).append(x)
    for _, cs in by_block.items():
        cs.sort(key=lambda z: z["Lstar"])
        for i in range(1, len(cs) - 1):
            a, m, b = cs[i - 1], cs[i], cs[i + 1]
            span = b["Lstar"] - a["Lstar"]
            m["SW"] = (b["G"] - a["G"]) / span if span > 1e-12 else None
    for x in cells:
        x.setdefault("SW", None)
    return cells


def rel(a, b):
    if a is None or b is None or not np.isfinite(a) or not np.isfinite(b) or b == 0:
        return None
    return abs(a - b) / abs(b)


def err_stat(cells, key, label=None):
    """Relative error of one route against the exact point value, over an optional label subset.
    Only cells where the route is DEFINED contribute; the count is reported either way."""
    sub = [x for x in cells if (label is None or x["label"] == label)]
    vals = [rel(x[key], x["c_true"]) for x in sub]
    have = [v for v in vals if v is not None]
    out = {"n_cells": len(sub), "n_defined": len(have)}
    if not have:
        return out
    a = np.array(have)
    out.update({"median": float(np.median(a)), "worst": float(a.max()), "best": float(a.min())})
    return out


def pearson(xs, ys):
    """Correlation over the cells where BOTH are defined; UNDEFINED (None) when fewer than MIN_N
    cells carry a value or when either series is constant -- a 0 over a constant series is a 0/0
    cell, not a measured zero."""
    pairs = [(a, b) for a, b in zip(xs, ys) if a is not None and b is not None]
    if len(pairs) < MIN_N:
        return None, len(pairs)
    x = np.array([p[0] for p in pairs], dtype=float)
    y = np.array([p[1] for p in pairs], dtype=float)
    if x.std() < 1e-15 or y.std() < 1e-15:
        return None, len(pairs)
    return float(np.corrcoef(x, y)[0, 1]), len(pairs)


def point_invariance(cells):
    """THE STRUCTURAL CERTIFICATE, measured.  Every quantity a deployment logs is a function of the
    VISITED OPERATING POINT L* -- so two prices that select the same L* produce byte-identical
    telemetry (and identical G, since G = L* C(L*)), while two prices that select different L*
    produce different telemetry.  The sweep is not a smarter moment: it is the only route that
    DIFFERENCES ACROSS operating points, and this certificate shows where the information lives."""
    groups = {}
    for x in cells:
        groups.setdefault((x["plant"], x["tau"], x["Lstar"]), []).append(x)
    multi = [g for g in groups.values() if len(g) > 1 and all(y["M2"] is not None for y in g)]
    spread = {"n_groups": len(multi)}
    if multi:
        spread["max_price_span_within_a_group"] = float(max(max(y["lam"] for y in g)
                                                           - min(y["lam"] for y in g) for g in multi))
        # RELATIVE spreads: an absolute tolerance on a quantity that spans five decades (G runs to
        # 1e5 while the price ladder spans 1e-2..1e5) is not a tolerance, so each spread is scaled
        # by the group's own magnitude -- the certificate is the same-in-the-last-ulp claim, stated
        # in the only units in which it can be stated.
        for key in ("M1", "M2", "G", "profile_rho"):
            worst = 0.0
            for g in multi:
                vals = [y[key] for y in g]
                scale = max(abs(v) for v in vals)
                if scale > 0:
                    worst = max(worst, (max(vals) - min(vals)) / scale)
            spread["max_rel_%s_spread_within_a_group" % key] = float(worst)
    per_block = {}
    for x in cells:
        per_block.setdefault((x["plant"], x["tau"]), set()).add(x["Lstar"])
    spread["distinct_visited_points_per_block"] = sorted(len(v) for v in per_block.values())
    return spread


def direction_test(cells, key="M2", label=None):
    """The DIRECTION claim, counted: of the cells where the estimate is defined and the ground
    truth's local slope is non-zero, how many carry the right sign?  For M1 this is trivially all
    of them (both are positive costs), which is exactly why a level cannot be wrong about a
    direction and a slope can -- so it is reported for M2 and stated as trivial for M1."""
    sub = [x for x in cells if x.get(key) is not None and x.get("c_slope") not in (None, 0.0)
           and (label is None or x["label"] == label)]
    agree = sum(1 for x in sub if np.sign(x[key]) == np.sign(x["c_slope"]))
    return {"n_defined": len(sub), "n_right_sign": agree,
            "fraction_right_sign": (agree / len(sub)) if sub else None}


def object_test(cells, key, interior_only=True):
    """P4's object statistic: over each (plant, tau) block, does the route's estimate TRACK the
    exact c across the prices?  Read on the INTERIOR cells only -- where the visited point moves
    with the price -- and reported with the n it was taken over, per block."""
    out = []
    blocks = {}
    for x in cells:
        blocks.setdefault((x["plant"], x["tau"]), []).append(x)
    for key_, cs in sorted(blocks.items()):
        sub = [x for x in cs if (not interior_only or x["label"] == "interior")]
        r, n = pearson([x[key] for x in sub], [x["c_true"] for x in sub])
        out.append({"plant": key_[0], "tau": key_[1], "n": n, "r": r,
                    "n_interior": sum(1 for x in cs if x["label"] == "interior")})
    rs = [o["r"] for o in out if o["r"] is not None]
    return {"per_block": out,
            "blocks_with_a_defined_r": len(rs),
            "median_r": float(np.median(rs)) if rs else None,
            "min_r": float(min(rs)) if rs else None}


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

    # 1. feasibility is decided by the period product's spectral radius, not by guesswork
    A1, B1, Q1, R1 = v0.make_plants()["double-int R=1"]
    K1, _ = v0.lqr_gain(A1, B1, Q1, R1)
    W1 = np.eye(A1.shape[0])
    p_inf, rho_inf = phase_profile(A1, B1, K1, W1, 0.0, 20)
    check("plant-infeasible-loop-is-refused", p_inf is None and rho_inf >= 1.0,
          "rho=%.4f (this plant's chunk of 20 is past its margin)" % rho_inf)

    # 2. the profile's MEAN is the loop's own average cost -- certified against an INDEPENDENT
    #    Monte-Carlo route (a different algorithm, a different failure mode)
    prof, rho = phase_profile(A, B, K, W, 0.0, 5)
    mc = mc_chunked(A, B, K, W, 0.0, 5, T=400000, burn=40000, seed=11)
    mp, mm = sum(prof) / len(prof), sum(mc) / len(mc)
    rel_mc = abs(mp - mm) / mm
    check("plant-recursion-agrees-with-an-independent-monte-carlo", rel_mc < 0.02,
          "recursion=%.6f mc=%.6f rel=%.2e" % (mp, mm, rel_mc))

    # 3. the profile's mean is the QUASI-STATIC proxy to the accuracy #116 measured (<=3e-3 is
    #    claimed for the integral surrogate; this is that claim read per phase)
    c, dmax = v1.plants_with_curves()["double-int R=100"]
    tau, L = 0.0, 5
    ex = [v0.interp(c, dmax, tau + j) for j in range(1, int(L) + 1)]
    ep = sum(ex) / len(ex)
    rel_proxy = abs(mp - ep) / ep
    check("plant-profile-mean-is-the-quasi-static-proxy", rel_proxy < 0.05,
          "profile_mean=%.4f proxy_mean=%.4f rel=%.2e" % (mp, ep, rel_proxy))

    # 4. the profile SLOPES AGAINST the frozen-delay curve -- the whole reason M2 cannot work.
    #    The test is a SIGN contrast (a direction claim), measured on the plant whose periodic
    #    orbit is most pronounced: the near-margin double integrator, chunk 10.
    p_r1, rho_r1 = phase_profile(A1, B1, K1, W1, 0.0, 6)
    c_r1, dmax_r1 = v1.plants_with_curves()["double-int R=1"]
    ex_r1 = [v0.interp(c_r1, dmax_r1, 0.0 + j) for j in range(1, 7)]
    m2_r1 = (p_r1[-1] - p_r1[0]) / 5.0
    slope_c_r1 = ex_r1[-1] - ex_r1[0]
    check("plant-within-chunk-slope-has-the-opposite-sign-to-the-curve",
          m2_r1 < 0 and slope_c_r1 > 0,
          "M2=%.4f (profile %.2f -> %.2f) while c rises %.2f -> %.2f" %
          (m2_r1, p_r1[0], p_r1[-1], ex_r1[0], ex_r1[-1]))

    # 5. M2 is zero on a constant profile and correct on a profile that IS the curve
    flat = [10.0] * 7
    m2_flat = (flat[-1] - flat[0]) / (len(flat) - 1.0)
    ramp = [10.0 + 3.0 * j for j in range(7)]
    m2_ramp = (ramp[-1] - ramp[0]) / (len(ramp) - 1.0)
    check("plant-slope-is-zero-on-a-flat-profile-and-3.0-on-a-ramp",
          m2_flat == 0.0 and abs(m2_ramp - 3.0) < 1e-12,
          "flat=%.3f ramp=%.3f" % (m2_flat, m2_ramp))

    # 6. M1 is exactly the logged mean cost -- the identity that makes it model-free
    cs, dyn = cells_for_plant("double-int R=100", c, dmax)
    cs = route_estimates(cs, dyn, {})
    worst = max(abs(x["M1"] - (x["J"] - x["lam"] / x["Lstar"])) for x in cs)
    check("plant-M1-is-the-logged-combination", worst < 1e-12, "max deviation=%.2e" % worst)

    # 7. the routes are DEFINED where they should be, and the sweep control is carried
    check("plant-routes-are-populated",
          any(x["M2"] is not None for x in cs) and any(x["SW"] is not None for x in cs),
          "M2 defined=%d SW defined=%d" % (sum(1 for x in cs if x["M2"] is not None),
                                           sum(1 for x in cs if x["SW"] is not None)))

    # 8. the object statistic is not blind: on a synthetic ramp it reads a perfect correlation,
    #    and on a constant series it is UNDEFINED rather than zero
    xs = list(range(6))
    r_perfect, n_perfect = pearson(xs, [2.0 * v for v in xs])
    r_const, n_const = pearson(xs, [5.0] * 6)
    r_short, n_short = pearson([1.0, 2.0], [1.0, 2.0])
    check("plant-object-statistic-detects-a-tracking-series",
          r_perfect is not None and abs(r_perfect - 1.0) < 1e-12 and r_const is None
          and r_short is None,
          "perfect=%.6f const=%s short=%s" % (r_perfect, r_const, r_short))

    # 9. a swept control on a block that MOVES must show a positive correlation
    blocks = {}
    for x in cs:
        blocks.setdefault(x["tau"], []).append(x)
    any_tracking = False
    for _, sub in blocks.items():
        r, n = pearson([x["SW"] for x in sub], [x["c_true"] for x in sub])
        if r is not None and r > 0.5 and n >= MIN_N:
            any_tracking = True
    check("plant-sweep-control-tracks-the-curve-somewhere", any_tracking)

    # 10. determinism of the exact route (the MC certificate is separate and seeded)
    p2, _ = phase_profile(A, B, K, W, 0.0, 5)
    check("plant-exact-profile-is-deterministic", all(abs(a - b) < TOLERANCE for a, b in zip(prof, p2)))

    # 11. THE STRUCTURAL CERTIFICATE: two prices that select the SAME visited point give identical
    #     telemetry (and identical G), while the block does visit several points.  Measured on the
    #     fixture's own cells, so it is a fact about this data and not a restatement of an identity.
    inv = point_invariance(cs)
    check("plant-same-visited-point-gives-identical-telemetry",
          inv.get("n_groups", 0) > 0
          and inv.get("max_rel_M2_spread_within_a_group", 1.0) < 1e-12
          and inv.get("max_rel_G_spread_within_a_group", 1.0) < 1e-12
          and len(set(inv.get("distinct_visited_points_per_block", []))) > 1,
          "groups=%s price_span=%.3g rel_G_spread=%.2e rel_M2_spread=%.2e distinct_L*=%s" % (
              inv.get("n_groups"), inv.get("max_price_span_within_a_group", 0.0),
              inv.get("max_rel_G_spread_within_a_group", 0.0),
              inv.get("max_rel_M2_spread_within_a_group", 0.0),
              inv.get("distinct_visited_points_per_block")))

    print(json.dumps({"plants": checks, "passed": ok, "total": len(checks)}, indent=2))
    return 0 if ok == len(checks) else 1


# ------------------------------------------------------------------ main
def measure_all():
    curves = v1.plants_with_curves()
    cache, all_cells = {}, []
    for name in sorted(curves):
        c, dmax = curves[name]
        cs, dyn = cells_for_plant(name, c, dmax)
        route_estimates(cs, dyn, cache)
        for x in cs:
            x["flatness"] = x.get("profile_flatness")
        all_cells.extend(cs)

    routes = {}
    for key, label in (("M1", "moments: logged mean cost  J - lam/L*"),
                       ("M2", "moments: within-chunk phase slope"),
                       ("SW", "control: centred difference of G (the sweep)")):
        routes[key] = {
            "reading": label,
            "error_vs_point": {"all": err_stat(all_cells, key),
                               "interior": err_stat(all_cells, key, "interior"),
                               "pinned": err_stat(all_cells, key, "pinned")},
            "object_test_interior": object_test(all_cells, key, interior_only=True),
        }

    # the head-to-head, per route, over the cells where BOTH that route and the sweep are defined
    # -- reported over all cells and over the INTERIOR cells (where the visited point moves)
    def head(route, label=None):
        sub = [x for x in all_cells
               if x[route] is not None and x["SW"] is not None
               and (label is None or x["label"] == label)]
        if not sub:
            return None
        em = float(np.median([rel(x[route], x["c_true"]) for x in sub]))
        es = float(np.median([rel(x["SW"], x["c_true"]) for x in sub]))
        return {"n": len(sub), "median_err_route": em, "median_err_sweep": es,
                "ratio_sweep_better_by": (em / es) if es > 0 else None}

    fl = [x["flatness"] for x in all_cells if x.get("flatness") is not None]
    inv = point_invariance(all_cells)
    res = {
        "build": BUILD,
        "goal": "P4 (moments half) -- do the model-free telemetry readings recover c(tau+L*)?",
        "cells": {"total": len(all_cells),
                  "interior": sum(1 for x in all_cells if x["label"] == "interior"),
                  "pinned": sum(1 for x in all_cells if x["label"] == "pinned"),
                  "M2_defined": sum(1 for x in all_cells if x["M2"] is not None),
                  "SW_defined": sum(1 for x in all_cells if x["SW"] is not None)},
        "profile_flatness_max_over_min": ({"n": len(fl), "median": float(np.median(fl)),
                                           "worst": float(max(fl))} if fl else None),
        "routes": routes,
        "direction_test_M2": {"all": direction_test(all_cells, "M2"),
                              "interior": direction_test(all_cells, "M2", "interior"),
                              "note": "M1 is a cost LEVEL and agrees in sign by construction; the "
                                      "direction test is informative only for a slope (M2)"},
        "point_invariance": inv,
        "head_to_head": {"M1_vs_sweep": {"all": head("M1"), "interior": head("M1", "interior")},
                         "M2_vs_sweep": {"all": head("M2"), "interior": head("M2", "interior")}},
        "identity_check": {
            "reading": "at an interior point the exact ground truth is the logged cost, c = J",
            "interior_median_rel_err_identity": err_stat(all_cells, "J", "interior").get("median")},
    }
    return res


def write_json(path, obj):
    """Stage to a temp file and os.replace: a truncate-then-fail write is not atomic."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-v3-", suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def main():
    R = measure_all()
    print(json.dumps(R, indent=2, sort_keys=True))
    write_json("spike_ident_v3_results.json", R)
    return R


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
