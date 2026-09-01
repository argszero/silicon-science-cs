#!/usr/bin/env python3
"""Issue #63 — Tier B stratification filter + Tier A anchor selection.

Input : snapshots/inventory.json (from search_repos.py)
Output: snapshots/tierb_candidates.json  — selected Tier B per-stratum repos (quota-capped)
         snapshots/tier_ab_corpus.json   — full corpus: Tier A anchors + NEG controls + Tier B
         snapshots/tierb_stats.txt       — selection stats

Rules (notes_r120.md + #52/#57/#61 lessons):
  - archived excluded
  - curated-list / knowledge / tutorial / docs / learning / exercise repos excluded
    (case-insensitive match on name + description; "awesome" lists, "interview", "cheat-sheet")
  - non-software repos excluded by description heuristics (devops-exercises etc.)
  - per-stratum quota: pick top-stars after exclusions; if a stratum has fewer
    candidates than quota, take all (and note the shortfall)
  - Tier A: seeds flagged tier_a_seed kept as anchors; blockchain-family seeds
    kept in S5 stratum; NEG_control seeds kept as negative controls
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(ROOT, "snapshots")

# per-stratum quotas (notes_r120.md design)
QUOTAS = {
    "S1_database": 50,
    "S2_storage": 25,
    "S3_coordination": 20,
    "S4_mq_streaming": 30,
    "S5_blockchain": 40,
    "S6_kv_cache_search": 15,
}

# curated/knowledge/tutorial exclusion patterns (lowercased)
EXCLUDE_PATTERNS = [
    r"awesome",
    r"tutorial",
    r"exercises?",
    r"interview",
    r"cheat[- ]sheet",
    r"roadmap",
    r"books?",
    r"resources?",
    r"learning",
    r"course",
    r"docs?\b",
    r"documentation",
    r"example",
    r"demo",
    r"starter",
    r"boilerplate",
    r"template",
    r"list of",
    r"curated",
    r"top-?\d+",
    r"the art of",
    r"coding",
    r"leetcode",
    r"algorithm.*(practice|challenge)",
    r"sample",
    r"getting started",
    r"learn",
    r"notes",
    r"knowledge",
]

# description-based software heuristics — repos whose description suggests
# non-distributed-systems software (pure web/frontend/mobile/etc.)
NON_DS_PATTERNS = [
    r"web framework",
    r"frontend",
    r"ui components",
    r"css",
    r"mobile app",
    r"android",
    r"ios app",
    r"game engine",
    r"video",
    r"image",
    r"photo",
    r"music",
    r"chatbot",
    r"website",
    r"blog",
    r"portfolio",
    r"latex",
    r"markdown",
    r"notion",
    r"figma",
    r"design",
    r"django",
    r"rails",
    r"next\.js",
    r"react",
    r"vue",
    r"angular",
    r"flutter",
    r"swiftui",
    r"react native",
]

# names that are known curated lists / knowledge repos (lowercase full_name)
EXCLUDE_NAMES = {
    "bregman-arie/devops-exercises",
    "kamranahmedse/developer-roadmap",
    "sindresorhus/awesome",
    "vinta/awesome-python",
    "jwasham/coding-interview-university",
    "donnemartin/system-design-primer",
    "public-apis/public-apis",
    "freeCodeCamp/freeCodeCamp",
}

# Tier A anchor systems + negative controls — independent of Tier B quotas.
# (These are the consensus-producing population; keep them OUT of Tier B so the
# H3 anchor-vs-general contrast is not polluted.)
ANCHOR_NAMES = {
    "etcd-io/etcd", "hashicorp/consul", "apache/zookeeper", "apache/kafka",
    "tikv/tikv", "redpanda-data/redpanda", "scylladb/scylladb",
    "apple/foundationdb", "lni/dragonboat", "tikv/raft-rs", "hashicorp/raft",
    "baidu/braft", "cometbft/cometbft", "hyperledger/fabric",
    "MystenLabs/sui", "aptos-labs/aptos-core",
}
NEG_NAMES = {"bitcoin/bitcoin", "ethereum/go-ethereum"}


def excluded(repo: dict) -> tuple[bool, str]:
    name = (repo.get("full_name") or "").lower()
    desc = (repo.get("description") or "").lower()
    if name in EXCLUDE_NAMES:
        return True, "known-curated"
    if any(re.search(p, desc) for p in EXCLUDE_PATTERNS):
        return True, "curated/knowledge/tutorial"
    if any(re.search(p, desc) for p in NON_DS_PATTERNS):
        return True, "non-distributed-systems"
    return False, ""


def main():
    with open(os.path.join(SNAP, "inventory.json")) as f:
        inventory = json.load(f)

    # Split by membership: Tier A anchors + NEG controls by name (regardless of
    # how they entered inventory), Tier B = everything else.
    # Case-insensitive: full_name is lowercased for the set comparison.
    anchor_l = {n.lower() for n in ANCHOR_NAMES}
    neg_l = {n.lower() for n in NEG_NAMES}
    tier_a, neg, tier_b_all = [], [], []
    for r in inventory:
        full = r["full_name"].lower()
        if full in neg_l:
            r["membership"] = "NEG"
            neg.append(r)
        elif full in anchor_l:
            r["membership"] = "TierA"
            tier_a.append(r)
        else:
            tier_b_all.append(r)
    tier_a.sort(key=lambda r: -r["stars"])
    neg.sort(key=lambda r: -r["stars"])

    # shortfall tracking
    tier_b_selected = {}
    stats_lines = []
    for stratum, quota in QUOTAS.items():
        cands = [r for r in tier_b_all if r["stratum"] == stratum and not r["archived"]]
        cands.sort(key=lambda r: -r["stars"])
        kept, rejected = [], 0
        for r in cands:
            is_ex, why = excluded(r)
            if is_ex:
                rejected += 1
                continue
            kept.append(r)
            if len(kept) >= quota:
                break
        tier_b_selected[stratum] = kept
        stats_lines.append(
            f"{stratum}: quota={quota} candidates={len(cands)} rejected={rejected} selected={len(kept)}"
        )

    tier_b_flat = [r for stratum in QUOTAS for r in tier_b_selected[stratum]]
    for r in tier_b_flat:
        r["membership"] = "TierB"
    corpus = tier_a + neg + tier_b_flat

    with open(os.path.join(SNAP, "tierb_candidates.json"), "w") as f:
        json.dump({k: v for k, v in tier_b_selected.items()}, f, indent=1)
    with open(os.path.join(SNAP, "tier_ab_corpus.json"), "w") as f:
        json.dump(corpus, f, indent=1)

    by_membership = {}
    for r in corpus:
        by_membership[r["membership"]] = by_membership.get(r["membership"], 0) + 1
    by_lang = {}
    for r in corpus:
        lang = r["language"] or "unknown"
        by_lang[lang] = by_lang.get(lang, 0) + 1

    lines = [
        "tier_ab_corpus: %d repos" % len(corpus),
        "membership: " + ", ".join(f"{k}={v}" for k, v in sorted(by_membership.items())),
        "language: " + ", ".join(f"{k}={v}" for k, v in sorted(by_lang.items(), key=lambda kv: -kv[1])),
        "",
    ] + stats_lines + ["", "TierA anchors:"]
    for r in tier_a:
        lines.append(f"  {r['stars']:>8}  {(r['language'] or '?'):<10} {r['full_name']}  {r['stratum']}")
    lines.append("NEG controls:")
    for r in neg:
        lines.append(f"  {r['stars']:>8}  {(r['language'] or '?'):<10} {r['full_name']}")
    with open(os.path.join(SNAP, "tierb_stats.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
