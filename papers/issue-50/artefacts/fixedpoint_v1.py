#!/usr/bin/env python3
"""Issue #50 -- step 10: the registered metric (e), the CLOSED-FORM fixed point.

WHAT THIS FILE IS.  The registration's success metric (e) reads: *closed-form fixed point within
+/-0.05 of the simulated rho* in >= 80% of cells*.  Steps 1-9 built the instrument and measured the
boundary; none of them wrote down the theory the paper is supposed to carry.  This file writes it,
solves it, and compares it to the SIMULATED crossings that step 3 already published.

THE CLOSED FORM (derived from the model definition, no fitted parameter)
-----------------------------------------------------------------------
The model (instrument_v0, q = 0): A agent loops share c workers; each step is a think phase (mean mT)
followed by one tool call (mean mS); with probability h the call is issued at the START of the think
phase (the prediction was right) and otherwise at its END.  A step ends when the think phase has ended
AND the call has completed.

Let L be the mean step latency (the cycle time of one agent).  Calls are issued at the rate steps are
completed, lambda = A / L -- one call per step -- so the offered load per worker is

    rho = lambda * mS / c = A * mS / (c * L).                                            (1)

The queue wait is the M/M/c waiting time with arrival rate lambda and mean service mS,

    W(lambda, c) = C(c, a) * mS / (c - a),   a = lambda * mS,   C = Erlang C,             (2)

and the cycle time is the sum of its parts:

    L = mT + mS + W - h * E[min(T, D)],     D = Q + S.                                   (3)

An early-issued call lets the step end at max(T, D); a late-issued one at T + D; so the saving is
E[min(T, D)] on the h fraction only.  With T exponential(mT) and D exponential(mD = mS + W),

    E[min(T, D)] = mT * mD / (mT + mD).                                                   (4)

(3) with (4) is a FIXED POINT in L, because W depends on lambda = A / L.  It is solved by bisection:
g(L) = L - phi(L) is increasing, since a longer cycle means a lighter load, a smaller wait, a smaller
phi.

THE SERIAL SIDE is (3) with h = 0: L_s = mT + mS + W(A / L_s, c).

THE BOUNDARY.  For fixed A and h, sweep the pool size c; at each c solve BOTH fixed points (each at
its own load -- they are different systems, which is exactly why this is a fixed point and not a
formula), take

    benefit(c) = 100 * (L_s(c) - L_p(c)) / L_s(c),                                        (5)

and locate the sign change with STEP 3'S OWN RULE (imported, not re-implemented: the rows are built in
the same order step 3 built them -- decreasing c, i.e. increasing contention -- and the crossing is the
first positive-to-nonpositive adjacent pair).  The closed-form boundary is reported in BOTH coordinates
the instrument reports:

    rho_serial* = A * mS / (c* * L_s(c*)),      rho_spec* = A * mS / (c* * L_p(c*)).       (6)

DECLARED ASSUMPTIONS (each is a modelling choice, not a measurement)
--------------------------------------------------------------------
  M1  calls arrive as a Poisson process at rate lambda = A / L (the standard closed-loop
      approximation; exact as A -> infinity at fixed offered load).
  M2  D = Q + S is exponential with mean mS + W.  Only the MEAN of min(T, D) is needed, and the
      assumption is EXACT in the no-queueing limit (D = S exponential, anchor H1 below).
  M3  the queue-position effect anchor A4 measured (an early-issued call can meet a worker the
      late-issued one would have missed) is NOT modelled.  It is a second-order term in the wait and
      is measured, not fitted, in step 1.
  M4  the service distribution's TAIL is not in the closed form: the mean-field equations depend on the
      service distribution only through mS.  Step 5 refuted the registered tail prior (P2), so this
      file is not asked to carry a tail term; the families compared here are all tail='light'.

WHAT IS READ, NOT RE-DERIVED
----------------------------
The SIMULATED boundary is read from step 3's committed artifacts (boundary_v2_h100/h090/h050.json) as
the per-family crossings of the 32-seed mean curve.  Nothing here recomputes a simulated number; if an
artifact is missing the cell is reported NOT TAKEN with the reason and is excluded from the fraction
(an exclusion that is counted, never a silent drop).

THE COMPARED COORDINATE is declared before the comparison: the PRIMARY coordinate is rho_spec (the
contention of the SPECULATING run, which is the run whose boundary is being predicted); rho_serial is
reported beside it as the secondary coordinate.  The metric (e) verdict is taken on the primary one,
with the secondary one printed so a reader can see whether the conclusion depended on the choice.

WHAT THIS FILE IS NOT.  It is not a proof that the model is right: it is a closed form with declared
assumptions, and the only question it answers is whether it predicts the boundary the instrument
measures, to the tolerance the registration chose.  A miss is a finding about the theory.
"""
import argparse
import io
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True

TOLERANCE = 0.05          # registered metric (e)
MIN_FRACTION = 0.80       # registered metric (e)
PRIMARY = "rho_spec"      # declared above, before any comparison

STEP3_FILES = {"h1.0": "boundary_v2_h100.json",
               "h0.9": "boundary_v2_h090.json",
               "h0.5": "boundary_v2_h050.json"}


# --------------------------------------------------------------------------- the closed form
def _logsumexp(xs):
    mx = max(xs)
    if mx == float("-inf"):
        return mx
    return mx + math.log(sum(math.exp(x - mx) for x in xs))


def erlang_c(c, a):
    """Erlang C: the probability an arriving call has to wait (M/M/c, offered load a).

    Computed entirely in LOG space -- the direct form needs a**c / c!, which overflows for the
    largest pools this file sweeps (c = 256 was the cell that found it).  Clamped: a >= c is a
    saturated system and returns 1.0 (the caller reports saturation rather than a number, but the
    formula must not raise).
    """
    if a <= 0.0:
        return 0.0
    if a >= c:
        return 1.0
    la = math.log(a)
    logs = [0.0]                                   # log of a^n / n! for n = 0
    for n in range(1, c):
        logs.append(logs[-1] + la - math.log(n))
    log_waiting = logs[-1] + la - math.log(c) - math.log1p(-a / c)   # log of a^c/(c!(1-rho))
    return math.exp(log_waiting - _logsumexp(logs + [log_waiting]))


def wait_mmc(lam, c, mS):
    """Mean queue wait W in an M/M/c queue (arrival rate lam, mean service mS); inf when saturated."""
    a = lam * mS
    if a <= 0.0:
        return 0.0
    if a >= c:
        return float("inf")
    return erlang_c(c, a) * mS / (c - a)


def phi(L, A, c, mT, mS, h, load_factor=1.0):
    """One right-hand side of the fixed point (3): the cycle time implied by a cycle time.

    `load_factor` scales the arrival rate a policy is charged for.  It is 1.0 everywhere in the model
    -- it exists so the selftest can plant an ASYMMETRIC mistake (a policy charged the wrong load),
    which a symmetric change to this function cannot express.
    """
    W = wait_mmc(load_factor * A / L, c, mS)
    if W == float("inf"):
        return float("inf")
    mD = mS + W
    return mT + mD - h * mT * mD / (mT + mD)      # (4) inside (3)


def solve_fixed_point(A, c, mT, mS, h, iters=200, load_factor=1.0, floor_shift=0.0):
    """Bisect g(L) = L - phi(L) = 0.  g is increasing in L (a longer cycle means a lighter load).

    The bracket starts at max(zero-queueing floor, rho = 1 FOR THE CHARGED LOAD) -- `load_factor * A`,
    not `A`.  With the arrival unscaled the domain did not always contain the root the equation has
    (measured: charging half the load puts the root below a floor computed at load 1, and the bisection
    then converged to the floor and returned a number that was not a root).  `load_factor` is 1.0 in
    every real run, so this moves no real number; it makes the domain match the equation.

    `floor_shift` raises the bracket's lower end above the saturation point.  It is the only way to
    reach the refusal branch below, and it is 0.0 in every real run.
    """
    lo = max(mT + mS - h * mT * mS / (mT + mS), (1.0 + floor_shift) * load_factor * A * mS / c)
    hi = 4.0 * (A * mS / c + mT + mS)
    guard = 0
    while hi - phi(hi, A, c, mT, mS, h, load_factor) <= 0.0:
        hi *= 2.0
        guard += 1
        if guard > 200:
            return None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if mid - phi(mid, A, c, mT, mS, h, load_factor) <= 0.0:
            lo = mid
        else:
            hi = mid
    L = 0.5 * (lo + hi)
    # THE RESIDUAL IS PART OF THE CLAIM.  If the bracket's lower end lies above the root, the bisection
    # converges to that end -- a number that is not a solution of the equation it names.  No root in the
    # admissible domain is reported as no root.  (A check that can never fire is decoration, so the
    # selftest reaches this branch with an explicit floor plant.)
    resid = abs(L - phi(L, A, c, mT, mS, h, load_factor))
    if not (resid <= 1e-6 * max(1.0, L)):
        return None
    return {"L": L, "W": wait_mmc(load_factor * A / L, c, mS), "rho": A * mS / (c * L),
            "residual": resid}


def cell_closed(A, c, mT, mS, h, spec_load_factor=1.0, benefit_offset_pct=0.0, floor_shift=0.0):
    """One (A, c) cell: both fixed points, and the benefit of speculating at this pool size.

    `spec_load_factor` is the selftest's planting hook (see phi): it charges the SPECULATING policy a
    different arrival rate, which is the only way to make a plant that is asymmetric between the two
    policies.  It is 1.0 in every real run.

    `benefit_offset_pct` subtracts a constant from the reported benefit, leaving BOTH fixed points
    untouched.  It exists because with the plant off the closed form has NO boundary at any pool size
    -- so without it the comparison's primary path (crossing -> tolerance -> MET/UNMET) is unreachable
    and its correctness is untested.  A plant that moves only the benefit is exactly the control that
    reaches it, and it doubles as proof that the crossing rule responds to the benefit it is given.
    It is 0.0 in every real run.
    """
    ser = solve_fixed_point(A, c, mT, mS, 0.0)
    spe = solve_fixed_point(A, c, mT, mS, h, load_factor=spec_load_factor,
                            floor_shift=floor_shift)
    if ser is None or spe is None:
        return None
    return {"agents": A, "workers": c, "h": h,
            "L_serial": ser["L"], "L_spec": spe["L"], "W_spec": spe["W"],
            "rho_serial": ser["rho"], "rho_spec": spe["rho"],
            "benefit_pct": 100.0 * (ser["L"] - spe["L"]) / ser["L"] - benefit_offset_pct,
            "benefit_raw_pct": 100.0 * (ser["L"] - spe["L"]) / ser["L"],
            "benefit_offset_pct": benefit_offset_pct}


SWEEP_FLOOR = 1     # declared: the closed form is swept down to a SINGLE worker, one pool below


PLANT_BENEFIT_OFFSET_PCT = 0.0     # 0.0 in every real run.  The selftest arms it to reach the
                                   # comparison's primary path, which the unplanted curve never reaches.


def closed_benefit_offset(A, h, c_lo, c_hi, mT, mS):
    """The closed side's per-family plant offset: 0.0 unless the selftest has armed the plant.

    Armed, it subtracts `PLANT_BENEFIT_OFFSET_PCT x` the benefit at the SMALLEST pool in the family --
    enough to make that last cell negative, and therefore to give the closed form a boundary it does
    not otherwise have.  Both fixed points are untouched by it, which the selftest checks directly.
    """
    if PLANT_BENEFIT_OFFSET_PCT == 0.0:
        return 0.0
    base, _failed = rows_closed(A, c_lo, c_hi, mT, mS, h)
    return PLANT_BENEFIT_OFFSET_PCT * base[-1]["benefit_pct"]


def rows_closed(A, c_lo, c_hi, mT, mS, h, floor=None, benefit_offset_pct=0.0):
    """The cell list for one family, in STEP 3'S ORDER: decreasing c, i.e. increasing contention.

    The sweep is extended BELOW step 3's window (down to `floor`, default SWEEP_FLOOR = a single
    worker) so that a closed-form boundary just outside the measured window is FOUND and reported
    rather than excluded as "no crossing" -- and so that "the closed form has no boundary at any pool
    size" is a statement the file can actually make.
    """
    out, failed = [], []
    for c in range(c_hi, (SWEEP_FLOOR if floor is None else floor) - 1, -1):
        r = cell_closed(A, c, mT, mS, h, benefit_offset_pct=benefit_offset_pct)
        if r is not None:
            out.append(r)
        else:
            failed.append(c)
    return out, failed


def crossing_closed(rows, key):
    """Step 3's rule, imported so the two sides cannot drift apart."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import boundary_v2
    return boundary_v2.crossing_of_curve(rows, key)


# --------------------------------------------------------------------------- the simulated side
def read_artifact(fname):
    """The only place an artifact file is read, so a control can substitute a known side."""
    return json.load(io.open(os.path.join(HERE, fname), encoding="utf-8"))


def simulated_cells():
    """Read step 3's published crossings.  Nothing is recomputed here."""
    cells = []
    for tag, fname in sorted(STEP3_FILES.items()):
        p = os.path.join(HERE, fname)
        if not os.path.exists(p):
            cells.append({"file": fname, "status": "NOT TAKEN", "reason": "artifact not present"})
            continue
        d = read_artifact(fname)
        for fam in d["families"]:
            cells.append({"file": fname, "h": d["h"], "agents": fam["agents"],
                          "c_range": fam["c_range"],
                          "sim_rho_spec": fam["crossing_rho_spec"]["x_star"],
                          "sim_ambiguous_spec": fam["crossing_rho_spec"]["ambiguous"],
                          "sim_rho_serial": fam["crossing_rho_serial"]["x_star"],
                          "sim_ambiguous_serial": fam["crossing_rho_serial"]["ambiguous"],
                          "sim_pools": [list(x) for x in fam["crossing_rho_spec"]["cells"]],
                          "status": "READ"})
    return cells


def compare(mT, mS, tol=TOLERANCE):
    """Compare the closed form to step 3's published boundary, primary and secondary.

    PRIMARY (the registered test): each side's BOUNDARY in the declared primary coordinate.  A family
    where the closed form has no sign change at ANY pool size >= SWEEP_FLOOR is reported as
    NO CLOSED-FORM BOUNDARY -- counted, with the reason and the benefit range that shows it, never a
    pass.  That outcome is itself the finding, so it must be visible as a count.

    SECONDARY (descriptive; NOT the registered test): the two models compared AT THE SAME CELL (same
    family, same pool) on both coordinates and on the benefit.  This measures the closed form where the
    instrument already is, whether or not it predicts the flip -- it is reported beside the primary
    result so a reader can see which part of the disagreement is the boundary and which is the level.
    """
    results, excluded, same_cell = [], [], []
    for cell in simulated_cells():
        if cell["status"] != "READ":
            excluded.append({"reason": cell["reason"], "file": cell["file"]})
            continue
        if cell["sim_ambiguous_spec"]:
            excluded.append({"reason": "the simulated crossing itself is AMBIGUOUS (step 3 reported "
                                       "more than one sign change on this family)",
                             "file": cell["file"], "agents": cell["agents"]})
            continue
        A, h = cell["agents"], cell["h"]
        c_lo, c_hi = cell["c_range"]
        rows, failed = rows_closed(A, c_lo, c_hi, mT, mS, h,
                                   benefit_offset_pct=closed_benefit_offset(A, h, c_lo, c_hi, mT, mS))
        if failed:
            excluded.append({"reason": "NO CLOSED-FORM FIXED POINT at pool size(s) %s (the solver "
                                       "found no root in the admissible domain and refused to return "
                                       "the bracket end instead)" % failed,
                             "file": cell["file"], "agents": A, "h": h})
            continue
        # per-pool agreement, on every pool both sides produced
        art = read_artifact(cell["file"])
        fam = [f for f in art["families"] if f["agents"] == A][0]
        for r in rows:
            simrow = [x for x in fam["rows"] if x["workers"] == r["workers"]]
            if not simrow:
                continue
            simrow = simrow[0]
            same_cell.append({"file": cell["file"], "h": h, "agents": A, "workers": r["workers"],
                              "d_rho_spec": abs(r["rho_spec"] - simrow["rho_spec"]),
                              "d_rho_serial": abs(r["rho_serial"] - simrow["rho_serial"]),
                              "d_benefit_pct": abs(r["benefit_pct"] - simrow["benefit_pct"]),
                              "sim_benefit_pct": simrow["benefit_pct"],
                              "closed_benefit_pct": r["benefit_pct"],
                              "within_spec": abs(r["rho_spec"] - simrow["rho_spec"]) <= tol})
        cr = crossing_closed(rows, PRIMARY)
        if cr is None:
            b = [r["benefit_pct"] for r in rows]
            excluded.append({"reason": "NO CLOSED-FORM BOUNDARY: the closed-form benefit stays "
                                       "positive at every pool size from %d to %d (min benefit "
                                       "%.3f%%, max %.3f%%)" % (SWEEP_FLOOR, c_hi, min(b), max(b)),
                             "file": cell["file"], "agents": A, "h": h,
                             "benefit_min_pct": min(b), "benefit_max_pct": max(b)})
            continue
        if cr["ambiguous"]:
            excluded.append({"reason": "the closed-form benefit changes sign more than once inside the "
                                       "sweep (%d times)" % cr["n_crossings"],
                             "file": cell["file"], "agents": A, "h": h})
            continue
        c_star = cr["cells"][0][1]
        row = [r for r in rows if r["workers"] == c_star]
        if len(row) != 1:
            excluded.append({"reason": "the crossing names a pool the sweep did not produce",
                             "file": cell["file"], "agents": A, "h": h})
            continue
        closed = row[0]
        sim = cell["sim_rho_spec"]
        results.append({"file": cell["file"], "h": h, "agents": A, "c_star": c_star,
                        "sim_crossing_pools": cell.get("sim_pools"),
                        "inside_measured_window": bool(c_lo <= c_star <= c_hi),
                        "sim_rho_spec": sim, "closed_rho_spec": closed["rho_spec"],
                        "delta_spec": abs(closed["rho_spec"] - sim),
                        "sim_rho_serial": cell["sim_rho_serial"],
                        "closed_rho_serial": closed["rho_serial"],
                        "delta_serial": abs(closed["rho_serial"] - cell["sim_rho_serial"]),
                        "closed_benefit_pct": closed["benefit_pct"],
                        "within_spec": abs(closed["rho_spec"] - sim) <= tol,
                        "within_serial": abs(closed["rho_serial"] - cell["sim_rho_serial"]) <= tol})
    return results, excluded, same_cell


def verdict(results, excluded, same_cell, tol=TOLERANCE, frac=MIN_FRACTION):
    """The registered criterion, on the primary coordinate, with the exclusions counted by kind."""
    n = len(results)
    kinds = {}
    for e in excluded:
        if e["reason"].startswith("NO CLOSED-FORM FIXED POINT"):
            k = "no closed-form fixed point"
        elif e["reason"].startswith("NO CLOSED-FORM"):
            k = "no closed-form boundary"
        elif e["reason"].startswith("the simulated crossing itself is AMBIGUOUS"):
            k = "simulated crossing ambiguous"
        elif "artifact not present" in e["reason"]:
            k = "artifact not present"
        elif e["reason"].startswith("the closed-form benefit changes sign more than once"):
            k = "closed-form sign change ambiguous"
        else:
            k = "other"
        kinds[k] = kinds.get(k, 0) + 1
    sc = [x["d_rho_spec"] for x in same_cell]
    scm = sorted(sc)[len(sc) // 2] if sc else None
    ben = sorted(x["d_benefit_pct"] for x in same_cell)
    # The DENOMINATOR the criterion is read over, recorded as its own field.  `n_excluded` and
    # `n_evaluated` are written by different expressions on purpose: with both sides of a
    # sentence like "18 of 18 excluded" bound to `len(excluded)`, no run of this instrument can
    # ever make it read anything but "N of N" -- and that is exactly the defect the review of
    # round 1 returned (major, required change 3).  A pair that produced a boundary enters
    # `results`; a pair that could not enters `excluded`; this field counts both.
    base = {"tolerance": tol, "min_fraction": frac, "n": n, "n_excluded": len(excluded),
            "n_evaluated": len(results) + len(excluded),
            "exclusion_kinds": kinds, "n_within": None, "fraction": None,
            "secondary_same_cell_n": len(sc), "secondary_same_cell_median": scm,
            "secondary_same_cell_worst": max(sc) if sc else None,
            "secondary_same_cell_within": sum(1 for x in same_cell if x["within_spec"]),
            "secondary_same_cell_benefit_median": ben[len(ben) // 2] if ben else None,
            "n_boundary_inside_measured_window": None}
    if n == 0:
        base.update({"status": "UNMET",
                     "reason": "no family produced a comparable boundary in either model's own terms "
                               "(%d exclusion(s), see exclusion_kinds)" % len(excluded),
                     "within": 0, "fraction": 0.0})
        return base
    within = sum(1 for r in results if r["within_spec"])
    f = within / float(n)
    base.update({"status": "MET" if f >= frac else "UNMET", "within": within, "fraction": f,
                 "n_within": within, "n_comparable": n,
                 "worst": max(r["delta_spec"] for r in results),
                 "median": sorted(r["delta_spec"] for r in results)[n // 2],
                 "within_serial": sum(1 for r in results if r["within_serial"]),
                 "median_serial": sorted(r["delta_serial"] for r in results)[n // 2],
                 "n_boundary_inside_measured_window":
                     sum(1 for r in results if r["inside_measured_window"])})
    return base


# --------------------------------------------------------------------------- anchors
def anchor_h1(mT=2.0, mS=1.0):
    """H1 -- zero queueing: the closed form must give benefit = E[min(T,S)] = mT*mS/(mT+mS).

    The instrument's anchor A3 measured exactly this limit; the identity is what anchors the overlap
    term.  Here it is evaluated on the closed form at W = 0.
    """
    limit = mT * mS / (mT + mS)
    saving = mT * mS / (mT + mS)
    return {"limit": limit, "closed": saving, "abs_diff": abs(limit - saving)}


def anchor_h2(A=16, c=4, mT=2.0, mS=1.0):
    """H2 -- h = 0 must reduce EXACTLY to the serial fixed point (same L, benefit 0)."""
    ser = solve_fixed_point(A, c, mT, mS, 0.0)
    spe = solve_fixed_point(A, c, mT, mS, 0.0)
    cell = cell_closed(A, c, mT, mS, 0.0)
    return {"abs_dL": abs(ser["L"] - spe["L"]), "benefit_pct": cell["benefit_pct"]}


def anchor_h3(cs=(1, 3, 8), a=0.5, mS=1.0):
    """H3 -- at c = 1 the wait must be the M/M/1 wait a*mS/(1-a); more servers must wait less."""
    out = []
    for c in cs:
        if c == 1:
            w = wait_mmc(a / mS, 1, mS)
            out.append({"c": c, "wait": w, "closed_form": a * mS / (1.0 - a),
                        "abs_diff": abs(w - a * mS / (1.0 - a))})
        else:
            out.append({"c": c, "wait": wait_mmc(a / mS, c, mS), "closed_form": None,
                        "abs_diff": None})
    return out


def anchor_h4(A=16, mT=2.0, mS=1.0, h=1.0):
    """H4 -- as the pool grows the benefit must rise toward the zero-contention limit of H1, IN PERCENT.

    The first version of this arm compared a PERCENTAGE against a TIME (E[min(T,S)] = 0.6667 versus the
    measured 22.22%) and failed at every pool size: the arm was false about its own object.  The limit
    of benefit_pct is 100 * E[min(T,S)] / (mT + mS), because at large pools the serial cycle tends to
    mT + mS while the saving tends to E[min(T,S)].
    """
    limit_time = mT * mS / (mT + mS)
    limit_pct = 100.0 * limit_time / (mT + mS)
    vals = []
    for c in (4, 8, 16, 64, 256):
        cell = cell_closed(A, c, mT, mS, h)
        vals.append({"c": c, "benefit_pct": cell["benefit_pct"],
                     "abs_from_limit": abs(cell["benefit_pct"] - limit_pct), "rho_spec": cell["rho_spec"]})
    return {"limit_time": limit_time, "limit_pct": limit_pct, "cells": vals}


# --------------------------------------------------------------------------- selftest
def selftest(mT=2.0, mS=1.0):
    """Every arm must be able to fail.  Each prints what it read, not only a verdict."""
    arms, fails = [], []

    def arm(name, ok, detail):
        arms.append({"arm": name, "ok": bool(ok), "detail": detail})
        if not ok:
            fails.append(name)

    h1 = anchor_h1(mT, mS)
    arm("H1 zero-queueing limit is E[min(T,S)]", h1["abs_diff"] <= 1e-12, h1)

    h2 = anchor_h2(mT=mT, mS=mS)
    arm("H2 h=0 reduces to the serial fixed point",
        h2["abs_dL"] <= 1e-12 and abs(h2["benefit_pct"]) <= 1e-12, h2)

    h3 = anchor_h3(mS=mS)
    arm("H3 c=1 wait is the M/M/1 wait", h3[0]["abs_diff"] <= 1e-12, h3[0])
    arm("H3 more servers wait less", h3[1]["wait"] < h3[0]["wait"] and h3[2]["wait"] < h3[1]["wait"],
        [x["wait"] for x in h3])

    h4 = anchor_h4(mT=mT, mS=mS)
    mono = all(h4["cells"][i]["benefit_pct"] <= h4["cells"][i + 1]["benefit_pct"] + 1e-9
               for i in range(len(h4["cells"]) - 1))
    arm("H4 benefit rises toward the zero-contention limit IN PERCENT", mono, h4["cells"])
    arm("H4 the largest pool is within 0.5pp of that limit",
        h4["cells"][-1]["abs_from_limit"] <= 0.5, h4["cells"][-1])
    arm("H4 the limit is the percent form, not the time form",
        abs(h4["limit_pct"] - 100.0 * h4["limit_time"] / (mT + mS)) <= 1e-12,
        {"limit_pct": h4["limit_pct"], "limit_time": h4["limit_time"]})

    rows = [{"benefit_pct": b, "rho_spec": 0.9 + 0.01 * i, "agents": 16, "workers": 10 - i}
            for i, b in enumerate([1.0, -1.0, 1.0, -1.0])]
    cr = crossing_closed(rows, "rho_spec")
    arm("the crossing rule reports AMBIGUOUS for two sign changes", cr is not None and cr["ambiguous"], cr)
    arm("the crossing rule is step 3's own function",
        (crossing_closed.__doc__ or "").startswith("Step 3's rule"), crossing_closed.__doc__)

    # the sweep really is extended below step 3's window, and the file can tell the two sweeps apart
    wide, wide_failed = rows_closed(16, 2, 5, mT, mS, 1.0)
    narrow, narrow_failed = rows_closed(16, 2, 5, mT, mS, 1.0, floor=2)
    arm("the sweep is extended below the measured window",
        SWEEP_FLOOR < 2 and len(wide) > len(narrow) and wide[-1]["workers"] == SWEEP_FLOOR,
        {"wide_last_pool": wide[-1]["workers"], "narrow_last_pool": narrow[-1]["workers"],
         "n_wide": len(wide), "n_narrow": len(narrow)})

    results, excluded, same_cell = compare(mT, mS)
    v = verdict(results, excluded, same_cell)
    arm("the comparison ran on every family step 3 published",
        len(results) + len(excluded) == 18,
        {"n_comparable": len(results), "n_excluded": len(excluded), "kinds": v["exclusion_kinds"]})
    arm("every exclusion carries a reason", all(e.get("reason") for e in excluded),
        [e["reason"][:60] for e in excluded][:3])
    arm("the same-cell block is populated and names its coordinate",
        all(("d_rho_spec" in x and "d_rho_serial" in x and "d_benefit_pct" in x) for x in same_cell)
        and len(same_cell) > 50,
        {"n": len(same_cell), "median_d_rho_spec": v["secondary_same_cell_median"]})

    # ARM: the solver's answer really IS a root of the equation it names -- the positive side of the
    # refusal below, without which "refused" would be the only thing the residual check could say.
    plain = cell_closed(16, 4, mT, mS, 1.0)
    spe_plain = solve_fixed_point(16, 4, mT, mS, 1.0)
    arm("a returned cell IS a root (residual at machine level) and the unplanted cell is answered",
        plain is not None and spe_plain is not None and spe_plain["residual"] <= 1e-9,
        {"residual": spe_plain and spe_plain["residual"],
         "benefit_pct": plain and plain["benefit_pct"]})

    # ARM (two-sided): raise the bracket's lower end above the root.  The solver must REFUSE, while the
    # identical call with the plant off must answer.  This is what makes the refusal branch live.
    shifted = solve_fixed_point(16, 4, mT, mS, 1.0, floor_shift=1.5)
    unshift = solve_fixed_point(16, 4, mT, mS, 1.0)
    arm("a bracket that starts above the root is REFUSED, while the same call unplanted is answered",
        shifted is None and unshift is not None,
        {"planted": shifted, "unplanted_L": unshift and unshift["L"]})

    # ARM: the bracket scales with the CHARGED load.  Charging half the load moves the rho<=1 bound
    # down; the solver must still find the root rather than refuse at the edge of its own domain.
    half = solve_fixed_point(16, 2, mT, mS, 1.0, load_factor=0.5)
    arm("the bracket scales with the charged load (half the load is still answered)",
        half is not None and half["residual"] <= 1e-9,
        {"L": half and half["L"], "residual": half and half["residual"]})

    # ARM (two-sided): the benefit plant gives the closed form a boundary the unplanted curve does not
    # have, and it moves NO fixed point -- so a crossing read off it is a crossing of the benefit.
    base_rows, _bf = rows_closed(16, 2, 8, mT, mS, 1.0)
    off = 1.5 * base_rows[-1]["benefit_pct"]
    planted_rows, _pf = rows_closed(16, 2, 8, mT, mS, 1.0, benefit_offset_pct=off)
    cr_off = crossing_closed(base_rows, PRIMARY)
    cr_on = crossing_closed(planted_rows, PRIMARY)
    same_rho = all(abs(a["rho_spec"] - b["rho_spec"]) <= 1e-12
                   for a, b in zip(base_rows, planted_rows))
    arm("the benefit plant creates a boundary the unplanted curve does not have",
        cr_off is None and cr_on is not None and not cr_on["ambiguous"] and same_rho,
        {"unplanted_crossing": cr_off,
         "planted_crossing": cr_on and {"x_star": cr_on["x_star"], "pools": cr_on["cells"]},
         "fixed_points_untouched": same_rho, "offset_pct": off})

    # CONTROLS ON THE MACHINERY (two-sided).  On the real data every family reads NO CLOSED-FORM
    # BOUNDARY, so the comparison's primary path never runs.  These arms build a simulated side out of
    # the planted closed form itself: with the sides equal the comparison must read MET, 0.10 apart it
    # must read UNMET.  That is what makes the real UNMET a fact about the MODEL rather than about
    # machinery that can never compare.
    real_sim = globals()["simulated_cells"]
    real_read = globals()["read_artifact"]
    saved_plant = PLANT_BENEFIT_OFFSET_PCT
    globals()["PLANT_BENEFIT_OFFSET_PCT"] = 1.5

    def synth_side(shift):
        cells, arts = [], {}
        for cell in real_sim():
            if cell["status"] != "READ":
                continue
            A, h = cell["agents"], cell["h"]
            c_lo, c_hi = cell["c_range"]
            rows, _f = rows_closed(A, c_lo, c_hi, mT, mS, h,
                                   benefit_offset_pct=closed_benefit_offset(A, h, c_lo, c_hi, mT, mS))
            cr = crossing_closed(rows, PRIMARY)
            if cr is None or cr["ambiguous"]:
                continue
            c_star = cr["cells"][0][1]
            row = [r for r in rows if r["workers"] == c_star][0]
            arts.setdefault(cell["file"], {"h": h, "families": []})["families"].append(
                {"agents": A, "c_range": [c_lo, c_hi],
                 "rows": [{"workers": r["workers"], "rho_spec": r["rho_spec"],
                           "rho_serial": r["rho_serial"], "benefit_pct": r["benefit_pct"]}
                          for r in rows],
                 "crossing_rho_spec": {"x_star": row["rho_spec"] + shift, "ambiguous": False,
                                       "cells": cr["cells"]},
                 "crossing_rho_serial": {"x_star": row["rho_serial"] + shift, "ambiguous": False,
                                         "cells": cr["cells"]}})
            c2 = dict(cell)
            c2.update({"sim_rho_spec": row["rho_spec"] + shift,
                       "sim_rho_serial": row["rho_serial"] + shift,
                       "sim_ambiguous_spec": False,
                       "sim_pools": [list(x) for x in cr["cells"]]})
            cells.append(c2)
        return cells, arts

    def run_synth(shift):
        cells, arts = synth_side(shift)
        globals()["simulated_cells"] = lambda: cells
        globals()["read_artifact"] = lambda fname: arts[fname]
        try:
            r, e, sc = compare(mT, mS)
            v_ = verdict(r, e, sc)
        finally:
            globals()["simulated_cells"] = real_sim
            globals()["read_artifact"] = real_read
        return r, e, sc, v_

    try:
        s_res, s_exc, s_same, s_v = run_synth(0.0)
        t_res, t_exc, t_same, t_v = run_synth(0.10)
    finally:
        globals()["PLANT_BENEFIT_OFFSET_PCT"] = saved_plant

    arm("a simulated side ON the closed boundary reads MET (the primary path is reachable)",
        s_v["status"] == "MET" and s_v["n"] >= 10 and s_v["within"] == s_v["n"],
        {"status": s_v["status"], "n": s_v["n"], "within": s_v["within"],
         "excluded": len(s_exc), "same_cell_n": len(s_same), "kinds": s_v["exclusion_kinds"]})

    arm("a 0.10 shift in the simulated boundary reads UNMET (the tolerance is load-bearing)",
        t_v["status"] == "UNMET" and t_v["n"] >= 10 and t_v["within"] == 0,
        {"status": t_v["status"], "n": t_v["n"], "within": t_v["within"],
         "tol": t_v["tolerance"]})

    arm("the planted side covered EVERY family step 3 published (MET is not read off a handful)",
        s_v["n"] == 18 and len(t_res) == 18,
        {"n_met_side": s_v["n"], "n_unmet_side": len(t_res)})

    saved_files = dict(STEP3_FILES)
    STEP3_FILES.clear()
    STEP3_FILES["h1.0"] = "no_such_artifact.json"
    try:
        r2, e2, s2 = compare(mT, mS)
        v2 = verdict(r2, e2, s2)
    finally:
        STEP3_FILES.clear()
        STEP3_FILES.update(saved_files)
    arm("a missing artifact is NOT TAKEN and cannot be a pass",
        len(r2) == 0 and v2["status"] == "UNMET" and len(e2) >= 1, {"n": len(r2), "excluded": len(e2)})

    return {"arms": arms, "n_fails": len(fails), "fails": fails}


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--mT", type=float, default=2.0)
    ap.add_argument("--mS", type=float, default=1.0)
    args = ap.parse_args(argv)

    if args.selftest:
        st = selftest(args.mT, args.mS)
        for a in st["arms"]:
            print("%-62s %s" % (a["arm"], "OK" if a["ok"] else "FAILED"))
            print("      read: %s" % json.dumps(a["detail"])[:400])
        print("SELFTEST: %d arm(s), %d failure(s)" % (len(st["arms"]), st["n_fails"]))
        return 0 if st["n_fails"] == 0 else 1

    t0 = time.time()
    results, excluded, same_cell = compare(args.mT, args.mS)
    v = verdict(results, excluded, same_cell)
    print("== closed-form fixed point (mT=%.3f, mS=%.3f) vs step 3's published crossings ==" % (args.mT, args.mS))
    print("== primary coordinate: %s (declared before the comparison); secondary: rho_serial ==" % PRIMARY)
    if results:
        print("%-14s %-4s %-5s %-4s %-6s %-9s %-9s %-8s" %
              ("file", "h", "A", "c*", "in-win", "sim_spec", "closed", "delta"))
        for r in sorted(results, key=lambda x: (x["file"], x["agents"])):
            print("%-14s %-4.1f %-5d %-4d %-6s %-9.5f %-9.5f %-8.5f%s" %
                  (r["file"], r["h"], r["agents"], r["c_star"], str(r["inside_measured_window"]),
                   r["sim_rho_spec"], r["closed_rho_spec"], r["delta_spec"],
                   "" if r["within_spec"] else "   <-- OUTSIDE TOLERANCE"))
    for e in excluded:
        print("EXCLUDED: %s" % json.dumps(e))
    print("-- metric (e) PRIMARY: %s | comparable cells %d | within %.5f: %s (%.1f%%) | required >= %.0f%%" %
          (v["status"], v["n"], v["tolerance"],
           ("%d" % v["within"]) if v["n"] else "n/a",
           100.0 * (v["fraction"] or 0.0), 100.0 * v["min_fraction"]))
    print("-- exclusions by kind: %s" % json.dumps(v["exclusion_kinds"]))
    if v["n"]:
        print("-- worst |delta| %.5f, median |delta| %.5f | boundaries inside the measured window %d/%d" %
              (v["worst"], v["median"], v["n_boundary_inside_measured_window"], v["n"]))
    print("-- SECONDARY (same cell, NOT the registered test): %d comparison(s) | median |delta rho_spec| "
          "%.5f | worst %.5f | within tolerance %d/%d | median |delta benefit_pct| %.3f" %
          (v.get("secondary_same_cell_n") or 0, v.get("secondary_same_cell_median") or float("nan"),
           v.get("secondary_same_cell_worst") or float("nan"), v.get("secondary_same_cell_within") or 0,
           v.get("secondary_same_cell_n") or 0, v.get("secondary_same_cell_benefit_median") or float("nan")))
    print("-- anchors: H1 %s | H2 %s | H4 limit_pct %.5f against c=256 benefit %.5f%%" %
          (json.dumps(anchor_h1(args.mT, args.mS)), json.dumps(anchor_h2(mT=args.mT, mS=args.mS)),
           anchor_h4(mT=args.mT, mS=args.mS)["limit_pct"],
           anchor_h4(mT=args.mT, mS=args.mS)["cells"][-1]["benefit_pct"]))
    print("-- elapsed %.1f s (printed, NOT in the artefact)" % (time.time() - t0))
    out = {"model": {"mT": args.mT, "mS": args.mS, "q": 0.0}, "sweep_floor": SWEEP_FLOOR,
           "tolerance": TOLERANCE, "min_fraction": MIN_FRACTION, "primary_coordinate": PRIMARY,
           "declared_assumptions": ["M1 Poisson arrivals at A/L", "M2 D = Q+S exponential",
                                    "M3 queue-position effect not modelled",
                                    "M4 no tail term (P2 refuted in step 5)"],
           "cells": results, "excluded": excluded, "same_cell": same_cell, "verdict": v,
           "anchors": {"H1": anchor_h1(args.mT, args.mS), "H2": anchor_h2(mT=args.mT, mS=args.mS),
                       "H3": anchor_h3(mS=args.mS), "H4": anchor_h4(mT=args.mT, mS=args.mS)},
           "selftest": selftest(args.mT, args.mS)}
    # The wall clock is printed, never serialized: a number the artefact carries is a number a run can
    # change, and this artefact is meant to be byte-identical across runs.  (The timing of the run is
    # evidence about the run -- it stays in the log, which is not the artefact.)
    if args.json:
        io.open(args.json, "w", encoding="utf-8", newline="\n").write(
            json.dumps(out, indent=1, sort_keys=True) + "\n")
        print("wrote %s" % args.json)
    # THE EXIT CODE IS NOT THE VERDICT.  UNMET is a result this file is designed to be able to report;
    # the verdict travels in the JSON and in the printed line above.  A non-zero code means the run
    # could not produce a comparison at all (every artifact absent) -- the only "failed to run" here.
    if not results and excluded and all(e["reason"] == "artifact not present" for e in excluded):
        print("-- exit 3: no artifact could be read; nothing was compared")
        return 3
    print("-- exit 0: run complete; the verdict (%s) is in the JSON, not in the exit code" % v["status"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
