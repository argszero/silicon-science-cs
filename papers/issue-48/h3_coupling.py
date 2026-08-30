#!/usr/bin/env python3
"""Issue #48 — H3 dependency-coupling analysis.

Question: do ROS1-only packages and their dependencies propagate migration lag?
Two complementary analyses:
  A. Intra-repo coupling: within each repo, packages whose deps include a
     ROS1-only package (in-repo or named) — the 'still-coupled' set.
  B. External ROS1 footprint: ROS2 packages declaring deps on known ROS1-only
     ecosystem packages (roscpp, rospy, actionlib, catkin, tf, rosbag, ...)
     — direct legacy coupling that survives in migrated repos.
"""
import json, re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent
cls = json.load(open(ROOT / "snapshots" / "package_classes.json"))
graph = json.load(open(ROOT / "snapshots" / "dep_graph.json"))

# TRUE ROS1-only ecosystem packages (no ROS2 port): the discriminating set.
# Dual-era packages (pluginlib, message_filters, nodelet, dynamic_reconfigure,
# rosgraph_msgs, tf2, ...) have ROS2 ports and are NOT legacy coupling.
ROS1_NAMES = {"roscpp", "rospy", "roslaunch", "rostest", "rosconsole", "actionlib",
              "roslib", "rospack", "catkin", "rosbag", "rosbag_storage",
              "rosgraph", "rosmaster", "roswtf", "tf", "rosunit", "xmlrpcpp",
              "roscpp_serialization", "roscpp_traits", "rosbag_migration_rule",
              "rosparam", "rosservice", "rossrv", "rostopic", "rosnode",
              "rosmsg", "rosdep", "rosmake", "message_generation"}

# B: ROS2 packages (class ROS2) declaring ROS1-only ecosystem deps
print("=" * 78)
print("B. ROS2-classified packages declaring ROS1-only ecosystem dependencies")
print("   (direct legacy coupling surviving inside migrated packages)")
print("=" * 78)
hits = []
for node, rec in graph.items():
    if rec["class"] != "ROS2":
        continue
    legacy = sorted(set(rec["deps"]) & ROS1_NAMES)
    if legacy:
        hits.append((node, legacy))
print(f"ROS2 packages with ROS1-only deps: {len(hits)} / {sum(1 for r in graph.values() if r['class']=='ROS2')}")
for node, legacy in sorted(hits):
    print(f"  {node:78s} -> {legacy}")
legacy_counter = Counter()
for _, legacy in hits:
    legacy_counter.update(legacy)
print()
print("legacy dep frequency:", dict(legacy_counter.most_common(12)))

# A: intra-repo coupling — for each repo, ROS1-only packages present, and which
# other packages (any class) in the SAME repo depend on them by name
print()
print("=" * 78)
print("A. Intra-repo coupling: in-repo packages depending on in-repo ROS1-only packages")
print("=" * 78)
total_coupled = 0
for repo, recs in cls.items():
    r1_in = {r["path"].split("/")[-1].replace(".xml", "") for r in recs if r["class"] == "ROS1"}
    if not r1_in:
        continue
    repo_graph = {k: v for k, v in graph.items() if k.startswith(repo + "::")}
    coupled = []
    for node, rec in repo_graph.items():
        dep_names = set(rec["deps"])
        hit = dep_names & r1_in
        if hit and rec["class"] != "ROS1":  # already-ROS1 packages trivially coupled
            coupled.append((node, sorted(hit)))
    if coupled:
        total_coupled += len(coupled)
        print(f"\n{repo} — ROS1-only pkgs in repo: {sorted(r1_in)[:6]} ...")
        for node, hit in coupled[:5]:
            print(f"    {node.split('::')[1][:60]:60s} depends on {hit}")
print(f"\nnon-ROS1 packages coupled to in-repo ROS1-only packages: {total_coupled} total")
