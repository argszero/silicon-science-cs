#!/usr/bin/env python3
"""Assemble issue #50's manuscript: resolve every number, number every citation.

Two rules live here, and both are enforced rather than intended.

**No number is typed into the prose.** Every measured quantity in the parts is a
`{{fact}}` placeholder (optionally `{{fact|.3f}}`), and `FACTS` below is the single owner
of each: a fact is computed from a committed artefact under `artefacts/`, and a placeholder
that does not resolve is a FAILED ASSEMBLY, never an empty string. A number typed into the
prose is a claim with no owner, and this package has already paid for that twice.

**Citations are numbered by first use, and the numbering is derived, not maintained.**
`[@key]` becomes `[n]` in order of first appearance in the parts; the order is written to
`refs_order.json`, which the reference layer's builder consumes, so the bibliography cannot
disagree with the body about either the order or the membership. Three properties are
checked and each fails the assembly:

  * every cited key has a row in the selection layer;
  * every row of the layer is cited at least once (quality-bar item 13: an entry that never
    appears in the body is padding and does not count toward the 100-reference floor);
  * both counters are printed, with their common denominator.

Usage:
Run order (each file has ONE writer, and each `--check` names its own object):
  assemble.py           -> manuscript.md BODY + refs_order.json
  refs_build_display.py -> references.json + refs_display.json, in the order assemble.py derived
  refs_render.py        -> the `## References` SECTION in manuscript.md

  python3 assemble.py            write the body and refs_order.json
  python3 assemble.py --check    render and compare with the committed manuscript.md
  python3 assemble.py --selftest liveness of the quantified-sentence collector above
                                 (each rule planted in a throwaway copy of the package)
"""
import ast
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "artefacts")
PARTS = ["manuscript_part1.md",
         "manuscript_part2.md",
         "manuscript_part3.md",
         "manuscript_part4.md"]          # grown as the parts land
MS = os.path.join(HERE, "manuscript.md")
ORDER = os.path.join(HERE, "refs_order.json")
SELECTION = os.path.join(ART, "refs_selection_v50.json")
VERIFIED = os.path.join(ART, "refs_verified_v50.json")

# A bracket may carry several keys (`[@a;@b]`).  The first version of this pattern saw only one
# key per bracket, and all three of the citation checks below are computed from it -- so a
# multi-key bracket was not numbered, not counted, and not reported.  The post-condition after
# numbering is what makes that class of miss a FAILED ASSEMBLY instead of a silent one.
CITE = re.compile(r"\[@([A-Za-z0-9_\-]+)((?:\s*;\s*@[A-Za-z0-9_\-]+)*)\]")
KEY_IN = re.compile(r"[A-Za-z0-9_\-]+")
# A fact name may carry capitals (`rho_star_A16`): the first version of this pattern was
# `[a-z0-9_]+`, so placeholders naming a capitalised fact were never matched -- not resolved
# and, worse, not REPORTED, because the report was taken over the matches. A placeholder the
# pattern cannot see is a placeholder nobody owns.
PH = re.compile(r"\{\{([A-Za-z0-9_]+)(\|[^}]+)?\}\}")


def load(name):
    return json.load(io.open(os.path.join(ART, name), encoding="utf-8"))


def fam(doc, agents, field="x_star"):
    for f in doc["families"]:
        if f["agents"] == agents:
            return f["crossing_rho_spec"][field]
    raise KeyError("no family for agents=%s" % agents)


def cell(doc, key):
    for c in doc["cells"]:
        if c["key"] == key:
            return c
    raise KeyError("no variant cell " + key)


# --- the one owner of every number the manuscript prints -----------------------
def build_facts():
    sel = load("refs_selection_v50.json")["rows"]
    ver = {r["key"]: r for r in load("refs_verified_v50.json")["rows"]}
    h100 = load("boundary_v2_h100.json")
    var = load("variant_v1.json")
    fix = load("fixedpoint_v1.json")

    n_a16, n_a96 = fam(h100, 16), fam(h100, 96)
    c = cell(var, "h0.50/c4")
    within = sum(1 for r in fix["same_cell"] if abs(r["d_rho_spec"]) <= fix["tolerance"])
    facts = {
        # how many of this manuscript's references are 2026 speculation-for-agents works
        "n_2026_speculation_works": lambda: sum(
            1 for r in sel if r["section"] == "S2.2" and ver[r["key"]].get("record_year") == 2026),
        # the boundary at h = 1.0, and the span the pool size buys
        "rho_star_A16": lambda: n_a16,
        "rho_star_A96": lambda: n_a96,
        "rho_star_span": lambda: abs(n_a16 - n_a96),
        # the matched-parallelism control: the share of the informed gain a blind
        # schedule of the SAME width already buys = 1 - F, at one declared cell
        "blind_share_h050": lambda: 1.0 - c["F"]["mean"],
        # the closed form, compared in the same coordinate (the secondary reading)
        "fix_within_tol_pct": lambda: 100.0 * within / len(fix["same_cell"]),
    }
    facts.update(build_design_facts())
    facts.update(build_results_facts())
    facts.update(build_package_facts())
    return facts



# --- section 3's numbers: the instrument's own declarations, read from the artefacts -----------
def build_design_facts():
    """Every quantity section 3 prints, each computed from a committed artefact.

    Two of these are read from a file rather than from a JSON: the Pareto tail index is read from the
    code that draws it, and the `h` grid is read from the boundary files' own names, each of which
    states the value it holds (`boundary_v2_h050.json` holds h = 0.50).  A number typed into the prose
    is a claim with no owner; a number read from the artefact that carries it has one.
    """
    iv = load("instrument_v0_results.json")
    b100 = load("boundary_v2_h100.json")
    var = load("variant_v1.json")
    dec = load("decompose_v1_h100.json")
    tail = load("tail_v1_h100.json")
    pred = load("predsplit_v1.json")
    side = load("sideeffect_v1.json")
    mech = load("mechanism_v1.json")
    fix = load("fixedpoint_v1.json")
    ext = load("external_v1.json")
    src = io.open(os.path.join(ART, "instrument_v0.py"), encoding="utf-8").read()

    cfg = iv["config"]
    a1 = iv["anchors"]["A1/M-M-1-mean-sojourn"]["detail"]
    a3 = iv["anchors"]["A3/zero-contention-hiding-limit"]["detail"]
    a4 = iv["anchors"]["A4/benefit-falls-across-the-saturated-half"]["detail"]
    # the boundary files name their own h: ..._h050.json holds h = 0.50 (hundredths)
    hs = sorted(int(f.split("_h")[1][:3]) / 100.0 for f in os.listdir(ART)
                if f.startswith("boundary_v2_h") and f.endswith(".json"))
    m = re.search(r"(?m)^\s*alpha = ([0-9.]+)", src)
    if m is None:
        raise RuntimeError("the Pareto tail index is not readable from instrument_v0.py")
    return {
        # the instrument's own configuration
        "think_mean": lambda: cfg["mT"],
        "service_mean": lambda: cfg["mS"],
        "hiding_limit": lambda: cfg["mT"] * cfg["mS"] / (cfg["mT"] + cfg["mS"]),
        "pareto_alpha": lambda: float(m.group(1)),
        "h_oracle_value": lambda: max(hs),
        # the anchors
        "n_anchors": lambda: len(iv["anchors"]),
        "n_anchors_ok": lambda: sum(1 for a in iv["anchors"].values() if a["ok"]),
        "a1_levels_n": lambda: len(cfg["a1_levels"]),
        "a1_n": lambda: cfg["a1_n"],
        "a1_tol": lambda: cfg["a1_tol"],
        "a1_max_rel_error": lambda: max(d["rel_error"] for d in a1),
        "a3_measured": lambda: a3["benefit"],
        "a3_rel_error": lambda: a3["rel_error"],
        "a4_rise_rho": lambda: a4["low_contention_rises_at"][0],
        # the draw discipline
        "draw_prefix_validated": lambda: b100["draw_prefix"]["derivation_validated"],
        "draw_prefix_checked": lambda: b100["draw_prefix"]["checked"],
        "draw_prefix_tol": lambda: b100["draw_prefix"]["derivation_tol"],
        # the grids
        "boundary_pool_list": lambda: ", ".join(str(f["agents"]) for f in b100["families"]),
        "boundary_h_values": lambda: ", ".join("%.2f" % h for h in hs),
        "boundary_seeds": lambda: len(b100["seeds"]),
        "boundary_tol": lambda: b100["matched_rho"]["tol"],
        "boundary_matched_pairs": lambda: b100["matched_rho"]["n_pairs"],
        "boundary_matched_disagreeing": lambda: b100["matched_rho"]["n_disagreeing"],
        "variant_h_values": lambda: ", ".join("%.2f" % v for v in var["h_grid"]),
        "variant_c_values": lambda: ", ".join(str(c) for c in var["c_grid"]),
        "variant_cells": lambda: len(var["cells"]),
        "variant_seeds": lambda: len(var["seeds"]),
        "decompose_cells": lambda: len(dec["cells"]),
        "decompose_seeds": lambda: len(dec["seeds"]),
        "tail_families": lambda: len(tail["families"]),
        "tail_seeds": lambda: len(tail["seeds"]),
        "predsplit_seeds": lambda: len(pred["seeds"]),
        "sideeffect_families": lambda: len(side["families"]),
        "sideeffect_seeds": lambda: len(side["seeds"]),
        "sideeffect_shrink_rows": lambda: len(side["shrinkage"]),
        "sideeffect_not_located": lambda: sum(1 for r in side["shrinkage"] if r["not_located"]),
        "mechanism_groups": lambda: len(mech["groups"]),
        "mechanism_seeds": lambda: len(mech["seeds"]),
        "fixedpoint_cells": lambda: len(fix["same_cell"]),
        # RC3 (review round 1, `major`): both sides of "18 of 18 cells were excluded" were
        # `len(fix["excluded"])`.  The denominator is now the count the instrument records for
        # what it EVALUATED (pairs that produced a boundary + pairs that could not), a field
        # written by a different expression -- so a run that excluded five of eighteen reads
        # "5 of 18".  The unit is a swept (family, width) PAIR, not a cell: the same package
        # prints its 141 same-cell rows separately.
        "fixedpoint_evaluated": lambda: fix["verdict"]["n_evaluated"],
        "fixedpoint_excluded": lambda: fix["verdict"]["n_excluded"],
        "fixedpoint_tol": lambda: fix["tolerance"],
        "fixedpoint_min_fraction": lambda: fix["min_fraction"],
        "external_cells": lambda: ext["summary"]["n_cells"],
    }



# --- section 4's numbers: the registered criteria, read from the artefacts that decided them ----
def build_results_facts():
    """Every quantity section 4 prints, each computed from a committed artefact.

    Section 4 is the section whose job is to report the *registered* criteria in their registered
    order, each as met or as unmet with the reason.  All of it is read here: a number in this section
    that no artefact carries would be the one kind of sentence this paper must not contain.
    """
    b100 = load("boundary_v2_h100.json")
    tail = load("tail_v1_h100.json")
    var = load("variant_v1.json")
    pred = load("predsplit_v1.json")
    side = load("sideeffect_v1.json")
    fix = load("fixedpoint_v1.json")
    ext = load("external_v1.json")
    mech = load("mechanism_v1.json")
    dec = load("decompose_v1_h100.json")

    rows = [r for f in b100["families"] for r in f["rows"]]
    fam16 = [f for f in b100["families"] if f["agents"] == 16][0]
    fam96 = [f for f in b100["families"] if f["agents"] == 96][0]
    fs = b100["families"]
    d16 = [f for f in tail["p2_first_half"]["per_family"] if f["agents"] == 16][0]
    dmax = max(tail["p2_first_half"]["per_family"], key=lambda f: abs(f["delta"]["mean"]))
    s2 = {f["agents"]: f for f in tail["p2_second_half_step2"]["per_family"]}
    var_cells = {c["key"]: c for c in var["cells"]}
    pf = [f for fam_list in pred["families"].values() for f in fam_list]
    v4 = side["verdicts"]
    m4b = side["m4b"][0]["cells"][0]
    ll = side["load_law"]["load_to_reach"]["groups"]
    sec = fix["verdict"]
    es = ext["summary"]

    # -- the six registered criteria's own verdicts, DERIVED here rather than typed anywhere -------
    # Section 4.1's summary says which criteria are unmet, and that sentence is a claim about the six
    # registered tests -- so the artefacts that decided the tests own it.  Three of the six carry a
    # verdict a run wrote (P3a's threshold, the fixed point's status, the external cell's status); the
    # other three are decided by a rule over the artefact's own numbers (does the committed window
    # cover the registered +/-5% band; is any mean-matched family's separation at least the registered
    # 0.15 with an interval that excludes zero).  The prose may not disagree with what is computed
    # here, and the assembler prints the whole table so a reader sees the derivation, not only its
    # effect.
    def criteria_status():
        band_lo = min(r["benefit_pct"] for r in rows)
        band_hi = max(r["benefit_pct"] for r in rows)
        sharpness_measured = band_lo <= -5.0 and band_hi >= 5.0
        located_first_half = b100["direction"]["rho_spec"]["n_located"] == len(fs)
        separation_met = any(abs(f["delta"]["mean"]) >= 0.15 and (f["delta"]["ci"][0] > 0.0
                                                                  or f["delta"]["ci"][1] < 0.0)
                             for f in tail["p2_first_half"]["per_family"])
        return {
            "i": "met" if (sharpness_measured and located_first_half)
                 else ("part" if located_first_half else "outright"),
            "ii": "met" if separation_met else "outright",
            "iii": "met" if var["verdicts"]["P3a"].startswith("CONFIRMED") else "outright",
            "iv": "met" if (v4["P4a"]["verdict"] == "CONFIRMED"
                            and v4["P4c"]["verdict"] == "CONFIRMED") else "outright",
            "v": "met" if sec["status"] != "UNMET" else "outright",
            "vi": "met" if ext["metric_f"]["status"] == "MET" else "outright",
        }

    crit = criteria_status()

    return {
        # -- (i) the boundary, cell by cell
        "b_families_located": lambda: b100["direction"]["rho_spec"]["n_located"],
        # RC2 (review round 1, `major`): the numerator USED to be `{{b_families_located}} of
        # {{b_families_located}}` -- one placeholder on both sides, so the ratio could only ever
        # read "N of N" and this is the outcome sentence of registered criterion (i).  The
        # denominator is the swept family count, recorded beside it in the same artefact.
        "b_families_total": lambda: b100["direction"]["rho_spec"]["n_families"],
        "b_families_ambiguous": lambda: len(b100["direction"]["rho_spec"]["ambiguous"]),
        "rho_star_serial_A16": lambda: fam16["crossing_rho_serial"]["x_star"],
        "rho_star_serial_A96": lambda: fam96["crossing_rho_serial"]["x_star"],
        "rho_interval_width": lambda: b100["direction"]["rho_spec"]["mean_interval_width"],
        "rho_span_over_interval": lambda: b100["direction"]["rho_spec"]["span_over_interval"],
        "rho_two_sample_delta": lambda: b100["direction"]["rho_spec"]["two_sample_delta"]["delta"],
        "rho_two_sample_ci_lo": lambda: b100["direction"]["rho_spec"]["two_sample_delta"]["ci"][0],
        "rho_two_sample_ci_hi": lambda: b100["direction"]["rho_spec"]["two_sample_delta"]["ci"][1],
        # the artefact records `monotone_decreasing: false`, and it is right where the prose
        # said "falls as the pool grows": A = 48 and A = 64 differ by a rise inside the mean
        # interval.  Both values and their difference are bound here so the sentence can state
        # the caveat instead of a trend word wider than the evidence.
        "rho_star_A48": lambda: [f for f in fs if f["agents"] == 48][0]["crossing_rho_spec"]["x_star"],
        "rho_star_A64": lambda: [f for f in fs if f["agents"] == 64][0]["crossing_rho_spec"]["x_star"],
        "rho_rise_A48_A64": lambda: ([f for f in fs if f["agents"] == 64][0]["crossing_rho_spec"]["x_star"]
                                     - [f for f in fs if f["agents"] == 48][0]["crossing_rho_spec"]["x_star"]),
        "window_benefit_max": lambda: max(r["benefit_pct"] for r in rows),
        "window_benefit_min": lambda: min(r["benefit_pct"] for r in rows),
        "bracket_width_min": lambda: min(f["crossing_rho_spec"]["width"] for f in fs),
        "bracket_width_max": lambda: max(f["crossing_rho_spec"]["width"] for f in fs),
        # the windows bound the fall: a family's WHOLE observed benefit range, from its own
        # positive maximum to below zero, happens inside its own rho window.
        "win_rho_span_max": lambda: max(max(r["rho_spec"] for r in f["rows"])
                                        - min(r["rho_spec"] for r in f["rows"]) for f in fs),
        "win_benefit_span_max": lambda: max(max(r["benefit_pct"] for r in f["rows"])
                                            - min(r["benefit_pct"] for r in f["rows"]) for f in fs),
        # -- (ii) the tail separation test
        "tail_hiding_limit_heavy": lambda: tail["premise"]["16"]["hiding_limit_heavy"],
        "tail_hiding_limit_light": lambda: tail["premise"]["16"]["hiding_limit_light"],
        "tail_mean_gap_rel_worst": lambda: max(p["relative_mean_gap"] for p in tail["premise"].values()),
        "tail_families_located": lambda: tail["p2_first_half"]["counts"]["located"],
        # the same degeneracy the collector was built for: this pair read
        # `{{tail_families_located}} of {{tail_families_located}}`.  The denominator is the number
        # of family pairs the test was run over, recorded as its own list in the artefact.
        "tail_families_tested": lambda: len(tail["families"]["heavy"]),
        "tail_delta_A16": lambda: d16["delta"]["mean"],
        "tail_delta_ci_lo": lambda: d16["delta"]["ci"][0],
        "tail_delta_ci_hi": lambda: d16["delta"]["ci"][1],
        "tail_delta_worst_abs": lambda: abs(dmax["delta"]["mean"]),
        "tail_shortfall_factor": lambda: 0.15 / abs(dmax["delta"]["mean"]),
        "tail_delta_over_pool_span": lambda: abs(dmax["delta"]["mean"]) / b100["direction"]["rho_spec"]["span"],
        "tail_delta_worst_A": lambda: dmax["agents"],
        "tail_fall_heavy_A16": lambda: s2[16]["heavy"]["mean"],
        "tail_fall_light_A16": lambda: s2[16]["light"]["mean"],
        "tail_fall_step": lambda: tail["p2_second_half_step2"]["step"],
        # -- (iii) the prediction-attributable fraction
        "variant_cells": lambda: len(var["cells"]),
        "F_min": lambda: min(c["F"]["mean"] for c in var["cells"]),
        "F_max": lambda: max(c["F"]["mean"] for c in var["cells"]),
        "F_h025": lambda: var_cells["h0.25/c4"]["F"]["mean"],
        "blind_share_h025": lambda: 1.0 - var_cells["h0.25/c4"]["F"]["mean"],
        "F_h050": lambda: var_cells["h0.50/c4"]["F"]["mean"],
        "F_h075": lambda: var_cells["h0.75/c4"]["F"]["mean"],
        "F_ratio_narrow_to_wide": lambda: var_cells["h0.25/c4"]["F"]["mean"] / var_cells["h0.75/c4"]["F"]["mean"],
        # RC1 (review round 1, `major`): `V3_capacity.k` is the FIRST cell's k.  Bound to a
        # single numeral it read "`k` = 100 in every run" while the twelve cells carry
        # k = 100 / 200 / 300 by width (`cells[*].k`), i.e. one row's value predicated over all
        # 192 runs.  The value is now read PER WIDTH off the cells, and the identity's own two
        # counts come from the check the artefact records.
        "variant_k_by_width": lambda: ", ".join(
            str(sorted(set(c["k"] for c in var["cells"] if c["h"] == h))[0])
            for h in var["h_grid"]),
        "variant_identity_runs": lambda: var["V3_capacity"]["n_seeds"],
        "variant_identity_bad": lambda: len(var["V3_capacity"]["bad"]),
        "F_h050_ci_lo": lambda: var_cells["h0.50/c4"]["F"]["ci"][0],
        "F_h050_ci_hi": lambda: var_cells["h0.50/c4"]["F"]["ci"][1],
        # the OTHER reading of the same threshold (a different quantity; reported, not chosen)
        "channel_F_min": lambda: min(f["F_min"] for f in pf),
        "channel_spearman_worst": lambda: max(f["spearman_F_rho"] for f in pf),
        # -- (iv) the side-effect channel
        "p4a_families": lambda: v4["P4a"]["n"],
        "p4b_lowest": lambda: min(v4["P4b"]["measured"][k][0] for k in v4["P4b"]["measured"]),
        "p4b_highest": lambda: max(v4["P4b"]["measured"][k][0] for k in v4["P4b"]["measured"]),
        "p4b_shortfall": lambda: v4["P4b"]["shortfall_factor"],
        "p4c_cells_located": lambda: v4["P4c"]["reading_b_cells_read"],
        "p4c_cells_losing": lambda: v4["P4c"]["reading_b_cells_with_losing_steps"],
        "p4c_frac_lo": lambda: v4["P4c"]["reading_b_losing_fraction"][0],
        "p4c_frac_hi": lambda: v4["P4c"]["reading_b_losing_fraction"][1],
        "p4c_by_construction": lambda: v4["P4c"]["reading_a_cells_negative"],
        "m4b_neg_steps": lambda: m4b["n_negative"],
        "m4b_steps": lambda: m4b["n_steps"],
        "m4b_frac_neg": lambda: m4b["frac_negative"],
        "m4b_hidden_frac": lambda: m4b["hidden_fraction"],
        "m4b_mean_benefit": lambda: m4b["mean_benefit"],
        "m4b_mean_negative": lambda: m4b["mean_negative"],
        "load_for_threshold_lo": lambda: ll["A=16/h0.50"]["load_for_threshold"],
        "load_for_threshold_hi": lambda: ll["A=16/h0.90"]["load_for_threshold"],
        "load_for_threshold_ratio": lambda: ll["A=16/h0.90"]["load_for_threshold"] / ll["A=16/h0.50"]["load_for_threshold"],
        "db_per_load_lo": lambda: min(mech["load_decomposition"][0]["db_per_load"].values()),
        "db_per_load_hi": lambda: max(mech["load_decomposition"][0]["db_per_load"].values()),
        # -- (v) the closed-form fixed point
        "fix_secondary_within": lambda: sec["secondary_same_cell_within"],
        "fix_secondary_n": lambda: sec["secondary_same_cell_n"],
        "fix_secondary_median": lambda: sec["secondary_same_cell_median"],
        "fix_secondary_worst": lambda: sec["secondary_same_cell_worst"],
        # -- (vi) the external cell
        "ext_cells": lambda: es["n_cells"],
        "ext_sign_match": lambda: es["sign_match"],
        "ext_band_lo": lambda: es["model_band_pct_in_reported_region"][0],
        "ext_band_hi": lambda: es["model_band_pct_in_reported_region"][1],
        "ext_region_lo": lambda: es["reported_region_overlap_p"][0],
        "ext_region_hi": lambda: es["reported_region_overlap_p"][1],
        "ext_spork_published": lambda: es["h_sensitivity"]["published_target_pct"],
        "ext_spork_probe": lambda: es["h_sensitivity"]["h_probe_low"],
        "ext_spork_probe_ci_lo": lambda: es["h_sensitivity"]["h_probe_low_ci"][0],
        "ext_spork_probe_ci_hi": lambda: es["h_sensitivity"]["h_probe_low_ci"][1],
        "ext_oracle": lambda: es["h_sensitivity"]["h_oracle"],
        "ext_smc_telecom_published": lambda: [v for v in ext["verdicts"] if v["key"] == "smc_telecom"][0]["published_reduction_pct"],
        "ext_smc_band_lo": lambda: [v for v in ext["verdicts"] if v["key"] == "smc_telecom"][0]["band"][0],
        "ext_smc_band_hi": lambda: [v for v in ext["verdicts"] if v["key"] == "smc_telecom"][0]["band"][1],
        "ext_appworld_published": lambda: [v for v in ext["verdicts"] if v["key"] == "smc_appworld"][0]["published_reduction_pct"],
        "ext_ceiling": lambda: [v for v in ext["verdicts"] if v["key"] == "smc_appworld"][0]["model_ceiling_pct"],
        "ext_appworld_shortfall": lambda: [v for v in ext["verdicts"] if v["key"] == "smc_appworld"][0]["published_reduction_pct"] - [v for v in ext["verdicts"] if v["key"] == "smc_appworld"][0]["model_ceiling_pct"],
        # -- the mechanism readings (the registered adjunct hypotheses)
        "hr_deviating": lambda: len(mech["hr_rho"]["deviating"]),
        "hr_groups": lambda: mech["h_shift"]["n_groups"],
        "hshift_consistent": lambda: len(mech["h_shift"]["consistent"]),
        "dec_contrast_cells": lambda: dec["contrast_rho"]["n"],
        "dec_carrying_overshoot": lambda: dec["contrast_rho"]["largest_count"]["overshoot"],
        "dec_overshoot_abs": lambda: dec["contrast_rho"]["mean_abs_delta"]["overshoot"],
        "dec_S_abs": lambda: dec["contrast_rho"]["mean_abs_delta"]["S"],
        # -- which of the six criteria the artefacts say are unmet, and how many ------------
        # The owner of section 4.1's summary sentence.  `outright` = the registered test is
        # not met; `part` = one half of the criterion is met and the other is not; `met` =
        # every half of it is.  The three sets are printed by the assembler.
        "criteria_unmet_outright": lambda: ",".join(sorted(k for k, v in crit.items()
                                                           if v == "outright")),
        "criteria_unmet_part": lambda: ",".join(sorted(k for k, v in crit.items()
                                                       if v == "part")),
        "criteria_met": lambda: ",".join(sorted(k for k, v in crit.items() if v == "met")),
        "n_criteria_unmet_outright": lambda: sum(1 for v in crit.values() if v == "outright"),
        "n_criteria_unmet_part": lambda: sum(1 for v in crit.values() if v == "part"),
    }



# --- sections 5-9: the package's own properties, read from the package -----------------------
def build_package_facts():
    """The quantities sections 5-9 print about the artefact set itself.

    These are properties of the package that a reader can check without trusting us: how many files
    the evidence is, how large it is, how many scripts carry the model, and -- the load-bearing one --
    how many of those scripts' imports are neither the standard library nor a sibling in the same
    directory.  A deterministic, dependency-free instrument is a claim; this is the reading of it.
    """
    import sys as _sys
    files = sorted(os.listdir(ART))
    pys = [f for f in files if f.endswith(".py")]
    std = set(_sys.stdlib_module_names)
    siblings = set(os.path.splitext(f)[0] for f in pys)
    mods = set()
    for f in pys:
        t = io.open(os.path.join(ART, f), encoding="utf-8").read()
        # READ the imports by PARSING the file, not by matching a pattern over its text: a pattern
        # also matches the words inside prose, and this one did -- a docstring line beginning
        # "from has one." was counted as an import of a module named `has`.
        for node in ast.walk(ast.parse(t)):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods.add(node.module.split(".")[0])
    outside = sorted(m for m in mods if m not in std and m not in siblings)
    return {
        "n_evidence_files": lambda: len(files),
        "evidence_mb": lambda: round(sum(os.path.getsize(os.path.join(ART, f)) for f in files)
                                     / (1024.0 * 1024.0), 2),
        "n_instrument_scripts": lambda: len(pys),
        "n_import_modules": lambda: len(mods),
        "n_imports_outside": lambda: len(outside),
        # the sweeps' own declared totals, summed from the artefacts rather than typed
        "n_deciding_cells": lambda: (sum(len(f["rows"]) for n in
                                         ("boundary_v2_h050.json", "boundary_v2_h090.json",
                                          "boundary_v2_h100.json")
                                         for f in load(n)["families"])
                                     + len(load("decompose_v1_h100.json")["cells"])
                                     + sum(len(v) for v in load("tail_v1_h100.json")["families"].values())
                                     + len(load("variant_v1.json")["cells"])),
        # kept apart from the cell count: a mechanism "group" is a family, not a cell, and a sum that
        # mixes the two units is a number whose name is wrong
        "n_deciding_groups": lambda: len(load("mechanism_v1.json")["groups"]),
        "n_deciding_seeds": lambda: max(len(load(n)["seeds"]) for n in
                                       ("boundary_v2_h050.json", "boundary_v2_h100.json",
                                        "mechanism_v1.json", "tail_v1_h100.json")),
    }


def resolve(text, facts):
    bad = []

    def sub(m):
        name, fmt = m.group(1), (m.group(2) or "")
        if name not in facts:
            bad.append("unknown fact {{%s}}" % name)
            return m.group(0)
        v = facts[name]()
        if isinstance(v, float):
            spec = fmt[1:] if fmt else ".6g"
            return format(v, spec)
        return str(v)

    out = PH.sub(sub, text)
    return out, bad


def keys_in(m):
    """Every key of one citation bracket, in the order it is written."""
    return KEY_IN.findall(m.group(1) + m.group(2))


def cite_order(text):
    seen = []
    for m in CITE.finditer(text):
        for k in keys_in(m):
            if k not in seen:
                seen.append(k)
    return seen


def number_citations(text, order):
    n = {k: i + 1 for i, k in enumerate(order)}
    return CITE.sub(lambda m: "[%s]" % ", ".join(str(x) for x in sorted(n[k] for k in keys_in(m))), text)


# --- the quantified sentinel: what a ratio and a counted sentence are built from -------------------
# Required change 4 of the review of round 1 asks for a collector rather than a wider promise, and
# this is the build-time half of it.  The class it exists for is: a sentence that QUANTIFIES --
# "N of M", "none of them", "all twelve" -- is a claim about a set, and it is only as strong as the
# bindings under it.  Two ways it fails, both of which the review found in this manuscript:
#
#   * ONE BINDING ON BOTH SIDES.  `{{x}} of {{x}}` renders as "N of N" for every possible run, so no
#     measurement can ever make the sentence read a shortfall.  Two of the six registered criteria
#     had their outcome sentence in that form.
#   * A TYPED NUMERAL.  "none was ambiguous" and "3 of 3" were typed while the bound fact sat in the
#     table unused, so the build had nothing to compare.
#
# DOMAIN names the noun each counted fact is a count OF.  A ratio is legal only when both facts are
# declared and their domains agree -- "23 of 25 pairs" or "128 of 141 rows", never "18 of 18 cells"
# over (family, width) pairs.  A fact declared here and never used is a FAILED ASSEMBLY: a registered
# count that no sentence quotes is either a dead binding or evidence that a numeral was typed.
DOMAIN = {
    # families / pools
    "b_families_located": "family", "b_families_total": "family", "b_families_ambiguous": "family",
    "tail_families_located": "family", "tail_families_tested": "family",
    "p4a_families": "family", "n_anchors": "anchor", "n_anchors_ok": "anchor",
    # cells and pairs (a cell is a pool x contention grid point; a pair is two cells)
    "variant_cells": "cell", "variant_identity_runs": "run", "variant_identity_bad": "run",
    "p4c_cells_located": "cell", "p4c_cells_losing": "cell", "p4c_by_construction": "cell",
    "dec_contrast_cells": "pair", "dec_carrying_overshoot": "pair",
    "boundary_matched_pairs": "pair", "boundary_matched_disagreeing": "pair",
    "fixedpoint_evaluated": "pair", "fixedpoint_excluded": "pair",
    "draw_prefix_checked": "configuration", "draw_prefix_validated": "configuration",
    "hr_deviating": "group", "hr_groups": "group", "hshift_consistent": "group",
    # rows, steps, cells of the readings that report one number per cell
    "fix_secondary_n": "row", "fix_secondary_within": "row",
    "m4b_steps": "step", "m4b_neg_steps": "step",
    "ext_cells": "cell", "ext_sign_match": "cell",
    "n_criteria_unmet_outright": "criterion", "n_criteria_unmet_part": "criterion",
}
RATIO = re.compile(r"\{\{([A-Za-z0-9_]+)(?:\|[^}]+)?\}\}\s*(?:\*\*)?\s*of\s*(?:\*\*)?\s*"
                   r"\{\{([A-Za-z0-9_]+)(?:\|[^}]+)?\}\}")


def check_quantified(text):
    """Every ratio in the parts: two DIFFERENT bindings, of one declared domain.  Returns failures."""
    bad = []
    for m in RATIO.finditer(text):
        num, den = m.group(1), m.group(2)
        if num == den:
            bad.append("the ratio `%s of %s` is bound to ONE fact on both sides -- it can only ever "
                       "read 'N of N', so no run can make it report a shortfall" % (num, den))
            continue
        if num not in DOMAIN or den not in DOMAIN:
            missing = [n for n in (num, den) if n not in DOMAIN]
            bad.append("the ratio `%s of %s` uses %s, which declares no domain -- a quantified "
                       "sentence may not rest on an undeclared count"
                       % (num, den, ", ".join(missing)))
            continue
        if DOMAIN[num] != DOMAIN[den]:
            bad.append("the ratio `%s of %s` compares a count of %s with a count of %s"
                       % (num, den, DOMAIN[num], DOMAIN[den]))
    for name in sorted(DOMAIN):
        if ("{{%s}}" % name) not in text and ("{{%s|" % name) not in text:
            bad.append("the registered count `%s` is bound and quoted by no sentence -- either the "
                       "binding is dead or the sentence typed the numeral instead" % name)
    return bad


def selftest():
    """Liveness of the collector above: every branch must be able to fire.

    A check nobody has seen fail is decoration, and this one was added in revision round 1 in answer
    to a review that found two of the six registered criteria carrying an outcome sentence no run
    could ever make read a shortfall.  So each branch gets a plant, and each plant is DERIVED FROM THE
    FILE it breaks rather than typed: the ratio, the two fact names and the fact to unquote are read
    out of the parts at run time, so this control cannot go stale while the prose moves under it.

    Each plant runs in its OWN throwaway copy of the package.  The first version of this control
    patched one copy for all three plants and restored by string-replacing the planted text back --
    and when a plant's anchor was found in two files it left the copy dirty for the next one, which
    then reported a failure belonging to its predecessor (the plant that tests the cross-domain rule
    fired the one-binding rule instead).  A control that carries state between its own cases is not a
    control; a fresh copy per case is the fix, and it costs a directory copy.
    """
    import shutil
    import subprocess
    import tempfile

    text = "\n".join(io.open(os.path.join(HERE, q), encoding="utf-8").read() for q in PARTS)
    m = RATIO.search(text)
    if m is None:
        print("ASSEMBLE SELFTEST: no ratio in the parts to plant on -- the collector is untested, "
              "not passing")
        return 1
    num, den = m.group(1), m.group(2)
    used = next((n for n in sorted(DOMAIN) if "{{%s}}" % n in text), None)
    cross = next((n for n in sorted(DOMAIN) if DOMAIN[n] != DOMAIN.get(num)), None)
    if used is None or cross is None:
        print("ASSEMBLE SELFTEST: could not derive a plant (num=%r den=%r)" % (num, den))
        return 1
    bold = "**" if "**" in m.group(0) else ""
    plants = [
        ("one binding on both sides",
         m.group(0), "{{%s}} of %s{{%s}}" % (num, bold, num), "ONE fact on both sides"),
        ("a declared count quoted by no sentence",
         "{{%s}}" % used, "the value", "quoted by no sentence"),
        ("a ratio across two domains",
         "{{%s}}" % den, "{{%s}}" % cross, "compares a count of"),
    ]

    def build(root):
        r = subprocess.run([sys.executable, "assemble.py"], cwd=root,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode("utf-8", "replace")

    work = tempfile.mkdtemp(prefix="assemble-selftest-")
    bad = 0
    try:
        # control: the package as committed must build, or the plants below prove nothing
        base = os.path.join(work, "control")
        shutil.copytree(HERE, base, ignore=shutil.ignore_patterns("research", ".repro-scratch",
                                                                 "__pycache__", ".git"))
        rc, out = build(base)
        print("  control: the unplanted copy builds (%s)" % ("ok" if rc == 0 else "FAILED"))
        if rc != 0:
            print("    " + out.strip().replace("\n", "\n    ")[-500:])
            return 1
        for i, (name, old, new, needle) in enumerate(plants):
            root = os.path.join(work, "plant%d" % i)
            shutil.copytree(HERE, root, ignore=shutil.ignore_patterns("research", ".repro-scratch",
                                                                     "__pycache__", ".git"))
            patched = None
            for q in PARTS:
                f = os.path.join(root, q)
                s = io.open(f, encoding="utf-8").read()
                if old in s:
                    io.open(f, "w", encoding="utf-8").write(s.replace(old, new, 1))
                    patched = q
                    break
            if patched is None:
                print("  plant %-42s ANCHOR NOT FOUND -- the plant tests nothing" % name)
                bad += 1
                continue
            rc, out = build(root)
            fired = rc != 0 and needle in out
            print("  plant %-42s in %-18s fired=%s" % (name, patched, fired))
            if not fired:
                bad += 1
                print("    " + out.strip().replace("\n", "\n    ")[-400:])
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("ASSEMBLE SELFTEST: %d plant(s), %d not firing" % (len(plants), bad))
    return 0 if bad == 0 else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    raw = []
    for p in PARTS:
        path = os.path.join(HERE, p)
        if not os.path.exists(path):
            print("ASSEMBLY FAILED: part %s is missing" % p)
            return 1
        raw.append(io.open(path, encoding="utf-8").read())
    text = "\n".join(raw)

    facts = build_facts()
    text, bad = resolve(text, facts)
    if bad:
        print("ASSEMBLY FAILED: %d unresolved placeholder(s):" % len(bad))
        for b in sorted(set(bad)):
            print("  " + b)
        return 1
    # ... and the post-condition the first version of this file lacked: NOTHING of the placeholder
    # form may survive the substitution, whatever the pattern happened to match.  This check is
    # taken over the assembled text rather than over the resolver's own matches, so a placeholder
    # the pattern cannot see is a FAILED ASSEMBLY instead of an unexplained `{{...}}` in the paper.
    left = re.findall(r"\{\{[^}]*\}\}", text)
    if left:
        print("ASSEMBLY FAILED: %d placeholder(s) survived substitution: %s"
              % (len(left), ", ".join(sorted(set(left))[:6])))
        return 1

    # ... the post-condition required change 4 asks for: every quantified sentence rests on two
    # independent, domain-declared bindings, and every registered count is quoted by one.  This is a
    # build failure, not a review finding -- which is what section 4.1 says the assembly step is for.
    qbad = check_quantified("\n".join(raw))
    if qbad:
        print("ASSEMBLY FAILED: %d quantified-sentence defect(s):" % len(qbad))
        for b in qbad[:8]:
            print("  " + b)
        return 1

    # ... the post-condition for citations, of the same shape as the one for placeholders: after
    # numbering, NOTHING of the bracket form may survive, whatever the pattern happened to match.
    stray = re.findall(r"\[@[^\]]*\]", number_citations(text, cite_order(text)))
    if stray:
        print("ASSEMBLY FAILED: %d citation bracket(s) survived numbering: %s"
              % (len(stray), ", ".join(sorted(set(stray))[:6])))
        return 1

    order = cite_order(text)
    sel = {r["key"]: r for r in json.load(io.open(SELECTION, encoding="utf-8"))["rows"]}
    unknown = [k for k in order if k not in sel]
    uncited = [k for k in sel if k not in order]
    if unknown:
        print("ASSEMBLY FAILED: %d cited key(s) have no row in the layer: %s"
              % (len(unknown), ", ".join(unknown)))
        return 1
    if uncited:
        print("ASSEMBLY FAILED: %d row(s) of the layer are never cited (padding): %s"
              % (len(uncited), ", ".join(uncited)))
        return 1

    body = number_citations(text, order)
    body = body.rstrip("\n") + "\n"

    # The references section is NOT this file's object: `refs_render.py` owns it.  Whatever is
    # already committed is carried through unchanged, so a bare `assemble.py` cannot silently
    # strip the bibliography, and the renderer refreshes it in the next step.
    hdr = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$")
    m = hdr.search(body)
    carried = ""
    if not m and os.path.exists(MS):
        old_ms = io.open(MS, encoding="utf-8").read()
        om = hdr.search(old_ms)
        if om:
            carried = old_ms[om.start():]
            print("carried the existing references section through unchanged "
                  "(refs_render.py owns it; run it to refresh)")
    body = body + ("\n" + carried if carried else "")
    order_doc = {"what": "issue #50 citation order, derived from the assembled manuscript",
                 "rule": "first appearance in the parts; the reference layer is built in this order",
                 "n": len(order), "keys": order}

    if "--check" in sys.argv:
        if not os.path.exists(MS):
            print("ASSEMBLY CHECK: no committed manuscript.md to compare with")
            return 1
        have = io.open(MS, encoding="utf-8").read()
        hm = re.compile(r"(?m)^##\s*(?:\d+\.\s*)?References\s*$").search(have)
        have_body = have[:hm.start()] if hm else have
        fresh_body = body[:hdr.search(body).start()] if hdr.search(body) else body
        same = have_body == fresh_body
        comm_order = json.load(io.open(ORDER, encoding="utf-8"))["keys"] \
            if os.path.exists(ORDER) else []
        print("manuscript.md body (the part before the references section, which this file"
              " does not own) matches a fresh assembly: %s" % same)
        print("  citations: %d, numbered 1..%d in first-citation order" % (len(order), len(order)))
        print("  layer rows: %d cited, %d uncited" % (len(order), len(uncited)))
        print("  refs_order.json matches: %s" % (comm_order == order))
        return 0 if (same and comm_order == order) else 1

    io.open(MS, "w", encoding="utf-8").write(body)
    io.open(ORDER, "w", encoding="utf-8").write(json.dumps(order_doc, ensure_ascii=False, indent=1) + "\n")
    print("assembled %d line(s), %d citation(s) numbered 1..%d, from %d part(s)"
          % (body.count("\n"), len(order), len(order), len(PARTS)))
    print("  facts resolved: " + json.dumps({k: round(v(), 6) if isinstance(v(), float) else v()
                                             for k, v in sorted(facts.items())}))
    print("  wrote manuscript.md and refs_order.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
