#!/usr/bin/env python3
"""Issue #63 — pin corpus: build tier_ab_corpus.json (dict) with head_sha per repo.

Snapshot semantics (mirrors #57/#61): every repo pinned by the default-branch HEAD
commit at snapshot time -> reproducible census. Resume-safe (cached entries kept).

Input : snapshots/tier_ab_corpus.json (list from tierb_filter.py)
Output: snapshots/tier_ab_corpus.json (dict full_name -> meta incl. head_sha)
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(ROOT, "snapshots")
CORPUS_PATH = os.path.join(SNAP, "tier_ab_corpus.json")


def gh_api(path: str) -> dict:
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def pin(repo: str, meta: dict):
    """Fetch default branch + HEAD sha for a repo. Returns status str."""
    try:
        r = gh_api(f"repos/{repo}")
    except subprocess.CalledProcessError as e:
        return f"FAILED: {str(e.stderr)[:100]}"
    default = r.get("default_branch", "main")
    try:
        c = gh_api(f"repos/{repo}/commits/{default}?per_page=1")
        sha = c.get("sha", "")
    except subprocess.CalledProcessError as e:
        return f"FAILED: commit {str(e.stderr)[:100]}"
    meta["default_branch"] = default
    meta["head_sha"] = sha
    meta["pinned_at"] = datetime.now(timezone.utc).isoformat()
    return f"ok {sha[:10]}"


def main():
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if os.path.exists(CORPUS_PATH):
        existing = json.load(open(CORPUS_PATH))
        corpus = existing if isinstance(existing, dict) else {}
    else:
        corpus = {}

    raw = json.load(open(CORPUS_PATH))
    if isinstance(raw, list):
        for r in raw:
            full = r["full_name"]
            if full in corpus:
                continue
            corpus[full] = {k: r[k] for k in ("stars", "language", "membership", "stratum", "description") if k in r}
    else:
        # dict form: keep existing meta
        raw = []

    todo = [(full, v) for full, v in corpus.items() if not v.get("head_sha")]
    print(f"corpus {len(corpus)} repos, {len(todo)} to pin (parallel 8, incremental save)...", flush=True)

    def work(item):
        full, meta = item
        return full, pin(full, meta)

    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(work, it) for it in todo]
        for fut in as_completed(futs):
            full, status = fut.result()
            done += 1
            if done % 20 == 0:
                with open(CORPUS_PATH, "w") as f:
                    json.dump(corpus, f, indent=1)
                print(f"  ... {done}/{len(todo)}", flush=True)
            if not status.startswith("ok"):
                print(f"  WARN {full}: {status}", flush=True)

    with open(CORPUS_PATH, "w") as f:
        json.dump(corpus, f, indent=1)

    n = len(corpus)
    by_m = {}
    for v in corpus.values():
        by_m[v.get("membership", "?")] = by_m.get(v.get("membership", "?"), 0) + 1
    n_pinned = sum(1 for v in corpus.values() if v.get("head_sha"))
    print(f"\ncorpus: {n} repos, pinned {n_pinned}")
    print("membership: " + ", ".join(f"{k}={v}" for k, v in sorted(by_m.items())))


if __name__ == "__main__":
    main()
