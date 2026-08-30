#!/usr/bin/env python3
"""Issue #48 — manuscript↔canonical-output traceability check.

Each needle must appear verbatim in expected_output/discovery_results.txt.
Ensures the manuscript narrative and the frozen canonical run tell the same story.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FROZEN = (ROOT / "expected_output" / "discovery_results.txt").read_text()

NEEDLES = {
    "H1 ROS2 432/568 = 76.06%": "SUMMARY: H1 CONFIRMED (ROS2 432/568 = 76.06%",
    "H1 ROS1 tail 131 = 23.06%": "ROS1 tail 131 = 23.06% all frozen/legacy lines",
    "H1 table 2 ROS2 count": "ROS2: 432/568 = 76.06%",
    "H1 table 2 ROS1 count": "ROS1: 131/568 = 23.06%",
    "H2 tier gradient C 100.0%": "Tier C 100.0% > Tier D 70.0% > Tier B 61.7% > Tier A 49.1%",
    "H3 0/432 ROS2 with ROS1 deps": "ROS2 packages declaring any ROS1-only dependency: 0/432",
    "H3 hermetic finding": "migration is hermetic — no package mixes ROS1 and ROS2 client stacks",
    "validation 23 cells 1.000": "accuracy 1.000 (ROS1 10/10, ROS2 10/10, none 3/3",
    "summary lines": "SUMMARY: H3 FALSIFIED (0/432 ROS2 packages carry ROS1-only deps",
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
