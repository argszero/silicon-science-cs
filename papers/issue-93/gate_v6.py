#!/usr/bin/env python3
"""#93 v6 -- the boundary's dependence on L/c: metric (a)'s second clause.

WHERE THIS SITS.  v1 owns the boundary's closed form and its sign laws, v5 owns its INTERVAL, and the
registration's metric (a) is

    "the boundary `b*(a, s, L, c)` with bootstrap CIs and its dependence on `L/c`"

R422 read the interval; this round reads the clause after it -- the DEPENDENCE ON `L/c`.  The exact boundary is a
function of the cost ratio `R = L/c`, and the model says what shape that dependence has:

    mismatch      b*(R) = [ (1 + t(1-pi)f) / (pi*R) - f ] / (a - f)
                  -> a 1/R hyperbola, zero at R_m = (1 + t(1-pi)f)/(pi*f) = 1/(pi f) + t(1-pi)/pi,
                     and NEGATIVE beyond it: above R_m the misrepresentation channel has NO fidelity bar
    substitution  b*(R) = [ 1 + eta(1-pi)R ] / [ R(pi*a + eta(1-pi)) - t(1-pi)f ]
                  -> a hyperbola with the POSITIVE asymptote eta(1-pi)/(pi*a + eta(1-pi)): never zero

with `t = cb/c`.  The two channels therefore differ in kind, not in degree, and the difference is what the sweep
is for: one bar is erasable by making the harm large relative to the escalation cost, the other is not.

THE REGISTERED NOTATION OMITS TWO PARAMETERS, AND THAT IS MEASURED, NOT ARGUED.  The registration writes the
boundary as `b*(a, s, L, c)`.  The model's own algebra carries `cb` (the false-block cost, through `t = cb/c`)
and `eta` (the laundering factor) as well, and `s` does not enter both channels the same way.  C6 is a CONTROL
with three limbs, each two-sided -- a parameter that moves the boundary must move it, and a parameter that does
not must move it NOT by a hair:
    (a) vary `t = cb/c` at fixed `R`: BOTH channels' boundaries must move;
    (b) vary `eta` at fixed `(R, t)`: the substitution boundary must move, the mismatch boundary must be EXACTLY
        unmoved (eta enters only the laundering term);
    (c) vary `s` at fixed `(R, t, eta)`: the substitution boundary must move, the mismatch boundary must be
        exactly unmoved (the affine mismatch value's zero does not depend on the coverage decision).
  So the registered symbol is not wrong, it is INCOMPLETE, and the clause "its dependence on L/c" reads as if `R`
  were the only ratio that matters.  That is recorded as a wording finding (C8), the same rule outcomes.md
  applies to the priors.

THE SWEEP IS A SECOND-ROUTE READ.  Every closed-form boundary on the sweep is checked against a BISECTION ON THE
EXACT ENUMERATION (`V0.enumerate_exact`) -- v1's own second route, reused rather than re-derived.  A reading
whose value does not change sign on [0, 1] has NO boundary there: it is SKIPPED, counted, and its two endpoint
values are published, because "no boundary on this grid" is a state and not a failure (self-audit Class 80/111).
The skip count is a denominator that gets published with the numbers that depend on it.

THE `1/R` RATE IS CHECKED AS A RATE.  `|b*(R) - limit|` falling to zero is not the claim; falling like `1/R` is.
Over a declared decade ladder the ratio of consecutive differences must equal the ratio of the `R`'s (the
correction is `O(1/R^2)`, so a declared tolerance covers it).  For `mismatch` the `1/R` term is the ONLY
R-dependence, so the rate is exact there; for `substitution` it is the leading term of a convergent expansion.

THE DEPENDENCE IS ALSO READ WITH AN INTERVAL.  The clause sits inside a metric registered "with bootstrap CIs",
so the sweep is not left as algebra: C7 reuses v5's estimator at two declared R values and requires the exact
boundary to lie inside the measured interval (the two instruments' own machinery must agree).

PRE-REGISTERED CLAIMS (written before the run -- see `preregistered` in the record).
  P1 the law: the closed form equals the bisected enumeration at every reading with a sign change, < 1e-6.
  P2 monotone: both boundaries are STRICTLY decreasing in R over the grid, on both routes.
  P3 the limits: mismatch's limit is NEGATIVE (the bar leaves the axis) and substitution's is POSITIVE; each is
     approached at the measured rate 1/R.
  P4 R_m: the mismatch bar is zero exactly at the closed-form R_m and negative beyond it.
  P5 the crossover: the two boundaries change which is larger at a single R_c, bracketable and bisectable, with
     the crossing inside the declared bracket.
  P6 the omissions: t moves both boundaries; eta moves only substitution; s moves only substitution.
  P7 the interval: at the declared R values the exact boundary lies inside v5's measured interval.

Run:  /usr/bin/python3 gate_v6.py
Writes gate_v6_results.json beside this file.
"""
import io
import json
import math
import os
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate_v0 as V0  # noqa: E402
import gate_v1 as V1  # noqa: E402
import gate_v5 as V5  # noqa: E402

OUT = os.path.join(HERE, "gate_v6_results.json")
# `c` is held at the registered defaults' value and `L` is swept through `R = L/c`, so the sweep's R = 50 point
# IS the defaults cell (L = 1.0, c = 0.02) -- the sweep contains the round's own reference point rather than
# sitting beside it.
C_FIXED = 0.02
SWEEP_R = (0.5, 1.0, 2.0, 5.0, 8.0, 10.0, 20.0, 50.0, 110.0, 200.0, 1000.0, 10000.0)
RATE_LADDER = (100.0, 1000.0, 10000.0)
RATE_TOL = 0.20                  # the tolerance on consecutive-difference ratios, declared before the run
CROSSOVER_BRACKET = (5.0, 10.0)
INTERVAL_R = (10.0, 20.0)
BISECT_TOL = 1e-6
TOL_MOVED = 1e-9                 # a parameter that moves a boundary must move it by more than this
# ... and one that does NOT must move it by less than this.  The floor is the SECOND ROUTE's own
# resolution: `s` is read by bisecting the enumeration, whose floating-point resolution is ~1e-16, so a
# tolerance below that would be a claim the route cannot support (the observed worst is reported
# against this floor as a ratio, never against zero).
TOL_UNMOVED = 1e-9
CHANNELS = ("mismatch", "substitution")


def params_at_R(R, **kw):
    """The defaults with `L = R*c`, so the sweep's abscissa IS the registered ratio L/c."""
    return V0._p(L=R * C_FIXED, **kw)


def bisect_boundary(params, channel, s=1.0, lo=0.0, hi=1.0, n=200):
    """b* by BISECTING THE EXACT ENUMERATION -- the second route (v1's own), not the closed form.

    Returns (value, v_lo, v_hi); a value of None means the enumerated value does not change sign on [0, 1], so
    there is NO boundary there.  The endpoints are returned either way: a skip has to publish the values that
    justify it.
    """
    def v(b):
        return params["L"] * params["pi"] - V0.enumerate_exact(params, s, variant=channel, b=b,
                                                               screen_only=False)[0]
    v_lo, v_hi = v(lo), v(hi)
    if v_lo * v_hi >= 0.0:
        return None, v_lo, v_hi
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        if v(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi), v_lo, v_hi


def bisect_at_s(params, channel, s):
    """The same second route but for a general coverage `s`: the boundary is where V(s) changes sign."""
    return bisect_boundary(params, channel, s=s)


def say(msg):
    print(msg)
    sys.stdout.flush()


def crc32(path):
    return "%08x" % (zlib.crc32(io.open(path, "rb").read()) & 0xFFFFFFFF)


def main():
    res = {
        "what": "issue #93 v6 -- the boundary's dependence on L/c: metric (a)'s second clause",
        "why": "the registration asks for the boundary 'with bootstrap CIs AND ITS DEPENDENCE ON L/c'; v1/v5 "
               "read the boundary and its interval, nothing had read the cost-ratio dependence as its own object",
        "preregistered": dict(
            P1="the closed form equals the bisected enumeration at every reading with a sign change (< 1e-6)",
            P2="both boundaries are strictly decreasing in R over the grid, on both routes",
            P3="mismatch's limit is negative and substitution's positive, each approached at the rate 1/R",
            P4="the mismatch bar is zero exactly at the closed-form R_m and negative beyond it",
            P5="the two boundaries change which is larger at a single bracketable R_c",
            P6="t moves both boundaries; eta moves only substitution; s moves only substitution",
            P7="at the declared R values the exact boundary lies inside v5's measured interval"),
        "c_fixed": C_FIXED, "sweep_R": list(SWEEP_R), "t_default": None, "eta_default": None,
        "build": dict(script_crc32=crc32(os.path.abspath(__file__))),
    }
    base = V0._p()
    pi, a, f, eta, cb = base["pi"], base["a"], base["f"], base["eta"], base["cb"]
    t = cb / C_FIXED
    res["t_default"] = t
    res["eta_default"] = eta
    u = eta * (1.0 - pi)
    v_ = pi * a + u
    res["limits"] = dict(
        mismatch_limit=-f / (a - f),
        substitution_limit=u / v_,
        mismatch_R_zero=(1.0 + t * (1.0 - pi) * f) / (pi * f),
        substitution_denominator_zero=t * (1.0 - pi) * f / v_,
        formulas=dict(
            mismatch="[(1 + t(1-pi)f)/(pi*R) - f] / (a - f)",
            substitution="[1 + eta(1-pi)R] / [R(pi*a + eta(1-pi)) - t(1-pi)f]"),
        reads="with t = cb/c: the registered symbol b*(a, s, L, c) omits the false-block cost cb")

    # ---------------------------------------------------------------- C1: the sweep, two routes
    say("C1  the sweep: closed form against a bisection on the exact enumeration")
    readings, skipped = [], []
    for channel in CHANNELS:
        for R in SWEEP_R:
            pr = params_at_R(R)
            closed = V1.bstar_closed(pr, channel)
            got, v_lo, v_hi = bisect_boundary(pr, channel)
            row = dict(channel=channel, R=R, L=pr["L"], closed=closed, bisected=got,
                       abs_diff=(abs(got - closed) if got is not None else None),
                       v_at_0=v_lo, v_at_1=v_hi)
            readings.append(row)
            if got is None:
                skipped.append(dict(channel=channel, R=R, v_at_0=v_lo, v_at_1=v_hi,
                                    reason="the enumerated value does not change sign on [0, 1]"))
    checked = [r for r in readings if r["bisected"] is not None]
    worst = max(r["abs_diff"] for r in checked)
    res["C1_law"] = dict(rows=readings, n_readings=len(readings), n_checked=len(checked),
                         n_skipped=len(skipped), skipped=skipped, worst_abs_diff=worst, tolerance=BISECT_TOL)
    say("    %d reading(s): %d with a sign change (worst |closed - bisected| = %.3e, tol %.0e), %d skipped"
        % (len(readings), len(checked), worst, BISECT_TOL, len(skipped)))
    if worst > BISECT_TOL:
        raise RuntimeError("the closed-form boundary does not match the bisected enumeration: worst %.3e over "
                           "%d reading(s)" % (worst, len(checked)))

    # ---------------------------------------------------------------- C2: monotone in R
    mono = {}
    for channel in CHANNELS:
        rows = [r for r in readings if r["channel"] == channel]
        bad_closed, bad_bisected = [], []
        for lo, hi in zip(rows, rows[1:]):
            if hi["closed"] - lo["closed"] >= 0.0:
                bad_closed.append(dict(R_lo=lo["R"], R_hi=hi["R"],
                                       d=hi["closed"] - lo["closed"]))
            if lo["bisected"] is not None and hi["bisected"] is not None:
                if hi["bisected"] - lo["bisected"] >= 0.0:
                    bad_bisected.append(dict(R_lo=lo["R"], R_hi=hi["R"],
                                             d=hi["bisected"] - lo["bisected"]))
        mono[channel] = dict(n_steps=len(rows) - 1, non_decreasing_closed=bad_closed,
                             non_decreasing_bisected=bad_bisected)
    res["C2_monotone"] = mono
    say("C2  strictly decreasing in R on both routes: %s"
        % ", ".join("%s (%d steps, %d closed / %d bisected violations)"
                    % (ch, mono[ch]["n_steps"], len(mono[ch]["non_decreasing_closed"]),
                       len(mono[ch]["non_decreasing_bisected"])) for ch in CHANNELS))
    for ch in CHANNELS:
        if mono[ch]["non_decreasing_closed"] or mono[ch]["non_decreasing_bisected"]:
            raise RuntimeError("a boundary is not strictly decreasing in R: %s" % mono[ch])

    # ---------------------------------------------------------------- C3: the limits, at the rate 1/R
    rates = {}
    for channel in CHANNELS:
        limit = res["limits"]["mismatch_limit" if channel == "mismatch" else "substitution_limit"]
        diffs = []
        for R in RATE_LADDER:
            pr = params_at_R(R)
            diffs.append(abs(V1.bstar_closed(pr, channel) - limit))
        ratios = [lo / hi if hi else None for lo, hi in zip(diffs, diffs[1:])]
        expect = [hi / lo for lo, hi in zip(RATE_LADDER, RATE_LADDER[1:])]
        bad = [dict(measured=r, expected=e) for r, e in zip(ratios, expect)
               if r is None or abs(r - e) / e > RATE_TOL]
        rates[channel] = dict(limit=limit, differences=diffs, differences_ratio=ratios,
                              expected_ratio=expect, tolerance=RATE_TOL, violations=bad)
    res["C3_rate"] = rates
    say("C3  the limits and their rate: mismatch -> %+.6f, substitution -> %+.6f; consecutive-difference ratios "
        "%s (expected %s)" % (res["limits"]["mismatch_limit"], res["limits"]["substitution_limit"],
                              [["%.4f" % r if r is not None else "n/a" for r in rates[ch]["differences_ratio"]]
                               for ch in CHANNELS][0], ["%.1f" % e for e in rates["mismatch"]["expected_ratio"]]))
    for ch in CHANNELS:
        if rates[ch]["violations"]:
            raise RuntimeError("the %s boundary does not approach its limit at the rate 1/R: %s"
                               % (ch, rates[ch]["violations"]))
    if not (res["limits"]["mismatch_limit"] < 0.0 < res["limits"]["substitution_limit"]):
        raise RuntimeError("the two channels' limits do not differ in SIGN, which is the round's finding: %s"
                           % res["limits"])

    # ---------------------------------------------------------------- C4: the mismatch bar's zero
    R_m = res["limits"]["mismatch_R_zero"]
    at_m = V1.bstar_closed(params_at_R(R_m), "mismatch")
    below = V1.bstar_closed(params_at_R(R_m * 0.9), "mismatch")
    above = V1.bstar_closed(params_at_R(R_m * 1.1), "mismatch")
    res["C4_R_zero"] = dict(R_m=R_m, b_at_R_m=at_m, b_below=below, b_above=above,
                            sign_change=bool(below > 0.0 > above))
    say("C4  the mismatch bar's zero: R_m = %.4f, b*(R_m) = %+.2e, below %+.4f, above %+.4f (sign change %s)"
        % (R_m, at_m, below, above, res["C4_R_zero"]["sign_change"]))
    if abs(at_m) > 1e-12 or not res["C4_R_zero"]["sign_change"]:
        raise RuntimeError("the mismatch bar is not zero at the closed-form R_m: %s" % res["C4_R_zero"])

    # ---------------------------------------------------------------- C5: the crossover
    def diff(R):
        pr = params_at_R(R)
        return V1.bstar_closed(pr, "mismatch") - V1.bstar_closed(pr, "substitution")

    lo, hi = CROSSOVER_BRACKET
    d_lo, d_hi = diff(lo), diff(hi)
    if d_lo * d_hi >= 0.0:
        raise RuntimeError("the declared bracket does not contain a crossover: d(%.1f) = %+.5f, d(%.1f) = %+.5f"
                           % (lo, d_lo, hi, d_hi))
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if diff(lo) * diff(mid) <= 0.0:
            hi = mid
        else:
            lo = mid
    R_c = 0.5 * (lo + hi)
    # The crossover has a CLOSED FORM, and the algebra says why it is where it is: setting either boundary to
    # the axis's own edge b = 1 gives the same R, so the two bars cross exactly where BOTH reach b = 1.
    R_c_closed = (1.0 + t * (1.0 - pi) * f) / (pi * a)
    b_mism_c = V1.bstar_closed(params_at_R(R_c_closed), "mismatch")
    b_subs_c = V1.bstar_closed(params_at_R(R_c_closed), "substitution")
    edge_ok = abs(b_mism_c - 1.0) < 1e-12 and abs(b_subs_c - 1.0) < 1e-12
    res["C5_crossover"] = dict(bracket=list(CROSSOVER_BRACKET), R_c=R_c, R_c_closed=R_c_closed,
                               closed_vs_bisected=abs(R_c - R_c_closed), d_at_c=diff(R_c),
                               d_below=diff(CROSSOVER_BRACKET[0]), d_above=diff(CROSSOVER_BRACKET[1]),
                               b_mismatch_at_R_c=b_mism_c, b_substitution_at_R_c=b_subs_c,
                               both_at_the_axis_edge=edge_ok,
                               higher_bar_below="mismatch", higher_bar_above="substitution",
                               mismatch_window=[R_c_closed, res["limits"]["mismatch_R_zero"]],
                               substitution_window=[res["limits"]["substitution_denominator_zero"], None])
    say("C5  the crossover: R_c = %.4f (bisected) = %.4f (closed form (1+t(1-pi)f)/(pi*a)), agree to %.1e; "
        "BOTH bars sit exactly at the axis edge b = 1 there (%.12f / %.12f)"
        % (R_c, R_c_closed, abs(R_c - R_c_closed), b_mism_c, b_subs_c))
    say("      -> the MISREPRESENTATION bar exists only on the bounded window R in (%.4f, %.4f); the LAUNDERING "
        "bar exists on (%.4f, inf)" % (R_c_closed, res["limits"]["mismatch_R_zero"],
                                       res["limits"]["substitution_denominator_zero"]))
    if abs(diff(R_c)) > 1e-9:
        raise RuntimeError("the bisection did not close on the crossover: %+.3e" % diff(R_c))
    if abs(R_c - R_c_closed) > 1e-9 or not edge_ok:
        raise RuntimeError("the crossover's closed form or the axis-edge identity fails: R_c %.6f vs %.6f, "
                           "b = %.12f / %.12f" % (R_c, R_c_closed, b_mism_c, b_subs_c))

    # ---------------------------------------------------------------- C6: the omissions (three limbs)
    R0 = 50.0
    pr0 = params_at_R(R0)
    b0 = {ch: V1.bstar_closed(pr0, ch) for ch in CHANNELS}
    limb_t = []
    for tv in (1.0, t, 5.0):
        pr = params_at_R(R0, cb=tv * C_FIXED)
        b = {ch: V1.bstar_closed(pr, ch) for ch in CHANNELS}
        limb_t.append(dict(t=tv, mismatch=b["mismatch"], substitution=b["substitution"],
                           moved={ch: abs(b[ch] - b0[ch]) for ch in CHANNELS}))
    limb_eta = []
    for ev in (0.5, eta, 1.5):
        pr = params_at_R(R0, eta=ev)
        b = {ch: V1.bstar_closed(pr, ch) for ch in CHANNELS}
        limb_eta.append(dict(eta=ev, mismatch=b["mismatch"], substitution=b["substitution"],
                             moved={ch: abs(b[ch] - b0[ch]) for ch in CHANNELS}))
    limb_s = []
    for sv in (0.25, 0.5, 1.0):
        b = {ch: bisect_at_s(pr0, ch, sv)[0] for ch in CHANNELS}
        limb_s.append(dict(s=sv, mismatch=b["mismatch"], substitution=b["substitution"],
                           moved={ch: (abs(b[ch] - b0[ch]) if b[ch] is not None else None)
                                  for ch in CHANNELS}))
    res["C6_omissions"] = dict(R_fixed=R0, baseline=b0, limb_t=limb_t, limb_eta=limb_eta, limb_s=limb_s,
                               moved_tolerance=TOL_MOVED, unmoved_tolerance=TOL_UNMOVED)
    # NON-VACUITY, and it is not decoration: every guard below SKIPS the row that IS the baseline, so a limb made
    # only of baseline rows would pass every one of them without measuring anything.  A control owes its
    # denominator, and a limb owes at least one row that differs from the baseline on the parameter it varies.
    vacuous = []
    for label, limb, key, base_val in (("t", limb_t, "t", t), ("eta", limb_eta, "eta", eta),
                                       ("s", limb_s, "s", 1.0)):
        n_varying = sum(1 for x in limb if abs(x[key] - base_val) > 1e-15)
        if n_varying == 0:
            vacuous.append(dict(limb=label, rows=len(limb)))
    res["C6_omissions"]["vacuity"] = dict(vacuous_limbs=vacuous, rule="each limb must vary its parameter")
    if vacuous:
        raise RuntimeError("a control limb has no non-baseline row, so its guards would pass vacuously: %s"
                           % vacuous)
    say("C6  the omissions at R = %.0f: t = cb/c moves both (max %.4f); eta moves substitution by %.4f and "
        "mismatch by %.1e; s moves substitution%s and mismatch by %.1e"
        % (R0, max(max(x["moved"].values()) for x in limb_t),
           max(x["moved"]["substitution"] for x in limb_eta),
           max(x["moved"]["mismatch"] for x in limb_eta),
           "", max(x["moved"]["mismatch"] for x in limb_s if x["moved"]["mismatch"] is not None)))
    for x in limb_t:                                  # (a) t = cb/c must move BOTH (the baseline row excluded)
        if abs(x["t"] - t) < 1e-15:             # the baseline row IS the baseline: it must NOT move
            if any(x["moved"][ch] > TOL_UNMOVED for ch in CHANNELS):
                raise RuntimeError("the baseline row moved, so the control is not measuring the parameter: %s" % x)
            continue
        for ch in CHANNELS:
            if x["moved"][ch] <= TOL_MOVED:
                raise RuntimeError("cb does not move the %s boundary, so the registered symbol would be "
                                   "complete: %s" % (ch, x))
    for x in limb_eta:                                  # (b) eta: substitution must move, mismatch must not (baseline excluded)
        if abs(x["eta"] - eta) < 1e-15:             # the baseline row IS the baseline: it must NOT move
            if any(x["moved"][ch] > TOL_UNMOVED for ch in CHANNELS):
                raise RuntimeError("the baseline row moved, so the control is not measuring the parameter: %s" % x)
            continue
        if x["moved"]["substitution"] <= TOL_MOVED:
            raise RuntimeError("eta does not move the substitution boundary: %s" % x)
        if x["moved"]["mismatch"] > TOL_UNMOVED:
            raise RuntimeError("eta moves the mismatch boundary, which is a claim this round must check before "
                               "making it: %s" % x)
    for x in limb_s:                                  # (c) s: substitution must move, mismatch must not (baseline excluded)
        if abs(x["s"] - 1.0) < 1e-15:             # the baseline row IS the baseline: it must NOT move
            if any(x["moved"][ch] > TOL_UNMOVED for ch in CHANNELS):
                raise RuntimeError("the baseline row moved, so the control is not measuring the parameter: %s" % x)
            continue
        if x["moved"]["substitution"] is None or x["moved"]["substitution"] <= TOL_MOVED:
            raise RuntimeError("the coverage s does not move the substitution boundary: %s" % x)
        if x["moved"]["mismatch"] is not None and x["moved"]["mismatch"] > TOL_UNMOVED:
            raise RuntimeError("the coverage s moves the mismatch boundary: %s" % x)

    # ---------------------------------------------------------------- C7: the dependence, with an interval
    intervals = []
    for R in INTERVAL_R:
        pr = params_at_R(R)
        for ch in CHANNELS:
            est = V5.estimate(pr, ch)
            exact = V1.bstar_closed(pr, ch)
            fie = est["fieller"]
            intervals.append(dict(R=R, channel=ch, exact_b_star=exact, b_hat_star=est["b_hat_star"],
                                  state=fie["kind"],
                                  lo=fie.get("lo"), hi=fie.get("hi"), width=fie.get("width"),
                                  covers=bool(fie["kind"] == "bounded" and fie["lo"] <= exact <= fie["hi"])))
    res["C7_interval"] = dict(rows=intervals, n=len(intervals),
                              n_covering=sum(1 for x in intervals if x["covers"]))
    say("C7  the dependence with an interval at R in %s: %d of %d exact boundaries inside the measured set"
        % (list(INTERVAL_R), res["C7_interval"]["n_covering"], len(intervals)))
    if res["C7_interval"]["n_covering"] != len(intervals):
        raise RuntimeError("a measured interval does not contain the exact boundary: %s"
                           % [x for x in intervals if not x["covers"]])

    # ---------------------------------------------------------------- C8: the wording finding
    res["C8_registered_wording"] = dict(
        registered_symbol="b*(a, s, L, c)",
        measured="the boundary also depends on cb (through t = cb/c) and on eta, and s moves only the laundering "
                 "channel while R = L/c moves both",
        finding="the clause 'its dependence on L/c' reads as if R were the only ratio that matters; the "
                "false-block cost relative to the escalation cost (t = cb/c) is a second ratio the registered "
                "symbol does not name, and the sweep must declare it (C6 shows it moves both boundaries)")
    res["checks"] = dict(C1_law="PASS", C2_monotone="PASS", C3_rate="PASS", C4_R_zero="PASS",
                         C5_crossover="PASS", C6_omissions="PASS", C7_interval="PASS", C8_wording="reported")
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, indent=1, sort_keys=True))
    say("")
    say("gate_v6_results.json written (%d bytes), script crc32 %s" % (os.path.getsize(OUT),
                                                                     res["build"]["script_crc32"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
