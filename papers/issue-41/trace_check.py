#!/usr/bin/env python3
"""Issue #41 — traceability check: manuscript numbers vs canonical expected output."""
import sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

NEEDLES = [
    ("12 implementations", "12 implementations +"),
    ("8 consumers", "8 consumers)"),
    ("H2 multipath 4/12", "multipath     4/12"),
    ("H2 migration 12/12", "migration    12/12"),
    ("H2 datagram 12/12", "datagram     12/12"),
    ("H2 pmtu 10/12", "pmtu         10/12"),
    ("H2 0rtt 11/12", "0rtt         11/12"),
    ("H1 ngtcp2 405", "ngtcp2         405"),
    ("H1 top-1 91.2%", "91.2%"),
    ("H1 quinn 7", "quinn            7"),
    ("H3 self-impl nginx", "self-implemented"),
    ("H3 self-impl haproxy", "self-implemented"),
]

def main():
    txt = (ROOT / "expected_output" / "discovery_results.txt").read_text()
    fails = [label for label, needle in NEEDLES if needle not in txt]
    r = subprocess.run([sys.executable, "validate.py"], capture_output=True, text=True)
    for claim, needle in [("precision 1.000", "precision=1.000"),
                          ("TP=10 FP=0", "TP=10 FP=0")]:
        if needle not in r.stdout:
            fails.append(claim)
    if fails:
        print("TRACE FAIL:", *fails, sep="\n  ")
        return 1
    print(f"traceability: ALL {len(NEEDLES) + 2} checks OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
