#!/usr/bin/env python3
"""Issue #38 — traceability check: manuscript numbers vs canonical expected output.

Every core number in manuscript.md must appear in expected_output/discovery_results.txt
(or be recomputed by validate.py). Exit 0 iff all checks pass. Run after reproduce.sh.
"""
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

NEEDLES = [
    # (manuscript claim, needle in canonical output)
    ("1254 program sources", "TOTAL: 1254 BPF program sources"),
    ("5474 SEC instances", "5474 instances"),
    ("H1 top-3 = 58.4%", "top-3 families (tracing+socket+TC) 3197/5474 = 58.4%"),
    ("H1 top-4 = 66.0%", "top-4 (incl. other) 3611/5474 = 66.0%"),
    ("broad census 15339/1091", "15339 calls, 1091 distinct"),
    ("broad top-20 = 34.6%", "top-20 34.6%"),
    ("canonical 9301/215/216", "9301 calls, 215 distinct of 216"),
    ("canonical top-10 = 50.0%", "top-10 50.0%"),
    ("canonical top-20 = 62.5%", "top-20 62.5%"),
    ("canonical top-50 = 79.6%", "top-50 79.6%"),
    ("map_lookup_elem 1581 17.0%", "bpf_map_lookup_elem               1581  (17.0%)"),
    ("bpf2bpf 246 19.6%", "bpf2bpf            246 files  (19.6%)"),
    ("tail_calls 53 4.2%", "tail_calls          53 files  (4.2%)"),
    ("perfbuf 40 3.2%", "perfbuf             40 files  (3.2%)"),
    ("ringbuf 24 1.9%", "ringbuf             24 files  (1.9%)"),
    ("arena 18 1.4%", "arena               18 files  (1.4%)"),
    ("bounded_loops 13 1.0%", "bounded_loops       13 files  (1.0%)"),
    ("kernel n=1076", "kernel 1076"),
    ("production n=178", "production 178"),
    ("bpf2bpf 15.2/46.1", "bpf2bpf               15.2%      46.1%"),
    ("bounded_loops 0.2/6.2", "bounded_loops          0.2%       6.2%"),
    ("perfbuf 0.9/16.9", "perfbuf                0.9%      16.9%"),
    ("tail_calls 4.0/5.6", "tail_calls             4.0%       5.6%"),
    ("ringbuf 2.0/1.1", "ringbuf                2.0%       1.1%"),
    ("arena 1.7/0.0", "arena                  1.7%       0.0%"),
    ("H1 production-only 628/800 78.5%", "top-2 named families (tracing+kprobe) 628/800 = 78.5%"),
    ("H1 production-only top-3 726/800 90.8%", "top-3 (incl. other) 726/800 = 90.8%"),
    ("H2 production-only 2550/214", "2550 calls, 214 distinct; top-10 50.9% | top-20 63.4%"),
    ("helper non-canonical 878 names", "878 distinct non-canonical names"),
    ("singleton non-canonical 241", "singleton non-canonical names (1 call each): 241"),
]

def main():
    txt = (ROOT / "expected_output" / "discovery_results.txt").read_text()
    fails = [label for label, needle in NEEDLES if needle not in txt]
    # validation metrics from committed sample + indexes
    r = subprocess.run([sys.executable, "validate.py"], capture_output=True, text=True)
    vout = r.stdout
    for claim, needle in [("TP=19", "TP=19"), ("precision 0.950", "precision=0.950"),
                          ("recall 1.000", "recall=1.000"), ("accuracy 0.975", "accuracy=0.975"),
                          ("wilson precision CI", "wilson95 precision=[0.764,0.991]"),
                          ("wilson recall CI", "recall=[0.832,1.000]"),
                          ("wilson accuracy CI", "accuracy=[0.871,0.996]")]:
        if needle not in vout:
            fails.append(claim)
    if fails:
        print("TRACE FAIL:", *fails, sep="\n  ")
        return 1
    print(f"traceability: ALL {len(NEEDLES) + 4} checks OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
