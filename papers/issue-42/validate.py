#!/usr/bin/env python3
"""Assert the manuscript's numbers against the artefacts that produced them.

Each check carries THREE parts: a path into an artefact, the value expected there, and the
claim sentence fragment that must appear in manuscript.md.  Checking the value alone is not
enough on a citation-dense paper, where "73.1" can appear as part of a reference number; and
checking the phrase alone is not enough, because the phrase may quote a stale run.  Both.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
J = lambda name: json.load(io.open(os.path.join(HERE, "artefacts", name), encoding="utf-8"))

def main():
    v0, v1, v2, v3 = J("results_v0.json"), J("results_v1.json"), J("results_v2.json"), J("results_v3.json")
    refs = json.load(io.open(os.path.join(HERE, "artefacts", "refs_final.json"), encoding="utf-8"))
    cal = json.load(io.open(os.path.join(HERE, "artefacts", "calibration_dossier.json"), encoding="utf-8"))
    doc = io.open(os.path.join(HERE, "manuscript.md"), encoding="utf-8").read()
    # some claims live in the citation report, not the manuscript: a check must look where
    # its claim actually lives, or it is testing the wrong document.
    rdoc = io.open(os.path.join(HERE, "reference-check.md"), encoding="utf-8").read()
    # Phrase matching normalises whitespace: a claim sentence wrapped across a line is the
    # same claim, and a validator that fails on wrapping trains its author to ignore it.
    def ws(s):
        return " ".join(s.split())

    P = v3["part"]
    f2 = lambda k, f: v2["laws"][k]["oos"][f]
    CHECKS = [
      # --- construct / v0 ---
      ("v0_check_tally", len(v0["checks"]), 19, "**19/19 reductions.**"),
      ("v0_accuracy_invariance", [round(b["C2_hat"], 4) for b in v0["beta_sweep"]][:2], [0.1505, 0.1503],
       "Measured C2 across the dial is 0.1505, 0.1503, 0.1501, 0.1501"),
      ("v0_marginal_zero_at_aligned", round(v0["beta_sweep"][-1]["marginal_catch"], 4), 0.0,
       "0.1505, 0.1058, 0.0607, **0.0000**"),
      # --- v1 ---
      ("v1_check_tally", len(v1["checks"]), 18, "**18/18 checks.**"),
      ("v1_accuracy_ordered_capture", round(v1["regret"]["accuracy_ordered"]["mean_value_ratio"], 3), 0.527,
       "**accuracy-ordered selection 0.527**"),
      ("v1_analytic_capture", round(v1["regret"]["analytic"]["mean_value_ratio"], 3), 1.0,
       "a residual-catch rule reaches 1.000"),
      ("v1_inversion_share", round(v1["inversion"]["F1_easy_weak"]["frac_inversion"], 2), 0.32,
       "32 percent of equal-cost strictly-lower-accuracy pairs are"),
      ("v1_obs_vs_pred_beta05", [round(v1["marginal_catch_verification"][2]["observed_mean"], 5),
                                 round(v1["marginal_catch_verification"][2]["predicted"], 5)], [0.01504, 0.015],
       "observed 0.01504 against a predicted"),
      ("v1_obs_sd_beta05", round(v1["marginal_catch_verification"][2]["observed_sd"], 5), 0.0003,
       "standard deviation 0.00030"),
      # --- v2 ---
      ("v2_check_tally", len(v2["checks"]), 14, "**14/14 checks.**"),
      ("v2_heldout_cells", v2["laws"]["L0_constant"]["oos"]["n_cells"], 504, "504 held-out cells"),
      ("v2_fit_cells", v2["laws"]["L0_constant"]["fit"]["n_cells"], 300, "5 dial values (300 cells)"),
      ("v2_operational_median_err", round(f2("L2_operational", "median_rel_err"), 4), 0.0304,
       "error is 3.04 percent against the registered 25 percent limit"),
      ("v2_constant_median_err", round(f2("L0_constant", "median_rel_err"), 4), 0.731,
       "| constant | 71.6 pct | 73.1 pct |"),
      ("v2_costratio_median_err", round(f2("L1_by_cost_ratio", "median_rel_err"), 4), 0.929,
       "| indexed by cost ratio | 55.3 pct | 92.9 pct |"),
      ("v2_parametric_median_err", round(f2("L4_parametric", "median_rel_err"), 4), 0.635,
       "| parametric power law | 79.1 pct | 63.5 pct |"),
      ("v2_independence_acc", round(f2("L3_independence", "decision_accuracy"), 4), 0.575,
       "| independence assumed | 100 pct | 100 pct | 57.5 pct |"),
      ("v2_operational_acc", round(f2("L2_operational", "decision_accuracy"), 4), 0.992,
       "| **operational (from a finite log)** | **3.5 pct** | **3.04 pct** | **99.2 pct** |"),
      ("v2_seed_stream_mean", round(v2["criterion_5d_seed_streams"]["mean"], 4), 0.0322,
       "of 3.22 percent, standard deviation 0.21 percent"),
      ("v2_seed_stream_sd", round(v2["criterion_5d_seed_streams"]["sd"], 4), 0.0021,
       "standard deviation 0.21 percent"),
      ("v2_seed_stream_worst", round(v2["criterion_5d_seed_streams"]["max_stream"], 4), 0.0372,
       "and worst stream\n3.72 percent"),
      ("v2_small_log_error", round(v2["criterion_5d_small_log"]["mean"], 4), 0.1332,
       "held-out error is 13.3"),
      ("v2_deferral_capture", round(v2["baselines_oos"]["deferral_threshold"]["mean_value_ratio"], 3), 0.839,
       "cost-sensitive deferral 0.839"),
      ("v2_deferral_median_regret_zero", round(v2["baselines_oos"]["deferral_threshold"]["median_rel_regret"], 4), 0.0,
       "**median regret is 0.000 while its mean shortfall is 16 percent**"),
      # --- v3 calibration ---
      ("v3_check_tally", [v3["n_pass"], v3["n_check"]], [24, 25], "**24/25"),
      ("v3_span_synthetic", round(P["span"]["synthetic"]["factor"], 1), 138.0, "a factor of **138**"),
      ("v3_span_synthetic_min", round(P["span"]["synthetic"]["min"], 4), 0.0051, "T spans 0.0051 to 0.7031"),
      ("v3_span_synthetic_max", round(P["span"]["synthetic"]["max"], 4), 0.7031, "0.0051 to 0.7031"),
      ("v3_span_calibrated", round(P["span"]["calibrated"]["factor"], 2), 4.84, "**4.84x**"),
      ("v3_span_cal_min", round(P["span"]["calibrated"]["min"], 4), 0.124, "| T minimum | 0.0051 | 0.1240 |"),
      ("v3_span_cal_max", round(P["span"]["calibrated"]["max"], 4), 0.6, "| T maximum | 0.7031 | 0.6000 |"),
      ("v3_share_of_synthetic", round(100 * P["span"]["share_of_synthetic"], 1), 3.5, "**3.5 pct**"),
      ("v3_operational_oos_acc", round(P["race_on_calibrated_region"]["L2_operational"]["score"]["decision_accuracy"], 4), 1.0,
       "| **operational** | **0.0630** | **1.0000** |"),
      ("v3_operational_oos_err", round(P["race_on_calibrated_region"]["L2_operational"]["score"]["median_rel_err"], 4), 0.063,
       "**operational** | **0.0630**"),
      ("v3_constant_oos_acc", round(P["race_on_calibrated_region"]["L0_constant"]["score"]["decision_accuracy"], 4), 0.9,
       "| constant | 0.1735 | 0.9000 |"),
      ("v3_costratio_oos_acc", round(P["race_on_calibrated_region"]["L1_by_cost_ratio"]["score"]["decision_accuracy"], 4), 0.9333,
       "| indexed by cost ratio | 0.1561 | 0.9333 |"),
      ("v3_independence_oos_acc", round(P["race_on_calibrated_region"]["L3_independence"]["score"]["decision_accuracy"], 4), 0.6333,
       "| independence assumed | 1.0000 | 0.6333 |"),
      ("v3_constant_misdecides", round(100 * P["race_on_calibrated_region"]["L0_constant"]["score"]["decision_accuracy"], 1), 90.0,
       "misdecides **6 of 60** held-out cells (10.0 percent)"),
      ("v3_refuted_predictions", v3["n_refuted_registered_predictions"], 1, "**A registered prediction was refuted here"),
      # --- v3 composition ---
      ("v3_composition_matched", round(P["composition"]["arms"]["skewed"]["matched"]["cumulative"], 4), 0.5975,
       "| **cumulative** | **0.5975** | **0.6483** |"),
      ("v3_composition_spread", round(P["composition"]["arms"]["skewed"]["spread"]["cumulative"], 4), 0.6483,
       "| **cumulative** | **0.5975** | **0.6483** |"),
      ("v3_composition_gap_pct", round(100 * abs(P["composition"]["arms"]["skewed"]["matched"]["cumulative"]
                                                 - P["composition"]["arms"]["skewed"]["spread"]["cumulative"])
                                       / P["composition"]["arms"]["skewed"]["matched"]["cumulative"], 1), 8.5,
       "differs by **8.5\npercent**"),
      ("v3_composition_first_matched", round(P["composition"]["arms"]["skewed"]["matched"]["marginals"][0], 4), 0.2738,
       "| 1 | 0.2738 | 0.3000 |"),
      ("v3_composition_first_spread", round(P["composition"]["arms"]["skewed"]["spread"]["marginals"][0], 4), 0.3,
       "| 1 | 0.2738 | 0.3000 |"),
      ("v3_composition_prediction_ratio", round(P["composition"]["registered_prediction"]["observed_ratio"], 2), 0.79,
       "The observed ratio is **0.79"),
      # --- v3 adversarial ---
      ("v3_hstar", round(P["adversarial"]["h_star"], 4), 0.2, "h_star = **0.2000**"),
      ("v3_hstar_is_model_derived", P["adversarial"]["provenance"], "model_derived",
       "h_star is therefore **model-derived**, not measured"),
      ("v3_calibration_region_systems", len({r["sys"] for r in cal if r["kind"] == "quant"}), 5,
       "come from 7 quantitative\ncells over 5 systems"),
      # --- calibration dossier ---
      ("cal_cells", len(cal), 12, "12 cells drawn from 10 independent published systems"),
      ("cal_systems", len({r["sys"] for r in cal}), 10, "10 independent published systems"),
      ("cal_quant", len([r for r in cal if r["kind"] == "quant"]), 7, "of which 7 are\nquantitative"),
      ("cal_quotes_verified", all(r["quote_verified"] for r in cal), True,
       "Every quote is verified against a committed capture, and the verifier is **two-sided**"),
      # --- references ---
      ("refs_total", len(refs), 117, "117 entries, 117 verified"),
      ("refs_all_verified", all(r["verdict"] == "verified" for r in refs), True, "0 unreachable, 0 title-mismatched"),
    ]

    fails = []
    for name, actual, expected, phrase in CHECKS:
        ok_val = (abs(actual - expected) < 5e-4) if isinstance(expected, float) else (actual == expected)
        ok_phrase = (ws(phrase) in ws(doc)) or (ws(phrase) in ws(rdoc))
        status = "PASS" if (ok_val and ok_phrase) else "FAIL"
        if status == "FAIL":
            fails.append((name, actual, expected, ok_val, ok_phrase))
        print("%-4s %-36s value=%-16s expected=%-16s phrase=%s" % (
            status, name, str(actual)[:16], str(expected)[:16], "yes" if ok_phrase else "NO"))
    print()
    print("VALIDATE %d/%d" % (len(CHECKS) - len(fails), len(CHECKS)))
    if fails:
        print("\nFAILURES:")
        for n, a, e, ov, op in fails:
            print("   %s: value_ok=%s phrase_ok=%s (got %r, want %r)" % (n, ov, op, a, e))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
