#!/usr/bin/env python3
"""Issue #48 — ROS 1 -> ROS 2 migration census extraction.

Commands:
  list-pkgs   : enumerate package.xml census units per repo from pinned trees
  fetch       : fetch package.xml files via jsDelivr @ pinned SHA -> snapshots/pkgs/
  classify    : classify each package as ROS1 / ROS2 / dual / none from deps
  signals     : aggregate per-repo + per-tier migration signals

Classification rule (prefix-based, robust to dual-era packages):
  ROS1-only : exact {catkin, xmlrpcpp, actionlib, tf, rosunit, roslib, rospack}
              + prefix {roscpp, rospy, roslaunch, rostest, rosconsole, rosbag,
                        rosgraph, rosmaster, roswtf}
  ROS2-only : exact {builtin_interfaces}
              + prefix {rcl, ament, rosidl, rmw, rcutils, launch}
  dual      : deps from BOTH sets
  none      : neither (message/interface pkgs, pure libs, non-ROS)
  Note: pluginlib / message_filters / nodelet / dynamic_reconfigure / tf2 /
        std_msgs / sensor_msgs / ... exist in BOTH ecosystems -> non-discriminating.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
TREES = SNAP / "trees"
PKGS = SNAP / "pkgs"

ROS1_EXACT = {"catkin", "xmlrpcpp", "actionlib", "tf", "rosunit", "roslib", "rospack",
              "rosbag", "rosbag_storage", "rosbag_migration_rule", "rosgraph", "rosmaster"}
ROS1_PREFIX = ("roscpp", "rospy", "roslaunch", "rostest", "rosconsole",
               "roswtf")
ROS2_EXACT = {"builtin_interfaces"}
ROS2_PREFIX = ("rcl", "ament", "rosidl", "rmw", "rcutils", "launch", "rosbag2")

def load_corpus():
    return json.load(open(ROOT / "corpus.json"))

def all_repos():
    return [p["repo"] for p in load_corpus()["tiers"]["projects"]]

def repo_meta(repo):
    return next(p for p in load_corpus()["tiers"]["projects"] if p["repo"] == repo)

def tree_paths(repo):
    t = json.load(open(TREES / f"{repo.replace('/', '__')}.json"))
    return [e.get("path", "") for e in t["tree"]]

# ---------- list census units ----------
def cmd_list_pkgs():
    rows = []
    for repo in all_repos():
        pkgs = [p for p in tree_paths(repo) if p.endswith("package.xml")]
        rows.append((repo, len(pkgs), pkgs))
    tot = sum(r[1] for r in rows)
    print(f"{'repo':48s} {'pkgs':>5s}")
    for repo, n, _ in sorted(rows, key=lambda x: -x[1]):
        print(f"{repo:48s} {n:5d}")
    print(f"TOTAL package.xml: {tot}")

# ---------- fetch ----------
def cmd_fetch():
    PKGS.mkdir(parents=True, exist_ok=True)
    listf = ROOT / ".fetch_pkgs.txt"
    lines = []
    total = 0
    for repo in all_repos():
        sha = repo_meta(repo)["head_sha"]
        for p in tree_paths(repo):
            if not p.endswith("package.xml"):
                continue
            dest = PKGS / repo.replace("/", "__") / p
            if dest.exists() and dest.stat().st_size > 0:
                continue
            url = f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/{p}"
            lines.append(f"{url}\t{dest}")
            total += 1
    listf.write_text("\n".join(lines) + "\n")
    print(f"fetch: {total} package.xml to fetch", flush=True)
    if total == 0:
        return
    script = f"cat {listf} | xargs -P 16 -n 2 bash {ROOT / 'fetch_one.sh'}"
    r = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=280)
    if r.returncode != 0:
        print(r.stderr[-300:], file=sys.stderr)
    print(f"fetch: done (exit {r.returncode})", flush=True)

# ---------- classify ----------
DEPEND_RE = re.compile(r"<([a-z_]+_depend|depend)>([^<]+)</", re.I)

def classify_package(text):
    deps = {m.group(2).strip() for m in DEPEND_RE.finditer(text)}
    r1 = {d for d in deps if d in ROS1_EXACT or d.startswith(ROS1_PREFIX)}
    r2 = {d for d in deps if d in ROS2_EXACT or d.startswith(ROS2_PREFIX)}
    if r1 and r2:
        return "dual", sorted(r1), sorted(r2)
    if r1:
        return "ROS1", sorted(r1), []
    if r2:
        return "ROS2", [], sorted(r2)
    return "none", [], []

def cmd_classify():
    out = {}
    for repo in all_repos():
        d = PKGS / repo.replace("/", "__")
        recs = []
        if d.exists():
            for f in sorted(d.rglob("package.xml")):
                try:
                    txt = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                cls, r1, r2 = classify_package(txt)
                rel = str(f.relative_to(d))
                recs.append({"path": rel, "class": cls, "ros1_deps": r1, "ros2_deps": r2})
        out[repo] = recs
    json.dump(out, open(SNAP / "package_classes.json", "w"), indent=2)
    # summary
    from collections import Counter
    c = Counter()
    per_repo = {}
    for repo, recs in out.items():
        rc = Counter(r["class"] for r in recs)
        c.update(rc)
        per_repo[repo] = dict(rc)
    print(f"{'class':8s} {'count':>6s} {'pct':>7s}")
    tot = sum(c.values())
    for k in ("ROS1", "ROS2", "dual", "none"):
        print(f"{k:8s} {c[k]:6d} {c[k]/tot*100:6.1f}%")
    print(f"{'TOTAL':8s} {tot:6d}")
    print()
    print(f"{'repo':48s} {'ROS1':>4s} {'ROS2':>4s} {'dual':>4s} {'none':>4s} {'mig%':>6s}")
    for repo in all_repos():
        rc = per_repo.get(repo, {})
        n = sum(rc.values())
        mig = rc.get("ROS2", 0) / n * 100 if n else 0
        print(f"{repo:48s} {rc.get('ROS1',0):4d} {rc.get('ROS2',0):4d} {rc.get('dual',0):4d} {rc.get('none',0):4d} {mig:5.1f}%")

def cmd_signals():
    # aggregate per-tier migration summary from package_classes.json
    cls = json.load(open(SNAP / "package_classes.json"))
    corpus = load_corpus()
    from collections import Counter
    tier_c = Counter()
    for p in corpus["tiers"]["projects"]:
        repo = p["repo"]
        tier = p["tier"]
        rc = Counter(r["class"] for r in cls.get(repo, []))
        for k, v in rc.items():
            tier_c[(tier, k)] += v
    print("tier-level package classification:")
    for tier in ("Tier A core", "Tier B stacks", "Tier C platforms", "Tier D apps"):
        row = {k: v for (t, k), v in tier_c.items() if t == tier}
        n = sum(row.values())
        mig = row.get("ROS2", 0) / n * 100 if n else 0
        print(f"  {tier:18s} ROS1={row.get('ROS1',0):4d} ROS2={row.get('ROS2',0):4d} "
              f"dual={row.get('dual',0):4d} none={row.get('none',0):4d} mig%={mig:5.1f}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list-pkgs"
    if cmd == "list-pkgs":
        cmd_list_pkgs()
    elif cmd == "fetch":
        cmd_fetch()
    elif cmd == "classify":
        cmd_classify()
    elif cmd == "signals":
        cmd_signals()
    else:
        print(__doc__)
