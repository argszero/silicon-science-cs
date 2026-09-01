#!/usr/bin/env python3
"""Issue #63 — retrieve candidate corpus for the consensus-protocol adoption census.

Population design (notes_r120.md):
  Tier A: consensus library/keeper anchors (exact repo lookup) —
          used for H3 ecosystem-stratified analysis + classifier calibration.
  Tier B: stratified distributed-systems corpus via topic searches
          S1 databases / S2 storage / S3 coordination / S4 MQ-streaming /
          S5 blockchain-DLT / S6 kv-cache-search (>=1000 stars each stratum).
  Negative control: bitcoin/ethereum (PoW/PoS, non-classic consensus family).

Outputs (research/snapshots/):
  search_results.json   — raw per-query search API responses
  inventory.json        — deduped candidate inventory (stratum-tagged)
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

# Tier A: consensus-producing anchors (ecosystem spread).
TIER_A_SEEDS = [
    "etcd-io/etcd",                   # Go    — Raft embedded (etcd-raft module)
    "hashicorp/consul",               # Go    — Raft (hashicorp/raft)
    "apache/zookeeper",               # Java  — ZAB (paxos-family)
    "apache/kafka",                   # Java  — KRaft (raft-like, self-impl)
    "tikv/tikv",                      # Rust  — Raft (tikv/raft-rs)
    "redpanda-data/redpanda",         # C++   — Raft (self-impl)
    "scylladb/scylladb",              # C++   — Raft (self-impl)
    "apple/foundationdb",             # C++   — Paxos (self-impl)
    "lni/dragonboat",                 # Go    — Raft library
    "tikv/raft-rs",                   # Rust  — Raft library
    "hashicorp/raft",                 # Go    — Raft library
    "baidu/braft",                    # C++   — Raft library
    "cometbft/cometbft",              # Go    — BFT (tendermint successor)
    "hyperledger/fabric",             # Go    — BFT ordering service
    "MystenLabs/sui",                 # Rust  — Narwhal/Bullshark BFT
    "aptos-labs/aptos-core",          # Rust  — Jolteon BFT
]
# Negative control stratum (non-classic consensus family: PoW/PoS).
NEG_CONTROL_SEEDS = [
    "bitcoin/bitcoin",                # PoW — no Raft/Paxos/BFT-family
    "ethereum/go-ethereum",           # PoW/PoS — no Raft/Paxos/BFT-family
]

# Tier B: per-stratum topic searches (>=1000 stars implicit in top-stars sort).
TIER_B_STRATA = {
    "S1_database": {
        "queries": ["topic:database stars:>=1000",
                    "topic:distributed-database stars:>=1000",
                    "topic:sql stars:>=1000"],
        "target": 50,
    },
    "S2_storage": {
        "queries": ["topic:storage stars:>=1000",
                    "topic:object-storage stars:>=1000",
                    "topic:distributed-storage stars:>=1000"],
        "target": 25,
    },
    "S3_coordination": {
        "queries": ["topic:coordination stars:>=1000",
                    "topic:service-discovery stars:>=1000",
                    "topic:distributed-lock stars:>=1000"],
        "target": 20,
    },
    "S4_mq_streaming": {
        "queries": ["topic:message-queue stars:>=1000",
                    "topic:streaming stars:>=1000",
                    "topic:pubsub stars:>=1000"],
        "target": 30,
    },
    "S5_blockchain": {
        "queries": ["topic:blockchain stars:>=1000",
                    "topic:consensus-algorithm stars:>=1000",
                    "topic:distributed-ledger stars:>=1000"],
        "target": 40,
    },
    "S6_kv_cache_search": {
        "queries": ["topic:key-value stars:>=1000",
                    "topic:cache stars:>=1000",
                    "topic:search stars:>=1000"],
        "target": 15,
    },
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

    # --- Tier B: per-stratum topic searches ---
    for sname, spec in TIER_B_STRATA.items():
        for qi, q in enumerate(spec["queries"]):
            print(f"  {sname} [{qi + 1}/{len(spec['queries'])}] (target {spec['target']}): {q}")
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
                        "stratum": sname,
                        "source": "tierb_search",
                        "query_hits": [q],
                    }
                elif full in seen and q not in seen[full]["query_hits"]:
                    seen[full]["query_hits"].append(q)
            time.sleep(3)  # stay under 30 req/min

    # --- Tier A: exact seed lookup (anchors + negative controls) ---
    for s in TIER_A_SEEDS + NEG_CONTROL_SEEDS:
        if s in seen:
            continue
        try:
            it = gh_api(f"repos/{s}")
            stratum = "S5_blockchain" if s in TIER_A_SEEDS and s in (
                "cometbft/cometbft", "hyperledger/fabric", "MystenLabs/sui",
                "aptos-labs/aptos-core") else "TierA_anchor"
            if s in NEG_CONTROL_SEEDS:
                stratum = "NEG_control"
            seen[s] = {
                "full_name": s,
                "stars": it.get("stargazers_count", 0),
                "language": it.get("language"),
                "description": (it.get("description") or "")[:300],
                "html_url": it.get("html_url"),
                "archived": it.get("archived", False),
                "stratum": stratum,
                "source": "tier_a_seed",
                "query_hits": [],
            }
            print(f"  seed: {s} ({it.get('stargazers_count', 0)} stars, {stratum})")
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
    by_stratum = {}
    for r in active:
        st = r["stratum"]
        by_stratum[st] = by_stratum.get(st, 0) + 1
    by_lang = {}
    for r in active:
        lang = r["language"] or "unknown"
        by_lang[lang] = by_lang.get(lang, 0) + 1
    star_bins = {"0": 0, "1-99": 0, "100-999": 0, "1k-9.9k": 0, "10k+": 0}
    for r in active:
        s = r["stars"]
        if s == 0: star_bins["0"] += 1
        elif s < 100: star_bins["1-99"] += 1
        elif s < 1000: star_bins["100-999"] += 1
        elif s < 10000: star_bins["1k-9.9k"] += 1
        else: star_bins["10k+"] += 1

    top_strata = sorted(by_stratum.items(), key=lambda kv: -kv[1])
    top_langs = sorted(by_lang.items(), key=lambda kv: -kv[1])[:14]
    lines = [
        f"inventory: {n} unique repos (Tier A anchors + negative controls + Tier B per-stratum topics, deduped)",
        f"active (non-archived): {len(active)}",
        f"archived: {n - len(active)}",
        "stratum histogram: " + ", ".join(f"{k}={v}" for k, v in top_strata),
        "language histogram: " + ", ".join(f"{k}={v}" for k, v in top_langs),
        "star bins: " + ", ".join(f"{k}={v}" for k, v in star_bins.items()),
        "",
        "top 50 by stars:",
    ]
    for r in active[:50]:
        lines.append(f"  {r['stars']:>8}  {(r['language'] or '?'):<12} {r['full_name']}  {r['stratum']}")
    with open(os.path.join(SNAP, "inventory_stats.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
