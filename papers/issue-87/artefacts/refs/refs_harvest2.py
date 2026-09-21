#!/usr/bin/env python3
"""#87 R403 -- second harvest pass: targeted queries over a WIDE window, with the abstract snippet printed.

The first pass (refs_harvest.py) used the two windows and broad terms; its buckets were noisy because a
broad term pulls in physics.  This pass asks the narrow questions the paper actually makes claims about,
over one wide window [2015-01-01, 2026-09-21] (both endpoints written), and prints each candidate with a
short abstract snippet, so a difference line can be written from the record rather than from the title.

Writes refs_pool2.json.
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
OUT = os.path.join(HERE, "refs_pool2.json")
ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"
W = ("201501010000", "202609212359")     # the wide window, both endpoints written
SCAN_DATE = "2026-09-21"

QUERIES = [
    ("q-kernel-theory", 'ti:"quantum kernel"'),
    ("q-kernel-est", 'abs:"quantum kernel" AND abs:"estimating"'),
    ("q-feature-map", 'ti:"feature map" AND cat:quant-ph'),
    ("q-embedding", 'ti:"quantum embedding" OR ti:"data encoding"'),
    ("q-kernel-conc", 'abs:"kernel" AND abs:"concentration"'),
    ("q-barren", 'ti:"barren plateau"'),
    ("q-advbench", 'abs:"quantum machine learning" AND abs:"classical baseline"'),
    ("q-dequant", 'abs:"dequantization" AND cat:quant-ph'),
    ("q-geometry", 'abs:"quantum kernel" AND abs:"geometry"'),
    ("q-kalign", 'abs:"kernel alignment" AND cat:stat.ML'),
    ("q-kselect", 'abs:"kernel" AND abs:"hyperparameter" AND cat:stat.ML'),
    ("q-mkl", 'ti:"multiple kernel learning"'),
    ("q-randfeat", 'ti:"random features"'),
    ("q-nystrom", 'ti:"Nystrom" AND ti:"kernel"'),
    ("q-cv", 'abs:"nested cross-validation" AND cat:stat.ML'),
    ("q-multtest", 'abs:"multiple testing" AND cat:stat.ML'),
    ("q-statcomp", 'abs:"statistical comparison" AND abs:"machine learning" AND abs:"algorithms"'),
    ("q-qmlreview", 'ti:"quantum machine learning" AND ti:"review"'),
    ("q-expressivity", 'abs:"expressivity" AND abs:"kernel" AND cat:quant-ph'),
    ("q-advantage", 'ti:"quantum advantage" AND cat:quant-ph'),
]


def fetch(url, tries=3, timeout=50):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/refharvest2"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:      # noqa: BLE001
            last = e
            time.sleep(2 + 3 * k)
    raise RuntimeError("fetch failed: %s (%s)" % (url, last))


def query(qbody, n=40):
    q = "%s AND submittedDate:[%s TO %s]" % (qbody, W[0], W[1])
    url = ("https://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q)
           + "&start=0&max_results=%d&sortBy=relevance&sortOrder=descending" % n)
    root = ET.fromstring(fetch(url))
    out = []
    for e in root.findall(ATOM + "entry"):
        eid = (e.findtext(ATOM + "id") or "").strip()
        aid = eid.rsplit("/abs/", 1)[-1].split("v")[0]
        pub = (e.findtext(ATOM + "published") or "").strip()
        prim = e.find(ARX + "primary_category")
        out.append(dict(
            source="arxiv", id=aid, url="https://arxiv.org/abs/" + aid,
            title=" ".join((e.findtext(ATOM + "title") or "").split()),
            authors=[(a.findtext(ATOM + "name") or "").strip() for a in e.findall(ATOM + "author")],
            year=int(pub[:4]) if pub[:4].isdigit() else None, published=pub,
            primary=prim.get("term") if prim is not None else "",
            summary=" ".join((e.findtext(ATOM + "summary") or "").split())))
    return out


def main():
    show = "-show" in sys.argv
    rep = dict(scan_date=SCAN_DATE, window=list(W), queries={}, errors=[])
    for label, qbody in QUERIES:
        try:
            rows = query(qbody)
            rep["queries"][label] = dict(query=qbody, n=len(rows), rows=rows)
            print("%-16s %-46s %d" % (label, qbody[:46], len(rows)), flush=True)
        except Exception as e:      # noqa: BLE001
            rep["errors"].append((label, repr(e)))
            print("%-16s ERROR %r" % (label, e), flush=True)
        time.sleep(3.2)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("\nwrote %s | errors %d" % (os.path.basename(OUT), len(rep["errors"])))
    if show:
        for label, blk in rep["queries"].items():
            print("\n=== %s  %s ===" % (label, blk["query"]))
            for r in blk["rows"]:
                a = r["authors"][0].split()[-1] if r["authors"] else "?"
                print("  %s  %s  %-12s %s" % (r["id"], r["year"], a[:12], r["title"][:88]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
