#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 8: WHAT MOVES THE BOUNDARY WHEN THE EFFECT CHANNEL IS CHARGED.

WHAT THIS FILE IS.  Step 7 measured the side-effect channel: a charge on the steps that MISS, landing as
worker-busy time, moving the boundary in rho coordinates by 0.00304 (h = 0.9, q = 0.05, comp = 1) -- and it
left one question UNRESOLVED in its own record: WHY does the boundary move at all in rho coordinates, and why
does the same DECLARED LOAD buy 1.5-2.1x more shrinkage at h = 0.5 than at h = 0.9?  (Its "load law" -- same
added load, same shrinkage -- was refuted, and two candidate mechanisms were written down without a test:
(i) the reference curve's local slope at its own crossing differs by hit rate; (ii) the load-to-contention
transfer differs when half the calls are not issued early.)

THE TWO MODELS, DECLARED BEFORE THE RUN.  Both are statements about the SAME object: the reference family's
own benefit-versus-contention curve, and the charged family's measured benefit at its own contention.

  H-rho   ("the charge acts only through contention"):  b_charged(rho) == b_ref(rho).  The charge raises the
          contention of every cell and nothing else.  Consequence: the boundary in rho coordinates does NOT
          move -- the charged family reaches zero benefit AT THE SAME rho, just at a different worker count.
          Measured as the residual r = b_charged - interp_ref(rho_charged), paired by seed, at every cell whose
          contention lies inside the reference family's own contention range.
          Verdict: COINCIDENT iff r's interval contains 0 at every comparable cell; DEVIATES iff some cell's
          interval excludes 0; NOT COMPARABLE iff no cell is comparable (with the reason printed).

  H-shift ("the charged curve is the reference curve displaced downward by a measurable amount"): if
          b_charged(rho) == b_ref(rho) - db with db measured at the crossing, then the charged family crosses
          zero where b_ref(rho) == db, i.e. it crosses EARLIER by

              shrink_pred = db / |s|,      s = the reference curve's slope across its own crossing cells,

          where `s` is a SECANT over the two cells that bound the reference crossing (declared: a secant, not
          a derivative -- the curve between cells is not resolved by this design).  Verdict against step 7's
          paired shrinkage interval on the same families: CONSISTENT iff shrink_pred lies inside it;
          INCONSISTENT iff outside (with the factor by which it misses).

WHY THE PIECES ARE MEASURED THE WAY THEY ARE.  The independent unit is a DRAW STREAM, so:
  * the reference curve is built PER SEED from that seed's own (rho, benefit) points, and evaluated at that
    same seed's charged contention -- two families compared position-by-position in a shared list would pair a
    seed with a different seed (step 7's Class 60 family of defect);
  * interpolation is LINEAR IN RHO between the reference family's own cells, and a target contention outside
    the reference family's range is NOT COMPARABLE, not extrapolated;
  * every residual carries a t interval over seeds (`boundary_v1.t_ci`, the estimator steps 2, 3, 5, 6, 7 used);
  * the measured shrinkage is read by CALLING STEP 7'S OWN FUNCTION on the same families, not re-implemented
    (`--selftest` asserts the two readings agree numerically, so this file cannot quietly become a second
    opinion about the same quantity).

WHAT THIS FILE DOES NOT CLAIM.  It does not claim that `db` is constant in rho (the residual table shows
whether it is), nor that the secant equals a derivative, nor that the charge has no effect other than the two
models above: a third possibility -- that the charge changes the SHAPE of the curve -- is reported as "both
models fail" rather than forced into one of them.

CPU only, stdlib only, fixed seeds, no network.  `instrument_v0.py` is imported UNMODIFIED; steps 2, 4 and 7
supply the interval, the per-step terms and the charged-cell machinery (`cell3` / `sweep3` /
`crossings_labelled` / `paired_shrinkage`), so this file's cells are made by the same code path as step 7's.
"""
import argparse
import io
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import instrument_v0 as I      # noqa: E402  the model, unmodified
import boundary_v1 as B1       # noqa: E402  step 2's t interval
import sideeffect_v1 as S7     # noqa: E402  step 7's cells, crossings and paired shrinkage

# The two families of one comparison are made by the same code path, so a residual of zero means "the same
# number twice", not "two estimates that happen to agree".  Anything above this is a difference in the physics.
RESIDUAL_TOL = 1e-12

# The windows are NARROW on purpose: this file needs the crossing's neighbourhood, not the whole curve.  They
# are read off step 7's own located crossings (A = 16: c = 2..8 depending on the config; A = 64: c = 14..30).
WINDOWS = ((16, 2, 9), (64, 12, 26))

# (h, q, comp) -- the references (q = 0) and the charged configs each reference is compared against.  The set is
# step 7's, restricted to the (A, h) pairs whose shrinking it resolved, so the measured shrinkage this file
# tests against is the one step 7 already published.
REFS = (0.9, 0.5)
CHARGED = ((0.9, 0.05, 1.0), (0.9, 0.05, 5.0), (0.9, 0.25, 4.0),
           (0.5, 0.01, 1.0), (0.5, 0.05, 1.0))

# The (h, config) pairs whose DECLARED load matches: step 7's load law was refuted on these two loads,
# and the point of the table below is to say which factor differs -- the drop per unit load, or the slope.
MATCHED_LOADS = (0.005, 0.025)

NOT_COMPARABLE = "NOT COMPARABLE"

# Step 7's own product, used ONLY as a coordinate to read this run's narrow windows against (see
# `window_preserves_step7_crossing`).  It is a reading, not an input: no number of this file's results is
# taken from it.
STEP7_RECORD = "sideeffect_v1.json"

# --------------------------------------------------------------------------- one seed's own curve
def points_of(fam, seed_index, key="rho_spec"):
    """One seed's own (contention, benefit) points inside a family, sorted by contention.

    The unit of the whole study is a draw stream: a family's cells are `n_seeds` streams measured at several
    worker counts, so a curve belongs to a stream and not to a family.  Returning them in rho order is what
    makes the interpolation below a function of contention rather than of the worker count.
    """
    pts = sorted((r["per_seed_rho_spec"][seed_index], r["per_seed"][seed_index]) for r in fam["rows"])
    return pts


def interp_at(pts, x):
    """Linear in contention between a seed's own points; None outside their range (never extrapolated).

    A target contention below the first or above the last point is NOT a defect and NOT a zero: it is a
    comparison this design cannot make, and the caller counts it.
    """
    if not pts or x < pts[0][0] or x > pts[-1][0]:
        return None
    for i in range(len(pts) - 1):
        lo, hi = pts[i], pts[i + 1]
        if lo[0] <= x <= hi[0]:
            if hi[0] == lo[0]:
                return lo[1]
            w = (x - lo[0]) / (hi[0] - lo[0])
            return lo[1] + w * (hi[1] - lo[1])
    return pts[-1][1]


def local_linearisation_bound(pts, x):
    """How wrong can LINEAR interpolation at `x` be, judging by the family's own second differences?

    The deviation this file tests is `b_charged(x) - interp_ref(x)` with `x` the charged family's own
    contention -- an INTERIOR point of the reference family's grid in general.  Interpolating between two nodes
    with a straight line is an approximation, and a verdict of "DEVIATES" is only worth reporting if the
    residual is larger than what that approximation alone can produce.  The standard estimate for a function
    sampled on a grid: for a locally quadratic piece with second difference `d2` over the bracketing step, the
    interpolation error on it is at most `d2 / 8`.  Read here from the seed's OWN nodes (the triple nearest the
    bracket), so the bound is measured from the same object being interpolated and not from a model of it.

    Returns 0.0 when `x` IS a node (no interpolation happened) and None when no triple is available.
    """
    n = len(pts)
    if n < 3:
        return None
    for i in range(n - 1):
        lo, hi = pts[i], pts[i + 1]
        if lo[0] <= x <= hi[0]:
            if x == lo[0] or x == hi[0] or hi[0] == lo[0]:
                return 0.0
            j = i if 1 <= i <= n - 2 else (i + 1 if 1 <= i + 1 <= n - 2 else None)
            if j is None:
                return None
            d2 = abs(pts[j - 1][1] - 2.0 * pts[j][1] + pts[j + 1][1])
            return d2 / 8.0
    return None


def overlap(fam_a, fam_b, key="rho_spec"):
    """The contention range both families' seeds actually span: the region where a comparison is possible."""
    lo = max(fam_a["rows"][0][key], fam_b["rows"][0][key])
    hi = min(fam_a["rows"][-1][key], fam_b["rows"][-1][key])
    return {"lo": lo, "hi": hi, "non_empty": lo < hi}


def coincidence(fam_base, fam_target, key="rho_spec"):
    """`fam_target`'s benefit against the curve of `fam_base`, evaluated at the target's own contention.

    Both are families from step 7's `sweep3`, so `rows[i]['per_seed']` is the mean benefit of one DRAW STREAM
    (warm-up trimmed by the model itself) and `rows[i]['per_seed_rho_spec']` is that stream's measured
    contention.  The comparison is per (cell, seed) and the residual's interval is over SEEDS.

    Used in both directions (charged-vs-reference and reference-vs-charged); a result that holds in one
    direction only is a property of where the two rho ranges overlap, and the caller prints both.
    """
    ov = overlap(fam_base, fam_target, key)
    out = {"base": fam_base["kn"], "target": fam_target["kn"], "overlap": ov, "cells": []}
    n_cmp = n_not = 0
    for r in fam_target["rows"]:
        res, used, skipped, bounds = [], 0, 0, []
        for si in range(r["n_seeds"]):
            x = r["per_seed_rho_spec"][si]
            pts = points_of(fam_base, si, key)
            y_ref = interp_at(pts, x)
            if y_ref is None:
                skipped += 1
                continue
            res.append(r["per_seed"][si] - y_ref)
            b = local_linearisation_bound(pts, x)
            if b is not None:
                bounds.append(b)
            used += 1
        n_cmp += used
        n_not += skipped
        out["cells"].append({"workers": r["workers"], "rho": r[key], "benefit": r["benefit_pct"],
                             "per_seed_residual": res, "n_used": used, "n_skipped": skipped,
                             "mean": statistics.fmean(res) if res else None,
                             "ci": B1.t_ci(res) if len(res) > 1 else None,
                             "mean_bound": statistics.fmean(bounds) if bounds else None,
                             "n_bounds": len(bounds)})
    out["n_compared"] = n_cmp
    out["n_skipped"] = n_not
    out["status"] = "READ" if n_cmp else NOT_COMPARABLE
    out["reason"] = (None if n_cmp else
                     "no cell of %s has a contention inside %s's own range %s"
                     % (fam_target["kn"], fam_base["kn"],
                        (["%.5f" % ov["lo"], "%.5f" % ov["hi"]] if not ov["non_empty"] else "its span")))
    cells = [c for c in out["cells"] if c["ci"]]
    out["all_contain_zero"] = bool(cells) and all(c["ci"][0] <= 0 <= c["ci"][1] for c in cells)
    out["n_cells_excluding_zero"] = sum(1 for c in cells if not (c["ci"][0] <= 0 <= c["ci"][1]))
    out["worst_abs_mean"] = max((abs(c["mean"]) for c in cells), default=None)
    # A cell "excludes zero" meaningfully only if its residual also clears the interpolation error this design
    # can produce on its own: |mean| > the mean bound from the interpolated family's second differences.
    out["n_cells_excluding_zero_beyond_bound"] = sum(
        1 for c in cells
        if not (c["ci"][0] <= 0 <= c["ci"][1])
        and c["mean_bound"] is not None and abs(c["mean"]) > c["mean_bound"])
    out["worst_bound"] = max((c["mean_bound"] for c in cells if c["mean_bound"] is not None), default=None)
    return out


def crossing_cells(fam):
    """The two worker counts that bound this family's crossing, as a tuple of INTs.

    Step 7's record stores each bounding cell as an `[agents, workers]` pair, and this file interpolates over
    the WORKER count -- so the pair's second coordinate is what has to come out here (a bare int is passed
    through, so a fixture may hand either shape).  Unpacking the pair directly would read the AGENT count as a
    worker count and then raise deep inside `secant_slope`; arm 3 of `--selftest` is what caught that, and the
    check is kept here as a shape assertion rather than a comment.
    """
    cr = fam["crossing"]
    if cr is None or cr.get("ambiguous"):
        return None
    cells = []
    for c in cr["cells"]:
        if isinstance(c, (list, tuple)):
            if len(c) != 2:
                raise ValueError("crossing cell %r is not (agents, workers)" % (c,))
            cells.append(c[1])
        else:
            cells.append(c)
    if len(cells) != 2:
        raise ValueError("crossing of %s has %d cell(s), not 2" % (fam["kn"], len(cells)))
    return tuple(cells)


def match_workers(fam_cells, workers):
    """True iff `workers` is one of the crossing cells (given either shape)."""
    for c in fam_cells:
        w = c[1] if isinstance(c, (list, tuple)) else c
        if w == workers:
            return True
    return False


def secant_slope(fam, seed_index=None, key="rho_spec"):
    """Benefit points per unit contention across the family's own crossing cells (a SECANT, declared).

    A derivative is not available: between two cells the curve is not resolved by this design.  With
    `seed_index` the same secant is taken on that seed's own points, so the slope carries an interval too.
    """
    cc = crossing_cells(fam)
    if cc is None:
        return None
    (w_a, w_b) = cc
    def val(w, si):
        for r in fam["rows"]:
            if r["workers"] == w:
                return (r["per_seed_rho_spec"][si] if si is not None else r[key],
                        r["per_seed"][si] if si is not None else r["benefit_pct"])
        raise KeyError("worker count %d not in family %s" % (w, fam["kn"]))
    if seed_index is None:
        ra, ba = val(w_a, None)
        rb, bb = val(w_b, None)
        return (ba - bb) / (ra - rb) if ra != rb else None
    ra, ba = val(w_a, seed_index)
    rb, bb = val(w_b, seed_index)
    return (ba - bb) / (ra - rb) if ra != rb else None


def slope_with_interval(fam, key="rho_spec"):
    if fam["crossing"] is None or fam["crossing"].get("ambiguous"):
        return {"status": "NOT LOCATED"}
    ss = [secant_slope(fam, si, key) for si in range(fam["rows"][0]["n_seeds"])]
    ss = [s for s in ss if s is not None]
    return {"status": "READ", "mean": statistics.fmean(ss) if ss else None,
            "ci": B1.t_ci(ss) if len(ss) > 1 else None, "per_seed": ss}


# --------------------------------------------------------------------------- the shift model and the verdicts
def crossing_gap(coin, fam_ref):
    """`db` -- how far the charged curve sits BELOW the reference at the reference's own crossing cells.

    Read from a `coincidence` table (target minus reference, so db = -residual) at the two cells that bound the
    reference family's crossing, as a mean over the comparable seeds of those two cells, with a t interval.
    `None` when either bounding cell is not comparable.
    """
    cc = crossing_cells(fam_ref)
    if cc is None:
        return {"status": "NOT LOCATED"}
    want = set(cc)
    per_seed, used_cells = [], []
    for cell in coin["cells"]:
        if cell["workers"] not in want or not cell["per_seed_residual"]:
            continue
        used_cells.append(cell["workers"])
        per_seed.extend(-x for x in cell["per_seed_residual"])
    if not per_seed:
        return {"status": NOT_COMPARABLE,
                "reason": "neither crossing cell of %s has a comparable contention in %s"
                          % (fam_ref["kn"], coin["target"])}
    return {"status": "READ", "cells": sorted(used_cells), "n": len(per_seed),
            "mean": statistics.fmean(per_seed), "per_seed": per_seed,
            "ci": B1.t_ci(per_seed) if len(per_seed) > 1 else None}


def predict_shrink(gap, slope):
    """`shrink_pred = db / |s|` -- the boundary displacement implied by a downward displacement of the curve."""
    if gap.get("status") != "READ" or slope.get("status") != "READ" or not slope["mean"]:
        return {"status": "NOT DERIVABLE"}
    s = abs(slope["mean"])
    return {"status": "READ", "value": gap["mean"] / s, "db": gap["mean"], "slope": slope["mean"],
            "db_ci": gap.get("ci"), "slope_ci": slope.get("ci"),
            # The prediction's own spread, from the two factors' independent intervals -- an ESTIMATE, declared:
            # it is the interval of a ratio and is used only to say whether the comparison can be read.
            "value_ci_estimate": (None if not gap.get("ci") or not slope.get("ci") else
                                  [gap["ci"][0] / s, gap["ci"][1] / s])}


def compare_to_measured(pred, measured):
    """Is the model's prediction inside step 7's paired shrinkage interval?"""
    if pred.get("status") != "READ" or not measured or not measured.get("shrink_known") or measured.get("not_located"):
        return {"verdict": "NOT READ", "reason": "prediction or measurement not available"}
    lo, hi = measured["ci"]
    v = pred["value"]
    vlo, vhi = (pred.get("value_ci_estimate") or [v, v])
    inside = (vlo <= hi and vhi >= lo)          # interval overlap, not point containment
    out = {"verdict": "CONSISTENT" if inside else "INCONSISTENT",
           "predicted": v, "predicted_ci": [vlo, vhi], "measured": measured["mean"],
           "measured_ci": [lo, hi], "point_inside": (lo <= v <= hi)}
    if not inside:
        out["factor"] = (v / hi) if v > hi else (lo / v) if v > 0 else None
    return out


def group(pool, h, cfg, ref_fam, cfg_fam, measured):
    """Everything one (pool, h, config) comparison says, in one record."""
    coin_a = coincidence(ref_fam, cfg_fam)      # charged curve at the reference curve
    coin_b = coincidence(cfg_fam, ref_fam)      # and the reverse, to show the comparison's direction
    slope = slope_with_interval(ref_fam)
    gap = crossing_gap(coin_a, ref_fam)
    pred = predict_shrink(gap, slope)
    cmp_ = compare_to_measured(pred, measured)
    return {"pool": pool, "h": h, "config": list(cfg), "load": (1.0 - h) * cfg[0] * cfg[1],
            "ref": ref_fam["kn"], "target": cfg_fam["kn"], "kn": cfg_fam["kn"],
            "charge_per_step": cfg_fam["measured_charge_per_step"],
            "coincidence_charged_at_ref": coin_a, "coincidence_ref_at_charged": coin_b,
            "slope": slope, "gap": gap, "prediction": pred, "comparison": cmp_,
            # The measured shrinkage is step 7's OWN record of that quantity, kept whole enough that the
            # report and the checks can read its STATUS (`shrink_known`, `not_located`) and not only its
            # number -- a filter that drops the status leaves a group that located nothing looking READ.
            "measured_shrinkage": ({k: measured.get(k) for k in ("mean", "ci", "n_pairs", "n_unpaired",
                                                                 "shrink_known", "not_located", "error")
                                    if k in measured} if measured else None),
            "db_per_load": (gap["mean"] / ((1.0 - h) * cfg[0] * cfg[1])
                            if gap.get("status") == "READ" and (1.0 - h) * cfg[0] * cfg[1] > 0 else None)}


def hr_verdict(groups):
    """H-rho over the whole run: does the charge act ONLY through measured contention?"""
    read = [g["coincidence_charged_at_ref"] for g in groups if g["coincidence_charged_at_ref"]["status"] == "READ"]
    if not read:
        return {"verdict": NOT_COMPARABLE, "reason": "no group had a comparable contention range"}
    # A cell counts as a deviation only if its residual interval excludes zero AND the residual is larger
    # than the error LINEAR INTERPOLATION alone can produce on that family's own grid.  Both counts are
    # reported: the weaker one says how much of the signal sits at the resolution limit of this design.
    deviating = [g["kn"] for g in groups
                 if g["coincidence_charged_at_ref"]["status"] == "READ"
                 and g["coincidence_charged_at_ref"]["n_cells_excluding_zero_beyond_bound"] > 0]
    raw = [g["kn"] for g in groups
           if g["coincidence_charged_at_ref"]["status"] == "READ"
           and not g["coincidence_charged_at_ref"]["all_contain_zero"]]
    if deviating:
        return {"verdict": "DEVIATES", "n_groups": len(read), "deviating": deviating,
                "excluding_zero_any": raw,
                "n_cells_excluding_zero": {g["kn"]: g["coincidence_charged_at_ref"]["n_cells_excluding_zero"]
                                           for g in groups if g["kn"] in deviating},
                "n_cells_beyond_bound": {
                    g["kn"]: g["coincidence_charged_at_ref"]["n_cells_excluding_zero_beyond_bound"]
                    for g in groups if g["kn"] in deviating}}
    if raw:
        return {"verdict": "COINCIDENT WITHIN RESOLUTION", "n_groups": len(read), "excluding_zero_any": raw,
                "reason": "cell(s) exclude zero, but no residual exceeds the linearisation bound this design"
                          " produces on the same family's own grid"}
    return {"verdict": "COINCIDENT", "n_groups": len(read)}


def shift_verdict(groups):
    """H-shift: is `shrink_pred = db / |s|` inside the measured paired shrinkage interval?"""
    seen = [g for g in groups if g["comparison"]["verdict"] in ("CONSISTENT", "INCONSISTENT")]
    if not seen:
        return {"verdict": "NOT READ", "reason": "no group could be compared"}
    bad = [g["kn"] for g in seen if g["comparison"]["verdict"] == "INCONSISTENT"]
    ok = [g["kn"] for g in seen if g["comparison"]["verdict"] == "CONSISTENT"]
    return {"verdict": "ALL CONSISTENT" if not bad else ("ALL INCONSISTENT" if not ok else "MIXED"),
            "consistent": ok, "inconsistent": bad, "n_groups": len(seen),
            "factors": {g["kn"]: g["comparison"].get("factor") for g in seen
                        if g["comparison"].get("factor")}}


def load_decomposition(groups):
    """At matched declared load, which factor differs: the drop per unit load, or the reference slope?

    Step 7's own open question lives here.  Two configs with the SAME declared load but different hit rates
    shrink the boundary by different amounts (1.5-2.1x more at the lower hit rate).  The shift model splits
    that into two measurable factors -- the displacement `db` per unit load, and the reference curve's slope
    `s` at its own crossing -- so the ratio of the two members' shrinks can be read against the ratio of each
    factor: whichever factor moves further from 1 carries the h-dependence, and if that factor is the slope
    while db/load stays put, the displacement is a property of the LOAD and the shrinkage is a property of the
    WORKLOAD'S SHAPE.

    This is a measurement over the members, not a fitted law: no functional form is imposed on either factor.
    """
    out = []
    for L in MATCHED_LOADS:
        # Group by (load, POOL): a matched pair must differ in the hit rate and in nothing else.  Grouping on
        # the load alone silently pairs one pool's low-h family with ANOTHER pool's high-h family, and the
        # ratio that comes out then describes the pool difference while wearing the hit-rate's name -- which
        # is what the first deciding run printed (members are named in the record, which is how it showed).
        pools = sorted({g["pool"] for g in groups if abs(g["load"] - L) < 1e-12})
        for P in pools:
            members = [g for g in groups if abs(g["load"] - L) < 1e-12 and g["pool"] == P]
            if len(members) < 2 or len({g["h"] for g in members}) < 2:
                continue
            members = sorted(members, key=lambda g: g["h"])       # the LOWER hit rate first
            lo_m, hi_m = members[0], members[-1]

            def ratio(a, b):
                return (a / b) if (a is not None and b not in (None, 0)) else None

            def val(g, field):
                if field == "db_per_load":
                    return g["db_per_load"]
                if field == "slope":
                    return g["slope"]["mean"] if g["slope"]["status"] == "READ" else None
                if field == "predicted":
                    return g["prediction"].get("value") if g["prediction"]["status"] == "READ" else None
                return (g["measured_shrinkage"] or {}).get("mean")

            ratios = {f: ratio(val(lo_m, f), val(hi_m, f))
                      for f in ("measured", "predicted", "db_per_load", "slope")}
            away = {f: (abs(ratios[f] - 1.0) if ratios[f] is not None else None)
                    for f in ("db_per_load", "slope")}
            carry = None
            if away["db_per_load"] is not None and away["slope"] is not None:
                carry = "the slope" if away["slope"] > away["db_per_load"] else "the drop per unit load"
            out.append({"load": L, "members": [g["kn"] for g in members],
                        "db_per_load": {g["kn"]: g["db_per_load"] for g in members},
                        "slope": {g["kn"]: val(g, "slope") for g in members},
                        "predicted": {g["kn"]: val(g, "predicted") for g in members},
                        "measured": {g["kn"]: val(g, "measured") for g in members},
                        "ratio_low_h_over_high_h": ratios, "carried_by": carry,
                        "low_h": lo_m["kn"], "high_h": hi_m["kn"],
                        "h_low": lo_m["h"], "h_high": hi_m["h"]})
    return out


# --------------------------------------------------------------------------- the run's own checks
def interp_reproduces_its_nodes(fams):
    """The interpolator, pointed at a family's own contentions, must return that family's own benefits."""
    worst = 0.0
    for fam in fams.values():
        for si in range(fam["rows"][0]["n_seeds"]):
            pts = points_of(fam, si)
            for r in fam["rows"]:
                x = r["per_seed_rho_spec"][si]
                y = r["per_seed"][si]
                got = interp_at(pts, x)
                worst = max(worst, abs(got - y))
    return worst


def self_coincidence_is_zero(fams):
    """A family compared against its own curve must produce residuals identically zero."""
    worst = 0.0
    for fam in fams.values():
        coin = coincidence(fam, fam)
        if coin["status"] != "READ":
            return None
        for c in coin["cells"]:
            for x in c["per_seed_residual"]:
                worst = max(worst, abs(x))
    return worst


def shrink_read_here(fams, refs, charged):
    """The measured shrinkage, read through step 7's own family objects (not re-derived from raw cells)."""
    out = []
    for (h, q, comp) in charged:
        for a in sorted({f["agents"] for f in fams.values()}):
            ref = fams["%s/h%.2f/q0.00/c0.0" % (a, h)]
            cfg = fams["%s/h%.2f/q%.2f/c%.1f" % (a, h, q, comp)]
            m = S7.paired_shrinkage(ref, cfg)
            out.append({"family": cfg["kn"], "mean": m.get("mean"), "ci": m.get("ci"),
                        "n_pairs": m.get("n_pairs"), "n_unpaired": m.get("n_unpaired"),
                        "not_located": m.get("not_located")})
    return out


def load_step7_record(path=None):
    """Step 7's product, or None when it is not where this file expects it."""
    p = path or os.path.join(HERE, STEP7_RECORD)
    if not os.path.exists(p):
        return None
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def norm_cells(cells):
    """A crossing's cells as a comparable value: a list of `[agents, workers]` int pairs.

    Step 7's record comes back from JSON as lists of lists; the live family object carries whatever
    `crossing_of_curve` built (tuples).  Comparing them directly compares SHAPES, not crossings: the same
    crossing then reads as "moved" for every family of the run -- which is how this defect was caught, on the
    first deciding run, by a check whose only job was to read a premise back.
    """
    return [[int(c[0]), int(c[1])] if isinstance(c, (list, tuple)) else [None, int(c)] for c in cells]


def window_preserves_step7_crossing(fams, published, seeds, tol=1e-9):
    """Did the NARROW window keep the crossing step 7 published?  A premise, measured -- not assumed.

    This file needs the crossing's neighbourhood rather than the whole curve, so its windows are narrower than
    step 7's (A=16: c=2..9 where step 7 used 2..12; A=64: c=12..26 where step 7 used 12..40).  Narrowing a
    window CAN move a crossing in general: the rule finds the pair of adjacent cells that straddle zero, and a
    pair outside the window is not found.  "The rule does not read the window's ends" is a claim about code --
    the honest form is to read step 7's OWN published crossings back and compare, which also catches the case
    where a window truncates the charged family before its crossing.

    Returns READ-ish statuses only: PRESERVED (every family present in the record agrees, cells and x*),
    MOVED (with the families that differ), or NOT TAKEN with a reason (record absent, or taken on other
    seeds) -- a reading that was not taken must never look like one that passed.
    """
    if not published:
        return {"status": "NOT TAKEN", "reason": "%s is not in %s" % (STEP7_RECORD, HERE)}
    pub_seeds = published.get("seeds")
    if pub_seeds and list(pub_seeds) != list(seeds):
        return {"status": "NOT TAKEN",
                "reason": "%s was taken on %d seed(s) (%s...), this run on %d (%s...)"
                          % (STEP7_RECORD, len(pub_seeds), pub_seeds[0], len(seeds), seeds[0])
                          if pub_seeds and seeds else "%s was taken on other seeds" % STEP7_RECORD}
    tables = published.get("families") or {}
    checked, moved, missing, worst = [], [], [], 0.0
    for kn, fam in sorted(fams.items()):
        pub = tables.get(kn)
        if pub is None:
            missing.append(kn)
            continue
        checked.append(kn)
        if bool(pub.get("not_located")) != bool(fam["not_located"]):
            moved.append(kn)
            continue
        if fam["not_located"]:
            continue
        if norm_cells((pub.get("crossing") or {}).get("cells") or []) != norm_cells(fam["crossing"]["cells"]):
            moved.append(kn)
            continue
        if fam["x_star"] is not None and pub.get("x_star") is not None:
            worst = max(worst, abs(fam["x_star"] - pub["x_star"]))
    if not checked:
        return {"status": "NOT TAKEN", "reason": "no family of this run appears in %s" % STEP7_RECORD}
    if moved or worst > tol:
        return {"status": "MOVED", "checked": len(checked), "moved": moved, "missing": missing,
                "worst_x_star_delta": worst}
    return {"status": "PRESERVED", "checked": len(checked), "missing": missing, "worst_x_star_delta": worst}


def shrinkage_agrees_with_step7(seeded, published, tol=1e-12):
    """The shrinkage this file reads must BE step 7's published number, not a second opinion about it.

    Both are computed by calling step 7's own `paired_shrinkage` on families this file built itself, so the
    comparison is between an independent re-measurement and the record -- and it is the anchor that says the
    NARROWER windows changed no measurement.  Reported as a worst absolute difference plus the families that
    disagree, and NOT TAKEN (with a reason) when the record or the family is absent.
    """
    if not published:
        return {"status": "NOT TAKEN", "reason": "%s absent" % STEP7_RECORD}
    table = {e["family"]: e for e in (published.get("shrinkage") or [])}
    if not table:
        return {"status": "NOT TAKEN", "reason": "%s carries no shrinkage entries" % STEP7_RECORD}
    worst, checked, missing, disagree = 0.0, [], [], []
    for entry in seeded:
        pub = table.get(entry["family"])
        if pub is None:
            missing.append(entry["family"])
            continue
        checked.append(entry["family"])
        if entry["mean"] is None or pub.get("mean") is None:
            if entry["mean"] != pub.get("mean"):
                disagree.append(entry["family"])
            continue
        d = abs(entry["mean"] - pub["mean"])
        worst = max(worst, d)
        if d > tol:
            disagree.append(entry["family"])
    if not checked:
        return {"status": "NOT TAKEN",
                "reason": "none of this run's %d charged families appears in %s"
                          % (len(seeded), STEP7_RECORD)}
    return {"status": "AGREES" if not disagree else "DISAGREES", "checked": len(checked),
            "missing": missing, "disagreeing": disagree, "worst_abs_delta": worst}


def run_checks(groups, fams, node_gap, self_gap, seeded, window=None, anchor=None):
    checks = {
        "interpolation_reproduces_its_nodes": node_gap <= RESIDUAL_TOL,
        "self_comparison_is_exactly_zero": (self_gap is not None and self_gap <= RESIDUAL_TOL),
        # Both families of every group must have LOCATED a crossing: without that there is no measured
        # shrinkage to compare against and no secant to divide the displacement by.  Read on the status that
        # carries the fact (`shrink_known`), not on the dict being non-empty.
        "every_group_located_its_crossing": all(
            bool((g["measured_shrinkage"] or {}).get("shrink_known")) for g in groups),
        "every_group_shares_its_reference_seeds": all(
            g["coincidence_charged_at_ref"]["status"] == "READ" for g in groups),
        "declared_load_is_charged": all(
            (g["charge_per_step"] > 0.0) for g in groups if g["load"] > 0),
        "measured_shrinkage_is_step7s_own_read": (seeded is not None and
                                                 all(s["not_located"] is not None for s in seeded)),
    }
    # A reading that was not taken is not registered as a check at all (its reason is printed instead): the
    # exit code answers "is this run trustworthy", and it can only answer for the readings that were taken.
    if window is not None and window.get("status") == "PRESERVED":
        checks["the_narrow_window_keeps_step7s_crossing"] = True
    if anchor is not None and anchor.get("status") == "AGREES":
        checks["the_shrinkage_read_here_is_step7s_published_number"] = True
    return checks


# --------------------------------------------------------------------------- report
def fmt_ci(ci, spec="%+.5f"):
    return "-" if not ci else (spec + ".." + spec) % tuple(ci)


def fmt_ratio(v):
    return "-" if v is None else "%.3f" % v


def report(groups, hr, sh, load_tab, checks, cfg0, seeds, windows, node_gap, self_gap, window=None,
           anchor=None):
    print("== step 8: what moves the boundary when the effect channel is charged | %d seeds %d..%d |"
          " mT=%.1f mS=%.1f steps=%d ==" % (len(seeds), seeds[0], seeds[-1], cfg0["mT"], cfg0["mS"],
                                            cfg0["steps"]))
    print("   windows %s | references h %s | charged %s" % (list(windows), list(REFS), list(CHARGED)))
    print()
    print("   H-rho and H-shift, per (pool, h, config):")
    print("     %-24s %-7s %-11s %-13s %-20s %-13s %-20s %-9s"
          % ("family", "load", "charge/step", "db (pp)", "db 95% CI", "slope (pp/rho)", "measured shrink",
             "prediction"))
    for g in sorted(groups, key=lambda x: (x["pool"], -x["h"], x["kn"])):
        gp = g["gap"]
        sl = g["slope"]
        ms = g["measured_shrinkage"] or {}
        pr = g["prediction"]
        print("     %-24s %-7.4f %-11.6f %-13s %-20s %-13s %-20s %-9s"
              % (g["kn"], g["load"], g["charge_per_step"],
                 ("%+.5f" % gp["mean"]) if gp.get("status") == "READ" else gp.get("status"),
                 fmt_ci(gp.get("ci")) if gp.get("status") == "READ" else "-",
                 ("%+.3f" % sl["mean"]) if sl.get("status") == "READ" else sl.get("status"),
                 ("%+.5f [%s]" % (ms["mean"], fmt_ci(ms["ci"]))) if ms.get("mean") is not None else
                 str(ms.get("not_located")),
                 ("%+.5f" % pr["value"]) if pr.get("status") == "READ" else pr.get("status")))
        c = g["comparison"]
        co = g["coincidence_charged_at_ref"]
        print("       -> H-rho: %s (%d comparable cell(s), %d excluding zero of which %d beyond the"
              " linearisation bound %s, %d not comparable) | H-shift: %s%s"
              % ("coincident" if co["all_contain_zero"] else "DEVIATES",
                 len([x for x in co["cells"] if x["ci"]]),
                 co["n_cells_excluding_zero"], co["n_cells_excluding_zero_beyond_bound"],
                 ("%.2e" % co["worst_bound"]) if co.get("worst_bound") is not None else "n/a",
                 co["n_skipped"],
                 c["verdict"], (" (predicted/measured miss by %.2fx)" % c["factor"]) if c.get("factor") else ""))
    print()
    print("   H-rho overall: %s%s" % (hr["verdict"], (" -- deviating: %s" % hr.get("deviating")) if
                                      hr.get("deviating") else
                                      "" if hr["verdict"] == "COINCIDENT" else " (%s)" % hr.get("reason")))
    print("   H-shift overall: %s | consistent %s | inconsistent %s"
          % (sh["verdict"], sh.get("consistent"), sh.get("inconsistent")))
    print()
    print("   the load-law question, decomposed (same declared load, different h):")
    for blk in load_tab:
        print("     load %.4f:" % blk["load"])
        for kn in blk["members"]:
            print("       %-24s db/load %-10s slope %-10s predicted %-10s measured %s"
                  % (kn,
                     ("%+.4f" % blk["db_per_load"][kn]) if blk["db_per_load"][kn] is not None else "-",
                     ("%+.3f" % blk["slope"][kn]) if blk["slope"][kn] is not None else "-",
                     ("%+.5f" % blk["predicted"][kn]) if blk["predicted"][kn] is not None else "-",
                     ("%+.5f" % blk["measured"][kn]) if blk["measured"][kn] is not None else "-"))
        r = blk["ratio_low_h_over_high_h"]
        print("       -> h=%.2f over h=%.2f: measured x%s | predicted x%s | db/load x%s | slope x%s%s"
              % (blk["h_low"], blk["h_high"], fmt_ratio(r["measured"]), fmt_ratio(r["predicted"]),
                 fmt_ratio(r["db_per_load"]), fmt_ratio(r["slope"]),
                 ("  (carried by %s)" % blk["carried_by"]) if blk["carried_by"] else ""))
    if not load_tab:
        print("     no matched-load pair was read")
    print()
    print("   checks: " + " | ".join("%s=%s" % (k, "OK" if v else "FAIL") for k, v in sorted(checks.items())))
    print("   worst |interp(node) - node| %.2e | worst self-residual %.2e" % (node_gap, self_gap))
    if anchor is not None:
        print("   step-7 anchor: shrinkage %s over %s famil%s%s"
              % (anchor["status"], anchor.get("checked", 0),
                 "y" if anchor.get("checked") == 1 else "ies",
                 "" if anchor["status"] == "AGREES" else
                 " -- %s" % (anchor.get("reason") or "disagreeing: %s (worst |delta| %.2e)"
                             % (anchor.get("disagreeing"), anchor.get("worst_abs_delta")))))
    if window is not None:
        print("   window premise (%s): %s%s" % (STEP7_RECORD, window["status"],
              "" if window["status"] == "PRESERVED" else
              " -- %s" % (window.get("reason") or "families moved: %s" % window.get("moved"))))


# --------------------------------------------------------------------------- selftest
def case(name, ok, detail):
    return (name, bool(ok), detail)


def fake_fam(kn, rows, crossing=None):
    rows = sorted(rows, key=lambda r: r["rho_spec"])
    return {"kn": kn, "agents": 16, "h": 0.9, "q": 0.0, "comp": 0.0, "c_range": [1, len(rows)],
            "rows": rows, "crossing": crossing or {"ambiguous": False, "cells": [[16, rows[-1]["workers"]],
                                                                                 [16, rows[0]["workers"]]]},
            "not_located": False,
            "x_star": 0.9, "load": 0.0, "measured_charge_per_step": 0.0}


def fake_row(workers, rho, benefit, n_seeds=4):
    return {"workers": workers, "rho_spec": rho, "benefit_pct": benefit, "n_seeds": n_seeds,
            "per_seed": [benefit] * n_seeds, "per_seed_rho_spec": [rho] * n_seeds,
            "ci": [benefit - 0.01, benefit + 0.01]}


def fake_curve(kn, rho_lo, rho_hi, n=6, offset=0.0):
    """A monotone decreasing synthetic family: benefit from +2 pp at the loosest contention to -2 pp at the
    tightest, displaced by `offset`."""
    rows = []
    for i in range(n):
        w = 100 + i
        rho = rho_lo + (rho_hi - rho_lo) * i / (n - 1)
        b = 2.0 - 4.0 * i / (n - 1) - offset
        rows.append(fake_row(w, rho, b))
    return fake_fam(kn, rows)


def selftest():
    """Each arm fails for its OWN reason, and the three verdict rules are each shown to be reachable."""
    out = []

    # 1. the interpolator: nodes exact, middle linear, outside is None (not extrapolated)
    pts = [(0.10, 1.0), (0.20, 3.0), (0.30, 2.0)]
    mid = interp_at(pts, 0.15)
    out.append(case("interpolation_is_exact_at_nodes_and_none_outside",
                    interp_at(pts, 0.10) == 1.0 and interp_at(pts, 0.30) == 2.0
                    and abs(mid - 2.0) < 1e-12
                    and interp_at(pts, 0.05) is None and interp_at(pts, 0.35) is None,
                    "nodes exact, midpoint %.3f, outside -> %s / %s"
                    % (mid, interp_at(pts, 0.05), interp_at(pts, 0.35))))

    # 2. a family against itself has exactly zero residuals (the comparison's baseline)
    f = fake_curve("self", 0.80, 0.99)
    coin = coincidence(f, f)
    worst = max(abs(x) for c in coin["cells"] for x in c["per_seed_residual"])
    out.append(case("self_comparison_is_exactly_zero", coin["status"] == "READ" and worst == 0.0,
                    "status %s, worst residual %.1e" % (coin["status"], worst)))

    # 3. the two models are separable: a displaced curve must show a non-zero gap AND its prediction must
    #    equal offset / |slope| (the formula the model declares)
    base = fake_curve("base", 0.80, 0.99)
    moved = fake_curve("moved", 0.80, 0.99, offset=0.5)
    coin2 = coincidence(base, moved)
    gap = crossing_gap(coin2, base)
    sl = slope_with_interval(base)
    pred = predict_shrink(gap, sl)
    rhs = 0.5 / abs(sl["mean"])
    out.append(case("the_shift_model_is_separable_and_its_formula_holds",
                    coin2["n_cells_excluding_zero"] == len([c for c in coin2["cells"] if c["ci"]])
                    and gap["status"] == "READ" and abs(gap["mean"] - 0.5) < 1e-12
                    and abs(pred["value"] - rhs) < 1e-12,
                    "every comparable cell excludes zero; gap %.4f (= the plant); prediction %.6f vs"
                    " db/|slope| %.6f" % (gap["mean"], pred["value"], rhs)))

    # 4. disjoint contention ranges are NOT COMPARABLE with a reason, never a silent zero
    far = fake_curve("far", 0.30, 0.50)
    coin3 = coincidence(base, far)
    out.append(case("disjoint_ranges_are_not_comparable",
                    coin3["status"] == NOT_COMPARABLE and coin3["n_compared"] == 0
                    and "inside" in (coin3["reason"] or ""),
                    "status %s (%s), compared %d" % (coin3["status"], coin3["reason"], coin3["n_compared"])))

    # 5. the comparison is TWO-SIDED: the same prediction read against an interval that contains it and
    #    against a fixture whose slope is halved (which doubles the prediction and must miss).  An arm that
    #    only asserted "the verdict is one of the two strings" would be satisfied by a function that always
    #    returns the same one -- the interval here is centred on the honest prediction so the CONSISTENT side
    #    is exercised, not merely reachable in principle.
    meas = {"mean": pred["value"], "ci": [pred["value"] - 5e-04, pred["value"] + 5e-04],
            "shrink_known": True, "not_located": False}
    ok = compare_to_measured(pred, meas)
    bad = compare_to_measured(predict_shrink(gap, {"status": "READ", "mean": sl["mean"] / 2.0,
                                                   "ci": None}), meas)
    out.append(case("the_comparison_can_say_both",
                    ok["verdict"] == "CONSISTENT" and ok["point_inside"]
                    and bad["verdict"] == "INCONSISTENT"
                    and abs(bad["predicted"] / ok["predicted"] - 2.0) < 1e-12,
                    "prediction %.6f inside [%.6f, %.6f] -> %s; halved-slope %.6f -> %s (misses by %.2fx)"
                    % (ok["predicted"], meas["ci"][0], meas["ci"][1], ok["verdict"], bad["predicted"],
                       bad["verdict"], bad["factor"])))

    # 6. the two overall verdicts are reachable in their own terms
    g_ok = {"kn": "a", "coincidence_charged_at_ref": {"status": "READ", "all_contain_zero": True,
                                                      "n_cells_excluding_zero": 0,
                                                      "n_cells_excluding_zero_beyond_bound": 0},
            "comparison": {"verdict": "CONSISTENT"}}
    g_bad = {"kn": "b", "coincidence_charged_at_ref": {"status": "READ", "all_contain_zero": False,
                                                       "n_cells_excluding_zero": 2,
                                                       "n_cells_excluding_zero_beyond_bound": 2},
             "comparison": {"verdict": "INCONSISTENT", "factor": 3.0}}
    # the third branch: cells whose interval excludes zero but whose residual is inside what interpolation
    # alone can produce -- a deviation the design cannot distinguish from its own approximation
    g_tiny = {"kn": "c", "coincidence_charged_at_ref": {"status": "READ", "all_contain_zero": False,
                                                        "n_cells_excluding_zero": 2,
                                                        "n_cells_excluding_zero_beyond_bound": 0},
              "comparison": {"verdict": "CONSISTENT"}}
    out.append(case("the_overall_verdicts_are_reachable",
                    hr_verdict([g_ok])["verdict"] == "COINCIDENT"
                    and hr_verdict([g_bad])["verdict"] == "DEVIATES"
                    and hr_verdict([g_tiny])["verdict"] == "COINCIDENT WITHIN RESOLUTION"
                    and shift_verdict([g_ok])["verdict"] == "ALL CONSISTENT"
                    and shift_verdict([g_bad])["verdict"] == "ALL INCONSISTENT"
                    and shift_verdict([g_ok, g_bad])["verdict"] == "MIXED",
                    "H-rho COINCIDENT / DEVIATES / COINCIDENT-WITHIN-RESOLUTION and H-shift ALL"
                    " CONSISTENT / ALL INCONSISTENT / MIXED all reachable"))

    # 7. the load decomposition groups on (declared load, POOL) and refuses anything else
    def g(kn, load, h, db, slope=-30.0, pred=0.001, meas=0.001, pool=16):
        return {"kn": kn, "load": load, "h": h, "pool": pool, "db_per_load": db,
                "slope": {"status": "READ", "mean": slope},
                "prediction": {"status": "READ", "value": pred},
                "measured_shrinkage": {"mean": meas, "shrink_known": True, "not_located": False}}
    tab = load_decomposition([g("x", 0.005, 0.9, 2.0), g("y", 0.005, 0.5, 4.0), g("z", 0.005, 0.5, 9.0)])
    two_pools = load_decomposition([g("a16", 0.005, 0.5, 2.0, pool=16), g("a64", 0.005, 0.9, 3.0, pool=64)])
    out.append(case("the_load_decomposition_groups_correctly",
                    len(tab) == 1 and tab[0]["load"] == 0.005 and set(tab[0]["members"]) == {"x", "y", "z"}
                    and load_decomposition([g("x", 0.005, 0.9, 1.0), g("z", 0.005, 0.9, 1.0)]) == []
                    and two_pools == [],
                    "one matched-load group with %d member(s); members sharing h are skipped; two families"
                    " from DIFFERENT pools are never paired (%d group(s) from a cross-pool fixture)"
                    % (len(tab[0]["members"]), len(two_pools))))

    # 8. the decomposition names WHICH factor carries the h-dependence, and it can name either one
    slope_carries = load_decomposition([g("low", 0.005, 0.5, 2.0, slope=-100.0, pred=0.02, meas=0.02),
                                        g("high", 0.005, 0.9, 2.0, slope=-200.0, pred=0.01, meas=0.01)])
    db_carries = load_decomposition([g("low", 0.005, 0.5, 4.0, slope=-200.0, pred=0.02, meas=0.02),
                                     g("high", 0.005, 0.9, 2.0, slope=-200.0, pred=0.01, meas=0.01)])
    out.append(case("the_decomposition_names_the_carrying_factor",
                    len(slope_carries) == 1 and slope_carries[0]["carried_by"] == "the slope"
                    and len(db_carries) == 1 and db_carries[0]["carried_by"] == "the drop per unit load"
                    and abs(slope_carries[0]["ratio_low_h_over_high_h"]["measured"] - 2.0) < 1e-12,
                    "same db/load and 2x slope -> '%s'; 2x db/load and same slope -> '%s'"
                    % (slope_carries[0]["carried_by"], db_carries[0]["carried_by"])))

    # 9. the window premise is THREE-SIDED: preserved, moved (named), and not-taken with a reason
    def fam_with(kn, cells, x_star):
        f = fake_fam(kn, [fake_row(4, 0.98, 1.0), fake_row(3, 0.99, -1.0)],
                     crossing={"ambiguous": False, "cells": cells})
        f["x_star"] = x_star
        return f
    kn = "16/h0.90/q0.00/c0.0"
    pub = {"seeds": [101, 102],
           "families": {kn: {"not_located": False, "crossing": {"cells": [[16, 4], [16, 3]]},
                             "x_star": 0.985}}}
    # the record's cells arrive as JSON lists; a live family's may be tuples -- the same crossing must read
    # PRESERVED either way (this is the defect the first deciding run printed as "MOVED, all 14 families")
    f_tuples = fam_with(kn, ((16, 4), (16, 3)), 0.985)
    w_shapes = window_preserves_step7_crossing({kn: f_tuples}, pub, [101, 102])
    w_ok = window_preserves_step7_crossing({kn: fam_with(kn, [[16, 4], [16, 3]], 0.985)}, pub, [101, 102])
    w_moved = window_preserves_step7_crossing({kn: fam_with(kn, [[16, 5], [16, 4]], 0.99)}, pub, [101, 102])
    w_absent = window_preserves_step7_crossing({kn: fam_with(kn, [[16, 4], [16, 3]], 0.985)}, None, [101, 102])
    w_seeds = window_preserves_step7_crossing({}, pub, [201, 202])
    out.append(case("the_window_premise_is_three_sided",
                    w_ok["status"] == "PRESERVED" and w_ok["checked"] == 1
                    and w_moved["status"] == "MOVED" and w_moved["moved"] == [kn]
                    and w_absent["status"] == "NOT TAKEN" and w_seeds["status"] == "NOT TAKEN"
                    and w_shapes["status"] == "PRESERVED",
                    "preserved(1 checked) / moved(%s) / absent(%s) / other-seeds(%s) / tuple-vs-list"
                    " cells read %s"
                    % (w_moved["moved"], w_absent["reason"][:28], w_seeds["reason"][:28],
                       w_shapes["status"])))

    # 10. the linearisation bound is an UPPER estimate and it is tight on a known quadratic: on
    #     f(x)=1000(x-0.5)^2 with nodes 0.1 apart the bound is d2/8 = 2.5, which is exactly the interpolation
    #     error at a midpoint -- so the bound is not merely "large", and it must vanish at a node.
    quad = [(0.10, 1000.0 * (0.10 - 0.5) ** 2), (0.20, 1000.0 * (0.20 - 0.5) ** 2),
            (0.30, 1000.0 * (0.30 - 0.5) ** 2), (0.40, 1000.0 * (0.40 - 0.5) ** 2)]
    bnd = local_linearisation_bound(quad, 0.15)
    true_err = abs(interp_at(quad, 0.15) - 1000.0 * (0.15 - 0.5) ** 2)
    out.append(case("the_linearisation_bound_brackets_the_real_error",
                    bnd is not None and abs(bnd - 2.5) < 1e-12 and true_err <= bnd + 1e-12
                    and local_linearisation_bound(quad, 0.20) == 0.0
                    and local_linearisation_bound([(0.1, 1.0), (0.2, 2.0)], 0.15) is None,
                    "bound %.4f vs real interpolation error %.4f at the midpoint; 0.0 at a node; None with"
                    " two nodes" % (bnd, true_err)))

    # 11. the step-7 anchor is three-sided: AGREES, DISAGREES (naming the family), NOT TAKEN with a reason
    seeded = [{"family": "f1", "mean": 0.00304}, {"family": "f2", "mean": 0.00665}]
    pub = {"shrinkage": [{"family": "f1", "mean": 0.00304}, {"family": "f2", "mean": 0.00665}]}
    a_ok = shrinkage_agrees_with_step7(seeded, pub)
    a_bad = shrinkage_agrees_with_step7([{"family": "f1", "mean": 0.00305}], pub)
    a_none = shrinkage_agrees_with_step7(seeded, None)
    out.append(case("the_step7_anchor_is_three_sided",
                    a_ok["status"] == "AGREES" and a_ok["checked"] == 2 and a_ok["worst_abs_delta"] == 0.0
                    and a_bad["status"] == "DISAGREES" and a_bad["disagreeing"] == ["f1"]
                    and a_none["status"] == "NOT TAKEN",
                    "two families agree exactly; a 1e-05 drift is named; a missing record is NOT TAKEN"))

    bad = [n for n, ok, _ in out if not ok]
    for n, ok, d in out:
        print("  %-46s %s  %s" % (n, "ok" if ok else "FAIL", d))
    print("  selftest: %d case(s), %d failed" % (len(out), len(bad)))
    return 1 if bad else 0


# --------------------------------------------------------------------------- main
def build_families(cfg0, windows, seeds):
    """Every family this round needs: the references and the charged configs, at every pool size."""
    fams = {}
    for (a, c_lo, c_hi) in windows:
        for h in REFS:
            cfg = dict(cfg0, q=0.0, comp=0.0)
            fams["%s/h%.2f/q0.00/c0.0" % (a, h)] = S7.family3(cfg, a, c_lo, c_hi, h, seeds)
        for (h, q, comp) in CHARGED:
            cfg = dict(cfg0, q=q, comp=comp)
            fams["%s/h%.2f/q%.2f/c%.1f" % (a, h, q, comp)] = S7.family3(cfg, a, c_lo, c_hi, h, seeds)
    return fams


def main(argv=None):
    ap = argparse.ArgumentParser(description="issue #50 step 8 -- what moves the boundary under a charge")
    ap.add_argument("--seeds", type=int, default=16)
    ap.add_argument("--seed0", type=int, default=101)
    ap.add_argument("--quick", action="store_true", help="3 seeds and a narrow pool for a smoke run")
    ap.add_argument("--json", metavar="PATH", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    seeds = [args.seed0 + i for i in range(3 if args.quick else args.seeds)]
    cfg0 = I.default_cfg()
    windows = ((16, 3, 6),) if args.quick else WINDOWS
    print("building families ...")
    fams = build_families(cfg0, windows, seeds)
    groups = []
    for (a, _lo, _hi) in windows:
        for (h, q, comp) in CHARGED:
            ref = fams["%s/h%.2f/q0.00/c0.0" % (a, h)]
            cfg = fams["%s/h%.2f/q%.2f/c%.1f" % (a, h, q, comp)]
            measured = S7.paired_shrinkage(ref, cfg)
            groups.append(group(a, h, (q, comp), ref, cfg, measured))
    hr = hr_verdict(groups)
    sh = shift_verdict(groups)
    load_tab = load_decomposition(groups)
    node_gap = interp_reproduces_its_nodes(fams)
    self_gap = self_coincidence_is_zero(fams)
    seeded = shrink_read_here(fams, REFS, CHARGED)
    window = ({"status": "NOT TAKEN", "reason": "--quick runs a different window than step 7's record"}
              if args.quick else
              window_preserves_step7_crossing(fams, load_step7_record(), seeds))
    record = None if args.quick else load_step7_record()
    anchor = shrinkage_agrees_with_step7(seeded, record)
    checks = run_checks(groups, fams, node_gap, self_gap, seeded, window, anchor)
    report(groups, hr, sh, load_tab, checks, cfg0, seeds, windows, node_gap, self_gap, window, anchor)
    print("   H-rho overall: %s | H-shift overall: %s" % (hr["verdict"], sh["verdict"]))
    payload = {
        "what": "issue #50 instrument v0 step 8 -- what moves the boundary when the effect channel is charged",
        "seeds": seeds, "windows": windows, "refs": list(REFS), "charged": [list(c) for c in CHARGED],
        "model": {k: cfg0[k] for k in sorted(cfg0) if not isinstance(cfg0[k], list)},
        "declared": {
            "H_rho": "b_charged(rho) == b_ref(rho): the charge acts only through measured contention",
            "H_shift": "b_charged(rho) == b_ref(rho) - db -> shrink_pred = db / |s|, s a SECANT over the"
                       " reference crossing cells",
            "unit": "a draw stream; curves are built per seed and residuals are paired by seed",
            "not_comparable": "a target contention outside the reference family's own range is NOT COMPARABLE",
            "residual_tol": RESIDUAL_TOL,
        },
        "families": fams, "groups": groups, "hr_rho": hr, "h_shift": sh,
        "load_decomposition": load_tab, "seeded_shrinkage": seeded, "checks": checks,
        "window_check": window, "step7_anchor": anchor,
        "interp_node_worst": node_gap, "self_residual_worst": self_gap,
    }
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
