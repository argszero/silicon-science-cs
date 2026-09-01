#!/usr/bin/env python3
"""Issue #61 — trace_check.py: verify every headline number in manuscript.md is
traceable to the committed hypotheses_report.txt (claim traceability, #52/#57 pattern).

Exit 0 iff all manuscript headline numbers appear in the report AND all required
committed files are present.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

REQUIRED_FILES = [
    "manuscript.md", "README.md", "reproduce.sh", "validate.py", "trace_check.py",
    "hypotheses.py", "classifier_v1.py", "content_probe.py", "extract_manifests.py",
    "snapshots/hypotheses_report.txt",
    "snapshots/tier_ab_corpus.json", "snapshots/tierb_candidates.json",
    "snapshots/pqc_dep_evidence.json", "snapshots/content_probe_evidence.json",
    "snapshots/classifier_v1_labels.json",
    "snapshots/annotation/ground_truth_r114.tsv",
]

# (label, string, source-report-pattern to verify presence)
TRACE_ITEMS = [
    ("H1 point estimate", "2.0%", r"L2\+L3 Tier B: \d+/\d+ = 2\.0%"),
    ("H1 CI lower", "0.8%", r"CI \[0\.8%, 5\.1%\]"),
    ("H1 CI upper", "5.1%", r"CI \[0\.8%, 5\.1%\]"),
    ("H2 point estimate", "91.1%", r"L1 share 91\.1%"),
    ("H2 CI lower", "79.3%", r"CI \[79\.3%, 96\.5%\]"),
    ("H3 anchor rate", "90.0%", r"= 90\.0%  vs"),
    ("Tier B population", "199", r"Tier B n=199"),
    ("L2 count", "4", r"L2\+L3 Tier B: 4/"),
    ("linux ML-DSA", "crypto/mldsa.c", r"crypto/mldsa\.c"),
    ("UK baseline", "44.0%", r"44\.0%"),
]


def main():
    ok = True
    print("trace_check.py — manuscript claim traceability (issue #61)")
    ms = (ROOT / "manuscript.md").read_text() if (ROOT / "manuscript.md").exists() else ""
    report = (SNAP / "hypotheses_report.txt").read_text()

    for name, needle, report_pat in TRACE_ITEMS:
        in_ms = needle in ms
        in_report = re.search(report_pat, report) is not None
        match = in_ms and in_report
        ok &= match
        print(f"  [{'OK' if match else 'FAIL'}] '{needle}' ({name}): manuscript={in_ms} report={in_report}")

    print("")
    print("  required committed files:")
    for f in REQUIRED_FILES:
        present = (ROOT / f).exists()
        ok &= present
        print(f"  [{'OK' if present else 'MISSING'}] {f}")

    print(f"\n{'PASS' if ok else 'FAIL'}: {'0 traceability gaps' if ok else 'gaps found'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
