"""Issue #47 -- FREEZE CHECK: every number in design_freeze_v1.md must have a home in an artefact.

A prose document that quotes numbers is a VIEW of the results files (lesson of R315-325).  This
script re-derives each quoted number from `sufficiency_v1_results.json` / `external_cell_v1_results.json`
or from the file digests themselves, and requires the rendered string to appear in the document.

The digest table is parsed, not trusted: for every row of the form a table row of file, label and 16-hex digest
the hex must equal the first 16 hex digits of sha256(file).  A stale digest is the exact failure this
catches.

Run: python3 freeze_check_v1.py     (writes freeze_check_v1_results.json)
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(HERE, "design_freeze_v1.md")
OUT = os.path.join(HERE, "freeze_check_v1_results.json")

rows, failures = [], []


def check(name, ok, detail=""):
    rows.append({"check": name, "pass": bool(ok), "detail": detail})
    if not ok:
        failures.append(name)
    print("%-6s %-62s %s" % ("PASS" if ok else "FAIL", name, detail))


def main():
    doc = io.open(DOC, encoding="utf-8").read()
    suf = json.load(io.open(os.path.join(HERE, "sufficiency_v1_results.json"), encoding="utf-8"))
    ext = json.load(io.open(os.path.join(HERE, "external_cell_v1_results.json"), encoding="utf-8"))

    def present(text, expected, label):
        ok = text == expected and doc.count(text) >= 1
        check("quote/%s" % label, ok, "doc has %r == %r (count %d)" % (text, expected, doc.count(text)))

    # ---- 1. the digest table: parsed and re-derived -----------------------------------------
    digest_rows = re.findall(r"^\| `([^`]+)`[^|]*\| `([0-9a-f]{16})` \|$", doc, re.M)
    check("digests/table_has_eight_rows", len(digest_rows) == 8, "found %d" % len(digest_rows))
    for fname, quoted in digest_rows:
        path = os.path.join(HERE, fname)
        real = hashlib.sha256(io.open(path, "rb").read()).hexdigest()[:16]
        check("digests/%s" % fname, real == quoted, "doc %s vs file %s" % (quoted, real))

    # ---- 1b. the post-registration amendment: a separate record, separately checked ----------
    # The registered table above must keep exactly its eight rows, so the certificate stage added
    # after registration is declared in its own section (F0b) in its own format, and checked here.
    # Folding it into the table would have rewritten the record of what was registered; leaving it
    # unchecked would have made the newest artefact the only unverified one.
    amend = re.search(r"## F0b\..*?(?=\n## )", doc, re.S)
    check("amendment/section_present", amend is not None,
          "F0b found" if amend else "no F0b section in the freeze document")
    # FAIL CLOSED, and without an early return: a missing section must make every amendment check
    # fail and the run exit non-zero.  The first version of this block called a `finish()` helper
    # that does not exist, so a missing F0b would have raised NameError instead of reporting -- a
    # guard whose failure mode is a crash is indistinguishable, to a reader of the exit status,
    # from one that works.
    text = amend.group(0) if amend is not None else ""
    pairs = re.findall(r"^- `([^`]+)` \u2014 sha256 \(first 16\) `([0-9a-f]{16})`$", text, re.M)
    check("amendment/declares_its_artefacts", len(pairs) == 2, "declared %d" % len(pairs))
    for fname, quoted in pairs:
        path = os.path.join(HERE, fname)
        present_ = os.path.exists(path)
        real = hashlib.sha256(io.open(path, "rb").read()).hexdigest()[:16] if present_ else None
        check("amendment/%s" % fname, present_ and real == quoted,
              "doc %s vs file %s" % (quoted, real))
    # The amendment must say WHAT it adds and WHAT it leaves alone -- an amendment that does not
    # state its scope is indistinguishable from a silent edit of the registered design.
    for phrase, label in (("criterion", "names the criterion it closes"),
                          ("UNMET", "names the state it replaces"),
                          ("no registered prior", "states what it does not change"),
                          ("F1", "names the claim section it leaves intact"),
                          ("F2", "names the scope limits it leaves intact")):
        check("amendment/%s" % label.replace(" ", "_"), phrase in text,
              "%r in F0b: %s" % (phrase, phrase in text))

    # ---- 2. sufficiency (step 6) ------------------------------------------------------------
    B = suf["part_B_matched_magnitude_witness"]["blocks"]
    witness = [b for b in B if b["problem"] == "ski" and b["profile"] == "unbiased_extreme"][0]
    check("suff/witness_gap_is_the_max_over_blocks",
          abs(witness["median_ratio_diff_plus_minus"]) == max(abs(b["median_ratio_diff_plus_minus"])
                                                              for b in B))
    present("%.4f" % witness["median_ratio_diff_plus_minus"], "-0.5679", "witness_gap")
    present("%.4f" % witness["mde_cluster_unit"], "0.0187", "witness_mde")
    present("%d/%d" % (witness["plus_arm_better"], witness["n_pairs"]), "16/16", "witness_replicates")
    present("%d/%d" % (suf["controls"]["C5_blocks_where_under_prediction_is_worse"],
                       suf["controls"]["C5_blocks_total"]), "31/39", "blocks_clearing_own_mde")
    present("%.2f" % suf["controls"]["C3_max_scalar_feature_gap_over_all_blocks"], "0.00", "scalar_gap")
    check("suff/the_witness_gap_is_stated_in_scientific_notation_too",
          "0.00e+00" in doc and suf["controls"]["C3_max_scalar_feature_gap_over_all_blocks"] == 0.0,
          "doc holds 0.00e+00 and the artefact holds exactly zero")
    # the list holds SIX rows: three matched-form and three form-confounded.  Keying by problem
    # alone silently keeps whichever came last, which is exactly how this check first failed --
    # a dict build that DISCARDS half its input is a defect in the check, not in the document.
    all_b = suf["part_C2_clean_and_confounded_contrasts"]["contrast_b_clean"]
    clean = {b["problem"]: b for b in all_b if "form-confounded" not in b["contrast"]}
    confounded = {b["problem"]: b for b in all_b if "form-confounded" in b["contrast"]}
    check("suff/the_contrast_list_decomposes_into_three_matched_and_three_confounded_rows",
          len(all_b) == 6 and len(clean) == 3 and len(confounded) == 3,
          "%d rows: %d matched-form, %d form-confounded" % (len(all_b), len(clean), len(confounded)))
    for prob, want in (("ski", "+1.48"), ("sched", "+2.61"), ("paging", "+0.97")):
        present("%+.2f" % clean[prob]["advantage_vs_MDE_cluster"], want, "clean_contrast_%s" % prob)
    even = {b["problem"]: b for b in suf["part_C2_clean_and_confounded_contrasts"]["control_c_even_target"]}
    for prob, want in (("ski", "-12.95"), ("sched", "-13.12"), ("paging", "-1.53")):
        present("%.2f" % even[prob]["advantage_vs_MDE_cluster"], want, "even_target_%s" % prob)
    for prob, want in (("ski", "-9.16"), ("sched", "+6.62"), ("paging", "-3.70")):
        present("%+.2f" % confounded[prob]["advantage_vs_MDE_cluster"], want,
                "confounded_contrast_%s" % prob)
    shift = suf["null_shift_from_the_even_target_adv_over_mde"]
    check("suff/the_null_shift_dictionary_agrees_with_the_control_rows",
          all(abs(shift[p] - even[p]["advantage_vs_MDE_cluster"]) < 1e-12 for p in shift),
          str({k: round(v, 2) for k, v in shift.items()}))

    # ---- 3. the external cell ---------------------------------------------------------------
    X1 = {b["problem"]: b for b in ext["tests"]["X1_order"]["blocks"]}
    for prob, want in (("ski", "0.744"), ("paging", "0.889"), ("sched", "1.000")):
        present("%.3f" % X1[prob]["kendall_tau_mean_vs_tail"], want, "tau_%s" % prob)
    for prob, want in (("ski", "0.697"), ("paging", "0.873"), ("sched", "1.000")):
        present("%.3f" % X1[prob]["tau_excluding_the_zero_anchor"], want, "tau_nozero_%s" % prob)
    c5 = ext["controls"]["C5_attachment_control"]
    for key, want in (("a_shared_attachment_exact_on_nonnegative_errors", "32/32"),
                      ("b_per_page_attachment_differs_on_the_same_information", "31/32"),
                      ("c_shared_attachment_differs_on_a_positive_BIAS_profile", "6/32")):
        present(c5[key], want, "c5_%s" % key.split("_")[0])
    X2 = {b["problem"]: b for b in ext["tests"]["X2_reach"]["blocks"]}
    present("%d of 13 profiles at or above 0.8%%, %d at or above 8.8%%"
            % (X2["ski"]["n_profiles_at_or_above_the_published_0.8pct"],
               X2["ski"]["n_profiles_at_or_above_the_published_8.8pct"]),
            "12 of 13 profiles at or above 0.8%, 11 at or above 8.8%", "reach_ski")
    present("%d of\n13" % X2["paging"]["n_profiles_at_or_above_the_published_0.8pct"],
            "0 of\n13", "reach_paging_zero")
    present("%.4f" % X2["paging"]["min"], "-0.4060", "paging_worst_unit_min")
    present("%.4f" % X2["sched"]["min"], "-0.3080", "sched_worst_unit_min")
    A = ext["anchor_published_numbers"]
    present("%.0f%%" % (A["mean_gain_over_classic"] * 100), "26%", "anchor_mean_gain")
    present("%.1f%%" % (A["implied_comparison_mean_gain"] * 100), "16.7%", "anchor_derived_mean")
    check("anchor/the_derived_mean_is_written_as_the_derivation",
          abs(A["implied_comparison_mean_gain"] - (1.26 / 1.08 - 1.0)) < 1e-15
          and "1.26 / 1.08 - 1.0" in doc)
    present("%.1f%% vs %.1f%%" % (A["worst_trace_degradation"] * 100,
                                  A["comparison_worst_trace_degradation"] * 100),
            "0.8% vs 8.8%", "anchor_worst_pair")
    check("cell/all_checks_pass", ext["ALL_PASS"] is True and suf["ALL_PASS"] is True,
          "external ALL_PASS=%s sufficiency ALL_PASS=%s" % (ext["ALL_PASS"], suf["ALL_PASS"]))
    check("cell/the_liveness_control_is_recorded_as_complete",
          json.load(io.open(os.path.join(HERE, "external_cell_mutation_v1_results.json"),
                            encoding="utf-8"))["all_targets_fired"] is True)

    out = {"n_checks": len(rows), "n_failed": len(failures), "failed": failures, "rows": rows,
           "ALL_PASS": not failures}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"checks": len(rows), "failed": failures, "ALL_PASS": not failures}, indent=1))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
