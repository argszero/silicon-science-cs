#!/usr/bin/env python3
"""Issue #61 — Tier B filter: from raw inventory to the census population.

Population = top-starred open-source SOFTWARE projects per ecosystem bucket
(>=1k stars, non-archived), excluding curated lists / knowledge bases / docs-only
(they contain no code and would dominate star rankings).

Buckets + quotas (design from notes_r111.md, total ~200):
  Python 40, Go 35, Rust 30, Java 30, C/C++ 35 (merged C + C++), JS/TS 30 (merged).

Outputs:
  snapshots/tierb_candidates.json  — {full_name: {stars, language, description, head_sha placeholder}}
  snapshots/tierb_filter_stats.txt — drops by reason + final counts
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(ROOT, "snapshots")

QUOTAS = {"Python": 40, "Go": 35, "Rust": 30, "Java": 30, "C/C++": 35, "JS/TS": 30}
LANG_BUCKET = {
    "Python": "Python", "Go": "Go", "Rust": "Rust", "Java": "Java",
    "C": "C/C++", "C++": "C/C++", "JavaScript": "JS/TS", "TypeScript": "JS/TS",
}

# Curated-list / knowledge-base / learning / docs-only patterns (name or description).
LIST_PATTERNS = [
    r"^awesome[- ]", r"-awesome$", r"^[a-z0-9-]+-list$", r"list-of-", r"lists$",
    r"free-programming", r"project-based-learning", r"system-design", r"interview",
    r"handbook", r"cheat-?sheet", r"roadmap", r"-guide$", r"tutorial", r"docs$",
    r"collection", r"examples?$", r"the-algorithms", r"algorithms implemented",
    r"hello-algo", r"hello 算法", r"hellogithub", r"leetcode", r"design patterns implemented",
    r"knowledge", r"courses?$", r"books?$", r"blog", r"notes$", r"resources?$",
    r"public-apis", r"best-of", r"hackathon", r"design-resources", r"free-",
    r"^js$", r"java-guide", r"javascript-algorithms", r"javalearning", r"algorithm$",
    r"interview guide", r"面试", r"algorithm animation", r"codebase and curriculum",
    r"learning-example", r"-learning$", r"springboot-learning", r"learning ",
]
NAME_ONLY = [r"^awesome", r"-awesome$", r"public-apis", r"free-programming", r"hellogithub",
             r"hello-algo", r"java-design-patterns", r"leetcode", r"-guide$", r"^the-algorithms"]


def is_list_repo(r: dict) -> bool:
    name = r["full_name"].lower().split("/")[1]
    desc = (r.get("description") or "").lower()
    blob = f"{name} {desc}"
    for pat in LIST_PATTERNS:
        if re.search(pat, blob):
            return True
    # curated-list name heuristics (description may be empty)
    for pat in NAME_ONLY:
        if re.search(pat, name):
            return True
    return False


def main():
    inv = json.load(open(os.path.join(SNAP, "inventory.json")))
    buckets = {b: [] for b in QUOTAS}
    drops = {"archived": 0, "list": 0, "unknown_lang": 0, "stars<1k": 0, "quota": 0}
    kept = {}

    # Stage 1: bucket all active tierb repos (seeds are a separate stratum; skip for Tier B)
    for r in inv:
        if r["source"] != "tierb_search":
            continue
        if r.get("archived"):
            drops["archived"] += 1
            continue
        if (r.get("stars") or 0) < 1000:
            drops["stars<1k"] += 1
            continue
        bucket = LANG_BUCKET.get(r.get("language"))
        if not bucket:
            drops["unknown_lang"] += 1
            continue
        if is_list_repo(r):
            drops["list"] += 1
            continue
        buckets[bucket].append(r)

    # Stage 2: quota per bucket — stratified across the star range.
    # top_band = first 100 per bucket (mega-projects), mid_band = 101+ (1k-100k zone).
    # Select ceil(Q/2) from the top band and floor(Q/2) from the mid band,
    # so the population spans mega and mid-range projects (design: >=1k stars).
    for b, quota in QUOTAS.items():
        rows = sorted(buckets[b], key=lambda r: -r["stars"])
        top_band, mid_band = rows[:100], rows[100:]
        n_top = (quota + 1) // 2
        n_mid = quota - n_top
        chosen = top_band[:n_top] + mid_band[:n_mid]
        drops["quota"] += max(0, len(rows) - quota)
        for r in chosen:
            kept[r["full_name"]] = {
                "stars": r["stars"],
                "language": r["language"],
                "bucket": b,
                "description": (r.get("description") or "")[:300],
            }

    with open(os.path.join(SNAP, "tierb_candidates.json"), "w") as f:
        json.dump(kept, f, indent=1, sort_keys=True)

    lines = [
        f"Tier B candidates: {len(kept)}",
        "drops: " + ", ".join(f"{k}={v}" for k, v in drops.items()),
        "",
        "per-bucket counts:",
    ]
    per = {}
    for r in kept.values():
        per[r["bucket"]] = per.get(r["bucket"], 0) + 1
    for b, n in sorted(per.items()):
        lines.append(f"  {b}: {n}")
    lines.append("")
    lines.append("lowest-star kept per bucket (quota floor):")
    for b in QUOTAS:
        rows = sorted([r for r in kept.values() if r["bucket"] == b], key=lambda x: -x["stars"])
        if rows:
            lines.append(f"  {b}: min {rows[-1]['stars']} stars ({rows[-1]['language']})")
    with open(os.path.join(SNAP, "tierb_filter_stats.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
