"""Issue #47 -- MUTATION CONTROL for the external cell.

A check that never fires is decoration (lesson of R280-R301, re-learned every round).  So: for every
named check in `external_cell_v1.py`, corrupt a THROWAWAY COPY textually so that the claim it
asserts becomes false, re-run the copy, and require that the named check FAILS.

Corrupting text, not monkeypatching, is deliberate: it exercises the code path the reader will run,
including the printed statement and the JSON it writes.

Each mutation is also required to be SURGICAL: it may fire its own check, and every other check must
stay green.  A mutation that trips half the file is not evidence that the target check works.

Run: python3 external_cell_mutation_v1.py     (writes external_cell_mutation_v1_results.json)
"""
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "external_cell_mutation_v1_results.json")
SRC = os.path.join(HERE, "external_cell_v1.py")
SCRATCH = os.path.join(HERE, "_mutant")

# (label, expected failing check, exact text to find, replacement)
MUTATIONS = [
    ("X1-published-pair-not-concordant",
     "X1/published_pair_is_concordant",
     'published_concordant = (ANCHOR["mean_gain_over_classic"] > ANCHOR["implied_comparison_mean_gain"]',
     'published_concordant = (ANCHOR["mean_gain_over_classic"] < ANCHOR["implied_comparison_mean_gain"]'),
    ("X1-harness-concordance-inverted",
     "X1/harness_is_concordant_in_every_problem",
     'and b["kendall_tau_mean_vs_tail"] > 0',
     'and b["kendall_tau_mean_vs_tail"] > 1.5'),
    ("X1-without-zero-anchor-inverted",
     "X1/concordance_survives_removing_the_zero_anchor",
     'and b["tau_excluding_the_zero_anchor"] > 0 for b in X1)',
     'and b["tau_excluding_the_zero_anchor"] > 1.5 for b in X1)'),
    ("X2-reference-scale-wrong",
     "X2/the_reference_scale_is_the_published_pair",
     'abs(ref_lo - ANCHOR["worst_trace_degradation"]) < 1e-15',
     'abs(ref_lo - ANCHOR["worst_trace_degradation"]) < -1.0'),
    ("X2-counts-name-other-blocks",
     "X2/the_counts_are_consistent_with_the_blocks_they_summarise",
     'and [b["problem"] for b in X2] == list(problems),',
     'and [b["problem"] for b in X2] == [],'),
    ("X3-harmful-policy-looks-helpful",
     "X3/an_explicitly_harmful_policy_is_reported_as_harm_in_every_problem",
     'all(b["mean_gain"] < 0 and b["worst_unit_degradation"] > 0 for b in X3)',
     'all(b["mean_gain"] > 0 and b["worst_unit_degradation"] > 0 for b in X3)'),
    ("C1-zero-error-degrades",
     "C1/zero_error_is_the_consistency_anchor_and_never_degrades",
     'all(g > 0 and d <= 1e-12 for _, g, d in ctl["C1_zero_error_both_arms"])',
     'all(g > 0 and d <= -1e-12 for _, g, d in ctl["C1_zero_error_both_arms"])'),
    ("C2-determinism-threshold-moved",
     "C2/same_arm_identical",
     'check("C2/same_arm_identical", ctl["C2_same_arm_identical"] == 0)',
     'check("C2/same_arm_identical", ctl["C2_same_arm_identical"] == -1)'),
    ("C3-hand-value-shifted",
     "C3/classic_implementations_match_hand_computed_values",
     '== {"fifo_cyclic_k1": 6, "lru_cyclic_k1": 6,',
     '== {"fifo_cyclic_k1": 7, "lru_cyclic_k1": 6,'),
    ("C4-degeneracy-threshold-moved",
     "C4/the_grid_is_not_degenerate",
     'all(v >= 4 for v in ctl["C4_profile_grid_distinct_mean_gains"].values())',
     'all(v >= 99 for v in ctl["C4_profile_grid_distinct_mean_gains"].values())'),
    ("C5a-invariance-claim-weakened",
     "C5a/shared_attachment_is_EXACTLY_invariant_to_non_negative_errors",
     'c5["a_shared_attachment_exact_on_nonnegative_errors"] == "%d/%d" % (4 * TRACES, 4 * TRACES)',
     'c5["a_shared_attachment_exact_on_nonnegative_errors"] == "0/32"'),
    ("C5b-non-invariance-claim-inverted",
     "C5b/the_per_page_attachment_is_NOT_invariant_on_the_same_information",
     'c5["b_per_page_attachment_differs_on_the_same_information"] != "0/%d" % (4 * TRACES,)',
     'c5["b_per_page_attachment_differs_on_the_same_information"] == "0/32"'),
    ("C5c-bias-vs-multiplier-claim-inverted",
     "C5c/a_positive_BIAS_profile_is_not_a_non_negative_MULTIPLIER",
     'c5["c_shared_attachment_differs_on_a_positive_BIAS_profile"] != "0/%d" % (4 * TRACES,)',
     'c5["c_shared_attachment_differs_on_a_positive_BIAS_profile"] == "0/32"'),
]


def parse_failures(stdout):
    out = []
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "FAIL":
            out.append(parts[1])
    return out


def main():
    base = io.open(SRC, encoding="utf-8").read()
    if os.path.isdir(SCRATCH):
        shutil.rmtree(SCRATCH)
    os.makedirs(SCRATCH)
    for f in ("instrument_v0.py", "paging_v1.py"):
        shutil.copy(os.path.join(HERE, f), os.path.join(SCRATCH, f))

    rows = []
    for label, expected, old, new in MUTATIONS:
        assert base.count(old) == 1, "mutation anchor not unique: %s (%d)" % (label, base.count(old))
        mutant = os.path.join(SCRATCH, "mutant_%s.py" % label)
        io.open(mutant, "w", encoding="utf-8").write(base.replace(old, new))
        proc = subprocess.run([sys.executable, os.path.basename(mutant)], cwd=SCRATCH,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout = proc.stdout.decode("utf-8", "replace")
        failed = parse_failures(stdout)
        rows.append({"mutation": label, "target": expected, "target_fired": expected in failed,
                     "all_failed": failed, "only_target": failed == [expected],
                     "returncode": proc.returncode})
        print("%-40s target %-6s fired=%s  failed=%d %s"
              % (label, "YES" if expected in failed else "NO", expected in failed, len(failed),
                 "" if failed == [expected] else failed))

    shutil.rmtree(SCRATCH)
    bad = [r["mutation"] for r in rows if not r["target_fired"]]
    not_surgical = [r["mutation"] for r in rows if not r["only_target"]]
    out = {"n_mutations": len(rows), "n_checks_in_target_file": 13,
           "all_targets_fired": not bad, "targets_that_did_not_fire": bad,
           "mutations_that_fired_more_than_their_target": not_surgical, "rows": rows}
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("n_mutations", "all_targets_fired",
                                          "targets_that_did_not_fire",
                                          "mutations_that_fired_more_than_their_target")}, indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
