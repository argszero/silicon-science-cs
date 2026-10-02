#!/usr/bin/env python3
"""Issue #118 -- reference DISCOVERY over the arXiv API.

Discovery is NOT curation and NOT verification.  An arXiv search returns noise (an off-topic
paper sharing a word), and this file records only WHAT WAS FOUND, with the query that found it.

The sibling `refs_tool.py` is the verifier (re-fetch by identifier, compare titles); the sibling
`refs_curate.py` is the curator.  Only curation decides what is cited; only the verifier decides
whether a citation is real.

Usage:  /usr/bin/python3 refs_discover.py [--refresh]
Cache:  refs/arxiv_cache/<slug>.json   (a re-run does not re-hit the API)
Out:    refs/candidates.json
"""
import hashlib
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
    # --- the construct: capacity, dropping, routing discipline --------------------------------
    ("capacity-factor", "expert capacity"),
    ("capacity-factor-2", "capacity factor"),
    ("token-dropping", "token dropping"),
    ("token-choice", "token-choice routing"),
    ("expert-choice", "expert-choice routing"),
    ("top-k-routing", "top-k routing"),
    ("router-collapse", "routing collapse"),
    ("expert-specialization", "expert specialization"),
    ("sparse-moe", "sparse mixture-of-experts"),
    ("conditional-computation", "conditional computation"),
    # --- load balancing: the field's remedy ---------------------------------------------------
    ("aux-loss", "auxiliary loss load balancing"),
    ("load-balance-loss", "load balancing loss"),
    ("aux-loss-free", "auxiliary-loss-free"),
    ("bias-balancing", "bias-based balancing"),
    ("gating-balance", "gating network balance"),
    ("load-imbalance", "expert load imbalance"),
    # --- dispatch / expert parallelism --------------------------------------------------------
    ("expert-parallelism", "expert parallelism"),
    ("all-to-all", "all-to-all communication"),
    ("token-dispatch", "token dispatching"),
    ("expert-offloading", "expert offloading"),
    ("expert-caching", "expert caching"),
    # --- inference serving --------------------------------------------------------------------
    ("moe-inference", "Mixture-of-Experts inference"),
    ("moe-serving", "MoE serving"),
    ("speculative-moe", "speculative decoding mixture-of-experts"),
    ("batch-inference", "batch inference latency"),
    ("continuous-batching", "continuous batching"),
    ("dynamic-shapes", "dynamic tensor shapes"),
    # --- the theory: tails, order statistics, overflow ----------------------------------------
    ("order-statistics", "order statistics maximum"),
    ("balls-into-bins", "balls into bins"),
    ("binomial-tail", "binomial tail"),
    ("saddlepoint", "saddlepoint approximation"),
    ("multinomial-tail", "multinomial tail probability"),
    ("max-load", "maximum load"),
    ("occupancy", "occupancy problem"),
    ("large-deviations", "large deviations"),
    ("queuing-overflow", "queue overflow"),
    # --- architectures / named systems --------------------------------------------------------
    ("switch-transformer", "Switch Transformer"),
    ("gshard", "GShard"),
    ("glam", "GLaM"),
    ("mixtral", "Mixtral of Experts"),
    ("deepseek-moe", "DeepSeekMoE"),
    ("qwen-moe", "Qwen mixture-of-experts"),
    ("olmoe", "OLMoE"),
    ("dbrx", "DBRX"),
    ("model-scaling", "mixture-of-experts scaling"),
    # --- risk / security ----------------------------------------------------------------------
    ("capacity-overflow", "capacity overflow backdoor"),
    ("moe-backdoor", "backdoor mixture-of-experts"),
    ("routing-attack", "routing attack"),
    # --- adjacent framing the manuscript leans on ---------------------------------------------
    ("throughput-latency", "throughput latency tradeoff"),
    ("memory-bound", "memory-bound inference"),
    ("hardware-utilization", "hardware utilization"),
    ("quantization-moe", "quantization mixture-of-experts"),
    ("pruning-moe", "expert pruning"),
    ("moe-finetuning", "mixture-of-experts fine-tuning"),
    ("moe-multimodal", "mixture-of-experts multimodal"),
    ("moe-vision", "mixture-of-experts vision"),
    ("moe-robotics", "mixture-of-experts robotics"),
    ("moe-long-context", "long context inference"),
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
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                raw = r.read().decode("utf-8", "replace")
            break
        except Exception as e:
            if attempt == 3:
                raw = ""
                print("  ! fetch failed: %s (%s)" % (query, e), file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    ents = []
    if raw:
        try:
            root = ET.fromstring(raw)
            for e in root.findall("a:entry", NS):
                # keep the FULL identifier: pre-2007 ids carry a category prefix
                # (math/0508451), and stripping it to the bare number makes the id unresolvable
                # (arXiv answers HTTP 400) -- measured on the first verification run.
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
