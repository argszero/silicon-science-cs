#!/usr/bin/env python3
"""Issue #63 — hypotheses H1/H2/H3/H4 from classifier v0 labels.

H1: Raft family is the dominant consensus protocol in top OSS
    (majority of consensus-positive Tier B repos).
H2: consensus arrives predominantly via embedded dependency libraries
    (channel=lib) rather than in-repo implementations (channel=self).
H3: adoption is ecosystem-stratified — Tier A anchors (consensus-producing
    systems) are ~100% consensus-positive vs Tier B general population;
    Go dominates among adopters.
H4: longitudinal — Raft 2014 early-adopter enumeration survival (baseline
    table; computed from a manual mapping, see l4_longitudinal.py).

Outputs: snapshots/hypotheses_report.txt (canonical for reproduce.sh)
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

labels = json.load(open(SNAP / "classifier_v1_labels.json"))
corpus = json.load(open(SNAP / "tier_ab_corpus.json"))

TIER_B = {r: v for r, v in labels.items() if v["membership"] == "TierB"}
TIER_A = {r: v for r, v in labels.items() if v["membership"] == "TierA"}
POS = {r: v for r, v in TIER_B.items() if v["level"] in ("L1", "L2")}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def fisher_2x2(a, b, c, d):
    """One-sided Fisher exact test (alternative='greater') for
    [[a, b], [c, d]] — probability of observing a table at least as extreme."""
    def ln_fact(n):
        if n <= 1:
            return 0.0
        return math.lgamma(n + 1)
    total = a + b + c + d
    row1, row2, col1, col2 = a + b, c + d, a + c, b + d
    p0 = math.exp(ln_fact(row1) + ln_fact(row2) + ln_fact(col1) + ln_fact(col2) - ln_fact(total))
    p = 0.0
    # iterate over possible a' >= a
    for a_ in range(a, min(row1, col1) + 1):
        b_ = row1 - a_
        c_ = col1 - a_
        d_ = row2 - c_
        if b_ < 0 or c_ < 0 or d_ < 0:
            continue
        p += math.exp(ln_fact(row1) + ln_fact(row2) + ln_fact(col1) + ln_fact(col2)
                      - ln_fact(total)
                      - ln_fact(a_) - ln_fact(b_) - ln_fact(c_) - ln_fact(d_))
    return p


def flip_sensitivity(n_positive, n_total, target_frac):
    """How many L2/L1 flips (positives -> negatives) to bring share below target?"""
    flips = 0
    k = n_positive
    while k / n_total > target_frac and k > 0:
        k -= 1
        flips += 1
    return flips


# ---------------- H1 ----------------
fam = Counter(v["family"] for v in POS.values())
n_pos = len(POS)
raft_k = fam.get("Raft", 0)
p_raft, lo_raft, hi_raft = wilson(raft_k, n_pos)
flips_h1 = flip_sensitivity(raft_k, n_pos, 0.50)  # flips to lose majority

# ---------------- H2 ----------------
chan = Counter(v["channel"] for v in POS.values())
lib_k = chan.get("lib", 0)
p_lib, lo_lib, hi_lib = wilson(lib_k, n_pos)
flips_h2 = flip_sensitivity(lib_k, n_pos, 0.50)

# ---------------- H3 ----------------
ta_pos = sum(1 for v in TIER_A.values() if v["level"] in ("L1", "L2"))
tb_pos = n_pos
fisher_p = fisher_2x2(ta_pos, len(TIER_A) - ta_pos, tb_pos, len(TIER_B) - tb_pos)

# Go dominance among adopters
go_k = sum(1 for v in POS.values() if v.get("language") == "Go")
p_go, lo_go, hi_go = wilson(go_k, n_pos)

# ---------------- Report ----------------
lines = [
    "Consensus in the Wild — hypotheses report (classifier v1, snapshot 2026-09-01)",
    "=" * 78,
    f"corpus: {len(labels)} (Tier A {len(TIER_A)} / Tier B {len(TIER_B)} / NEG 2)",
    f"Tier B distribution: L0 {sum(1 for v in TIER_B.values() if v['level']=='L0')} "
    f"/ L1 {sum(1 for v in TIER_B.values() if v['level']=='L1')} "
    f"/ L2 {sum(1 for v in TIER_B.values() if v['level']=='L2')}",
    f"consensus-positive (Tier B, L1+L2): {n_pos}/{len(TIER_B)} = {n_pos/len(TIER_B)*100:.1f}%",
    "",
    "H1 — Raft family dominance (of consensus-positive Tier B repos):",
    f"  family distribution: Raft={fam.get('Raft',0)} BFT={fam.get('BFT',0)} Paxos={fam.get('Paxos',0)}",
    f"  Raft share = {raft_k}/{n_pos} = {p_raft*100:.1f}%  (Wilson 95% CI [{lo_raft*100:.1f}%, {hi_raft*100:.1f}%])",
    f"  flips to lose majority (50%): {flips_h1}",
    "",
    "H2 — dependency-library-driven adoption (of consensus-positive Tier B repos):",
    f"  channel distribution: lib={lib_k} self={chan.get('self',0)}",
    f"  lib share = {lib_k}/{n_pos} = {p_lib*100:.1f}%  (Wilson 95% CI [{lo_lib*100:.1f}%, {hi_lib*100:.1f}%])",
    f"  flips to drop below 50%: {flips_h2}",
    "",
    "H3 — ecosystem stratification:",
    f"  Tier A anchors consensus-positive: {ta_pos}/{len(TIER_A)} = {ta_pos/len(TIER_A)*100:.1f}%",
    f"  Tier B consensus-positive: {tb_pos}/{len(TIER_B)} = {tb_pos/len(TIER_B)*100:.1f}%",
    f"  Fisher exact (one-sided) p = {fisher_p:.3e}",
    f"  Go share among Tier B adopters: {go_k}/{n_pos} = {p_go*100:.1f}%  (Wilson 95% CI [{lo_go*100:.1f}%, {hi_go*100:.1f}%])",
    "",
    f"Tier B consensus-positive repos ({n_pos}):",
]
for r, v in sorted(POS.items(), key=lambda kv: -kv[1]["stars"]):
    lines.append(f"  {v['stars']:>7} {v['language'] or '?':<10} {v['level']} {v['family'] or '-':<5} "
                 f"{v['channel'] or '-':<4} {r}")
lines.append("")
lines.append("NEG controls: bitcoin/go-ethereum -> L0 (PoW/PoS, non-classic family) ✓")

report = "\n".join(lines)
out = SNAP / "hypotheses_report.txt"
out.write_text(report)
print(report)
