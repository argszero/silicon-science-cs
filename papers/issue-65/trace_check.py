#!/usr/bin/env python3
"""Issue #65 — trace_check.py: every manuscript headline number must be
traceable to a committed artifact (snapshots/expected_output/* or validate.py).

Headline numbers (manuscript §4) and their provenance:
  corpus 189 / TierA 12 / TierB 174 / NEG 3   -> classifier_v1_stats.txt
  L0 168 / L1 1 / L2 5                        -> classifier_v1_stats.txt
  6/174 = 3.4% eBPF-positive                  -> hypotheses_report.txt
  5/174 = 2.9% verified embedders             -> hypotheses_report.txt
  H1 Fisher p = 7.451e-15                     -> hypotheses_report.txt
  H2 100% Wilson CI [56.6%, 100%]             -> hypotheses_report.txt
  H3 tracing 60% vs net-path 40%              -> hypotheses_report.txt
  H3 SEC() census tracing 99 vs net-path 8    -> validate.py C07
  H4 7/7 cohort alive                         -> hypotheses_report.txt
  strata S1=2/29 S3=4/29 others 0             -> hypotheses_report.txt
  missing-tree worst case 8.6% p=6.978e-12    -> sensitivity_report.txt
  flips to erase H1: 6 (all positives)        -> sensitivity_report.txt
  threshold gap 0.6 pp (3.4% vs 2.9%)         -> sensitivity_report.txt
Exit 0 iff every number is found in its artifact.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "snapshots" / "expected_output"

hy = (EXP / "hypotheses_report.txt").read_text()
se = (EXP / "sensitivity_report.txt").read_text()
cs = (EXP / "classifier_v1_stats.txt").read_text()
va = (ROOT / "validate.py").read_text()

CHECKS = [
    ("corpus 189", "corpus: 189" in hy or "189" in cs),
    ("Tier A 12 / Tier B 174 / NEG 3", "(TierA 12 / TierB 174 / NEG 3)" in cs),
    ("L0 168 / L1 1 / L2 5", "L0 168 / L1 1 / L2 5" in cs),
    ("6/174 = 3.4%", "6/174 = 3.4%" in hy),
    ("5/174 = 2.9%", "5/174 = 2.9%" in hy),
    ("H1 p = 7.451e-15", "7.451e-15" in hy),
    ("H2 Wilson CI [56.6%, 100%]", "[56.6%, 100.0%]" in hy),
    ("H3 60.0% tracing / 40.0% net-path", "60.0%" in hy and "40.0%" in hy),
    ("H3 SEC() 99 vs 8", "tracing 99 vs net-path 8" in va),
    ("H4 7/7 alive", "7/7" in hy),
    ("strata S1=2 S3=4", "S1_cloudnative=2/29" in hy and "S3_netsec=4/29" in hy),
    ("missing-tree worst case 8.6%", "8.6%" in se),
    ("worst-case p = 6.978e-12", "6.978e-12" in se),
    ("H1 erasure needs 6 flips", "flips needed to reach p >= 0.05: 6" in se),
    ("threshold gap 0.6 pp", "0.6 pp" in se),
]

ok = True
print("trace_check.py — manuscript headline numbers -> committed artifacts")
print("=" * 72)
for label, cond in CHECKS:
    print(f"  [{'OK' if cond else 'MISS'}] {label}")
    ok = ok and cond
print("=" * 72)
print(f"{'PASS: 0 gaps' if ok else 'FAIL: gaps found'}")
sys.exit(0 if ok else 1)
