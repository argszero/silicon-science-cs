#!/usr/bin/env python3
"""Issue #155 -- screen the harvested pool down to candidates, with reasons counted.

Two passes, because one pass is what produced the homonym pool:

  pass 1 (significance)  drop records whose title names a DIFFERENT field that
                         shares the vocabulary: queueing theory (waiting times,
                         vacations, retrials), active queue management, ATM
                         buffer schemes, wireless/cellular scheduling, and
                         dictionary-like records whose "title" is a bare term.
  pass 2 (construct)     keep a record only if its title names a construct this
                         paper actually uses.

A record is kept only if it survives BOTH. Every rejection is stored with its
reason and counted, because a screen that silently drops records is a lie of
omission.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "pool.json")
OUT = os.path.join(HERE, "candidates.json")

# pass 1: other fields that share the words
OTHER_FIELD = [
    (re.compile(r"M/G/1|M/M/1|G/G/1|vacation|retrial|polling system|waiting time|"
                r"busy period|queue length|arrival rate|markov|markovian|stationary distribution", re.I),
     "queueing theory"),
    (re.compile(r"active queue management|\bAQM\b|\bRED\b|random early|drop precedence|"
                r"congestion control|\bECN\b", re.I), "AQM / congestion control"),
    (re.compile(r"\bATM\b|asynchronous transfer mode", re.I), "ATM"),
    (re.compile(r"\bMIMO\b|satellite|CDMA|cellular|\bLTE\b|5G|\bWiFi\b|wireless|"
                r"radio resource|\bOFDM", re.I), "wireless / cellular"),
    (re.compile(r"university|student admission|hospital|triage|job shop|"
                r"supply chain|inventory|call center", re.I), "unrelated application"),
    (re.compile(r"\bLRU\b|\bcache replacement\b|\bcaching\b", re.I), "cache replacement"),
]

# pass 2: constructs this paper actually uses
CONSTRUCTS = [
    (re.compile(r"PIFO|push-in first-out|push in first out", re.I), "PIFO"),
    (re.compile(r"programmable (packet )?sched|packet sched|packet-sched", re.I), "packet scheduling"),
    (re.compile(r"priority queue", re.I), "priority queue structure"),
    (re.compile(r"switch sched|input-queued|virtual output|output-queued|"
                r"combined input|matching", re.I), "switch scheduling"),
    (re.compile(r"strict priority|deficit round robin|weighted fair queue|fair queue|"
                r"round robin", re.I), "dequeue discipline"),
    (re.compile(r"permutation", re.I), "permutations"),
    (re.compile(r"descent", re.I), "descents"),
    (re.compile(r"increasing subsequence|patience sorting|Erdos|Szekeres|"
                r"Robinson.Schensted", re.I), "subsequence theory"),
    (re.compile(r"Dilworth|partially ordered|poset|chain decompos|chain partition", re.I), "posets"),
    (re.compile(r"sorting network|comparator network|sorting with", re.I), "sorting networks"),
    (re.compile(r"competitive analysis|competitive ratio|online algorithm", re.I), "competitive analysis"),
    (re.compile(r"lookahead", re.I), "lookahead"),
    (re.compile(r"bufferless|reorder|reorder(ing)? buffer", re.I), "reordering"),
    (re.compile(r"smartNIC|network processor|programmable data plane|\bP4\b|"
                r"fpga|hardware queue|line card|line-rate|line rate", re.I), "hardware data plane"),
    (re.compile(r"flow completion|tail latency|datacenter network", re.I), "datacenter measurement"),
    (re.compile(r"heap|van Emde Boas|fusion tree|predecessor", re.I), "priority-queue data structures"),
]


def bare_term_title(title):
    """A dictionary/ontology record: a very short title with no sentence in it."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", title)
    return len(words) <= 3 and not any(c in title for c in "?:")


def main():
    with open(POOL, encoding="utf-8") as fh:
        pool = json.load(fh)
    kept = pool["kept"]

    candidates, rejected = [], []
    counts = {"other_field": {}, "no_construct": 0, "bare_term": 0}

    for r in kept:
        t = r["title"]
        if bare_term_title(t):
            r["reject_reason"] = "bare-term title (dictionary/ontology record)"
            counts["bare_term"] += 1
            rejected.append(r)
            continue
        hit = None
        for pat, label in OTHER_FIELD:
            if pat.search(t):
                hit = label
                break
        if hit:
            r["reject_reason"] = "other field: %s" % hit
            counts["other_field"][hit] = counts["other_field"].get(hit, 0) + 1
            rejected.append(r)
            continue
        cons = [label for pat, label in CONSTRUCTS if pat.search(t)]
        if not cons:
            r["reject_reason"] = "names no construct this paper uses"
            counts["no_construct"] += 1
            rejected.append(r)
            continue
        r["constructs"] = cons
        candidates.append(r)

    summary = {
        "pool_kept": len(kept),
        "candidates": len(candidates),
        "rejected_bare_term": counts["bare_term"],
        "rejected_other_field": counts["other_field"],
        "rejected_other_field_total": sum(counts["other_field"].values()),
        "rejected_no_construct": counts["no_construct"],
        "rejected_total": len(rejected),
        "rejection_rate": len(rejected) / len(kept) if kept else 0.0,
    }
    out = {"summary": summary,
           "search_form": pool["summary"],
           "candidates": sorted(candidates, key=lambda r: (-r["year"], r["title"])),
           "rejected": rejected}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("pool kept for review      : %d" % len(kept))
    print("rejected, bare-term title : %d" % counts["bare_term"])
    print("rejected, other field     : %d  %s"
          % (sum(counts["other_field"].values()), counts["other_field"]))
    print("rejected, no construct    : %d" % counts["no_construct"])
    print("CANDIDATES                : %d  (rejection rate %.3f)"
          % (len(candidates), summary["rejection_rate"]))
    print("wrote %s" % os.path.basename(OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
