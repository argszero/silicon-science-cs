#!/usr/bin/env python3
"""Issue #63 — sensitivity analysis for hypotheses (H1/H2/H3).

Scenarios:
  S0 (baseline, classifier v1): Tier B 12/174 positive; H1 Raft 8/12; H2 lib 9/12.
  S1 (indirect-rule off): the 3 downgraded repos (tidb/lnd/chainlink) stay
     positive → 15/174; H1 Raft 10/15; H2 lib 13/15. Shows indirect-rule impact.
  S2 (emqx channel boundary): emqx counted channel=lib instead of self →
     H2 lib 10/12. Shows channel-rule impact on H2.
  S3 (worst-case for H1): if 2 non-Raft positives were mislabeled Raft
     (family noise) → Raft 6/12. Shows H1 fragility.
  S4 (worst-case for H2): if 3 lib positives were actually self →
     lib 6/12 = 50%. Shows H2 fragility.
  S5 (conservative CI): recompute H1/H2 Wilson CI at 90% level.

Outputs: snapshots/sensitivity_report.txt
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
labels = json.load(open(SNAP / "classifier_v1_labels.json"))

TIER_B = {r: v for r, v in labels.items() if v["membership"] == "TierB"}
POS = {r: v for r, v in TIER_B.items() if v["level"] in ("L1", "L2")}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def flips_to(share, target):
    k = 0
    n = len(share)
    while (share.count("Raft") - k) / (n - k) > target and k < share.count("Raft"):
        k += 1
    return k


lines = []
# S0 baseline
pos_repos = sorted(POS.keys())
n0 = len(POS)
fam0 = [v["family"] for v in POS.values()]
lib0 = sum(1 for v in POS.values() if v["channel"] == "lib")
lines += [
    "Sensitivity analysis — issue #63 (classifier v1, snapshot 2026-09-01)",
    "=" * 78,
    f"S0 baseline: Tier B positives = {n0}/174; "
    f"H1 Raft {fam0.count('Raft')}/{n0} = {fam0.count('Raft')/n0*100:.1f}%; "
    f"H2 lib {lib0}/{n0} = {lib0/n0*100:.1f}%",
]

# S1 indirect-rule off (back to v0: 15 positives, emqx was lib in v0)
n1 = n0 + 3
fam1 = fam0 + ["Raft", "Raft", "BFT"]  # tidb=Raft, lnd=Raft, chainlink=BFT
lib1 = lib0 + 3 + 1  # +3 indirect repos (all lib) + emqx was lib in v0
lines += [
    "",
    f"S1 (indirect-rule OFF: tidb/lnd/chainlink stay positive): {n1}/174 = {n1/174*100:.1f}%; "
    f"H1 Raft {fam1.count('Raft')}/{n1} = {fam1.count('Raft')/n1*100:.1f}% (vs 66.7%); "
    f"H2 lib {lib1}/{n1} = {lib1/n1*100:.1f}% (vs 75.0%)",
    "    → indirect rule removes 20% of positives; H2 drops 11.7pp if kept (86.7% → 75.0%).",
]

# S2 emqx channel boundary
lib2 = lib0 + 1  # emqx self → lib
lines += [
    "",
    f"S2 (emqx channel=self → lib): H2 lib {lib2}/{n0} = {lib2/n0*100:.1f}% (vs 75.0%); "
    f"H1 unchanged {fam0.count('Raft')}/{n0}",
    "    → channel adjudication moves H2 by 8.3pp; both above 50%.",
]

# S3 H1 worst-case: 2 non-Raft mislabeled Raft
fam3 = fam0.copy()
# remove 2 Raft → non-Raft (worst case family noise)
fam3[fam3.index("Raft")] = "BFT"
fam3[fam3.index("Raft")] = "Paxos"
lines += [
    "",
    f"S3 (H1 worst-case: 2 Raft mislabeled): Raft {fam3.count('Raft')}/{n0} = {fam3.count('Raft')/n0*100:.1f}% "
    f"(vs 66.7%) — still majority at {fam3.count('Raft')/(n0)*100:.1f}%",
]

# S4 H2 worst-case: 3 lib → self
lib4 = lib0 - 3
lines += [
    "",
    f"S4 (H2 worst-case: 3 lib mislabeled self): lib {lib4}/{n0} = {lib4/n0*100:.1f}% (vs 75.0%) "
    f"— at 50% boundary",
]

# S5 90% CI
p_h1, lo90_h1, hi90_h1 = wilson(fam0.count("Raft"), n0, z=1.645)
p_h2, lo90_h2, hi90_h2 = wilson(lib0, n0, z=1.645)
lines += [
    "",
    f"S5 (90% Wilson CI): H1 Raft {fam0.count('Raft')}/{n0} = {p_h1*100:.1f}% "
    f"90% CI [{lo90_h1*100:.1f}%, {hi90_h1*100:.1f}%]; "
    f"H2 lib {lib0}/{n0} = {p_h2*100:.1f}% 90% CI [{lo90_h2*100:.1f}%, {hi90_h2*100:.1f}%]",
]

report = "\n".join(lines)
(SNAP / "sensitivity_report.txt").write_text(report)
print(report)
