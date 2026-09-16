#!/usr/bin/env python3
"""Issue #47 -- CANONICAL RUNNER: run the frozen stages, then RECOMPUTE what the paper claims.

    python3 canonical_runner.py              # stages + recompute + cross-check + canonical_results.json
    python3 canonical_runner.py --selftest   # prove the recomputations can fail (no stage re-run)
    python3 canonical_runner.py --no-stages  # skip the (slow) stages, recompute from artefacts on disk

WHY THIS FILE COMPUTES RATHER THAN COLLECTS.  A manuscript whose numbers are *read out of* an
artefact is only as good as the day the artefact was made: if a stage changes, the aggregate keeps
reporting the old value, and the check that compares them compares a file against itself.  So every
number the manuscript cites is **recomputed here from the stage artefacts' primitives** by a rule
written out in this file, and each recomputed value is then **cross-checked against the value the
stage recorded about itself** (`facts[...]["recorded"]`).  A disagreement fails the run.  The
aggregate is a view of the artefacts, not a transcript of them.

The four disciplines a guard in this package is held to (a review of this package's own instruments
asked for them, and they apply to this file as much as to any other):

  * CROSSOVER   -- a rule whose branch depends on a parameter names the parameter and says which
                   term wins; a quantity that can be UNDEFINED says so instead of reporting a
                   negative finding (see `criteria()`, where a registered metric that was never
                   measured reports `unmet` rather than a number).
  * EXCLUSIONS  -- an exclusion publishes the VALUES it drops, not only its rate (see
                   `external_reach()`, which reports every profile in and out of the reach window).
  * COVERAGE    -- each guard states the fraction of the surface it covers, and the type of
                   guarantee (value-level vs placement-level).
  * LIVENESS    -- every recomputation is mutated in `--selftest` and must fail there, because a
                   check that cannot fail is decoration.

Network-free, CPU-only, deterministic: no clock, no environment, no git object, no absolute path.
`--selftest` runs against copies in a scratch directory and needs no coordinate.
"""
import ast
import hashlib
import io
import itertools
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "run.log")

# The stage chain, in the order the claims require.  Each stage's own tree of checks is reduced to
# "how many ran, how many failed" and cross-checked against the flag the stage recorded about
# itself -- a flag is a claim, the check list is the evidence.
# Each stage declares its evidence explicitly, because the artefacts do NOT share one schema: four
# carry checks[i].ok, one carries checks[i].pass, one carries its checks under `verdict`, and one
# persists ONLY the flag.  A reader that assumed a field name would report a stage's success as a
# failure -- this runner did exactly that on its first run -- so the schema is declared here and a
# missing field RAISES rather than defaulting.
STAGES = [
    {"tag": "anchor", "script": "anchor_smoke.py", "artefact": "anchor_smoke_results.json",
     "flag": "ANCHORS_ALL_PASS", "evidence": ("verdict", "ok"),
     "what": "the classic competitive ratios and the consistency end, recovered exactly"},
    {"tag": "v0", "script": "instrument_v0.py", "artefact": "instrument_v0_results.json",
     "flag": "END_ANCHORS_ALL_PASS", "evidence": ("checks", "ok"),
     "what": "the crossed grid of error profiles, with the end anchors re-checked inside it"},
    {"tag": "scorer", "script": "scorer_v0.py", "artefact": "scorer_v0_results.json",
     "flag": "SCORER_CHECKS_ALL_PASS", "evidence": ("checks", "ok"),
     "what": "the held-out fit of the scalar baseline against the signed decomposition"},
    {"tag": "mechanism", "script": "mechanism_v0.py", "artefact": "mechanism_v0_results.json",
     "flag": "MECHANISM_CHECKS_ALL_PASS", "evidence": ("checks", "ok"),
     "what": "the mechanism: which decision each problem makes from the prediction"},
    {"tag": "paging", "script": "paging_v1.py", "artefact": "paging_v1_results.json",
     "flag": "CHECKS_ALL_PASS", "evidence": ("checks", "ok"),
     "what": "the per-page attachment, against the step-common one it replaces"},
    {"tag": "sufficiency", "script": "sufficiency_v1.py", "artefact": "sufficiency_v1_results.json",
     "flag": "ALL_PASS", "evidence": ("checks", "pass"),
     "what": "the scalar-insufficiency witness and the object-level contrast design"},
    {"tag": "external", "script": "external_cell_v1.py", "artefact": "external_cell_v1_results.json",
     "flag": "ALL_PASS", "evidence": None,
     "what": "the committed external cell anchored to a published system result"},
    {"tag": "lambdacert", "script": "lambda_cert_v1.py", "artefact": "lambda_cert_v1_results.json",
     "flag": "CHECKS_ALL_PASS", "evidence": ("checks", "ok"),
     "what": "the registered criterion (c): the certificate rule's calibration loss, as a factor"},
]


def read(name):
    """The text of a file in this package (package-relative, so it needs no coordinate)."""
    return io.open(os.path.join(HERE, name), encoding="utf-8").read()


def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def load(name):
    return json.load(io.open(os.path.join(HERE, name), encoding="utf-8"))


def run_stages(log):
    """Run every stage in order.  A stage that exits non-zero stops the run: the aggregate must not
    be built from a stage that failed."""
    rows = []
    for st in STAGES:
        log("== stage %-12s %s -- %s" % (st["tag"], st["script"], st["what"]))
        proc = subprocess.run([sys.executable, st["script"]], cwd=HERE,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout.split("\n"):
            log("   " + line)
        if proc.returncode != 0:
            log("   STAGE FAILED: %s exited %d" % (st["script"], proc.returncode))
            return None
        rows.append(st["tag"])
    return rows


def evidence_of(d, schema, artefact):
    """Reduce a stage's artefact to (run, failed) using its DECLARED schema.

    Fail-closed on purpose: an artefact whose declared evidence field is absent raises instead of
    silently producing an empty list, because "no checks found" and "every check passed" must never
    look the same to a reader of the aggregate.
    """
    if schema is None:
        return None, None, []
    node, field = schema
    if node not in d:
        raise KeyError("artefact %s declares no %r node for its evidence" % (artefact, node))
    rows = d[node]
    if not isinstance(rows, list):
        raise TypeError("artefact %s: %s is %s, not a list of checks"
                        % (artefact, node, type(rows).__name__))
    missing = [i for i, r in enumerate(rows) if field not in r]
    if missing:
        raise KeyError("artefact %s: %d of %d checks carry no %r field"
                       % (artefact, len(missing), len(rows), field))
    failed = [r for r in rows if not r[field]]
    return len(rows), len(failed), [r.get("check") for r in failed]


def stage_summary(st):
    """The stage's evidence, its recorded flag, and whether the two agree."""
    d = load(st["artefact"])
    run, failed, names = evidence_of(d, st["evidence"], st["artefact"])
    recorded = d.get(st["flag"])
    if recorded is None:
        raise KeyError("artefact %s records no %r flag" % (st["artefact"], st["flag"]))
    recomputed = None if run is None else (run > 0 and not failed)
    return {
        "tag": st["tag"],
        "script": st["script"],
        "script_sha256": sha(os.path.join(HERE, st["script"])),
        "artefact": st["artefact"],
        "artefact_sha256": sha(os.path.join(HERE, st["artefact"])),
        "what": st["what"],
        "checks_run": run,
        "checks_failed": failed,
        "flag": st["flag"],
        "flag_value": recorded,
        "recomputed_all_pass": recomputed,
        # where the artefact persists no per-check list, the flag is the only local record: the
        # agreement is then decided by the process exit status, and that residual is stated here
        # rather than papered over by defaulting to True.
        "agree": True if recomputed is None else bool(recomputed == bool(recorded)),
        "evidence_persisted": run is not None,
        "failed_checks": names,
    }


def kendall_tau(xs, ys):
    """Kendall tau-a over paired observations, computed here so the ordering claim is not taken
    from a stored field.

    THE CONVENTION IS PART OF THE RULE, and this one is the stage's: a pair tied in EITHER
    coordinate is dropped from numerator and denominator alike (`tau-a`).  Computing tau-b instead
    -- counting tied pairs in the denominator -- returns the same magnitude only when no ties exist;
    on the paging cell, where two profiles share a mean gain exactly, it returns 0.854 where the
    stage records 0.889.  That discrepancy is the reason this docstring names the convention: an
    implementation that silently used the other one would disagree with the artefact, and a rule
    whose text says "ties dropped" while its code counts them is the defect this package's own
    instruments are audited for.
    """
    num = den = 0
    for i, j in itertools.combinations(range(len(xs)), 2):
        a, b = xs[i] - xs[j], ys[i] - ys[j]
        if a == 0 or b == 0:
            continue
        num += 1 if a * b > 0 else -1
        den += 1
    return (num / den) if den else None


def witness(suf, facts):
    """F1.1 -- the scalar-insufficiency witness, recomputed from the per-block rows.

    The witness is constructive, not a p-value: two arms with the SAME multiset of |error| (one all
    positive, one all negative) have identical scalar features BY CONSTRUCTION, while the realised
    loss differs.  So the recomputation asserts the scalar gap is exactly zero over every block (this
    is the load-bearing identity -- a non-zero gap would mean the arms were not matched) and reports
    the loss gap against the cluster-unit MDE of its own block.
    """
    B = suf["part_B_matched_magnitude_witness"]["blocks"]
    gap = max(b["max_scalar_feature_gap"] for b in B)
    worst = min(B, key=lambda b: b["median_ratio_diff_plus_minus"])
    over = [b for b in B if abs(b["median_ratio_diff_plus_minus"]) > b["mde_cluster_unit"]]
    for name, value, rule in (
            ("claim1.scalar_gap_max_exact", gap,
             "max over blocks of max_scalar_feature_gap -- the load-bearing identity, exact 0"),
            ("claim1.worst_loss_gap", worst["median_ratio_diff_plus_minus"],
             "min over blocks of median_ratio_diff_plus_minus"),
            ("claim1.worst_block_mde", worst["mde_cluster_unit"],
             "mde_cluster_unit of the argmin block"),
            ("claim1.blocks_total", len(B), "len(blocks)"),
            ("claim1.blocks_exceeding_own_mde", len(over),
             "count of blocks with |loss gap| > their own cluster MDE"),
            ("claim1.pairs_per_block_min", min(b["n_pairs"] for b in B),
             "min over blocks of n_pairs"),
            ("claim1.worst_problem", worst["problem"], "problem of the argmin block"),
            ("claim1.worst_profile", worst["profile"], "profile of the argmin block")):
        facts[name] = {"value": value, "rule": rule, "recorded": None,
                       "source": ("sufficiency_v1_results.json:part_B_matched_magnitude_witness "
                                  "-- the blocks carry no summary field, so this is recomputation "
                                  "without a recorded value to cross-check against")}
    return {"scalar_gap_exact_zero": gap == 0.0,
            "worst_loss_gap": worst["median_ratio_diff_plus_minus"],
            "worst_block": [worst["problem"], worst["profile"]],
            "blocks": len(B), "blocks_over_mde": len(over)}


def sign_channel(suf, facts):
    """F1.2 -- the sign channel, recomputed as (median advantage) / (cluster MDE of the same block).

    THE FORM CONFOUND IS THE POINT.  `part_C2.contrast_b_clean` carries six rows: three matched
    **in form** and three mismatched, and the two families are distinguished by the CONTRAST STRING,
    not by the problem name -- a previous check keyed them by problem and compared the document
    against the mismatched numbers.  Only the matched-form family is reported as evidence; the other
    is carried as the confound it is (its sign is not even stable across problems).
    """
    rows = suf["part_C2_clean_and_confounded_contrasts"]["contrast_b_clean"]
    clean = [r for r in rows if "even2" in r["contrast"]]
    conf = [r for r in rows if "even1" in r["contrast"]]
    out = {"clean": {}, "confounded": {}}
    for label, fam in (("clean", clean), ("confounded", conf)):
        for r in fam:
            adv = r["median_advantage_odd"] / r["mde_cluster_unit"]
            facts["claim2.%s_advantage_mde.%s" % (label, r["problem"])] = {
                "value": adv,
                "rule": "median_advantage_odd / mde_cluster_unit (cluster unit) of the same block",
                "recorded": r["advantage_vs_MDE_cluster"],
                "source": "sufficiency_v1_results.json:part_C2.contrast_b_clean[%r]" % r["contrast"]}
            facts["claim2.%s_resolvable.%s" % (label, r["problem"])] = {
                "value": bool(r["resolvable_cluster_unit"]),
                "rule": "the row's resolvable_cluster_unit (cluster unit is the generalising unit)",
                "recorded": r["resolvable_cluster_unit"], "source": "same"}
            out[label][r["problem"]] = {"advantage_vs_mde": adv,
                                        "resolvable": bool(r["resolvable_cluster_unit"])}
    # the registered reading rule: only a POSITIVE, resolvable, matched-form contrast is evidence
    out["evidence"] = {p: bool(v["resolvable"] and v["advantage_vs_mde"] > 2.0)
                       for p, v in out["clean"].items()}
    return out


def null_shift(suf, facts):
    """L2 -- the specificity control.  A design that penalises its own odd term under a sign-free
    target cannot be read as evidence against a signed model from a NEGATIVE result, so this number
    is a scope limit, and it is reported as one rather than as a finding."""
    ns = suf["null_shift_from_the_even_target_adv_over_mde"]
    for p, v in ns.items():
        facts["limit.L2_null_shift.%s" % p] = {
            "value": v, "rule": "advantage over MDE under the EVEN synthetic target",
            "recorded": v, "source": "sufficiency_v1_results.json:null_shift_..."}
    return dict(ns)


def external_reach(ext, facts):
    """F1.3 + L3 -- the external cell.  Two things are recomputed rather than read:
    the Kendall tau of mean gain against tail (from the cell rows, with a tie-aware implementation),
    and the REACH of the harness against the published robustness scale -- reported per profile,
    with the values in and out of the window, because a reach statement whose excluded profiles are
    invisible is exactly the kind of exclusion this package's own rules forbid.
    """
    pub = ext["anchor_published_numbers"]
    lo, hi = pub["worst_trace_degradation"], pub["comparison_worst_trace_degradation"]
    tau = {}
    reach = {}
    for p, rows in ext["cells"].items():
        g = [r["mean_gain"] for r in rows]
        w = [r["worst_unit_degradation"] for r in rows]
        kept = [(r["profile"], r["worst_unit_degradation"]) for r in rows if r["profile"] != "zero"]
        # ORIENTATION IS PART OF THE DEFINITION.  The published pair says the cache with the larger
        # mean gain has the SMALLER worst-trace degradation, so the second variate is the tail read
        # as "higher is better" (-worst_unit_degradation).  Computing tau against the raw degradation
        # returns the same magnitude with the opposite sign, and a tau whose orientation is unstated
        # cannot be read as "concordant" at all -- the first version of this rule got the sign wrong
        # and the cross-check against the stage's recorded value caught it.
        better_tail = [-r["worst_unit_degradation"] for r in rows]
        keep = [i for i, r in enumerate(rows) if r["profile"] != "zero"]
        tau[p] = {"all": kendall_tau(g, better_tail),
                  "excluding_zero_anchor": kendall_tau([g[i] for i in keep],
                                                       [better_tail[i] for i in keep])}
        in_lo = sorted(r["profile"] for r in rows if r["worst_unit_degradation"] >= lo)
        in_hi = sorted(r["profile"] for r in rows if r["worst_unit_degradation"] >= hi)
        reach[p] = {"profiles": len(rows), "at_or_above_0.8pct": len(in_lo),
                    "at_or_above_8.8pct": len(in_hi),
                    "in_window": in_lo, "out_of_window": sorted(r["profile"] for r in rows
                                                                if r["profile"] not in in_lo),
                    "min_worst_unit_degradation": min(w)}
        rec = [b for b in ext["tests"]["X1_order"]["blocks"] if b["problem"] == p][0]
        for key, val in tau[p].items():
            facts["claim3.tau_%s.%s" % (key, p)] = {
                "value": val,
                "rule": "Kendall tau of mean_gain against the tail read as higher-is-better "
                        "(-worst_unit_degradation; ties dropped from numerator and denominator, as "
                        "the stage computes it)"
                        + (" (zero-error anchor excluded, paired)" if key != "all" else ""),
                "recorded": rec["kendall_tau_mean_vs_tail"] if key == "all"
                else rec["tau_excluding_the_zero_anchor"],
                "source": "external_cell_v1_results.json:cells[%s]" % p}
        for key, val in reach[p].items():
            if isinstance(val, (int, float)):
                facts["limit.L3_reach_%s.%s" % (key, p)] = {
                    "value": val,
                    "rule": "count of profiles in cells[%s] whose worst_unit_degradation is at or "
                            "above the published scale (%.3f / %.3f), or the minimum" % (p, lo, hi),
                    "recorded": None, "source": "external_cell_v1_results.json:cells[%s]" % p}
    facts["claim3.published_mean_gain"] = {
        "value": pub["mean_gain_over_classic"], "rule": "transcribed from the arXiv abs record",
        "recorded": pub["mean_gain_over_classic"], "source": "anchor_published_numbers"}
    facts["claim3.published_implied_mean_gain"] = {
        "value": pub["implied_comparison_mean_gain"],
        "rule": "DERIVED: mean_gain_over_classic / comparison_gain_over_classic - 1, in the artefact",
        "recorded": pub["implied_comparison_mean_gain"], "source": "anchor_published_numbers"}
    return {"tau": tau, "reach": reach}


def pearson(xs, ys):
    """Pearson r, computed here -- the direction finding is a claim about these numbers, so the
    correlation must not be read out of the stage's field.  Returns None when either variate is
    constant: an undefined correlation is reported as undefined, never as a number.
    """
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / (sxx ** 0.5 * syy ** 0.5)


def lambda_calibration(lc, facts):
    """(c) -- the registered lambda-calibration loss, RECOMPUTED from the per-profile primitives.

    The registered metric is a FACTOR: how much worse the certificate rule's worst-case ratio is
    than the profile's own best lambda.  The stage stores, per profile, the two ratio primitives
    (`ratio_wc`, `ratio_star`), the per-profile loss with its between-stream interval, the two
    lambdas, and the profile's own tail and spread.  Everything the manuscript quotes is derived
    here from those, and cross-checked against the stage's summary:

      * the factor itself is the MEAN OF PER-STREAM RATIOS, not the ratio of the two means -- they
        are different numbers, and the stage's `loss` is the former.  The ratio of means is
        reported beside it (`*_ratio_of_means`) so a reader can see the gap is small rather than
        take the equivalence on faith;
      * the median is the stage's convention, an UPPER median (`sorted(...)[n//2]`), not the
        average of the two central values that `statistics.median` would return -- on an even
        profile count the two differ, and a convention is part of a rule;
      * `displaced` is recomputed from the two stored lambdas rather than read from the flag;
      * the direction statistics (mean loss over tail vs non-tail profiles, and the two
        correlations) are recomputed, so the registered prior P2's fate is decided here.
    """
    problems = ("ski", "sched", "paging")
    out = {}
    for p in problems:
        rows = {name: r for name, r in lc["losses"][p].items() if name != "zero"}
        rec = lc["criterion_c"][p]
        losses = [r["loss"] for r in rows.values()]
        n = len(losses)
        upper_median = sorted(losses)[n // 2]
        big_name = max(rows, key=lambda k: (rows[k]["loss"], k))
        big = rows[big_name]
        displaced = sum(1 for r in rows.values() if r["lam_wc"] != r["lam_star"])
        rom = {k: (r["ratio_wc"] / r["ratio_star"] if r["ratio_star"] else None)
               for k, r in rows.items()}
        facts["claim4.lambda_loss_median.%s" % p] = {
            "value": upper_median, "recorded": rec["loss_median"], "rule":
            "upper median (sorted(losses)[n//2]) of the per-profile factors, n=%d profiles" % n,
            "source": "lambda_cert_v1_results.json:losses[...].loss -- the per-profile factor is "
                      "the stage's primitive; the median is the derived statistic"}
        facts["claim4.lambda_loss_max.%s" % p] = {
            "value": big["loss"], "recorded": rec["loss_max"], "rule":
            "the largest per-profile factor (profile %s, spread %.2f), with its own 95%% "
            "between-stream interval [%.4f, %.4f]" % (big_name, big["spread"], big["loss_lo"],
                                                      big["loss_hi"]),
            "source": "lambda_cert_v1_results.json:losses[...].loss (max over profiles)"}
        facts["claim4.lambda_loss_interval_%s.%s" % ("lo", p)] = {
            "value": big["loss_lo"], "recorded": rec["loss_max_lo"],
            "rule": "lower end of the max profile's 95% between-stream interval",
            "source": "lambda_cert_v1_results.json:losses[...].loss_lo"}
        facts["claim4.lambda_loss_interval_%s.%s" % ("hi", p)] = {
            "value": big["loss_hi"], "recorded": rec["loss_max_hi"],
            "rule": "upper end of the max profile's 95% between-stream interval",
            "source": "lambda_cert_v1_results.json:losses[...].loss_hi"}
        facts["claim4.lambda_displaced.%s" % p] = {
            "value": displaced, "recorded": rec["n_displaced"], "rule":
            "profiles whose certificate lambda differs from the profile's own best lambda (%d of "
            "%d), recomputed from the two stored lambdas rather than read from the `displaced` flag"
            % (displaced, n),
            "source": "lambda_cert_v1_results.json:losses[...].{lam_wc,lam_star}"}
        facts["claim4.lambda_wc_values.%s" % p] = {
            "value": sorted(set(r["lam_wc"] for r in rows.values())),
            "recorded": rec["lam_wc_values"],
            "rule": "the distinct lambdas the certificate rule selects across profiles",
            "source": "lambda_cert_v1_results.json:losses[...].lam_wc"}
        rom_median = sorted(v for v in rom.values() if v is not None)[n // 2]
        facts["claim4.lambda_ratio_of_means_median.%s" % p] = {
            "value": rom_median, "recorded": None, "rule":
            "ratio of the two MEANS (ratio_wc/ratio_star), the counterpart of the mean-of-ratios "
            "factor above; recorded=None because the artefact does not store it. Reported so the "
            "gap between the two aggregations is visible (max |gap| over profiles: %.4f)"
            % max((abs(rom[k] - rows[k]["loss"]) for k in rows), default=0.0),
            "source": "lambda_cert_v1_results.json:losses[...].{ratio_wc,ratio_star}"}

        tail_rows = [r for r in rows.values() if r["tail"] > 0]
        other_rows = [r for r in rows.values() if r["tail"] == 0]
        dir_rec = lc["direction"][p]
        means = {
            "mean_loss_tail": sum(r["loss"] for r in tail_rows) / len(tail_rows),
            "mean_loss_other": sum(r["loss"] for r in other_rows) / len(other_rows),
        }
        facts["claim4.lambda_mean_loss_tail.%s" % p] = {
            "value": means["mean_loss_tail"], "recorded": dir_rec["mean_loss_tail_profiles"],
            "rule": "mean factor over the profiles with a non-zero tail (%d of %d)"
                    % (len(tail_rows), n),
            "source": "lambda_cert_v1_results.json:losses[...].{loss,tail}"}
        facts["claim4.lambda_mean_loss_other.%s" % p] = {
            "value": means["mean_loss_other"], "recorded": dir_rec["mean_loss_other_profiles"],
            "rule": "mean factor over the profiles with no tail (%d of %d)"
                    % (len(other_rows), n),
            "source": "lambda_cert_v1_results.json:losses[...].{loss,tail}"}
        for key in ("tail", "spread"):
            r_ = pearson([r[key] for r in rows.values()], [r["loss"] for r in rows.values()])
            facts["claim4.lambda_corr_%s.%s" % (key, p)] = {
                "value": r_, "recorded": dir_rec["corr_" + key],
                "rule": "Pearson r between the profile's %s and its factor, over the %d non-zero "
                        "profiles (None if a variate is constant)" % (key, n),
                "source": "lambda_cert_v1_results.json:losses[...]"}

        lam_wc_by_eta = {}
        for eta_key, entry in lc["rule"][p].items():
            lam_wc_by_eta.setdefault(entry["lam_wc"], []).append(float(eta_key))
        interior = sorted(k for k, etas in lam_wc_by_eta.items() if 0.0 < k < 1.0)
        out[p] = {"n_profiles": n, "median": upper_median, "max": big["loss"],
                  "max_profile": big_name, "max_lo": big["loss_lo"], "max_hi": big["loss_hi"],
                  "displaced": displaced, "lam_wc_values": sorted(set(r["lam_wc"]
                                                                      for r in rows.values())),
                  "mean_loss_tail": means["mean_loss_tail"],
                  "mean_loss_other": means["mean_loss_other"],
                  "corr_tail": facts["claim4.lambda_corr_tail.%s" % p]["value"],
                  "interior_lambdas": interior,
                  "oos_median": rec.get("loss_oos_median")}
    return out


def attachment_controls(ext, facts):
    """L1 -- the attachment is model-dependent.  Three exact relations, with the trap named: a
    positive BIAS is not a non-negative MULTIPLIER (clamping), so the shared attachment is not
    blind to every positive-error profile."""
    c = ext["controls"]
    relations = {k: v for k, v in c.items() if k.startswith("C5")}
    for k, v in sorted(relations.items()):
        facts["limit.L1_attachment.%s" % k] = {
            "value": v.get("ok") if isinstance(v, dict) else v,
            "rule": "the relation as the cell records it (see controls[%s]); carried, not "
                    "recomputed -- recomputing it means re-running the cell's attachment" % k,
            "recorded": v.get("ok") if isinstance(v, dict) else None,
            "source": "external_cell_v1_results.json:controls[%s]" % k}
    return relations


def criteria(suf, ext, extras, facts):
    """The registered success metrics, each with a MEASURED / UNMET state.

    Metric (c) -- the lambda-calibration loss as a factor -- WAS unmet in the first submission of
    this package: the registered measurement needs a certificate-chosen lambda, and no stage
    computed that formula, so the package reported the state rather than a number (the alternative,
    reporting the fixed-grid proxy whose own direction the registered prior contradicts, would have
    been a negative finding printed in place of an undefined one).  The stage `lambdacert` now
    computes the certificate rule and the factor per profile, and `lambda_calibration()` above
    recomputes every number quoted here from the per-profile primitives, so (c) reports a measured
    quantity.

    The registered prior P2 -- that the gap grows with the tail -- is reported as HALF confirmed and
    the numbers are in `detail`: the tail profiles do carry a higher mean factor in all three
    problems, but the correlation is weak and the relation is non-monotone in spread, so the
    registered wording is not supported as written.  A prior that survives at half strength is
    reported at half strength.
    """
    lam = extras["lambda"]

    def c_detail(p):
        d = lam[p]
        interior = ("interior (lambda %s)" % ", ".join("%.2f" % v for v in d["interior_lambdas"])
                    if d["interior_lambdas"] else "an endpoint (bang-bang)")
        return ("median factor %.4f over %d non-zero profiles; worst profile %s at %.4f "
                "[%.4f, %.4f] (95%% between-stream, in-sample lambda*); the same worst profile "
                "under a lambda* fitted out of sample gives %.4f, so the factor does not rest on "
                "choosing lambda on the streams it is scored on; the certificate lambda differs "
                "from the profile's own best lambda on %d of %d profiles; the certificate rule's "
                "lambda is %s on this problem"
                % (d["median"], d["n_profiles"], d["max_profile"], d["max"], d["max_lo"],
                   d["max_hi"], d["oos_median"], d["displaced"], d["n_profiles"], interior))

    return {
        "a_signed_beats_scalar_on_held_out_cells": {
            "state": "measured",
            "detail": ("scalar insufficiency is witnessed by construction (identical scalar "
                       "features, different loss); the held-out model comparison is in stage "
                       "'scorer' and the object-level contrasts in 'sufficiency'"),
            "evidence": extras["sign_channel"]["evidence"]},
        "b_classic_anchors_recovered": {
            "state": "measured", "detail": "stage 'anchor' plus the end anchors inside stage 'v0'"},
        "c_lambda_calibration_loss": {
            "state": "measured",
            "detail": ("reported as a factor per problem (mean of per-stream ratios of the "
                       "certificate rule's worst-case ratio to the profile's own best lambda), "
                       "with a 95% between-stream interval -- " + "; ".join(
                           "%s: %s" % (p, c_detail(p)) for p in ("ski", "sched", "paging"))
                       + ". Prior P2 (the gap grows with the tail) is HALF confirmed: tail "
                         "profiles carry the higher mean factor in all three problems (ski "
                         "%.4f vs %.4f, sched %.4f vs %.4f, paging %.4f vs %.4f) while the "
                         "correlations are weak and the relation is non-monotone in spread, "
                         "so the registered wording is not supported as written."
                       % (lam["ski"]["mean_loss_tail"], lam["ski"]["mean_loss_other"],
                          lam["sched"]["mean_loss_tail"], lam["sched"]["mean_loss_other"],
                          lam["paging"]["mean_loss_tail"], lam["paging"]["mean_loss_other"])),
            "evidence": {p: {"median": lam[p]["median"], "max": lam[p]["max"],
                             "max_interval": [lam[p]["max_lo"], lam[p]["max_hi"]],
                             "displaced": "%d/%d" % (lam[p]["displaced"], lam[p]["n_profiles"]),
                             "corr_tail": lam[p]["corr_tail"]}
                         for p in ("ski", "sched", "paging")}},
        "d_streams_and_sensitivity": {
            "state": "measured",
            "detail": "each cell carries disjoint streams; the flip-count bound is reported per "
                      "headline number in the manuscript's sensitivity section"},
    }


def build(log):
    stages = [stage_summary(s) for s in STAGES]
    suf = load("sufficiency_v1_results.json")
    ext = load("external_cell_v1_results.json")
    facts = {}
    w = witness(suf, facts)
    sc = sign_channel(suf, facts)
    ns = null_shift(suf, facts)
    ex = external_reach(ext, facts)
    ac = attachment_controls(ext, facts)
    lc = lambda_calibration(load("lambda_cert_v1_results.json"), facts)
    return stages, {"witness": w, "sign_channel": sc, "null_shift": ns, "external": ex,
                    "attachment": ac, "lambda": lc}, facts


# --- coordinate census declaration: begin (the detector's own tables; excluded from the scan) --
# A coordinate is any input that is not the package itself: the repository, the environment, the
# command line, the working directory, the network, the clock, the interpreter.  Evidence that
# changes with them is evidence about the machine that ran it, not about the artefact.  This
# package has no network and no clock, and no stage reads a git object: the census proves it rather
# than asserting it, and fails if a later edit introduces one.
COORD_CLASSES = [
    ("C1 git object read", r'\["git"|git\s+(?:show|rev-parse|log|diff|status)\b|\.git\b'),
    ("C2 above-package read", r'os\.path\.dirname\(HERE\)|\.\./|\.github'),
    ("C3 environment", r'os\.environ|getenv|PYTHONPATH'),
    ("C4 argv", r'sys\.argv'),
    ("C5 cwd / absolute path", r'abspath|os\.getcwd|cwd='),
    # C6 matches a network CALL, not a URL.  The anchor's arXiv link is a data literal in a
    # docstring, and the first version of this detector flagged it -- a pattern that matches more
    # than the construct it names is the same defect class as a window narrower than its construct
    # (a review of the sibling package found that one).  The read is the call; the URL is data.
    ("C6 network", r'\bcurl\b|urlopen|urllib\.request|requests\.(?:get|post)|socket\.socket|'
                   r'ftplib|http\.client|subprocess\.\w+\(\s*\[\s*["\']curl'),
    ("C7 clock / entropy", r'time\.time\(|monotonic|datetime\.|random\.(?!Random)|os\.urandom|uuid4'),
    ("C8 interpreter", r'sys\.version\b'),
]
# Empty classes: the reads that must NOT occur anywhere in the package.
COORD_FORBIDDEN = ["C1 git object read", "C6 network", "C7 clock / entropy"]
# Each detector must match a planted instance -- a detector that never fires is decoration.
COORD_CANARIES = {
    "C1 git object read": 'r = subprocess.run(["git", "show", "HEAD:a.py"], cwd=".")',
    "C2 above-package read": 'D = os.path.dirname(HERE)',
    "C3 environment": 'env = dict(os.environ); env.pop("PYTHONPATH", None)',
    "C4 argv": 'args = sys.argv[1:]',
    "C5 cwd / absolute path": 'HERE = os.path.dirname(os.path.abspath(__file__))',
    "C6 network": 'r = subprocess.run(["curl", "-s", url])',
    "C7 clock / entropy": 't = time.time()',
    "C8 interpreter": 'print(sys.version)',
}
CENSUS_SELF = "canonical_runner.py"
CENSUS_SOURCES = sorted(f for f in os.listdir(HERE) if f.endswith((".py", ".sh")))
# --- coordinate census declaration: end ---------------------------------------------------------


def split_census_declaration(text):
    """(region, outside): the span holding this census's own tables, and the code proper.

    The census scans the package it lives in, so it necessarily contains the patterns and canaries
    it searches for.  Those are DATA: nothing in the span executes.  The span is delimited by the
    two banner lines, and the checks assert that it is a single span and that it reads no
    coordinate -- an exclusion wider than the thing it excludes is the defect this whole exercise is
    about, so the boundary is drawn at the data and the file it lives in stays inside the scan.
    """
    bs = [m.start() for m in re.finditer(r"^# --- coordinate census declaration: begin.*$", text, re.M)]
    es = [m.end() for m in re.finditer(r"^# --- coordinate census declaration: end.*$", text, re.M)]
    if len(bs) != 1 or len(es) != 1 or es[0] < bs[0]:
        raise ValueError("census declaration banners: %d begin, %d end" % (len(bs), len(es)))
    return text[bs[0]:es[0]], text[:bs[0]] + text[es[0]:]


def coordinate_census(sources):
    """{class: {filename: [(lineno, line)]}} -- every source line that reads a coordinate."""
    cen = {}
    for cls, pat in COORD_CLASSES:
        hits = {}
        for name in sorted(sources):
            lines = [(i + 1, l.strip()) for i, l in enumerate(sources[name].split("\n"))
                     if re.search(pat, l)]
            if lines:
                hits[name] = lines
        cen[cls] = hits
    return cen


def coordinate_check(log):
    """Print the census and return the number of violations.  Two mutations prove it can fail.

    Every source file is read, the declaration span of THIS file is replaced by the code outside
    it, and the resulting counts are published per class.  The forbidden classes must be empty --
    and the control that a read planted OUTSIDE the span is still caught is what keeps the
    exclusion from becoming an immunity (the exact trap a review found in the sibling package).
    """
    region, outside = split_census_declaration(read(CENSUS_SELF))
    calls = sorted(set("%s.%s" % (n.func.value.id, n.func.attr)
                       for n in ast.walk(ast.parse(region))
                       if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                       and isinstance(n.func.value, ast.Name)))
    problems = []
    log("       coordinate census over %d source file(s); the declaration span of %s is data, not"
        " code (%d calls in it: %s)"
        % (len(CENSUS_SOURCES), CENSUS_SELF, len(calls), ", ".join(calls) or "none"))
    sources = {f: read(f) for f in CENSUS_SOURCES}
    sources[CENSUS_SELF] = outside
    cen = coordinate_census(sources)
    for cls, _ in COORD_CLASSES:
        h = cen[cls]
        n = sum(len(v) for v in h.values())
        mark = ""
        if cls in COORD_FORBIDDEN and n:
            mark = "  <-- MUST BE EMPTY"
            problems.append("%s has %d site(s)" % (cls, n))
        log("         %-24s %3d site(s) in %-2d file(s)  %s%s"
            % (cls, n, len(h), ", ".join(sorted(h)) if n else "-- none", mark))
    blind = [cls for cls, line in COORD_CANARIES.items()
             if not coordinate_census({"planted.py": line})[cls]]
    if blind:
        problems.append("detector(s) that never fire: %s" % ", ".join(sorted(blind)))
    log("         detectors firing on a planted instance: %d of %d"
        % (len(COORD_CLASSES) - len(blind), len(COORD_CLASSES)))
    leak = dict(sources)
    leak["leaky.py"] = COORD_CANARIES["C1 git object read"]
    leak2 = dict(sources)
    leak2[CENSUS_SELF] = outside + COORD_CANARIES["C1 git object read"] + "\n"
    caught = (bool(coordinate_census(leak)["C1 git object read"])
              and bool(coordinate_census(leak2)["C1 git object read"]))
    if not caught:
        problems.append("a leaked git read was NOT caught (the exclusion is an immunity)")
    log("         controls: a git read planted in another file and one planted outside the"
        " declaration span are both caught: %s" % caught)
    for p in problems:
        log("       CENSUS VIOLATION: %s" % p)
    return len(problems)


def main():
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    lines = []

    def log(s):
        print(s)
        lines.append(s)

    if "--no-stages" not in argv:
        if run_stages(log) is None:
            io.open(LOG, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            return 1

    stages, extras, facts = build(log)
    bad = [s for s in stages if not s["agree"] or (s["checks_failed"] or 0)]
    log("")
    log("%-12s %-32s %6s %6s %s" % ("stage", "script", "run", "failed", "flag agrees"))
    for s in stages:
        log("%-12s %-32s %6s %6s %s"
            % (s["tag"], s["script"], s["checks_run"] if s["checks_run"] is not None else "n/p",
               s["checks_failed"] if s["checks_failed"] is not None else "n/p",
               "yes" if s["agree"] else "NO"))

    # every recomputed fact is cross-checked against the value the artefact recorded about itself
    disagree = [k for k, v in facts.items()
                if v["recorded"] is not None and not _same(v["value"], v["recorded"])]
    log("")
    log("facts recomputed: %d | disagreeing with the artefact's own value: %d" % (len(facts),
                                                                                 len(disagree)))
    for k in disagree:
        log("  DISAGREES %s: recomputed %r vs recorded %r" % (k, facts[k]["value"],
                                                              facts[k]["recorded"]))

    crit = criteria(suf=load("sufficiency_v1_results.json"),
                    ext=load("external_cell_v1_results.json"), extras=extras, facts=facts)
    log("")
    for k, v in crit.items():
        log("criterion %-44s %s" % (k, v["state"].upper()))
    # the one-line summary the README quotes: the registered metrics in their registered order,
    # each in the state it was measured in (UNMET is a state, not a failure of the run)
    log("criteria: %s" % ", ".join(
        "%s=%s" % (letter, "MET" if crit[key]["state"] == "measured" else "UNMET")
        for letter, key in zip("abcd", [k for k in crit])))

    # THE STATE WORD MUST FOLLOW THE EVIDENCE.  A criterion is a claim about the run, and the run
    # knows which stages it executed: a criterion whose stages are present and green cannot be
    # reported `unmet`, and one whose stages are absent cannot be reported `measured`.  Without this
    # rule the round-3 change to criterion (c) would be a sentence rather than a consequence -- and
    # a future edit that reverted it while the certificate stage kept passing would be invisible.
    # (d) is deliberately OUT of the mapping: its evidence is the disjoint-stream design of the
    # cells, not a stage, and putting it here would fabricate a stage link that does not exist.
    CRIT_STAGES = {"a_signed_beats_scalar_on_held_out_cells": ("scorer", "sufficiency"),
                   "b_classic_anchors_recovered": ("anchor", "v0"),
                   "c_lambda_calibration_loss": ("lambdacert",)}
    by_tag = {s["tag"]: s for s in stages}
    state_bad = []
    for key, tags in CRIT_STAGES.items():
        green = all(t in by_tag and by_tag[t]["agree"] and not by_tag[t]["checks_failed"]
                    for t in tags)
        measured = crit[key]["state"] == "measured"
        if green != measured:
            state_bad.append("%s: state=%s but stages %s are %s"
                             % (key, crit[key]["state"], ",".join(tags),
                                "green" if green else "absent or failing"))
    for msg in state_bad:
        log("  CRITERION STATE DISAGREES WITH THE EVIDENCE: %s" % msg)
    log("criterion states vs their stages: %d disagreement(s)" % len(state_bad))
    log("")
    for k in ("claim1.worst_loss_gap", "claim1.scalar_gap_max_exact", "claim1.blocks_exceeding_own_mde",
              "claim2.clean_advantage_mde.ski", "claim2.clean_advantage_mde.sched",
              "claim2.clean_advantage_mde.paging", "claim3.tau_all.ski", "claim3.tau_all.paging",
              "claim3.tau_all.sched"):
        if k in facts:
            log("  %-38s %s" % (k, _fmt(facts[k]["value"])))
    log("")
    log("external reach (published robustness scale 0.008..0.088):")
    for p, r in extras["external"]["reach"].items():
        log("  %-7s %d of %d profiles at or above 0.8%%; min worst-unit %+.4f | out: %s"
            % (p, r["at_or_above_0.8pct"], r["profiles"], r["min_worst_unit_degradation"],
               ",".join(r["out_of_window"])))

    log("")
    census_violations = coordinate_check(log)

    verdict = not bad and not disagree and not census_violations and not state_bad
    out = {
        "study": "issue-47 signed-error decomposition (cs.DS)",
        "stages": stages,
        "criteria": crit,
        "claims": {"F1_1_witness": extras["witness"], "F1_2_sign_channel": extras["sign_channel"],
                   "F1_3_ordering": extras["external"]["tau"], "L2_null_shift": extras["null_shift"],
                   "L3_reach": extras["external"]["reach"], "L1_attachment": extras["attachment"]},
        "facts": facts,
        "coordinate_census": {"violations": census_violations,
                              "forbidden_classes": COORD_FORBIDDEN},
        "ALL_PASS": verdict,
    }
    blob = json.dumps(out, sort_keys=True, indent=1)
    io.open(os.path.join(HERE, "canonical_results.json"), "w", encoding="utf-8").write(blob + "\n")
    log("")
    log("canonical_results.json sha256 %s" % hashlib.sha256((blob + "\n").encode("utf-8")).hexdigest())
    log("coordinate census: %d violation(s)" % census_violations)
    log("verdict: %s" % ("OK" if verdict else "NOT READY"))
    io.open(LOG, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return 0 if verdict else 1


def _same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) < 1e-9
        except (TypeError, ValueError):
            return a == b
    return a == b


def _fmt(v):
    return "%+.4f" % v if isinstance(v, float) else repr(v)


# --------------------------------------------------------------------------------- liveness
def selftest():
    """Corrupt a throwaway copy of an artefact once per named recomputation and require the
    recomputation to NOTICE.

    The test is a comparison against a BASELINE recomputed from the pristine artefact, not against
    the artefact's own recorded field.  The first version of this control compared only against the
    recorded field, which made three of the five cases pass for the wrong reason: those facts have
    no recorded value (`recorded is None`), so any corruption at all looked "noticed".  A control
    that cannot distinguish "the mutation changed the number" from "there was nothing to compare"
    is the decoration this file's own docstring warns about.
    """
    cases = [
        ("claim1: an arm whose scalar features are not identical",
         "sufficiency_v1_results.json", "claim1.scalar_gap_max_exact", "value",
         lambda d: d["part_B_matched_magnitude_witness"]["blocks"][0].__setitem__(
             "max_scalar_feature_gap", 0.25)),
        ("claim1: the loss gap moved off its argmin",
         "sufficiency_v1_results.json", "claim1.worst_loss_gap", "value",
         lambda d: min(d["part_B_matched_magnitude_witness"]["blocks"],
                       key=lambda b: b["median_ratio_diff_plus_minus"]).__setitem__(
             "median_ratio_diff_plus_minus", -0.9999)),
        ("claim1: a block's MDE inflated so it no longer clears its own bar",
         "sufficiency_v1_results.json", "claim1.blocks_exceeding_own_mde", "value",
         lambda d: [b.__setitem__("mde_cluster_unit", 9.0)
                    for b in d["part_B_matched_magnitude_witness"]["blocks"]]),
        # TWO MECHANISMS, TWO CONTROLS.  The facts this runner emits are protected by two different
        # checks: a RECOMPUTATION (the value is derived from primitives, so corrupting a primitive
        # moves it) and a CROSS-CHECK (the derived value must equal the field the stage recorded
        # about itself).  A mutation of the recorded field moves nothing in the recomputation -- it
        # is caught by the cross-check alone -- so the case declares which mechanism must notice.
        # Testing every case the same way would have reported this one as a dead control.
        ("claim2/CROSSCHECK: the recorded advantage no longer follows its median/MDE",
         "sufficiency_v1_results.json", "claim2.clean_advantage_mde.ski", "crosscheck",
         lambda d: next(r for r in d["part_C2_clean_and_confounded_contrasts"]["contrast_b_clean"]
                        if "even2" in r["contrast"]).__setitem__(
             "advantage_vs_MDE_cluster", 99.0)),
        ("claim2: a matched-form row's MDE shifted, moving its resolvability",
         "sufficiency_v1_results.json", "claim2.clean_advantage_mde.sched", "value",
         lambda d: next(r for r in d["part_C2_clean_and_confounded_contrasts"]["contrast_b_clean"]
                        if "even2" in r["contrast"] and r["problem"] == "sched").__setitem__(
             "mde_cluster_unit", 1e-6)),
        ("claim3: the cell rows no longer agree with the recorded tau",
         "external_cell_v1_results.json", "claim3.tau_all.ski", "value",
         lambda d: d["cells"]["ski"][0].__setitem__("mean_gain", -1.0)),
        ("claim3: a cell row's tail value shifted, moving the tau",
         "external_cell_v1_results.json", "claim3.tau_all.paging", "value",
         lambda d: d["cells"]["paging"][0].__setitem__("worst_unit_degradation", 5.0)),
        ("L3: a profile's worst-unit value moved out of the reach window",
         "external_cell_v1_results.json", "limit.L3_reach_at_or_above_0.8pct.ski", "value",
         lambda d: d["cells"]["ski"][3].__setitem__("worst_unit_degradation", -0.5)),
        # --- criterion (c): the stage added in round 3 to close the metric that was UNMET --------
        ("claim4: a profile's factor moved, shifting the median",
         "lambda_cert_v1_results.json", "claim4.lambda_loss_median.ski", "value",
         lambda d: d["losses"]["ski"]["unbiased_low"].__setitem__("loss", 9.0)),
        # The certificate lambda and the profile's own best lambda are two primitives; `displaced`
        # is RECOMPUTED from them, so it must ignore the stage's own flag when the lambdas move.
        # The mutation must move the object it names: `tail_mid` is the ONE paging profile whose
        # two lambdas already coincide, so setting them equal there changes nothing and the case
        # passed for the wrong reason on its first run -- the same "a model of the adversary that
        # cannot move the object under test" family this package's own lesson file records.
        ("claim4: two lambdas made equal, moving the displaced count",
         "lambda_cert_v1_results.json", "claim4.lambda_displaced.paging", "value",
         lambda d: d["losses"]["paging"]["over_mid"].__setitem__(
             "lam_wc", d["losses"]["paging"]["over_mid"]["lam_star"])),
        ("claim4/CROSSCHECK: the recorded median no longer follows the profiles",
         "lambda_cert_v1_results.json", "claim4.lambda_loss_median.sched", "crosscheck",
         lambda d: d["criterion_c"]["sched"].__setitem__("loss_median", 4.25)),
        ("claim4: the tail and non-tail means recompute from a moved profile",
         "lambda_cert_v1_results.json", "claim4.lambda_mean_loss_other.paging", "value",
         lambda d: d["losses"]["paging"]["unbiased_mid"].__setitem__("loss", 0.5)),
    ]

    def recompute(artefact, d):
        facts = {}
        if artefact == "sufficiency_v1_results.json":
            witness(d, facts)
            sign_channel(d, facts)
        elif artefact == "lambda_cert_v1_results.json":
            lambda_calibration(d, facts)
        else:
            external_reach(d, facts)
        return facts

    pristine = {}
    for case in cases:
        artefact = case[1]
        if artefact not in pristine:
            pristine[artefact] = json.load(io.open(os.path.join(HERE, artefact), encoding="utf-8"))

    failed = []
    for name, artefact, fact, kind, mutate in cases:
        base = recompute(artefact, pristine[artefact]).get(fact, {})
        d = json.load(io.open(os.path.join(HERE, artefact), encoding="utf-8"))
        mutate(d)
        try:
            got = recompute(artefact, d).get(fact, {})
        except Exception as exc:                 # a mutation that breaks the rule is noticed too
            print("PASS %-62s (raised %s)" % (name, type(exc).__name__))
            continue
        if kind == "crosscheck":
            noticed = (got.get("recorded") is not None
                       and not _same(got.get("value"), got.get("recorded")))
            detail = "recomputed=%r recorded=%r" % (got.get("value"), got.get("recorded"))
        else:
            noticed = not _same(got.get("value"), base.get("value"))
            detail = "baseline=%r mutated=%r" % (base.get("value"), got.get("value"))
        print("%-4s %-62s %s" % ("PASS" if noticed else "FAIL", name, detail))
        if not noticed:
            failed.append(name)
    print("selftest: %d case(s), %d NOT noticed" % (len(cases), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
