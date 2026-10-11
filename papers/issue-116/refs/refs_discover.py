#!/usr/bin/env python3
"""Issue #116 -- reference DISCOVERY over the arXiv API.

Discovers candidate references by topic phrase and writes refs/candidates.json.
Discovery is NOT curation and NOT verification: an arXiv search returns noise
(an off-topic paper with a shared word), and this file says only WHAT WAS FOUND.

The sibling `refs_tool.py` is the verifier: it re-fetches each CHOSEN entry by its
own identifier and compares the returned title. Only curation decides what is
cited; only the verifier decides whether a citation is real.

Usage:  python3 refs_discover.py [--refresh]
Cache:  refs/arxiv_cache/<slug>.xml   (a re-run does not re-hit the API)
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

NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
CACHE = "refs/arxiv_cache"
OUT = "refs/candidates.json"
MAX_RESULTS = 40

# SHORT phrases only: the API matches the quoted string verbatim, so a long query
# returns zero (measured: all:+"action chunking robot policy" -> 0 results).
QUERIES = [
    # the construct: the execution horizon of a chunked policy
    ("action-chunking", "action chunking"),
    ("chunked-policy", "chunked action"),
    ("real-time-chunking", "real-time chunking"),
    ("temporal-ensembling", "temporal ensembling"),
    ("diffusion-policy", "diffusion policy"),
    ("flow-policy", "flow matching policy"),
    ("vision-language-action", "vision-language-action"),
    ("action-repetition", "action repetition"),
    ("frame-skip", "frame skip"),
    ("control-frequency", "control frequency"),
    ("inference-latency", "inference latency"),
    ("open-loop", "open-loop execution"),
    # the cost side
    ("input-delay", "input delay"),
    ("delay-margin", "delay margin"),
    ("networked-control", "networked control"),
    ("sampled-data", "sampled-data control"),
    ("stale-information", "stale information"),
    ("actuator-saturation", "actuator saturation"),
    ("anytime-algorithm", "anytime algorithm"),
    ("imprecise-computation", "imprecise computation"),
    ("speculative", "speculative execution latency"),
    ("inference-scheduling", "inference scheduling"),
    # the theory
    ("receding-horizon", "receding horizon"),
    ("prediction-horizon", "prediction horizon"),
    ("double-integrator", "double integrator"),
    ("lyapunov-equation", "Lyapunov equation"),
    ("lqg", "linear quadratic Gaussian"),
    ("heavy-tail", "heavy-tailed"),
    ("bursty", "bursty disturbance"),
    ("options", "options framework"),
    ("macro-action", "macro-action"),
    ("amortized-inference", "amortized inference"),
    ("stochastic-mpc", "stochastic model predictive control"),
    ("disturbance-observer", "disturbance observer"),
    # the setting
    ("teleoperation", "teleoperation latency"),
    ("humanoid", "humanoid control"),
    ("visual-servoing", "visual servoing"),
    ("edge-inference", "edge inference latency"),
    ("imitation-learning", "imitation learning manipulation"),
    ("rl-manipulation", "reinforcement learning manipulation"),
    ("control-barrier", "control barrier function"),
    ("world-model", "world model planning"),
    ("dexterous", "dexterous manipulation"),
    ("robot-benchmark", "robot manipulation benchmark"),
    ("vla-inference", "vision-language-action inference"),
    ("chunk-length", "action chunk length"),
]


def norm_title(t):
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def fetch(slug, query, refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, slug + ".xml")
    if os.path.exists(path) and not refresh:
        return open(path, "rb").read()
    url = ("https://export.arxiv.org/api/query?search_query=" +
           urllib.parse.quote('all:"%s"' % query) +
           "&sortBy=relevance&sortOrder=descending&max_results=%d" % MAX_RESULTS)
    req = urllib.request.Request(url, headers={"User-Agent": "issue116-refs/1.0"})
    body = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            break
        except urllib.error.HTTPError as e:                 # 429 -> back off
            if e.code != 429 or attempt == 3:
                raise
            time.sleep(15.0 * (attempt + 1))
    with open(path, "wb") as fh:
        fh.write(body)
    time.sleep(3.0)            # arXiv asks for >= 3 s between calls
    return body


def parse(body):
    root = ET.fromstring(body)
    out = []
    for e in root.findall("a:entry", NS):
        raw_id = (e.findtext("a:id", "", NS) or "").strip()
        aid = raw_id.rsplit("/abs/", 1)[-1]
        aid = re.sub(r"v\d+$", "", aid)              # canonical id without version
        out.append({
            "title": re.sub(r"\s+", " ", (e.findtext("a:title", "", NS) or "")).strip(),
            "arxiv": aid,
            "published": (e.findtext("a:published", "", NS) or "")[:10],
            "updated": (e.findtext("a:updated", "", NS) or "")[:10],
            "category": (e.find("arxiv:primary_category", NS).get("term")
                         if e.find("arxiv:primary_category", NS) is not None else ""),
            "authors": [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)][:6],
        })
    return out


def main():
    refresh = "--refresh" in sys.argv
    seen, cands, per_q = {}, [], {}
    for slug, q in QUERIES:
        try:
            entries = parse(fetch(slug, q, refresh))
        except Exception as e:                              # noqa: BLE001
            print(f"  {slug:<22} FETCH FAILED: {type(e).__name__}: {e}")
            per_q[slug] = 0
            continue
        n_new = 0
        for it in entries:
            ti = norm_title(it["title"])
            if not ti or ti in seen:
                continue
            seen[ti] = True
            it["query"] = slug
            cands.append(it)
            n_new += 1
        per_q[slug] = n_new
        print(f"  {slug:<22} returned {len(entries):>3}  new {n_new:>3}")
    with open(OUT, "w") as fh:
        json.dump({"n": len(cands), "source": "arXiv API (export.arxiv.org)",
                   "max_results_per_query": MAX_RESULTS, "per_query_new": per_q,
                   "candidates": cands}, fh, indent=1, sort_keys=True)
    print(f"\n{len(cands)} unique candidates -> {OUT}")
    print("NOTE: discovery only -- curation decides what is CITED; verification"
          " against the entry's own identifier is refs_tool.py's job.")
    print("sha256", hashlib.sha256(open(OUT, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
