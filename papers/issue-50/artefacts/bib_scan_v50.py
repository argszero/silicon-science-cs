
#!/usr/bin/env python3
"""bib_scan_v50 -- the candidate pool for issue #50's bibliography.

Every query is derived from a CLAIM THIS PAPER MAKES (speculative tool
execution, contention-indexed boundaries, latency hiding under a shared
worker pool, tail latency, side effects and idempotency, parallel speedup,
and the evaluation methodology for speedup claims).  No query names any
project, system, or tool of the author's.

Two channels, each with its own date field, and both recorded:
  * arXiv API   -- sortBy=submittedDate, field submittedDate
  * Crossref    -- query.bibliographic, no date filter (a bibliography is not
                   a recency sample; the window is recorded for the record only)
The scan's own UTC timestamps are part of the evidence.
"""
import io, json, os, time, urllib.parse, urllib.request, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "silicon-science-cs/issue-50 bib scan (mailto:author@example.invalid)"

ARXIV_Q = [
 'all:"speculative execution" AND all:tools',
 'all:"speculative tool"',
 'all:"tool call" AND all:speculation',
 'all:prefetch AND all:agent AND all:execution',
 'all:"speculative decoding"',
 'all:"branch prediction" AND all:misprediction',
 'all:"memory prefetching"',
 'all:"thread-level speculation"',
 'all:"software speculation"',
 'all:"latency hiding"',
 'all:"M/M/c"',
 'all:"queueing theory" AND all:approximation',
 'all:"tail latency"',
 'all:"heavy-tailed" AND all:latency',
 'all:"parallel speedup"',
 'all:"Amdahl"',
 'all:"fork-join"',
 'all:"worker pool"',
 'all:"performance evaluation" AND all:speedup',
 'all:"learned index" AND all:prediction AND all:systems',
 'all:"online algorithms with predictions"',
 'all:"ski rental"',
 'all:"side channel" AND all:speculation',
 'all:"transactional memory"',
 'all:"idempotency" AND all:retry',
 'all:"workload characterization" AND all:datacenter',
 'all:agents AND all:"tool use" AND all:benchmark',
 'all:LLM AND all:agent AND all:scheduling',
]

CROSSREF_Q = [
 "speculative execution performance",
 "speculative tool execution",
 "latency hiding parallel execution",
 "queueing approximation M/M/c response time",
 "tail latency large scale systems",
 "heavy tailed distribution queueing",
 "thread level speculation",
 "software prefetching performance",
 "online algorithms with predictions paging",
 "ski rental problem learning augmented",
 "Amdahl law parallel speedup",
 "fork join scheduling analysis",
 "performance evaluation methodology speedup",
 "idempotency retry distributed systems",
 "caching prefetching prediction",
 "workload characterization server utilization",
]

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                return None
            time.sleep(2 + 2 * i)
    return None

def arxiv(query, n=40):
    q = urllib.parse.quote('all:"%s"' % query)
    url = ("https://export.arxiv.org/api/query?search_query=%s"
           "&start=0&max_results=%d&sortBy=submittedDate&sortOrder=descending" % (q, n))
    txt = get(url)
    if txt is None:
        return "FETCH_FAILED", []
    if "<entry" not in txt:
        return "EMPTY_BODY", []
    out = []
    for m in re.finditer(r"<entry>(.*?)</entry>", txt, re.S):
        e = m.group(1)
        def one(tag):
            mm = re.search(r"<%s>(.*?)</%s>" % (tag, tag), e, re.S)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""
        idm = re.search(r"<id>(.*?)</id>", e, re.S)
        aid = idm.group(1).rstrip("/").split("/abs/")[-1] if idm else ""
        out.append({
            "source": "arxiv", "id": aid,
            "title": one("title"),
            "abstract": one("summary")[:600],
            "published": one("published"),
            "updated": one("updated"),
            "authors": re.findall(r"<name>(.*?)</name>", e),
            "query": query,
        })
    return "OK", out

def crossref(query, n=30):
    q = urllib.parse.quote(query)
    url = ("https://api.crossref.org/works?query.bibliographic=%s&rows=%d"
           "&select=DOI,title,author,issued,container-title,type,created" % (q, n))
    txt = get(url)
    if txt is None:
        return "FETCH_FAILED", []
    try:
        d = json.loads(txt)
    except Exception:
        return "UNPARSEABLE", []
    out = []
    for it in d.get("message", {}).get("items", []):
        t = (it.get("title") or [""])[0]
        yr = None
        try:
            yr = it["issued"]["date-parts"][0][0]
        except Exception:
            yr = None
        au = []
        for a in it.get("author", []) or []:
            nm = " ".join(x for x in [a.get("given"), a.get("family")] if x)
            if nm:
                au.append(nm)
        out.append({
            "source": "crossref", "id": it.get("DOI", ""),
            "title": t, "year": yr,
            "venue": (it.get("container-title") or [""])[0],
            "type": it.get("type", ""),
            "authors": au, "query": query,
        })
    return "OK", out

def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()

CONTROL_ARXIV = 'all:"tail latency"'
CONTROL_CROSSREF = "speculative execution performance"

def control():
    """R349: a search that cannot be shown to return something cannot support
    any absence claim.  Two known-non-empty queries, one per channel."""
    st_a, ra = arxiv(CONTROL_ARXIV, n=5)
    st_c, rc = crossref(CONTROL_CROSSREF, n=5)
    ok = (st_a == "OK" and len(ra) > 0) and (st_c == "OK" and len(rc) > 0)
    print("CONTROL arxiv=%-12s n=%d | crossref=%-12s n=%d -> %s"
          % (st_a, len(ra), st_c, len(rc), "PASS" if ok else "FAIL"))
    return {"arxiv": {"query": CONTROL_ARXIV, "status": st_a, "n": len(ra)},
            "crossref": {"query": CONTROL_CROSSREF, "status": st_c, "n": len(rc)},
            "ok": ok}

def main():
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ctl = control()
    recs, report = [], []
    for q in ARXIV_Q:
        st, rows = arxiv(q)
        report.append({"channel": "arxiv", "query": q, "status": st, "n": len(rows)})
        recs.extend(rows)
        print("arxiv  %-55s %-14s %d" % (q[:55], st, len(rows)), flush=True)
        time.sleep(3.0)
    for q in CROSSREF_Q:
        st, rows = crossref(q)
        report.append({"channel": "crossref", "query": q, "status": st, "n": len(rows)})
        recs.extend(rows)
        print("xref   %-55s %-14s %d" % (q[:55], st, len(rows)), flush=True)
        time.sleep(0.5)
    ended = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # dedup on normalized title, keeping the first (order = query order)
    seen, dedup = {}, []
    for r in recs:
        k = norm(r["title"])
        if not k:
            continue
        if k in seen:
            seen[k]["seen_in"].append(r["query"])
            continue
        r = dict(r); r["seen_in"] = [r["query"]]
        seen[k] = r; dedup.append(r)
    out = {
        "what": "issue #50 bibliography candidate pool",
        "started_utc": started, "ended_utc": ended,
        "arxiv_queries": ARXIV_Q, "crossref_queries": CROSSREF_Q,
        "control": ctl,
        "per_query": report,
        "n_records": len(recs), "n_dedup": len(dedup),
        "records": dedup,
    }
    with io.open(os.path.join(HERE, "bib_scan_v50.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    bad = [r for r in report if r["status"] != "OK"]
    print("\nrecords %d -> dedup %d ; channels not OK: %d" % (len(recs), len(dedup), len(bad)))
    print("window %s -> %s" % (started, ended))
    if bad:
        for b in bad:
            print("  NOT OK:", b)
    return 0

if __name__ == "__main__":
    sys.exit(main())
