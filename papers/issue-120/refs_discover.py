#!/usr/bin/env python3
"""Issue #120 -- reference DISCOVERY over the arXiv API.

Discovery is NOT curation and NOT verification.  An arXiv search returns noise (an off-topic
paper sharing a word), and this file records only WHAT WAS FOUND, with the query that found it.

The sibling `refs_tool.py` is the verifier (re-fetch by identifier, compare titles); the sibling
`refs_curate.py` is the curator.  Only curation decides what is cited; only the verifier decides
whether a citation is real.

Usage:  /usr/bin/python3 refs_discover.py [--refresh]
Cache:  refs/arxiv_cache/<slug>.json   (a re-run does not re-hit the API)
Out:    refs/candidates.json
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
CACHE = "refs/arxiv_cache"
OUT = "refs/candidates.json"
MAX_RESULTS = 40

# SHORT phrases only: the API matches a quoted phrase VERBATIM, so a long query returns zero and
# reads like a thin literature (measured on #116: 40 of 46 long queries returned 0 results).
QUERIES = [
    # --- the construct: the offline optimum and the profile it is defined against ----------------
    ("offline-optimal", "offline optimal caching"),
    ("belady", "Belady's algorithm"),
    ("paging-competitive", "competitive paging"),
    ("paging-lower-bound", "paging lower bound"),
    ("weighted-caching", "weighted caching"),
    ("caching-migration", "caching with migration"),
    ("cache-oblivious", "cache-oblivious"),
    # --- the profile: reuse / stack distance, and what LRU is a function of ----------------------
    ("reuse-distance", "reuse distance"),
    ("stack-distance", "stack distance"),
    ("stack-algorithm", "stack algorithm"),
    ("miss-ratio-curve", "miss ratio curve"),
    ("hit-rate-curve", "hit rate curve"),
    ("working-set", "working set"),
    ("locality", "temporal locality"),
    ("trace-driven", "trace-driven simulation"),
    ("cache-simulation", "cache simulation"),
    ("cache-modeling", "cache performance model"),
    ("reuse-prediction", "reuse distance prediction"),
    # --- the deployed policies: the family the profile fixes -------------------------------------
    ("lru", "least recently used"),
    ("lfu", "least frequently used"),
    ("rrip", "re-reference interval prediction"),
    ("arc-cache", "adaptive replacement cache"),
    ("tinylfu", "TinyLFU"),
    ("lru-k", "LRU-K"),
    ("clock", "clock replacement algorithm"),
    ("eviction", "cache eviction"),
    ("admission", "cache admission"),
    ("replacement-survey", "cache replacement survey"),
    ("set-associative", "set-associative cache"),
    ("last-level-cache", "last level cache"),
    # --- memory tiering: the application the construct bounds ------------------------------------
    ("memory-tiering", "memory tiering"),
    ("tiered-memory", "tiered memory"),
    ("cxl-memory", "CXL memory"),
    ("far-memory", "far memory"),
    ("page-migration", "page migration"),
    ("hot-page", "hot page detection"),
    ("numa-balancing", "NUMA balancing"),
    ("memory-disaggregation", "memory disaggregation"),
    ("hbm", "high bandwidth memory"),
    ("memory-bandwidth", "memory bandwidth"),
    ("swap-reclaim", "memory reclaim"),
    ("zswap", "zswap"),
    ("thp", "transparent huge page"),
    # --- adjacent caches that use the same machinery ---------------------------------------------
    ("buffer-pool", "buffer pool replacement"),
    ("kv-cache", "KV cache management"),
    ("kv-eviction", "KV cache eviction"),
    ("web-cache", "web cache replacement"),
    ("cdn-cache", "CDN caching"),
    ("flash-cache", "flash cache"),
    ("storage-cache", "storage cache"),
    ("in-memory-cache", "in-memory cache"),
    ("prefetcher", "hardware prefetcher"),
    ("tlb", "translation lookaside buffer"),
]


def slug(q):
    return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:60]


def fetch(query, refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, slug(query) + ".json")
    if os.path.exists(path) and not refresh:
        with open(path) as f:
            return json.load(f)
    url = ("http://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote('all:"%s"' % query)
           + "&sortBy=relevance&sortOrder=descending&max_results=%d" % MAX_RESULTS)
    raw = ""
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                raw = r.read().decode("utf-8", "replace")
            break
        except Exception as e:
            if attempt == 3:
                print("  ! fetch failed: %s (%s)" % (query, e), file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    ents = []
    if raw:
        try:
            root = ET.fromstring(raw)
            for e in root.findall("a:entry", NS):
                # keep the FULL identifier: pre-2007 ids carry a category prefix
                # (math/0508451), and stripping it to the bare number makes the id unresolvable
                # (arXiv answers HTTP 400) -- measured on #118's first verification run.
                rid = e.find("a:id", NS).text.replace("http://arxiv.org/abs/", "")
                tt = " ".join(e.find("a:title", NS).text.split())
                pub = e.find("a:published", NS).text[:10]
                cats = [c.get("term") for c in e.findall("a:category", NS)]
                ents.append(dict(id=rid, title=tt, published=pub, cats=cats))
        except ET.ParseError:
            print("  ! parse failed: %s" % query, file=sys.stderr)
    with open(path, "w") as f:
        json.dump(ents, f, indent=1)
    return ents


def main():
    refresh = "--refresh" in sys.argv
    cand = {}
    print("discovery over %d queries (MAX_RESULTS=%d)" % (len(QUERIES), MAX_RESULTS))
    for i, (key, q) in enumerate(QUERIES, 1):
        ents = fetch(q, refresh)
        print("  [%2d/%d] %-24s -> %d" % (i, len(QUERIES), key, len(ents)))
        for e in ents:
            c = cand.setdefault(e["id"], dict(id=e["id"], title=e["title"], published=e["published"],
                                              cats=e["cats"], queries=[]))
            if key not in c["queries"]:
                c["queries"].append(key)
        time.sleep(3)
    os.makedirs("refs", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(dict(n_queries=len(QUERIES), n_candidates=len(cand),
                       candidates=sorted(cand.values(), key=lambda x: x["id"])), f, indent=1)
    print("\n%d unique candidates -> %s" % (len(cand), OUT))


if __name__ == "__main__":
    main()
