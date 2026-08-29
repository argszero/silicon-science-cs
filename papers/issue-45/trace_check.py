#!/usr/bin/env python3
"""Issue #45 — manuscript↔canonical-output traceability check.

Each needle must appear verbatim in expected_output/discovery_results.txt.
Ensures the manuscript narrative and the frozen canonical run tell the same story.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FROZEN = (ROOT / "expected_output" / "discovery_results.txt").read_text()

NEEDLES = {
    "H1 axe-family 6/14 = 42.86%": "axe-family runtime testing (axe-core/jest-axe/react-axe): 6/14 = 42.86%",
    "H1 < 50%": "SUMMARY: H1 CONFIRMED (axe-family 6/14 = 42.86% < 50%",
    "H1 axe concentration 6/6": "axe concentration: all runtime a11y testers use axe-family: YES (6/6)",
    "H1 lint-only 1/14": "lint-only (eslint-plugin-jsx-a11y, no runtime test): 1/14",
    "H1 none 7/14 = 50%": "no a11y testing or linting: 7/14 = 50.00%",
    "H2 density spread 52.3x": "density range (nonzero): 0.027 .. 1.413 = 52.3x spread",
    "H2 role coverage 0..28": "role coverage range: 0 .. 28 distinct roles",
    "H2 zero-density 3/14": "zero-density repos: 3/14",
    "H3 3/4 strict axe": "a11y-first axe-equipped 3/4 strict",
    "H3 density ratio 2.19x": "mean density 0.648 vs 0.296 = 2.19x",
    "H3 fluentui caveat": "fluentui density below overall median",
    "H3 ariakit caveat": "ariakit axe app-level only",
    "validation 56 cells 1.000": "precision 1.000 | recall 1.000 | accuracy 1.000 (TP=33 FP=0 TN=23 FN=0)",
    "summary lines": "SUMMARY: H1 CONFIRMED",
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
