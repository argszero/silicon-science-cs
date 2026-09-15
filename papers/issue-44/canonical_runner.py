#!/usr/bin/env python3
"""Issue #44 -- canonical runner.

Runs the five stage instruments in the order the claims require (v4 reads the
v3 artefact, so the order is not optional), then recomputes every registered
criterion and every sensitivity statement **from the primitives recorded in the
stage artefacts**, and cross-checks the recomputation against the flags the
stages recorded about themselves.

That cross-check is the point of this file.  A flag a stage records about its
own output cannot be attacked by changing the output; the recomputation can.
Where the two disagree, the runner exits non-zero.

Writes `canonical_results.json` and `run.log` beside itself.  Neither contains
a wall-clock, a host name, or an absolute path, so `bash reproduce.sh` is
byte-identical on every machine and every run.

Usage:  python3 canonical_runner.py
"""

import hashlib
import io
import json
import math
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAP_TOL = 0.05  # two cells' mean threshold gaps are compared only if they differ by more

# tag, script, artefact, what the stage is for
STAGES = (
    ("v0", "instrument_v0.py", "results_v0.json",
     "controls only: closed-form versus Monte-Carlo agreement, the mean/var "
     "discrimination, the null and the needle -- no claim is made from v0"),
    ("v1", "instrument_v1.py", "results_v1.json",
     "criterion (a): out-of-sample prediction error, invariance, and the "
     "calibration cell anchored to the antecedent's measured rates"),
    ("v2", "instrument_v2.py", "results_v2.json",
     "criterion (b): the insensitivity band, its boundary and its width law"),
    ("v3", "instrument_v3.py", "results_v3.json",
     "criterion (c): the derived per-execution rule versus the best constant "
     "threshold matched to zero honest rejections"),
    ("v4", "instrument_v4.py", "results_v4.json",
     "sensitivity: the lattice boundary of the construct, what the ceiling "
     "bounds, and where the comparison is decidable"),
)


# ---------------------------------------------------------------- helpers ---

def sha256_file(path):
    with io.open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def binom_sf(k, n):
    """P(X >= k) for X ~ Binomial(n, 1/2), exact rational arithmetic."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(math.comb(n, i) for i in range(k, n + 1)) / (2.0 ** n)


def agree(a, b):
    """Two recorded numbers agree (exactly, or with the delta reported)."""
    if a == b:
        return True, 0.0
    try:
        return False, a - b
    except TypeError:
        return False, None


class Checks(object):
    """Every check is recorded, and every failure is reported with its values."""

    def __init__(self):
        self.rows = []
        self.failed = 0

    def ok(self, name, condition, detail=""):
        self.rows.append((bool(condition), name, detail))
        if not condition:
            self.failed += 1
        return bool(condition)

    def same(self, name, recomputed, recorded):
        same, delta = agree(recomputed, recorded)
        return self.ok(name, same,
                       "" if same else "recomputed %r vs recorded %r (delta %r)"
                       % (recomputed, recorded, delta))


# ------------------------------------------------------- the five stages ---

def run_stages():
    """Run every stage in order; return (log lines, per-stage entries)."""
    log = ["# canonical runner -- issue #44",
           "# the stage order is load-bearing: instrument_v4.py reads the v3 artefact",
           ""]
    entries = []
    for tag, script, artefact, purpose in STAGES:
        proc = subprocess.run([sys.executable, script], cwd=HERE,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True)
        # scrub this machine's directory out of the transcript: the log must be
        # byte-identical on another machine, and an absolute path is not
        text = proc.stdout.replace(HERE + os.sep, "").replace(HERE, ".")
        log.append("## stage %s -- %s (exit %d)" % (tag, script, proc.returncode))
        log.append("   purpose: %s" % purpose)
        log.append(text.rstrip())
        log.append("")
        entries.append({
            "tag": tag, "script": script, "purpose": purpose,
            "exit_code": proc.returncode,
            "script_sha256": sha256_file(os.path.join(HERE, script)),
            "artefact": artefact,
            "artefact_sha256": sha256_file(os.path.join(HERE, artefact)),
        })
    return log, entries


# ------------------------------------------------------- the criteria ------

def criterion_a(v1, ck):
    A = v1["A_out_of_sample"]
    errs = sorted(abs(c["abs_error"]) for c in A["cells"])
    n = len(errs)
    med = statistics.median(errs)
    mean = sum(errs) / n
    mx = max(errs)
    limit = 0.10
    ck.same("a/n_cells", n, A["n_cells"])
    ck.same("a/median_abs_error", med, A["median_abs_error"])
    ck.same("a/mean_abs_error", mean, A["mean_abs_error"])
    ck.same("a/max_abs_error", mx, A["max_abs_error"])
    ck.same("a/recorded_limit", A["criterion_a_limit"], limit)
    met = med <= limit
    ck.same("a/recorded_flag", A["criterion_a_met"], met)
    return {"registered": "held-out prediction: median absolute error <= 10 pp",
            "status": "MET" if met else "UNMET",
            "n_cells": n, "median_abs_error": med, "mean_abs_error": mean,
            "max_abs_error": mx, "limit": limit}


def criterion_b(v2, ck):
    tol = v2["tol"]
    ck.same("b/tol", tol, 0.20)
    coarse = [abs(x) for x in v2["criterion_b_width_rel_errs"].values()]
    refined = [abs(x) for x in v2["criterion_b_width_rel_errs_refined"].values()]
    max_coarse, max_refined = max(coarse), max(refined)
    edge = abs(v2["criterion_b_edge_position_max_rel_err_refined"])
    slope = v2["K1_zero_delta_slope"]["slope"]
    cut = v2["slope_cut"]
    widths_ok = max_refined <= tol
    edge_ok = edge <= tol
    nonempty = abs(slope) <= cut
    ck.same("b/coarse_grid_flag", v2["criterion_b_width_within_tol"], max_coarse <= tol)
    ck.same("b/refined_width_flag", v2["criterion_b_width_within_tol_refined"], widths_ok)
    ck.same("b/edge_position_flag", v2["criterion_b_edge_position_within_tol_refined"], edge_ok)
    ck.same("b/non_empty_flag", v2["K1_zero_delta_insensitive"], nonempty)
    # the width law: width * sqrt(k) / sigma is constant in k at fixed sigma
    law = {}
    for row in v2["band_law_tangent"]:
        law.setdefault(row["sigma"], []).append(row["width_times_sqrt_k_over_sigma"])
    spreads = {s: max(v) - min(v) for s, v in law.items()}
    ck.ok("b/band_law_constant_in_k",
          all(sp <= 1e-9 for sp in spreads.values()),
          "max spread in width*sqrt(k)/sigma: %r" % spreads)
    met = widths_ok and edge_ok and nonempty
    ck.same("b/recorded_flag", v2["criterion_b_met"], met)
    return {"registered": "insensitivity region non-empty (|slope in log k| <= 0.01) "
                          "with its boundary within +/-20 % of the predicted band width",
            "status": "MET" if met else "UNMET",
            "tol": tol, "max_width_rel_err_coarse": max_coarse,
            "max_width_rel_err_refined": max_refined,
            "edge_position_max_rel_err_refined": edge,
            "slope_at_delta_zero": slope, "slope_cut": cut,
            "width_law_spreads": {str(k): v for k, v in spreads.items()}}


def criterion_c(v3, ck):
    cells = v3["cells"]
    inf = {k: c for k, c in sorted(cells.items())
           if 0.01 < c["predicted_power_derived"] < 0.99}
    n_inf = len(inf)
    better = [k for k, c in inf.items() if c["paired_power_difference"]["mean"] > 0]
    sig_better = [k for k, c in inf.items()
                  if c["paired_power_difference"]["ci_lo"] > 0.0]
    sig_worse = [k for k, c in inf.items()
                 if c["paired_power_difference"]["ci_hi"] < 0.0]
    p = binom_sf(len(better), n_inf)
    cc = v3["criterion_c"]
    ck.same("c/n_cells", len(cells), 48)
    ck.same("c/informative_rule_flag_agrees",
            sorted(k for k, c in cells.items() if c["informative"]), sorted(inf))
    ck.same("c/n_informative", n_inf, cc["n_informative_cells"])
    ck.same("c/n_derived_better", len(better), cc["n_cells_derived_better"])
    ck.same("c/n_constant_better", n_inf - len(better), cc["n_cells_constant_better"])
    ck.same("c/n_significantly_better", len(sig_better),
            len(cc["cells_derived_significantly_better"]))
    ck.same("c/n_significantly_worse", len(sig_worse),
            len(cc["cells_constant_significantly_better"]))
    ck.same("c/sign_test_p", p, cc["sign_test_p_one_sided"])
    factors = sorted(c["factor"]["mean"] for c in inf.values()
                     if math.isfinite(c["factor"]["mean"]))
    ck.same("c/median_factor", statistics.median(factors), cc["median_factor"])
    ck.same("c/min_factor", min(factors), cc["min_factor"])
    ck.same("c/max_factor", max(factors), cc["max_factor"])
    # the registered wording: the derived rule is better, and the constant rule
    # is never significantly better
    met = (len(better) > n_inf / 2.0) and p < 0.05 and not sig_worse
    ck.same("c/recorded_flag", v3["criterion_c_met"], met)
    strict_fail = [k for k, c in inf.items() if not c["factor"]["ci_lo"] > 1.0]
    ck.same("c/strict_reading_n_failures", len(strict_fail),
            v3["criterion_c_strict_n_failures"])
    ck.same("c/strict_reading_flag", v3["criterion_c_strict_met"], not strict_fail)
    # the mechanism block: order-free, and its verdict must follow its own statistic
    m = v3["mechanism_gap_ordering"]
    pairs = sorted((c["standardised_threshold_gap"]["mean"], c["factor"]["mean"], k)
                   for k, c in inf.items() if math.isfinite(c["factor"]["mean"]))
    rises = falls = 0
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            if abs(pairs[j][0] - pairs[i][0]) <= GAP_TOL:
                continue
            lo, hi = (i, j) if pairs[i][0] < pairs[j][0] else (j, i)
            if pairs[hi][1] > pairs[lo][1]:
                rises += 1
            elif pairs[hi][1] < pairs[lo][1]:
                falls += 1
    compared = rises + falls
    tau = ((rises - falls) / float(compared)) if compared else None
    ck.same("c/mechanism_pairs_compared", compared, m["pairs_compared"])
    ck.same("c/mechanism_factor_rises_with_gap", rises, m["factor_rises_with_gap"])
    ck.same("c/mechanism_factor_falls_with_gap", falls, m["factor_falls_with_gap"])
    ck.same("c/mechanism_tau_like", tau, m["tau_like"])
    ck.same("c/mechanism_is_order_free", m["order_free"], True)
    # the recomputed verdict must mirror the instrument's THREE states, not two (see
    # instrument_v3.py): an undefined statistic is neither ordered nor unordered.  Mirroring the
    # two-state form here would also raise TypeError on None, i.e. fail for the wrong reason.
    ck.same("c/mechanism_verdict_follows_its_own_statistic",
            m["verdict"] == ("the exclusion rule leaves no comparable pair: the statistic is "
                             "UNDEFINED, neither ordered nor unordered"
                             if tau is None else
                             ("the mean gap ORDERS the factor" if tau > 0.5
                              else "the mean gap does not order the factor")), True)
    q_spreads = {}
    for b in range(4):
        chunk = pairs[b * len(pairs) // 4:(b + 1) * len(pairs) // 4]
        fs = [c[1] for c in chunk]
        q_spreads[str(b)] = max(fs) - min(fs)
    ck.same("c/mechanism_quartile_spreads", q_spreads,
            {str(i): q["factor_spread"] for i, q in
             enumerate(m["ordering_is_not_determination"]["gap_quartiles"])})
    widest = m["ordering_is_not_determination"]["max_factor_spread_inside_a_quartile"]
    ck.ok("c/ordering_is_not_determination", widest > 0.1,
          "max factor spread inside a gap quartile: %r" % widest)
    ck.same("c/distribution_mechanism_flag", v3["mechanism_correct_is_distribution"]["verdict"],
            "holds" if v3["K4_ok"] else "fails")
    return {"registered": "the derived rule beats the best constant threshold matched "
                          "to zero honest rejections, as a factor with CIs",
            "status": "MET" if met else "UNMET",
            "n_informative_cells": n_inf,
            "n_derived_better": len(better), "n_constant_better": n_inf - len(better),
            "n_significantly_better": len(sig_better),
            "n_significantly_worse": len(sig_worse),
            "sign_test_p_one_sided": p,
            "factor": {"min": min(factors), "median": statistics.median(factors),
                       "max": max(factors)},
            "secondary_strict_reading": {
                "wording": "the factor's 95 % CI lower bound exceeds 1 in every "
                           "informative cell",
                "status": "UNMET" if strict_fail else "MET",
                "n_failing_cells": len(strict_fail)},
            "mechanism": {
                "statistic": m["statistic"], "order_free": m["order_free"],
                "pairs_compared": compared,
                "factor_rises_with_gap": rises, "factor_falls_with_gap": falls,
                "tau_like": tau, "verdict": m["verdict"],
                "ordering_is_not_determination": m["ordering_is_not_determination"],
                "distribution_mechanism":
                    {"verdict": v3["mechanism_correct_is_distribution"]["verdict"],
                     "n_unmatched_of_48": v3["K4_n_unmatched"],
                     "max_abs_z": v3["K4_max_abs_z"],
                     "why": v3["mechanism_correct_is_distribution"]["why"]}}}


def criterion_d(stages, ck):
    per_stage = {}
    for tag, _s, artefact, _p in STAGES:
        per_stage[tag] = load(os.path.join(HERE, artefact))["n_streams"]
    floor = all(v >= 3 for v in per_stage.values())
    ck.ok("d/n_streams_at_least_3", floor, "%r" % per_stage)
    v3 = load(os.path.join(HERE, "results_v3.json"))
    lens = sorted(set(len(c["fpr_constant"]["per_stream"]) for c in v3["cells"].values()))
    ck.ok("d/per_stream_arrays_present", lens == [v3["n_streams"]],
          "per-stream array lengths: %r (n_streams %d)" % (lens, v3["n_streams"]))
    return {"registered": "at least 3 disjoint streams per cell, mean +/- sd, "
                          "with intervals on the key contrasts",
            "status": "MET" if (floor and lens == [v3["n_streams"]]) else "UNMET",
            "n_streams_per_stage": per_stage,
            "v3_per_stream_array_length": lens[0] if len(lens) == 1 else lens}


# ------------------------------------------------------ the sensitivity ----

def sensitivity(v4, ck):
    s1 = v4["S1_lattice"]
    tol = s1["tolerance_pp"]
    r_star = s1["r_star_usable_boundary"]
    rows = s1["rows"]
    measured_rows = [r for r in rows if r["error"] is not None]
    inside = [r for r in measured_rows if r["lattice_ratio"] <= r_star]
    worst_inside = max(abs(r["error"]) for r in inside)
    worst_overall = max(abs(r["error"]) for r in measured_rows)
    ck.ok("S1/every_cell_inside_the_boundary_is_within_tolerance",
          worst_inside <= tol, "worst |error| inside r* = %.6f (tolerance %r)"
          % (worst_inside, tol))
    bad = [r["lattice_ratio"] for r in measured_rows if abs(r["error"]) > tol]
    largest_ratio_exceeding = max(bad) if bad else 0.0
    ck.same("S1/largest_ratio_still_exceeding_tolerance",
            largest_ratio_exceeding, s1["largest_ratio_exceeding_tolerance"])
    flips = {}
    for r in measured_rows:
        flips.setdefault(r["sigma_node"], []).append((r["k"], r["error"]))
    stage_rule, ties_excluded = {}, {}
    for sigma, pts in flips.items():
        pts.sort()
        signs = [1 if e > 0 else -1 for _k, e in pts]   # the stage's rule: an exact 0 is negative
        stage_rule[sigma] = sum(1 for i in range(1, len(signs))
                                if signs[i] != signs[i - 1])
        nonzero = [1 if e > 0 else -1 for _k, e in pts if e != 0.0]
        ties_excluded[sigma] = sum(1 for i in range(1, len(nonzero))
                                   if nonzero[i] != nonzero[i - 1])
    recorded_flips = {r["sigma_node"]: r["sign_flips_in_k"]
                      for r in s1["non_monotonicity"]}
    ck.same("S1/sign_flips_in_k_recomputed_agree", stage_rule, recorded_flips)
    ck.ok("S1/error_changes_sign_under_both_foldings_of_exact_ties",
          all(v >= 1 for v in stage_rule.values())
          and all(v >= 1 for v in ties_excluded.values()),
          "stage rule %r | exact ties excluded %r" % (stage_rule, ties_excluded))
    gauss = v4["S1_gaussian_control"]
    ck.ok("S1/gaussian_control_exact", v4["K1_gaussian_exact"],
          "max |error| %r" % v4["K1_max_gaussian_error"])
    gain = worst_overall / v4["K1_max_gaussian_error"]
    ck.ok("S1/gaussian_control_tighter_than_the_lattice",
          gain > 100.0, "gaussian %r vs worst lattice %r -> %.1fx tighter"
          % (v4["K1_max_gaussian_error"], worst_overall, gain))
    ck.ok("S1/mirror_control_opposite_sign", v4["K4_mirror_opposite"])

    measured = v4["S2_measured"]
    overshoot = [e["mean_difference"] - e["bound_1_minus_pc"] for e in measured]
    ck.ok("S2/the_difference_never_exceeds_its_bound",
          max(overshoot) <= 0.0, "max overshoot %r" % max(overshoot))
    ck.same("S2/bounds_hold_flag", v4["K2_bounds_hold"], max(overshoot) <= 0.0)
    ck.ok("S2/saturated_cells_still_resolve_the_difference",
          all(e["ci_lo"] > 0 or not e["saturated"] for e in measured),
          "saturated cells whose interval does not exclude zero: %r"
          % [e["n_cal"] for e in measured if e["saturated"] and not e["ci_lo"] > 0])
    sat = [e["bound_1_minus_pc"] for e in measured if e["saturated"]]
    uns = [e["bound_1_minus_pc"] for e in measured if not e["saturated"]]
    ck.ok("S2/both_saturated_and_unsaturated_sets_non_empty",
          bool(sat) and bool(uns), "%d saturated, %d unsaturated" % (len(sat), len(uns)))
    ck.same("S2/saturated_max_achievable_gain", max(sat), v4["K2_saturated_max_gain"])
    ck.same("S2/unsaturated_max_achievable_gain", max(uns), v4["K2_unsaturated_max_gain"])
    ck.same("S2/gain_bound_shrinks", max(sat) < max(uns), v4["K2_gain_bound_shrinks"])
    k2_ok = (bool(sat) and bool(uns) and max(overshoot) <= 0.0
             and max(sat) < max(uns) and max(sat) <= tol)
    ck.same("S2/recorded_flag", v4["K2_ok"], k2_ok)
    grid = v4["S2_grid"]
    ck.same("S2/n_saturated_in_the_grid", sum(1 for g in grid if g["saturated"]),
            v4["K2_n_saturated"])
    bound_matches = all(abs(g["achievable_difference_bound"]
                            - (1.0 - g["power_constant_predicted"])) < 1e-12
                        for g in grid)
    ck.ok("S2/bound_is_one_minus_the_constant_rules_power", bound_matches)

    res = v4["S3_resolution"]
    summary = v4["S3_summary"]
    streams = v4["n_streams"]
    decidable = [r for r in res if r["ci_lo_at_41"] > 1.0]
    never = [r for r in res if r["n_min_streams"] is None]
    n_mins = sorted(r["n_min_streams"] for r in res if r["n_min_streams"] is not None)
    ck.same("S3/n_cells", len(res), summary["n_cells"])
    ck.same("S3/n_decidable_at_41", len(decidable), summary["n_decidable_at_41"])
    ck.same("S3/n_indecidable_at_41", len(res) - len(decidable), summary["n_indecidable_at_41"])
    ck.same("S3/n_never_decidable", len(never), summary["n_never_decidable"])
    ck.same("S3/never_decidable_cells", [r["cell"] for r in never],
            summary["never_decidable_cells"])
    ck.ok("S3/every_never_decidable_cell_has_a_factor_at_or_below_one",
          all(r["factor"] <= 1.0 for r in never),
          "%r" % [(r["cell"], r["factor"]) for r in never])
    ck.same("S3/n_min_median", statistics.median(n_mins), summary["n_min_median"])
    ck.same("S3/n_min_min", min(n_mins), summary["n_min_min"])
    ck.same("S3/n_min_max", max(n_mins), summary["n_min_max"])
    agreement = [r for r in res if r["n_min_streams"] is not None
                 and (r["n_min_streams"] <= streams) == (r["ci_lo_at_41"] > 1.0)]
    disagree = [r["cell"] for r in res if r["n_min_streams"] is not None
                and (r["n_min_streams"] <= streams) != (r["ci_lo_at_41"] > 1.0)]
    ck.same("S3/decidable_iff_n_min_within_the_budget", len(agreement),
            v4["K3_agreement"]["n_agree"])
    ck.same("S3/disagreements", disagree, v4["K3_agreement"]["disagreements"])
    ck.same("S3/recorded_flag", v4["K3_ok"], not disagree)
    # the inversion must reproduce v3's own verdict, cell by cell
    v3 = load(os.path.join(HERE, "results_v3.json"))
    v3_dec = sorted(k for k, c in v3["cells"].items()
                    if c["informative"] and c["factor"]["ci_lo"] > 1.0)
    ck.same("S3/inversion_reproduces_v3_interval_verdict",
            sorted(r["cell"] for r in decidable), v3_dec)
    return {
        "S1_lattice": {
            "statement": s1["r_star_statement"],
            "usable_boundary_r_star": r_star, "tolerance_pp": tol,
            "n_cells": len(rows),
            "worst_abs_error_inside_the_boundary": worst_inside,
            "worst_abs_error_over_all_measured_cells": worst_overall,
            "largest_ratio_still_exceeding_tolerance": largest_ratio_exceeding,
            "sign_flips_in_k_per_node": recorded_flips,
            "sign_flips_with_exact_ties_excluded": ties_excluded,
            "gaussian_control_max_abs_error": v4["K1_max_gaussian_error"],
            "gaussian_control_tighter_by_factor": gain},
        "S2_ceiling": {
            "n_saturated_in_the_grid": sum(1 for g in grid if g["saturated"]),
            "n_grid": len(grid),
            "n_saturated_measured": len(sat), "n_unsaturated_measured": len(uns),
            "saturated_max_achievable_gain": max(sat),
            "unsaturated_max_achievable_gain": max(uns),
            "max_overshoot_of_the_bound": max(overshoot)},
        "S3_decidability": {
            "n_cells": len(res), "n_decidable_at_41": len(decidable),
            "n_indecidable_at_41": len(res) - len(decidable),
            "n_never_decidable": len(never),
            "n_min_median": statistics.median(n_mins),
            "n_min_min": min(n_mins), "n_min_max": max(n_mins)},
    }


# ------------------------------------------------------- prior evidence ----

def prior_evidence(v0, v2, ck):
    c2 = v0["controls"]["C2_discrimination"]
    mean_flat = all(abs(r["mean_k64"] - r["mean_k4"]) < 0.01 for r in c2)
    var_grows = all(r["var_k64"] > r["var_k4"] for r in c2)
    ck.ok("P1/mean_statistic_flat_in_k", mean_flat,
          "max |mean_k64 - mean_k4| %r"
          % max(abs(r["mean_k64"] - r["mean_k4"]) for r in c2))
    ck.ok("P1/variance_statistic_grows_in_k", var_grows)
    null = v2["K1_null_location_preserving"]
    worst_null = max(r["abs_err"] for r in null)
    ck.ok("P1/location_preserving_null_matches_the_construct",
          all(r["ok_vs_construct"] for r in null),
          "worst |err| %r over %d cells" % (worst_null, len(null)))
    law = {}
    for row in v2["band_law_tangent"]:
        law.setdefault(row["sigma"], []).append(row["width_times_sqrt_k_over_sigma"])
    ck.ok("P2/band_width_shrinks_as_one_over_sqrt_k",
          all(max(v) - min(v) <= 1e-9 for v in law.values()))
    best = v0["best_responder"]
    best_is_location_preserving = all(
        d["node_best"].startswith("collapse") for d in best.values())
    best_power_zero = all(d["node_best_power"] == 0.0 for d in best.values())
    ck.ok("P3/the_nodes_best_response_is_uniformly_undetectable",
          best_is_location_preserving and best_power_zero,
          "%r" % {k: (d["node_best"], d["node_best_power"]) for k, d in best.items()})
    return {
        "P1": {"registered": "against a location-preserving divergence, detection is "
                             "bounded away from 1 by a constant no budget improves",
               "evidence": {"mean_statistic_flat_in_k": mean_flat,
                            "variance_statistic_grows_in_k": var_grows,
                            "worst_null_abs_err": worst_null,
                            "n_null_cells": len(null)},
               "status": "CONFIRMED" if (mean_flat and var_grows
                                         and all(r["ok_vs_construct"] for r in null))
                         else "NOT CONFIRMED"},
        "P2": {"registered": "against a location-shifting divergence, detection improves "
                             "only inside a transition band around the threshold, whose "
                             "width shrinks like sigma/sqrt(k)",
               "evidence": {"width_law_spreads": {str(k): max(v) - min(v)
                                                  for k, v in law.items()}},
               "status": "CONFIRMED"},
        "P3": {"registered": "against a best-responding node, the marginal value of one "
                             "more re-execution at the verifier's optimum tends to zero",
               "evidence": {"best_response_per_budget":
                            {k: [d["node_best"], d["node_best_power"]]
                             for k, d in best.items()}},
               "status": "CONFIRMED" if (best_is_location_preserving and best_power_zero)
                         else "NOT CONFIRMED"},
    }


# ------------------------------------------------------------- the entry ---

# ------------------------------------------------- the manuscript's numbers ---

def _flips_ties_excluded(rows):
    """Sign changes in the error as the budget grows, ignoring exact zeros."""
    pts = [(r["k"], r["error"]) for r in sorted(rows, key=lambda r: r["k"])
           if r["error"] != 0.0]
    signs = [1 if e > 0 else -1 for _k, e in pts]
    return sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])


def manuscript_facts(v0, v1, v2, v3, v4, out, ck):
    """Every aggregate the manuscript quotes, recomputed from the stage artefacts.

    A number that appears in the prose and not here has no home in the package.
    """
    A = v1["A_out_of_sample"]
    inf = {k: c for k, c in v3["cells"].items()
           if 0.01 < c["predicted_power_derived"] < 0.99}

    def group(by):
        res = {}
        for key in sorted(set(c[by] for c in inf.values())):
            rs = [c for c in inf.values() if c[by] == key]
            fs = sorted(c["factor"]["mean"] for c in rs)
            res[str(key)] = {
                "n_cells": len(rs),
                "median_factor": statistics.median(fs),
                "min_factor": min(fs),
                "max_factor": max(fs),
                "n_better": sum(1 for c in rs
                                if c["paired_power_difference"]["mean"] > 0),
                "n_significantly_better": sum(1 for c in rs
                                              if c["paired_power_difference"]["ci_lo"] > 0),
            }
        return res

    by_lam, by_ncal = group("lam"), group("n_cal")
    ck.same("facts/per_lambda_cells_sum_to_informative",
            sum(g["n_cells"] for g in by_lam.values()), len(inf))
    ck.same("facts/per_n_cal_cells_sum_to_informative",
            sum(g["n_cells"] for g in by_ncal.values()), len(inf))

    s1 = v4["S1_lattice"]
    measured = [r for r in s1["rows"] if r["error"] is not None]
    gauss = v4["S1_gaussian_control"]
    worst_overall = max(abs(r["error"]) for r in measured)
    s3 = v4["S3_resolution"]
    n_mins = sorted(r["n_min_streams"] for r in s3 if r["n_min_streams"] is not None)
    c2 = v0["controls"]["C2_discrimination"]
    null = v2["K1_null_location_preserving"]
    keys = sorted(v2["measured_bands"], key=float)

    facts = {
        "crit_a": {"n_cells": A["n_cells"], "median_abs_error": A["median_abs_error"],
                   "mean_abs_error": A["mean_abs_error"],
                   "max_abs_error": A["max_abs_error"], "limit": A["criterion_a_limit"],
                   "n_cells_within_1pp": sum(1 for c in A["cells"]
                                             if abs(c["abs_error"]) <= 0.01)},
        "crit_a_invariance": {"n_groups": v1["B_invariance"]["n_groups"],
                              "max_spread": v1["B_invariance"]["max_spread"]},
        "crit_a_mechanism_blindness": {
            "n_cells": v1["verdicts"]["C_mechanism_blindness_n"],
            "max_abs_error": v1["verdicts"]["C_mechanism_blindness_max_error"]},
        "crit_a_calibration_cell": {
            "alpha_anchor": v1["D_calibration"]["alpha_anchor"],
            "c_alpha_anchor": v1["D_calibration"]["c_alpha_anchor"],
            "k": v1["D_calibration"]["divergent_pairs"]["k"],
            "implied_u": v1["D_calibration"]["divergent_pairs"]["implied_u"],
            "implied_delta": v1["D_calibration"]["divergent_pairs"]["implied_delta_at_sigma_1"],
            "observed_power": v1["D_calibration"]["divergent_pairs"]["observed_power"],
            "fabrication_observed": v1["D_calibration"]["same_input_fabrication"]["observed_detection"],
            "fabrication_predicted": v1["D_calibration"]["same_input_fabrication"]["construct_prediction"],
            "fabrication_abs_error": v1["D_calibration"]["same_input_fabrication"]["abs_error"]},
        "crit_b": {"tol": v2["tol"],
                   "max_width_rel_err_coarse": max(abs(x) for x in
                                                   v2["criterion_b_width_rel_errs"].values()),
                   "max_width_rel_err_refined": max(abs(x) for x in
                                                    v2["criterion_b_width_rel_errs_refined"].values()),
                   "edge_rel_err_coarse": abs(v2["criterion_b_edge_position_max_rel_err"]),
                   "edge_rel_err_refined": abs(v2["criterion_b_edge_position_max_rel_err_refined"]),
                   "slope_at_delta_zero": v2["K1_zero_delta_slope"]["slope"],
                   "slope_cut": v2["slope_cut"], "n_grid": v2["n_grid"],
                   "width_law_spreads": {
                       k: max(r["width_times_sqrt_k_over_sigma"] for r in v2["band_law_tangent"]
                              if str(r["sigma"]) == k)
                       - min(r["width_times_sqrt_k_over_sigma"] for r in v2["band_law_tangent"]
                             if str(r["sigma"]) == k)
                       for k in sorted(set(str(r["sigma"]) for r in v2["band_law_tangent"]))},
                   "per_sigma": {k: {
                       "width_rel_err": v2["measured_bands"][k]["width_rel_err"],
                       "width_rel_err_refined": v2["measured_bands"][k]["width_rel_err_refined"],
                       "delta_lo_pred": v2["predicted_bands"][k]["delta_lo"],
                       "delta_hi_pred": v2["predicted_bands"][k]["delta_hi"],
                       "delta_lo_meas": v2["measured_bands"][k]["delta_lo_refined"],
                       "delta_hi_meas": v2["measured_bands"][k]["delta_hi_refined"],
                       "width_pred": v2["measured_bands"][k]["width_pred"],
                       "width_meas": v2["measured_bands"][k]["width"]}
                       for k in keys},
                   "n_sigma": len(keys), "k_band": v2["k_band"]},
        "crit_c": {"n_informative_cells": len(inf),
                   "n_derived_better": v3["criterion_c"]["n_cells_derived_better"],
                   "n_constant_better": v3["criterion_c"]["n_cells_constant_better"],
                   "n_significantly_better": len(v3["criterion_c"]["cells_derived_significantly_better"]),
                   "n_significantly_worse": len(v3["criterion_c"]["cells_constant_significantly_better"]),
                   "sign_test_p_one_sided": v3["criterion_c"]["sign_test_p_one_sided"],
                   "median_factor": v3["criterion_c"]["median_factor"],
                   "min_factor": v3["criterion_c"]["min_factor"],
                   "max_factor": v3["criterion_c"]["max_factor"],
                   "strict_reading_n_failures": v3["criterion_c_strict_n_failures"],
                   "by_lambda": by_lam, "by_n_cal": by_ncal,
                   "n_cells_with_ci_excluding_one": sum(1 for c in inf.values()
                                                        if c["factor"]["ci_lo"] > 1.0)},
        "crit_c_mechanism": {
            "pairs_compared": v3["mechanism_gap_ordering"]["pairs_compared"],
            "factor_rises_with_gap": v3["mechanism_gap_ordering"]["factor_rises_with_gap"],
            "factor_falls_with_gap": v3["mechanism_gap_ordering"]["factor_falls_with_gap"],
            "tau_like": v3["mechanism_gap_ordering"]["tau_like"],
            "quartile_spread": v3["mechanism_gap_ordering"]["ordering_is_not_determination"]
            ["max_factor_spread_inside_a_quartile"],
            "k4_n_unmatched_of_48": v3["K4_n_unmatched"], "k4_max_abs_z": v3["K4_max_abs_z"],
            "k1_n_checks": v3["K1_n_checks"], "k1_max_abs_z": v3["K1_max_abs_z"]},
        "crit_d": {"streams": v3["n_streams"],
                   "streams_by_stage": {"v0": v0["n_streams"], "v1": v1["n_streams"],
                                        "v2": v2["n_streams"], "v3": v3["n_streams"],
                                        "v4": v4["n_streams"]}},
        "priors": {
            "P1_status": out["prior_evidence"]["P1"]["status"],
            "P2_status": out["prior_evidence"]["P2"]["status"],
            "P3_status": out["prior_evidence"]["P3"]["status"],
            "worst_null_abs_err": max(r["abs_err"] for r in null),
            "n_null_cells": len(null),
            "mean_stat_flat_max_delta": max(abs(r["mean_k64"] - r["mean_k4"]) for r in c2),
            "var_k4_max": max(r["var_k4"] for r in c2),
            "var_k64_max": max(r["var_k64"] for r in c2),
            "n_best_response_budgets": len(v0["best_responder"]),
            "best_response_node": sorted(set(d["node_best"] for d in v0["best_responder"].values())),
            "best_response_max_power": max(d["node_best_power"]
                                           for d in v0["best_responder"].values()),
        },
        "S1": {"r_star": s1["r_star_usable_boundary"], "tol_pp": s1["tolerance_pp"],
               "n_cells": len(measured),
               "worst_abs_error_inside": max(abs(r["error"]) for r in measured
                                             if r["lattice_ratio"] <= s1["r_star_usable_boundary"]),
               "worst_abs_error_overall": worst_overall,
               "largest_ratio_exceeding": s1["largest_ratio_exceeding_tolerance"],
               "gaussian_max_abs_error": v4["K1_max_gaussian_error"],
               "gaussian_tighter_by": worst_overall / v4["K1_max_gaussian_error"],
               "median_abs_error_by_ratio_bin": {
                   "%g-%g" % (b["ratio_lo"], b["ratio_hi"]): b["median_abs_error"]
                   for b in s1["bins"]},
               "max_abs_error_by_ratio_bin": {
                   "%g-%g" % (b["ratio_lo"], b["ratio_hi"]): b["max_abs_error"]
                   for b in s1["bins"]},
               "n_cells_inside_boundary": sum(
                   1 for r in measured if r["lattice_ratio"] <= s1["r_star_usable_boundary"]),
               "sign_flips_stage_rule": {str(n["sigma_node"]): n["sign_flips_in_k"]
                                         for n in s1["non_monotonicity"]},
               "sign_flips_ties_excluded": {
                   str(n["sigma_node"]): _flips_ties_excluded(
                       [r for r in measured if r["sigma_node"] == n["sigma_node"]])
                   for n in s1["non_monotonicity"]},
               "mirror_opposite": v4["K4_mirror_opposite"]},
        "S2": {"n_grid": len(v4["S2_grid"]), "n_saturated": v4["K2_n_saturated"],
               "n_saturated_measured": len([e for e in v4["S2_measured"] if e["saturated"]]),
               "n_unsaturated_measured": len([e for e in v4["S2_measured"] if not e["saturated"]]),
               "saturated_max_gain": v4["K2_saturated_max_gain"],
               "unsaturated_max_gain": v4["K2_unsaturated_max_gain"],
               "max_overshoot": max(e["mean_difference"] - e["bound_1_minus_pc"]
                                    for e in v4["S2_measured"]),
               "n_measured_ci_excludes_zero": sum(1 for e in v4["S2_measured"]
                                                  if e["ci_excludes_zero"]),
               "n_measured": len(v4["S2_measured"]),
               "measured": [{"n_cal": e["n_cal"], "k": e["k"], "lam": e["lam"],
                             "saturated": e["saturated"], "bound": e["bound_1_minus_pc"],
                             "difference": e["mean_difference"], "ci_lo": e["ci_lo"],
                             "ci_hi": e["ci_hi"]} for e in v4["S2_measured"]]},
        "S3": {"n_cells": len(s3),
               "n_decidable": len([r for r in s3 if r["ci_lo_at_41"] > 1.0]),
               "n_indecidable": len([r for r in s3 if r["ci_lo_at_41"] <= 1.0]),
               "n_never_decidable": len([r for r in s3 if r["n_min_streams"] is None]),
               "n_min_median": statistics.median(n_mins),
               "n_min_min": min(n_mins), "n_min_max": max(n_mins),
               "n_agree": v4["K3_agreement"]["n_agree"],
               "never_decidable_cells": v4["K3_agreement"] and
               [r["cell"] for r in s3 if r["n_min_streams"] is None]},
        "stage_params": {
            "v0": {"n_mc": v0["n_mc"], "n_streams": v0["n_streams"], "alpha": v0["alpha"],
                   "n_controls": len(v0["controls"]),
                   "all_pass": v0["verdicts"]["ALL_CONTROLS_PASS"]},
            "v1": {"n_mc": v1["n_mc_grid"], "n_streams": v1["n_streams"],
                   "c_alpha": v1["c_alpha"], "all_pass": v1["verdicts"]["ALL_PASS"]},
            "v2": {"n_mc": v2["n_mc"], "n_streams": v2["n_streams"], "n_grid": v2["n_grid"],
                   "k_band": v2["k_band"], "sigmas": v2["sigmas"], "all_pass": v2["ALL_PASS"]},
            "v3": {"n_mc": v3["n_mc"], "n_streams": v3["n_streams"], "k_grid": v3["k_grid"],
                   "lam_grid": v3["lam_grid"], "n_cal_grid": v3["n_cal_grid"],
                   "sigma_h": v3["sigma_h"], "n_cells": len(v3["cells"]),
                   "all_pass": v3["ALL_PASS"]},
            "v4": {"n_mc": v4["n_mc"], "n_streams": v4["n_streams"],
                   "s1_delta": v4["s1_delta"], "s1_node_sigmas": v4["s1_node_sigmas"],
                   "all_pass": v4["ALL_PASS"]},
        },
    }
    kb = facts["crit_b"]["k_band"]
    ck.same("facts/band_law_has_four_budgets", len(kb), 4)
    facts["crit_b"].update({
        "k_band_min": kb[0], "k_band_mid1": kb[1],
        "k_band_mid2": kb[2], "k_band_max": kb[-1],
        "width_law_spread_max": max(facts["crit_b"]["width_law_spreads"].values()),
        "margin_factor": int(round(facts["crit_b"]["tol"]
                                   / abs(facts["crit_b"]["max_width_rel_err_refined"]))),
        "zero_delta_insensitive": bool(v2["K1_zero_delta_insensitive"]),
    })
    ck.ok("facts/width_law_is_tight",
          facts["crit_b"]["width_law_spread_max"] < 1e-9,
          "%.3e" % facts["crit_b"]["width_law_spread_max"])
    facts["crit_c_mechanism"]["z_tol"] = v3["z_tol"]
    facts["S2"]["saturated_gain_ratio"] = (facts["S2"]["unsaturated_max_gain"]
                                           / facts["S2"]["saturated_max_gain"])
    facts["S1"]["bin_labels"] = ["%g-%g" % (b["ratio_lo"], b["ratio_hi"])
                                 for b in s1["bins"]]
    ck.same("facts/bin_labels_match_ratio_bin_keys",
            sorted(facts["S1"]["bin_labels"]),
            sorted(facts["S1"]["median_abs_error_by_ratio_bin"]))
    for lam_key, g in facts["crit_c"]["by_lambda"].items():
        g["lam"] = float(lam_key)     # the label the manuscript prints, not a measurement
    for ncal_key, g in facts["crit_c"]["by_n_cal"].items():
        g["n_cal"] = int(ncal_key)
    ck.same("facts/lambda_keys_are_the_grid",
            sorted(facts["crit_c"]["by_lambda"]), sorted(str(x) for x in v3["lam_grid"]))
    ck.same("facts/n_cal_keys_are_the_grid",
            sorted(int(k) for k in facts["crit_c"]["by_n_cal"]), sorted(v3["n_cal_grid"]))
    ck.same("facts/crit_c_ci_excluding_one_matches_strict_failures",
            facts["crit_c"]["n_cells_with_ci_excluding_one"],
            len(inf) - v3["criterion_c_strict_n_failures"])
    ck.same("facts/s3_decidable_plus_indecidable",
            facts["S3"]["n_decidable"] + facts["S3"]["n_indecidable"], facts["S3"]["n_cells"])
    ck.same("facts/s1_cells_inside_boundary_counted",
            facts["S1"]["n_cells_inside_boundary"],
            sum(1 for r in measured
                if r["lattice_ratio"] <= s1["r_star_usable_boundary"]))
    ck.ok("facts/gaussian_control_is_far_tighter",
          facts["S1"]["gaussian_tighter_by"] > 100.0,
          "%.1fx" % facts["S1"]["gaussian_tighter_by"])
    ck.ok("facts/priors_all_resolved",
          all(out["prior_evidence"][p]["status"] in ("CONFIRMED", "NOT CONFIRMED")
              for p in ("P1", "P2", "P3")))
    out["manuscript_facts"] = facts
    return facts


def main():
    checks = Checks()
    out = {"experiment": "issue #44 -- canonical aggregate over the five stage artefacts",
           "alpha": 0.05, "stage_order_is_load_bearing": True}
    log, entries = run_stages()
    out["stages"] = entries
    for e in entries:
        if e["exit_code"] != 0:
            sys.stdout.write("stage %s exited %d\n" % (e["tag"], e["exit_code"]))
            with io.open(os.path.join(HERE, "run.log"), "w", encoding="utf-8") as fh:
                fh.write("\n".join(log) + "\n")
            return 1

    v0 = load(os.path.join(HERE, "results_v0.json"))
    v1 = load(os.path.join(HERE, "results_v1.json"))
    v2 = load(os.path.join(HERE, "results_v2.json"))
    v3 = load(os.path.join(HERE, "results_v3.json"))
    v4 = load(os.path.join(HERE, "results_v4.json"))

    out["stage_verdicts"] = {
        e["tag"]: {k: v for k, v in load(os.path.join(HERE, e["artefact"])).items()
                   if k in ("ALL_PASS", "ALL_CONTROLS_PASS")}
        for e in entries}
    out["criteria"] = {
        "a": criterion_a(v1, checks),
        "b": criterion_b(v2, checks),
        "c": criterion_c(v3, checks),
        "d": criterion_d(entries, checks),
    }
    out["sensitivity"] = sensitivity(v4, checks)
    out["prior_evidence"] = prior_evidence(v0, v2, checks)
    manuscript_facts(v0, v1, v2, v3, v4, out, checks)
    out["cross_checks"] = {
        "n_checks": len(checks.rows),
        "n_failed": checks.failed,
        "note": "every criterion and every sensitivity number is recomputed from the "
                "stage artefacts' primitives and compared with the flag the stage "
                "recorded about itself; the two must agree",
        "failures": [[n, d] for ok, n, d in checks.rows if not ok],
    }

    dest = os.path.join(HERE, "canonical_results.json")
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
    digest = sha256_file(dest)

    log.append("## aggregate")
    log.append("   criteria: " + ", ".join(
        "%s=%s" % (k, out["criteria"][k]["status"]) for k in sorted(out["criteria"])))
    log.append("   prior evidence: " + ", ".join(
        "%s=%s" % (k, out["prior_evidence"][k]["status"]) for k in sorted(out["prior_evidence"])))
    log.append("   cross-checks: %d run, %d failed" % (len(checks.rows), checks.failed))
    for ok, name, detail in checks.rows:
        if not ok:
            log.append("   FAIL %s: %s" % (name, detail))
    log.append("   canonical_results.json sha256 " + digest)
    with io.open(os.path.join(HERE, "run.log"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\n")

    sys.stdout.write("criteria: " + ", ".join(
        "%s=%s" % (k, out["criteria"][k]["status"]) for k in sorted(out["criteria"])) + "\n")
    sys.stdout.write("cross-checks: %d run, %d failed\n"
                     % (len(checks.rows), checks.failed))
    for ok, name, detail in checks.rows:
        if not ok:
            sys.stdout.write("FAIL %s: %s\n" % (name, detail))
    sys.stdout.write("canonical_results.json sha256 %s\n" % digest)
    return 1 if checks.failed else 0


if __name__ == "__main__":
    sys.exit(main())
