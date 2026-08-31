#!/usr/bin/env python3
"""Issue #52 — traceability check (trace_check.py).

Every manuscript headline number must appear verbatim in the canonical
expected_output/discovery_results.txt. Fails if any needle is missing.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FROZEN = (ROOT / "expected_output" / "discovery_results.txt").read_text()

NEEDLES = [
    "32 open-source repositories",
    "16 era-pairs",
    "C-side repos with ANY Rust component: 2/16",
    "git/git 10.5%",
    "google/boringssl 11.1%",
    "Rust-side repos >=90% Rust: 14/16",
    "MIXED-language components: 1 (0.4%)",
    "BINDING 1/16",
    "REWRITE 15/16",
    "accuracy 1.000",
    "disagreement 2/7",
]

ok = True
for n in NEEDLES:
    hit = n in FROZEN
    ok = ok and hit
    print(f"  {'OK ' if hit else 'MISSING'}  needle[{n}]")

print(f"traceability: {'ALL %d checks OK' % len(NEEDLES) if ok else 'FAILED'}")
raise SystemExit(0 if ok else 1)
