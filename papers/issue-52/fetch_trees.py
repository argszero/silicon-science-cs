#!/usr/bin/env python3
"""Issue #52 — fetch recursive git trees for all 32 pinned repos (resume-safe).

Saves research/snapshots/trees/<repo>.json (raw API JSON per repo).
"""
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORPUS = json.load(open(ROOT / "corpus.json"))
OUT = ROOT / "snapshots" / "trees"
OUT.mkdir(parents=True, exist_ok=True)

repos = []
for p in CORPUS["tiers"]["pairs"]:
    for side in ("c_side", "rust_side"):
        repos.append((p[side]["repo"], p[side]["head_sha"]))

def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)

ok = 0
for i, (repo, sha) in enumerate(repos):
    fname = repo.replace("/", "__") + ".json"
    if (OUT / fname).exists():
        print(f"[{i+1}/32] {repo:44s} cached", flush=True)
        ok += 1
        continue
    data = gh(f"repos/{repo}/git/trees/{sha}?recursive=1")
    if data is None or "tree" not in data:
        print(f"[{i+1}/32] {repo:44s} FAILED (truncated={data and data.get('truncated')})", file=sys.stderr)
        continue
    json.dump(data, open(OUT / fname, "w"))
    print(f"[{i+1}/32] {repo:44s} {len(data['tree'])} entries (truncated={data.get('truncated')})", flush=True)
    ok += 1
    time.sleep(0.4)

print(f"done: {ok}/32 trees saved")
