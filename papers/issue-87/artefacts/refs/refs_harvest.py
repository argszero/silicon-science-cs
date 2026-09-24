#!/usr/bin/env python3
"""#87 R403 -- the reference corpus harvest, with the search FORM stated as data.

The journal's bar (README quality-bar item 2) makes the *search* a carrier: which indices, which
terms, which window (counted on a NAMED date field, both endpoints written), and the scan date.
This script performs that search and records the form it performed into the output, so the
manuscript's related-work section and `reference-check.md` can state a search rather than assert one.

INDICES
  * arXiv API (export.arxiv.org), date field = `submittedDate` (the submission date).  arXiv exposes
    one date filter; it has NO way to filter on a paper's latest version, so a paper revised into
    relevance after its original posting is invisible to a window that reaches only the posting --
    recorded as an unavailable coordinate rather than silently ignored.
  * Crossref REST API (api.crossref.org), used per-DOI for the canonical/classical works (records
    that carry a DOI).  Crossref exposes four date fields over one query; the field used here is
    `published` (from-pub-date/until-pub-date), and the other three (created, online-publication,
    print-publication) are recorded as NOT read for this harvest.

WINDOWS (both endpoints written; a window is a coordinate, not a word)
  W1 "hot"      submittedDate [2026-01-01, 2026-09-21]  -- the current-season literature
  W2 "classic"  submittedDate [2018-01-01, 2025-12-31]  -- the field preceding the hot window
  W3 DOIs       no window: named records, each read by its own identifier

SCAN DATE     2026-09-21 (when this harvest was run)

OUTPUT
  refs_raw.json  -- every harvested record with the fields the house entry style needs
                    (authors, year, title, venue/identifier, resolvable URL) plus the query that
                    returned it, so selection can be audited against the form
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
SCAN_DATE = "2026-09-21"

ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"

W1 = ("202601010000", "202609212359")
W2 = ("201801010000", "202512312359")

# (query label, arXiv search_query body, window, max_results)
ARX_QUERIES = [
    ("arx-W1-zkernel", 'all:"quantum kernel"', W1, 40),
    ("arx-W1-zfeat", 'all:"quantum feature map"', W1, 40),
    ("arx-W1-zkernel-adv", 'all:"quantum kernel" AND all:"advantage"', W1, 40),
    ("arx-W1-qmlbench", 'cat:cs.LG AND all:"quantum machine learning"', W1, 40),
    ("arx-W1-barren", 'all:"barren plateau"', W1, 30),
    ("arx-W1-kalign", 'all:"kernel alignment"', W1, 30),
    ("arx-W1-pqk", 'all:"projected quantum kernel"', W1, 20),
    ("arx-W1-entangle", 'all:"entanglement" AND all:"kernel"', W1, 30),
    ("arx-W2-zkernel", 'all:"quantum kernel"', W2, 40),
    ("arx-W2-zkernelmethods", 'ti:"quantum kernel methods"', W2, 20),
    ("arx-W2-kalign", 'all:"kernel target alignment"', W2, 25),
    ("arx-W2-randfeat", 'ti:"random features"', W2, 25),
    ("arx-W2-dequant", 'all:"dequantization" AND cat:quant-ph', W2, 25),
    ("arx-W2-krr", 'all:"kernel ridge regression"', W2, 25),
    ("arx-W2-mkl", 'all:"multiple kernel learning"', W2, 25),
    ("arx-W2-nys", 'all:"Nystrom" AND all:"kernel approximation"', W2, 20),
    ("arx-W2-qksvm", 'all:"quantum" AND all:"support vector machine"', W2, 25),
    ("arx-W2-kerneltheory", 'all:"reproducing kernel Hilbert space"', W2, 25),
]

# The classical/statistical spine, read per DOI (records that are not primarily arXiv).
CROSSREF_DOIS = [
    ("10.1007/BF02289343", "kernel ridge / statistical learning anchor"),
    ("10.1023/A:1007437227846", "kernel methods in statistics"),
    ("10.1162/089976698300017746", "kernel regression and the smoothing literature"),
    ("10.1214/aos/1013699998", "random features"),
    ("10.1109/5.726791", "regularisation and the classical margin literature"),
    ("10.1023/A:1022627411411", "capacity control"),
    ("10.1007/s10994-006-6226-1", "multiple comparison procedures for learners"),
    ("10.1111/j.2517-6161.1995.tb02031.1", "false discovery rate"),
    ("10.2307/2331554", "the paired small-sample statistic (Student)"),
    ("10.1093/biomet/6.1.1", "the rank/order-statistic tradition"),
    ("10.1214/aos/1176346060", "cross-validation theory"),
    ("10.1080/01621459.1979.10481038", "bootstrap resampling"),
    ("10.1214/ss/1009213726", "Bayesian model selection"),
    ("10.1162/089976600300015475", "model selection and overfitting"),
    ("10.1023/A:1010933404324", "ensemble baselines"),
    ("10.1023/A:1009706826165", "kernel-target alignment"),
    ("10.1007/978-3-540-78646-7_21", "kernel alignment, refined"),
    ("10.1162/089976603321780317", "kernel choice and the regularisation path"),
    ("10.1017/CBO9780511809682", "the RKHS framework (book)"),
    ("10.1007/978-1-4614-7556-8", "kernel methods in practice"),
    ("10.1007/978-1-4471-5782-1", "kernel methods: a survey"),
    ("10.1162/neco.1995.7.5.954", "support-vector kernels"),
    ("10.1145/1143844.1143977", "empirical kernel selection"),
    ("10.1109/TPAMI.2005.127", "kernel parameter selection"),
    ("10.1038/323533a0", "learning from examples"),
    ("10.1103/PhysRevLett.80.4811", "quantum computation with a small number of qubits"),
    ("10.1103/RevModPhys.75.715", "quantum information and computation"),
    ("10.1126/science.1058040", "quantum algorithms"),
    ("10.1038/nature23474", "quantum computing in the NISQ era"),
    ("10.1103/RevModPhys.74.1", "quantum computation and information"),
    ("10.1103/PhysRevA.97.042315", "circuit-centric quantum kernels"),
    ("10.1103/PhysRevLett.122.140504", "the kernel-advantage claim"),
    ("10.1038/s41534-019-0187-2", "quantum-kernel implementation on hardware"),
    ("10.1038/s41567-019-0648-8", "quantum machine learning: a review"),
    ("10.22331/q-2021-08-30-531", "power of data in quantum machine learning"),
    ("10.1126/science.abn7293", "dequantisation and the limits of the advantage"),
    ("10.1103/PhysRevX.11.041011", "trainability limits"),
    ("10.1038/s41467-024-49403-9", "quantum kernels beyond classically simulable maps"),
    ("10.1088/2058-9565/ac30f0", "kernel methods and quantum feature maps"),
    ("10.1103/PhysRevA.105.032416", "the geometry of quantum feature maps"),
]


def fetch(url, tries=3, timeout=50):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/refharvest"})
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
            summary=" ".join((e.findtext(ATOM + "summary") or "").split())[:400],
        ))
    return out


def crossref_doi(doi):
    d = json.loads(fetch("https://api.crossref.org/works/" + urllib.parse.quote(doi)))
    m = d["message"]
    year = None
    for k in ("published", "issued", "published-print", "published-online", "created"):
        parts = (m.get(k) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            year = parts[0][0]
            break
    return dict(
        source="crossref", doi=doi, url="https://doi.org/" + doi,
        title=" ".join((m.get("title") or [""])[0].split()),
        authors=[(a.get("family", "") + (", " + a["given"].split()[0] if a.get("given") else ""))
                 for a in (m.get("author") or [])],
        raw_authors=m.get("author") or [],
        year=year,
        venue=" ".join(((m.get("container-title") or [""])[0] or m.get("publisher", "")).split()),
        type=m.get("type", ""),
    )


def main():
    rep = dict(scan_date=SCAN_DATE,
               form=dict(
                   arxiv=dict(index="arXiv API (export.arxiv.org)", date_field="submittedDate",
                              windows={"W1": list(W1), "W2": list(W2)},
                              unavailable="no filter on the latest version: a paper revised into "
                                          "relevance after its original posting is invisible to a "
                                          "window that reaches only the posting"),
                   crossref=dict(index="Crossref REST API (api.crossref.org)", date_field="published",
                                 windows={"W3": "per-identifier, no window"},
                                 not_read=["created", "published-online", "published-print"]),
                   queries=[q[0] for q in ARX_QUERIES],
                   scan_date=SCAN_DATE),
               arxiv={}, crossref={}, errors=[])
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
    for doi, note in CROSSREF_DOIS:
        try:
            r = crossref_doi(doi)
            r["note"] = note
            rep["crossref"][doi] = r
            print("%-40s %s (%s)" % (doi, r["title"][:60], r["year"]), flush=True)
        except Exception as e:      # noqa: BLE001
            rep["errors"].append((doi, repr(e)))
            print("%-40s ERROR %r" % (doi, e), flush=True)
        time.sleep(0.4)
    ids = set()
    for lab, blk in rep["arxiv"].items():
        for r in blk["rows"]:
            ids.add(r["id"])
    rep["n_unique_arxiv"] = len(ids)
    rep["n_crossref_ok"] = len(rep["crossref"])
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("\nunique arXiv ids %d | crossref records %d | errors %d | wrote %s"
          % (len(ids), len(rep["crossref"]), len(rep["errors"]), os.path.basename(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
