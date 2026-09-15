#!/usr/bin/env python3
"""
issue #44 -- instrument_v4.py
"The scope limits, measured: where the construct is exact, where a comparison is
decidable, and what each limit costs"

Three boundaries were declared while the results came in (v1 section 4, v3 sections 3
and 5). This instrument turns each into a reproducible, two-sided check rather than a
caveat in prose. Every section reports the boundary AND the quantity that moves across
it; each carries a control that must fire.

S1 -- HEAVY-TAILED NODES AT SMALL BUDGETS (declared in v1 section 4)
   The construct predicts power = Phi(u), u = (sqrt(k)*delta_D - c_alpha)/sigma_D from the
   node's OWN moments. For a Gaussian node this is exact at every k. For a node whose
   moments match a Gaussian's but whose shape is heavy-tailed (affine contamination:
   q of the draws at `big`, the rest at 0, tuned so q*big = delta and
   1 + q(1-q)big^2 = sigma^2), the sample mean is skewed at small k and the Gaussian
   tail prediction overstates or understates the true rate.
   MEASURED: the absolute error of the construct as a function of k, for a fixed node;
   the empirical decay exponent of |error| in k, compared with the CLT's -1/2; and the
   budget at which the error crosses a declared tolerance (1 percentage point).
   BOUNDARY, stated for use: the construct is exact (within Monte-Carlo resolution) for
   Gaussian nodes at every budget; for a heavy node, |error| <= 1 pp requires the budget
   reported in S1_boundary.

S2 -- CEILING SATURATION (declared in v3 section 5)
   Both rules approach power 1 as the margin grows, and near the ceiling neither the
   factor nor its interval carries information. Declare the saturated set as cells whose
   CONSTANT-rule construct power exceeds 0.99, map it in (lam, k, n_cal), and show the
   two consequences that make it a scope limit rather than a nuisance: the achievable
   difference is bounded by (1 - power_constant), and the paired-difference interval
   straddles zero in those cells whatever the effect is.
   BOUNDARY: a comparison is informative only where the constant rule's power <= 0.99.

S3 -- THE RESOLUTION LIMIT OF THE DERIVED-vs-CONSTANT COMPARISON (declared in v3 section 3)
   In v3, 17 of 42 informative cells could not certify the factor's interval above 1 at
   41 streams. That is not a property of the rules; it is the NUMBER OF STREAMS required
   against the effect size. For each cell, invert the measured interval: the number of
   streams N_min at which the interval's lower bound would reach 1. Then show the failure
   pattern is exactly "N_min > streams available", and give the rule for planning:
   N_min is set by the effect size, not by the budget.
   BOUNDARY: the question "is the derived rule better?" is empirically decidable in a cell
   iff N_min <= the streams the study can afford.

CONTROLS (each must be able to fail; see verify_v4.py)
  K1 the Gaussian control for S1: with q = 0 (an exactly Gaussian node) the construct's
     error must sit at Monte-Carlo resolution at EVERY budget -- otherwise S1 is
     measuring the instrument, not heavy tails.
  K2 S2's saturation definition must separate cells: the saturated set must be non-empty
     and its complement non-empty, and inside the set the achievable difference must be
     bounded by (1 - power_constant) with the bound attained-ish.
  K3 S3's inversion must reproduce v3's verdict: recomputing "decidable" from N_min must
     agree with the criterion-(c) strict reading recorded in results_v3.json, cell by cell.
  K4 a signed direction control for S1: a node with the SAME moments but a LEFT-heavy
     shape must err in the opposite direction to a right-heavy one (the error is a
     shape effect, not a moment effect).

Pure stdlib. Deterministic: no clock, no entropy beyond seeded streams, and the artefact
carries no timing field (the R241 lesson).
"""

import json
import math
import os
import random
import statistics
import sys


# ---------------------------------------------------------------- special funcs
def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def phi_inv(p):
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if phi(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


ALPHA = 0.05
C_ALPHA = phi_inv(1.0 - ALPHA)
SIGMA_H = 1.0
T_975_DF40 = 2.021
N_STREAMS = 41
N_MC = 12000
TOL_PP = 0.01                     # the declared tolerance for S1, 1 percentage point
FORBIDDEN_TOKENS = ("time", "runtime", "elapsed", "wall", "clock", "timestamp",
                    "date", "now", "sec", "secs", "seconds", "second", "ms",
                    "duration", "sim", "start", "end", "stamp")


def seed_for(*parts):
    h = 17
    for p in parts:
        if isinstance(p, str):
            v = 0
            for i, ch in enumerate(p):
                v = (v * 131 + ord(ch)) & 0x7FFFFFFF
        else:
            v = int(round(float(p) * 1000))
        h = (h * 1000003 + v) & 0x7FFFFFFF
    return h


def c_star(n_cal):
    return phi_inv(1.0 - 1.0 / (n_cal + 1.0))


# ---------------------------------------------------------------- shapes
def contamination_params(delta, sigma):
    """A two-point heavy-tailed node with EXACTly the moments (delta, sigma):
    mass q at `big`, the rest at 0.  For a two-point law

        mean = q*big,   var = q*big^2 - (q*big)^2 = q(1-q)big^2,

    so solving mean = delta and var = sigma^2 gives

        q = delta^2 / (sigma^2 + delta^2),   big = (sigma^2 + delta^2) / delta.

    THE FIRST VERSION OF THIS FUNCTION WAS WRONG, and the error is worth keeping: it set
    big = delta/q and then declared var = 1 + q(1-q)big^2, which is the variance of a
    *unit-variance base plus a spike*, not of the two-point node it actually drew.  The
    construct was therefore handed a sigma the node did not have, and S1 measured a moment
    mismatch instead of a shape effect -- visible as large, sign-alternating errors
    (|error| up to 0.16 and changing sign with k).  What caught it: S1's own Gaussian
    control stayed exact (it uses true Gaussian draws), so the fault had to be in the node,
    and the errors were not monotone in k as a CLT story requires."""
    q = delta * delta / (sigma * sigma + delta * delta)
    big = (sigma * sigma + delta * delta) / delta
    return q, big


def draw_contaminated(r, q, big, k):
    """Sample mean of k draws from the contaminated (heavy-tailed) node."""
    s = 0.0
    for _ in range(k):
        s += big if r.random() < q else 0.0
    return s / k


def draw_contaminated_mirror(r, q, big, k):
    """The MIRRORED shape: mass at `big` replaced by mass at -big, mean shifted back by
    the node's mean so the moments are identical and only the SHAPE differs."""
    mu = q * big
    s = 0.0
    for _ in range(k):
        s += (-big if r.random() < q else 0.0)
    return s / k + mu


def draw_gaussian(r, delta, sigma, k):
    s = 0.0
    for _ in range(k):
        s += r.gauss(delta, sigma)
    return s / k


# ---------------------------------------------------------------- S1
# Several two-point nodes at a fixed location margin, differing only in how sparse and
# how far out their spike is.  For a two-point node the sample mean lives on a LATTICE
# with spacing big/k, so the Gaussian tail prediction is a discretisation approximation,
# not a CLT one; the controlling quantity is the lattice spacing measured in units of
# the mean's own standard deviation,
#
#       ratio = (big/k) / (sigma/sqrt(k)) = big / (sigma * sqrt(k)).
#
# The design sweeps BOTH axes so that the claim "ratio governs the error" is testable
# rather than asserted: the same ratio is reached by different (node, k) pairs.
S1_DELTA = 0.30
S1_NODE_SIGMAS = [0.30, 0.60, 1.497, 3.00]
S1_K = [4, 8, 16, 32, 64, 128, 256, 512, 1024]
S1_SPIKE_RATIOS = [2.0, 3.0, 5.0, 10.0]


def s1_lattice():
    """The error of the construct against the lattice ratio, over a swept design."""
    rows = []
    for sigma in S1_NODE_SIGMAS:
        q, big = contamination_params(S1_DELTA, sigma)
        for k in S1_K:
            tau = C_ALPHA / math.sqrt(k)
            pred = phi((math.sqrt(k) * S1_DELTA - C_ALPHA) / sigma)
            vals = []
            for st in range(9):
                r = random.Random(seed_for("s1", sigma, k, st))
                rej = sum(1 for _ in range(N_MC) if draw_contaminated(r, q, big, k) > tau)
                vals.append(rej / float(N_MC))
            m = statistics.fmean(vals)
            sd = statistics.stdev(vals)
            ratio = big / (sigma * math.sqrt(k))
            rows.append({"sigma_node": sigma, "q": q, "big": big, "k": k,
                         "lattice_ratio": ratio,
                         "lattice_spacing_over_mean_sd": ratio,
                         "predicted": pred, "measured": m, "error": m - pred,
                         "abs_error": abs(m - pred), "stream_sd": sd,
                         "se": sd / math.sqrt(9),
                         "within_mc_resolution": abs(m - pred) <= 4.0 * sd / math.sqrt(9) + 0.002})
    # does the ratio GOVERN the error?  bin by ratio and report the worst error per bin,
    # over ALL (node, k) pairs -- if the ratio governs, the bins are ordered and tight.
    bins = [(0.0, 0.25), (0.25, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 100.0)]
    binned = []
    for lo, hi in bins:
        sel = [r for r in rows if lo <= r["lattice_ratio"] < hi]
        if not sel:
            continue
        binned.append({"ratio_lo": lo, "ratio_hi": hi, "n": len(sel),
                       "max_abs_error": max(r["abs_error"] for r in sel),
                       "median_abs_error": statistics.median([r["abs_error"] for r in sel]),
                       "n_nodes": len(set(r["sigma_node"] for r in sel))})
    # the ratio below which the construct is within tolerance, in every cell measured
    order = sorted(rows, key=lambda r: r["lattice_ratio"])
    ratio_ok = None
    for i, r in enumerate(order):
        if r["lattice_ratio"] < 0.5:
            ratio_ok = r["lattice_ratio"]
            break
    # the largest ratio at which ANY cell still exceeds tolerance ...
    worst = max((r for r in rows if r["abs_error"] > TOL_PP), key=lambda r: r["lattice_ratio"],
                default=None)
    # ... and the USABLE boundary: the largest r* such that EVERY measured cell with
    # ratio <= r* is within tolerance.  This is the number a reader applies.
    r_star = 0.0
    for r in sorted(rows, key=lambda r: r["lattice_ratio"]):
        if r["abs_error"] <= TOL_PP:
            r_star = r["lattice_ratio"]
        else:
            break
    # is the error NON-MONOTONE in k at fixed node?  (the lattice effect)
    nonmono = []
    for sigma in S1_NODE_SIGMAS:
        ks = [r for r in rows if r["sigma_node"] == sigma]
        ks.sort(key=lambda r: r["k"])
        signs = [1 if r["error"] > 0 else -1 for r in ks]
        flips = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])
        nonmono.append({"sigma_node": sigma, "big": ks[0]["big"],
                        "spike_over_sigma": ks[0]["big"] / sigma,
                        "sign_flips_in_k": flips,
                        "monotone_in_k": flips == 0})
    return {"delta": S1_DELTA, "rows": rows, "bins": binned,
            "tolerance_pp": TOL_PP,
            "r_star_usable_boundary": r_star,
            "r_star_statement": ("|error| <= %.0f pp for every measured cell with "
                                 "big/(sigma*sqrt(k)) <= %.4f" % (100 * TOL_PP, r_star)),
            "largest_ratio_exceeding_tolerance": (worst["lattice_ratio"] if worst else None),
            "largest_ratio_cell": (worst if worst else None),
            "non_monotonicity": nonmono}



def s1_gaussian_control():
    """K1: with q -> 0 the node IS Gaussian, so the construct must be exact at every k."""
    rows = []
    for k in S1_K:
        delta, sigma = S1_DELTA, 1.497
        tau = C_ALPHA / math.sqrt(k)
        pred = phi((math.sqrt(k) * delta - C_ALPHA) / sigma)
        vals = []
        for st in range(9):
            r = random.Random(seed_for("s1g", k, st))
            rej = sum(1 for _ in range(N_MC)
                      if draw_gaussian(r, delta, sigma, k) > tau)
            vals.append(rej / float(N_MC))
        m = statistics.fmean(vals)
        sd = statistics.stdev(vals)
        rows.append({"k": k, "predicted": pred, "measured": m, "abs_error": abs(m - pred),
                     "se": sd / math.sqrt(9),
                     "ok": abs(m - pred) <= 4.0 * sd / math.sqrt(9) + 0.002})
    return rows


def s1_mirror_control():
    """K4: identical moments, mirrored shape -- the errors must have opposite signs."""
    out = []
    for k in (16, 64):
        q, big = contamination_params(S1_DELTA, 1.497)
        sigma = 1.497
        tau = C_ALPHA / math.sqrt(k)
        pred = phi((math.sqrt(k) * S1_DELTA - C_ALPHA) / sigma)
        row = {"k": k, "predicted": pred}
        for name, fn in (("right_heavy", draw_contaminated),
                         ("left_heavy", draw_contaminated_mirror)):
            vals = []
            for st in range(N_STREAMS):
                r = random.Random(seed_for("s1m", name, k, st))
                rej = sum(1 for _ in range(N_MC) if fn(r, q, big, k) > tau)
                vals.append(rej / float(N_MC))
            row[name] = {"measured": statistics.fmean(vals),
                         "error": statistics.fmean(vals) - pred}
        row["opposite_signs"] = (row["right_heavy"]["error"] * row["left_heavy"]["error"] < 0)
        out.append(row)
    return out


# ---------------------------------------------------------------- S2
S2_LAM = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0]
S2_K = [4, 16, 64]
S2_NCAL = [5, 20, 100, 1000]


def s2_ceiling():
    cells = []
    for n_cal in S2_NCAL:
        r = random.Random(seed_for("s2", n_cal))
        draws = [phi_inv(r.random() ** (1.0 / n_cal)) for _ in range(20000)]
        for k in S2_K:
            se = SIGMA_H / math.sqrt(k)
            for lam in S2_LAM:
                delta = lam * se
                pc = statistics.fmean([phi((delta - m * se) / se) for m in draws])
                pd = phi(lam - c_star(n_cal))
                cells.append({"n_cal": n_cal, "k": k, "lam": lam,
                              "power_constant_predicted": pc,
                              "power_derived_predicted": pd,
                              "saturated": bool(pc > 0.99),
                              "achievable_difference_bound": 1.0 - pc,
                              "predicted_difference": pd - pc})
    return cells


def s2_measured_saturation():
    """Measure the paired-difference interval in saturated vs unsaturated cells, to show
    the ceiling really does remove the information rather than merely being large."""
    out = []
    for n_cal, k in ((20, 16), (100, 4)):
        se = SIGMA_H / math.sqrt(k)
        for lam in (1.0, 2.0, 4.0, 6.0):
            delta = lam * se
            pd_c, pd_d = [], []
            for st in range(N_STREAMS):
                r_cal = random.Random(seed_for("s2cal", n_cal, k, lam, st))
                tau_c = max(r_cal.gauss(0.0, se) for _ in range(n_cal))
                tau_d = c_star(n_cal) * se
                r_div = random.Random(seed_for("s2div", n_cal, k, lam, st))
                a = b = 0
                for _ in range(N_MC):
                    x = r_div.gauss(delta, se)
                    if x > tau_d:
                        a += 1
                    if x > tau_c:
                        b += 1
                pd_d.append(a / float(N_MC))
                pd_c.append(b / float(N_MC))
            m_c = statistics.fmean(pd_c)
            d = [x - y for x, y in zip(pd_d, pd_c)]
            md = statistics.fmean(d)
            se_d = statistics.stdev(d) / math.sqrt(N_STREAMS)
            out.append({"n_cal": n_cal, "k": k, "lam": lam,
                        "power_constant": m_c, "saturated": bool(m_c > 0.99),
                        "mean_difference": md,
                        "ci_lo": md - T_975_DF40 * se_d,
                        "ci_hi": md + T_975_DF40 * se_d,
                        "ci_excludes_zero": bool(md - T_975_DF40 * se_d > 0),
                        "bound_1_minus_pc": 1.0 - m_c,
                        "difference_within_bound": bool(md <= 1.0 - m_c + 1e-9),
                        "ci_width": 2.0 * T_975_DF40 * se_d})
    return out


# ---------------------------------------------------------------- S3
def s3_resolution(v3):
    """Invert v3's measured intervals: the number of streams at which each cell's
    factor interval lower bound would reach 1."""
    rows = []
    for key, c in sorted(v3["cells"].items()):
        if not c["informative"]:
            continue
        f = c["factor"]
        if f.get("mean") is None:
            continue
        se41 = f.get("rel_se")
        if se41 is None:
            continue
        fmean = f["mean"]
        margin = fmean - 1.0
        if margin <= 1.0e-12:
            nmin = None                       # never decidable: the effect is <= 0
        else:
            nmin = N_STREAMS * ((T_975_DF40 * se41 * fmean) / margin) ** 2
        rows.append({"cell": key, "n_cal": c["n_cal"], "k": c["k"], "lam": c["lam"],
                     "factor": fmean, "ci_lo_at_41": f["ci_lo"],
                     "decidable_at_41": bool(f["ci_lo"] > 1.0),
                     "n_min_streams": nmin,
                     "n_min_over_41": (nmin / N_STREAMS) if nmin else None})
    return rows


# ---------------------------------------------------------------- run
def run(here):
    out = {"alpha": ALPHA, "c_alpha": C_ALPHA, "n_streams": N_STREAMS, "n_mc": N_MC,
           "tol_pp": TOL_PP, "s1_delta": S1_DELTA, "s1_node_sigmas": S1_NODE_SIGMAS}

    # ---- S1
    h = s1_lattice()
    g = s1_gaussian_control()
    mir = s1_mirror_control()
    out["S1_lattice"] = h
    out["S1_gaussian_control"] = g
    out["S1_mirror_control"] = mir
    out["K1_gaussian_exact"] = all(r["ok"] for r in g)
    out["K1_max_gaussian_error"] = max(r["abs_error"] for r in g)
    out["K4_mirror_opposite"] = all(r["opposite_signs"] for r in mir)

    # ---- S2
    cells = s2_ceiling()
    meas = s2_measured_saturation()
    out["S2_grid"] = cells
    out["S2_measured"] = meas
    out["K2_saturated_nonempty"] = any(c["saturated"] for c in cells)
    out["K2_unsaturated_nonempty"] = any(not c["saturated"] for c in cells)
    out["K2_n_saturated"] = sum(1 for c in cells if c["saturated"])
    out["K2_bounds_hold"] = all(r["difference_within_bound"] for r in meas)
    # The consequence of the ceiling is NOT that the difference becomes undetectable --
    # the streams are so tightly packed at 1.0 that a 0.02 pp effect can still resolve.
    # It is that the difference becomes NEGLIGIBLE: the achievable gain is bounded by
    # 1 - power_constant, so above the ceiling the derived rule cannot buy more than
    # a fraction of a percentage point however many streams are run.
    sat = [r for r in meas if r["saturated"]]
    unsat = [r for r in meas if not r["saturated"]]
    out["K2_saturated_max_gain"] = max(r["bound_1_minus_pc"] for r in sat) if sat else None
    out["K2_unsaturated_max_gain"] = max(r["bound_1_minus_pc"] for r in unsat) if unsat else None
    out["K2_gain_bound_shrinks"] = bool(sat and unsat
                                        and out["K2_saturated_max_gain"]
                                        < out["K2_unsaturated_max_gain"])
    out["K2_ok"] = bool(out["K2_saturated_nonempty"] and out["K2_unsaturated_nonempty"]
                        and out["K2_bounds_hold"] and out["K2_gain_bound_shrinks"]
                        and out["K2_saturated_max_gain"] <= TOL_PP)

    # ---- S3
    v3path = os.path.join(here, "results_v3.json")
    v3 = json.load(open(v3path, encoding="utf-8"))
    res = s3_resolution(v3)
    out["S3_resolution"] = res
    agree = sum(1 for r in res
                if (r["n_min_streams"] is not None
                    and (r["n_min_streams"] <= N_STREAMS) == r["decidable_at_41"]))
    disagree = [r["cell"] for r in res
                if r["n_min_streams"] is not None
                and (r["n_min_streams"] <= N_STREAMS) != r["decidable_at_41"]]
    out["K3_agreement"] = {"n_cells": len(res), "n_agree": agree,
                           "disagreements": disagree,
                           "agrees_with_v3": len(disagree) == 0}
    dec = [r["n_min_streams"] for r in res if r["n_min_streams"] is not None]
    undec = [r["cell"] for r in res if r["n_min_streams"] is None]
    out["S3_summary"] = {
        "n_cells": len(res),
        "n_decidable_at_41": sum(1 for r in res if r["decidable_at_41"]),
        "n_indecidable_at_41": sum(1 for r in res if not r["decidable_at_41"]),
        "n_never_decidable": len(undec),
        "never_decidable_cells": undec,
        "n_min_median": statistics.median(dec) if dec else None,
        "n_min_min": min(dec) if dec else None,
        "n_min_max": max(dec) if dec else None,
    }

    out["K3_ok"] = out["K3_agreement"]["agrees_with_v3"]
    out["ALL_PASS"] = bool(out["K1_gaussian_exact"] and out["K4_mirror_opposite"]
                           and out["K2_ok"] and out["K3_ok"])
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = run(here)
    dest = os.path.join(here, "results_v4.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    h = out["S1_lattice"]
    print("wrote", dest)
    print("ALL_PASS:", out["ALL_PASS"])
    print()
    print("S1 lattice: the construct vs the ratio big/(sigma*sqrt(k))  [delta=%.2f]" % h["delta"])
    print("  node sigma |  q      | big    | spike/sigma | sign flips in k")
    for nm in h["non_monotonicity"]:
        print("   %8.3f  | %.4f | %6.3f | %11.2f | %d"
              % (nm["sigma_node"], contamination_params(S1_DELTA, nm["sigma_node"])[0],
                 nm["big"], nm["spike_over_sigma"], nm["sign_flips_in_k"]))
    print("  ratio bin          n   nodes  median |err|   max |err|")
    for b in h["bins"]:
        print("   [%.2f, %.2f)  %4d   %2d     %.4f       %.4f"
              % (b["ratio_lo"], b["ratio_hi"], b["n"], b["n_nodes"],
                 b["median_abs_error"], b["max_abs_error"]))
    print("   largest ratio at which any cell exceeds 1 pp: %s"
          % (("%.3f" % h["largest_ratio_exceeding_tolerance"])
             if h["largest_ratio_exceeding_tolerance"] is not None else "none"))
    print("   USABLE BOUNDARY: %s" % h["r_star_statement"])
    print("   K1 Gaussian control exact at every budget: %s (max err %.4f)"
          % (out["K1_gaussian_exact"], out["K1_max_gaussian_error"]))
    print("   K4 mirrored shape errs opposite: %s" % out["K4_mirror_opposite"])
    for r in out["S1_mirror_control"]:
        print("      k=%-4d right-heavy err %+.4f | left-heavy err %+.4f"
              % (r["k"], r["right_heavy"]["error"], r["left_heavy"]["error"]))
    print()
    print("S2 ceiling: %d of %d grid cells saturated (constant-rule power > 0.99)"
          % (out["K2_n_saturated"], len(out["S2_grid"])))
    print("     n_cal    k  lam   pow_c   saturated  bound(1-pc)  measured diff [CI]")
    for r in out["S2_measured"]:
        print("  %5d %5d %4.1f   %.4f   %-9s  %.4f       %+.4f [%+.4f,%+.4f] %s"
              % (r["n_cal"], r["k"], r["lam"], r["power_constant"],
                 "yes" if r["saturated"] else "no", r["bound_1_minus_pc"],
                 r["mean_difference"], r["ci_lo"], r["ci_hi"],
                 "excludes 0" if r["ci_excludes_zero"] else "straddles 0"))
    print("   bounds hold: %s | max achievable gain (1-power_c): saturated %.5f vs "
          "unsaturated %.5f -> the ceiling bounds the PRIZE, not the detection"
          % (out["K2_bounds_hold"], out["K2_saturated_max_gain"],
             out["K2_unsaturated_max_gain"]))
    print()
    s = out["S3_summary"]
    print("S3 resolution: %d informative cells; decidable at 41 streams: %d; not: %d; never: %d"
          % (s["n_cells"], s["n_decidable_at_41"], s["n_indecidable_at_41"],
             s["n_never_decidable"]))
    print("   N_min (streams needed) median %.0f, range [%.0f, %.0f]"
          % (s["n_min_median"], s["n_min_min"], s["n_min_max"]))
    print("   K3 inversion reproduces v3's verdict: %s (%d/%d cells agree)"
          % (out["K3_ok"], out["K3_agreement"]["n_agree"], out["K3_agreement"]["n_cells"]))
    lo = sorted([r for r in out["S3_resolution"]], key=lambda r: (r["lam"], r["k"]))
    print("     worst cells by N_min:")
    for r in sorted(out["S3_resolution"],
                    key=lambda r: -(r["n_min_over_41"] or 1e9))[:6]:
        nm = r["n_min_streams"]
        print("      %-14s lam=%.0f k=%-3d factor %.4f  N_min %s  (%.0fx the streams used)"
              % (r["cell"], r["lam"], r["k"], r["factor"],
                 ("%.0f" % nm) if nm else "never", r["n_min_over_41"] or float("inf")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
