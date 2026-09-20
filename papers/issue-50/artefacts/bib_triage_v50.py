#!/usr/bin/env python3
"""Merge the CONTROLLED channels into one pool and triage it into clusters.

Channel discipline (R349): a channel enters the pool only from a pass whose
POSITIVE CONTROL passed.  Pass 1's Crossref control passed; pass 1's arXiv
control FAILED, so pass 1's arXiv rows are DROPPED and pass 2's (control PASS)
supply the arXiv rows.  Mixing them would let an uncontrolled partial sample
sit inside a controlled one.
"""
import io, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SHORT = re.compile(r"\b(editorial|erratum|corrigendum|retraction|front matter|back matter|"
                   r"table of contents|index of|author index|proceedings of|abstracts of)\b", re.I)

OFFTOPIC_TERMS = [   # word-boundary matched, never substrings (R339: "gene" hit "general")
 "cancer", "gene", "protein", "cell", "patient", "clinical", "medical", "covid", "virus",
 "soil", "crop", "materials", "catalys", "polymer", "neural network training accuracy for image",
 "speech recognition", "recommendation", "sentiment", "water", "energy grid", "wireless channel",
]

def norm(t): return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()

def load(fn):
    return json.load(io.open(os.path.join(HERE, fn), encoding="utf-8"))

def year_of(r):
    if r["source"] == "crossref":
        return r.get("year")
    p = r.get("published", "")
    return int(p[:4]) if p[:4].isdigit() else None

def authors_line(r):
    a = r.get("authors") or []
    if not a: return ""
    fam = a[0].split()[-1] if a[0].split() else ""
    return fam + (" et al." if len(a) > 1 else "")

def offtopic(title):
    t = " " + norm(title) + " "
    for term in OFFTOPIC_TERMS:
        if " " + term + " " in t:
            return True
    return False

CLUSTERS = [
 ("agent-speculation", r"speculat|predictive execution|pre-execut|tool call|tool-call|agent.*tool|tool.*agent"),
 ("hardware-speculation", r"branch predict|mispredict|speculative execution|memory prefetch|prefetch|store buffer|out-of-order|thread.level spec|software spec"),
 ("queueing-theory", r"queue|m/m/|waiting time|sojourn|pollaczek|little.s law|response time|service time|priority"),
 ("tail-latency", r"tail latency|heavy.tail|percentile|straggler|tail at scale"),
 ("parallel-speedup", r"speedup|amdahl|fork.join|parallelism|multicore|scalab|worker pool|thread pool|utilization"),
 ("side-effects", r"idempot|retry|exactly.once|transactional|side effect|compensat|saga|crash consisten"),
 ("online-predictions", r"prediction|learned|ski rental|rent.or.buy|advice|competitive|online algorithm|paging|caching"),
 ("methodology", r"benchmark|methodolog|reproducib|measurement|evaluation|experiment design|workload characteri|statistical"),
 ("security-speculation", r"side channel|spectre|meltdown|transient execution|microarchitectural leak"),
]

def main():
    p1 = load("bib_scan_v50.json")
    p2 = load("arxiv_pass2_v50.json")
    if not (p1["control"]["crossref"]["n"] > 0):
        print("pass 1 crossref control FAILED -- pool void"); return 2
    if not (p2["meta"]["control"]["n"] > 0 and p2["meta"]["channel"] == "OK"):
        print("pass 2 arxiv control FAILED -- pool void"); return 2
    kept = [r for r in p1["records"] if r["source"] == "crossref"]
    dropped_p1_arxiv = [r for r in p1["records"] if r["source"] == "arxiv"]
    kept += p2["records"]
    seen, pool = {}, []
    for r in kept:
        k = norm(r["title"])
        if not k or SHORT.search(r["title"]) or offtopic(r["title"]):
            continue
        if k in seen:
            continue
        seen[k] = r
        pool.append(r)
    print("pool %d (crossref %d + arxiv %d) ; dropped pass-1 arxiv rows %d"
          % (len(pool), sum(1 for r in pool if r["source"] == "crossref"),
             sum(1 for r in pool if r["source"] == "arxiv"), len(dropped_p1_arxiv)))
    print("year span:", min(y for y in (year_of(r) for r in pool) if y), "-", max(y for y in (year_of(r) for r in pool) if y))
    assigned, lines = set(), []
    for name, pat in CLUSTERS:
        rx = re.compile(pat, re.I)
        members = [r for r in pool if rx.search(r["title"])]
        for r in members:
            if id(r) not in assigned:
                assigned.add(id(r)); r["cluster"] = name
        lines.append((name, members))
    rest = [r for r in pool if id(r) not in assigned]
    for r in rest: r["cluster"] = "other"
    lines.append(("other", rest))
    with io.open(os.path.join(HERE, "bib_pool_v50.json"), "w", encoding="utf-8") as f:
        json.dump({"n": len(pool), "channels": {"crossref": "pass 1 (control PASS)",
                   "arxiv": "pass 2 (control PASS)", "pass1_arxiv": "DROPPED (control FAILED)"},
                   "records": pool}, f, ensure_ascii=False, indent=1)
    print()
    for name, members in lines:
        print("### %-22s n=%d" % (name, len(members)))
    print("\ncluster sizes:", json.dumps(Counter(r["cluster"] for r in pool).most_common()))
    return 0

if __name__ == "__main__":
    sys.exit(main())
