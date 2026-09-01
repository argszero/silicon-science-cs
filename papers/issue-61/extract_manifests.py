#!/usr/bin/env python3
"""Issue #61 — monorepo-aware manifest extraction + PQC dependency detection (Channel 1).

From the R112 recursive trees (snapshots/trees/), enumerate ALL manifest paths
(root + nested, covering monorepos), fetch a bounded subset (raw.githubusercontent,
parallel), and detect PQC-capable dependencies (dictionary Channel 1) in each manifest.

Outputs:
  snapshots/manifest_tree_paths.json — per repo: all manifest paths found in tree
  snapshots/pqc_dep_evidence.json    — per repo: {path -> [PQC dep hits]}
  snapshots/pqc_dep_evidence_stats.txt
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
}
MAX_MANIFESTS_PER_REPO = 40  # bound network fetches for huge monorepos

# PQC-capable dependency signals (dictionary Channel 1) — name-level regexes.
PQC_DEP_PATTERNS = [
    ("liboqs",              r"liboqs(?:-python|-go|-java|-dotnet|-crypto)?\b"),
    ("oqs-provider",        r"oqs-provider\b|oqsprovider"),
    ("pqcrypto-*",          r"pqcrypto(?:-kyber|-dilithium|-sphincsplus|-falcon|-ml-kem|-ml-dsa)?\b"),
    ("ml-kem crate",        r"\bml-kem(?:-crypto)?\b|\bmlkem(?:-crypto)?\b"),
    ("cloudflare/circl",    r"github\.com/cloudflare/circl"),
    ("refraction-networking/quantum", r"refraction-networking/quantum"),
    ("BouncyCastle",        r"org\.bouncycastle\b|bcprov|bcpkix"),
    ("liboqs-java",         r"org\.openquantumsafe"),
    ("@noble/post-quantum", r"@noble/post-quantum"),
    ("pqcrypto npm",        r"\"pqcrypto\"|'pqcrypto'|liboqs-js"),
    ("aws-lc-rs",           r"aws-lc-rs\b|aws-lc-sys\b"),
    ("aws-lc",              r"\baws-lc\b|aws-lc-fips-sys"),
    ("boringssl",           r"boringssl\b"),
    ("wolfssl",             r"wolfssl\b|wolfcrypt"),
    ("botan",               r"\bbotan\b"),
    ("mbedtls",             r"mbedtls\b|mbed-crypto"),
    ("gnutls",              r"gnutls\b|libgnutls"),
    ("openssl>=3.5",        r"openssl[\s~=><]*\d+(?:\.\d+)*"),
    ("open-quantum-safe",   r"open-quantum-safe\b|openquantumsafe"),
    ("PQClean",             r"pqclean\b"),
    ("rustls-post-quantum", r"rustls-post-quantum\b"),
    ("s2n-tls",             r"s2n-tls\b|s2n-tls-sys"),
    ("tink-pqc",            r"tink\b|com\.google\.crypto\.tink"),
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
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "12", "-o", "-", "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=18,
        )
        code = out.stdout.strip()[-3:] if out.stdout else "000"
        body = out.stdout[:-3] if len(out.stdout) > 3 else ""
        if code == "200":
            return True, body
    except subprocess.TimeoutExpired:
        pass
    return False, ""


def detect(content):
    hits = []
    for name, pat in PQC_DEP_PATTERNS:
        if re.search(pat, content, re.I):
            hits.append(name)
    return sorted(set(hits))


def main():
    corpus = json.load(open(SNAP / "tier_ab_corpus.json"))
    repos = sorted(corpus.keys())

    # 1) enumerate manifest paths from trees
    paths_map = {}
    for repo in repos:
        paths = enumerate_manifest_paths(repo)
        paths_map[repo] = paths
    json.dump(paths_map, open(SNAP / "manifest_tree_paths.json", "w"), indent=1)

    n_with = sum(1 for v in paths_map.values() if v)
    total_paths = sum(len(v) for v in paths_map.values())
    print(f"repos: {len(repos)} | with ≥1 manifest path in tree: {n_with} | total manifest paths: {total_paths}")

    # 2) fetch bounded subset per repo + detect PQC deps
    evidence = {}
    tasks = []
    for repo in repos:
        paths = paths_map[repo]
        if not paths:
            evidence[repo] = []
            continue
        paths = sorted(paths, key=lambda p: (p.count("/"), len(p)))
        chosen = paths[:MAX_MANIFESTS_PER_REPO]
        branch = corpus[repo].get("default_branch", "main")
        for p in chosen:
            tasks.append((repo, branch, p))
    print(f"fetching {len(tasks)} manifests (parallel 12)...", flush=True)

    def work(t):
        repo, branch, p = t
        ok, body = raw_fetch(repo, branch, p)
        if not ok or not body:
            return repo, p, [], "fetch-fail"
        return repo, p, detect(body), "ok"

    fetched_map = defaultdict(list)
    fetches = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        for i, (repo, p, hits, status) in enumerate(pool.map(work, tasks)):
            fetched_map[repo].append({"path": p, "pqc_deps": hits, "status": status})
            fetches += 1
            if (i + 1) % 150 == 0 or i == len(tasks) - 1:
                print(f"  [{i+1}/{len(tasks)}]", flush=True)

    # 3) aggregate per repo
    repo_deps = {}
    for repo in repos:
        hits = set()
        per_path = []
        for e in fetched_map.get(repo, []):
            per_path.append(e)
            hits.update(e["pqc_deps"])
        repo_deps[repo] = {
            "pqc_deps": sorted(hits),
            "n_manifest_fetched": len(per_path),
            "n_manifest_paths": len(paths_map.get(repo, [])),
            "per_path": per_path,
        }

    json.dump(repo_deps, open(SNAP / "pqc_dep_evidence.json", "w"), indent=1)

    # stats
    with_dep = {r: v["pqc_deps"] for r, v in repo_deps.items() if v["pqc_deps"]}
    by_dep = defaultdict(int)
    for v in with_dep.values():
        for d in v:
            by_dep[d] += 1
    lines = [
        f"repos with ≥1 PQC-capable dep (monorepo-aware): {len(with_dep)} / {len(repos)}",
        f"fetches: {fetches}",
        "per-dep repo counts: " + ", ".join(f"{k}={v}" for k, v in sorted(by_dep.items(), key=lambda kv: -kv[1])),
        "",
        "repos with PQC dep, star-sorted:",
    ]
    for repo, deps in sorted(with_dep.items(), key=lambda kv: -corpus[kv[0]].get("stars", 0)):
        lines.append(f"  {corpus[repo]['stars']:>8}  {repo:<45} {deps}")
    with open(SNAP / "pqc_dep_evidence_stats.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
