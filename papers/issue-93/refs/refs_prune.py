#!/usr/bin/env python3
"""#93 R414 -- stage 1's committed evidence: the FORM and what it measured, without the raw bulk.

Inputs (regenerable from the scripts beside this one; the raw pools are ~2.6 MB and are NOT committed):
    refs_raw.json      pass 1  (refs_harvest.py  -- two windows, broad terms, date-sorted)
    refs_raw2.json     pass 2  (refs_harvest2.py -- one wide window, narrow terms, relevance-sorted)
    refs_classic.json  the classical limb (refs_classic.py -- Crossref title search, two identity rules)
Output:
    refs_form.json     the committed result of stage 1

The checkable property of this stage is that it is a FUNCTION OF FILES ON DISK: two runs produce a
byte-identical `refs_form.json`.  (The pools themselves are network-derived and drift as the index grows --
they are re-runnable from the stated form, which is why the form is what gets committed.)
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_form.json")


def load(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return json.load(fh)


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def main():
    p1, p2, cl = load("refs_raw.json"), load("refs_raw2.json"), load("refs_classic.json")

    def arxiv_counts(pool):
        return {lab: dict(query=blk["query"], window=blk["window"], n_returned=blk["n_returned"])
                for lab, blk in sorted(pool["arxiv"].items())}

    ids1 = {r["id"] for blk in p1["arxiv"].values() for r in blk["rows"]}
    ids2 = {r["id"] for blk in p2["arxiv"].values() for r in blk["rows"]}
    multi = {}
    for pool in (p1, p2):
        for lab, blk in pool["arxiv"].items():
            for r in blk["rows"]:
                multi.setdefault(r["id"], set()).add(lab)
    shared = sum(1 for v in multi.values() if len(v) > 1)

    verdicts = {}
    for t, j in sorted(cl["queries"].items()):
        verdicts[t] = dict(verdict=j["verdict"], rule=j["rule"],
                           doi=(j["matched"] or {}).get("doi"), record=(j["matched"] or {}).get("title"),
                           record_authors=((j["matched"] or {}).get("authors") or [])[:1],
                           record_year=(j["matched"] or {}).get("year"),
                           expectation=j["expectation"], main_title_tokens=j["main_title_tokens"],
                           ruleA=j["ruleA"]["verdict"], ruleB=j["ruleB"]["verdict"],
                           ruleB_refusal_reason=j["ruleB_refusal_reason"],
                           near_miss_below_main_rule=[t for t, v in sorted(j["near_miss"].items())
                                                      if v >= 0.6][:3])

    rep = dict(
        round="R414", study="issue #93 (binding fidelity sets the net value of a human approval gate)",
        scan_date=p1["scan_date"],
        form=dict(
            arxiv=dict(index="arXiv API (export.arxiv.org)", date_field="submittedDate",
                       windows=dict(W1=list(p1["form"]["arxiv"]["windows"]["W1"]),
                                    W2=list(p1["form"]["arxiv"]["windows"]["W2"]),
                                    W3=list(p2["form"]["windows"]["W3"])),
                       sorts=dict(pass1="submittedDate descending", pass2="relevance"),
                       unavailable="no filter on a paper's latest version: a work revised into relevance "
                                   "after its original posting is invisible to a window that reaches only "
                                   "the posting"),
            crossref=dict(index="Crossref REST API (api.crossref.org)",
                          field="query.bibliographic (a title search; no date window)",
                          rows_read=8,
                          date_fields_not_read=["created", "published-online", "published-print"],
                          rules=cl["rules"],
                          format_not_read="Crossref's own date field is read for the year only; a record "
                                          "without a date is reported with year null rather than dropped "
                                          "silently (stage 2 owns whether such an entry is admitted)"),
            authored_inputs=dict(
                pass1_queries=[dict(label=lab, body=blk["query"]) for lab, blk in sorted(p1["arxiv"].items())],
                pass2_queries=[dict(label=lab, body=blk["query"]) for lab, blk in sorted(p2["arxiv"].items())],
                classic_titles=sorted(cl["queries"].keys()),
                expectations=cl.get("expectations", {})),
        ),
        measured=dict(
            pass1=dict(queries=len(p1["arxiv"]), rows=sum(b["n_returned"] for b in p1["arxiv"].values()),
                       unique_ids=len(ids1), per_query=arxiv_counts(p1)),
            pass2=dict(queries=len(p2["arxiv"]), rows=sum(b["n_returned"] for b in p2["arxiv"].values()),
                       unique_ids=len(ids2), per_query=arxiv_counts(p2)),
            arxiv_union=len(ids1 | ids2),
            arxiv_ids_returned_by_more_than_one_query=shared,
            classic=dict(queries=cl["n_queries"], matched=cl["n_matched"], ruleA=cl["n_ruleA"],
                         ruleB=cl["n_ruleB"], ruleB_refused=cl["n_ruleB_refused"],
                         unique_dois=cl["n_unique_dois"], collisions=cl["collisions"]),
            controls=cl["controls"],
            verdicts=verdicts,
            errors=dict(pass1=p1["errors"], pass2=p2["errors"], classic=cl["errors"]),
        ),
        limitations=[
            "The classical limb's NOT FOUND means NOT FOUND WITHIN 8 CANDIDATE ROWS: the title query is a "
            "recall-limited instrument, and 9 of the 64 queries returned no row whose main title reached the "
            "identity rule although the work is citable. A work that cannot be identified is not cited.",
            "The arXiv window is the submission date; a paper's later versions are not reachable by any "
            "window arXiv exposes.",
            "Rule B is admitted only where the query declares a metadata expectation; a registry record "
            "whose author field is '&NA;' cannot satisfy any expectation and is refused (two such refusals "
            "are recorded above).",
        ],
        pool_hashes=dict(refs_raw_json=sha(os.path.join(HERE, "refs_raw.json")),
                         refs_raw2_json=sha(os.path.join(HERE, "refs_raw2.json")),
                         refs_classic_json=sha(os.path.join(HERE, "refs_classic.json")),
                         refs_classic_r1_json=sha(os.path.join(HERE, "refs_classic_r1.json"))),
    )
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    m = rep["measured"]
    print("pass1 %d queries / %d rows / %d ids" % (m["pass1"]["queries"], m["pass1"]["rows"], m["pass1"]["unique_ids"]))
    print("pass2 %d queries / %d rows / %d ids" % (m["pass2"]["queries"], m["pass2"]["rows"], m["pass2"]["unique_ids"]))
    print("arxiv union %d (shared by >1 query: %d)" % (m["arxiv_union"], m["arxiv_ids_returned_by_more_than_one_query"]))
    print("classic %d/%d matched (A %d, B %d, B refused %d) | unique DOIs %d | collisions %d"
          % (m["classic"]["matched"], m["classic"]["queries"], m["classic"]["ruleA"], m["classic"]["ruleB"],
             m["classic"]["ruleB_refused"], m["classic"]["unique_dois"], len(m["classic"]["collisions"])))
    print("controls %d/%d" % (sum(1 for c in cl["controls"].values() if c["ok"]), len(cl["controls"])))
    print("wrote %s (sha %s)" % (os.path.basename(OUT), sha(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
