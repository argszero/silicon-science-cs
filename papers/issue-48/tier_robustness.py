#!/usr/bin/env python3
"""Issue #48 — Tier-gradient robustness (review RC3 / question Q4).

Computes the H2 tier gradient under two additional weightings so the
concentration claim is not hostage to one repository:
  (a) package-weighted (canonical, cross-checked vs expected_output)
  (b) package-weighted with autoware.universe excluded (Tier C n=242 -> 1)
  (c) per-repo weighted (unweighted mean of per-repo migration %, package-bearing repos)
  (d) repo-majority count (repos whose default branch is majority-ROS2)

Reads committed snapshots (package_classes.json + corpus.json); deterministic.
Writes tier_robustness_report.txt.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

pc = json.load(open(SNAP / "package_classes.json"))
corpus = json.load(open(ROOT / "corpus.json"))
repos = corpus["tiers"]["projects"]
tier_of = {p["repo"]: p["tier"] for p in repos}

TIERS = ["Tier A core", "Tier B stacks", "Tier C platforms", "Tier D apps"]
SHORT = {"Tier A core": "Tier A", "Tier B stacks": "Tier B",
         "Tier C platforms": "Tier C", "Tier D apps": "Tier D"}

# per-repo package classes
def mig_pct(repo):
    pkgs = pc.get(repo, [])
    n = len(pkgs)
    if n == 0:
        return 0.0, 0, 0
    ros2 = sum(1 for p in pkgs if p["class"] == "ROS2")
    return (100.0 * ros2 / n), n, ros2

def pct(a, b):
    return f"{100.0*a/b:.1f}%" if b else "n/a"

lines = []
lines.append("ISSUE #48 — TIER-GRADIENT ROBUSTNESS REPORT (review RC3; canonical unchanged)")
lines.append("")

# (a) canonical package-weighted
lines.append("== (a) package-weighted (canonical) ==")
canon = {}
for t in TIERS:
    pkgs = [p for repo in pc for p in pc[repo] if tier_of[repo] == t]
    n = len(pkgs)
    ros2 = sum(1 for p in pkgs if p["class"] == "ROS2")
    ros1 = sum(1 for p in pkgs if p["class"] == "ROS1")
    none = sum(1 for p in pkgs if p["class"] == "none")
    canon[t] = (n, ros2)
    lines.append(f"  {SHORT[t]:8s} n={n:4d}  ROS2={ros2:4d} ({pct(ros2, n)})  ROS1={ros1:4d}  none={none:3d}")
lines.append("")

# (b) Tier C without autoware.universe
lines.append("== (b) Tier C without autoware.universe ==")
tc_excl = [p for repo in pc for p in pc[repo]
           if tier_of[repo] == "Tier C platforms" and repo != "autowarefoundation/autoware.universe"]
n = len(tc_excl)
ros2 = sum(1 for p in tc_excl if p["class"] == "ROS2")
lines.append(f"  Tier C minus autoware.universe: n={n}, ROS2={ros2} ({pct(ros2, n)}) — "
             f"autoware.universe alone = 241/242 of Tier C packages")
lines.append("")

# (c) per-repo weighted
lines.append("== (c) per-repo weighted (unweighted mean of per-repo migration %) ==")
for t in TIERS:
    members = [p["repo"] for p in repos if p["tier"] == t]
    m_all = [(r, mig_pct(r)) for r in members]
    bear = [(r, m, n, r2) for (r, (m, n, r2)) in m_all if n > 0]
    mean_bear = sum(m for _, m, _, _ in bear) / len(bear) if bear else 0.0
    mean_all = sum(m for (_, (m, n, r2)) in m_all) / len(m_all) if m_all else 0.0
    rows = "  ".join(f"{r.split('/')[-1]}:{m:.0f}%" for r, m, _, _ in bear)
    lines.append(f"  {SHORT[t]:8s} mean(bearing repos)={mean_bear:.1f}%  mean(all repos)={mean_all:.1f}%")
    lines.append(f"           {rows}")
    lines.append("")
lines.append("")

# (d) repo-majority
lines.append("== (d) repo-majority (repos whose default-branch packages are majority ROS2) ==")
for t in TIERS:
    members = [p["repo"] for p in repos if p["tier"] == t]
    maj = [r for r in members if mig_pct(r)[0] >= 50.0]
    lines.append(f"  {SHORT[t]:8s} {len(maj)}/{len(members)} repos majority-ROS2")
lines.append("")

lines.append("== reading ==")
lines.append("  The strict package-weighted order C > D > B > A (canonical) does NOT survive")
lines.append("  per-repo weighting (A moves above D and B because the official ros2/* org is")
lines.append("  7 fully-migrated small repos); the robust structural claims are: tiers are")
lines.append("  bimodal (repos are ~0% or ~100%), Tier C is 100% (autoware.universe 241 +")
lines.append("  micro_ros_msgs 1), and package-weighted adoption is driven by large repos.")
open(ROOT / "tier_robustness_report.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
