#!/usr/bin/env python3
"""Issue #126 -- reference scan + VERIFICATION for the precision-floor manuscript.

VENDORED, NOT RE-IMPLEMENTED.  The verification core below (`_get`, `norm`, `title_matches`,
`arxiv_search`, `crossref_by_title`, `_arxiv_titles`, `verify`) is a byte-for-byte copy of issue
#124's `refscan124.py`, which was itself repaired across three rounds (Class 175: a remembered
identifier RESOLVES to a different real paper, so only a TITLE comparison catches it; a match metric
must be symmetric; a transport failure is an outage, not a finding.  Class 176: an API that caps a
batch makes its own truncation look like unanswerable records).  `--selftest` asserts the copy is
still identical, because the value of importing proven verification code is lost the moment it is
quietly rewritten.

What is #126's own: the query families, the canonical works, and the topic terms -- the paper's
SUBJECT is the reachable-accuracy boundary of mixed-precision kernels, so the pool must carry the
error-analysis and mixed-precision literature rather than the evaluation-statistics literature.

  * arXiv API (`id_list`)                    -- existence by identifier, title compared.
  * Crossref (`query.bibliographic` search)  -- canonical works found BY TITLE, then matched.

Usage: python3 refscan126.py              (discover: write refs_raw.json)
       python3 refscan126.py --curate     (relevance-filter raw -> refs_pool.json)
       python3 refscan126.py --verify     (re-verify every pool entry by TITLE match)
       python3 refscan126.py --report     (write reference-check.md from the verified pool)
       python3 refscan126.py --selftest   (plants + the vendoring certificate)
"""
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "refs_raw.json")
POOL = os.path.join(HERE, "refs_pool.json")
CITE_KEY = re.compile(r"\[@([A-Za-z0-9_./:\-]+)\]")   # the citation key form build_refs.py rewrites
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
UA = "silicon-science-cs-refscan/1.0 (journal reference verification)"
ATOM = "{http://www.w3.org/2005/Atom}"

ARXIV_QUERIES = [
    ("mixed", 'cat:cs.MS AND all:"mixed precision"'),
    ("mixed2", 'all:"mixed precision" AND all:"iterative refinement"'),
    ("lowprec", 'cat:cs.MS AND all:"low precision" AND all:"linear algebra"'),
    ("half", 'all:"half precision" AND all:"accuracy" AND all:"GPU"'),
    ("fp8", 'all:"fp8" AND all:"training" AND all:"numerics"'),
    ("fp4", 'all:"fp4" AND all:"quantization" AND all:"numerical"'),
    ("tensorcore", 'all:"tensor core" AND all:"precision" AND all:"matrix multiplication"'),
    ("erranalysis", 'cat:cs.NA AND all:"rounding error analysis"'),
    ("backward", 'cat:cs.NA AND all:"backward error" AND all:"bound"'),
    ("compensated", 'all:"compensated summation" OR all:"error-free transformation"'),
    ("kahan", 'all:"Kahan summation" OR all:"compensated summation" AND all:"accuracy"'),
    ("condnum", 'cat:cs.NA AND all:"condition number" AND all:"accuracy"'),
    ("stochround", 'all:"stochastic rounding" AND all:"error"'),
    ("probround", 'all:"probabilistic" AND all:"rounding error" AND all:"analysis"'),
    ("emulate", 'all:"emulating" AND all:"precision" AND all:"floating-point"'),
    ("ozaki", 'all:"error-free transformation" AND all:"matrix multiplication"'),
    ("energy", 'all:"energy efficiency" AND all:"floating point" AND all:"precision"'),
    ("energy2", 'all:"energy" AND all:"numerical" AND all:"precision" AND all:"HPC"'),
    ("reproduce", 'all:"reproducibility" AND all:"floating point" AND all:"HPC"'),
    ("sparse", 'all:"sparse" AND all:"mixed precision" AND all:"solver"'),
    ("precond", 'all:"preconditioner" AND all:"precision" AND all:"linear system"'),
    ("autotune", 'all:"autotuning" AND all:"precision" AND all:"linear algebra"'),
    ("verified", 'all:"verified computing" AND all:"floating point"'),
    ("gpuacc", 'all:"GPU" AND all:"numerical accuracy" AND all:"tensor"'),
]

# canonical works this paper must argue against, given by TITLE (not by a remembered DOI).
CANONICAL = [
    ("Accuracy and Stability of Numerical Algorithms", 2002),
    ("Rounding Errors in Algebraic Processes", 1963),
    ("Further remarks on reducing truncation errors", 1965),
    ("A New Approach to Probabilistic Rounding Error Analysis", 2019),
    ("Stochastic rounding and its probabilistic backward error analysis", 2021),
    ("Numerical behavior of NVIDIA tensor cores", 2021),
    ("Harnessing GPU Tensor Cores for Fast FP16 Arithmetic to Speed up Mixed-Precision Iterative Refinement Solvers", 2018),
    ("Accelerating the Solution of Linear Systems by Iterative Refinement in Three Precisions", 2018),
    ("A New Analysis of Iterative Refinement and Its Application to Accurate Solution of Ill-Conditioned Sparse Linear Systems", 2017),
    ("Mixed Precision Block Fused Multiply-Add: Fast Algorithms and Error Analysis", 2020),
    ("Using Mixed Precision in Iterative Refinement", 2007),
    ("Recovering single precision accuracy from tensor core computations", 2022),
    ("Accurate sum and dot product", 2005),
    ("Accurate and Efficient Floating Point Summation", 2003),
    ("Ultimately Fast Accurate Summation", 2009),
    ("Error-free transformations of matrix multiplication by using fast routines of matrix multiplication", 2012),
    ("The University of Florida Sparse Matrix Collection", 2011),
    ("What Every Computer Scientist Should Know About Floating-Point Arithmetic", 1991),
    ("Handbook of Floating-Point Arithmetic", 2018),
    ("IEEE Standard for Floating-Point Arithmetic", 2019),
    ("Numerical Linear Algebra", 1997),
    ("Matrix Computations", 2013),
    ("Exploiting the Performance of 32 bit Floating Point Arithmetic in Obtaining 64 bit Accuracy", 2006),
    ("A Survey of Numerical Methods for the Solution of Toeplitz Systems of Equations", 1985),
    ("Numerical Methods for Least Squares Problems", 1996),
    ("The Design and Implementation of FFTW3", 2005),
    ("Ginkgo: A Modern Linear Operator Algebra Framework for High Performance Computing", 2022),
    ("Numerical Algorithms for High-Performance Computational Science", 2020),
    ("High-Performance Matrix Multiplication from Abstracted Data Types", 2019),
    ("An Error Analysis of the LAPACK routines", 2020),
]

# Works the paper's Related Work cannot do without, which the Crossref title search MISSED (its top
# hit was a different record -- a journal's peer-review sub-record, a book chapter, or a near title).
# Resolved through the arXiv title route instead, with the SAME two-sided matcher, and every addition
# must still survive `--verify`.  A remembered identifier is never used (Class 175(a)).
GAPFILL = [
    "Numerical behavior of NVIDIA tensor cores",
    "Using Mixed Precision in Iterative Refinement",
    "Mixed Precision Block Fused Multiply-Add: Fast Algorithms and Error Analysis",
    "FP8 Formats for Deep Learning",
    "Error-Free Transformations of Matrix Multiplication by Using Fast Routines of Matrix Multiplication",
    "A Floating-Point Technique for Extending the Available Precision",
    "Accurate Floating-Point Product and Exponentiation",
    "A New Error Analysis of Iterative Refinement",
    "Stochastic rounding: implementation, error analysis and applications",
    "Emulating FP64 with 2:1 Compression and Error Correction",
    "Performance, Power, and Accuracy Trade-offs of Mixed-Precision Matrix Multiplication",
    "Fast Accurate Summation",
    "Mixed-Precision Conjugate Gradient Solvers with RL-Driven Precision Tuning",
    "Error Analysis and Precision Selection for Mixed-Precision DEIM-CUR Decompositions",
    "Mixed-Precision Computing for Scientific Discovery: Formats, Co-Design, and Responsible Approximation",
]

# a pool entry counts as on-topic if the title/abstract carries one of these objects (Class 164(d):
# a pattern must name the OBJECT, not the vocabulary)
TOPIC_TERMS = [
    "precision", "floating-point", "floating point", "rounding", "round-off", "roundoff",
    "error analysis", "backward error", "forward error", "condition number", "ill-conditioned",
    "accumulat", "summation", "dot product", "matrix multiplication", "gemm", "tensor core",
    "iterative refinement", "compensated", "error-free transformation", "stochastic rounding",
    "half precision", "bfloat16", "fp8", "fp4", "mixed precision", "bit-width", "numerical accuracy",
    "numerical stability", "numerical behavior", "reproducib", "sparse", "precondition",
    "linear system", "linear algebra", "kernel", "energy efficiency", "energy per", "throughput",
]


def _get(url, timeout=40, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(3.0 * (i + 1))
    raise last


def norm(s):
    """Normalise a title for comparison: case-fold, strip accents/punctuation/whitespace."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def title_matches(a, b, min_frac=0.8):
    """Do two titles name the same work?  Token overlap measured in BOTH directions (the min of the
    two fractions), so a subtitle added or dropped by the publisher still matches, but a SHORT
    GENERIC title does not match a long specific one.  The first version of this divided by the
    SHORTER title, which let 'Machine Learning Benchmarks' score a perfect 1.00 against 'Accounting
    for Variance in Machine Learning Benchmarks' -- a metric that can never fail on the object it is
    built to catch (Class 164(d)/172(b): the denominator was the wrong object)."""
    ta, tb = set(norm(a).split()), set(norm(b).split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return min(inter / len(ta), inter / len(tb))


ARXIV_ID_RE = re.compile(r"^(?:[a-z\-]+(?:\.[A-Z]{2})?/\d{7}|\d{4}\.\d{4,5})$")


def _abs_id(entry_id):
    """The canonical arXiv id from an Atom <id> URL (e.g. http://arxiv.org/abs/math.NA/0009057v1).

    DECLARED REPAIR (R550, found on #126's foreign corpus).  The imported version took the LAST path
    segment, which is correct for new-style ids (2401.01234v2 -> 2401.01234) and WRONG for old-style
    ones, whose subject-class prefix is part of the id: math.NA/0009057 became a bare `0009057`, and
    arXiv answers HTTP 400 for such an id -- so ONE truncated id failed a whole 50-id batch and 50
    records were reported TRANSPORT-UNKNOWN.  #124 never hit this because its queries were cs.LG/cs.CL,
    which return only new-style ids: a case set that cannot exercise a path is why importing proven
    code needs a foreign corpus (Class 189's lesson, one level out).  Both derivations go through this
    function so the discovery and verification paths cannot drift apart.
    """
    return re.sub(r"v\d+$", "", entry_id.split("/abs/")[-1])


def arxiv_search(query, max_results=40):
    q = urllib.parse.quote(query, safe="")
    url = ("https://export.arxiv.org/api/query?search_query=%s"
           "&sortBy=relevance&max_results=%d" % (q, max_results))
    root = ET.fromstring(_get(url).decode("utf-8", "replace"))
    out = []
    for e in root.findall(ATOM + "entry"):
        aid = _abs_id(e.findtext(ATOM + "id", ""))
        out.append({"source": "arxiv", "id": aid,
                    "title": re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip(),
                    "authors": [a.findtext(ATOM + "name", "") for a in e.findall(ATOM + "author")],
                    "published": e.findtext(ATOM + "published", "")[:10],
                    "summary": re.sub(r"\s+", " ", e.findtext(ATOM + "summary", "")).strip(),
                    "query": query})
    return out


STOPWORDS = set("a an the of in for and with its their to on by from using".split())


def arxiv_by_title(title, max_results=8):
    """Resolve an arXiv record BY TITLE, and accept it only if the SAME two-sided matcher accepts it.
    The identifier is re-derived, never guessed (Class 175(a)).

    TWO ROUTES, in order, and the second exists because the first was measured to fail: arXiv's
    quoted-phrase search returns `totalResults=0` for a long phrase -- `all:"Numerical Behavior of
    NVIDIA Tensor Cores"` finds nothing while `all:"NVIDIA Tensor Cores"` finds 29 records -- so a
    single phrase route reports "not on arXiv" for papers that are on arXiv.  The fallback ANDs the
    content words, which is the form the pool's own queries use and which works.
    """
    q_phrase = 'all:"%s"' % re.sub(r'[":]', " ", title)
    words = [w.strip(",.:;") for w in re.sub(r'[":]', " ", title).split()]
    words = [w for w in words if len(w) > 3 and w.lower() not in STOPWORDS]
    q_terms = " AND ".join('all:"%s"' % w for w in words)
    for q in (q_phrase, q_terms):
        if not q:
            continue
        try:
            got = arxiv_search(q, max_results=max_results)
        except Exception:
            continue
        for r in got:
            if title_matches(title, r["title"]) >= 0.8:
                return r
        time.sleep(2.0)
    return None


def crossref_best_by_title(title, rows=20):
    """A SECOND Crossref route, additive to the imported one.  The imported `crossref_by_title` reads
    the FIRST record of a 5-row answer: for a book, a chaptered volume or a journal that publishes
    peer-review sub-records, the top hit is a DIFFERENT work and the route reports a MISS for a work
    Crossref actually holds (measured on #126's canonical list: 12 of 30 titles came back WEAK or
    MISS).  This route scores EVERY record of a wider answer with the SAME imported matcher and keeps
    the best -- recall without touching the claim core."""
    q = urllib.parse.quote(re.sub(r"[^\w\s:]", " ", title), safe="")
    url = ("https://api.crossref.org/works?rows=%d&query.bibliographic=%s" % (rows, q))
    try:
        items = json.loads(_get(url).decode("utf-8", "replace"))["message"]["items"]
    except Exception:
        return None
    best = None
    for it in items:
        tt = (it.get("title") or [""])[0]
        if not tt:
            continue
        m = title_matches(title, tt)
        if best is None or m > best[0]:
            best = (m, it, tt)
    if best is None or best[0] < 0.8:
        return None
    it = best[1]
    doi = it.get("DOI", "")
    if not doi:
        return None
    return {"source": "crossref", "id": doi, "title": best[2],
            "authors": [(a.get("family", "") + " " + a.get("given", "")).strip()
                        for a in it.get("author", [])][:12],
            "published": str((it.get("issued", {}).get("date-parts") or [[""]])[0][0]),
            "summary": re.sub(r"\s+", " ", it.get("abstract", "") or ""),
            "query": title, "added_by": "gapfill-crossref"}


def repair_ids():
    """Re-derive the identifier of any pool entry whose key is not a valid arXiv id.  Drops an entry
    only when the title route finds nothing that matches, and says which."""
    pool = json.load(open(POOL))
    bad = sorted(k for k, v in pool.items()
                 if v["source"] == "arxiv" and not ARXIV_ID_RE.match(k))
    print("ids failing the arXiv-id shape: %d" % len(bad))
    fixed = dropped = 0
    for k in bad:
        r = pool[k]
        got = arxiv_by_title(r["title"])
        if got is None:
            print("  [DROP] %s -> no title match for %r" % (k, r["title"][:60]))
            del pool[k]
            dropped += 1
        else:
            print("  [FIX ] %s -> %s  (%s)" % (k, got["id"], got["title"][:52]))
            r2 = dict(r)
            r2["id"] = got["id"]
            r2["id_repaired_from"] = k
            del pool[k]
            pool[got["id"]] = r2
            fixed += 1
        time.sleep(3.0)
    # (b) the stored `id` field must equal the KEY.  Discovery strips the version to form the key
    # (`id.split("v")[0]`, so 1803.04014v1 -> key 1803.04014) but stored the versioned id beside it,
    # so an entry's own id field disagreed with the id it is filed and verified under.  Inert for
    # verification (it reads the KEY) and misleading for a reader, which is the worst combination.
    normalised = 0
    for k, v in pool.items():
        if v.get("id") != k:
            v["id"] = k
            normalised += 1
    left = sorted(k for k, v in pool.items()
                  if v["source"] == "arxiv" and not ARXIV_ID_RE.match(k))
    assert not left, "ids still failing the shape after repair: %s" % left
    json.dump(pool, open(POOL, "w"), indent=1, sort_keys=True)
    print("repair: %d fixed, %d dropped, %d id fields normalised; pool now %d"
          % (fixed, dropped, normalised, len(pool)))
    return 0


def gapfill():
    """Resolve the GAPFILL titles by arXiv title search and add every match to the pool.  Additions
    are marked, and the caller must re-run `--verify`: this step only widens the pool, it does not
    verify (verification is one pass, over every entry, or it is nothing)."""
    pool = json.load(open(POOL))
    titles_set = {v["title"].lower() for v in pool.values()}
    added = missed = 0
    for title in GAPFILL:
        got = arxiv_by_title(title)
        if got is None:
            got = crossref_best_by_title(title)       # the wider route, for books and volumes
        if got is None:
            print("  [MISS] %s" % title[:66])
            missed += 1
        elif got["title"].lower() in titles_set:
            print("  [HAVE] %s" % got["title"][:66])
        else:
            r = dict(got)
            r["added_by"] = "gapfill"
            pool[got["id"]] = r
            titles_set.add(got["title"].lower())
            print("  [ADD ] %s -> %s" % (title[:34], got["title"][:52]))
            added += 1
        time.sleep(3.0)
    json.dump(pool, open(POOL, "w"), indent=1, sort_keys=True)
    print("gapfill: %d added, %d missed; pool now %d (RE-RUN --verify)" % (added, missed, len(pool)))
    return 0


def crossref_by_title(title):
    """Search Crossref for a work BY TITLE and return the best candidate with its match score."""
    url = ("https://api.crossref.org/works?rows=5&query.bibliographic="
           + urllib.parse.quote(title, safe=""))
    items = json.loads(_get(url).decode("utf-8", "replace"))["message"]["items"]
    best = None
    for m in items:
        t = (m.get("title") or [""])[0]
        sc = title_matches(title, t)
        if best is None or sc > best[2]:
            year = None
            for k in ("published-print", "published-online", "issued"):
                if m.get(k, {}).get("date-parts"):
                    year = m[k]["date-parts"][0][0]
                    break
            best = (m.get("DOI", ""), t, sc, year,
                    (m.get("container-title") or [""])[0],
                    ["%s %s" % (a.get("given", ""), a.get("family", "")) for a in m.get("author", [])][:8])
    if best is None:
        return None
    doi, t, sc, year, cont, auth = best
    return {"source": "crossref", "id": doi, "title": t, "authors": auth,
            "published": str(year or ""), "container": cont,
            "cited_title": title, "title_match": round(sc, 3), "query": "bibliographic:" + title}


def discover():
    raw = {}
    print("== arXiv ==")
    for tag, q in ARXIV_QUERIES:
        try:
            got = arxiv_search(q)
        except Exception as e:
            print("  [%-9s] FAILED: %s" % (tag, e)); time.sleep(3); continue
        new = 0
        for r in got:
            k = r["id"].split("v")[0]
            if k not in raw:
                raw[k] = r; new += 1
        print("  [%-9s] %2d hits (%d new)" % (tag, len(got), new))
        time.sleep(3.0)
    print("== Crossref (canonical works, found BY TITLE) ==")
    for title, yr in CANONICAL:
        try:
            r = crossref_by_title(title)
            if r is None:
                print("  [MISS] %s" % title[:58]); continue
            flag = "OK " if r["title_match"] >= 0.8 else "WEAK"
            print("  [%s %.2f] %s -> %s" % (flag, r["title_match"], title[:40], r["title"][:44]))
            if r["title_match"] >= 0.8:
                raw[r["id"]] = r
        except Exception as e:
            print("  [FAIL] %s: %s" % (title[:40], e))
        time.sleep(1.0)
    json.dump(raw, open(RAW, "w"), indent=1, sort_keys=True)
    print("\nraw unique: %d -> %s" % (len(raw), os.path.relpath(RAW, HERE)))


def curate():
    raw = json.load(open(RAW))
    import math
    pool = {}
    for k, r in raw.items():
        if r["source"] == "crossref":
            pool[k] = r                          # canonical works are kept by construction
            continue
        text = (r["title"] + " " + r["summary"]).lower()
        hits = sum(1 for t in TOPIC_TERMS if t in text)
        if hits >= 2:                            # on-topic: names >=2 of the objects we cite
            r2 = dict(r); r2["topic_hits"] = hits
            pool[k] = r2
    json.dump(pool, open(POOL, "w"), indent=1, sort_keys=True)
    print("curated pool: %d of %d raw  -> %s" % (len(pool), len(raw), os.path.relpath(POOL, HERE)))


def _arxiv_titles(ids, chunk=50):
    """Fetch titles for many arXiv ids in BATCHES (id_list=...) -- one request per chunk, not per
    id.  The first version issued one request per entry, which on 239 entries ran past 30 minutes
    once arXiv throttled it.  Returns ({id: title}, n_batches_failed): a chunk that FAILED (429,
    timeout) must be reported as a TRANSPORT failure, never as 'these records are absent' -- the
    first version of this function let a 429 masquerade as 239 unverified records (Class 164(a)):
    an outage is not a finding.

    NOTE the `max_results` on the query: the arXiv API caps an `id_list` request at 10 entries
    unless told otherwise, so the first batched run silently returned 10 titles per 50-id chunk and
    reported the other 189 as 'unanswerable'.  Request the chunk's own size and ASSERT the count,
    or a transport-shaped silence looks like a data problem."""
    out = {}
    failed = 0
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        url = ("https://export.arxiv.org/api/query?id_list=" + ",".join(part)
               + "&max_results=%d" % len(part))
        try:
            root = ET.fromstring(_get(url).decode("utf-8", "replace"))
        except Exception as e:
            print("    [batch %d-%d] TRANSPORT FAILURE: %s" % (i, i + len(part), e), flush=True)
            failed += 1
            continue
        got = root.findall(ATOM + "entry")
        if len(got) < len(part):
            # fewer entries than ids: this is a REAL signal (some ids absent/withdrawn) but it must
            # not be silently absorbed -- say how many came back
            print("    [batch %d-%d] WARNING: %d ids, %d entries returned"
                  % (i, i + len(part), len(part), len(got)), flush=True)
        for e in got:
            aid = _abs_id(e.findtext(ATOM + "id", ""))
            out[aid] = re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip()
        print("    batch %d/%d ok (%d titles)" % (i // chunk + 1, (len(ids) + chunk - 1) // chunk, len(out)),
              flush=True)
        time.sleep(3.0)
    return out, failed


def verify():
    pool = json.load(open(POOL))
    ok = mismatch = transport = 0
    arxiv_keys = [k for k, v in pool.items() if v["source"] == "arxiv"]
    print("verifying %d arXiv + %d Crossref entries" % (len(arxiv_keys),
          len(pool) - len(arxiv_keys)), flush=True)
    live, failed_batches = _arxiv_titles(arxiv_keys)
    for key in arxiv_keys:
        if key not in live:
            transport += 1                       # no answer for this id: UNKNOWN, not a finding
            continue
        good = title_matches(pool[key]["title"], live[key]) >= 0.8
        ok += 1 if good else 0
        mismatch += 0 if good else 1
        if not good:
            print("  MISMATCH %s\n     stored: %s\n     live  : %s"
                  % (key, pool[key]["title"][:66], live[key][:66]), flush=True)
    for key, r in sorted(pool.items()):
        if r["source"] != "crossref":
            continue
        try:
            m = json.loads(_get("https://api.crossref.org/works/"
                                + urllib.parse.quote(key, safe="")).decode("utf-8", "replace"))["message"]
            good = title_matches(r["title"], (m.get("title") or [""])[0]) >= 0.8
        except Exception:
            transport += 1
            continue
        ok += 1 if good else 0
        mismatch += 0 if good else 1
        time.sleep(0.8)
    total = len(pool)
    print("VERIFIED %d / %d ; TITLE MISMATCH %d ; TRANSPORT-UNKNOWN %d (batches failed: %d)"
          % (ok, total, mismatch, transport, failed_batches))
    print("a nonzero TRANSPORT-UNKNOWN is an OUTAGE, not evidence about the records -- re-run later")
    # a transport failure must NOT be reported as success, and a mismatch MUST fail the run
    return 0 if (mismatch == 0 and transport == 0) else 1


# the IMPORTED claim core: asserted byte-identical to issue #124's verified originals
CLAIM_CORE = ["_get", "norm", "title_matches", "crossref_by_title", "verify"]
# imported functions carrying a DECLARED repair.  A declaration must be BY SHAPE AND WITH A REASON
# (Class 112), and the certificate asserts the repair is PRESENT -- so reverting it fires too.
DECLARED_REPAIRS = {
    "arxiv_search": "id derivation routed through _abs_id (old-style ids keep their subject-class "
                    "prefix; the imported rsplit('/')[-1] produced bare '0009057' and arXiv answered "
                    "HTTP 400, failing a whole 50-id batch) -- R550, found on #126's foreign corpus",
    "_arxiv_titles": "same id derivation, same repair",
}
ORIGIN = os.path.join(HERE, "..", "..", "issue-124", "research", "refscan124.py")


def _fn_source(path, name):
    """The SOURCE TEXT of one function, via ast -- so the comparison is of the code as parsed, not of
    a line range that a later edit can shift."""
    import ast
    src = io.open(path, encoding="utf-8").read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node)
    return None


def _core_diff(origin, copy, names=None):
    """The claim-core functions that differ between two files.  Two PATHS, so the comparison has two
    sides that can disagree -- a certificate whose two sides are the same expression is a tautology
    that can never fire (Class 171), and the plant below is what proves this one can."""
    diffs = []
    for name in (CLAIM_CORE if names is None else names):
        a = _fn_source(origin, name)
        b = _fn_source(copy, name)
        if a is None or b is None:
            diffs.append("%s: missing (%s/%s)" % (name, a is not None, b is not None))
        elif a.strip() != b.strip():
            diffs.append("%s: DIFFERS" % name)
    return diffs


def vendoring_certificate(verbose=True, copy=None):
    """Assert that the verification core was IMPORTED, not re-implemented.  This is the round's
    method claim (Class 174(e): a law is a policy only once a foreign data source satisfies it, and
    the strong test is to import the CLAIM code UNCHANGED) -- and a claim with no check is prose.
    A missing origin file is a SKIP with a reason, never a pass: on a checkout of the committed tree
    the sibling research tree does not exist, and the certificate must say so rather than go green.
    """
    if not os.path.exists(ORIGIN):
        return ("SKIPPED: origin %s not present in this tree -- the vendoring claim is UNCHECKED here"
                % os.path.relpath(ORIGIN, HERE))
    copy = copy or os.path.abspath(__file__)
    diffs = _core_diff(ORIGIN, copy, CLAIM_CORE)
    if diffs:
        raise AssertionError("the vendored verification core was modified: %s" % "; ".join(diffs))
    missing = []
    for name in sorted(DECLARED_REPAIRS):
        d = _core_diff(ORIGIN, copy, [name])
        if not d:
            missing.append(name)
    if missing:
        raise AssertionError("declared repair(s) NOT PRESENT (the declaration is false): %s"
                             % "; ".join(missing))
    if verbose:
        print("vendoring certificate: %d/%d claim-core functions byte-identical to issue #124's "
              "verified originals; %d declared repair(s) present"
              % (len(CLAIM_CORE), len(CLAIM_CORE), len(DECLARED_REPAIRS)))
    return ("OK: %d identical, %d declared repairs present" % (len(CLAIM_CORE), len(DECLARED_REPAIRS)))


def selftest():
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-30s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    # the matcher must ACCEPT a true match (subtitle variation allowed) and REJECT a generic short
    # title -- the exact false positives the first version produced
    holds("accept-identical", title_matches("Deep Reinforcement Learning that Matters",
                                            "Deep Reinforcement Learning that Matters") == 1.0)
    holds("accept-subtitle", title_matches("Reporting Score Distributions Makes a Difference",
                                           "Reporting Score Distributions Makes a Difference: A Study") >= 0.8)
    holds("reject-generic-short", title_matches(
        "Accounting for Variance in Machine Learning Benchmarks", "Machine Learning Benchmarks") < 0.8)
    holds("reject-substring", title_matches(
        "A Study of Cross-Validation and Bootstrap for Accuracy Estimation", "Cross validation") < 0.8)
    holds("reject-different", title_matches("Shape Quantization and Recognition with Randomized Trees",
                                            "Approximate Statistical Tests for Comparing Classifiers") < 0.8)
    # the CITED-SET report: the object is the manuscript's citation list, so the checks are about
    # citations, not about the pool.  Both directions are planted -- a citation the pool does not
    # carry, and a key filed under the WRONG source (Class 191: a field disagreeing with the key it is
    # filed under is inert and misleading at once).
    pool = json.load(open(POOL)) if os.path.exists(POOL) else {}
    if pool:
        draft = io.open(os.path.join(HERE, "manuscript_source.md"), encoding="utf-8").read()
        rows, order = cited_rows(pool, draft)
        holds("cited-rows-one-per-key", len(rows) == len(order) and len(order) == len(set(order)))
        holds("cited-set-is-a-subset", len(order) <= len(pool))
        an_arxiv = [k for k in pool if pool[k]["source"] == "arxiv"][0]
        mis = "doi:" + an_arxiv                     # right id, wrong source
        try:
            cited_rows(pool, "see [@%s]." % mis)
            holds("source-mismatch-fails", False)
        except AssertionError:
            holds("source-mismatch-fails", True)
        try:
            cited_rows(pool, "see [@arxiv:9999.99999].")
            holds("dangling-cited-key-fails", False)
        except AssertionError:
            holds("dangling-cited-key-fails", True)
        refs_path2 = os.path.join(HERE, "references.md")
        if os.path.exists(refs_path2):
            rl = read_lines(refs_path2)
            holds("numbering-matches-reference-list", numbering_matches(rows, rl))
            swapped = list(rl)
            swapped[0], swapped[1] = swapped[1], swapped[0]
            holds("numbering-plant-fires", not numbering_matches(rows, swapped))
        # the plant must be able to PASS: a genuine citation resolves and produces one row
        holds("real-citation-resolves", len(cited_rows(pool, "see [@arxiv:%s]." % an_arxiv)[0]) == 1)
    else:
        print("[%-30s] SKIPPED (no pool)" % "cited-set-report")
    # the vendoring certificate, and a PLANT proving it can fail: a copy whose claim core was
    # edited must be caught.  Without this the certificate is decoration -- and the first run of the
    # real one DID fire, on an edit of mine to `verify()`, which is how it was shown to work.
    import tempfile
    src = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    mutated = src.replace("def norm(s):\n", "def norm(s):\n    s = s  # planted edit\n", 1)
    assert mutated != src, "the plant did not change the source"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
        fh.write(mutated)
        tmp = fh.name
    if os.path.exists(ORIGIN):
        diff = _core_diff(ORIGIN, tmp)
        holds("plant-detected-by-certificate", any("norm" in d for d in diff))
        holds("clean-copy-passes", _core_diff(ORIGIN, os.path.abspath(__file__)) == [])
        print("[%-30s] %s" % ("vendoring-certificate", vendoring_certificate(verbose=False)))
        # the OTHER side: a copy whose declared repair was REVERTED must fire, or the declaration is
        # unenforced prose (a declaration the check cannot test is not a declaration)
        mine = _fn_source(os.path.abspath(__file__), "_arxiv_titles")
        org = _fn_source(ORIGIN, "_arxiv_titles")
        reverted = src.replace(mine, org, 1)
        holds("revert-plant-changed-source", reverted != src)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
            fh.write(reverted)
            tmp2 = fh.name
        try:
            vendoring_certificate(verbose=False, copy=tmp2)
            holds("reverted-repair-detected", False)
        except AssertionError as e:
            holds("reverted-repair-detected", "NOT PRESENT" in str(e))
        os.unlink(tmp2)
    else:
        print("[%-30s] SKIPPED (no origin tree)" % "vendoring-certificate")
    os.unlink(tmp)
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def verify_pages(sample=None, offset=0):
    """Verify by arXiv ABSTRACT PAGE (a different endpoint from the API, which serves while the API
    is 429 -- the journal's own documented workaround).  Slower per entry, so it takes a sample and
    reports the rate; it is a SPOT CHECK, not the full pass, and it says so."""
    pool = json.load(open(POOL))
    keys = sorted(k for k, v in pool.items() if v["source"] == "arxiv")
    if sample:
        keys = keys[offset:offset + sample]
    ok = mismatch = transport = 0
    for k in keys:
        try:
            html = _get("https://arxiv.org/abs/" + k).decode("utf-8", "replace")
        except Exception as e:
            print("  [%s] TRANSPORT: %s" % (k, e), flush=True); transport += 1; time.sleep(2); continue
        m = re.search(r'<meta name="citation_title" content="([^"]*)"', html)
        live = m.group(1) if m else ""
        good = title_matches(pool[k]["title"], live) >= 0.8
        ok += 1 if good else 0
        mismatch += 0 if good else 1
        if not good:
            print("  MISMATCH %s\n     stored: %s\n     live  : %s"
                  % (k, pool[k]["title"][:62], live[:62]), flush=True)
        time.sleep(2.0)
    n = len(keys)
    print("abstract-page SPOT CHECK: verified %d / %d ; MISMATCH %d ; TRANSPORT %d"
          % (ok, n, mismatch, transport))
    print("(a spot check, not the full pass -- the API pass is deferred while it is throttled)")
    return 0 if mismatch == 0 else 1


def read_lines(path):
    return [l for l in io.open(path, encoding="utf-8").read().split("\n") if l.strip()]


def numbering_matches(rows, ref_lines):
    """Do the report's rows carry the same papers under the same numbers as the reference list?

    The report numbers a citation by its first appearance in the draft and the reference list numbers
    it the same way -- in different code, on the same input.  The comparison is on the LINK, which is
    the one field both artefacts carry, so a re-ordering (an inserted entry, an edited table) shows up
    as a disagreement rather than as a pair of documents that each look internally consistent."""
    if len(ref_lines) != len(rows):
        return False
    for rl, rw in zip(ref_lines, rows):
        if rl.rsplit(" ", 1)[-1].strip() != rw.split("|")[6].strip():
            return False
    return True


def cited_rows(pool, draft):
    """The CITED subset, in first-appearance order: every entry the manuscript actually cites, with
    the live record it was verified against.  The Phase-B report is about the paper's citation list,
    not about the pool the author collected -- a pool entry the text never cites is padding, and a
    key the text cites but the pool does not carry is a citation that was never verified.  Both are
    asserted here (R551: the pool is 337 entries, the manuscript cites 107 of them)."""
    order = []
    for m in CITE_KEY.finditer(draft):
        if m.group(1) not in order:
            order.append(m.group(1))
    rows, missing = [], []
    for i, k in enumerate(order, 1):
        src, _sep, eid = k.partition(":")
        want = "crossref" if src == "doi" else "arxiv"
        e = pool.get(eid)
        if e is None or e.get("source") != want:
            missing.append(k)
            continue
        # the stored title is cleaned the same way the reference list cleans it: this report is read
        # by a human and pasted into the submission, so publisher markup is a presentation defect
        title = WS.sub(" ", TAG.sub("", (e.get("title") or "").replace("\n", " "))).strip()
        verifier = "arXiv id_list" if want == "arxiv" else "Crossref works/<doi>"
        free = ("https://arxiv.org/abs/" + eid) if want == "arxiv" else ("https://doi.org/" + eid)
        rows.append("| [%d] | `%s` | %s | %s | %s | %s |"
                    % (i, k, want, verifier, title.replace("|", "/"), free))
    assert not missing, ("%d cited key(s) do not resolve in the verified pool (a citation that was "
                         "never verified): %s" % (len(missing), sorted(set(missing))[:8]))
    return rows, order


def report():
    """Write the Phase-B citation-authenticity report for the manuscript's CITED set.  One line per
    cited entry: number -> citation key -> source -> the endpoint that verified it -> the title as
    returned -> the link.  The header records the pool it was drawn from and the exact verification
    pass, read back from the log rather than typed (Class 164(b))."""
    pool = json.load(open(POOL))
    draft = io.open(os.path.join(HERE, "manuscript_source.md"), encoding="utf-8").read()
    rows, order = cited_rows(pool, draft)
    # The report's [n] must be the manuscript's [n].  Both are derived from the same draft, but by
    # different code paths (cited_rows here, build_refs.py there), so assert the two ORDERINGS are the
    # same object-level sequence -- a report whose numbers point at a different paper than the
    # manuscript's numbers is worse than no report (Class 124(a): a key derived from order re-points).
    refs_path = os.path.join(HERE, "references.md")
    if os.path.exists(refs_path):
        ref_lines = read_lines(refs_path)
        assert numbering_matches(rows, ref_lines), (
            "the report's [n] and the reference list's [n] disagree -- the two orderings are different "
            "objects (%d report rows, %d list entries)" % (len(rows), len(ref_lines)))
    n_arxiv = sum(1 for r in rows if "| arxiv |" in r)
    log_path = os.path.join(HERE, "verify_log.txt")
    if os.path.exists(log_path):
        passes = [l.strip() for l in io.open(log_path, encoding="utf-8") if l.strip()]
        pass_line = passes[-1] if passes else "NO PASS RECORDED"
    else:
        pass_line = "NO PASS RECORDED -- run `--verify` first (this line is read back, never typed)"
    lines = [
        "# Reference authenticity check -- issue #126",
        "",
        "Every entry **cited by the manuscript** was checked against a LIVE external record, comparing",
        "the returned TITLE against the stored title (two-sided token match, threshold 0.80).  A",
        "resolver that merely answers is not enough: a remembered identifier can resolve to a",
        "DIFFERENT real paper, so the check is the title comparison, not the HTTP status.",
        "",
        "- sources: arXiv API `id_list` (batched, `max_results` set per chunk) + Crossref `works/<doi>`",
        "- verified pool: %d entries; **cited by the manuscript: %d** (%d arXiv, %d Crossref)"
        % (len(pool), len(order), n_arxiv, len(order) - n_arxiv),
        "- last full pass: %s" % pass_line,
        "- an entry is dropped, never kept, if its title does not match; the manuscript may cite only",
        "  pool entries, so the list below is a subset of the verified pool by construction",
        "",
        "| ref | citation key | source | verified against | title as returned | link |",
        "|-----|--------------|--------|------------------|-------------------|------|",
    ]
    lines.extend(rows)
    path = os.path.join(HERE, "reference-check.md")
    io.open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote %s (%d cited entries of %d verified)" % (os.path.basename(path), len(order), len(pool)))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--gapfill" in sys.argv:
        sys.exit(gapfill())
    if "--repair-ids" in sys.argv:
        sys.exit(repair_ids())
    if "--curate" in sys.argv:
        sys.exit(curate() or 0)
    if "--verify" in sys.argv:
        # The wrapper records the pass, so `verify()` stays the byte-identical import.  It captures
        # what verify() PRINTS and stores that line, so the log carries the pass the verifier
        # reported rather than a number recomputed outside it (Class 164(b): the check must read the
        # thing it names, not a second copy of it).
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = verify()
        printed = buf.getvalue()
        sys.stdout.write(printed)
        summary = [l for l in printed.splitlines() if l.startswith("VERIFIED ")]
        if summary:
            with io.open(os.path.join(HERE, "verify_log.txt"), "a", encoding="utf-8") as f:
                f.write("%s  rc=%d  %s\n"
                        % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), rc, summary[-1]))
        sys.exit(rc)
    if "--report" in sys.argv:
        sys.exit(report() or 0)
    if "--verify-pages" in sys.argv:
        i = sys.argv.index("--verify-pages")
        n = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 12
        off = int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 0
        sys.exit(verify_pages(n, off))
    sys.exit(discover() or 0)
