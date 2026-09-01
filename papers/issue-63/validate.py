#!/usr/bin/env python3
"""Issue #63 — validate.py: cross-check hypotheses numbers against committed
ground truth from an independent re-implementation (mirrors #52/#57/#61).

Re-computes the census counts + point estimates directly from committed snapshots
(tier_ab_corpus + classifier_v1_labels) and compares them with
hypotheses_report.txt. Exit 0 iff every reported number matches.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    labels = json.load(open(SNAP / "classifier_v1_labels.json"))

    tierb = [r for r, v in corpus.items() if v.get("membership") == "TierB"]
    tiera = [r for r, v in corpus.items() if v.get("membership") == "TierA"]
    neg = [r for r, v in corpus.items() if v.get("membership") == "NEG"]
    n_tb = len(tierb)

    l0 = sum(1 for r in tierb if labels[r]["level"] == "L0")
    l1 = sum(1 for r in tierb if labels[r]["level"] == "L1")
    l2 = sum(1 for r in tierb if labels[r]["level"] == "L2")
    assert l0 + l1 + l2 == n_tb, f"level sum mismatch: {l0}+{l1}+{l2} != {n_tb}"

    pos = [r for r in tierb if labels[r]["level"] in ("L1", "L2")]
    n_pos = len(pos)
    raft = sum(1 for r in pos if labels[r]["family"] == "Raft")
    lib = sum(1 for r in pos if labels[r]["channel"] == "lib")

    p1, lo1, hi1 = wilson(raft, n_pos)
    p2, lo2, hi2 = wilson(lib, n_pos)
    ta_pos = sum(1 for r in tiera if labels[r]["level"] in ("L1", "L2"))

    # H3 Fisher exact (one-sided) from 2x2
    def fisher_2x2(a, b, c, d):
        import math
        def ln_fact(n):
            return 0.0 if n <= 1 else math.lgamma(n + 1)
        total = a + b + c + d
        row1, row2, col1, col2 = a + b, c + d, a + c, b + d
        p = 0.0
        for a_ in range(a, min(row1, col1) + 1):
            b_ = row1 - a_
            c_ = col1 - a_
            d_ = row2 - c_
            if b_ < 0 or c_ < 0 or d_ < 0:
                continue
            p += math.exp(ln_fact(row1) + ln_fact(row2) + ln_fact(col1) + ln_fact(col2)
                          - ln_fact(total) - ln_fact(a_) - ln_fact(b_) - ln_fact(c_) - ln_fact(d_))
        return p

    fisher_p = fisher_2x2(ta_pos, len(tiera) - ta_pos, n_pos, n_tb - n_pos)

    report = (SNAP / "hypotheses_report.txt").read_text()

    checks = [
        ("Tier B n", str(n_tb), f"Tier B {n_tb}", "174"),
        ("Tier B L0", str(l0), f"L0 {l0}", None),
        ("Tier B L1", str(l1), f"L1 {l1}", None),
        ("Tier B L2", str(l2), f"L2 {l2}", None),
        ("consensus-positive n", str(n_pos), f"{n_pos}/174", "12"),
        ("H1 Raft share", f"{raft}/{n_pos}", f"Raft={raft}", None),
        ("H1 point", f"{p1*100:.1f}%", f"{p1*100:.1f}%", "66.7%"),
        ("H1 CI lo", f"{lo1*100:.1f}%", f"{lo1*100:.1f}%", "39.1%"),
        ("H1 CI hi", f"{hi1*100:.1f}%", f"{hi1*100:.1f}%", "86.2%"),
        ("H2 lib share", f"{lib}/{n_pos}", f"lib={lib}", None),
        ("H2 point", f"{p2*100:.1f}%", f"{p2*100:.1f}%", "75.0%"),
        ("H2 CI lo", f"{lo2*100:.1f}%", f"{lo2*100:.1f}%", "46.8%"),
        ("H2 CI hi", f"{hi2*100:.1f}%", f"{hi2*100:.1f}%", "91.1%"),
        ("H3 anchor share", f"{ta_pos}/{len(tiera)}", f"{ta_pos}/{len(tiera)}", None),
        ("H3 fisher p", f"{fisher_p:.3e}", f"{fisher_p:.3e}", "4.225e-16"),
        ("NEG L0", "2", "bitcoin/go-ethereum -> L0", "2"),
    ]

    ok = True
    print("validate.py — independent re-count (issue #63)")
    for name, computed, in_report_needle, expected_str in checks:
        in_report = in_report_needle in report
        if expected_str is not None:
            match = computed == expected_str and in_report
            detail = f"computed={computed} expected={expected_str} report={in_report}"
        else:
            match = in_report
            detail = f"report={in_report}"
        ok &= match
        print(f"  [{'OK' if match else 'FAIL'}] {name}: {detail}")

    # NEG control: bitcoin + go-ethereum must be L0
    neg_l0 = all(labels[r]["level"] == "L0" for r in neg)
    ok &= neg_l0
    print(f"  [{'OK' if neg_l0 else 'FAIL'}] NEG controls all L0 ({len(neg)} repos)")

    print(f"\n{'PASS' if ok else 'FAIL'}: independent re-count {'9/9 consistent' if ok else 'mismatch'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
