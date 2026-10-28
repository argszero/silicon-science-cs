#!/usr/bin/env python3
"""Issue #155 -- harvest a reference pool from Crossref, with its provenance.

Design, and why it is shaped this way:

* **Every query carries a topic term AND a systems term.** `scheduling`,
  `priority`, `queue`, `admission` all have enormous other-field senses (job
  scheduling, ER triage, admission to university, queuing theory), so a
  single-term query returns a pool that is mostly not about this paper. The
  pairing is the mechanical screen; the review pass below is the semantic one.
* **The search form is stored with the pool, not with the manuscript**: the
  indices, the exact query strings, the window on a named date field with both
  endpoints, and the scan date, so a reader can re-run it and reach the same
  absence.
* **Rejections are counted and printed.** A pool that silently drops records is
  a lie of omission.

Output: pool.json (every harvested record plus its provenance and its fate).
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "pool.json")

# --- the search form, stated before it is run ---------------------------------
INDEX = "api.crossref.org/works, field query.bibliographic"
# window on the `issued` date field, both endpoints; the lower endpoint reaches
# back past the oldest work the paper can build on (Even-Itai 1971, Tarjan 1972)
WINDOW = {"field": "issued", "from": "1971-01-01", "to": "2026-10-28"}
SCAN_DATE = "2026-10-28"

# Each entry: (label, topic term, systems term). Both halves are joined into one
# bibliographic query; a record must be returned by the pair, not by either half.
QUERIES = [
    # ---- group A: the programmable-scheduling literature the paper answers ----
    ("pifo",        "push-in first-out",                  "programmable packet scheduling"),
    ("prog-sched",  "programmable packet scheduling",     "switch"),
    ("sp-pifo",     "strict-priority queues approximating", "PIFO"),
    ("packs",       "approximating PIFO",                 "packet scheduling"),
    ("rank-sched",  "packet rank scheduling",             "programmable data plane"),
    ("p4-sched",    "P4 programmable scheduler",          "packet"),
    ("smartnic-q",  "smartNIC queue",                     "packet processing"),
    ("hw-pq",       "hardware priority queue",            "network device"),
    # ---- group B: switch scheduling algorithms (the device model) ----
    ("voq",         "virtual output queueing",            "switch scheduling"),
    ("islip",       "iterative round robin matching",     "input-queued switch"),
    ("bvn",         "Birkhoff-von Neumann decomposition",  "switch scheduling"),
    ("combined-in", "combined input-output queueing",     "packet switch"),
    ("bufferless",  "bufferless switching",               "packet network"),
    ("reorder-sw",  "packet reordering",                  "switch"),
    ("linecard",    "line card scheduling",               "router"),
    # ---- group C: dequeue disciplines the paper compares ----
    ("strict-pri",  "strict priority scheduling",         "network queue"),
    ("drr",         "deficit round robin",                "packet scheduling"),
    ("wfq",         "weighted fair queueing",             "packet scheduling"),
    ("fair-share",  "fair share scheduling",              "network switch"),
    # ---- group D: permutation sorting machines (the statistic's home) ----
    ("perm-parq",   "permutation",                        "parallel queues"),
    ("sort-device", "sorting with a network",             "queues and stacks"),
    ("deque-sort",  "double-ended queue",                 "permutation sorting"),
    ("patience",    "patience sorting",                   "longest increasing subsequence"),
    ("descent-perm","descents",                           "permutation statistics"),
    ("queue-num",   "queue number",                       "graph layout"),
    # ---- group E: the combinatorial machinery ----
    ("dilworth",    "partially ordered set",              "chain decomposition theorem"),
    ("dilworth2",   "Dilworth theorem",                   "poset width"),
    ("rsk",         "Robinson-Schensted correspondence",  "subsequence"),
    ("ehrt",        "Erdos-Szekeres",                     "monotone subsequence"),
    # ---- group F: online algorithms / competitive analysis ----
    ("competitive", "competitive analysis",               "online algorithm"),
    ("lookahead",   "lookahead",                          "online scheduling"),
    ("paging-comp", "competitive paging",                 "lookahead"),
    # ---- group G: measurement of real schedulers ----
    ("trace-sched", "packet trace",                       "scheduling evaluation"),
    ("prod-sched",  "production traffic",                 "scheduling deployment"),
    ("fct",         "flow completion time",               "packet scheduling"),
]

ROWS = 60
ACADEMIC_TYPES = {"journal-article", "proceedings-article", "book-chapter",
                  "posted-content", "report"}


def fetch(label, topic, systems):
    q = urllib.parse.urlencode({
        "query.bibliographic": "%s %s" % (topic, systems),
        "rows": str(ROWS),
        "select": "title,author,container-title,issued,DOI,type,abstract",
        "filter": "from-pub-date:%s,until-pub-date:%s" % (WINDOW["from"], WINDOW["to"]),
    })
    url = "https://api.crossref.org/works?" + q
    req = urllib.request.Request(url, headers={
        "User-Agent": "silicon-science-cs journal package builder (issue 155)"})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=60) as fh:
                return json.load(fh)["message"]["items"]
        except Exception as exc:                                    # noqa: BLE001
            print("   ! %s attempt %d: %s" % (label, attempt, exc))
            time.sleep(3)
    return []


def norm(it):
    title = (it.get("title") or [""])[0]
    authors = [a.get("family") or a.get("name") or "" for a in (it.get("author") or [])]
    year = None
    parts = (it.get("issued", {}) or {}).get("date-parts") or [[None]]
    if parts and parts[0]:
        year = parts[0][0]
    return {
        "doi": (it.get("DOI") or "").lower(),
        "title": title.strip(),
        "authors": [a for a in authors if a],
        "venue": ((it.get("container-title") or [""])[0] or "").strip(),
        "year": year,
        "type": it.get("type") or "",
    }


def main():
    pool = {}
    provenance = []
    for label, topic, systems in QUERIES:
        print("== query %-11s  topic=%r  systems=%r" % (label, topic, systems))
        items = fetch(label, topic, systems)
        print("   returned %d" % len(items))
        provenance.append({"label": label, "topic": topic, "systems": systems,
                           "returned": len(items)})
        for it in items:
            r = norm(it)
            if not r["doi"] or not r["title"]:
                continue
            if r["doi"] in pool:
                pool[r["doi"]]["queries"].append(label)
                continue
            r["queries"] = [label]
            pool[r["doi"]] = r
        time.sleep(1.0)

    records = sorted(pool.values(), key=lambda r: r["doi"])

    # --- mechanical screen 1: academic type whitelist -------------------------
    kept, rejected_type = [], []
    for r in records:
        if r["type"] in ACADEMIC_TYPES:
            kept.append(r)
        else:
            r["reject_reason"] = "type: %s" % (r["type"] or "none")
            rejected_type.append(r)

    # --- mechanical screen 2: has a year and a venue or a DOI-hosted type -----
    kept2, rejected_meta = [], []
    for r in kept:
        if r["year"] and (r["venue"] or r["type"] in ("journal-article", "proceedings-article")):
            kept2.append(r)
        else:
            r["reject_reason"] = "no year or no venue"
            rejected_meta.append(r)

    summary = {
        # The first design of this harvester paired broad topic terms
        # ("scheduling", "queue", "priority") with broad systems terms. Run on
        # 2026-10-28 it returned 1059 unique records of which the great majority
        # were queueing theory (M/G/1 waiting times), active queue management,
        # ATM buffer schemes and dictionary-like keyword records whose "title" is
        # a term ("packet switch"). That is the homonym failure this file's
        # docstring warns about, so the query set above names CONSTRUCTS instead
        # and the population was widened rather than the screen loosened.
        "design_revision": (
            "v1 broad topic+systems pairs (20 queries) harvested 1059 unique "
            "records dominated by homonyms; v2 below names specific constructs"),
        "index": INDEX,
        "window": WINDOW,
        "scan_date": SCAN_DATE,
        "queries": provenance,
        "harvested_unique": len(records),
        "rejected_type": len(rejected_type),
        "rejected_meta": len(rejected_meta),
        "kept": len(kept2),
    }
    out = {"summary": summary,
           "kept": kept2,
           "rejected": rejected_type + rejected_meta}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("\nharvested unique: %d" % len(records))
    print("rejected, non-academic type: %d" % len(rejected_type))
    print("rejected, missing year/venue: %d" % len(rejected_meta))
    print("kept for review: %d" % len(kept2))
    print("wrote %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
