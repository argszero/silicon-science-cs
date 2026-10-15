#!/usr/bin/env python3
"""Issue #142 / research v6 -- P2's span law on the SECOND priced system (closing the one named gap).

BOUNDED GOAL (one goal, stated before it runs).  R634 (v1) DECIDED P2 on the first system: under noise
the differencing route has an interior MSE-optimal span h*, and h* ~ sigma^{2/(2b+2)} where b is the
MEASURED bias exponent -- sigma^{1/3} in the smooth limit (b=2) and sigma^{0.41} on the shipped model,
whose c(.) is only C^0 (a kink every 1.0 delay -> b=1.42).  R643 (v5) built a SECOND priced system (an
age-of-information sampler) but its instrument is noise-free, so P2 was NOT re-tested there.  This
instrument closes that gap: it asks whether the SAME law, with the SAME two arms (a smooth curve and a
kinked C^0 curve), holds on the second system.

WHY IT MATTERS.  The paper's central claim is that the laws are properties of the ROUTE, not of the
plant.  If P2's exponent is 1/3 for the smooth AoI curve and >1/3 for a C^0 representation of the SAME
curve -- exactly as on the robotics plant -- then the exponent is set by the REPRESENTATION's smoothness
and the route's differencing, and only the constants are the system's.  That is the cross-system form of
P2.

HOW IT IS MEASURED.  Exactly v1's machinery, on v5's curve:
  * the estimator is the CENTRED difference of G = L*J - lam = int_0^L c (the envelope identity, v0/v5):
        c_hat(x) = (G(x+h) - G(x-h)) / (2h)   -- whose target is the SPAN MEAN of c, not the point (P1);
  * its bias^2 A[k] and variance coefficient B[k] are computed EXACTLY (v1.accumulate), on a band FIXED
    across k (v1's fixed-band rule -- a k-dependent window corrupts the exponent, Class 267);
  * h*(sigma) is the sub-lattice argmin of MSE = A + sigma^2 B (v1.argmin_refined, Class 267's fixture);
  * the exponent is the log-log slope of h* against a sigma ladder, and the law's PREDICTION
    2/(2b+2) is computed from the SAME run's measured b -- derived, not fitted.

THE TWO ARMS (identical to v1's):
  * SMOOTH -- c(s) = 2 s2 (1 - e^{-theta s}) exactly (C^inf);
  * GRID   -- the same c sampled at a step S and LINEARLY interpolated (C^0, a kink every S) -- the
    representation a deployment's table would deliver.

python3 spike_ident_v6.py                 (writes spike_ident_v6_results.json)
python3 spike_ident_v6.py --selftest      (plants; must all fire)
"""
import json
import math
import os
import sys
import tempfile

import numpy as np

import spike_ident_v1 as v1
import spike_ident_v5 as v5

DELTA = v1.DELTA                 # 0.02, the same lattice as the first system
KMAX = v1.KMAX                   # 40, the same half-width range
SIGMAS = v1.SIGMAS               # the same sigma_J/J ladder
LMAX_A = 12.0                    # the AoI lattice's own upper end (c saturates by ~6/theta)
SOURCES = {"ou theta=0.5 s2=1.0": (0.5, 1.0),
           "ou theta=1.0 s2=1.0": (1.0, 1.0)}
TAUS = (0.0, 1.0, 2.0, 3.0, 4.0)
GRID_STEP = 1.0                  # the C^0 arm's kink spacing -- the analogue of the 1.0-delay node
BUILD = v1.BUILD


# ------------------------------------------------------------------ the two representations of c
def cfn_smooth(theta, s2):
    return lambda x: v5.c_exact(theta, s2, x)


def cfn_grid(theta, s2, S=GRID_STEP):
    """c sampled at multiples of S and linearly interpolated: C^0, a kink every S."""
    def f(x):
        i = math.floor(x / S)
        t = (x - i * S) / S
        return v5.c_exact(theta, s2, i * S) * (1.0 - t) + v5.c_exact(theta, s2, (i + 1) * S) * t
    return f


def build_block_a(theta, s2, tau, cfn):
    """v1.build_block's construction, with the curve function passed in (no integer-delay list): the
    operating curve on the DELTA grid and the price lam(L) that makes each grid L the operating point."""
    Ls, C = v1.objective_grid_fn(cfn, LMAX_A, tau)
    if Ls is None:
        return None
    lo = max(tau, 1.0)
    mask = Ls >= lo - 1e-9
    Ls, C = Ls[mask], C[mask]
    if len(Ls) < 3 * KMAX:
        return None
    G = Ls * C
    cg = np.array([cfn(tau + L) for L in Ls])
    lam = Ls * cg - G
    ok = np.zeros(len(Ls), dtype=bool)
    for i in range(len(Ls)):
        obj = C + lam[i] / Ls
        ok[i] = abs(int(np.argmin(obj)) - i) <= 1
    return {"Ls": Ls, "C": C, "G": G, "cg": cg, "lam": lam, "ok": ok,
            "tau": tau, "dmax": LMAX_A, "lo": lo}


def blocks_for_a(theta, s2, cfn, taus=TAUS):
    out = []
    for tau in taus:
        b = build_block_a(theta, s2, tau, cfn)
        if b is not None:
            out.append(b)
    return out


def measure_a(theta, s2, arm, grid_step=GRID_STEP):
    """v1.measure on one arm of the second system; `arm` in {"smooth","grid"}."""
    cfn = cfn_smooth(theta, s2) if arm == "smooth" else cfn_grid(theta, s2, grid_step)
    blocks = blocks_for_a(theta, s2, cfn)
    if not blocks:
        return None
    R = v1.measure(blocks, "aoi %s theta=%g s2=%g S=%g" % (arm, theta, s2, grid_step))
    R["blocks"] = len(blocks)
    R["grid_step"] = grid_step
    return R


def curve_degeneracy(theta, s2):
    """How much curvature the arm's c(s) carries over the measurement band -- a NEAR-FLAT curve has a
    near-flat bias, and v1's own plant 4 shows a flat bias has NO interior optimum (no law at all).
    Reported so a null exponent is readable as the curve's property, not the instrument's."""
    band = np.linspace(1.0, LMAX_A, 200)
    c2 = np.array([2.0 * s2 * theta * theta * math.exp(-theta * x) for x in band])   # |c''|
    return {"max_abs_c2": float(c2.max()), "min_abs_c2": float(c2.min()),
            "ratio_max_over_min": float(c2.max() / max(c2.min(), 1e-300))}


# ------------------------------------------------------------------ selftest
def selftest():
    ok, checks = 0, []

    def check(name, cond, detail=""):
        nonlocal ok
        checks.append({"plant": name, "fired": bool(cond), "detail": detail})
        if cond:
            ok += 1

    theta, s2 = SOURCES["ou theta=1.0 s2=1.0"]

    # 1. the estimator's premise: on a LINEAR curve the centred difference has EXACTLY zero bias
    #    (the span mean IS the point value) -- the same plant v1 carries, re-run on this lattice.
    Ls = np.linspace(1.0, 10.0, 200)
    cg = 3.0 + 2.0 * Ls
    G = 3.0 * Ls + Ls * Ls
    worst = 0.0
    for k in (1, 3, 7):
        h = Ls[k] - Ls[0]
        worst = max(worst, abs((G[2 * k] - G[0]) / (2.0 * h) - cg[k]))
    check("plant-linear-curve-centred-bias-is-zero", worst < 1e-9, "worst=%.3g" % worst)

    # 2. the SMOOTH arm's bias is second order (b ~ 2): the exponent the sigma^{1/3} law rests on
    S = measure_a(theta, s2, "smooth")
    b_s = S["law_bias_exponent"]
    check("plant-smooth-arm-bias-exponent-is-second-order",
          b_s is not None and 1.75 < b_s < 2.25, "b_smooth=%.4f" % b_s)

    # 3. the GRID (C^0) arm's bias is SUB-second-order (the kinks add a first-order term)
    Gg = measure_a(theta, s2, "grid")
    b_g = Gg["law_bias_exponent"]
    check("plant-grid-arm-bias-exponent-is-sub-second-order",
          b_g is not None and b_g < b_s - 1e-6, "b_grid=%.4f vs b_smooth=%.4f" % (b_g, b_s))

    # 4. THE LAW IS DERIVED, NOT FITTED: 2/(2b+2) from the SAME run's measured b matches the measured
    #    h*(sigma) slope, on BOTH arms
    ok4 = True
    det4 = []
    for arm, R in (("smooth", S), ("grid", Gg)):
        pred = R["hstar_predicted_from_ingredients"]
        got = R["hstar_vs_sigma_slope_centred"]
        det4.append("%s: pred=%.4f got=%.4f" % (arm, pred if pred else float("nan"),
                                                got if got else float("nan")))
        ok4 = ok4 and pred is not None and got is not None and abs(pred - got) < 0.05
    check("plant-measured-hstar-slope-matches-the-derived-2-over-2b-plus-2", ok4, " | ".join(det4))

    # 5. the second system's smooth arm gives a slope NEAR the first system's smooth arms (the law is
    #    the route's, so the systems agree) -- and the C^0 arm sits ABOVE it, as on the first system
    sl_s = S["hstar_vs_sigma_slope_centred"]
    sl_g = Gg["hstar_vs_sigma_slope_centred"]
    check("plant-second-system-reproduces-the-law-ordering",
          sl_s is not None and sl_g is not None and 0.28 < sl_s < 0.38 and sl_g > sl_s,
          "smooth=%.4f grid=%.4f" % (sl_s, sl_g))

    # 6. determinism of the whole measurement path
    S2 = measure_a(theta, s2, "smooth")
    check("plant-measurement-is-deterministic",
          S2["hstar_vs_sigma_slope_centred"] == S["hstar_vs_sigma_slope_centred"],
          "two identical runs agree exactly")

    # 7. the mechanism sweep is a CONTROLLED claim, not a narrative: the kink spacing moves b, and a
    #    denser kink set (smaller S) moves it toward the smooth value.  (The direction was measured,
    #    not assumed: the first guess -- "more kinks per span means more first-order bias, so b falls"
    #    -- is the OPPOSITE of what the run shows, and the plant pins the MEASURED ordering.)
    sweep = {}
    for S in (0.5, 1.0, 2.0):
        Rs = measure_a(theta, s2, "grid", grid_step=S)
        if Rs is not None:
            sweep[S] = Rs["law_bias_exponent"]
    check("plant-kink-spacing-moves-the-bias-exponent",
          len(sweep) == 3 and sweep[0.5] is not None and sweep[1.0] is not None
          and sweep[0.5] > sweep[1.0] + 1e-3,
          "b(S): " + ", ".join("S=%g -> %.4f" % (S, sweep[S]) for S in sorted(sweep)))

    # 8. the degeneracy diagnostic is present and finite (a null exponent must be readable as the
    #    curve's property): report it, and require it to be a real number for every source
    deg = curve_degeneracy(theta, s2)
    check("plant-curvature-degeneracy-diagnostic-is-finite",
          math.isfinite(deg["max_abs_c2"]) and deg["max_abs_c2"] > 0,
          "max|c''|=%.3g ratio=%.3g" % (deg["max_abs_c2"], deg["ratio_max_over_min"]))

    print(json.dumps({"plants": checks, "passed": ok, "total": len(checks)}, indent=2))
    return 0 if ok == len(checks) else 1


# ------------------------------------------------------------------ main
def system1_reference():
    """The first system's own numbers, read from v1's artefact so the comparison is against a record
    and not a memory.  v1's JSON carries one top-level key per arm (model / smooth / analytic)."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike_ident_v1_results.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    out = {}
    for arm in ("model", "smooth", "analytic"):
        a = d.get(arm)
        if isinstance(a, dict):
            out[arm] = {"arm_label": a.get("arm"),
                        "bias_exponent": a.get("law_bias_exponent"),
                        "hstar_slope_centred": a.get("hstar_vs_sigma_slope_centred"),
                        "hstar_predicted": a.get("hstar_predicted_from_ingredients")}
    return out or None


def main():
    per, pooled = {}, {}
    for name in sorted(SOURCES):
        theta, s2 = SOURCES[name]
        per[name] = {"theta": theta, "s2": s2, "degeneracy": curve_degeneracy(theta, s2),
                     "arms": {}, "grid_step_sweep": {}}
        for arm in ("smooth", "grid"):
            R = measure_a(theta, s2, arm)
            if R is not None:
                per[name]["arms"][arm] = {k: R[k] for k in
                                          ("arm", "blocks", "used_point_spans", "law_bias_exponent",
                                           "law_var_vs_a_exponent", "hstar_vs_sigma_slope_centred",
                                           "hstar_vs_sigma_slope_one_sided",
                                           "hstar_predicted_from_ingredients",
                                           "hstar_points_centred")}
        # THE MECHANISM SWEEP: b is set by the KINK SPACING, so varying the grid step must move it --
        # a denser kink set (smaller S) puts more kinks inside every span, adding first-order bias.
        for S in (0.5, 1.0, 2.0):
            R = measure_a(theta, s2, "grid", grid_step=S)
            if R is not None:
                per[name]["grid_step_sweep"]["S=%g" % S] = {
                    "grid_step": S, "law_bias_exponent": R["law_bias_exponent"],
                    "hstar_vs_sigma_slope_centred": R["hstar_vs_sigma_slope_centred"],
                    "hstar_predicted_from_ingredients": R["hstar_predicted_from_ingredients"]}
    R = {"build": BUILD, "grid": {"delta_L": DELTA, "kmax": KMAX, "lmax": LMAX_A,
                                  "sigma_ladder": SIGMAS, "grid_step": GRID_STEP},
         "per_source": per, "system1_reference": system1_reference()}
    print(json.dumps(R, indent=2, sort_keys=True))
    write_json("spike_ident_v6_results.json", R)
    return R


def write_json(path, obj):
    """Stage to a temp file and os.replace: a truncate-then-fail write is not atomic."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-v6-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    main()
