#!/usr/bin/env python3
"""Issue #43 — manuscript↔canonical-output traceability check.

Each needle must appear verbatim in expected_output/discovery_results.txt.
Ensures the manuscript narrative and the frozen canonical run tell the same story.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FROZEN = (ROOT / "expected_output" / "discovery_results.txt").read_text()

NEEDLES = {
    "H1 harness 1/16 = 6.25%": "external eval-harness dependency (manifest-declared): 1/16 = 6.25%",
    "H1 llama_index tonic-validate": "run-llama/llama_index -> ['tonic-validate']",
    "H2 judge 7/16 = 43.75%": "judge-based evaluation present: 7/16 = 43.75%",
    "H3 validation 0/16": "repos with human-validation markers (hand-verified, mechanisms.json): 0/16",
    "H3 0/7 judge users": "validation among judge users: 0/7 (0.00%)",
    "self-contained 7/7": "built-in/hand-rolled self-contained: 7/7 of judge users",
    "tracing 6/16 = 37.50%": "tracing/observability deps: 6/16 = 37.50%",
    "mechanism distribution": "mechanism distribution:",
    "summary line": "SUMMARY: H1 CONFIRMED (harness 6.25%)",
}

failed = 0
for name, needle in NEEDLES.items():
    if needle in FROZEN:
        print(f"  OK  {name}")
    else:
        print(f"  FAIL {name} — needle not found in frozen output")
        failed += 1

print(f"traceability: {'ALL ' + str(len(NEEDLES)) + ' checks OK' if failed == 0 else str(failed) + ' FAILED'}")
raise SystemExit(1 if failed else 0)
