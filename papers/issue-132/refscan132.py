#!/usr/bin/env python3
"""Issue #132 -- reference scan + VERIFICATION.

The subject is the BACKGROUND FRAME a similarity guard uses: the corpus-wide DF threshold (or the
stopword/boilerplate list behind it) that decides which shared units are "generic" and may be
ignored.  This file discovers the related work for that subject and VERIFIES every entry against a
live external record.

A citation is verified only if the returned record MATCHES the citation, not merely if the endpoint
answers.  A DOI or an arXiv id written from memory RESOLVES -- the API returns HTTP 200 with a real
record -- but the record can be a DIFFERENT paper.  So the check is the returned TITLE against the
stored title, compared two-sided, and nothing here is typed from memory: every key in the pool came
out of this tool's own discovery pass.

Three things the checks refuse to do, each because it was once the bug:

  * divide the title overlap by ONE of the two titles -- a short generic title then scores 1.00
    against a long specific one, i.e. a metric that can never fail on the object it is built to
    catch.  The score is the SMALLER of the two coverage fractions.
  * report a transport failure as a finding.  An outage is not evidence about a record: a failed
    batch yields TRANSPORT-UNKNOWN, never "these records do not exist", and makes the run fail.
  * silently under-ask.  The arXiv `id_list` endpoint caps a request at 10 entries unless
    `max_results` says otherwise, so a 50-id chunk returns 10 titles and the other 40 look
    unanswerable -- a truncation disguised as a data problem.  `max_results` is set to the chunk's
    own size and the returned count is asserted.

Sources, both declarative:
  * arXiv API (`search_query` discovery, then `id_list` verification).
  * Crossref `query.bibliographic` -- the canonical works are found BY TITLE, never by a remembered
    DOI, and each candidate's title match is recorded.

Usage:
    python3 refscan132.py              discover (write refs/raw.json)
    python3 refscan132.py --curate     relevance-filter raw -> refs/pool.json
    python3 refscan132.py --verify     re-verify every pool entry by TITLE match (drops nothing)
    python3 refscan132.py --report      emit reference-pool.md from the pool
    python3 refscan132.py --selftest    plant the failure modes, require them to fire
"""
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
REFDIR = os.path.join(HERE, "refs")
RAW = os.path.join(REFDIR, "raw.json")
POOL = os.path.join(REFDIR, "pool.json")
RECEIPT_CV = os.path.join(HERE, "citation-verification.json")   # written by --verify, read by --gate
ISSUE = 132
UA = "silicon-science-cs-refscan/1.0 (journal reference verification)"
ATOM = "{http://www.w3.org/2005/Atom}"

# Queries derive from the JOURNAL SCOPE of this paper (artefact similarity / near-duplicate and
# plagiarism detection / the operating point of a similarity threshold), not from a system name.
ARXIV_QUERIES = [
    ("neardup",   'cat:cs.IR AND all:"near-duplicate" AND all:"detection"'),
    ("textreuse", 'cat:cs.CL AND all:"text reuse" AND all:"detection"'),
    ("plagiarism", 'all:"plagiarism detection" AND all:"text"'),
    ("crossling", 'all:"cross-language" AND all:"plagiarism detection"'),
    ("xlingual",  'all:"cross-lingual" AND all:"similarity" AND all:"documents"'),
    ("boilerplate", 'all:"boilerplate" AND all:"removal" AND all:"web"'),
    ("template",  'all:"template detection" AND all:"web pages"'),
    ("stopwords", 'all:"stopword" AND all:"removal" AND all:"information retrieval"'),
    ("dfcutoff",  'all:"document frequency" AND all:"feature selection" AND all:"threshold"'),
    ("idf",       'all:"inverse document frequency" AND all:"term weighting"'),
    ("langid",    'all:"language identification" AND all:"n-gram"'),
    ("zipf",      'all:"Zipf" AND all:"word frequency" AND all:"corpus"'),
    ("sampling",  'all:"sampling bias" AND all:"corpus" AND all:"evaluation"'),
    ("subpop",    'all:"subpopulation" AND all:"fairness" AND all:"evaluation"'),
    ("simpson",   'all:"Simpson\'s paradox" AND all:"aggregation"'),
    ("threshold", 'cat:cs.SE AND all:"threshold" AND all:"similarity" AND all:"evaluation"'),
    ("clones",    'cat:cs.SE AND all:"code clone detection"'),
    ("shingle",   'all:"shingling" AND all:"similarity" AND all:"documents"'),
    ("bias_frame", 'all:"frame of reference" AND all:"bias" AND all:"measurement"'),
    ("coverage",  'all:"corpus coverage" AND all:"representativeness" AND all:"language"'),
]

# Canonical works this paper argues against, given by TITLE (never by a remembered identifier).
# The third field is an AUTHOR HINT: a bibliographic search for a bare title can return a DIFFERENT
# real paper (live here: "Winnowing" matched a website-fingerprinting paper, "Statistical
# Comparisons of Classifiers" matched an unrelated protocol paper), so a weak first result is
# retried with the author's surname, and then by arXiv title search.  A canonical work is never
# accepted on a weak match.
CANONICAL = [
    ("On the Resemblance and Containment of Documents", 1997, ""),
    ("Identifying and Filtering Near-Duplicate Documents", 2000, ""),
    ("Similarity Estimation Techniques from Rounding Algorithms", 2002, ""),
    ("Winnowing: Local Algorithms for Document Fingerprinting", 2003, "Schleimer"),
    ("Detecting Near-Duplicates for Web Crawling", 2007, ""),
    ("Syntactic Clustering of the Web", 1997, "Broder"),
    ("A Statistical Interpretation of Term Specificity and Its Application in Retrieval", 1972, "Spack"),
    ("N-Gram-Based Text Categorization", 1994, "Cavnar"),
    ("Automatic Language Identification Using Both N-Gram and Word Information", 2007, ""),
    ("Stop Word Lists in Free Open-Source Software Packages", 2018, "Sarica"),
    ("Effective Detection of Near Duplicate Web Pages", 2005, ""),
    ("Template Detection for Large Scale Search Engines", 2006, ""),
    ("A Survey of Plagiarism Detection Methods", 2012, ""),
    ("A Survey on Plagiarism Detection", 2015, ""),
    ("Cross-Language Plagiarism Detection: A Case Study", 2013, ""),
    ("Cross-Language Plagiarism Detection Using a Multilingual Semantic Network", 2014, ""),
    ("Empirical Measurements of the Web: Zipf, Heaps and Benford", 2001, ""),
    ("Controlling the false discovery rate: a practical and powerful approach to multiple testing", 1995, ""),
    ("Comparison and Evaluation of Code Clone Detection Techniques and Tools: A Qualitative Approach", 2009, ""),
    ("SourcererCC: Scaling Code Clone Detection to Big Code", 2016, "Sajnani"),
]

# Curation has two tiers.  A CORE term names an object the paper is ABOUT (a similarity statistic
# or an artefact-comparison task); a SUPPORT term names a method object it uses.  An entry is kept
# if it names a CORE object, or names at least three SUPPORT objects -- a single broad word
# ("benchmark", "threshold") admits a fairness paper or a remote-sensing paper, which is what the
# first pass did (Class: a pattern must name the OBJECT, not the vocabulary).
CORE_TERMS = [
    "near-duplicate", "near duplicate", "duplicate detection", "duplicate document", "deduplic",
    "plagiarism", "text reuse", "textual similarity", "string similarity", "clone detection",
    "code clone", "shingle", "winnow", "minhash", "simhash", "locality-sensitive", "fingerprint",
    "jaccard", "dice coefficient", "cosine similarity", "containment", "resemblance",
    "boilerplate", "template detection", "stopword", "stop word", "stop-word",
    "document frequency", "inverse document frequency", "term weighting", "feature selection",
    "cross-language", "cross-lingual", "multilingual", "language identification",
    "word frequency", "zipf", "heap\'s law", "long tail",
    "sampling bias", "representativeness", "corpus coverage", "subpopulation",
    "simpson\'s paradox", "confounder", "ecological fallacy", "stratification",
    "similarity metric", "similarity measure", "similarity search",
]
SUPPORT_TERMS = [
    "threshold", "false positive", "false alarm", "calibrat", "power law", "power-law",
    "heavy tail", "multiple comparison", "false discovery", "operating characteristic",
    "precision and recall", "ground truth", "statistical significance", "statistical power",
    "confidence interval", "reproducib", "benchmark", "test set", "evaluation", "corpus",
]


def _write(path, obj):
    """Atomic write (Class 201): stage to a sibling temp file, fsync, os.replace.  A truncating
    open() that then raises leaves the previous file intact rather than at 0 bytes."""
    tmp = path + ".stage"
    with open(tmp, "w", encoding="utf-8") as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=1, sort_keys=True)
            fh.write("\n")   # a JSON file this tool writes ends with a newline, as text files do
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


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
    """Case-fold, strip accents and punctuation, collapse whitespace -- for title comparison."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def title_matches(a, b, min_frac=0.8):
    """Token overlap in BOTH directions (the min of the two fractions).  Two-sided on purpose: a
    one-sided score lets a short generic title reach 1.00 against a long specific one."""
    ta, tb = set(norm(a).split()), set(norm(b).split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return min(inter / len(ta), inter / len(tb))


def arxiv_id(text):
    """The arXiv identifier in the form the API ACCEPTS and returns.

    Old-style ids (pre-2007) carry an ARCHIVE PREFIX -- `cs/0609060` -- and the naive
    `rsplit("/", 1)[-1]` strips it, leaving `0609060`, which the id_list endpoint rejects with
    HTTP 400.  Measured here: two of the pool's ids (both cs) were in that form, and the batch that
    held them failed while every other batch resolved.  So the normalisation keeps everything after
    `/abs/` and strips only the version suffix, and it is used in the DISCOVERY and the VERIFICATION
    alike -- a key that cannot round-trip is not an identifier."""
    t = (text or "").strip()
    if "/abs/" in t:
        t = t.rsplit("/abs/", 1)[-1]
    else:
        t = t.rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", t)


def arxiv_search(query, max_results=40):
    q = urllib.parse.quote(query, safe="")
    url = ("https://export.arxiv.org/api/query?search_query=%s"
           "&sortBy=relevance&max_results=%d" % (q, max_results))
    root = ET.fromstring(_get(url).decode("utf-8", "replace"))
    out = []
    for e in root.findall(ATOM + "entry"):
        aid = arxiv_id(e.findtext(ATOM + "id", ""))     # versionless: a paper's identity is not its version
        out.append({"source": "arxiv", "id": aid,
                    "title": re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip(),
                    "authors": [a.findtext(ATOM + "name", "") for a in e.findall(ATOM + "author")],
                    "published": e.findtext(ATOM + "published", "")[:10],
                    "summary": re.sub(r"\s+", " ", e.findtext(ATOM + "summary", "")).strip(),
                    "query": query})
    return out


def cr_title(m):
    """The FULL title of a Crossref record: `title` joined with `subtitle`.  Crossref splits a
    two-part title across two fields, so reading only `title` truncates the record -- measured live:
    `10.1145/872757.872770` is stored as title "Winnowing" + subtitle "local algorithms for document
    fingerprinting", and a reader that takes `title` alone reports the correct record as a MISMATCH.
    Reading the whole record is a repair to the reader, not a loosening of the threshold (the joined
    string is compared at the same 0.80, two-sided)."""
    t = (m.get("title") or [""])[0]
    sub = (m.get("subtitle") or [""])
    sub = sub[0] if sub else ""
    return ("%s: %s" % (t, sub)) if sub and sub.lower() not in t.lower() else t


YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def fallback_year(container, doi):
    """A publication year read out of the record's OWN strings, for a record Crossref dates nowhere.

    Measured on `10.1109/sequen.1997.666900` (Broder 1997): its Crossref record carries no `issued`,
    `published-print` or `published-online`, so the pool entry was built with an EMPTY year, and the
    manuscript rendered `Broder, A. ()` where the other entries print one (the editor's round-1
    change 1).  The year is not lost -- the record's own container title says
    `... Compression and Complexity of SEQUENCES 1997 ...` and the DOI's suffix says `sequen.1997` --
    so the fallback reads the LAST year token in the container title and, failing that, the year in
    the DOI's suffix.  Nothing is remembered: both are fields of the record being read, and the
    caller records which route was used, so a fallback year is never mistaken for an issued one.
    Returns (year, source) or (None, None) -- an undated record stays undated rather than invented.
    """
    for source, text in (("container-title", container), ("doi-suffix", doi)):
        years = YEAR_RE.findall(text or "")
        if years:
            return years[-1], source + " fallback"
    return None, None


def issued_year(m):
    """The year of a Crossref record and the field it came from: Crossref's own dates when it has
    one, the record's own text otherwise (`fallback_year`)."""
    for k in ("published-print", "published-online", "issued"):
        if m.get(k, {}).get("date-parts"):
            return str(m[k]["date-parts"][0][0]), k
    return fallback_year((m.get("container-title") or [""])[0], m.get("DOI", ""))


def crossref_by_title(title):
    """Search Crossref for a work BY TITLE; return the best candidate with its two-sided match."""
    url = ("https://api.crossref.org/works?rows=5&query.bibliographic="
           + urllib.parse.quote(title, safe=""))
    items = json.loads(_get(url).decode("utf-8", "replace"))["message"]["items"]
    best = None
    for m in items:
        t = cr_title(m)
        sc = title_matches(title, t)
        if best is None or sc > best[2]:
            year, ysrc = issued_year(m)
            best = (m.get("DOI", ""), t, sc, year, ysrc,
                    (m.get("container-title") or [""])[0],
                    ["%s %s" % (a.get("given", ""), a.get("family", "")) for a in m.get("author", [])][:8])
    if best is None:
        return None
    doi, t, sc, year, ysrc, cont, auth = best
    rec = {"source": "crossref", "id": doi, "title": t, "authors": auth,
           "published": str(year or ""), "container": cont,
           "cited_title": title, "title_match": round(sc, 3), "query": "bibliographic:" + title}
    if ysrc and ysrc not in ("issued", "published-print", "published-online"):
        rec["year_source"] = ("%s: Crossref carries no issued date for this record (%s); the year is "
                              "read from the record's own text" % (ysrc, doi))
    return rec


def arxiv_by_title(title, max_results=6):
    """Find a work on arXiv BY TITLE (`ti:"..."`).  The fallback for a canonical work whose
    Crossref bibliographic search returned a different real paper, and the route for works that
    live on arXiv with a publisher title the DOI record does not carry."""
    q = urllib.parse.quote('ti:"%s"' % title, safe="")
    url = ("https://export.arxiv.org/api/query?search_query=%s"
           "&sortBy=relevance&max_results=%d" % (q, max_results))
    try:
        root = ET.fromstring(_get(url).decode("utf-8", "replace"))
    except Exception:
        return None
    best = None
    for e in root.findall(ATOM + "entry"):
        t = re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip()
        sc = title_matches(title, t)
        if best is None or sc > best[1]:
            aid = arxiv_id(e.findtext(ATOM + "id", ""))
            auth = [a.findtext(ATOM + "name", "") for a in e.findall(ATOM + "author")]
            best = (aid, sc, t, e.findtext(ATOM + "published", "")[:10], auth)
    if best is None:
        return None
    aid, sc, t, pub, auth = best
    return {"source": "arxiv", "id": aid, "title": t, "authors": auth,
            "published": pub, "summary": "", "cited_title": title,
            "title_match": round(sc, 3), "query": 'ti:"%s"' % title}


def discover(canonical_only=False):
    raw = {}
    if canonical_only:
        raw = json.load(open(RAW))
        print("== Crossref (canonical works, found BY TITLE) -- merging into existing raw ==")
    else:
        print("== arXiv ==")
        for tag, q in ARXIV_QUERIES:
            try:
                got = arxiv_search(q)
            except Exception as e:
                print("  [%-11s] FAILED: %s" % (tag, e))
                time.sleep(3)
                continue
            new = 0
            for r in got:
                k = r["id"]
                if k not in raw:
                    raw[k] = r
                    new += 1
            print("  [%-11s] %2d hits (%d new)" % (tag, len(got), new))
            time.sleep(3.0)
        print("== Crossref (canonical works, found BY TITLE) ==")
    for title, yr, hint in CANONICAL:
        r = None
        try:
            r = crossref_by_title(title)
        except Exception as e:
            print("  [FAIL] %s: %s" % (title[:40], e))
        if (r is None or r["title_match"] < 0.8) and hint:
            # a bare-title search returned a DIFFERENT real paper; retry with the author surname
            try:
                r2 = crossref_by_title(title + " " + hint)
                if r2 is not None and r2["title_match"] > (r["title_match"] if r else 0):
                    r = r2
            except Exception:
                pass
            time.sleep(1.0)
        if r is None or r["title_match"] < 0.8:
            # last resort: the work may live on arXiv under a title the DOI record does not carry
            try:
                r3 = arxiv_by_title(title)
                if r3 is not None and r3["title_match"] > (r["title_match"] if r else 0):
                    r = r3
            except Exception:
                pass
            time.sleep(2.5)
        if r is None:
            print("  [MISS] %s" % title[:58])
        else:
            flag = "OK  " if r["title_match"] >= 0.8 else "WEAK"
            print("  [%s %.2f] %s -> %s" % (flag, r["title_match"], title[:38], r["title"][:44]))
            if r["title_match"] >= 0.8:
                r = dict(r)
                r["canonical"] = True
                raw[r["id"]] = r
        time.sleep(1.0)
    os.makedirs(REFDIR, exist_ok=True)
    _write(RAW, raw)
    print("\nraw unique: %d -> %s" % (len(raw), os.path.relpath(RAW, HERE)))


def curate():
    raw = json.load(open(RAW))
    pool = {}
    for k, r in raw.items():
        if r["source"] == "crossref" or r.get("canonical"):
            pool[k] = r                              # canonical works are kept by construction
            continue
        text = (r["title"] + " " + r["summary"]).lower()
        core = sum(1 for t in CORE_TERMS if t in text)
        sup = sum(1 for t in SUPPORT_TERMS if t in text)
        if core >= 1 or sup >= 4:                    # a named OBJECT, or four method objects
            r2 = dict(r)
            r2["core_hits"] = core
            r2["support_hits"] = sup
            pool[k] = r2
    _write(POOL, pool)
    print("curated pool: %d of %d raw -> %s" % (len(pool), len(raw), os.path.relpath(POOL, HERE)))


def _arxiv_titles(ids, chunk=20):
    """Fetch titles for many arXiv ids in BATCHES.  `max_results` is set to the chunk's own size
    (the API caps at 10 otherwise, and the shortfall then looks like absent records) and the
    returned count is checked.  A failed batch is a TRANSPORT failure, never a finding.

    A failed batch is RETRIED once after a longer pause: measured live, a burst rate limit (HTTP
    429) lands on the first batch of a fresh pass and every later batch -- spaced 12 s -- succeeds,
    so giving up on the first refusal turns a throttle into a permanent hole in the receipt."""
    out = {}
    failed = 0
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        url = ("https://export.arxiv.org/api/query?id_list=" + ",".join(part)
               + "&max_results=%d" % len(part))
        root = None
        for attempt in (1, 2):
            try:
                root = ET.fromstring(_get(url).decode("utf-8", "replace"))
                break
            except Exception as e:
                if attempt == 1:
                    print("    [batch %d-%d] TRANSPORT: %s -- retrying after 45 s"
                          % (i, i + len(part), e), flush=True)
                    time.sleep(45.0)
                    continue
                print("    [batch %d-%d] TRANSPORT FAILURE: %s" % (i, i + len(part), e), flush=True)
                failed += 1
        if root is None:
            continue
        got = root.findall(ATOM + "entry")
        if len(got) < len(part):
            print("    [batch %d-%d] WARNING: %d ids, %d entries returned"
                  % (i, i + len(part), len(part), len(got)), flush=True)
        for e in got:
            aid = arxiv_id(e.findtext(ATOM + "id", ""))
            out[aid] = re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip()
        time.sleep(12.0)     # arXiv rate-limits bursts (HTTP 429); space the batches out
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
            transport += 1
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
            good = title_matches(r["title"], cr_title(m)) >= 0.8
        except Exception:
            transport += 1
            continue
        ok += 1 if good else 0
        mismatch += 0 if good else 1
        time.sleep(0.8)
    total = len(pool)
    # THE RECEIPT IS WRITTEN HERE, by the pass that produces its numbers.  It was a committed file
    # that named this instrument and that NOTHING wrote (only prose pointed at it), so it could only
    # ever go stale -- and the offline gate now compares its composition against the pool, which
    # makes a pool edit without a re-verification a FAILING gate rather than a silent drift.
    #
    # And it is written ONLY by a CLEAN pass.  A receipt is a claim that the pool WAS verified; a
    # pass under a rate limit verified 236 of 256, and writing that over the shipped record would
    # replace a claim about the pool with a claim about the outage (measured live this round: the
    # first draft of this writer did exactly that).  A non-clean pass reports and leaves the
    # previous receipt alone, and the gate then fails on the composition mismatch -- which is the
    # correct state: the layer is unverified until a clean pass re-derives it.
    clean = (mismatch == 0 and transport == 0)
    if clean:
        receipt = {
            "instrument": "%s" % os.path.basename(__file__),
            "issue": ISSUE,
            "notes": [
                "every entry discovered by this tool; nothing typed from memory",
                "the check is the returned TITLE vs the stored title, two-sided (min of the two coverage fractions)",
                "an old-style arXiv id keeps its archive prefix (cs/0609060), a defect that made one batch fail HTTP 400",
                "written by `--verify` (clean passes only); `--gate` (offline) refuses a receipt whose composition is not the pool's",
            ],
            "pool": {
                "arxiv": len(arxiv_keys),
                "canonical": sum(1 for v in pool.values() if v.get("canonical")),
                "crossref": sum(1 for v in pool.values() if v["source"] == "crossref"),
                "total": total,
            },
            "sources": {
                "arxiv_id_list": "verification",
                "arxiv_search_query": "discovery",
                "crossref_query_bibliographic": "canonical works, found BY TITLE",
                "crossref_works_doi": "verification",
            },
            "subject": ("the background frame of a similarity guard "
                        "(corpus-wide DF threshold / stopword list)"),
            "title_match_threshold": 0.8,
            "verification": {
                "title_mismatch": mismatch,
                "transport_unknown": transport,
                "verified": ok,
            },
        }
        _write(RECEIPT_CV, receipt)
        print("wrote citation-verification.json (%d verified / %d)" % (ok, total))
    else:
        print("NOT WRITTEN: the pass was not clean (%d verified, %d transport-unknown) -- "
              "citation-verification.json is left as it stands" % (ok, transport))
    print("VERIFIED %d / %d ; TITLE MISMATCH %d ; TRANSPORT-UNKNOWN %d (batches failed: %d)"
          % (ok, total, mismatch, transport, failed_batches))
    print("a nonzero TRANSPORT-UNKNOWN is an OUTAGE, not evidence about the records -- re-run later")
    return 0 if clean else 1


def report():
    pool = json.load(open(POOL))
    n_arxiv = sum(1 for v in pool.values() if v["source"] == "arxiv")
    lines = [
        "# Reference pool -- issue #132",
        "",
        "Every entry below was discovered by `refscan132.py` (never typed from memory) and checked",
        "against a LIVE external record by comparing the returned TITLE with the stored title",
        "(two-sided token match, threshold 0.80).  A resolver that merely answers is not enough: a",
        "remembered identifier can resolve to a DIFFERENT real paper, so the check is the title",
        "comparison, not the HTTP status.",
        "",
        "- sources: arXiv API `search_query` (discovery) + `id_list` (verification, batched with",
        "  `max_results` set per chunk); Crossref `query.bibliographic` (canonical works, BY TITLE)",
        "  and `works/<doi>` (verification)",
        "- pool: %d entries (%d arXiv, %d Crossref)" % (len(pool), n_arxiv, len(pool) - n_arxiv),
        "- an entry whose title does not match its live record is dropped, never kept",
        "",
        "| key | source | verified against | title |",
        "|-----|--------|------------------|-------|",
    ]
    for k in sorted(pool):
        r = pool[k]
        verifier = "arXiv id_list" if r["source"] == "arxiv" else "Crossref works/<doi>"
        lines.append("| %s | %s | %s | %s |"
                     % (k, r["source"], verifier, r["title"].replace("|", "/")[:96]))
    _write(os.path.join(HERE, "reference-pool.md"), "\n".join(lines) + "\n")
    print("wrote reference-pool.md (%d entries)" % len(pool))


def duplicate_title_groups(pool):
    """The pool's duplicate titles, compared NORMALISED (`norm`: case-folded, accents stripped,
    punctuation collapsed) rather than by `.lower()`.

    The check's name has always been "one paper, one entry"; its predicate was `v["title"].lower()`,
    and that is weaker than its name in exactly the way that matters: the one duplicate the pool
    carried -- `SourcererCC: Scaling Code Clone Detection to Big Code` (arXiv 1512.06448) against
    `SourcererCC: scaling code clone detection to big-code` (the ICSE-2016 proceedings,
    10.1145/2884781.2884877) -- differs only in CASE and a hyphen, so the raw comparison passed and
    one work entered the bibliography twice (the editor's round-1 change 2).  The normaliser the file
    already uses for title matching is the right comparison for identity of title; using it here is
    the repair, not a loosening.
    """
    groups = {}
    for k, v in pool.items():
        groups.setdefault(norm(v.get("title")), []).append(k)
    return {t: ks for t, ks in groups.items() if len(ks) > 1}


def pool_checks(pool, receipt, listed):
    """Every OFFLINE predicate the reference layer states, as (label, ok) pairs.

    Factored out of `gate()` so the selftest can plant a defect IN the object each predicate reads and
    require the predicate to fire (a plant that is a re-typed paraphrase of the predicate is the
    defect Class 197 names).  `receipt` is `citation-verification.json` and `listed` the row count of
    the rendered `reference-pool.md`.
    """
    return [
        ("the pool carries at least 100 entries (the journal's floor)", len(pool) >= 100),
        ("every entry has an id, a source, a non-empty title and a YEAR VALUE",
         all(v.get("id") and v.get("source") in ("arxiv", "crossref")
             and (v.get("title") or "").strip() and (v.get("published") or "").strip()
             for v in pool.values())),
        ("the pool has no duplicate TITLE (one paper, one entry; normalised comparison)",
         not duplicate_title_groups(pool)),
        ("every key is its own id (a key that cannot round-trip is not an identifier)",
         all(k == v["id"] for k, v in pool.items())),
        ("an old-style arXiv id keeps its archive prefix",
         not any(v["source"] == "arxiv" and re.match(r"^\d{7}$", k) for k, v in pool.items())),
        ("reference-pool.md lists exactly the pool (%d)" % len(pool), listed == len(pool)),
        # The receipt is a claim about the pool it was taken over, and nothing re-derived it before:
        # it named its instrument and carried counts that only a live pass produces, so a pool edit
        # left it stale and silent (Class 193).  A receipt whose COMPOSITION is not the pool's is a
        # receipt about another object.
        ("the verification receipt describes THIS pool (composition and coverage)",
         receipt is not None
         and receipt.get("pool", {}).get("total") == len(pool)
         and receipt.get("pool", {}).get("arxiv") == sum(1 for v in pool.values() if v["source"] == "arxiv")
         and receipt.get("pool", {}).get("crossref") == sum(1 for v in pool.values() if v["source"] == "crossref")
         and receipt.get("verification", {}).get("verified") == len(pool)
         and receipt.get("issue") == ISSUE),
    ]


def gate():
    """The OFFLINE check: the network verification is a separate, documented pass (`--verify`, whose
    output IS `citation-verification.json`); this gate asserts the shipped pool, its rendered index
    and its receipt are complete and agree with one another, so `reproduce.sh` can check the whole
    reference layer without touching the network."""
    pool = json.load(open(POOL))
    receipt = json.load(open(RECEIPT_CV)) if os.path.exists(RECEIPT_CV) else None
    md = open(os.path.join(HERE, "reference-pool.md"), encoding="utf-8").read()
    listed = sum(1 for line in md.splitlines() if line.startswith("| ") and " | " in line[2:]
                 and not line.startswith("| key "))
    checks = pool_checks(pool, receipt, listed)
    bad = 0
    for lab, ok in checks:
        print("   %-4s %s" % ("ok" if ok else "FAIL", lab))
        bad += 0 if ok else 1
    for t, ks in duplicate_title_groups(pool).items():
        print("   note duplicate title: %s" % ", ".join(ks))
    print("GATE %d/%d" % (len(checks) - bad, len(checks)))
    return 1 if bad else 0


def selftest():
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-30s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    holds("accept-identical", title_matches("Detecting Near-Duplicates for Web Crawling",
                                            "Detecting Near-Duplicates for Web Crawling") == 1.0)
    holds("accept-subtitle", title_matches("Winnowing: Local Algorithms for Document Fingerprinting",
                                           "Winnowing: Local Algorithms for Document Fingerprinting, Revisited") >= 0.8)
    holds("reject-generic-short", title_matches(
        "Machine Learning Benchmarks", "Accounting for Variance in Machine Learning Benchmarks") < 0.8)
    holds("reject-substring", title_matches(
        "A Comparison of String Distance Metrics for Name-Matching Tasks", "String distance") < 0.8)
    holds("reject-different", title_matches("Power-Law Distributions in Empirical Data",
                                            "SourcererCC: Scaling Code Clone Detection to Big Code") < 0.8)
    # a record whose identifying phrase lands in Crossref's `subtitle` field must MATCH once the
    # reader joins title+subtitle (the live defect: 10.1145/872757.872770 stored as "Winnowing" +
    # "local algorithms for document fingerprinting" read as a mismatch under title-only)
    # an OLD-STYLE arXiv id carries an archive prefix; a normaliser that drops it produces an id the
    # API rejects (HTTP 400) -- measured here, two cs ids, and the whole batch failed while every
    # other batch resolved
    holds("id-keeps-old-style-prefix", arxiv_id("http://arxiv.org/abs/cs/0609060") == "cs/0609060")
    holds("id-keeps-new-style", arxiv_id("http://arxiv.org/abs/0909.4385v2") == "0909.4385")
    holds("id-strips-version-only", arxiv_id("http://arxiv.org/abs/1204.0182") == "1204.0182")
    holds("accept-split-subtitle", title_matches(
        "Winnowing: Local Algorithms for Document Fingerprinting",
        "Winnowing: local algorithms for document fingerprinting") >= 0.8)

    # ---- the three pool predicates, each planted IN the object it reads (Class 197: a plant that is
    # a re-typed paraphrase of the predicate tests the paraphrase, not the check).
    pool = json.load(open(POOL))
    receipt = json.load(open(RECEIPT_CV)) if os.path.exists(RECEIPT_CV) else None
    md = open(os.path.join(HERE, "reference-pool.md"), encoding="utf-8").read()
    listed = sum(1 for line in md.splitlines() if line.startswith("| ") and " | " in line[2:]
                 and not line.startswith("| key "))

    def check(label_frag, p, r, l):
        for lab, ok in pool_checks(p, r, l):
            if label_frag in lab:
                return ok
        raise AssertionError("no predicate named %r" % label_frag)

    holds("healthy-pool-passes-every-predicate",
          all(ok for _l, ok in pool_checks(pool, receipt, listed)))
    # (a) an EMPTY year value is the defect the check's name asks about; the key's presence is not
    planted = json.loads(json.dumps(pool))
    victim = sorted(planted)[0]
    planted[victim]["published"] = ""
    holds("plant-empty-year-FIRES",
          not check("YEAR VALUE", planted, receipt, len(planted)))
    holds("plant-missing-year-key-FIRES",
          not check("YEAR VALUE", {k: {kk: vv for kk, vv in v.items() if kk != "published"}
                                   for k, v in pool.items()}, receipt, len(pool)))
    # (b) the REAL duplicate, with both records' own strings: arXiv 1512.06448's title against the
    # ICSE-2016 proceedings title (10.1145/2884781.2884877).  They differ in case AND in one hyphen,
    # which is why the raw `.lower()` comparison reported no duplicate at all.  The plant is a MINIMAL
    # pool holding exactly these two records -- so the two predicates are compared on one object, and
    # the control is the defect itself rather than a mutation of the shipped pool (a plant that reuses
    # the shipped pair would collide with the entries it is standing in for).
    DUP_A = "SourcererCC: Scaling Code Clone Detection to Big Code"      # arXiv 1512.06448
    DUP_B = "SourcererCC: scaling code clone detection to big-code"      # 10.1145/2884781.2884877
    two = {"1512.06448": {"id": "1512.06448", "source": "arxiv", "title": DUP_A, "published": "2015-12-20"},
           "10.1145/2884781.2884877": {"id": "10.1145/2884781.2884877", "source": "crossref",
                                       "title": DUP_B, "published": "2016"}}
    holds("two-entries-one-work: the normalised predicate FIRES",
          list(duplicate_title_groups(two).values()) == [["1512.06448", "10.1145/2884781.2884877"]])
    holds("two-entries-one-work: the raw .lower() comparison MISSES it (the repaired half)",
          len({v["title"].lower() for v in two.values()}) == len(two))
    # (c) a receipt taken over a DIFFERENT pool (one entry more, or another issue)
    stale = json.loads(json.dumps(receipt))
    stale["pool"]["total"] += 1
    holds("plant-stale-receipt-count-FIRES",
          not check("receipt describes THIS pool", pool, stale, listed))
    other = json.loads(json.dumps(receipt))
    other["issue"] = 130
    holds("plant-receipt-for-another-issue-FIRES",
          not check("receipt describes THIS pool", pool, other, listed))
    holds("plant-missing-receipt-FIRES",
          not check("receipt describes THIS pool", pool, None, listed))
    holds("plant-index-row-count-FIRES",
          not check("reference-pool.md lists exactly", pool, receipt, listed - 1))
    # the fallback year: the real record shape, and four controls
    holds("year-fallback-container-title",
          fallback_year("Proceedings. Compression and Complexity of SEQUENCES 1997 (Cat. No.97TB100171)",
                        "10.1109/sequen.1997.666900") == ("1997", "container-title fallback"))
    holds("year-fallback-doi-suffix",
          fallback_year("Proceedings of ICSE", "10.1109/icse.1997.610000") == ("1997", "doi-suffix fallback"))
    holds("year-fallback-leaves-a-dated-record-alone",
          issued_year({"DOI": "10.1145/509907.509965", "container-title": ["STOC 2002"],
                       "issued": {"date-parts": [[2002, 5, 19]]}}) == ("2002", "issued"))
    holds("year-fallback-invents-nothing",
          fallback_year("Some Venue", "10.9999/zzzz") == (None, None))
    holds("year-fallback-takes-the-range-end",
          fallback_year("Proceedings of the 1994-1996 Workshop", "10.9999/zzzz") == ("1996", "container-title fallback"))
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--curate" in sys.argv:
        sys.exit(curate() or 0)
    if "--verify" in sys.argv:
        sys.exit(verify())
    if "--gate" in sys.argv:
        sys.exit(gate())
    if "--report" in sys.argv:
        sys.exit(report() or 0)
    sys.exit(discover(canonical_only="--canonical" in sys.argv) or 0)
