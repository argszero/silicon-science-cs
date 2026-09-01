#!/usr/bin/env python3
"""Issue #63 — monorepo-aware manifest extraction + consensus dependency detection (Channel 1).

From the R121 recursive trees (snapshots/trees/), enumerate ALL manifest paths
(root + nested, covering monorepos), fetch a bounded subset (raw.githubusercontent,
parallel), and detect consensus-library dependencies (dictionary Channel 1) in
each manifest.

Outputs:
  snapshots/manifest_tree_paths.json — per repo: all manifest paths found in tree
  snapshots/consensus_dep_evidence.json — per repo: {path -> [consensus dep hits]}
  snapshots/consensus_dep_evidence_stats.txt
"""
import json
import os
import re
import subprocess
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / "snapshots"
TREES = SNAP / "trees"
MANIFEST_NAMES = {
    "pyproject.toml", "requirements.txt", "package.json", "Cargo.toml",
    "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "uv.lock", "pixi.toml",
    "go.mod", "go.sum", "pom.xml", "build.gradle", "build.gradle.kts",
    "gradle/libs.versions.toml", "CMakeLists.txt", "vcpkg.json", "conanfile.txt",
    "conanfile.py", ".gitmodules", "Cargo.lock", "Package.swift", "flake.nix",
    "packages.lock.json", "pnpm-lock.yaml", "yarn.lock", "Gemfile", "Gemfile.lock",
    "WORKSPACE", "BUILD", "BUILD.bazel", "MODULE.bazel", "bazel/BUILD",
}
MAX_MANIFESTS_PER_REPO = 12  # bound network fetches for huge monorepos (root-first)

# Root-level manifest names — prioritized (a repo's consensus deps are declared
# at or near the root; nested manifests only matter for monorepos).
ROOT_PRIORITY = [
    "go.mod", "Cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "gradle/libs.versions.toml", "CMakeLists.txt", "vcpkg.json", "conanfile.txt",
    "package.json", "pyproject.toml", "requirements.txt", "WORKSPACE",
    "MODULE.bazel", "Cargo.lock", "go.sum", ".gitmodules",
]

# Consensus dependency signals (dictionary Channel 1) — name-level regexes.
# Grouped by protocol family; coordination-clients are flagged separately.
CONSENSUS_DEP_PATTERNS = [
    # --- Raft family ---
    ("etcd-raft",       r"go\.etcd\.io/etcd/raft/v\d|github\.com/etcd-io/raft|github\.com/coreos/etcd/raft"),
    ("hashicorp/raft",  r"github\.com/hashicorp/raft"),
    ("raft-rs crate",   r"^\s*raft\s*=|raft-persist|raft-proto"),           # Cargo.toml `raft = ...`
    ("openraft",        r"^\s*openraft\s*="),
    ("dragonboat",      r"github\.com/lni/dragonboat"),
    ("braft",           r"\bbraft\b|baidu/braft|github\.com/brpc/braft"),
    ("nuraft",          r"\bnuraft\b|eBay/NuRaft"),
    ("sofa-jraft",      r"com\.alipay\.sofa:jraft|sofa-jraft|io\.sofastack\.stack:jraft"),
    ("ratis",           r"org\.apache\.ratis"),
    ("atomix",          r"io\.atomix:atomix"),
    ("logcabin",        r"logcabin"),
    # --- Paxos family ---
    ("phxpaxos",        r"phxpaxos|Tencent/phxpaxos"),
    ("libpaxos",        r"libpaxos"),
    ("zookeeper(ZAB)",  r"org\.apache\.zookeeper:zookeeper"),               # server impl (ZAB)
    # --- BFT family ---
    ("cometbft",        r"github\.com/cometbft/cometbft"),
    ("tendermint",      r"github\.com/tendermint/tendermint"),
    ("tendermint-rs",   r"tendermint(?:-rs)?\s*="),
    ("libhotstuff",     r"libhotstuff|hotstuff"),
    ("narwhal",         r"narwhal"),
    ("bullshark",       r"bullshark"),
    # --- coordination clients (NOT consensus embedders — rule 5) ---
    ("zookeeper-client", r"org\.apache\.zookeeper:zookeeper|curator|zkclient"),
    ("etcd-client",     r"go\.etcd\.io/etcd/client/v\d|clientv3|etcd/client"),
]


def enumerate_manifest_paths(repo):
    fname = repo.replace("/", "__") + ".json"
    fpath = TREES / fname
    if not fpath.exists():
        return []
    data = json.load(open(fpath))
    paths = []
    for entry in data.get("tree", []):
        p = entry.get("path", "")
        if not p:
            continue
        base = os.path.basename(p)
        if base in MANIFEST_NAMES:
            paths.append(p)
    return paths


def raw_fetch(repo, branch, path):
    """Fetch raw file content via gh api (raw.githubusercontent is flaky)."""
    try:
        r = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={branch}",
             "-H", "Accept: application/vnd.github.raw"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return None
        return r.stdout
    except Exception:
        return None


def detect_deps(content):
    if not content:
        return []
    hits = []
    for name, pat in CONSENSUS_DEP_PATTERNS:
        if re.search(pat, content, re.MULTILINE):
            # capture the matching line(s) as evidence
            lines = [ln.strip()[:120] for ln in content.splitlines()
                     if re.search(pat, ln, re.MULTILINE)][:3]
            hits.append({"signal": name, "pattern": pat, "lines": lines})
    return hits


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    print(f"corpus: {len(corpus)} repos", flush=True)

    manifest_paths = {}
    for repo in corpus:
        paths = enumerate_manifest_paths(repo)
        if paths:
            manifest_paths[repo] = paths
    json.dump(manifest_paths, open(SNAP / "manifest_tree_paths.json", "w"), indent=1)
    print(f"manifest paths: {len(manifest_paths)} repos have manifests", flush=True)

    # bounded fetch + detect (parallel, resume-safe)
    evidence_path = SNAP / "consensus_dep_evidence.json"
    evidence = {}
    if evidence_path.exists():
        evidence = json.load(open(evidence_path))
        print(f"resuming: {len(evidence)} repos already scanned", flush=True)

    def work(repo):
        paths = manifest_paths.get(repo, [])
        # root-first priority sort
        paths.sort(key=lambda p: (0 if os.path.basename(p) in ROOT_PRIORITY else 1,
                                  p.count("/")))
        paths = paths[:MAX_MANIFESTS_PER_REPO]
        branch = corpus[repo].get("default_branch", "main")
        repo_hits = {}
        for p in paths:
            content = raw_fetch(repo, branch, p)
            if content is None:
                continue
            hits = detect_deps(content)
            if hits:
                repo_hits[p] = hits
        return repo, repo_hits

    todo = [r for r in manifest_paths if r not in evidence]
    print(f"fetching {len(todo)} repos (parallel 12, root-first, resume-safe)...", flush=True)
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(work, r): r for r in todo}
        done = 0
        for fut in futs:
            repo, repo_hits = fut.result()
            if repo_hits:
                evidence[repo] = repo_hits
            done += 1
            if done % 30 == 0:
                json.dump(evidence, open(evidence_path, "w"), indent=1)
                print(f"  ... {done}/{len(futs)}", flush=True)

    json.dump(evidence, open(evidence_path, "w"), indent=1)

    # --- stats ---
    by_signal = defaultdict(list)
    for repo, paths in evidence.items():
        sigs = set()
        for p, hits in paths.items():
            for h in hits:
                sigs.add(h["signal"])
        for s in sigs:
            by_signal[s].append(repo)
    lines = [
        f"repos with consensus-dep evidence: {len(evidence)} / {len(corpus)}",
        "",
        "signal -> repos:",
    ]
    for sig in sorted(by_signal, key=lambda s: -len(by_signal[s])):
        lines.append(f"  {sig}: {len(by_signal[s])} — {sorted(by_signal[s])[:20]}")
    with open(SNAP / "consensus_dep_evidence_stats.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:40]))


if __name__ == "__main__":
    main()
