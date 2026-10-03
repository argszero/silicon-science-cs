#!/usr/bin/env python3
"""Issue #120 -- reference CURATION.

Curation is NOT discovery and NOT verification.  Discovery returned 824 candidates, most of them
noise (a relevance search matches any paper sharing a word).  This file applies an EXPLICIT,
reproducible RULE to that pool -- a title must match a family's pattern AND the paper must carry a
computer-science category -- and assigns each kept entry a role naming WHERE it is used.

Titles are COPIED from the discovery artefact (`refs/candidates.json`) by identifier, never
retyped.  Any chosen id that is NOT in the pool must be declared in EXTRAS with its own title, so
the difference between "found by search" and "supplied by the author" stays visible.

A role is a statement about WHERE an entry is used, not a quality label.

Usage:  /usr/bin/python3 refs_curate.py
Out:    refs/curated.json
"""
import json
import os
import re
import sys

CAND = "refs/candidates.json"
OUT = "refs/curated.json"

# The selection RULE, in two limbs -- BOTH must hold:
#   (a) TOPIC ANCHOR: the title must be about caching / memory / paging at all (without this, a
#       bare "LRU" or "locality" match pulls in radio astronomy and deep learning);
#   (b) FAMILY: the title must match one family's pattern; the first family that matches IS the
#       role, and the role is what the entry is cited for.
ANCHOR = re.compile(
    r"cach|memory|\bram\b|dram|\bssd\b|\bpage\b|\bpaging\b|\btlb\b|prefetch|evict|"
    r"replacement polic|\bnuma\b|\bcxl\b|\bhbm\b|tiered|memory tier|buffer pool|"
    r"\bcache line\b|storage hierar",
    re.I)

FAMILIES = [
    # the construct: the offline optimum, the ceiling, and lower bounds on it
    ("construct", re.compile(
        r"offline optimal|belady|optimal (eviction|replacement|caching|page|memory)|"
        r"optimally cach|lower bound.*(cach|paging)|miss ratio curve|hit rate curve|"
        r"optimal paging|capacity planning|(upper|lower) bound.*cach", re.I)),
    # the profile: reuse/stack distance and the statistics LRU is a function of
    ("profile", re.compile(
        r"reuse distance|stack distance|working set|miss.ratio curve|hit.rate curve|"
        r"access (pattern|trace)|memory access|locality|trace.driven|"
        r"cache (simulation|model|performance|analysis|behavior)|analytical model.*cach", re.I)),
    # the deployed policy family
    ("policy", re.compile(
        r"cache (replacement|eviction|admission|management|partitioning|bypass|hierarchy)|"
        r"replacement polic|eviction polic|last.level cache|set.associative|"
        r"page (replacement|reclamation|migration)|\b(lru|lfu|rrip|srrip|tinylfu|clock)\b|"
        r"thrash|cache line|memory controller", re.I)),
    # the theory: online paging, competitive analysis, learning-augmented caching
    ("theory", re.compile(
        r"competitive (paging|analysis|caching|ratio)|online paging|paging algorithm|"
        r"k.server|learning.augmented cach|online cach|metrical task|ski rental|"
        r"randomized (paging|caching)|caching with", re.I)),
    # memory tiering: the application the construct bounds
    ("tiering", re.compile(
        r"memory tier|tiered memory|cxl|far memory|\bnuma\b|disaggregat|"
        r"heterogeneous memory|multi.tier memory|persistent memory|"
        r"\bhbm\b|memory (bandwidth|reclaim|disaggregation|placement)|"
        r"page (migration|placement|fault)|demand paging|zswap|memory overcommit|"
        r"hot (page|data) (detection|tracking)", re.I)),
    # adjacent caches that run the same machinery
    ("adjacent", re.compile(
        r"\bkv cache\b|key.value cache|buffer pool|flash cache|storage cache|ssd cache|"
        r"web cache|cdn cach|prefetch|page cache|content cach|edge cach|"
        r"in.memory (cache|index)|memory (offload|swapping)", re.I)),
]

# Author-supplied entries: the pre-arXiv foundations the field is built on.  These are NOT in the
# discovery pool (arXiv's index begins in 1991 and these are 1966-1988), so they are declared here
# with their own titles, and each DOI was RESOLVED FROM CROSSREF by title before being written down
# -- three of the four had been mis-remembered, and the verifier caught them (see the round notes).
EXTRAS = [
    ("10.1147/sj.52.0078", "construct",
     "Belady's MIN algorithm: the offline optimum that this paper's phi* minimizes, and the origin of the whole construct", "A study of replacement algorithms for a virtual-storage computer"),
    ("10.1147/sj.92.0078", "profile",
     "Mattson et al.'s stack algorithm: the law that makes LRU's curve a function of the reuse-distance profile -- the fact this paper shows does NOT extend to the ceiling", "Evaluation techniques for storage hierarchies"),
    ("10.1145/2786.2793", "theory",
     "Sleator & Tarjan's competitive analysis of paging, whose ratios are asymptotic constants and do not bind at these trace lengths", "Amortized efficiency of list update and paging rules"),
    ("10.1145/363095.363141", "profile",
     "Denning's working-set model: the origin of the 'working set' whose size this paper shows is only part of the story", "The working set model for program behavior"),
]


# Limb (c): EXCLUSIONS.  A relevance search also returns neighbouring fields that share the word
# "cache" but not the machinery -- wireless/edge content caching, video streaming, recommender and
# RL-driven popularity caching, and ML training caches.  These are named sub-areas, not a taste
# list, so the exclusion is as auditable as the selection.
EXCLUDE = re.compile(
    r"wireless|cellular|edge cach|federated|d2d|mec\b|small cell|content delivery network|"
    r"video (stream|deliver|cach)|360 degree|recommend|popularity|crowd|blockchain|"
    r"semantic commun|satellite|uav\b|drone|non.terrestrial|quantum|federated learning|"
    r"training (throughput|accelerat)|gradient|inference serv.*(cluster|datacenter)? schedul|"
    r"graph neural|spiking|radiance|mesh|molecular|climate|physics|astronom|biology|"
    r"survey of.*(eviction|replacement) in (large )?language|prompt cach",
    re.I)


def bare(aid):
    return re.sub(r"v\d+$", "", aid)


# Limb (d): a REVIEW pass, stated as an explicit id list.  The rule's arms (a)-(c) are regexes and
# cannot judge a title; reading the surviving titles turned up entries that share a noun but not the
# machinery (radix sort on GPUs, an FDTD code, a CNN accelerator, a flow-anomaly table).  These are
# removed BY ID, and the removal is auditable because the ids are named.  An id that the rule never
# selected is ignored here, so the list cannot silently inject anything.
REVIEWED_OUT = [
    "1301.4539",    # Sophie, an FDTD code -- "memory bandwidth" in a physics code
    "1611.01137",   # hybrid radix sort on GPUs
    "2010.06075",   # HLS meets FPGA HBM -- accelerator benchmarking
    "2105.11754",   # ScalaBFS on HBM FPGAs
    "2205.00779",   # CNN accelerator zero-block regularisation
    "2203.15722",   # RL for power distribution networks
    "1902.01492",   # optimising CNN convolutions
    "1902.04143",   # flow anomaly detection in DRAM tables
    "2109.00474",   # leaking control flow via the prefetcher -- a security paper
    "2102.01764",   # instruction prefetcher microarchitecture
    "2201.12027",   # random-forest prefetcher manager
    "2008.00176",   # random-forest prefetcher adaptation
    "2406.14008",   # graph-analytics miss-correlation prefetcher
    "2412.05211",   # spatial patterns / prefetcher
    "1902.11028",   # a Valgrind tool for a process's working set
    "2301.07492",   # failure-tolerant training over disaggregated memory
    "2204.12889",   # memory-disaggregated object store for big data
    "2410.11260",   # ZNS flash cache -- a storage-media paper
    "2503.11665",   # NVMe FDP flash caches -- a storage-media paper
    "2409.05867",   # radiance cache -- inverse rendering
    "2011.06354",   # charge transport in metal-organic frameworks
    "2104.06225",   # a persistent-memory key-value store -- NDP, not replacement
    "2403.13693",   # not a caching paper (guards against a mis-picked id)
]


def is_cs(cats):
    return any(c.startswith(("cs.", "cs")) for c in cats)


def role_of(title):
    for role, pat in FAMILIES:
        if pat.search(title):
            return role
    return None


def diff_for(role, title):
    """A one-line statement of WHERE the entry is used -- generated from the role, so it is not
    typed per entry and cannot drift from the rule that selected it."""
    return {
        "construct": "a treatment of the offline optimum / the ceiling this paper computes exactly",
        "profile": "a treatment of the recurrence profile this paper shows under-determines the ceiling",
        "policy": "a deployed replacement policy whose miss curve the profile fixes (Mattson) but whose gap to the optimum it does not",
        "theory": "competitive-analysis theory for paging, whose bounds are asymptotic and do not bind at these trace lengths",
        "tiering": "a memory-tiering system that buys capacity; this paper's construct bounds what that can deliver",
        "adjacent": "an adjacent cache (KV / buffer pool / storage / edge) that runs the same replacement machinery",
    }[role]


def main():
    if not os.path.exists(CAND):
        print("missing %s -- run refs_discover.py first" % CAND, file=sys.stderr)
        sys.exit(1)
    pool = json.load(open(CAND))["candidates"]
    kept = []
    for c in pool:
        if not is_cs(c["cats"]):
            continue
        if not ANCHOR.search(c["title"]):          # limb (a): about caching/memory at all
            continue
        if EXCLUDE.search(c["title"]):             # limb (c): not an adjacent field
            continue
        if bare(c["id"]) in REVIEWED_OUT:          # limb (d): removed on review, by id
            continue
        role = role_of(c["title"])
        if role is None:
            continue
        kept.append((c, role))

    # CAP per family, ranked by QUERY SUPPORT -- how many of the discovery queries returned the
    # entry, a reproducible proxy for topical centrality (an entry several independent queries
    # agree on is more likely to be about the topic than one a single broad query matched).
    CAPS = {"construct": 40, "theory": 40, "profile": 24, "policy": 28, "tiering": 46,
            "adjacent": 22}
    out, seen = [], set()
    for role, _pat in FAMILIES:
        fam = [(c, r) for c, r in kept if r == role]
        fam.sort(key=lambda t: (-len(t[0]["queries"]), t[0]["published"]))
        for c, _r in fam[:CAPS[role]]:
            b = bare(c["id"])
            if b in seen:
                continue
            seen.add(b)
            out.append(dict(id=c["id"], bare=b, title=c["title"], published=c["published"],
                            cats=c["cats"], role=role, diff=diff_for(role, c["title"]),
                            support=len(c["queries"]), source="discovery"))

    for aid, role, diff, title in EXTRAS:
        b = bare(aid)
        if b in seen:
            continue
        seen.add(b)
        out.append(dict(id=aid, bare=b, title=title, published="(pre-arXiv)",
                        cats=[], role=role, diff=diff, source="author",
                        doi=aid if aid.startswith("10.") else None))

    roles = {}
    for o in out:
        roles[o["role"]] = roles.get(o["role"], 0) + 1
    os.makedirs("refs", exist_ok=True)
    json.dump(dict(n=len(out), roles=roles,
                   rule="cs category AND a topic anchor AND a family pattern; capped per family by "
                        "query support",
                   entries=out), open(OUT, "w"), indent=1)
    print("curated %d entries -> %s" % (len(out), OUT))
    for r in sorted(roles):
        print("   %-12s %d" % (r, roles[r]))
    print("   source: %d discovery, %d author" % (
        sum(1 for o in out if o["source"] == "discovery"),
        sum(1 for o in out if o["source"] == "author")))


if __name__ == "__main__":
    main()
