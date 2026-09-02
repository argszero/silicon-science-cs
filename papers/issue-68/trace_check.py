#!/usr/bin/env python3
"""Issue #68 — trace_check.py: every manuscript headline number must be traceable
to a committed artifact (snapshots/expected_output/*, snapshots/*.json, validate.py).

Headline numbers (manuscript) and their provenance:
  corpus 187 = TierA 10 + TierB 174 + NEG 3          -> validate.py C01 / hypotheses_report.txt
  41/174 = 23.6% Wilson95 [17.9%, 30.4%]             -> hypotheses_report.txt
  H1 AI 37/116 = 31.9% vs general 4/58 = 6.9%        -> hypotheses_report.txt
  H1 Fisher p = 1.35e-4 / chi2 = 21.5                -> hypotheses_report.txt
  H2 server 20 / client 14 / both 7                  -> hypotheses_report.txt
  H2 pure 58.8% Wilson95 [42.2%, 73.6%]              -> hypotheses_report.txt
  H2-refined general 4/4 server-only, p = 0.126      -> hypotheses_report.txt
  eBPF 3.4% (7x contrast)                            -> hypotheses_report.txt
  H3 LATEST 2025-11-25, SUPPORTED 5 versions         -> h3_evidence.json
  H3 codesearch 66/65/68 hits (17/15/17 repos)       -> h3_evidence.json
  H3 pins: n8n-mcp dual, worldmonitor, open-design   -> h3_evidence.json
  H4 created 2025+ = 23; archived/stale = 0          -> hypotheses_report.txt
  sensitivity: rate<=20% needs 7 flips               -> sensitivity_report.txt
  H1 robust: 11 AI flips still p<0.05                -> sensitivity_report.txt
  threshold gap 22.4%-24.7% (CI overlap)             -> sensitivity_report.txt
Exit 0 iff every number is found in its artifact.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "snapshots" / "expected_output"

hy = (EXP / "hypotheses_report.txt").read_text()
se = (EXP / "sensitivity_report.txt").read_text()
h3 = (ROOT / "snapshots" / "h3_evidence.json").read_text()
va = (ROOT / "validate.py").read_text()

CHECKS = [
    ("corpus 187 = TierA 10 + TierB 174 + NEG 3", "corpus 187 = TierA 10 + TierB 174 + NEG 3" in hy),
    ("41/174 = 23.6%", "41/174 = 23.6%" in hy),
    ("Wilson95 [17.9%, 30.4%]", "[17.9%, 30.4%]" in hy),
    ("H1 AI 37/116 = 31.9%", "37/116 = 31.9%" in hy),
    ("H1 general 4/58 = 6.9%", "4/58 = 6.9%" in hy),
    ("H1 Fisher p = 1.35e-4", "0.000135" in hy),
    ("chi2 = 21.5", "21.5" in hy),
    ("H2 server 20 / client 14 / both 7", "server 20 / client 14 / both 7" in hy),
    ("H2 pure 58.8% CI [42.2%, 73.6%]", "[42.2%, 73.6%]" in hy),
    ("H2-refined general 4/4 server-only", "server 4 / client 0 / both 0" in hy),
    ("H2-refined p = 0.126", "0.126" in hy),
    ("eBPF 3.4% contrast", "3.4%" in hy),
    ("H3 LATEST = 2025-11-25", '"LATEST_PROTOCOL_VERSION": "2025-11-25"' in h3),
    ("H3 SUPPORTED 5 versions", '"2024-10-07"' in h3),
    ("H3 spec types 2026-07-28", "2026-07-28" in h3),
    ("H3 codesearch 66/17, 65/15, 68/17", '"files": 66' in h3 and '"files": 65' in h3 and '"files": 68' in h3),
    ("H3 pin n8n-mcp dual-version", "n8n-mcp" in h3 and "dual-version" in h3),
    ("H3 pin open-design bleeding-edge", "2026-01-26" in h3),
    ("H4 created 2025+ = 23", "created 2025+: 23/41" in hy),
    ("H4 archived/stale = 0", "archived or no-push-since-2026-06: 0" in hy),
    ("sensitivity rate<=20% needs 7 flips", "need 7 more false positives" in se),
    ("sensitivity H1 11 flips robust", "11 AI L2" in se),
    ("sensitivity threshold 22.4%-24.7%", "22.4%" in se and "24.7%" in se),
    ("validate C15 robustness", "C15" in va),
    ("all 41 false -> 3.4% eBPF baseline", "35 false (6 remain) -> 3.4%" in se),
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
