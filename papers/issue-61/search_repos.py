#!/usr/bin/env python3
"""Issue #61 — retrieve candidate corpus for the PQC migration census.

Population design (notes_r111.md):
  Tier A: crypto/TLS/network migration-frontier anchors (exact repo lookup) —
          used for H3 ecosystem-stratified analysis + classifier calibration.
  Tier B: top-starred repos per ecosystem (Python/Go/Rust/Java/C-C++/JS-TS),
          >=1k stars — the honest general population (NOT self-description-filtered).
  Tier C: dependency reverse-detection (GitHub code search for PQC manifest signals)
          — later round (R113), not here.

Outputs (research/snapshots/):
  search_results.json   — raw per-query search API responses
  inventory.json        — deduped candidate inventory across queries + Tier A seeds
  inventory_stats.txt   — human-readable stats

Rate limits: search API = 30 req/min authenticated; sleep between queries.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(ROOT, "snapshots")
os.makedirs(SNAP, exist_ok=True)

# Tier A: crypto/TLS/network migration-frontier anchors (ecosystem spread).
TIER_A_SEEDS = [
    "openssl/openssl",                  # C      — OpenSSL 3.5 ML-KEM TLS groups
    "google/boringssl",                 # C/C++  — ML-KEM
    "aws/aws-lc",                       # C      — ML-KEM hybrid
    "wolfSSL/wolfssl",                  # C      — ML-KEM/ML-DSA
    "open-quantum-safe/liboqs",         # C      — all NIST schemes
    "open-quantum-safe/oqs-provider",   # C      — OpenSSL 3 provider
    "Mbed-TLS/mbedtls",                 # C      — ML-KEM
    "gnutls/gnutls",                    # C      — PQC groups
    "randombit/botan",                  # C++    — ML-KEM/Kyber
    "curl/curl",                        # C      — PQC via OpenSSL 3.5
    "openssh/openssh-portable",         # C      — PQC KEX (hybrid)
    "aws/s2n-tls",                      # C      — ML-KEM hybrid
    "golang/go",                        # Go     — crypto stdlib
    "cloudflare/circl",                 # Go     — mlkem/dilithium/sphincs
    "rustls/rustls",                    # Rust   — PQC provider support
    "bcgit/bc-java",                    # Java   — BouncyCastle ML-KEM/ML-DSA/SLH-DSA
    "pyca/cryptography",                # Python — X25519MLKEM768 hybrid TLS
    "open-quantum-safe/liboqs-python",  # Python — liboqs binding
    "google/tink",                      # mixed  — hybrid encryption (PQC candidate)
    "signalapp/libsignal",              # Rust   — PQXDH hybrid
]

# Tier B: top-starred per ecosystem (>=1k stars implicit in top-100 of stars sort).
TIER_B_LANGUAGES = {
    "Python": 40,
    "Go": 35,
    "Rust": 30,
    "Java": 30,
    "C": 20,     # C and C++ merged after retrieval
    "C++": 20,
    "JavaScript": 15,
    "TypeScript": 20,
}


def gh_api(path: str) -> dict:
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def search_repos(query: str, max_pages: int = 3) -> list:
    """GitHub search API, manual pagination, stars desc."""
    import urllib.parse
    q = urllib.parse.quote(query)
    items_all = []
    for page in range(1, max_pages + 1):
        path = f"search/repositories?q={q}&sort=stars&order=desc&per_page=100&page={page}"
        try:
            resp = gh_api(path)
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e)
            print(f"  [warn] search page {page} failed: {err[:200]}", file=sys.stderr)
            break
        page_items = resp.get("items", [])
        items_all.extend(page_items)
        if len(page_items) < 100:
            break
        time.sleep(2)
    return items_all


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] retrieving candidates...")
    all_results = {}
    seen = {}

    # --- Tier B: per-ecosystem top-starred searches ---
    for i, (lang, quota) in enumerate(TIER_B_LANGUAGES.items()):
        q = f"language:{lang} stars:>=1000"
        print(f"  [{i + 1}/{len(TIER_B_LANGUAGES)}] {lang} (quota {quota}): {q}")
        items = search_repos(q)
        all_results[q] = items
        print(f"    got {len(items)}")
        for it in items:
            full = it.get("full_name")
            if full and full not in seen:
                seen[full] = {
                    "full_name": full,
                    "stars": it.get("stargazers_count", 0),
                    "language": it.get("language"),
                    "description": (it.get("description") or "")[:300],
                    "html_url": it.get("html_url"),
                    "archived": it.get("archived", False),
                    "source": "tierb_search",
                    "query_hits": [q],
                }
            elif full in seen and q not in seen[full]["query_hits"]:
                seen[full]["query_hits"].append(q)
        time.sleep(3)  # stay under 30 req/min

    # --- Tier A: exact seed lookup ---
    for s in TIER_A_SEEDS:
        if s in seen:
            continue
        try:
            it = gh_api(f"repos/{s}")
            seen[s] = {
                "full_name": s,
                "stars": it.get("stargazers_count", 0),
                "language": it.get("language"),
                "description": (it.get("description") or "")[:300],
                "html_url": it.get("html_url"),
                "archived": it.get("archived", False),
                "source": "tier_a_seed",
                "query_hits": [],
            }
            print(f"  seed: {s} ({it.get('stargazers_count', 0)} stars)")
        except subprocess.CalledProcessError as e:
            print(f"  [warn] seed lookup failed: {s}: {str(e.stderr)[:120]}", file=sys.stderr)
        time.sleep(1)

    with open(os.path.join(SNAP, "search_results.json"), "w") as f:
        json.dump(all_results, f, indent=1)

    inventory = sorted(seen.values(), key=lambda r: -r["stars"])
    with open(os.path.join(SNAP, "inventory.json"), "w") as f:
        json.dump(inventory, f, indent=1)

    # --- Stats ---
    n = len(inventory)
    active = [r for r in inventory if not r["archived"]]
    by_lang = {}
    for r in active:
        lang = r["language"] or "unknown"
        by_lang[lang] = by_lang.get(lang, 0) + 1
    top = sorted(by_lang.items(), key=lambda kv: -kv[1])[:12]
    star_bins = {"0": 0, "1-99": 0, "100-999": 0, "1k-9.9k": 0, "10k+": 0}
    for r in active:
        s = r["stars"]
        if s == 0: star_bins["0"] += 1
        elif s < 100: star_bins["1-99"] += 1
        elif s < 1000: star_bins["100-999"] += 1
        elif s < 10000: star_bins["1k-9.9k"] += 1
        else: star_bins["10k+"] += 1

    lines = [
        f"inventory: {n} unique repos (Tier A seeds + Tier B per-ecosystem top-stars, deduped)",
        f"active (non-archived): {len(active)}",
        f"archived: {n - len(active)}",
        "language histogram: " + ", ".join(f"{k}={v}" for k, v in top),
        "star bins: " + ", ".join(f"{k}={v}" for k, v in star_bins.items()),
        "",
        "top 40 by stars:",
    ]
    for r in active[:40]:
        lines.append(f"  {r['stars']:>8}  {(r['language'] or '?'):<12} {r['full_name']}  {r['source']}")
    with open(os.path.join(SNAP, "inventory_stats.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
