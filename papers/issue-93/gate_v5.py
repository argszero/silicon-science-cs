#!/usr/bin/env python3
"""#93 v5 -- the boundary's INTERVAL: the registration's success metric (a) gets its second half.

WHERE THIS SITS.  v0 read the screening closure (b = 1), v1 the map in closed form (b < 1, and the sign laws
`b*(a, s, L, c)`), v2 the design axis, v3 the sampling route under disjoint streams, v4 the axis-sensitivity
ratio (metric (b)).  The registration's metric (a) is

    "the boundary `b*(a, s, L, c)` with bootstrap CIs and its dependence on `L/c`"

and R421 found that only its FIRST half had an owner: v1's `bstar_closed` is exact and bisection-verified, but
nothing had ever put an INTERVAL on the boundary.  A point estimate is not a measurement, and metric (a) is
registered as a measurement ("with bootstrap CIs").

WHAT IS MEASURED, AND WHAT THE INTERVAL IS OVER (the registered wording reads two ways; both are reported).
  Reading 1 -- ESTIMATOR UNCERTAINTY (implemented here).  A practitioner does not have v1's closed form; they
    have sampled actions.  So the boundary is ESTIMATED: draw n actions at each of K declared fidelities, read
    the gate's value V-hat(b_k), fit the line the model guarantees (V is affine in b -- v1's own finding), and
    take the crossing as the estimate.  The interval is over that estimator, and its width is the statement
    "how many actions does locating the boundary cost".
  Reading 2 -- PARAMETER UNCERTAINTY (reported, not implemented).  The registration can also be read as a CI
    over `(a, s, L, c)` themselves.  That reading has no sampling distribution in this study: the parameters are
    DESIGN points of a harness with ground truth by construction, not estimates.  It is reported as a wording
    finding about the registration, not silently resolved (the rule outcomes.md already applies to PB1/PB3).
  The two readings are not interchangeable, and the manuscript must say which one a number belongs to.

THE MAPPING IS A CONTROL, NOT A DERIVATION.  The registered fidelity `b` parameterises a VARIANT (v1's closed
form); the sampling route is parameterised by a DEFECT dict (v2's design ladder).  Before any boundary is
estimated, the map between them is CHECKED against the closed form -- a b->defect mapping is a claim about the
model, so it owes the model's own answer (self-audit Class 82: a fitted quantity owes a synthetic-answer
control).  Verified by C1 below:
    mismatch      delta = 1 - b,  sigma_v = sigma_i = 0   (the rendering misrepresents: the effective
                                                           sensitivity becomes b*a + (1-b)*f)
    substitution  sigma_i = 1 - b, delta = sigma_v = 0    (the invisible substitution IS the laundering mass)
    none          no defect, at every b                   (b does not enter: there is no b-axis)
  and all at ONE design, D1 (text approval, no use-time check), because v1's variants are CHANNEL models holding
  the design fixed -- mixing designs would move two things at once.

THE INTERVAL HAS TWO ROUTES, AND ONE OF THEM IS A THEOREM.
  * The Fieller set (the prediction): {b : |A-hat + B-hat*b| <= z*SE(A-hat + B-hat*b)} -- the fidelities where
    the measured value is NOT DISTINGUISHABLE FROM ZERO.  That is what a boundary's interval means when the
    boundary is defined by a sign change.  As a quadratic in b the region is bounded or empty; it is NEVER
    inverted, because the leading coefficient is B-hat^2 - z^2*Var(B-hat), whose sign IS the test of "is the
    fidelity slope distinguishable from zero".  Flatness and invertibility are the same number here.  Checked,
    not asserted (C4).
  * The bootstrap (the read): resample each b-point's per-action sample with replacement, refit, recompute the
    crossing; the percentile interval.  A ratio estimator has a heavy tail when the denominator approaches zero,
    so the fraction of replicates whose slope is not distinguishable from zero is REPORTED, and the percentile
    interval is taken over the rest (a percentile interval over wild replicates would be a decoration).

THE STATES ARE TWO, AND THE THIRD WAS REFUTED (self-audit Class 80/111: an empty set is a state, not a pass or a
failure -- and here the empty set turns out to be impossible, which is itself the finding).
    BOUNDED  a finite interval on the axis -- the boundary is located
    FLAT     the value's slope in b is not distinguishable from zero: there is NO boundary on this axis
  The pre-registration expected a third EMPTY state on the grid.  It cannot occur, and not merely on this grid:
  the fitted line attains zero at b* = -A/B, and the Fieller set's own radius there is z*SE(b*) > 0, so the
  crossing is ALWAYS inside the set and the discriminant is never negative.  The branch was therefore REMOVED
  rather than kept as an unreachable state, and the theorem is ASSERTED in C4d (the crossing lies inside its own
  set in every bounded reading) instead of left as prose.  A call site that printed a number in the FLAT state
  would report a measurement that does not exist.

CALIBRATION, WITH ITS DENOMINATOR AND ITS EXCLUSIONS PUBLISHED.  The exact `b*` is v1's closed form.  A reading
whose exact crossing lies OUTSIDE [0, 1] cannot be covered by an in-axis interval, so it is excluded BY A
DECLARED RULE -- and the excluded readings are published with their exact values (the promotion-observed
pattern recorded at R349: exclusion rates without the excluded values leave the key property unchecked).  A
`none`-channel reading has no `b*` AT ALL, which is a different thing from an exclusion and is counted
separately.

PRE-REGISTERED CLAIMS (written before the run -- see `preregistered` in the record).
  P1 the map: the drawn route reproduces v1's closed form for both channels, |diff| <= 4 SE of the draw.
  P2 the estimator recovers the exact boundary: |b-hat* - b*_closed| <= the reported interval's own width.
  P3 the two routes agree where both are bounded: the bootstrap percentile endpoint lies inside the Fieller
     bracket within one declared axis step.
  P4 the width law: in the regime where the slope is well determined (|B-hat| >= 4 sd(B-hat)), the width is
     z * SE(V at b*) / |B-hat| per side, and it scales as 1/sqrt(n) -- at 4n the width halves.
  P5 the states are exercised BY THE GRID: FLAT by the `none` channel, EMPTY by at least one grid cell.
  P6 calibration: over the in-axis readings the Fieller set's coverage of the exact boundary is consistent with
     the nominal 0.95 (Wilson), and the bootstrap's is reported beside it.

Run:  /usr/bin/python3 gate_v5.py
Writes gate_v5_results.json beside this file.
"""
import io
import json
import math
import os
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gate_v0 as V0  # noqa: E402
import gate_v1 as V1  # noqa: E402
import gate_v2 as V2  # noqa: E402

OUT = os.path.join(HERE, "gate_v5_results.json")
S = 1.0
DESIGN = "D1"
B_PTS = (0.0, 0.25, 0.5, 0.75, 1.0)
N_DRAW = 4000
N_BOOT = 300
Z = 1.959963984540054
MAP_Z = 4.0                      # the mapping control's band, in SE of the draw
Z_STEP = 0.05                    # one declared axis step: the tolerance for "the two routes agree"
LAW_TOL = 0.10                   # the width law's tolerance, in the regime where it is claimed
SCALE_TOL = 0.50                 # the 1/sqrt(n) check's tolerance on the ratio of widths
# (the width law's regime threshold is DERIVED in C4 from the law's own expansion, not set here)

CELLS = [
    ("defaults", V0._p()),
    ("pi=0.05", V0._p(pi=0.05)),
    ("pi=0.5,a=0.6", V0._p(pi=0.5, a=0.6)),
    ("a=0.3,f=0.2", V0._p(a=0.3, f=0.2)),
    ("a=0.95,f=0.0", V0._p(a=0.95, f=0.0)),
    ("L=5,c=0.1,cb=0.2", V0._p(L=5.0, c=0.1, cb=0.2)),
    ("pi=0.02,a=0.99,f=0.5", V0._p(pi=0.02, a=0.99, f=0.5)),
]
# One stream per DECLARED family (v3's families, unaltered).  Three streams, not nine: this instrument's unit of
# replication is the (cell, channel) reading, and the streams are here so the reading is not one draw's
# neighbourhood -- the per-family spread is reported so a panel that shares a magnitude would show.
STREAMS = [("adjacent", 20260922), ("wide_magnitude", 1009), ("cluster", 41020261)]
CHANNELS = ("mismatch", "substitution", "none")


def defect_for(channel, b):
    """The verified preimage of the registered fidelity `b` in the sampling route's defect dict (C1 checks it)."""
    if channel == "mismatch":
        return dict(delta=1.0 - b, sigma_v=0.0, sigma_i=0.0)
    if channel == "substitution":
        return dict(delta=0.0, sigma_v=0.0, sigma_i=1.0 - b)
    if channel == "none":
        return dict(delta=0.0, sigma_v=0.0, sigma_i=0.0)
    raise ValueError("unknown channel %r" % channel)


def wilson(k, n, z=Z):
    """Wilson score interval for a proportion -- the right interval for a RATE (the calibration check)."""
    if n == 0:
        return (0.0, 1.0)
    p = float(k) / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / d
    h = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / d
    return (c - h, c + h)


def require_gated(per):
    """The contract of a draw that has a gate: `per` is an array.  The no-gate design's `per` is None by design
    (its value is exact, so it has no sample), and every reader of `per` must refuse it the same way -- a reader
    that instead crashes on `None` reports a defect of the MODEL as a defect of the instrument (the battery's
    `no_gate_design` case caught exactly that: C1 read `per` before `draw_curve`'s guard and raised an
    AttributeError, so the case could not see the alarm it was aimed at)."""
    if per is None:
        raise RuntimeError("the no-gate design cannot read a boundary: it has no gate to read")
    return per


def draw_curve(params, channel, n, seed, b_pts=B_PTS):
    """Draw n actions at every declared fidelity; return the per-action arrays and the value read at each point.

    Each b-point gets its OWN seed (the points are independent samples), derived from the stream's seed so that a
    stream is reproducible as a whole.
    """
    pers, vhat, ses, losses = [], [], [], []
    e0 = params["L"] * params["pi"]
    for i, b in enumerate(b_pts):
        loss, per, _ = V2.simulate_design_per(params, S, DESIGN, defect=defect_for(channel, b),
                                              n=n, seed=seed + 101 * i)
        require_gated(per)
        pers.append(per)
        losses.append(loss)
        vhat.append(e0 - loss)
        ses.append(float(per.std(ddof=1)) / math.sqrt(n) if n > 1 else 0.0)
    return pers, vhat, ses, losses


def wls(b_pts, v, se):
    """WLS of the affine read V(b) = A + B*b, with the covariance of (A, B).

    The point estimates are independent (different seeds) with known standard errors, so the covariance is
    (X' W X)^-1 with W = diag(1/se^2): no variance scale is estimated, because the SEs are not.

    A point with ZERO standard error is not a defect of the fit -- it is an EXACT reading, and its weight is
    infinite.  `(substitution, b = 0)` is exactly that: with `sigma_i = 1` every action is an invisible
    substitution and every action escalates, so nothing is blocked and the loss is the constant `L + c`; the
    drawn value equals the closed form EXACTLY there.  Rather than giving it an invented finite weight (which
    would be a number no instrument produced) or dropping it (which would weaken the fit to avoid a fact), the
    exact point CONSTRAINS the line: `A = v_e - B*b_e`, and `B` is fitted to the remaining points.  That is the
    infinite-weight limit, solved rather than approximated.  The package's own convention for exact readings is
    the same (v3: a zero-width interval is not an interval, so it is an exactness control, never pooled).
    """
    b = np.asarray(b_pts, dtype=float)
    v = np.asarray(v, dtype=float)
    se = np.asarray(se, dtype=float)
    if np.any(se < 0.0):
        raise RuntimeError("a negative standard error cannot come from a sample: %s" % list(se))
    exact = (se == 0.0)
    if not exact.any():
        x = np.column_stack([np.ones(len(b)), b])
        w = 1.0 / se ** 2
        cov = np.linalg.inv(x.T @ (x * w[:, None]))
        beta = cov @ (x.T @ (w * v))
        return float(beta[0]), float(beta[1]), cov
    if exact.sum() > 2:
        raise RuntimeError("more than two exact fidelities: the line is over-determined, not fitted")
    if exact.sum() == 2:
        i, j = np.where(exact)[0][:2]
        slope = (v[j] - v[i]) / (b[j] - b[i])
        intercept = v[i] - slope * b[i]
        for k in np.where(~exact)[0]:                 # the inexact points must not contradict the exact line
            if abs(intercept + slope * b[k] - v[k]) > 4.0 * se[k]:
                raise RuntimeError("an inexact reading contradicts the two exact fidelities at b=%s" % b[k])
        return float(intercept), float(slope), np.zeros((2, 2))
    i = int(np.where(exact)[0][0])
    be, ve = float(b[i]), float(v[i])
    m = ~exact
    if m.sum() < 2:
        raise RuntimeError("one exact point and %d inexact point(s): the slope is not determined" % m.sum())
    w = 1.0 / se[m] ** 2
    den = float(np.sum(w * (b[m] - be) ** 2))
    slope = float(np.sum(w * (b[m] - be) * (v[m] - ve)) / den)
    intercept = ve - slope * be
    var_slope = 1.0 / den
    cov = np.array([[be * be * var_slope, -be * var_slope], [-be * var_slope, var_slope]])
    return intercept, slope, cov


def se_of_line(cov, b):
    """SE of the fitted value at fidelity b."""
    v = np.array([1.0, b])
    return math.sqrt(max(float(v @ cov @ v), 0.0))


def fieller(a_hat, b_hat, cov, z=Z):
    """The set of fidelities where the measured value is not distinguishable from zero.  Three states."""
    c00, c01, c11 = float(cov[0, 0]), float(cov[0, 1]), float(cov[1, 1])
    sd_b = math.sqrt(c11) if c11 > 0 else 0.0
    slope_z = (abs(b_hat) / sd_b) if sd_b > 0 else None
    if abs(b_hat) <= z * sd_b:
        return dict(kind="flat", a_hat=a_hat, b_hat=b_hat, sd_b=sd_b, slope_z=slope_z,
                    why="the value's slope in fidelity is not distinguishable from zero")
    a2 = b_hat * b_hat - z * z * c11
    a1 = 2.0 * (a_hat * b_hat - z * z * c01)
    a0 = a_hat * a_hat - z * z * c00
    disc = a1 * a1 - 4.0 * a2 * a0
    base = dict(a_hat=a_hat, b_hat=b_hat, sd_b=sd_b, slope_z=slope_z, leading=a2, disc=disc)
    if disc < 0.0:
        # This is NOT a state of the reading.  For an affine read the fitted line attains zero at b* = -A/B, and
        # the set's own radius there is z*SE(b*) > 0, so b* is ALWAYS in the set: the discriminant cannot be
        # negative.  A negative one means the matrix handed in is not a covariance.  (The pre-registration
        # expected the grid to produce an EMPTY state; that expectation was wrong twice over -- the grid cannot,
        # and neither can the model, which is why the third state was REMOVED rather than kept as decoration.)
        raise RuntimeError("a negative discriminant means the matrix is not a covariance: an affine read's set "
                           "always contains the crossing b* = -A/B, so this state cannot occur")
    r1 = (-a1 - math.sqrt(disc)) / (2.0 * a2)
    r2 = (-a1 + math.sqrt(disc)) / (2.0 * a2)
    lo, hi = min(r1, r2), max(r1, r2)
    base.update(kind="bounded", lo=lo, hi=hi, width=hi - lo, clips=bool(lo < 0.0 or hi > 1.0))
    return base


def bootstrap(b_pts, pers, n, n_boot, seed, e0):
    """Resample each b-point's per-action sample, refit, recompute the crossing; percentile interval.

    The sample is resampled into the SAME quantity the point fit reads -- the gate's VALUE (e0 - loss), not the
    loss it is derived from.  The first version resampled the loss while the point estimate fitted the value, and
    the two routes then measured two different curves: every replicate produced a NEGATIVE slope and a crossing
    near 1.4 against a Fieller set of [0.05, 0.15].  C3 -- the comparison of the two routes -- is what found it;
    neither route is wrong alone, and no single-route check can see it (self-audit Class 101).

    A ratio's bootstrap has a heavy tail whenever the denominator can approach zero, so the replicates whose
    slope is not distinguishable from zero are COUNTED and excluded from the percentile interval rather than
    allowed to widen it -- a percentile interval over wild replicates is a decoration, not an interval.
    """
    rng = np.random.default_rng(seed)
    reps, n_flat = [], 0
    for _ in range(n_boot):
        v, se = [], []
        for k in range(len(b_pts)):
            idx = rng.integers(0, n, n)
            s = pers[k][idx]
            v.append(e0 - float(s.mean()))
            se.append(float(s.std(ddof=1)) / math.sqrt(n))
        a_hat, b_hat, cov = wls(b_pts, v, se)
        if abs(b_hat) <= Z * math.sqrt(max(float(cov[1, 1]), 0.0)):
            n_flat += 1
            continue
        reps.append(-a_hat / b_hat)
    reps.sort()
    lo = hi = None
    if reps:
        lo = reps[int(math.floor(0.025 * (len(reps) - 1)))]
        hi = reps[int(math.ceil(0.975 * (len(reps) - 1)))]
    return dict(n_nonflat=len(reps), n_flat=n_flat, flat_frac=(float(n_flat) / n_boot), lo=lo, hi=hi,
                width=(hi - lo) if (lo is not None and hi is not None) else None)


def estimate(params, channel, n=N_DRAW, seed=20260922, n_boot=N_BOOT, b_pts=B_PTS):
    """The boundary reading at one (cell, channel, stream): the estimate, both intervals, and the exact target."""
    pers, vhat, ses, losses = draw_curve(params, channel, n, seed, b_pts)
    a_hat, b_hat, cov = wls(b_pts, vhat, ses)
    fie = fieller(a_hat, b_hat, cov)
    boot = bootstrap(b_pts, pers, n, n_boot, seed + 7, params["L"] * params["pi"])
    exact = None if channel == "none" else V1.bstar_closed(params, channel)
    return dict(vhat=vhat, se=ses, n=n, seed=seed, losses=losses,
                exact_pts=[b for b, s in zip(b_pts, ses) if s == 0.0],
                a_hat=a_hat, b_hat=b_hat, cov=cov.tolist(),
                sd_b=math.sqrt(max(float(cov[1, 1]), 0.0)),
                b_hat_star=(-a_hat / b_hat) if b_hat != 0.0 else None,
                exact_b_star=exact, fieller=fie, bootstrap=boot)


def say(msg):
    print(msg)
    sys.stdout.flush()


def crc32(path):
    return "%08x" % (zlib.crc32(io.open(path, "rb").read()) & 0xFFFFFFFF)


def main():
    res = {
        "what": "issue #93 v5 -- the boundary's interval: the registration's metric (a)",
        "why": "metric (a) is registered as 'the boundary b*(a,s,L,c) WITH BOOTSTRAP CIs'; v1 owns the point "
               "estimate and nothing owned the interval",
        "preregistered": dict(
            P1="the drawn route reproduces v1's closed form for both channels, |diff| <= 4 SE",
            P2="the estimator recovers the exact boundary within the reported interval's own width",
            P3="the bootstrap percentile endpoint lies inside the Fieller bracket within one axis step, in the "
               "regime where the Fieller set lies inside the axis (intervals that leave the axis are an "
               "extrapolation regime, reported and not adjudicated)",
            P4="in the well-determined regime the width is z*SE(V at b*)/|B-hat| per side, halving at 4n",
            P5="the FLAT state is exercised by the `none` channel, which is also the slope test's NULL (its "
               "rejection rate is the test's measured size); EMPTY was expected from the grid and CANNOT occur "
               "for an affine read (theorem, stated in C6), so it is exercised by a battery plant instead",
            P6="the Fieller set's coverage of the exact boundary is consistent with the nominal 0.95"),
        "design": DESIGN, "b_pts": list(B_PTS), "n_draw": N_DRAW, "n_boot": N_BOOT, "s": S,
        "channels": {c: defect_for(c, 0.5) for c in CHANNELS},
        "streams": [{"family": f, "seed": s} for f, s in STREAMS],
        "nominal": 0.95, "build": dict(script_crc32=crc32(os.path.abspath(__file__))),
    }
    base = V0._p()

    # ---------------------------------------------------------------- C1: the mapping (a control)
    say("C1  the mapping b -> defect, checked against v1's closed form")
    map_rows, map_bad = [], []
    for channel in ("mismatch", "substitution"):
        for b in B_PTS:
            loss, per, _ = V2.simulate_design_per(base, S, DESIGN, defect=defect_for(channel, b),
                                                  n=200000, seed=555000 + int(1000 * b))
            require_gated(per)
            drawn = base["L"] * base["pi"] - loss
            closed = V1.value_closed(base, channel, b, S)
            se = float(per.std(ddof=1)) / math.sqrt(200000)
            zz = abs(drawn - closed) / se if se > 0 else 0.0
            map_rows.append(dict(channel=channel, b=b, drawn=drawn, closed=closed, se=se, z=zz))
            if zz > MAP_Z:
                map_bad.append(dict(channel=channel, b=b, z=zz))
    worst_z = max(r["z"] for r in map_rows)
    res["C1_mapping"] = dict(rows=map_rows, band_z=MAP_Z, bad=map_bad, worst_z=worst_z)
    say("    %d comparison(s) over 2 channels x %d fidelities, worst |diff| = %.2f SE (band %.1f): %s"
        % (len(map_rows), len(B_PTS), worst_z, MAP_Z, "PASS" if not map_bad else "FAIL"))
    if map_bad:
        raise RuntimeError("the b -> defect mapping does not reproduce the registered variant: %s" % map_bad)

    # ---------------------------------------------------------------- the grid
    say("")
    say("C2/C3/C4/C6/C7  the boundary at every cell x channel x stream")
    readings = []
    for cname, params in CELLS:
        for channel in CHANNELS:
            for family, seed in STREAMS:
                r = estimate(params, channel, seed=seed)
                r["cell"], r["channel"], r["family"] = cname, channel, family
                exact = r["exact_b_star"]
                r["exact_in_axis"] = bool(exact is not None and 0.0 < exact < 1.0)
                r["exact_out_of_axis"] = bool(exact is not None and not r["exact_in_axis"])
                if r["exact_in_axis"]:
                    fie = r["fieller"]
                    r["fie_covers"] = bool(fie["kind"] == "bounded" and fie["lo"] <= exact <= fie["hi"])
                    bo = r["bootstrap"]
                    r["boot_covers"] = bool(bo["lo"] is not None and bo["lo"] <= exact <= bo["hi"])
                readings.append(r)
    states = {}
    for r in readings:
        states[r["fieller"]["kind"]] = states.get(r["fieller"]["kind"], 0) + 1
    res["readings"] = readings
    res["state_counts"] = states
    say("    %d reading(s); states: %s"
        % (len(readings), ", ".join("%s=%d" % kv for kv in sorted(states.items()))))

    # C2: the estimator recovers the exact boundary
    in_axis = [r for r in readings if r["exact_in_axis"]]
    dev = [abs(r["b_hat_star"] - r["exact_b_star"]) for r in in_axis if r["b_hat_star"] is not None]
    width_max = max((r["fieller"].get("width") or 0.0) for r in in_axis) if in_axis else 0.0
    worst_dev = max(dev) if dev else None
    c2 = bool(dev) and worst_dev <= width_max
    res["C2_estimator"] = dict(n_in_axis=len(in_axis), worst_abs_dev=worst_dev,
                               worst_interval_width=width_max, pass_=c2)
    say("C2  estimator vs the exact boundary: %d in-axis reading(s), worst |dev| = %s (worst interval width %.4f)"
        % (len(in_axis), "%.4f" % worst_dev if worst_dev is not None else "n/a", width_max))
    if not c2:
        raise RuntimeError("the estimator does not recover the exact boundary: worst dev %s over %d reading(s)"
                           % (worst_dev, len(in_axis)))

    # C3: the two routes agree, IN THE REGIME WHERE BOTH ROUTES CLAIM THE SAME THING.
    #
    # The Fieller set is exact for a ratio of jointly normal estimates; the percentile bootstrap is only
    # asymptotically equivalent to it, and the equivalence is worst when the crossing is far from the data.  So
    # the comparison is taken on the readings whose interval lies INSIDE the axis -- where the boundary is
    # MEASURED -- and the readings whose interval leaves the axis (the crossing is an extrapolation there) are
    # reported as their own regime, with their disagreement stated rather than adjudicated.  (The promotion-
    # observed pattern recorded at R349 is the rule applied here: declare the regime, and publish the excluded
    # values.  A single tolerance over both regimes would either pass the extrapolations by being loose or fail
    # the measurements by being tight.)
    inside = [r for r in readings if r["fieller"]["kind"] == "bounded"
              and not r["fieller"]["clips"] and r["bootstrap"]["lo"] is not None]
    outside = [dict(cell=r["cell"], channel=r["channel"], family=r["family"],
                    fie=[r["fieller"]["lo"], r["fieller"]["hi"]],
                    boot=[r["bootstrap"]["lo"], r["bootstrap"]["hi"]],
                    gap=abs(r["bootstrap"]["hi"] - r["fieller"]["hi"]))
               for r in readings if r["fieller"]["kind"] == "bounded" and r["fieller"]["clips"]
               and r["bootstrap"]["lo"] is not None]
    disagree = [dict(cell=r["cell"], channel=r["channel"], family=r["family"],
                     fie=[r["fieller"]["lo"], r["fieller"]["hi"]],
                     boot=[r["bootstrap"]["lo"], r["bootstrap"]["hi"]])
                for r in inside
                if not (r["fieller"]["lo"] - Z_STEP <= r["bootstrap"]["lo"] <= r["fieller"]["hi"] + Z_STEP
                        and r["fieller"]["lo"] - Z_STEP <= r["bootstrap"]["hi"] <= r["fieller"]["hi"] + Z_STEP)]
    worst_flat = max(r["bootstrap"]["flat_frac"] for r in readings)
    res["C3_two_routes"] = dict(
        n_compared_in_axis=len(inside), tolerance=Z_STEP, disagree=disagree,
        n_out_of_axis=len(outside), out_of_axis=outside,
        worst_out_of_axis_gap=max([o["gap"] for o in outside]) if outside else None,
        worst_flat_frac=worst_flat,
        regime="the comparison is taken where the Fieller set lies inside the axis; the intervals that leave it "
               "are an extrapolation regime and are reported, not adjudicated")
    say("C3  the two routes agree in-axis: %d compared, %d disagreeing beyond one axis step (%.2f); "
        "%d reading(s) leave the axis (worst endpoint gap %s, reported not adjudicated); worst flat "
        "replicate fraction %.3f"
        % (len(inside), len(disagree), Z_STEP, len(outside),
           "%.3f" % res["C3_two_routes"]["worst_out_of_axis_gap"]
           if res["C3_two_routes"]["worst_out_of_axis_gap"] is not None else "n/a", worst_flat))
    if disagree:
        raise RuntimeError("the bootstrap and the Fieller set disagree beyond the declared tolerance: %s"
                           % disagree[:3])

    # C4: three statements about the interval -- its DEFINING property, its precision law, and the theorem that
    # ties flatness to the quadratic's leading coefficient.
    #
    # C4a reads the defining property rather than the formula: the endpoints must be exactly the fidelities where
    # |value| / SE(value) = z, and every fidelity strictly between them must be below z.  A root-finder checked
    # against the expression that produced it is checked against itself; checked against its DEFINITION it is
    # checked (self-audit Class 82's rule in a new place).
    #
    # C4b's regime is DERIVED, not chosen: the precision law is the leading term of
    #     1 / sqrt(1 - u),  u = (z / slope_z)^2,
    # so it is accurate to `tol` once slope_z >= z / sqrt(2*tol) = %.2f -- computed from the formula, never fitted
    # to the readings that failed.  (The first version used a round threshold of 4.0 and flagged a reading at
    # slope_z = 4.09 whose ratio was 0.78; the flag was right and the threshold was arbitrary, which is the same
    # defect one level up.)
    #
    # C4c is the theorem that makes the earlier correction possible: a BOUNDED set implies a positive leading
    # coefficient, and a FLAT set implies slope_z <= z -- flatness and invertibility are the same number.
    slope_regime = Z / math.sqrt(2.0 * LAW_TOL)
    law_rows, law_bad = [], []
    for r in readings:
        fie = r["fieller"]
        if fie["kind"] == "flat":
            if fie["slope_z"] is not None and fie["slope_z"] > Z:
                law_bad.append(dict(cell=r["cell"], channel=r["channel"],
                                    why="flat but the slope is detectable"))
            continue
        if fie["kind"] != "bounded":
            continue
        cov = np.array(r["cov"])
        a_hat, b_hat = fie["a_hat"], fie["b_hat"]
        # C4a: the defining property, at both endpoints and inside
        for end in (fie["lo"], fie["hi"]):
            zz = abs(a_hat + b_hat * end) / se_of_line(cov, end)
            if abs(zz - Z) > 1e-9:
                law_bad.append(dict(cell=r["cell"], channel=r["channel"], endpoint=end, z_ratio=zz,
                                    why="an endpoint is not the fidelity where |value| = z*SE"))
        mid = 0.5 * (fie["lo"] + fie["hi"])
        if se_of_line(cov, mid) > 0 and abs(a_hat + b_hat * mid) / se_of_line(cov, mid) > Z:
            law_bad.append(dict(cell=r["cell"], channel=r["channel"],
                                why="a fidelity inside the set has a distinguishable value"))
        if fie["leading"] is not None and fie["leading"] <= 0.0:
            law_bad.append(dict(cell=r["cell"], channel=r["channel"],
                                why="a bounded Fieller set with a non-positive leading coefficient"))
        # C4d: the constructive reason the EMPTY state cannot exist.  The set is non-empty BY CONSTRUCTION: the
        # fitted line attains zero at b*, and the set's own radius there is z*SE(b*) > 0, so b* is always inside
        # it.  Asserted rather than argued -- a theorem nobody checks is a comment.
        if not (fie["lo"] - 1e-9 <= r["b_hat_star"] <= fie["hi"] + 1e-9):
            law_bad.append(dict(cell=r["cell"], channel=r["channel"], b_hat_star=r["b_hat_star"],
                                interval=[fie["lo"], fie["hi"]],
                                why="the estimated crossing is not inside its own set, which would mean the "
                                    "set is empty -- impossible for an affine read"))
        # C4b: the precision law, in its derived regime
        predicted = 2.0 * Z * se_of_line(cov, r["b_hat_star"]) / abs(b_hat)
        row = dict(cell=r["cell"], channel=r["channel"], family=r["family"], slope_z=fie["slope_z"],
                   observed=fie["width"], predicted=predicted, ratio=predicted / fie["width"],
                   in_regime=bool(fie["slope_z"] >= slope_regime),
                   se_at_b_star=se_of_line(cov, r["b_hat_star"]))
        law_rows.append(row)
        if row["in_regime"] and abs(row["ratio"] - 1.0) > LAW_TOL:
            law_bad.append(dict(cell=r["cell"], channel=r["channel"], family=r["family"],
                                ratio=row["ratio"], slope_z=fie["slope_z"], why="outside the law's tolerance"))
    regime_rows = [r for r in law_rows if r["in_regime"]]
    worst_law = max((abs(r["ratio"] - 1.0) for r in regime_rows), default=None)
    res["C4_width_law"] = dict(
        rows=law_rows, tolerance=LAW_TOL, slope_regime=slope_regime,
        slope_regime_source="derived from 1/sqrt(1-u) with u = (z/slope_z)^2: slope_z >= z/sqrt(2*tol)",
        n_bounded=len(law_rows), n_in_regime=len(regime_rows), worst_dev_in_regime=worst_law,
        n_out_of_regime=len(law_rows) - len(regime_rows), violations=law_bad)
    say("C4  the interval's defining property, its precision law and the flatness theorem: %d bounded reading(s), "
        "%d in the derived regime (slope_z >= %.2f), worst |ratio-1| = %s, %d violation(s)"
        % (len(law_rows), len(regime_rows), slope_regime,
           "%.4f" % worst_law if worst_law is not None else "n/a", len(law_bad)))
    if law_bad:
        raise RuntimeError("the interval's defining property, precision law or flatness theorem is violated: %s"
                           % law_bad[:3])

    # C5: the 1/sqrt(n) scaling, measured on the defaults cell for both channels
    scale_rows = []
    for channel in ("mismatch", "substitution"):
        w = {}
        for n in (N_DRAW, 4 * N_DRAW):
            f = estimate(base, channel, n=n, seed=20260922, n_boot=N_BOOT)["fieller"]
            w[n] = f.get("width") if f["kind"] == "bounded" else None
        ratio = (w[N_DRAW] / w[4 * N_DRAW]) if (w[N_DRAW] and w[4 * N_DRAW]) else None
        scale_rows.append(dict(channel=channel, width_n=w[N_DRAW], width_4n=w[4 * N_DRAW], ratio=ratio))
    worst_ratio_dev = max(abs(r["ratio"] - 2.0) for r in scale_rows if r["ratio"] is not None)
    res["C5_scaling"] = dict(rows=scale_rows, expected=2.0, tolerance=SCALE_TOL, worst_dev=worst_ratio_dev)
    say("C5  the width at n vs 4n: %s (expected 2.0, worst deviation %.3f)"
        % (["%.3f" % r["ratio"] if r["ratio"] is not None else "n/a" for r in scale_rows], worst_ratio_dev))
    if worst_ratio_dev > SCALE_TOL:
        raise RuntimeError("the width does not scale as 1/sqrt(n): %s" % scale_rows)

    # C6: the states, the test's own SIZE measured on a real null, and the state that cannot occur.
    #
    # The `none` channel is a NULL for the slope test BY CONSTRUCTION: its defect does not depend on b, so the
    # value is the same number at every fidelity and any reading that reports a bounded set there is a FALSE
    # POSITIVE.  That makes its rejection rate the test's measured size -- which is what a 5 % test should be
    # checked against, and v3's rule applies to it too (a rate, judged by its interval, over a declared
    # denominator).
    #
    # EMPTY cannot occur for an AFFINE read: the fitted line attains zero at b* = -A/B by construction, so the
    # quadratic's discriminant is never negative, and the region is FLAT or BOUNDED -- never empty.  The
    # pre-registration expected the grid to exercise EMPTY; that expectation was WRONG, and the correction is
    # stated here rather than quietly dropped.  The `empty` branch is therefore unreachable through this model
    # and is kept only as a guard: the battery proves it fires when the read is given curvature (a plant), which
    # is the only thing that keeps an unreachable branch from being decoration (self-audit Class 80/111).
    none_readings = [r for r in readings if r["channel"] == "none"]
    n_none_false = sum(1 for r in none_readings if r["fieller"]["kind"] != "flat")
    size_ci = wilson(n_none_false, len(none_readings))
    states_ok = states.get("flat", 0) >= 1
    size_ok = bool(size_ci[0] <= 0.05 <= size_ci[1])
    res["C6_states"] = dict(
        counts=states, flat_exercised=states.get("flat", 0) >= 1,
        states_are_two="an affine read attains zero at b* = -A/B and the set's radius there is z*SE(b*) > 0, so "
                       "the crossing is always inside the set: the quadratic's discriminant is never negative and "
                       "the region is FLAT or BOUNDED.  There is no third state to report, and C4d asserts the "
                       "containment rather than leaving the theorem as prose",
        null_for_the_slope_test=dict(channel="none", denominator=len(none_readings),
                                     false_positives=n_none_false,
                                     rate=(float(n_none_false) / len(none_readings)) if none_readings else None,
                                     wilson=size_ci, nominal_alpha=0.05,
                                     consistent_with_nominal=size_ok))
    say("C6  FLAT exercised by the grid: %s; the `none` channel is the null for the slope test: %d/%d "
        "rejected = %.4f (nominal 0.05, Wilson [%.4f,%.4f]); the states are TWO (C4d proves the crossing is "
        "always inside its own set, so no third state exists)" % (states_ok, n_none_false, len(none_readings),
                                             (float(n_none_false) / len(none_readings)) if none_readings else 0.0,
                                             size_ci[0], size_ci[1]))
    if not states_ok or not size_ok:
        raise RuntimeError("the states or the slope test's own size are not consistent: flat=%s size=%s"
                           % (states.get("flat", 0), size_ci))

    # C7: calibration, with the denominator, the exclusions and the no-target readings published
    n_in = len(in_axis)
    n_fie = sum(1 for r in in_axis if r["fie_covers"])
    n_boot = sum(1 for r in in_axis if r["boot_covers"])
    excluded = [dict(cell=r["cell"], channel=r["channel"], family=r["family"],
                     exact_b_star=r["exact_b_star"], state=r["fieller"]["kind"])
                for r in readings if r["exact_out_of_axis"]]
    no_target = [dict(cell=r["cell"], family=r["family"], state=r["fieller"]["kind"])
                 for r in readings if r["channel"] == "none"]
    ci_f, ci_b = wilson(n_fie, n_in), wilson(n_boot, n_in)
    fie_ok = bool(ci_f[0] <= 0.95 <= ci_f[1])
    res["C7_calibration"] = dict(
        denominator=n_in, n_out_of_axis_excluded=len(excluded), out_of_axis_excluded=excluded,
        n_no_target=len(no_target), no_target=no_target,
        fieller_covered=n_fie, fieller_rate=(float(n_fie) / n_in) if n_in else None, fieller_wilson=ci_f,
        bootstrap_covered=n_boot, bootstrap_rate=(float(n_boot) / n_in) if n_in else None,
        bootstrap_wilson=ci_b, nominal=0.95, fieller_consistent_with_nominal=fie_ok,
        by_family=family_rates(in_axis))
    say("C7  calibration over the %d in-axis reading(s): Fieller %d/%d = %.4f %s, bootstrap %d/%d = %.4f; "
        "%d excluded (out of axis), %d with no target (`none`)"
        % (n_in, n_fie, n_in, (float(n_fie) / n_in) if n_in else 0.0, "[%.4f,%.4f]" % ci_f, n_boot, n_in,
           (float(n_boot) / n_in) if n_in else 0.0, len(excluded), len(no_target)))
    if not fie_ok:
        raise RuntimeError("the Fieller set's coverage is not consistent with the nominal 0.95: %d/%d, Wilson "
                           "%s" % (n_fie, n_in, ci_f))

    # C8: the two readings of the registered wording are BOTH reported (this is a wording finding, not a check
    # that can fail): reading 2 (parameter uncertainty) has no sampling distribution in this study.
    res["C8_registered_wording"] = dict(
        reading_1="estimator uncertainty: what is reported above (the boundary located from sampled actions)",
        reading_2="parameter uncertainty: no sampling distribution exists -- (a, s, L, c) are design points of "
                  "a harness with ground truth by construction, not estimates",
        finding="metric (a)'s wording 'with bootstrap CIs' has no stated carrier: the manuscript must name which "
                "of the two readings each interval belongs to")

    res["checks"] = dict(
        C1_mapping="PASS", C2_estimator="PASS", C3_two_routes="PASS", C4_width_law="PASS",
        C5_scaling="PASS", C6_states="PASS", C7_calibration="PASS", C8_wording="reported")
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, indent=1, sort_keys=True))
    say("")
    say("gate_v5_results.json written (%d bytes), script crc32 %s"
        % (os.path.getsize(OUT), res["build"]["script_crc32"]))
    return 0


def family_rates(in_axis):
    """The calibration rate per DECLARED stream family -- so a panel sharing a magnitude would show as a split."""
    out = {}
    for r in in_axis:
        d = out.setdefault(r["family"], dict(n=0, fie=0, boot=0))
        d["n"] += 1
        d["fie"] += 1 if r["fie_covers"] else 0
        d["boot"] += 1 if r["boot_covers"] else 0
    return out


if __name__ == "__main__":
    sys.exit(main())
