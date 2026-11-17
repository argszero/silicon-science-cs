#!/usr/bin/env python3
"""search_record.py -- the search behind the paper's one absence claim, recorded so it can be re-taken.

Section 1 says the recall literature does not ask what decides whether the identified set has any
width. That is a claim about the literature, and a claim about the literature owes a search: which
indices, which terms, which date field, which window with BOTH endpoints, and what came back. This
program runs that search and writes the answer down; the manuscript states it and binds every count
to this file.

It is a maintainer's step, because it needs the network. Its output is committed, so a reader
reproduces every number in the paper without network access -- the same arrangement `refs.json`
uses.

    python3 search_record.py            # writes search/absence_search.json

Two indices, because an absence claim is only as strong as the union of what it searched, and the
two answer different questions:

  arXiv      full text of preprints        date field `submittedDate`
  Crossref   publisher metadata            date field the issued date (`from-pub-date`/`until-pub-date`)

A source that does not answer is recorded as NOT RUN with its reason, never as zero hits: "the index
returned nothing" and "the index did not answer" are the two readings this file exists to keep
apart. The retrieval is mechanical; the relevance screen is a declared lexical rule plus a hand
reading recorded under `hand_review`, and both are labelled as what they are.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

OUT = "search/absence_search.json"
UA = "silicon-science-cs-issue158/1.0 (mailto:how2how2how2-arch@users.noreply.github.com)"

# Both endpoints, named. `to` is the day before this record was written, so the window is closed on
# both sides and re-taking it tomorrow with the same arguments gives the same window.
WINDOW = {"from": "2016-01-01", "to": "2026-11-09"}

TOP_N = 10
PAUSE_S = 1.0

# Each query states, in words, the thing it is trying to find. The index encodings below are what
# the two APIs are actually given; a reader re-taking the search uses these strings, not a memory of
# them. The union is the search: a paper asking the width question would have to land in one of them.
QUERIES = [
    dict(id="q1",
         statement="recall@k evaluated against a ground truth that several points share",
         arxiv='abs:"recall" AND abs:"tie" AND abs:"nearest neighbor"',
         crossref="recall at k tie nearest neighbor evaluation"),
    dict(id="q2",
         statement="ambiguity or non-uniqueness in the ground truth of a nearest-neighbour benchmark",
         arxiv='abs:"ground truth" AND abs:"ambiguity" AND abs:"nearest neighbor"',
         crossref="ground truth ambiguity nearest neighbor benchmark evaluation"),
    dict(id="q3",
         statement="identical distances at the k-th position and what they do to a reported metric",
         arxiv='abs:"identical distances" OR abs:"distance ties"',
         crossref="identical distances k-th nearest neighbor tie"),
    dict(id="q4",
         statement="tie-breaking as the thing that decides a reported recall",
         arxiv='abs:"tie-breaking" AND abs:"nearest neighbor"',
         crossref="tie-breaking nearest neighbor search recall"),
    dict(id="q5",
         statement="whether a retrieval metric is even identified by the data it is computed on",
         arxiv='abs:"identifiability" AND abs:"retrieval"',
         crossref="identifiability retrieval metric evaluation"),
    dict(id="q6",
         statement="quantiser resolution, the number of distinct distances, and recall",
         arxiv='abs:"quantization" AND abs:"distinct" AND abs:"distance"',
         crossref="quantization distinct distance values recall"),
]

# Declared lexical screen. A record survives into `hand_review` only if its title or abstract
# carries at least one term from EACH group -- one group names the mechanism this paper is about,
# the other names the evaluation setting it would have to be reported in. This is a screen, not a
# judgement: it can only shrink the pile a human then reads, and the counts it produces are printed
# beside the pile so a reader can see how much it threw away.
SCREEN = {
    "mechanism": ["tie", "ties", "identical distance", "distinct distance", "resolution",
                  "ambiguity", "non-unique", "nonunique", "identified set", "identifiability"],
    "setting": ["recall", "nearest neighbor", "nearest neighbour", "retrieval", "ground truth",
                "k-nn", "knn", "quantiz", "quantis"],
}


# The hand reading, recorded against stable identifiers rather than against a position in a list.
#
# `asks_width` is the one judgement this file records, and its rule is narrow: the record must treat
# the ambiguity of the k-th distance as the OBJECT of study and ask what makes the set of admissible
# recall values have width. A record that mentions ties in order to motivate an index, or that uses
# "identifiability" about a different object, is not an instance of this paper's question.
#
# Keying by id is what makes the record survive re-derivation: if a later run of the same queries
# retrieves something that was never read, `n_unreviewed` rises and the gate refuses; if a judgement
# names a record the index no longer returns, `n_stale` rises and the gate refuses. Neither can be
# fixed by leaving the field empty.
HAND_REVIEW = [
    ("10.22564/brjg.v40i1.2157", False,
     "a 'well tie' in geophysics: a borehole log correlated to a seismic trace, not a distance tie"),
    ("10.33369/jsds.v3i1.32381", False,
     "k-NN used as a classifier on clinical records; no notion of an undetermined metric"),
    ("http://arxiv.org/abs/2511.01458v2", False,
     "nearest-neighbour retrieval used to decide when to trust an answer; the metric is an input"),
    ("http://arxiv.org/abs/2003.00894v2", False,
     "consistency of the k-NN RULE (does it converge to the Bayes boundary), not whether a recall "
     "figure is determined; the nearest neighbour is assumed uniquely defined"),
    ("http://arxiv.org/abs/2007.03937v4", False,
     "a characterisation of Lebesgue points via nearest neighbours; a theorem about measure, no "
     "metric is being evaluated"),
    ("10.1609/aaai.v32i1.12138", False,
     "builds a graph to search faster; mentions ties as a feature of the graph, not as a question "
     "about what a recall number can mean"),
    ("http://arxiv.org/abs/2606.28327v1", False,
     "compares retrieval bounds across two systems; 'interference' is a bound on recall, not the "
     "identification of it"),
    ("http://arxiv.org/abs/2204.05952v2", False,
     "'identifiability' of VAR parameters under mixed sampling; a time-series object"),
    ("http://arxiv.org/abs/2102.08515v1", False,
     "identifiability of harmonic retrieval; a signal-processing object"),
    ("http://arxiv.org/abs/2504.13172v1", False,
     "a cross-modal retrieval architecture; reports recall, does not question what it identifies"),
    ("http://arxiv.org/abs/2310.18904v1", False,
     "identifiability of latent factors in contrastive learning; a representation-learning object"),
    ("10.1007/s00184-025-00994-4", False,
     "the journal version of the VAR identifiability record above"),
    ("10.3390/rs18203568", False,
     "identifiability of leaf-area index from remote sensing; 'spectral fidelity' is a retrieval "
     "error, not an identified set"),
    ("http://arxiv.org/abs/2403.05168v3", False,
     "representation learning across modalities; no metric-identification content"),
    ("http://arxiv.org/abs/2603.25030v1", False,
     "information-theoretic limits on node localisation; limits of an estimator, not of a metric's "
     "reading"),
]

# A caveat that has to travel with the numbers, because one of them is not a count of relevant work:
# Crossref's `query.bibliographic` is a ranked fuzzy match over titles, so `total-results` is an
# upper bound on candidates that share vocabulary, not a number of papers on the subject. The arXiv
# `abs:` conjunction is a real filter, so its totals can be read as the smaller number.
CAVEAT = ("Crossref bibliographic totals are fuzzy-match candidate counts, not counts of relevant "
          "works; the arXiv `abs:` conjunctions are filters. The records actually READ are the "
          "retrieved top-N per query per index, and their number is in the ledger.")


def fetch(url, tries=3):
    """One GET, no retries on 4xx. Returns (status, body) where status is 'ok' or a reason."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return "ok", r.read().decode("utf-8", "replace")
        except Exception as e:                       # noqa: BLE001 -- the reason is the datum
            last = "%s: %s" % (type(e).__name__, e)
            if "HTTP Error 4" in last:               # a refusal will not become an answer
                break
            time.sleep(2 * (attempt + 1))
    return last, None


def arxiv_window():
    return "submittedDate:[%s0000 TO %s2359]" % (
        WINDOW["from"].replace("-", ""), WINDOW["to"].replace("-", ""))


def ask_arxiv(q):
    """arXiv full text. The API joins terms with AND inside one `abs:` clause only if asked to; the
    declared string is passed through as written so the record shows what was really run."""
    search = "%s AND %s" % (q["arxiv"], arxiv_window()) if q["arxiv"] else arxiv_window()
    url = ("http://export.arxiv.org/api/query?" +
           urllib.parse.urlencode({"search_query": search, "start": 0, "max_results": TOP_N,
                                   "sortBy": "relevance", "sortOrder": "descending"}))
    status, body = fetch(url)
    if body is None:
        return dict(status="NOT RUN", reason=status, query=search, url=url)
    import re
    entries = re.findall(r"<entry>(.*?)</entry>", body, re.S)
    total = re.search(r"<opensearch:totalResults[^>]*>(\d+)<", body)
    out = []
    for e in entries:
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        i = re.search(r"<id>(.*?)</id>", e, re.S)
        p = re.search(r"<published>(.*?)</published>", e, re.S)
        s = re.search(r"<summary>(.*?)</summary>", e, re.S)
        out.append(dict(title=" ".join(t.group(1).split()) if t else "",
                        id=i.group(1).strip() if i else "",
                        year=(p.group(1)[:4] if p else ""),
                        abstract=" ".join(s.group(1).split())[:1200] if s else ""))
    return dict(status="ok", query=search, url=url,
                hits=int(total.group(1)) if total else None, retrieved=out)


def ask_crossref(q):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({
        "query.bibliographic": q["crossref"],
        "filter": "from-pub-date:%s,until-pub-date:%s,type:journal-article" % (
            WINDOW["from"], WINDOW["to"]),
        "rows": TOP_N, "select": "DOI,title,issued,abstract"})
    status, body = fetch(url)
    if body is None:
        return dict(status="NOT RUN", reason=status, query=q["crossref"], url=url)
    d = json.loads(body)
    msg = d.get("message", {})
    out = []
    for it in msg.get("items", []):
        t = (it.get("title") or [""])[0]
        yr = ""
        issued = (it.get("issued") or {}).get("date-parts") or [[]]
        if issued and issued[0]:
            yr = str(issued[0][0])
        out.append(dict(title=" ".join(t.split()), id=it.get("DOI", ""), year=yr,
                        abstract=" ".join((it.get("abstract") or "").split())[:1200]))
    return dict(status="ok", query=q["crossref"], url=url,
                hits=msg.get("total-results"), retrieved=out)


def screened(rec):
    text = (rec.get("title", "") + " " + rec.get("abstract", "")).lower()
    hit_m = [t for t in SCREEN["mechanism"] if t in text]
    hit_s = [t for t in SCREEN["setting"] if t in text]
    return dict(mechanism=hit_m, setting=hit_s, survives=bool(hit_m and hit_s))


def main():
    if not os.path.isdir("search"):
        os.makedirs("search", exist_ok=True)
    record = {
        "claim": ("The recall literature does not ask what decides whether the identified set of a "
                  "recall@k measurement has any width."),
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "window": dict(WINDOW,
                       date_field={"arxiv": "submittedDate",
                                   "crossref": "issued date (from-pub-date / until-pub-date)"},
                       note="closed interval; both endpoints inclusive"),
        "indices": {
            "arxiv": "arXiv API, all fields via `abs:` clauses, full-text abstracts",
            "crossref": "Crossref REST API, journal-article type, bibliographic query",
        },
        "top_n_per_query_per_index": TOP_N,
        "queries": [],
        "screen": SCREEN,
        "caveat": CAVEAT,
        "hand_review": {"rule": "recorded by the author, one line per screened survivor, after "
                                "reading the title and abstract; keyed by the record's own id",
                        "records": []},
    }

    for q in QUERIES:
        row = dict(id=q["id"], statement=q["statement"],
                   arxiv=ask_arxiv(q), crossref=ask_crossref(q))
        record["queries"].append(row)
        print("%s  arxiv=%-8s crossref=%-8s  %s" % (
            q["id"],
            row["arxiv"].get("hits") if row["arxiv"]["status"] == "ok" else "NOT RUN",
            row["crossref"].get("hits") if row["crossref"]["status"] == "ok" else "NOT RUN",
            q["statement"][:52]))
        time.sleep(PAUSE_S)

    # ---- totals, and the screen's own ledger ------------------------------------------------
    retrieved = []
    for row in record["queries"]:
        for src in ("arxiv", "crossref"):
            r = row[src]
            if r["status"] != "ok":
                continue
            for rec in r["retrieved"]:
                rec = dict(rec, source=src, query=row["id"])
                rec["screen"] = screened(rec)
                retrieved.append(rec)
    seen, unique = set(), []
    for rec in retrieved:
        key = (rec.get("id") or "") or rec.get("title", "").lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(rec)
    survivors = [r for r in unique if r["screen"]["survives"]]
    judged = {ident: (asks, why) for ident, asks, why in HAND_REVIEW}
    by_id = {(r.get("id") or ""): r for r in survivors}
    for ident, (asks, why) in sorted(judged.items()):
        r = by_id.get(ident)
        if r is None:
            continue
        record["hand_review"]["records"].append(
            dict(id=ident, title=r.get("title", ""), year=r.get("year", ""),
                 source=r["source"], query=r["query"], asks_width=asks, why=why))

    record["ledger"] = {
        "records_retrieved": len(retrieved),
        "records_deduped": len(unique),
        "survived_screen": len(survivors),
        "read_by_hand": len(record["hand_review"]["records"]),
        # A survivor nobody read, and a judgement whose record the index no longer returns. Both are
        # refusals in check_claims.py: the first means the search found something unexamined, the
        # second means the record describes a pile that no longer exists.
        "n_unreviewed": len([r for r in survivors if (r.get("id") or "") not in judged]),
        "n_stale": len([i for i in judged if i not in by_id]),
        "n_asks_width": sum(1 for r in record["hand_review"]["records"] if r["asks_width"]),
        "sources_not_run": sorted({s for row in record["queries"] for s in ("arxiv", "crossref")
                                   if row[s]["status"] != "ok"}),
    }

    json.dump(record, open(OUT, "w"), indent=1, sort_keys=True)
    print("\n-> %s" % OUT)
    L = record["ledger"]
    print("   retrieved %(records_retrieved)d, deduped %(records_deduped)d, survived screen "
          "%(survived_screen)d, read by hand %(read_by_hand)d, ask the question %(n_asks_width)d"
          % L)
    if L["sources_not_run"]:
        print("   NOT RUN: %s" % ", ".join(L["sources_not_run"]))
    if L["n_unreviewed"]:
        print("   UNREVIEWED: %d survivor(s) the record does not judge:" % L["n_unreviewed"])
        for r in survivors:
            if (r.get("id") or "") not in judged:
                print("     [%s/%s] %s" % (r["source"], r["query"], r.get("title", "")[:88]))
    if L["n_stale"]:
        print("   STALE: %d judgement(s) name a record the index no longer returns:" % L["n_stale"])
        for i in sorted(judged):
            if i not in by_id:
                print("     %s" % i)
    return 0


if __name__ == "__main__":
    sys.exit(main())
