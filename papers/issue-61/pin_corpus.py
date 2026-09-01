#!/usr/bin/env python3
"""Issue #61 — pin corpus: build tier_ab_corpus.json with head_sha per repo.

Snapshot semantics (mirrors #57): every repo pinned by the default-branch HEAD
commit at snapshot time -> reproducible census. Resume-safe (cached entries kept).

Output: snapshots/tier_ab_corpus.json
  {full_name: {stars, language, bucket|tier, head_sha, default_branch, pinned_at}}
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(ROOT, "snapshots")
CORPUS = os.path.join(SNAP, "tier_ab_corpus.json")

TIER_A = [
    "openssl/openssl", "google/boringssl", "aws/aws-lc", "wolfSSL/wolfssl",
    "open-quantum-safe/liboqs", "open-quantum-safe/oqs-provider", "Mbed-TLS/mbedtls",
    "gnutls/gnutls", "randombit/botan", "curl/curl", "openssh/openssh-portable",
    "aws/s2n-tls", "golang/go", "cloudflare/circl", "rustls/rustls", "bcgit/bc-java",
    "pyca/cryptography", "open-quantum-safe/liboqs-python", "google/tink", "signalapp/libsignal",
]


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
    corpus = {}
    if os.path.exists(CORPUS):
        corpus = json.load(open(CORPUS))
        print(f"resuming: {len(corpus)} already pinned", flush=True)

    # Tier B entries from tierb_candidates.json
    tb = json.load(open(os.path.join(SNAP, "tierb_candidates.json")))
    for repo, meta in tb.items():
        if repo in corpus and corpus[repo].get("head_sha"):
            continue
        entry = {"stars": meta["stars"], "language": meta["language"],
                 "bucket": meta["bucket"], "tier": "B",
                 "description": meta["description"]}
        status = pin(repo, entry)
        corpus[repo] = entry
        print(f"  [B] {repo}: {status}", flush=True)
        time.sleep(0.4)

    for repo in TIER_A:
        if repo in corpus and corpus[repo].get("head_sha"):
            continue
        entry = {"tier": "A", "stars": 0, "language": None, "bucket": "anchor",
                 "description": ""}
        status = pin(repo, entry)
        corpus[repo] = entry
        print(f"  [A] {repo}: {status}", flush=True)
        time.sleep(0.4)

    json.dump(corpus, open(CORPUS, "w"), indent=1, sort_keys=True)
    n_a = sum(1 for v in corpus.values() if v["tier"] == "A")
    n_b = sum(1 for v in corpus.values() if v["tier"] == "B")
    pinned = sum(1 for v in corpus.values() if v.get("head_sha"))
    print(f"corpus: {len(corpus)} repos (A={n_a}, B={n_b}), pinned={pinned}")


if __name__ == "__main__":
    main()
