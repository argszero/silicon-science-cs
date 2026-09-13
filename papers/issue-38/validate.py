#!/usr/bin/env python3
"""Validation suite for issue #38.

Every check below is attached to a specific sentence of `manuscript.md` and reads its
number out of `canonical_results.json` -- the artefact the canonical runner produces.
The suite asserts properties of the artefact; it never compares a file to a stored
digest, because the runner rewrites the artefact (and the figures) on every run. The
per-run facts that a verifier compares are printed by `reproduce.sh` instead.

Usage:  python3 validate.py          (prints VALIDATE n/n, exits non-zero on failure)
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "canonical_results.json")

FAILED = []
NCHECK = [0]


def check(label, cond, detail=""):
    NCHECK[0] += 1
    if not cond:
        FAILED.append("%s %s" % (label, detail))
        print("  [FAIL] %s %s" % (label, detail))


def close(a, b, tol=5e-3):
    return abs(a - b) <= tol


def main():
    d = json.load(open(ART, encoding="utf-8"))
    red, anc, lg = d["reductions"], d["anchors"], d["law_grid"]
    oos, clo, mech, p3 = d["oos"], d["closure"], d["mechanism"], d["p3_ablation"]

    # --- SS2.5 reductions: "270 reduction cells and they are exact in every one"
    check("r1_reduction_cells", red["cells"] == 270, red["cells"])
    check("r2_reduction_failures", red["failures"] == 0, red["failures"])
    check("r3_m_eq_N_is_oracle", red["A_attention_unbounded_eq_optimum"] is True)
    check("r4_sigma0_market_is_oracle", red["B_zero_noise_market_eq_optimum"] is True)

    # --- SS2.5 anchors
    check("a1_regrets_nonnegative", anc["all_regrets_nonnegative"] is True)
    check("a2_greedy_never_worse_than_random", close(anc["greedy_le_random_rate"], 1.0))
    check("a3_market_exact_at_sigma0", anc["market_exact_at_sigma_zero"] is True)
    check("a4_market_monotone_in_sigma", anc["market_monotone_nondecreasing_in_sigma"] is True)
    check("a5_planner_monotone_in_m", anc["planner_monotone_nonincreasing_in_m"] is True)
    check("a6_planner_exact_at_m_eq_N", anc["planner_exact_at_m_eq_N"] is True)
    # SS4.7 "greedy at or below random in 100% of bracketing cells (45 such cells)"
    check("a7_bracket_cells", anc["bracket_cells"] == 45, anc["bracket_cells"])
    mc = anc["market_curve_N64"]
    check("a8_market_curve_len", len(mc) == 8, len(mc))
    check("a9_market_curve_starts_at_zero", close(mc[0]["market_regret"], 0.0, 1e-12))
    check("a10_market_curve_rises", all(mc[i + 1]["market_regret"] >= mc[i]["market_regret"]
                                        for i in range(len(mc) - 1)))
    pc = anc["planner_curve_nested_N64"]
    check("a11_planner_curve_len", len(pc) == 8, len(pc))
    check("a12_planner_curve_ends_at_optimum",
          close(pc[-1]["planner_regret"], 0.0, 1e-12) and pc[-1]["m"] == 64)
    # SS4.7 random-assignment floor "0.573 regret per task at N = 64"
    rp = {r["N"]: r["value"] for r in anc["random_regret_per_task"]}
    check("a13_random_floor_N64", close(rp[64], 0.5731, 5e-4), rp[64])
    check("a14_random_floor_rises", rp[16] < rp[256], (rp[16], rp[256]))

    # --- SS4.1 P1 is refuted
    p1 = lg["p1_verdict"]
    check("p1_1_series_count", p1["n_series"] == 50, p1["n_series"])
    check("p1_2_all_endpoints_rise", p1["n_endpoint_rising"] == 50, p1["n_endpoint_rising"])
    check("p1_3_no_endpoint_falls", p1["n_endpoint_falling"] == 0, p1["n_endpoint_falling"])
    check("p1_4_none_strictly_decreasing", p1["n_strictly_decreasing"] == 0)
    check("p1_5_steps_total", p1["n_steps"] == 190, p1["n_steps"])
    check("p1_6_steps_nonneg_reported", p1["steps_nonneg"] == 173, p1["steps_nonneg"])
    check("p1_7_negative_dips_reported", p1["steps_negative"] == 17, p1["steps_negative"])
    check("p1_8_verdict", p1["verdict"] == "REFUTED", p1["verdict"])

    # --- SS4.2 P2 is unmet; the boundary is a proportionality
    check("p2_1_verdict_unmet", lg["p2_product_law"]["verdict"] == "UNMET")
    check("p2_2_median_rel_err", close(lg["p2_product_law"]["median_rel_err"], 0.2075, 1e-3))
    fit = lg["collapse_fit"]
    check("f1_fit_exponent", close(fit["b"], 1.0358, 1e-3), fit["b"])
    check("f2_fit_r2", close(fit["r2"], 0.9176, 1e-3), fit["r2"])
    check("f3_fit_n", fit["n"] == 240, fit["n"])

    # --- SS4.2 out-of-sample race
    check("o1_train_cells", oos["train_cells"] == 240, oos["train_cells"])
    check("o2_test_cells", oos["test_cells"] == 120, oos["test_cells"])
    sc = oos["scores"]
    check("o3_gamma_aware_median", close(sc["gamma_aware_proportional"]["median_rel_err"], 0.1837, 1e-3))
    check("o4_trivial_proportional_median",
          close(sc["trivial_proportional"]["median_rel_err"], 0.2701, 1e-3))
    check("o5_power_law_median", close(sc["fitted_power_law"]["median_rel_err"], 0.2851, 1e-3))
    check("o6_power_law_loses_to_trivial",
          sc["fitted_power_law"]["median_rel_err"] > sc["trivial_proportional"]["median_rel_err"])
    check("o7_constant_baseline_median",
          close(sc["constant_baseline"]["median_rel_err"], 0.5759, 1e-3))
    check("o8_test_refit_exponent", close(oos["test_refit"]["b"], 0.9773, 1e-3))
    check("o9_exponent_drift", close(oos["exponent_drift"], -0.0585, 1e-3))

    # --- SS4.3 closure: the two "physical" scales are ruled out
    check("c1_train_cells", clo["train_cells"] == 48, clo["train_cells"])
    check("c2_test_cells", clo["test_cells"] == 48, clo["test_cells"])
    check("c3_robust_cells", clo["robust_cells"] == 16, clo["robust_cells"])
    f = clo["forms_scored_on_unseen_cells"]
    check("c4_H_gamma_best_of_named", close(f["H_gamma"]["median_rel_err"], 0.1418, 1e-3))
    check("c5_H_const", close(f["H_const"]["median_rel_err"], 0.2296, 1e-3))
    check("c6_one_constant", close(clo["one_constant"]["c"], 2.9818, 1e-3))
    check("c7_more_params_not_better", f["H_beta"]["median_rel_err"] > f["H_const"]["median_rel_err"])
    # "the gap form is off by a factor of ~100% at the median and is catastrophic in the tail"
    check("c8_H_gap_median_off_by_100pct", f["H_gap"]["median_rel_err"] > 0.9)
    check("c9_H_gap_catastrophic_tail", f["H_gap"]["max_rel_err"] > 25.0)
    check("c10_H_gap2_beaten_by_H_const",
          f["H_gap2"]["median_rel_err"] > f["H_const"]["median_rel_err"])
    check("c11_H_scale_worst", f["H_scale"]["median_rel_err"] > 1.5)
    ag = clo["A_by_gamma"]
    vals = [ag[str(g)]["median"] for g in (0.25, 0.5, 1.0, 2.0)]
    check("c12_A_by_gamma_values", all(close(a, b, 1e-3) for a, b in
                                       zip(vals, [2.904, 2.686, 2.548, 2.388])), vals)
    check("c13_A_falls_weakly_with_gamma", vals[0] > vals[3])
    ad = clo["A_by_distribution"]
    check("c14_A_distribution_robust",
          max(abs(ad[d]["median"] - ad["uniform"]["median"]) / ad["uniform"]["median"]
              for d in ad) < 0.03, {k: v["median"] for k, v in ad.items()})
    eg = clo["exponent_by_gamma"]
    check("c15_exponent_near_one", all(close(eg[str(g)], 1.0, 3e-2) for g in (0.5, 1.0, 2.0)), eg)

    # --- SS4.3/SS5 the residual is not white, and reported
    am = lg["A_by_m"]
    med = [am[str(m)]["median"] for m in (1, 2, 4, 8, 16)]
    check("c16_A_by_m_values", all(close(a, b, 1e-3) for a, b in
                                   zip(med, [3.997, 2.777, 2.388, 2.513, 2.531])), med)
    check("c17_A_highest_at_m1", med[0] == max(med))
    usable = [c for c in lg["cells"] if c.get("A")]
    check("c18_law_cells", len(lg["cells"]) == 250, len(lg["cells"]))
    check("c19_law_usable", len(usable) == 240, len(usable))
    A = [c["A"] for c in usable]
    check("c20_A_median", close(sorted(A)[len(A) // 2], 2.734, 1e-2))
    check("c21_A_range", close(min(A), 1.612, 1e-2) and close(max(A), 13.570, 1e-2))
    check("c22_A_spread", close(max(A) / min(A), 8.42, 1e-2))
    sub = [c["A"] for c in usable if c["planner_per_task"] >= 0.2]
    check("c23_A_spread_narrowed_by_p_floor", close(max(sub) / min(sub), 3.37, 2e-2),
          (len(sub), max(sub) / min(sub)))

    # --- SS4.4 the law is attention-model agnostic
    aa = clo["attention_agnostic"]
    b = aa["budget_cells_at_same_cost_scale"]
    fr = aa["fraction_cells_never_fitted"]
    check("m1_budget_cells", b["n"] == 24, b["n"])
    check("m2_budget_constant", close(b["constant"], 2.5073, 1e-3))
    check("m3_fraction_cells_unfitted", aa["n"] == 12 and fr["median_rel_err"] < 0.2)
    check("m4_fraction_median_A", close(fr["median_A"], 2.232, 1e-2), fr["median_A"])
    check("m5_fraction_not_worse_than_budget",
          fr["median_rel_err"] <= b["median_rel_err"], (fr["median_rel_err"], b["median_rel_err"]))
    check("m6_cross_scale_constant_worse",
          aa["cross_cost_scale_constant_for_contrast"]["median_rel_err"] > fr["median_rel_err"])

    # --- SS4.5 the mechanism is scrambling (not mismatch)
    om = mech["oracle_mismatch_rate"]
    check("k1_oracle_mismatch_only_at_smallest_N", close(om[0]["rate"], 0.0594, 1e-3), om[0])
    check("k2_oracle_exactly_zero_above_N16", all(r["rate"] == 0.0 for r in om[1:]), om)
    ham = [s for s in mech["hamming"] if s["gamma"] == 1.0 and s["beta"] == 0.5
           and s["sigma"] == 0.05]
    check("k3_hamming_series_found", len(ham) == 1)
    hr = [p["rate"] for p in ham[0]["series"]]
    check("k4_hamming_values", all(close(a, b, 2e-3) for a, b in
                                   zip(hr, [0.138, 0.237, 0.339, 0.483, 0.662])), hr)
    check("k5_hamming_grows_with_N", all(hr[i] < hr[i + 1] for i in range(len(hr) - 1)))
    wb = {s["beta"]: {p["N"]: p["rate"] for p in s["series"]}
          for s in mech["wrong_block_rate"] if s["gamma"] == 1.0 and s["sigma"] == 0.05}
    check("k6_wrong_block_exactly_zero_for_beta_ge_1",
          all(wb[b][N] == 0.0 for b in wb if b >= 1.0 for N in wb[b]),
          {b: wb[b] for b in wb if b >= 1.0})

    # --- SS4.6 P3 is refuted by ablation
    check("q1_boundary_survives_specialisation_off",
          p3["specialisation_off_boundary_still_exists"] is True)
    ss = p3["sigma_star_specialisation_off"]
    check("q2_sigma_star_values", all(close(ss[str(N)], v, 3e-3) for N, v in
                                      ((16, 0.410), (64, 0.570), (256, 0.739))), ss)
    amp = p3["amplification_beta_max_over_beta_0"]
    check("q3_amplification_constant",
          all(close(amp[str(N)], v, 5e-2) for N, v in ((16, 3.93), (64, 4.12), (256, 3.94))), amp)
    check("q4_market_is_oracle_at_sigma0",
          p3["market_regret_exactly_zero_when_information_perfect"] is True)
    check("q5_verdict_refuted", p3["verdict"] == "REFUTED", p3["verdict"])
    mb = p3["market_mismatch_by_beta_at_sigma_0.2"]
    check("q6_mismatch_zero_for_beta_ge_1",
          all(v == 0.0 for b, vals in mb.items() if float(b) >= 1.0 for v in vals), mb)
    check("q7_mismatch_degenerate_at_beta0", min(mb["0.0"]) > 0.7, mb["0.0"])

    # --- SS8 no wall-clock / environment fields anywhere in the artefact
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                yield path + "/" + k
                for x in walk(v, path + "/" + k):
                    yield x
        elif isinstance(o, list):
            for i, v in enumerate(o):
                for x in walk(v, "%s[%d]" % (path, i)):
                    yield x
    bad = [k for k in walk(d)
           if any(t in k.lower() for t in ("second", "elapsed", "wall", "time", "duration",
                                           "hostname", "timestamp", "date", "cwd", "python"))]
    check("t1_no_wallclock_or_env_fields", not bad, bad)

    # --- SS8 the committed figures exist and the manifest agrees with the artefact
    man_path = os.path.join(HERE, "figures", "manifest.json")
    check("g1_manifest_exists", os.path.exists(man_path))
    man = json.load(open(man_path, encoding="utf-8"))
    check("g2_manifest_three_figures", len(man["figures"]) == 3, len(man["figures"]))
    for fig in man["figures"]:
        p = os.path.join(HERE, "figures", fig["file"])
        check("g3_figure_present_%s" % fig["file"], os.path.exists(p) and os.path.getsize(p) > 1000)
        if os.path.exists(p):
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            check("g4_figure_digest_matches_manifest_%s" % fig["file"], h == fig["sha256"],
                  "%s != %s" % (h[:12], fig["sha256"][:12]))
    art_h = hashlib.sha256(open(ART, "rb").read()).hexdigest()
    check("g5_manifest_artefact_digest", man["artefact_sha256"] == art_h,
          "%s != %s" % (man["artefact_sha256"][:12], art_h[:12]))

    print("VALIDATE %d/%d" % (NCHECK[0] - len(FAILED), NCHECK[0]))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
