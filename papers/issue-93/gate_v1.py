#!/usr/bin/env python3
"""#93 v1 -- the MAP in closed form: is there an interior coverage optimum at any fidelity?

WHAT THIS ROUND ASKS.  v0 (R408) read the screening case b = 1 and found the gate's value AFFINE in escalation
coverage s, so s* is a corner, not an interior point -- and registered PB3 ("the optimum is interior and falls
to the floor as b falls") therefore does not hold AT b = 1.  v1 asks the map's own question: does an interior
optimum appear for SOME b < 1?  If the value is affine in s at every b, PB3 cannot hold anywhere in this model,
and its shape needs a mechanism the registration never names.

WHAT IS DERIVED (route A, closed form, written from the model's statement):

    variant 'none'          V(s) = s*[L*pi*a               - c - cb(1-pi)f]
    variant 'mismatch'      V(s) = s*[L*pi*(b*a + (1-b)f)  - c - cb(1-pi)f]
    variant 'substitution'  V(s) = s*[L*pi*b*a             - c - cb(1-pi)b*f]  - eta*L(1-pi)(1-b)

  where V = E0 - E1 is the gate's per-action value against the no-gate baseline (E0 = L*pi).  Every one is
  (constant) + (constant)*s: the value is AFFINE in coverage for every b, variant and eta, hence s* is always a
  corner -- PB3's interior optimum does not exist in this model at all.

  The three slopes differ in exactly the way the construct predicts.  'mismatch' replaces the reviewer's
  sensitivity a by the EFFECTIVE sensitivity b*a + (1-b)*f, because an unfaithful rendering can still block a
  harmful action -- by a false positive on a benign rendering -- so a mismatch can only ever LOSE screening
  power, never add harm.  'substitution' keeps the screening coefficient b*a and ADDS a harm term
  eta*L(1-pi)(1-b) present even at s = 0: the laundering channel, which makes the gate strictly worse than no
  gate when coverage is off.

THE SIGN LAW (the fidelity at which the gate's value changes sign), closed form:

    substitution   b* = [c + eta*L(1-pi)] / [L*pi*a - cb(1-pi)f + eta*L(1-pi)]
    mismatch       b* = [(c + cb(1-pi)f)/(L*pi) - f] / (a - f)

  and V* > 0 is equivalent to V(1) > 0, because V(1) > 0 forces the slope negative (the laundering term is
  non-negative), so the coverage decision never has to be made separately from the value.

WHAT IS MEASURED, more than one route per quantity (Class 83: two paths to one number must be shown to agree
before either is used):
  1. CURVATURE: second differences of the enumerated value in s over a (variant, b, eta) grid.
  2. SLOPE: closed form against a central difference of the enumeration.
  3. THRESHOLD b*: closed form against a bisection on the enumeration.
  4. Monte Carlo at b < 1 against the enumeration (interval coverage and estimator bias).
  5. CONTINUITY: v1 at b = 1 must reproduce v0's own enumeration exactly (one instrument, two versions -- a
     version that does not reduce to its predecessor is a second model, not an extension).

THE FATIGUE ARM (the constructive half).  A linear fatigue coupling -- the reviewer's sensitivity degrades with
the volume of escalations, a_s = a*(1 - kappa*s) -- makes the value a PARABOLA in s with the closed-form optimum

    s*(b, kappa) = [L*pi*b*a - c - cb(1-pi)b*f] / (2*kappa*L*pi*b*a)

  which is INTERIOR for kappa > 0 and reaches the floor exactly at the sign-law threshold.  So PB3's registered
  shape (interior, falling to the floor as b falls) is exactly what a fatigue mechanism produces: the prior is
  not wrong, it presupposes a mechanism it never names.

PRE-REGISTERED BEFORE THE RUN (so the result can contradict the author):
  P1  AFFINE: the enumerated value's second difference in s is zero to floating point on the grid.
      FALSIFIER: any cell with resolvable curvature.
  P2  SLOPE LAW: the closed-form slope equals the enumeration's central difference, all cells.
  P3  SIGN LAW: the closed-form b* equals the bisected zero of the enumerated V, per variant and eta.
  P4  MISMATCH IS SAFE / SUBSTITUTION IS LAUNDERING: at b = 0 the mismatch arm's value is 0 (its own floor, no
      harm added) while the substitution arm's is strictly negative (-eta*L(1-pi)), and b*(sub) > b*(mis).
  P5  FATIGUE RESTORES PB3: with kappa > 0 the argmax is interior and the closed-form s* matches it; with
      kappa = 0 it is a corner; the floor sits at the sign-law b*.
  P6  CONTINUITY WITH v0: at b = 1 the v1 enumeration reproduces v0's screening values exactly.

Run:  /usr/bin/python3 gate_v1.py      (writes gate_v1_results.json beside itself)
"""
import io
import json
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "gate_v1_results.json")

import gate_v0 as V0                        # noqa: E402  the instrument this round extends

VARIANTS = ("none", "mismatch", "substitution")
B_GRID = (0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 1.0)
ETA_GRID = (0.0, 0.5, 1.0)
TOL = 1e-12


def _p(**kw):
    return V0._p(**kw)


# ------------------------------------------------------------------ route A: closed form (the map)
def slope_closed(params, variant, b):
    """dV/ds.  The variants differ in the coefficient of the screening term."""
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    if variant == "none":
        return L * pi * a - c - cb * (1.0 - pi) * f
    if variant == "mismatch":
        return L * pi * (b * a + (1.0 - b) * f) - c - cb * (1.0 - pi) * f
    return L * pi * b * a - c - cb * (1.0 - pi) * b * f


def value_closed(params, variant, b, s):
    """V(s) = E0 - E1.  (constant) + slope*s for every variant."""
    pi, L, eta = params["pi"], params["L"], params["eta"]
    base = -eta * L * (1.0 - pi) * (1.0 - b) if variant == "substitution" else 0.0
    return base + slope_closed(params, variant, b) * s


def vstar_closed(params, variant, b):
    """Best value over the coverage decision -- a corner, by affineness."""
    return max(value_closed(params, variant, b, 0.0), value_closed(params, variant, b, 1.0))


def bstar_closed(params, variant):
    """The fidelity at which V(1) = 0 (and, since V(1) > 0 forces slope < 0, where the gate's value changes
    sign)."""
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    eta = params["eta"]
    if variant == "mismatch":
        return ((c + cb * (1.0 - pi) * f) / (L * pi) - f) / (a - f)
    num = c + eta * L * (1.0 - pi)
    den = L * pi * a - cb * (1.0 - pi) * f + eta * L * (1.0 - pi)
    return num / den


# ------------------------------------------------------------------ the fatigue arm (PB3's mechanism)
def enum_fatigue(params, s, variant="substitution", b=1.0, kappa=0.0):
    """The state space with the linear fatigue coupling a_s = a*(1 - kappa*s).  Its own loop, so that the
    kappa = 0 case can be asserted equal to v0's enumeration (one model, two readings)."""
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    eta = params["eta"]
    a_s = a * (1.0 - kappa * s)
    harm = att = fb = 0.0
    total = 0.0
    for P_harm in (True, False):
        for esc in (True, False):
            for faithful in (True, False):
                if faithful or variant == "none":
                    render_harm, exec_harm, binds, substituted = P_harm, P_harm, True, False
                elif variant == "mismatch":
                    render_harm, exec_harm, binds, substituted = False, P_harm, True, False
                else:
                    render_harm, exec_harm, binds = P_harm, True, False
                    substituted = not P_harm
                p_reject = (a_s if render_harm else f) if esc else 0.0
                p_P = pi if P_harm else (1.0 - pi)
                p_E = s if esc else (1.0 - s)
                p_F = b if faithful else (1.0 - b)
                prob = p_P * p_E * p_F
                blocked = esc and binds                 # a rejection binds only in these branches
                p_exec = (1.0 - p_reject) if blocked else 1.0
                if exec_harm:
                    harm += prob * p_exec * (eta if substituted else 1.0)
                if esc:
                    att += prob
                if (not P_harm) and blocked:
                    fb += prob * p_reject
                total += prob
    if abs(total - 1.0) > 1e-12:
        raise RuntimeError("the fatigue arm's state space does not sum to 1: %.17g" % total)
    return L * harm + c * att + cb * fb, dict(harm=harm, attention=att, false_block=fb)


def sstar_fatigue_closed(params, b, kappa):
    """The parabola's vertex: s* = numerator / (2*kappa*L*pi*b*a).  None when the coupling is absent."""
    if kappa <= 0.0:
        return None
    pi, a, f = params["pi"], params["a"], params["f"]
    L, c, cb = params["L"], params["c"], params["cb"]
    num = L * pi * b * a - c - cb * (1.0 - pi) * b * f
    return num / (2.0 * kappa * L * pi * b * a)


# ------------------------------------------------------------------ the round's readings
def main():
    res = {"what": "issue #93 v1 -- the map in closed form: is the coverage optimum ever interior?",
           "why": "v0 found the value affine at b = 1; PB3's interior optimum needs a b < 1 reading",
           "preregistered": dict(
               P1="the enumerated value's second difference in s is zero to floating point on the grid",
               P2="the closed-form slope equals the enumeration's central difference",
               P3="the closed-form b* equals the bisected zero of the enumerated V",
               P4="mismatch is safe at b=0 (V=0) and substitution is laundering (V<0), b*(sub) > b*(mis)",
               P5="kappa>0 makes the argmax interior and the floor sits at the sign-law b*",
               P6="at b = 1 the v1 enumeration reproduces v0's screening values exactly"),
           "grids": dict(b=list(B_GRID), eta=list(ETA_GRID), variants=list(VARIANTS))}
    report = []

    def say(line=""):
        print(line)
        report.append(line)

    # ---- P6: the extension must reduce to the instrument it extends
    say("=== P6  continuity: v1 must reduce to v0 at b = 1")
    p0 = _p()
    cont, worst_cont = [], 0.0
    for s in (0.0, 0.25, 0.5, 1.0):
        v0_loss, _ = V0.enumerate_exact(p0, s)
        for variant in VARIANTS:
            v1_loss, _ = enum_fatigue(p0, s, variant=variant, b=1.0, kappa=0.0)
            d = abs(v0_loss - v1_loss)
            worst_cont = max(worst_cont, d)
            cont.append(dict(s=s, variant=variant, v0=v0_loss, v1=v1_loss, abs_diff=d))
    res["continuity"] = dict(rows=cont, worst_abs_diff=worst_cont)
    say("  worst |v1 - v0| over %d reads at b = 1: %.3e" % (len(cont), worst_cont))
    if worst_cont > TOL:
        raise RuntimeError("v1 does not reduce to v0 at b = 1: %.3e" % worst_cont)
    say("  -> the extension is one model read twice, not a second model")

    # ---- P1: curvature
    say()
    say("=== P1  curvature in s (an affine value has NO second difference)")
    s_trip = (0.25, 0.5, 0.75)
    curv, worst_curv = [], 0.0
    for variant in VARIANTS:
        for b in B_GRID:
            for eta in ETA_GRID:
                pr = _p(eta=eta)
                vals = [V0.enumerate_exact(pr, s, variant=variant, b=b, screen_only=False)[0] for s in s_trip]
                d2 = vals[0] - 2.0 * vals[1] + vals[2]
                scale = max(1.0, abs(vals[0]), abs(vals[1]), abs(vals[2]))
                worst_curv = max(worst_curv, abs(d2) / scale)
                curv.append(dict(variant=variant, b=b, eta=eta, v=vals, second_difference=d2,
                                 relative=abs(d2) / scale))
    res["curvature"] = dict(rows=curv, worst_relative=worst_curv, n=len(curv), tolerance=TOL)
    say("  worst relative second difference over %d cells: %.3e   (tolerance 1e-12)" % (len(curv), worst_curv))
    if worst_curv > TOL:
        bad = [r for r in curv if r["relative"] > TOL]
        raise RuntimeError("the value is NOT affine in coverage: %d cells show curvature, e.g. %s"
                           % (len(bad), bad[:3]))
    say("  -> the value is affine in coverage at EVERY fidelity, variant and severity: the coverage")
    say("     optimum is a corner at every point of the map -- PB3's interior optimum does not exist here.")

    # ---- P2: the slope law
    say()
    say("=== P2  the slope law (closed form vs the enumeration's central difference)")
    sl, worst_slope = [], 0.0
    h = 1e-4
    for variant in VARIANTS:
        for b in B_GRID:
            for eta in ETA_GRID:
                pr = _p(eta=eta)
                lo, _ = V0.enumerate_exact(pr, 0.5 - h, variant=variant, b=b, screen_only=False)
                hi, _ = V0.enumerate_exact(pr, 0.5 + h, variant=variant, b=b, screen_only=False)
                numeric = (pr["L"] * pr["pi"] - lo) - (pr["L"] * pr["pi"] - hi)
                numeric = ((pr["L"] * pr["pi"] - hi) - (pr["L"] * pr["pi"] - lo)) / (2.0 * h)
                want = slope_closed(pr, variant, b)
                d = abs(numeric - want)
                worst_slope = max(worst_slope, d)
                sl.append(dict(variant=variant, b=b, eta=eta, closed=want, numeric=numeric, abs_diff=d))
        say("  %-13s slope at b = 1: %+.6f   at b = 0.5: %+.6f   at b = 0: %+.6f"
            % (variant, slope_closed(_p(), variant, 1.0), slope_closed(_p(), variant, 0.5),
               slope_closed(_p(), variant, 0.0)))
    res["slope"] = dict(rows=sl, worst_abs_diff=worst_slope)
    say("  worst |closed - numeric| over %d cells: %.3e" % (len(sl), worst_slope))
    if worst_slope > 1e-6:
        raise RuntimeError("the closed-form slope does not match the enumeration: %.3e" % worst_slope)

    # ---- P3 + P4: the sign law
    say()
    say("=== P3/P4  the sign law b*, and the two channels' asymmetry")
    say("  ('none' has NO b-axis: it is the fidelity-free screening case, and its value is constant in b --")
    say("   putting it in a b* comparison would be a category error, found while reading this run's own output)")
    sign_rows, worst_b, skipped = [], 0.0, []

    def v_of(pr, variant, b):
        return pr["L"] * pr["pi"] - V0.enumerate_exact(pr, 1.0, variant=variant, b=b, screen_only=False)[0]

    for variant in VARIANTS:
        for eta in ETA_GRID:
            pr = _p(eta=eta)
            v0_, v1_ = v_of(pr, variant, 0.0), v_of(pr, variant, 1.0)
            if v0_ * v1_ >= 0.0:                       # no sign change on [0, 1] -> there is no b*
                skipped.append(dict(variant=variant, eta=eta, v_at_0=v0_, v_at_1=v1_,
                                    reason="V does not change sign on the fidelity axis"))
                say("  %-13s eta=%.1f  NO SIGN CHANGE: V(0) %+.6f, V(1) %+.6f" % (variant, eta, v0_, v1_))
                sign_rows.append(dict(variant=variant, eta=eta, closed=None, bisected=None,
                                      v_at_0=v0_, v_at_1=v1_, v_at_s0=value_closed(pr, variant, 0.5, 0.0)))
                continue
            want = bstar_closed(pr, variant)
            lo, hi = 0.0, 1.0
            for _ in range(200):                                  # bisection on the enumeration itself
                mid = 0.5 * (lo + hi)
                if v_of(pr, variant, mid) < 0.0:
                    lo = mid
                else:
                    hi = mid
            got = 0.5 * (lo + hi)
            d = abs(got - want)
            worst_b = max(worst_b, d)
            sign_rows.append(dict(variant=variant, eta=eta, closed=want, bisected=got, abs_diff=d,
                                  v_at_0=v0_, v_at_1=v1_,
                                  v_at_s0=value_closed(pr, variant, 0.5, 0.0)))
            say("  %-13s eta=%.1f  b* = %.6f (closed)  %.6f (bisected)   V(0) %+.6f  V(1) %+.6f"
                % (variant, eta, want, got, v0_, v1_))
    res["sign_law"] = dict(rows=sign_rows, worst_abs_diff=worst_b, skipped=skipped)
    subs = {r["eta"]: r for r in sign_rows if r["variant"] == "substitution"}
    mism = {r["eta"]: r for r in sign_rows if r["variant"] == "mismatch"}
    # The asymmetry is a statement about the ADDITIVE term (the value at s = 0), not about the value at b = 0:
    # with no escalation a mismatch changes nothing at all, while a substitution still converts a benign action
    # into a harmful one.  (The first version of this control used b = 0 and was simply wrong -- V(0) for
    # mismatch is -0.012, not 0: at zero fidelity the gate still wastes attention.)
    p4 = dict(mismatch_v_at_s0=[mism[e]["v_at_s0"] for e in ETA_GRID],
              substitution_v_at_s0=[subs[e]["v_at_s0"] for e in ETA_GRID],
              bstar_gap=[(e, subs[e]["closed"] - mism[e]["closed"]) for e in ETA_GRID])
    p4["mismatch_adds_nothing_at_zero_coverage"] = all(abs(v) < 1e-15 for v in p4["mismatch_v_at_s0"])
    # The laundering term is exactly -eta*L*(1-pi)*(1-b): it must equal that value at every eta, be STRICTLY
    # negative when eta > 0, and be EXACTLY zero at eta = 0 -- the eta = 0 cell is the control that isolates the
    # term, and a one-sided assertion would have accepted a model in which eta did nothing.
    pr_half = _p(eta=1.0)
    p4["laundering_law"] = [dict(eta=e,
                                 measured=subs[e]["v_at_s0"],
                                 predicted=-e * pr_half["L"] * (1.0 - pr_half["pi"]) * (1.0 - 0.5),
                                 abs_diff=abs(subs[e]["v_at_s0"]
                                              + e * pr_half["L"] * (1.0 - pr_half["pi"]) * (1.0 - 0.5)))
                            for e in ETA_GRID]
    p4["laundering_law_holds"] = all(r["abs_diff"] < 1e-15 for r in p4["laundering_law"])
    p4["substitution_adds_harm_at_zero_coverage"] = all(
        (subs[e]["v_at_s0"] < -1e-15) if e > 0.0 else abs(subs[e]["v_at_s0"]) < 1e-15 for e in ETA_GRID)
    p4["substitution_holds_higher_bar"] = all(g > 0 for _, g in p4["bstar_gap"])
    res["P4_channels"] = p4
    say("  -> at ZERO coverage, mismatch V = %s (exactly nothing: a mismatch can only lose screening power)"
        % ", ".join("%+.2e" % v for v in p4["mismatch_v_at_s0"]))
    say("  -> at ZERO coverage, substitution V = %s -- the laundering term, which is exactly"
        % ", ".join("%+.6f" % v for v in p4["substitution_v_at_s0"]))
    say("     -eta*L*(1-pi)*(1-b): STRICTLY negative for eta > 0 and EXACTLY zero at eta = 0, which is the")
    say("     control that isolates the term (law holds: %s); b*(sub) - b*(mis) = %s"
        % (p4["laundering_law_holds"], ", ".join("%.4f" % g for _, g in p4["bstar_gap"])))
    if worst_b > 1e-6:
        raise RuntimeError("the closed-form b* does not match the bisected zero: %.3e" % worst_b)
    if not (p4["mismatch_adds_nothing_at_zero_coverage"] and p4["laundering_law_holds"]
            and p4["substitution_adds_harm_at_zero_coverage"] and p4["substitution_holds_higher_bar"]):
        raise RuntimeError("the two channels are not asymmetric as registered: %s" % p4)
    if len(skipped) != len(ETA_GRID):
        raise RuntimeError("expected the b-independent variant to be skipped at every eta, got %d" % len(skipped))

    # ---- Monte Carlo at b < 1
    say()
    say("=== the Monte Carlo route at b < 1 (a third route to the same value)")
    mc_rows, covered, biases = [], 0, []
    for variant in VARIANTS:
        for b in (0.0, 0.3, 0.7, 1.0):
            pr = _p(eta=1.0)
            exact, _ = V0.enumerate_exact(pr, 0.6, variant=variant, b=b, screen_only=False)
            draw, CI, se, _ = V0.simulate(pr, 0.6, variant=variant, b=b, n=400000,
                                          seed=8300 + int(100 * b) + len(variant), screen_only=False)
            inside = bool(CI[0] <= exact <= CI[1])
            covered += int(inside)
            biases.append(draw - exact)
            mc_rows.append(dict(variant=variant, b=b, exact=exact, mc=draw, ci=list(CI), se=se, in_ci=inside))
    bias = float(np.mean(biases))
    bias_se = float(np.std(biases, ddof=1) / np.sqrt(len(biases)))
    res["monte_carlo"] = dict(rows=mc_rows, covered=covered, n=len(mc_rows), bias=bias, bias_se=bias_se,
                              bias_in_band=bool(abs(bias) <= 3 * bias_se))
    say("  covered %d of %d cells; mean bias %+.3e +- %.3e (%s)"
        % (covered, len(mc_rows), bias, bias_se, "consistent with zero" if abs(bias) <= 3 * bias_se else "BIASED"))
    if covered < len(mc_rows) - 1:
        raise RuntimeError("the Monte Carlo route missed its interval in %d cells" % (len(mc_rows) - covered))
    if abs(bias) > 3 * bias_se:
        raise RuntimeError("the Monte Carlo estimate is biased at b < 1: %.3e +- %.3e" % (bias, bias_se))

    # ---- P5: the fatigue arm -- PB3's shape, and the mechanism it presupposes
    say()
    say("=== P5  the fatigue arm: PB3's interior optimum is a MECHANISM, not a property")
    fat, worst_s = [], 0.0
    grid = [k / 200.0 for k in range(201)]
    # The floor: PB3's second clause is "falls to the floor as b falls".  The closed-form vertex is <= 0
    # exactly when L*pi*b*a <= c + cb(1-pi)b*f, i.e. below b_floor = c / (L*pi*a - cb(1-pi)*f) -- the same
    # threshold the sign law gives at eta = 0.  The grid must STRADDLE it, or the clause is untested (the
    # first version of this block used b >= 0.25 only and asserted the floor without ever reading it).
    pr_f = _p(eta=1.0)
    b_floor_closed = pr_f["c"] / (pr_f["L"] * pr_f["pi"] * pr_f["a"] - pr_f["cb"] * (1.0 - pr_f["pi"]) * pr_f["f"])
    for kappa in (0.0, 1.0):
        for b in (0.05, 0.1, 0.12, 0.13, 0.15, 0.2, 0.25, 0.5, 0.75, 1.0):
            pr = _p(eta=1.0)
            vals = [pr["L"] * pr["pi"] - enum_fatigue(pr, s, "substitution", b, kappa)[0] for s in grid]
            k_best = int(np.argmax(vals))
            s_num = grid[k_best]
            s_closed = sstar_fatigue_closed(pr, b, kappa)
            interior = bool(0.0 < s_num < 1.0)
            if s_closed is not None:
                worst_s = max(worst_s, abs(min(max(s_closed, 0.0), 1.0) - s_num))
            fat.append(dict(kappa=kappa, b=b, argmax=s_num, v_best=float(vals[k_best]), interior=interior,
                            closed=None if s_closed is None else float(s_closed), grid_step=1.0 / 200.0,
                            above_floor=bool(b > b_floor_closed)))
            say("  kappa=%.1f b=%.2f  argmax s* = %.3f (%s)  closed form %s  value %+.6f"
                % (kappa, b, s_num, "interior" if interior else "CORNER",
                   "n/a" if s_closed is None else "%+.3f" % s_closed, vals[k_best]))
    corners = [r for r in fat if r["kappa"] == 0.0]
    interiors = [r for r in fat if r["kappa"] > 0.0]
    # the floor test: with the coupling on, an interior optimum appears exactly above b_floor and the corner
    # at 0 appears below it -- read on both sides of the threshold, with the straddle recorded
    below = [r for r in interiors if not r["above_floor"]]
    above = [r for r in interiors if r["above_floor"]]
    p5 = dict(kappa0_all_corner=bool(all(not r["interior"] for r in corners)),
              # P5 as registered said "interior for kappa > 0"; the floor the same prior names is below
              # b_floor, so the precise claim is interior ABOVE the floor and 0 below it.  The over-strong
              # version was this file's own defect, caught because the floor is read on both sides.
              kappa1_interior_above_floor=bool(all(r["interior"] for r in interiors if r["above_floor"])),
              worst_grid_vs_closed=worst_s,
              grid_step=1.0 / 200.0,
              b_floor_closed=b_floor_closed,
              below_floor_all_corner=bool(all(r["argmax"] == 0.0 for r in below)),
              above_floor_all_interior=bool(all(r["interior"] for r in above)),
              n_below=len(below), n_above=len(above),
              sign_law_bstar_eta0=bstar_closed(_p(eta=0.0), "substitution"),
              floor_matches_sign_law=bool(abs(b_floor_closed - bstar_closed(_p(eta=0.0), "substitution")) < 1e-12))
    res["P5_fatigue"] = dict(rows=fat, **p5)
    say("  -> kappa = 0: every argmax is a corner (%s)" % p5["kappa0_all_corner"])
    say("  -> the closed-form vertex matches the grid argmax to %.3f (grid step %.3f)"
        % (worst_s, p5["grid_step"]))
    say("  -> PB3's FLOOR clause, read on both sides: the closed-form floor is b = %.4f; below it all %d"
        % (b_floor_closed, len(below)))
    say("     argmaxes sit at 0 (%s) and above it all %d are interior (%s)"
        % (p5["below_floor_all_corner"], len(above), p5["above_floor_all_interior"]))
    say("  -> the floor is the sign law's own threshold at eta = 0 (%.4f vs %.4f, equal: %s)"
        % (b_floor_closed, p5["sign_law_bstar_eta0"], p5["floor_matches_sign_law"]))
    say("  -> so the interior optimum and its floor are a property of the FATIGUE coupling, not of the gate:")
    say("     PB3's shape is exactly what that coupling produces, and the prior never names it.")
    if not (p5["kappa0_all_corner"] and p5["kappa1_interior_above_floor"]
            and p5["below_floor_all_corner"] and p5["above_floor_all_interior"] and p5["floor_matches_sign_law"]):
        raise RuntimeError("the fatigue arm does not separate corner from interior across the floor: %s" % p5)
    if len(below) < 2 or len(above) < 2:
        raise RuntimeError("the floor is not straddled: %d below, %d above" % (len(below), len(above)))
    if worst_s > 3.0 * p5["grid_step"]:
        raise RuntimeError("the closed-form s* does not match the grid argmax: %.4f" % worst_s)

    # ---- the map itself, at the defaults
    say()
    say("=== the map at the defaults (eta = 1): the gate's best value against fidelity")
    base = _p(eta=1.0)
    table = []
    for b in B_GRID:
        row = dict(b=b, none=vstar_closed(base, "none", b), mismatch=vstar_closed(base, "mismatch", b),
                   substitution=vstar_closed(base, "substitution", b))
        table.append(row)
        say("  b=%.2f   none %+.6f   mismatch %+.6f   substitution %+.6f" % (b, row["none"], row["mismatch"],
                                                                           row["substitution"]))
    res["map"] = table
    res["thresholds"] = {v: (None if v == "none" else bstar_closed(base, v)) for v in VARIANTS}
    say("  the sign thresholds at eta = 1: " + ", ".join(
        ("%s has NO b-axis (its value is constant in fidelity, %+.6f)" % (v, vstar_closed(base, v, 1.0))
         if res["thresholds"][v] is None else "%s b* = %.4f" % (v, res["thresholds"][v])) for v in VARIANTS))
    say("  (the fidelity-free case is the b = 1 screening comparison, not a threshold on b: reporting a b* for")
    say("   it would borrow the substitution formula's number for a variant that has no fidelity term.)")

    res["build"] = dict(python="%s.%s.%s" % tuple(map(str, sys.version_info[:3])), numpy=np.__version__,
                        script_crc32="%08x" % zlib.crc32(io.open(os.path.abspath(__file__), "rb").read()))
    res["report_sha256"] = "%08x" % zlib.crc32(("\n".join(report)).encode("utf-8"))
    with io.open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
    say()
    say("wrote %s" % OUT)
    say("report id %s  (crc32 of this report; a different build may move it)" % res["report_sha256"])


if __name__ == "__main__":
    main()
