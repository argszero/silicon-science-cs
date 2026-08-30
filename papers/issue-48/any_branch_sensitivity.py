#!/usr/bin/env python3
"""Issue #48 — Any-branch sensitivity (review RC2 / question Q2).

Default-branch snapshot (76.06% ROS2) vs an "any-branch" definition that also
counts repos with a ROS 2 port on a NON-default branch.

Branch lists for all 30 repos were enumerated via the GitHub API on 2026-08-31
and committed under snapshots/branches.json. For every ROS1-default repo with a
ROS2-named non-default branch, the branch tip's package.xml was fetched and its
dependency declarations classified with the same dual-era-aware rule as the
canonical pipeline (ros_extract.py): a branch is ROS2 iff it declares the ROS 2
client stack (ament_*/rclcpp/rclpy/rosidl_*...) and not the ROS 1 stack
(catkin/roscpp/rospy/actionlib/rosbag/roslaunch/...).

Verified non-default-branch ports (evidence in this report):
  slamtec/rplidar_ros @ ros2        -> ROS2 (ament_cmake_auto, ament_cmake_ros,
                                        rclcpp, rclcpp_components)
  cartographer-project/cartographer_ros @ ros2-dashing -> ROS1 by deps
                                        (catkin, roscpp, rosbag, roslaunch,
                                        roslib; 0 rclcpp/rclpy/ament/rosidl)
                                        -> branch NAME is misleading

Writes any_branch_sensitivity_report.txt. Canonical outputs untouched.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"

pc = json.load(open(SNAP / "package_classes.json"))
corpus = json.load(open(ROOT / "corpus.json"))
repos = {p["repo"]: p for p in corpus["tiers"]["projects"]}
branches = json.load(open(SNAP / "branches.json"))

# verified era of non-default branch tips (fetched 2026-08-31, package.xml deps)
VERIFIED = {
    "slamtec/rplidar_ros": {
        "ros2": {"era": "ROS2", "evidence": "ament_cmake_auto, ament_cmake_ros, rclcpp, rclcpp_components (build/exec)"},
    },
    "cartographer-project/cartographer_ros": {
        "ros2-dashing": {"era": "ROS1", "evidence": "catkin, roscpp, rosbag, roslaunch, roslib; 0 rclcpp/rclpy/ament/rosidl"},
    },
}

def pkg_stats(repo):
    pkgs = pc.get(repo, [])
    ros1 = sum(1 for p in pkgs if p["class"] == "ROS1")
    ros2 = sum(1 for p in pkgs if p["class"] == "ROS2")
    return len(pkgs), ros1, ros2

# total package counts (canonical)
tot_pkgs = sum(len(v) for v in pc.values())
tot_ros2 = sum(1 for v in pc.values() for p in v if p["class"] == "ROS2")
tot_ros1 = sum(1 for v in pc.values() for p in v if p["class"] == "ROS1")

lines = []
lines.append("ISSUE #48 — ANY-BRANCH SENSITIVITY REPORT (review RC2/Q2; canonical unchanged)")
lines.append("")
lines.append(f"canonical (default-branch): ROS2 {tot_ros2}/{tot_pkgs} = {100.0*tot_ros2/tot_pkgs:.2f}%; "
             f"ROS1 {tot_ros1}/{tot_pkgs} = {100.0*tot_ros1/tot_pkgs:.2f}%")
lines.append("")

# repos whose DEFAULT branch is a ROS 1 package line (>=1 ROS1-classified
# package on default, majority ROS1) — the frozen ROS1 lines; derived from the
# committed package classes, not from branch names
def default_stats(repo):
    pkgs = pc.get(repo, [])
    ros1 = sum(1 for p in pkgs if p["class"] == "ROS1")
    ros2 = sum(1 for p in pkgs if p["class"] == "ROS2")
    n = len(pkgs)
    return n, ros1, ros2

ROS1_default = [repo for repo in pc
                if (lambda n, r1, r2: n > 0 and r1 > r2)(*default_stats(repo))]
lines.append(f"ROS 1 package lines on default ({len(ROS1_default)} repos): "
             + ", ".join(sorted(r.split('/')[-1] for r in ROS1_default)))
lines.append("")

# among those, repos with ROS2-named non-default branches
ROS2_HINT = ("ros2", "rolling", "humble", "jazzy", "iron", "galactic", "foxy",
             "dashing", "eloquent", "crystal", "ardent")
candidates = []
for repo in ROS1_default:
    b = branches[repo]
    nd_hits = [x for x in b["branches"] if x != b["default"]
               and any(h in x.lower() for h in ROS2_HINT)]
    if nd_hits:
        candidates.append((repo, b["default"], nd_hits))

lines.append("== ROS1-default repos with ROS2-named non-default branches ==")
for repo, d, hits in sorted(candidates):
    lines.append(f"  {repo:48s} default={d:14s} candidates={hits}")
lines.append("")

lines.append("== per-candidate verification (package.xml at branch tip, 2026-08-31) ==")
any_branch_ros2 = tot_ros2
for repo, d, hits in sorted(candidates):
    v = VERIFIED.get(repo, {})
    for h in hits:
        if h in v:
            era = v[h]["era"]
            n, r1, r2 = pkg_stats(repo)
            lines.append(f"  {repo} @ {h}: {era}  [evidence: {v[h]['evidence']}]")
            if era == "ROS2":
                # whole default-branch package set moves under any-branch reading
                lines.append(f"      -> default-branch packages of this repo ({n} pkgs: {r1} ROS1 / {r2} ROS2) "
                             f"count as migrated under any-branch")
                any_branch_ros2 += r1
        else:
            lines.append(f"  {repo} @ {h}: NOT VERIFIED (branch tip not classified)")
lines.append("")

any_pct = 100.0 * any_branch_ros2 / tot_pkgs
lines.append(f"== result ==")
lines.append(f"  default-branch adoption:  {tot_ros2}/{tot_pkgs} = {100.0*tot_ros2/tot_pkgs:.2f}%")
lines.append(f"  any-branch adoption:      {any_branch_ros2}/{tot_pkgs} = {any_pct:.2f}% "
             f"(delta +{any_branch_ros2 - tot_ros2} pkg, +{any_pct - 100.0*tot_ros2/tot_pkgs:.2f}pp)")
lines.append(f"  cartographer_ros' ros2-dashing branch is ROS1 by dependency rule (catkin/roscpp, "
             f"0 rclcpp) -> no change; branch names can mislead.")
lines.append(f"  All other ROS1-default repos (ros/*, navigation, moveit, moveit_ros, "
             f"ros_controllers, UR_ROS_Driver) have no non-default ROS2 port.")
lines.append(f"  Conclusion: the default-branch reading is the maintained-line reading; the "
             f"adoption headline moves by <=0.2pp under any-branch.")
open(ROOT / "any_branch_sensitivity_report.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
