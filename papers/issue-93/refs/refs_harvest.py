#!/usr/bin/env python3
"""#93 R414 -- pass 1 of the reference-corpus harvest, with the search FORM stated as data.

The journal's bar makes the *search* a carrier of the claim (quality-bar items 12-13: >= 100 references,
each verified against a real record, each genuinely cited).  The recipe is the one this journal's #87
already committed (`papers/issue-87/artefacts/refs/`), re-run for #93's construct: a human approval gate
whose value depends on whether the reviewed object denotes the executed one.

INDICES
  * arXiv API (export.arxiv.org), date field = `submittedDate`.  arXiv exposes ONE date filter; it has
    NO filter on a paper's latest version, so a work revised into relevance after its original posting is
    invisible to a window that reaches only the posting -- recorded as an unavailable coordinate, not
    silently ignored.
  * Crossref REST API (api.crossref.org), used by TITLE (see `refs_classic.py`) for named works.  The DOI
    limb is deliberately NOT used here: #87 measured that a DOI recalled from memory is a claim the
    registry refutes (8 of 40 returned no record; several resolved to a different work).

WINDOWS (both endpoints written; a window is a coordinate, not a word)
  W1 "hot"      submittedDate [2026-01-01, 2026-09-22]  -- the current-season literature
  W2 "classic"  submittedDate [2018-01-01, 2025-12-31]  -- the field preceding the hot window

SCAN DATE     2026-09-22

OUTPUT  refs_raw.json -- every harvested record with the fields the house entry style needs
        (authors, year, title, venue/identifier, resolvable URL) plus the query that returned it.
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_raw.json")
SCAN_DATE = "2026-09-22"

ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"

W1 = ("202601010000", "202609222359")
W2 = ("201801010000", "202512312359")

# (query label, arXiv search_query body, window, max_results)
ARX_QUERIES = [
    # ---- the construct itself: gates, approval, oversight (hot window) ----
    ("arx-W1-hitl-agent", 'all:"human-in-the-loop" AND all:"agent"', W1, 40),
    ("arx-W1-approval", 'all:"human approval"', W1, 40),
    ("arx-W1-approvalfatigue", 'all:"approval fatigue"', W1, 25),
    ("arx-W1-oversight", 'all:"human oversight" AND cat:cs.AI', W1, 40),
    ("arx-W1-escalation", 'all:"escalation" AND all:"agent"', W1, 40),
    ("arx-W1-aicontrol", 'all:"AI control"', W1, 30),
    ("arx-W1-scalable", 'all:"scalable oversight"', W1, 25),
    ("arx-W1-defer", 'all:"when to defer" OR all:"learning to defer"', W1, 30),
    ("arx-W1-abstention", 'all:"abstention" AND all:"LLM"', W1, 25),
    # ---- the channel: does the reviewed object denote the executed one ----
    ("arx-W1-binding", 'all:"binding" AND all:"tool call"', W1, 25),
    ("arx-W1-substitution", 'all:"tool call" AND all:"mismatch"', W1, 25),
    ("arx-W1-provenance", 'all:"provenance" AND all:"agent" AND all:"tool"', W1, 30),
    ("arx-W1-oob", 'all:"out-of-band" AND all:"verification"', W1, 25),
    ("arx-W1-toctou", 'all:"time-of-check" OR all:"TOCTOU"', W1, 25),
    ("arx-W1-rendering", 'all:"rendering" AND all:"approval"', W1, 20),
    # ---- the mechanism: what a defective channel launders ----
    ("arx-W1-hijack", 'all:"approval" AND all:"hijack"', W1, 25),
    ("arx-W1-injection", 'all:"prompt injection" AND all:"agent"', W1, 40),
    ("arx-W1-authz", 'all:"authorization" AND all:"agent"', W1, 40),
    ("arx-W1-leastpriv", 'all:"least privilege"', W1, 30),
    ("arx-W1-confused", 'all:"confused deputy" OR all:"capability-based"', W1, 25),
    # ---- the human's own limits (hot + classic) ----
    ("arx-W1-automationbias", 'all:"automation bias"', W1, 25),
    ("arx-W1-alarmfatigue", 'all:"alarm fatigue" OR all:"alert fatigue"', W1, 30),
    ("arx-W1-fatigue", 'all:"reviewer fatigue" OR all:"rubber stamp"', W1, 20),
    ("arx-W2-hitl", 'all:"human-in-the-loop"', W2, 40),
    ("arx-W2-imitl", 'all:"interactive machine learning"', W2, 30),
    ("arx-W2-humancomp", 'all:"human computation"', W2, 30),
    ("arx-W2-defer", 'all:"learning to defer" OR all:"learning to reject"', W2, 30),
    ("arx-W2-reject", 'all:"reject option"', W2, 25),
    ("arx-W2-selectclass", 'all:"selective classification"', W2, 25),
    ("arx-W2-monitorlaw", 'all:"monitor" AND all:"detection" AND all:"entropy"', W2, 25),
    ("arx-W2-guardrail", 'all:"guardrail" AND all:"LLM"', W2, 25),
    ("arx-W2-aviation", 'all:"human" AND all:"automation" AND all:"complacency"', W2, 25),
    ("arx-W2-partial", 'all:"mixed-initiative" OR all:"mixed initiative"', W2, 25),
    ("arx-W2-adversarial", 'all:"adversarial" AND all:"agent" AND all:"tool"', W2, 30),
    ("arx-W2-sandbox", 'all:"sandbox" AND all:"untrusted"', W2, 25),
]


def fetch(url, tries=3, timeout=50):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/refharvest93"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:      # noqa: BLE001 -- network flake: retry, then record
            last = e
            time.sleep(2 + 3 * k)
    raise RuntimeError("fetch failed after %d tries: %s (%s)" % (tries, url, last))


def arxiv_query(qbody, window, n):
    q = qbody + " AND submittedDate:[%s TO %s]" % window
    url = ("https://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q)
           + "&start=0&max_results=%d&sortBy=submittedDate&sortOrder=descending" % n)
    xml = fetch(url)
    root = ET.fromstring(xml)
    out = []
    for e in root.findall(ATOM + "entry"):
        eid = (e.findtext(ATOM + "id") or "").strip()
        aid = eid.rsplit("/abs/", 1)[-1]
        base = aid.split("v")[0]
        pub = (e.findtext(ATOM + "published") or "").strip()
        authors = [(a.findtext(ATOM + "name") or "").strip() for a in e.findall(ATOM + "author")]
        prim = e.find(ARX + "primary_category")
        out.append(dict(
            source="arxiv", id=base, version=aid, url="https://arxiv.org/abs/" + base,
            title=" ".join((e.findtext(ATOM + "title") or "").split()),
            authors=authors, year=int(pub[:4]) if pub[:4].isdigit() else None,
            published=pub, primary=prim.get("term") if prim is not None else "",
            summary=" ".join((e.findtext(ATOM + "summary") or "").split())[:500],
        ))
    return out


def main():
    rep = dict(scan_date=SCAN_DATE,
               form=dict(
                   arxiv=dict(index="arXiv API (export.arxiv.org)", date_field="submittedDate",
                              windows={"W1": list(W1), "W2": list(W2)},
                              sort="submittedDate descending",
                              unavailable="no filter on the latest version: a work revised into "
                                          "relevance after its original posting is invisible to a "
                                          "window that reaches only the posting"),
                   crossref=dict(index="Crossref REST API (api.crossref.org)",
                                 field="query.bibliographic (a title search; no window)",
                                 date_field_not_read=["created", "published-online", "published-print"]),
                   queries=[q[0] for q in ARX_QUERIES],
                   scan_date=SCAN_DATE),
               arxiv={}, errors=[])
    for label, qbody, window, n in ARX_QUERIES:
        try:
            rows = arxiv_query(qbody, window, n)
            for r in rows:
                r["query"] = label
                r["query_body"] = qbody
            rep["arxiv"][label] = dict(query=qbody, window=list(window), n_returned=len(rows), rows=rows)
            print("%-24s %-3d rows" % (label, len(rows)), flush=True)
        except Exception as e:      # noqa: BLE001
            rep["errors"].append((label, repr(e)))
            print("%-24s ERROR %r" % (label, e), flush=True)
        time.sleep(3.2)
    ids = set()
    for lab, blk in rep["arxiv"].items():
        for r in blk["rows"]:
            ids.add(r["id"])
    rep["n_unique_arxiv"] = len(ids)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("\nqueries %d | unique arXiv ids %d | errors %d | wrote %s"
          % (len(ARX_QUERIES), len(ids), len(rep["errors"]), os.path.basename(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
