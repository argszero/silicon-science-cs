#!/usr/bin/env python3
"""Issue #63 — fetch recursive git trees for all corpus repos (resume-safe, parallel).

Uses head_sha from snapshots/tier_ab_corpus.json (pinned at R112 snapshot).
Saves snapshots/trees/<repo>.json (raw API JSON). Handles truncation flag.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORPUS = json.load(open(ROOT / "snapshots" / "tier_ab_corpus.json"))
OUT = ROOT / "snapshots" / "trees"
OUT.mkdir(parents=True, exist_ok=True)

repos = [(repo, v["head_sha"]) for repo, v in CORPUS.items()]


def fetch(repo, sha):
    fname = repo.replace("/", "__") + ".json"
    fpath = OUT / fname
    if fpath.exists():
        return repo, "cached", 0
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/git/trees/{sha}?recursive=1"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return repo, f"FAILED: {r.stderr[:80]}", 0
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return repo, "FAILED: bad json", 0
    if "tree" not in data:
        return repo, f"FAILED: no tree ({str(data)[:80]})", 0
    json.dump(data, open(fpath, "w"))
    return repo, f"ok ({len(data['tree'])} entries, truncated={data.get('truncated')})", len(data["tree"])


def main():
    print(f"fetching {len(repos)} trees (parallel 8)...", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(fetch, repo, sha) for repo, sha in repos]
        for i, f in enumerate(futs):
            repo, status, n = f.result()
            results.append((repo, status))
            if (i + 1) % 30 == 0 or i == len(futs) - 1:
                print(f"  [{i+1}/{len(futs)}]", flush=True)
    ok = sum(1 for _, s in results if s.startswith("ok") or s == "cached")
    trunc = sum(1 for _, s in results if "truncated=True" in s)
    failed = [(r, s) for r, s in results if s.startswith("FAILED")]
    print(f"done: {ok}/{len(repos)} ok (cached incl.), truncated={trunc}, failed={len(failed)}")
    for r, s in failed:
        print(f"  FAILED {r}: {s}", file=sys.stderr)
    json.dump(dict(results), open(ROOT / "snapshots" / "tree_status.json", "w"), indent=1)


if __name__ == "__main__":
    main()
