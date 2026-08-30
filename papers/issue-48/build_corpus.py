#!/usr/bin/env python3
"""Build corpus.json for issue #48 (ROS 1 -> ROS 2 migration census).

Balanced corpus: official ROS/ROS2 middleware orgs (fully-migrated bias) +
navigation/manipulation/control stacks (dual era) + simulation/autonomous-driving
+ application-level driver repos (long tail). Queries GitHub for default_branch,
head_sha and stars, then pins them.
"""
import json, subprocess, sys

REPOS = [
    # --- Tier A: official middleware / client libraries ---
    ("ros/ros",                "Tier A core", "ROS 1 metapackage"),
    ("ros/ros_comm",           "Tier A core", "ROS 1 communication stack"),
    ("ros/geometry2",          "Tier A core", "tf2 (ROS 1 branch)"),
    ("ros2/ros2",              "Tier A core", "ROS 2 metapackage"),
    ("ros2/rclcpp",            "Tier A core", "ROS 2 C++ client library"),
    ("ros2/rclpy",             "Tier A core", "ROS 2 Python client library"),
    ("ros2/rcl",               "Tier A core", "ROS 2 common libraries"),
    ("ros2/geometry2",         "Tier A core", "tf2 (ROS 2)"),
    ("ros2/launch",            "Tier A core", "ROS 2 launch system"),
    ("ros2/rosidl",            "Tier A core", "ROS 2 interface definitions"),
    ("ros2/rmw",               "Tier A core", "ROS 2 middleware abstraction"),
    # --- Tier B: stacks (navigation / manipulation / control) ---
    ("ros-navigation/navigation",    "Tier B stacks", "ROS 1 navigation stack"),
    ("ros-planning/navigation",      "Tier B stacks", "ROS 1 navigation stack (renamed home)"),
    ("ros-navigation/navigation2",   "Tier B stacks", "ROS 2 Nav2"),
    ("moveit/moveit",                "Tier B stacks", "MoveIt (ROS 1)"),
    ("moveit/moveit2",               "Tier B stacks", "MoveIt 2 (ROS 2)"),
    ("moveit/moveit_ros",            "Tier B stacks", "MoveIt ROS 1 plugins"),
    ("ros-controls/ros_controllers", "Tier B stacks", "ROS 1 controllers"),
    ("ros-controls/ros2_controllers","Tier B stacks", "ROS 2 controllers"),
    ("gazebosim/gazebo",             "Tier B stacks", "Gazebo Classic (ROS 1 era)"),
    ("gazebosim/gz-sim",             "Tier B stacks", "Gazebo Sim (ROS 2 era)"),
    # --- Tier C: autonomous driving / full platforms ---
    ("autowarefoundation/autoware",          "Tier C platforms", "Autoware.AI (ROS 1)"),
    ("autowarefoundation/autoware.universe", "Tier C platforms", "Autoware Universe (ROS 2)"),
    ("micro-ROS/micro_ros_msgs", "Tier C platforms", "ROS 2 on microcontrollers (msgs)"),
    # --- Tier D: application-level drivers (long tail) ---
    ("ros-drivers/joystick_drivers",      "Tier D apps", "joystick drivers (dual)"),
    ("realsenseai/realsense-ros",         "Tier D apps", "Intel RealSense driver (dual branches)"),
    ("cartographer-project/cartographer_ros", "Tier D apps", "Cartographer SLAM (ROS 1)"),
    ("UniversalRobots/Universal_Robots_ROS_Driver",   "Tier D apps", "UR ROS 1 driver"),
    ("UniversalRobots/Universal_Robots_ROS2_Driver",  "Tier D apps", "UR ROS 2 driver"),
    ("slamtec/rplidar_ros",               "Tier D apps", "RPLidar ROS 1 driver"),
    ("ros-perception/vision_opencv",      "Tier D apps", "cv_bridge / vision (dual)"),
]

def gh_json(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ! gh api {path} failed: {r.stderr[:120]}", file=sys.stderr)
        return None
    return json.loads(r.stdout)

def main():
    out = {
        "title": "ROS 2 in the Wild: A Corpus-Scale Census of ROS 1 → ROS 2 Migration",
        "issue": 48,
        "snapshot": "2026-08-30",
        "tiers": {"projects": []},
    }
    for repo, tier, role in REPOS:
        meta = gh_json(f"repos/{repo}")
        if meta is None:
            print(f"  SKIP {repo} (API fail)", file=sys.stderr)
            continue
        db = meta.get("default_branch", "master")
        ref = gh_json(f"repos/{repo}/git/ref/heads/{db}")
        sha = ref["object"]["sha"] if ref else None
        rec = {
            "repo": repo,
            "tier": tier,
            "role": role,
            "lang": meta.get("language"),
            "stars": meta.get("stargazers_count"),
            "default_branch": db,
            "head_sha": sha,
        }
        out["tiers"]["projects"].append(rec)
        print(f"  {repo:52s} {str(meta.get('stargazers_count')):>7s}★ {db:12s} {str(sha)[:10]}", flush=True)
    json.dump(out, open("corpus.json", "w"), indent=2)
    print(f"corpus.json: {len(out['tiers']['projects'])} repos written")

if __name__ == "__main__":
    main()
