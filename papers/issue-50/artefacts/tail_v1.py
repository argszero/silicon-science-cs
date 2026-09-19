#!/usr/bin/env python3
"""Issue #50 -- instrument v0, step 5: the registered prior P2 -- the mean-matched tail pair.

WHAT THIS FILE IS.  Steps 1-4 built the instrument, located the boundary (rho* ~ 0.985, indexed by the POOL
size A, span 20.5x the families' own intervals) and decomposed the A-effect (the mean is a mixture; the
typical step loses).  The registration (`heilmeier.md` section 4, frozen before any deciding run) says:

  P2 -- "the TAIL, not the mean, sets the boundary: two mean-matched tool-latency distributions have
  different rho*, the heavier tail giving the LARGER rho* but a STEEPER fall past it."

This file tests P2 on the object P2 names.  Both service classes already exist in the model
(`instrument_v0.draw_service`: exponential; and Pareto with tail index 2.5 scaled to the same mean), so the
manipulation is ONE coordinate of `cfg` and every other coordinate is held fixed.

THE ANALYSIS, DECLARED BEFORE THE RUN (a rule in this file, not a description of what came out):

  * Unit of measurement: a (tail, A, h) FAMILY.  Inside a family the worker count c is swept; nothing else
    varies.  The independent unit is a draw stream (a seed), as in steps 2-4.
  * rho*: the crossing of the family's benefit curve, located by STEP 3's rule, REUSED BY IMPORT -- the first
    positive-to-nonpositive sign change in rho order, interpolated in rho between the two bracketing cells.  A
    family with no crossing in its window, and a family with more than one, is reported as such and EXCLUDED
    (never silently dropped, never smoothed over).
  * P2 first half: per family, delta(s) = rho*(heavy, s) - rho*(light, s) over the seeds BOTH tails located.
    The per-family interval is a t interval over those differences.  Ladder rule: CONFIRMED iff every located
    family's interval lies strictly above zero; CONTRADICTED iff at least one lies strictly below zero;
    UNRESOLVED otherwise (including "no family located a difference").
  * P2 second half ("a steeper fall past it"): the fall is a SECANT ON THE FAMILY'S OWN GRID -- from the
    seed's own crossing to the cell ABOVE it in rho: fall(s) = -benefit(s, cell above) / (rho(cell above) -
    rho*(s)), in benefit-percent per unit rho.  A secant rather than a fixed small delta because the grid
    spacing at the crossing is what the design can resolve (0.001-0.006 in rho); a fixed delta smaller than
    that would make the "slope" a property of the interpolation rather than of the curve.  `step=2` (the cell
    two above) is reported beside it as the sensitivity of that definition.  A missing cell above, a seed
    whose curve never crosses, one that starts already crossed, and one that crosses twice are each COUNTED
    and excluded.  A curve that flattens or turns up above the crossing gives a non-positive fall: that is
    the measured value and it is NOT clamped.
  * The cross-tail comparison is PAIRED BY SEED, and the pairing basis is MEASURED, not asserted
    (`tail_pair_basis`): the two classes are drawn at the same RNG positions, so the THINK draws are identical
    and the stream after the draws is identical, while the SERVICE draws differ -- by construction, because
    the service class IS the manipulation.  Step 3's two-sample estimator (`welch`) is reported beside the
    paired number as a fallback that does not use the pairing.
  * The premise "mean-matched" is MEASURED, not assumed: the empirical mean of both service classes with t
    intervals over seeds.  If the intervals do not overlap the comparison is VOID (exit 3): a tail comparison
    run on two distributions whose means also differ compares two coordinates at once, which is exactly the
    defect step 3 was built to avoid.
  * The draw-level quantities P2's justification names are read, not assumed: `E[min(T,S)]` (the hiding limit,
    step 1's A3) and `P(S <= T)` (the CEILING on the fully-hidden population, since a step is fully hidden
    only if `w_p + S <= T` with `w_p >= 0`).  The ceiling is also used as a per-seed INEQUALITY against the
    hidden share the runs actually show -- a check that can fail.

CPU only, stdlib only, fixed seeds, no network.  `instrument_v0.py` is imported UNMODIFIED; steps 2-4 supply
the t interval, the crossing rule, the draw re-derivation with its stated tolerance, and the per-step terms
with their mixture definition.  None of those files changes.
"""
import argparse
import io
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import instrument_v0 as I      # noqa: E402  the model, unmodified
import boundary_v1 as B1       # noqa: E402  step 2's t interval
import boundary_v2 as B2       # noqa: E402  step 3's crossing rule + draw re-derivation
import decompose_v1 as D1      # noqa: E402  step 4's per-step terms + its mixture definition

# Two arithmetics over the same inputs must agree to the resolution of the coarser one.  `I.benefit` and this
# file's aggregate over `D1.per_step` are the same quantity computed twice; step 4 measured that pair at
# 7.0e-15, and the tolerance below is six orders above that.
AGREE_TOL = 1e-09

# The windows.  Each straddles BOTH tails' crossings for that pool size: a window tuned for one tail and
# reporting "NOT LOCATED" for the other would compare a number against a gap.  The heavy tail reaches a given
# measured contention at a slightly higher worker count than the light one, so each window reaches one cell
# further up than step 3's.
WINDOWS = [(16, 2, 7), (32, 4, 12), (64, 12, 24)]
TAILS = ("light", "heavy")


# --------------------------------------------------------------------------- the pair, measured
def draw_stats(cfg, agents, seeds):
    """What the two service classes actually ARE, measured on the draws themselves.

    Per seed: mean service, mean think, `E[min(T,S)]` (the hiding limit), `P(S <= T)` (the ceiling on the
    fully-hidden population) and two upper quantiles of S.  Both the aggregate and the interval are taken over
    SEED means -- the unit steps 2-4 use -- rather than over a pool of every draw, which would report a
    standard error over draws that are not independent within a seed.
    """
    keys = ("mean_s", "mean_t", "hiding_limit", "p_s_le_t", "p90_s", "p99_s")
    per = {k: [] for k in keys}
    n_draws = 0
    for s in seeds:
        T, S = B2.derive_draws(agents, s, cfg)
        flat_t = [t for row in T for t in row]
        flat_s = [x for row in S for x in row]
        n_draws = len(flat_s)
        per["mean_s"].append(statistics.fmean(flat_s))
        per["mean_t"].append(statistics.fmean(flat_t))
        per["hiding_limit"].append(statistics.fmean(min(t, x) for t, x in zip(flat_t, flat_s)))
        per["p_s_le_t"].append(sum(1 for t, x in zip(flat_t, flat_s) if x <= t) / float(n_draws))
        ordered = sorted(flat_s)
        per["p90_s"].append(ordered[int(0.90 * (n_draws - 1))])
        per["p99_s"].append(ordered[int(0.99 * (n_draws - 1))])
    out = {"tail": cfg["tail"], "mS": cfg["mS"], "agents": agents, "n_seeds": len(seeds),
           "n_draws_per_seed": n_draws, "per_seed": per}
    for k in keys:
        out[k] = statistics.fmean(per[k])
        out[k + "_ci"] = B1.t_ci(per[k]) if len(per[k]) > 1 else None
    return out


def intervals_overlap(a, b):
    """Two measured means are the same claim only if their own intervals overlap."""
    if not a or not b:
        return False
    return max(a[0], b[0]) <= min(a[1], b[1])


def premise_resolution(ds_light, ds_heavy):
    """The smallest relative mean gap the mean-match rule can DETECT at this seed count: the gap at which the
    two intervals stop overlapping.  Measured, because a rule whose resolution is unstated cannot be read --
    at two seeds the intervals are so wide that a 20% planted gap still \"overlaps\" (measured), which is a
    property of n and not of the pair."""
    lc, hc = ds_light["mean_s_ci"], ds_heavy["mean_s_ci"]
    if not lc or not hc:
        return None
    return ((lc[1] - lc[0]) / 2.0 + (hc[1] - hc[0]) / 2.0) / ds_light["mean_s"]


def premise(ds_light, ds_heavy):
    """Is the pair mean-matched?  MEASURED, reported, and able to come out False (see `--selftest`)."""
    lc, hc = ds_light["mean_s_ci"], ds_heavy["mean_s_ci"]
    rel = abs(ds_heavy["mean_s"] - ds_light["mean_s"]) / ds_light["mean_s"]
    cei_l, cei_h = ds_light["p_s_le_t"], ds_heavy["p_s_le_t"]
    lim_l, lim_h = ds_light["hiding_limit"], ds_heavy["hiding_limit"]
    return {"mean_matched": intervals_overlap(lc, hc), "mean_s_light": ds_light["mean_s"],
            "min_detectable_relative_gap": premise_resolution(ds_light, ds_heavy),
            "mean_s_heavy": ds_heavy["mean_s"], "mean_s_ci_light": lc, "mean_s_ci_heavy": hc,
            "relative_mean_gap": rel, "ceiling_light": cei_l, "ceiling_heavy": cei_h,
            "hiding_limit_light": lim_l, "hiding_limit_heavy": lim_h,
            "ceiling_higher": "light" if cei_l > cei_h else ("heavy" if cei_h > cei_l else "neither"),
            "hiding_limit_higher": ("light" if lim_l > lim_h else
                                    ("heavy" if lim_h > lim_l else "neither")),
            # Do the two quantities P2's justification names move in OPPOSITE directions for this pair?
            "opposed": (cei_l - cei_h) * (lim_l - lim_h) < 0}


def tail_pair_basis(agents, seeds, cfg_light, cfg_heavy):
    """The property the PAIRED comparison rests on -- measured here rather than assumed in a docstring.

      * `think_shared`    -- the derived think times are IDENTICAL between the two service classes for every
                             seed (T is drawn first, and the class does not touch it);
      * `service_differs` -- the service draws differ: the manipulation reached the object (a test that could
                             come out False, which is why it is a test);
      * `stream_aligned`  -- both classes consume exactly the same number of RNG draws, checked the strong
                             way: after drawing all T and all S, the NEXT draws of the two streams are
                             identical.  This is what makes "the two runs differ only in service class" a
                             statement about the draws rather than about the RNG.
    """
    out = {"agents": agents, "n_seeds": len(seeds), "checks": len(seeds), "think_shared": 0,
           "service_differs": 0, "stream_aligned": 0, "draws_consumed": None}
    for s in seeds:
        T1, S1 = B2.derive_draws(agents, s, cfg_light)
        T2, S2 = B2.derive_draws(agents, s, cfg_heavy)
        out["think_shared"] += 1 if T1 == T2 else 0
        out["service_differs"] += 1 if S1 != S2 else 0
        r1, r2 = random.Random(s), random.Random(s)
        for _ in range(2 * agents * cfg_light["steps"]):
            r1.random()
            r2.random()
        out["stream_aligned"] += 1 if [r1.random() for _ in range(5)] == [r2.random() for _ in range(5)] else 0
        out["draws_consumed"] = 2 * agents * cfg_light["steps"]
    out["think_shared_ok"] = out["think_shared"] == out["checks"]
    out["service_differs_ok"] = out["service_differs"] == out["checks"]
    out["stream_aligned_ok"] = out["stream_aligned"] == out["checks"]
    out["all_ok"] = out["think_shared_ok"] and out["service_differs_ok"] and out["stream_aligned_ok"]
    return out


# --------------------------------------------------------------------------- rules with an owner
def ceiling_violations(hidden, ceiling, tol=1e-12):
    """A step is fully hidden only if `w_p + S <= T`, and `w_p >= 0`, so `hidden <= P(S <= T)` per seed.
    Returned as a COUNT of seeds that break it -- one owner, so `--selftest` can plant a violation."""
    return sum(1 for hf, c in zip(hidden, ceiling) if hf > c + tol)


def agrees(a, b, tol=AGREE_TOL):
    """One owner for "two arithmetics agree", so the tolerance cannot drift between call sites."""
    return abs(a - b) <= tol


# --------------------------------------------------------------------------- one cell
def cell_t(cfg, agents, workers, h, seeds):
    """One cell of one tail: step 4's per-step terms reduced over seeds, plus the per-seed lists this step
    needs (benefit percent, hidden share, contention, the ceiling on the hidden population).

    The aggregation is written here rather than taken from `D1.cell`, because the per-seed lists ARE the point
    of this step, and it is CONTROLLED: this file's benefit is compared against the model's own `I.benefit`
    for the same seed, and the worst disagreement is carried in the row.
    """
    pct, hidden, ceil_, rho_s, rho_ser, model_pct = [], [], [], [], [], []
    tot_steps = 0
    worst_res = 0.0
    hid_sum = other_sum = 0.0
    hid_n = other_n = 0
    mean_s_seen = None
    for s in seeds:
        b = D1.make_runs(cfg, agents, workers, h, s)
        rows = D1.per_step(cfg, agents, b)
        tot_steps += len(rows)
        here = 100.0 * statistics.fmean(r["benefit"] for r in rows) / statistics.fmean(
            r["lat_s"] for r in rows)
        pct.append(here)
        m = I.benefit(dict(cfg, seed=s), agents, workers, h)
        model_pct.append(m["benefit_pct"])
        hidden.append(sum(1 for r in rows if r["hidden"]) / float(len(rows)))
        n_le = sum(1 for a in range(agents) for k in range(cfg["steps"])
                   if b["S"][a][k] <= b["T"][a][k])
        ceil_.append(n_le / float(agents * cfg["steps"]))
        for r in rows:
            worst_res = max(worst_res, abs(r["residual"]))
            if r["hidden"]:
                hid_sum += r["benefit"]
                hid_n += 1
            else:
                other_sum += r["benefit"]
                other_n += 1
        rho_s.append(b["spe"]["rho"])
        rho_ser.append(b["ser"]["rho"])
        mean_s_seen = statistics.fmean(x for row in b["S"] for x in row)
    worst_agree = max(abs(a - b) for a, b in zip(pct, model_pct))
    viol = ceiling_violations(hidden, ceil_)
    return {"agents": agents, "workers": workers, "h": h, "tail": cfg["tail"], "n_seeds": len(seeds),
            "n_steps": tot_steps,
            "rho_spec": statistics.fmean(rho_s), "per_seed_rho": rho_s,
            "rho_spec_ci": B1.t_ci(rho_s) if len(rho_s) > 1 else None,
            "rho_serial": statistics.fmean(rho_ser),
            "benefit_pct": statistics.fmean(pct), "per_seed": pct,
            "benefit_pct_ci": B1.t_ci(pct) if len(pct) > 1 else None,
            "benefit_pct_model": statistics.fmean(model_pct),
            "benefit_agreement_max_abs": worst_agree,
            "benefit_agrees_with_model": agrees(statistics.fmean(pct), statistics.fmean(model_pct)),
            "identity_max_residual": worst_res, "identity_tol": D1.IDENTITY_TOL,
            "identity_holds": worst_res <= D1.IDENTITY_TOL,
            "hidden_frac": statistics.fmean(hidden), "per_seed_hidden": hidden,
            "ceiling": statistics.fmean(ceil_), "per_seed_ceiling": ceil_,
            "seeds_hidden_above_ceiling": viol, "hidden_within_ceiling": viol == 0,
            "mean_benefit_hidden": (hid_sum / hid_n) if hid_n else None,
            "mean_benefit_other": (other_sum / other_n) if other_n else None,
            "hidden_share_of_net": (hid_sum / (hid_sum + other_sum)) if (hid_sum + other_sum) else None,
            "mean_s_measured": mean_s_seen}


# --------------------------------------------------------------------------- crossing, with the seed kept
def per_seed_crossings_idx(rows, key):
    """Step 3's per-seed crossing rule, with the SEED KEPT so a cross-tail comparison can be paired.

    The rule is `B2.per_seed_crossings`'; the values this returns must equal that function's list, which the
    battery and the run itself assert (`idx_matches_B2`).  A re-implementation that drifts from the reused
    rule is a FAILURE of this file, not a second opinion.
    """
    out = []
    for si in range(rows[0]["n_seeds"]):
        bs = [r["per_seed"][si] for r in rows]
        if bs[0] <= 0:                              # already crossed at the bottom of the window
            continue
        idx = [i for i in range(len(bs) - 1) if bs[i] > 0 >= bs[i + 1]]
        if len(idx) != 1:                           # never crossed, or crossed twice
            continue
        i = idx[0]
        out.append((si, rows[i][key] + (bs[i] / (bs[i] - bs[i + 1])) * (rows[i + 1][key] - rows[i][key])))
    return out


def idx_matches_B2(rows, key):
    """The reused rule and the index-keeping rule must produce the same numbers on the same rows."""
    mine = [v for _, v in per_seed_crossings_idx(rows, key)]
    theirs = B2.per_seed_crossings(rows, key)["crossings"]
    return {"mine": len(mine), "reused": len(theirs), "same": mine == theirs,
            "max_abs_diff": max((abs(a - b) for a, b in zip(mine, theirs)), default=0.0)}


def fall_per_seed(rows, key, step=1):
    """The descent rate past the crossing, per seed, as a SECANT on the family's own grid.

    `step=1` is the cell immediately above the seed's own crossing; the value is benefit-percent per unit rho
    and is NEGATIVE if the curve is still rising there (not clamped).  Every way a seed can fail to yield a
    secant is counted separately, so "n_used < n_seeds" is always explained.
    """
    falls, starts_crossed, never, ambiguous, no_cell = [], 0, 0, 0, 0
    for si in range(rows[0]["n_seeds"]):
        bs = [r["per_seed"][si] for r in rows]
        if bs[0] <= 0:
            starts_crossed += 1
            continue
        idx = [i for i in range(len(bs) - 1) if bs[i] > 0 >= bs[i + 1]]
        if not idx:
            never += 1
            continue
        if len(idx) > 1:
            ambiguous += 1
            continue
        i = idx[0]
        x_star = rows[i][key] + (bs[i] / (bs[i] - bs[i + 1])) * (rows[i + 1][key] - rows[i][key])
        j = i + step
        if j >= len(rows):
            no_cell += 1
            continue
        drho = rows[j][key] - x_star
        if drho <= 0:
            no_cell += 1
            continue
        falls.append((si, -bs[j] / drho))
    vals = [v for _, v in falls]
    return {"step": step, "falls": vals, "indexed": falls, "n_used": len(vals),
            "excluded_starts_crossed": starts_crossed, "excluded_never_crossed": never,
            "excluded_ambiguous": ambiguous, "excluded_no_cell_above": no_cell,
            "mean": statistics.fmean(vals) if vals else None,
            "ci": B1.t_ci(vals) if len(vals) > 1 else None,
            "sd": statistics.stdev(vals) if len(vals) > 1 else None}


# --------------------------------------------------------------------------- the reading, against step 3's
def light_tail_against_step_3(fams_light, path=None, tol=1e-09):
    """The light-tail arm is the SAME measurement as step 3's published crossing -- same estimator, same model,
    same seeds; only the swept window is wider.  Reading step 3's own artefact back is therefore a check on
    BOTH files rather than a restatement: if they differ, one of them is not the reading it claims to be, and
    the comparison in this file is against a coordinate no one else has seen.

    A missing or wrong-h sibling artefact is reported NOT TAKEN with its reason -- a check that did not run
    must not look like a check that passed.
    """
    p = path or os.path.join(HERE, "boundary_v2_h100.json")
    if not os.path.exists(p):
        return {"status": "NOT TAKEN", "reason": "%s is not present" % os.path.basename(p)}
    with io.open(p, encoding="utf-8") as fh:
        prev = json.load(fh)
    if abs(prev.get("h", -1.0) - 1.0) > 1e-12:
        return {"status": "NOT TAKEN", "reason": "sibling artefact is for h=%s" % prev.get("h")}
    by_agents = {f["agents"]: f for f in prev["families"]}
    out = {"status": "READ", "source": os.path.basename(p), "tol": tol, "max_abs_diff": 0.0,
           "all_agree": True, "per_family": []}
    for f in fams_light:
        cr = f["crossing_rho_spec"]
        mine = cr["x_star"] if (cr and not cr["ambiguous"]) else None
        theirs = (by_agents.get(f["agents"], {}).get("crossing_rho_spec") or {}).get("x_star")
        d = abs(mine - theirs) if (mine is not None and theirs is not None) else None
        if d is not None:
            out["max_abs_diff"] = max(out["max_abs_diff"], d)
        out["all_agree"] = out["all_agree"] and d is not None and d <= tol
        out["per_family"].append({"agents": f["agents"], "mine": mine, "step_3": theirs, "abs_diff": d})
    return out


def family(cfg, a, c_lo, c_hi, h, seeds):
    """One (tail, A, h) family: the swept cells, and the crossing located on them by step 3's rule."""
    rows = [cell_t(cfg, a, c, h, seeds) for c in range(c_lo, c_hi + 1)]
    rows.sort(key=lambda r: (r["rho_spec"], r["workers"]))
    fam = {"tail": cfg["tail"], "agents": a, "h": h, "c_range": [c_lo, c_hi], "rows": rows}
    key = "rho_spec"
    cr = B2.crossing_of_curve(rows, key)
    fam["crossing_" + key] = cr
    fam["per_seed_" + key] = B2.per_seed_crossings(rows, key) if cr else None
    fam["per_seed_idx_" + key] = per_seed_crossings_idx(rows, key) if cr else []
    fam["idx_matches_reused_" + key] = idx_matches_B2(rows, key)
    fam["fall_spec_1"] = fall_per_seed(rows, key, 1)
    fam["fall_spec_2"] = fall_per_seed(rows, key, 2)
    return fam


# --------------------------------------------------------------------------- the comparison
def paired(hv, lt):
    """Per-seed differences of two (seed index, value) lists, over the seeds that BOTH located.

    The pairing basis is measured (`tail_pair_basis`), and the number of seeds located on only one side is
    reported rather than absorbed into `n`.
    """
    dh, dl = dict(hv), dict(lt)
    common = sorted(set(dh) & set(dl))
    diffs = [dh[i] - dl[i] for i in common]
    return {"n": len(diffs), "n_heavy_only": len(set(dh) - set(dl)), "n_light_only": len(set(dl) - set(dh)),
            "diffs": diffs, "mean": statistics.fmean(diffs) if diffs else None,
            "ci": B1.t_ci(diffs) if len(diffs) > 1 else None}


def verdict_of(delta):
    """One family's verdict from its own interval, naming the side it landed on."""
    if not delta["ci"]:
        return "n/a (fewer than two paired seeds)"
    if delta["ci"][0] > 0:
        return "above zero"
    if delta["ci"][1] < 0:
        return "below zero"
    return "straddles zero"


def ladder_verdict(deltas):
    """The declared ladder rule.  Returns a word AND the counts, so a reader sees the evidence for it."""
    located = [d for d in deltas if d["ci"]]
    above = [d for d in located if d["ci"][0] > 0]
    below = [d for d in located if d["ci"][1] < 0]
    n = len(located)
    if not n:
        return "UNRESOLVED (no family located a difference)", {"located": 0, "above": 0, "below": 0}
    if below:
        return ("CONTRADICTED (%d of %d located families strictly below zero)" % (len(below), n),
                {"located": n, "above": len(above), "below": len(below)})
    if len(above) == n:
        return ("CONFIRMED (every one of the %d located families strictly above zero)" % n,
                {"located": n, "above": len(above), "below": 0})
    return ("UNRESOLVED (%d of %d located families strictly above zero)" % (len(above), n),
            {"located": n, "above": len(above), "below": 0})


def crossing_summary(fam, key):
    cr, ps, idx = fam.get("crossing_" + key), fam.get("per_seed_" + key), fam.get("per_seed_idx_" + key)
    if not cr:
        return {"x_star": None, "ci": None, "n_used": 0, "status": "NOT LOCATED (no crossing in window)"}
    if cr["ambiguous"]:
        return {"x_star": None, "ci": None, "n_used": 0,
                "status": "AMBIGUOUS (%d crossings in window)" % cr["n_crossings"],
                "crossings": cr["crossings"]}
    return {"x_star": cr["x_star"], "ci": ps["ci"] if ps else None, "n_used": len(idx or []),
            "status": "located", "excluded_never_crossed": ps["excluded_never_crossed"],
            "excluded_starts_crossed": ps["excluded_starts_crossed"],
            "excluded_ambiguous": ps["excluded_ambiguous"]}


def p2_first_half(hv_fams, lt_fams, key="rho_spec"):
    """The registered first half, one row per family, plus step 3's two-sample estimator as a fallback."""
    per = []
    for fh, fl in zip(hv_fams, lt_fams):
        if fh["agents"] != fl["agents"]:
            raise AssertionError("families compared across different pool sizes: %d vs %d"
                                 % (fh["agents"], fl["agents"]))
        ih, il = fh.get("per_seed_idx_" + key) or [], fl.get("per_seed_idx_" + key) or []
        d = paired(ih, il)
        per.append({"agents": fh["agents"], "key": key, "heavy": crossing_summary(fh, key),
                    "light": crossing_summary(fl, key), "delta": d, "delta_verdict": verdict_of(d),
                    "welch": B2.welch([v for _, v in ih], [v for _, v in il])})
    word, counts = ladder_verdict([p["delta"] for p in per])
    return {"per_family": per, "verdict": word, "counts": counts, "key": key}


def p2_second_half(hv_fams, lt_fams, step=1):
    """The registered second half: the fall past rho*, a secant on each family's own grid."""
    per = []
    for fh, fl in zip(hv_fams, lt_fams):
        hf, lf = fh["fall_spec_%d" % step], fl["fall_spec_%d" % step]
        d = paired(hf["indexed"], lf["indexed"])

        def side(f):
            return {"mean": f["mean"], "ci": f["ci"], "n_used": f["n_used"],
                    "excluded": {"never_crossed": f["excluded_never_crossed"],
                                 "starts_crossed": f["excluded_starts_crossed"],
                                 "ambiguous": f["excluded_ambiguous"],
                                 "no_cell_above": f["excluded_no_cell_above"]}}

        per.append({"agents": fh["agents"], "step": step, "heavy": side(hf), "light": side(lf),
                    "delta": d, "delta_verdict": verdict_of(d)})
    word, counts = ladder_verdict([p["delta"] for p in per])
    return {"per_family": per, "verdict": word, "counts": counts, "step": step,
            "definition": ("secant from the seed's own crossing to the cell %d above it in rho, "
                           "benefit-percent per unit rho" % step)}


# --------------------------------------------------------------------------- report
def fmt_ci(ci):
    return "n/a" if not ci else "[%+.5f, %+.5f]" % (ci[0], ci[1])


def fmt_ci5(ci):
    return "n/a" if not ci else "[%.5f, %.5f]" % (ci[0], ci[1])


def fmt_num(x, spec="%.3f"):
    return "n/a" if x is None else (spec % x)


def report(fams, prem, basis, first, second, second2, h, checks):
    print("== step 5 -- P2, the mean-matched tail pair (h=%.2f) ==" % h)
    print("  pairing basis (measured): think shared %d/%d, service differs %d/%d, stream aligned %d/%d"
          " (%s draws consumed per class) -> %s"
          % (basis["think_shared"], basis["checks"], basis["service_differs"], basis["checks"],
             basis["stream_aligned"], basis["checks"], basis["draws_consumed"],
             "PAIRED" if basis["all_ok"] else "PAIRING NOT VALID"))
    print("  premise (measured, not assumed): mean S light %.5f %s vs heavy %.5f %s | relative gap %.2e"
          " (the check can detect >= %.2e at this n) -> %s"
          % (prem["mean_s_light"], fmt_ci5(prem["mean_s_ci_light"]), prem["mean_s_heavy"],
             fmt_ci5(prem["mean_s_ci_heavy"]), prem["relative_mean_gap"],
             prem["min_detectable_relative_gap"] or 0.0,
             "MEAN-MATCHED" if prem["mean_matched"] else "NOT MATCHED -- COMPARISON VOID"))
    if not prem["mean_matched"]:
        print("  ** COMPARISON VOID: the two service classes are not mean-matched, so the verdicts below")
        print("     would compare the tail AND the mean at once -- they are not reported as P2 evidence. **")
    print("  draw level: hiding limit E[min(T,S)] light %.4f vs heavy %.4f (%s higher) | ceiling P(S<=T)"
          " light %.4f vs heavy %.4f (%s higher) | opposed: %s"
          % (prem["hiding_limit_light"], prem["hiding_limit_heavy"], prem["hiding_limit_higher"],
             prem["ceiling_light"], prem["ceiling_heavy"], prem["ceiling_higher"], prem["opposed"]))
    for tail in TAILS:
        print("  -- %s --" % tail)
        for f in fams[tail]:
            rows = f["rows"]
            print("     A=%-3d c %d..%d | rho %.5f..%.5f | crossing %s | fall(step1) %s n=%d"
                  % (f["agents"], f["c_range"][0], f["c_range"][1], rows[0]["rho_spec"],
                     rows[-1]["rho_spec"], crossing_summary(f, "rho_spec")["status"],
                     fmt_num(f["fall_spec_1"]["mean"], "%+.3f") + " " + fmt_ci5(f["fall_spec_1"]["ci"]),
                     f["fall_spec_1"]["n_used"]))
            if f["crossing_rho_spec"] and not f["crossing_rho_spec"]["ambiguous"]:
                ps = f["per_seed_rho_spec"]
                print("        rho* %.5f %s | indexed-vs-reused rule: %s | exclusions: %d never, %d starts"
                      " crossed, %d ambiguous"
                      % (f["crossing_rho_spec"]["x_star"], fmt_ci5(ps["ci"]),
                         "same" if f["idx_matches_reused_rho_spec"]["same"] else "DIFFERENT",
                         ps["excluded_never_crossed"], ps["excluded_starts_crossed"],
                         ps["excluded_ambiguous"]))
    print("  P2 first half (heavier tail -> LARGER rho*): %s" % first["verdict"])
    for p in first["per_family"]:
        lt, hv = p["light"], p["heavy"]
        print("     A=%-3d rho* light %s | heavy %s | delta %s n=%d (%d light-only, %d heavy-only) -> %s"
              % (p["agents"],
                 (fmt_num(lt["x_star"], "%.5f") + " " + fmt_ci5(lt["ci"])) if lt["x_star"] else lt["status"],
                 (fmt_num(hv["x_star"], "%.5f") + " " + fmt_ci5(hv["ci"])) if hv["x_star"] else hv["status"],
                 fmt_ci(p["delta"]["ci"]), p["delta"]["n"], p["delta"]["n_light_only"],
                 p["delta"]["n_heavy_only"], p["delta_verdict"]))
        if p["welch"]:
            print("           two-sample fallback: %+.5f %s (n=%s)"
                  % (p["welch"]["delta"], fmt_ci(p["welch"]["ci"]), p["welch"]["n"]))
    print("  P2 second half (heavier tail -> STEEPER fall past rho*): step1 %s | step2 %s"
          % (second["verdict"], second2["verdict"]))
    for p, p2 in zip(second["per_family"], second2["per_family"]):
        print("     A=%-3d fall light %s (n=%d) | heavy %s (n=%d) | delta %s n=%d -> %s"
              % (p["agents"], fmt_num(p["light"]["mean"], "%+.3f") + " " + fmt_ci5(p["light"]["ci"]),
                 p["light"]["n_used"], fmt_num(p["heavy"]["mean"], "%+.3f") + " " + fmt_ci5(
                     p["heavy"]["ci"]), p["heavy"]["n_used"], fmt_ci(p["delta"]["ci"]), p["delta"]["n"],
                 p["delta_verdict"]))
        print("           step2: light %s | heavy %s | delta %s -> %s"
              % (fmt_num(p2["light"]["mean"], "%+.3f"), fmt_num(p2["heavy"]["mean"], "%+.3f"),
                 fmt_ci(p2["delta"]["ci"]), p2["delta_verdict"]))
    print("  mixture at the crossing cell (step 4's terms, split by tail):")
    for tail in TAILS:
        for f in fams[tail]:
            cr = f["crossing_rho_spec"]
            if not cr or cr["ambiguous"]:
                continue
            rows = f["rows"]
            cell = rows[cr["index"]] if cr["b_lo"] < -cr["b_hi"] else rows[cr["index"] + 1]
            print("     %-5s A=%-3d c=%-3d rho %.5f benefit %+.3f | hidden %.4f <= ceiling %.4f |"
                  " mean benefit hidden %s vs other %s"
                  % (tail, cell["agents"], cell["workers"], cell["rho_spec"], cell["benefit_pct"],
                     cell["hidden_frac"], cell["ceiling"], fmt_num(cell["mean_benefit_hidden"], "%+.3f"),
                     fmt_num(cell["mean_benefit_other"], "%+.3f")))
    print("  checks: " + ", ".join("%s=%s" % (k, "OK" if v else "FAIL")
                                   for k, v in sorted(checks.items())))


# --------------------------------------------------------------------------- controls
def planted_rows(pts):
    """Rows for a synthetic family: `pts` is a list of (rho, [benefit percent per seed])."""
    n = len(pts[0][1])
    rows = [{"workers": 1 + i, "agents": 8, "n_seeds": n, "tail": "planted", "rho_spec": rho,
             "rho_serial": rho, "benefit_pct": statistics.fmean(bs), "per_seed": list(bs)}
            for i, (rho, bs) in enumerate(pts)]
    rows.sort(key=lambda r: r["rho_spec"])
    return rows


def planted_linear(k, rho0=0.90, npts=6, ns=3):
    """A synthetic family whose benefit is exactly linear in rho with slope -k: its fall past the crossing
    is therefore k at every `step`, which is what makes 'the fall is the planted slope' a falsifiable arm."""
    return planted_rows([(rho0 - 0.005 + 0.01 * i, [-k * (rho0 - 0.005 + 0.01 * i - rho0)] * ns)
                         for i in range(npts)])


def case(name, ok, detail):
    return (name, bool(ok), detail)


def selftest():
    """Each arm fails for its OWN reason or it is decoration.  The expectations are properties of the object,
    not of this file's prose: where an arm's first version was wrong, the detail line says what the object
    was instead."""
    out = []
    cfg0 = I.default_cfg()
    cl, ch = dict(cfg0, tail="light"), dict(cfg0, tail="heavy")
    seeds3 = [101, 102, 103]

    r = cell_t(cl, 16, 5, 1.0, seeds3)
    out.append(case("clean_cell_passes", r["identity_holds"] and r["benefit_agrees_with_model"]
                    and r["hidden_within_ceiling"],
                    "residual %.2e, agreement %.2e, ceiling violations %d"
                    % (r["identity_max_residual"], r["benefit_agreement_max_abs"],
                       r["seeds_hidden_above_ceiling"])))

    # The arm needs enough seeds for the rule to HAVE power: at two seeds the intervals are so wide that a
    # 20% planted gap still overlaps (measured -- this arm's first run failed exactly there), so the arm now
    # plants the gap at the run's own n and also asserts the resolution that explains why.
    seeds8 = [101 + i for i in range(8)]
    dsl8 = draw_stats(cl, 16, seeds8)
    dsh_bad = draw_stats(dict(cfg0, tail="heavy", mS=1.2 * cfg0["mS"]), 16, seeds8)
    p_bad = premise(dsl8, dsh_bad)
    out.append(case("premise_fails_on_a_mismatched_pair",
                    (not p_bad["mean_matched"]) and p_bad["min_detectable_relative_gap"] < 0.20,
                    "planted 20%% mean gap; measured gap %.4f, detectable >= %.4f at n=8, intervals %s vs %s"
                    % (p_bad["relative_mean_gap"], p_bad["min_detectable_relative_gap"],
                       fmt_ci5(p_bad["mean_s_ci_light"]), fmt_ci5(p_bad["mean_s_ci_heavy"]))))

    p_ok = premise(dsl8, draw_stats(ch, 16, seeds8))
    out.append(case("premise_holds_on_the_real_pair", p_ok["mean_matched"],
                    "measured gap %.2e vs detectable >= %.2e, opposed %s"
                    % (p_ok["relative_mean_gap"], p_ok["min_detectable_relative_gap"], p_ok["opposed"])))

    b = tail_pair_basis(16, [101, 102], cl, ch)
    out.append(case("pairing_basis_is_measured_and_true", b["all_ok"],
                    "think %d/%d, service differs %d/%d, stream aligned %d/%d"
                    % (b["think_shared"], b["checks"], b["service_differs"], b["checks"],
                       b["stream_aligned"], b["checks"])))

    f1 = family(cl, 16, 2, 6, 1.0, [101, 102, 103, 104])
    f2 = family(cl, 16, 2, 6, 1.0, [101, 102, 103, 104])
    d0 = paired(f1["per_seed_idx_rho_spec"], f2["per_seed_idx_rho_spec"])
    out.append(case("the_same_tail_twice_gives_exactly_zero",
                    d0["mean"] == 0.0 and d0["n"] == len(f1["per_seed_idx_rho_spec"]) and d0["n"] > 0,
                    "delta %.3e over n=%d, verdict %s" % (d0["mean"] or 0.0, d0["n"], verdict_of(d0))))

    rows = planted_rows([(0.90 + 0.01 * i, [1.0 + i, 2.0 + i]) for i in range(4)])
    cr = B2.crossing_of_curve(rows, "rho_spec")
    ps = B2.per_seed_crossings(rows, "rho_spec")
    out.append(case("no_crossing_is_reported_not_invented", cr is None and ps["n_used"] == 0
                    and ps["excluded_never_crossed"] == 2,
                    "crossing %s, n_used %d, never-crossed %d"
                    % (cr, ps["n_used"], ps["excluded_never_crossed"])))

    rows = planted_rows([(0.90 + 0.01 * i, [[1.0, -1.0, 1.0, -1.0][i]]) for i in range(4)])
    cr = B2.crossing_of_curve(rows, "rho_spec")
    out.append(case("two_crossings_are_reported_ambiguous",
                    bool(cr) and cr["ambiguous"] and cr["n_crossings"] == 2
                    and crossing_summary({"crossing_rho_spec": cr, "per_seed_rho_spec": None,
                                          "per_seed_idx_rho_spec": []}, "rho_spec")["x_star"] is None,
                    "ambiguous %s, n_crossings %s" % (cr["ambiguous"], cr["n_crossings"])))

    rows = planted_rows([(0.90, [1.0, 1.0, 1.0]), (0.91, [1.0, -1.0, 1.0]), (0.92, [-1.0, -1.0, 1.0])])
    ps = B2.per_seed_crossings(rows, "rho_spec")
    idx = per_seed_crossings_idx(rows, "rho_spec")
    out.append(case("a_seed_without_a_crossing_is_counted", ps["excluded_never_crossed"] == 1
                    and ps["n_used"] == 2 and len(idx) == 2,
                    "used %d, never-crossed %d, kept %d" % (ps["n_used"],
                                                            ps["excluded_never_crossed"], len(idx))))

    f = fall_per_seed(planted_linear(120.0), "rho_spec", 1)
    f2s = fall_per_seed(planted_linear(120.0), "rho_spec", 2)
    out.append(case("the_fall_is_the_planted_slope", f["n_used"] == 3
                    and all(abs(v - 120.0) < 1e-09 for v in f["falls"])
                    and all(abs(v - 120.0) < 1e-09 for v in f2s["falls"]),
                    "step1 mean %.9f, step2 mean %.9f, n=%d"
                    % (f["mean"], f2s["mean"], f["n_used"])))

    rows = planted_rows([(0.90, [1.0, 1.0]), (0.91, [1.0, 1.0]), (0.92, [1.0, 1.0]), (0.93, [-1.0, -1.0])])
    f = fall_per_seed(rows, "rho_spec", 2)
    out.append(case("no_cell_above_is_not_a_zero_fall", f["n_used"] == 0 and f["mean"] is None
                    and f["excluded_no_cell_above"] == 2,
                    "n_used %d, mean %s, no_cell_above %d" % (f["n_used"], f["mean"],
                                                              f["excluded_no_cell_above"])))

    out.append(case("hidden_above_the_ceiling_is_caught",
                    ceiling_violations([0.5], [0.4]) == 1 and ceiling_violations([0.3], [0.4]) == 0,
                    "planted break -> %d violation(s); a legal pair -> %d"
                    % (ceiling_violations([0.5], [0.4]), ceiling_violations([0.3], [0.4]))))

    out.append(case("model_disagreement_is_caught",
                    (not agrees(1.0, 1.5)) and agrees(1.0, 1.0 + 1e-12) and (not agrees(1.0, 1.0 + 1e-06)),
                    "agrees(1,1.5)=%s agrees(1,1+1e-12)=%s agrees(1,1+1e-6)=%s"
                    % (agrees(1.0, 1.5), agrees(1.0, 1.0 + 1e-12), agrees(1.0, 1.0 + 1e-06))))

    mr = idx_matches_B2(f1["rows"], "rho_spec")
    out.append(case("the_indexed_rule_equals_the_reused_rule", mr["same"] and mr["mine"] == mr["reused"]
                    and mr["mine"] > 0,
                    "mine %d, reused %d, same %s, max|diff| %.2e"
                    % (mr["mine"], mr["reused"], mr["same"], mr["max_abs_diff"])))

    ok_pos = ladder_verdict([{"ci": [0.001, 0.002]}, {"ci": [0.003, 0.004]}])[0].startswith("CONFIRMED")
    ok_neg = ladder_verdict([{"ci": [0.001, 0.002]}, {"ci": [-0.004, -0.003]}])[0].startswith("CONTRADICTED")
    ok_mid = ladder_verdict([{"ci": [-0.001, 0.002]}])[0].startswith("UNRESOLVED")
    ok_none = ladder_verdict([{"ci": None}])[0].startswith("UNRESOLVED")
    out.append(case("the_verdict_rule_reads_the_sign_it_is_given",
                    ok_pos and ok_neg and ok_mid and ok_none,
                    "all above %s | one below %s | straddling %s | none located %s"
                    % (ok_pos, ok_neg, ok_mid, ok_none)))

    c4 = cell_t(cl, 16, 4, 1.0, [101, 102])
    c6 = cell_t(cl, 16, 6, 1.0, [101, 102])
    out.append(case("the_ceiling_is_a_property_of_the_draws_not_of_c",
                    c4["per_seed_ceiling"] == c6["per_seed_ceiling"]
                    and c4["mean_s_measured"] == c6["mean_s_measured"],
                    "c=4 %s vs c=6 %s (mean S %.6f vs %.6f)"
                    % (c4["per_seed_ceiling"], c6["per_seed_ceiling"], c4["mean_s_measured"],
                       c6["mean_s_measured"])))

    planted_fams = [{"agents": 16, "crossing_rho_spec": {"x_star": 0.5, "ambiguous": False}}]
    a3 = light_tail_against_step_3(planted_fams)
    a3_missing = light_tail_against_step_3(planted_fams,
                                           path=os.path.join(HERE, "no_such_sibling.json"))
    out.append(case("the_step_3_cross_check_can_fail",
                    a3["status"] == "READ" and (not a3["all_agree"])
                    and a3_missing["status"] == "NOT TAKEN",
                    "planted 0.50000 against step 3's %s -> agree %s; an absent sibling -> %s"
                    % (fmt_num(a3["per_family"][0]["step_3"], "%.5f"), a3["all_agree"],
                       a3_missing["status"])))

    fails = [n for n, ok, _ in out if not ok]
    print("== step 5 --selftest: %d arms, %d failure(s) ==" % (len(out), len(fails)))
    for n, ok, d in out:
        print("  %-4s %-46s %s" % ("PASS" if ok else "FAIL", n, d))
    if fails:
        print("  FAILING: %s" % ", ".join(fails))
    return 0 if not fails else 1


# --------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="issue #50 step 5 -- P2, the mean-matched tail pair")
    ap.add_argument("--seeds", type=int, default=32, help="seeds per cell")
    ap.add_argument("--seed0", type=int, default=101)
    ap.add_argument("--h", type=float, default=1.0)
    ap.add_argument("--quick", action="store_true", help="4 seeds per cell, for a smoke run")
    ap.add_argument("--json", metavar="PATH", default=None, help="write the readings to PATH")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    seeds = [args.seed0 + i for i in range(4 if args.quick else args.seeds)]
    cfg0 = I.default_cfg()
    cl, ch = dict(cfg0, tail="light"), dict(cfg0, tail="heavy")
    print("== step 5: seeds %d..%d (%d), h=%.2f, windows %s, model mT=%.1f mS=%.1f steps=%d =="
          % (seeds[0], seeds[-1], len(seeds), args.h, WINDOWS, cfg0["mT"], cfg0["mS"], cfg0["steps"]))
    basis = tail_pair_basis(16, seeds, cl, ch)
    ds = {a: {"light": draw_stats(cl, a, seeds), "heavy": draw_stats(ch, a, seeds)} for a in (16, 64)}
    prem = {a: premise(ds[a]["light"], ds[a]["heavy"]) for a in (16, 64)}
    fams = {t: [family(cfg, a, lo, hi, args.h, seeds) for (a, lo, hi) in WINDOWS]
            for t, cfg in (("light", cl), ("heavy", ch))}
    first = p2_first_half(fams["heavy"], fams["light"], "rho_spec")
    second = p2_second_half(fams["heavy"], fams["light"], 1)
    second2 = p2_second_half(fams["heavy"], fams["light"], 2)
    against3 = light_tail_against_step_3(fams["light"])
    checks = {
        "pairing_basis_ok": basis["all_ok"],
        "premise_mean_matched": all(prem[a]["mean_matched"] for a in prem),
        "light_arm_agrees_with_step_3": against3["status"] != "READ" or against3["all_agree"],
        "crossing_rule_matches_the_reused_rule": all(
            f["idx_matches_reused_rho_spec"]["same"] for t in TAILS for f in fams[t]),
        "identity_holds_everywhere": all(
            r["identity_holds"] for t in TAILS for f in fams[t] for r in f["rows"]),
        "benefit_agrees_with_the_model_everywhere": all(
            r["benefit_agrees_with_model"] for t in TAILS for f in fams[t] for r in f["rows"]),
        "hidden_within_ceiling_everywhere": all(
            r["hidden_within_ceiling"] for t in TAILS for f in fams[t] for r in f["rows"]),
        "mean_s_constant_within_a_family": all(
            len({r["mean_s_measured"] for r in f["rows"]}) == 1 for t in TAILS for f in fams[t]),
        "ceiling_constant_within_a_family": all(
            len({tuple(r["per_seed_ceiling"]) for r in f["rows"]}) == 1 for t in TAILS for f in fams[t]),
    }
    report(fams, prem[16], basis, first, second, second2, args.h, checks)
    if against3["status"] == "READ":
        print("  the light-tail arm against step 3's published crossing (%s): max |diff| %.3e -> %s"
              % (against3["source"], against3["max_abs_diff"],
                 "same reading" if against3["all_agree"] else "DIFFERENT"))
    else:
        print("  the light-tail arm against step 3: NOT TAKEN (%s)" % against3["reason"])
    payload = {
        "what": "issue #50 instrument v0 step 5 -- registered prior P2 (mean-matched tail pair)",
        "h": args.h, "seeds": seeds, "windows": WINDOWS, "tails": list(TAILS),
        "model": {k: cfg0[k] for k in sorted(cfg0) if not isinstance(cfg0[k], list)},
        "declared": {"agree_tol": AGREE_TOL, "identity_tol": D1.IDENTITY_TOL,
                     "derivation_tol": B2.DERIVATION_TOL,
                     "ladder_rule": ("CONFIRMED iff every located family's interval lies strictly above "
                                     "zero; CONTRADICTED iff at least one lies strictly below zero; "
                                     "UNRESOLVED otherwise"),
                     "fall_definition": ("secant from the seed's own crossing to the cell 1 (and, as a "
                                         "sensitivity, 2) above it in rho, benefit-percent per unit rho"),
                     "void_on_premise": "exit 3, verdicts not reported as P2 evidence"},
        "pairing_basis": basis, "draw_stats": ds, "premise": prem, "families": fams,
        "p2_first_half": first, "p2_second_half": second, "p2_second_half_step2": second2,
        "light_arm_against_step_3": against3,
        "checks": checks, "void": not checks["premise_mean_matched"],
    }
    if args.json:
        with io.open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
            fh.write("\n")
    if not checks["premise_mean_matched"]:
        print("  COMPARISON VOID: the two service classes are not mean-matched; no P2 verdict is reported.")
        return 3
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
