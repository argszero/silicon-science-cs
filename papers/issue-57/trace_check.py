#!/usr/bin/env python3
"""Issue #57 — trace_check.py: verify the manuscript's core claims are backed
by committed artifacts (mirrors #52's traceability discipline).

Each needle is a claim string that MUST appear in the committed manuscript
(or the hypotheses report). Exit non-zero if any needle is missing.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
M = (ROOT / "manuscript.md").read_text() if (ROOT / "manuscript.md").exists() else ""
R = (ROOT / "snapshots" / "hypotheses_report.txt").read_text()

# (needle, where) — every core number in the manuscript must be traceable
NEEDLES = [
    ("68.2%", "H1 point estimate"),
    ("57.7%", "H1 CI lower bound"),
    ("48.1%", "H2 point estimate"),
    ("1.2%", "H3 point estimate"),
    ("58", "H1 SINGLE count"),
    ("27", "genuine MAS count"),
    ("13", "ORCH-WORKER count"),
    ("gpt-researcher", "H3 verified judge repo"),
    ("17", "H1 flip sensitivity"),
    ("86", "Tier B population"),
]

fails = 0
print("trace_check.py — manuscript claim traceability")
for needle, where in NEEDLES:
    # numbers must appear in the manuscript AND be derivable from the report
    in_ms = needle in M
    in_rep = needle in R
    ok = in_ms and in_rep
    if not ok:
        fails += 1
    print(f"  [{'OK' if ok else 'FAIL'}] '{needle}' ({where}): manuscript={in_ms} report={in_rep}")

# required files
FILES = [
    "manuscript.md", "README.md", "reproduce.sh", "validate.py", "trace_check.py",
    "hypotheses.py", "classifier_v3.py", "snapshots/hypotheses_report.txt",
    "snapshots/annotation/ground_truth.tsv",
    "snapshots/annotation/ground_truth_r105.tsv",
    "snapshots/annotation/ground_truth_r106.tsv",
    "snapshots/annotation/ground_truth_r107.tsv",
    "snapshots/annotation/pass_b.tsv", "snapshots/annotation/pass_b_r105.tsv",
    "snapshots/annotation/pass_b_r106.tsv", "snapshots/annotation/pass_b_r107.tsv",
]
print("\n  required committed files:")
for f in FILES:
    exists = (ROOT / f).exists()
    ok = exists
    if not ok:
        fails += 1
    print(f"  [{'OK' if ok else 'MISSING'}] {f}")

print(f"\n{'PASS' if fails == 0 else 'FAIL'}: {fails} traceability gaps")
sys.exit(0 if fails == 0 else 1)
