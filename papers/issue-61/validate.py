#!/usr/bin/env python3
"""Issue #61 — validate.py: cross-check hypotheses numbers against committed
ground truth from an independent re-implementation (mirrors #52/#57 discipline).

Re-computes the census counts + point estimates directly from committed snapshots
(tier_ab_corpus + classifier_v1_labels + ground_truth_r114) and compares them with
hypotheses_report.txt. Exit 0 iff every reported number matches.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    import math
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    labels = json.load(open(SNAP / "classifier_v1_labels.json"))

    tierb = [r for r, v in corpus.items() if v.get("tier") == "B" and not v.get("is_anchor")]
    anchors = [r for r, v in corpus.items() if v.get("is_anchor")]
    n_tb = len(tierb)

    l1 = sum(1 for r in tierb if labels[r]["level"] == "L1_CAPABLE")
    l2 = sum(1 for r in tierb if labels[r]["level"] == "L2_DIRECT")
    l3 = sum(1 for r in tierb if labels[r]["level"] == "L3_ACTIVE")
    l0 = sum(1 for r in tierb if labels[r]["level"] == "L0_NONE")
    assert l0 + l1 + l2 + l3 == n_tb, f"level sum mismatch: {l0}+{l1}+{l2}+{l3} != {n_tb}"
    direct = l2 + l3
    p1 = direct / n_tb
    lo1, hi1 = wilson(direct, n_tb)

    positive = l1 + direct
    p2 = l1 / positive if positive else 0.0
    lo2, hi2 = wilson(l1, positive)

    a_lv = {}
    for r in anchors:
        a_lv[r] = labels[r]["level"]
    a_direct = sum(1 for lv in a_lv.values() if lv in ("L2_DIRECT", "L3_ACTIVE"))
    a_n = len(anchors)
    p3a = a_direct / a_n

    report = (SNAP / "hypotheses_report.txt").read_text()

    checks = [
        ("Tier B n", str(n_tb), re.search(r"Tier B n=(\d+)", report).group(1)),
        ("H1 L2+L3 count", str(direct), re.search(r"L2\+L3 Tier B: (\d+)/", report).group(1)),
        ("H1 point %", f"{100*p1:.1f}", re.search(r"= (\d+\.\d)%  Wilson", report).group(1)),
        ("H1 CI lower", f"{100*lo1:.1f}", re.search(r"CI \[(\d+\.\d)%,", report).group(1)),
        ("H1 CI upper", f"{100*hi1:.1f}", re.search(r"CI \[\d+\.\d%, (\d+\.\d)%\]", report).group(1)),
        ("H2 L1 count", str(l1), re.search(r"L1=(\d+), L2\+L3", report).group(1)),
        ("H2 point %", f"{100*p2:.1f}", re.search(r"L1 share (\d+\.\d)%", report).group(1)),
        ("H3 anchors direct", str(a_direct), re.search(r"anchors L2\+L3: (\d+)/", report).group(1)),
        ("H3 anchor %", f"{100*p3a:.1f}", re.search(r"= (\d+\.\d)%  vs", report).group(1)),
    ]
    ok = True
    print("validate.py — hypotheses cross-check (issue #61)")
    for name, got, want in checks:
        match = got == want
        ok &= match
        print(f"  [{'OK' if match else 'FAIL'}] {name}: got={got} report={want}")
    print(f"\n{'PASS' if ok else 'FAIL'}: {sum(1 for c in checks if c[1]==c[2])}/{len(checks)} checks")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
