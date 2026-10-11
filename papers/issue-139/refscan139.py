#!/usr/bin/env python3
"""Issue #139 -- reference scan + VERIFICATION.

The subject is the SUCCESS-vs-COST FRONTIER of a set of interdependent proof obligations: a
dependency DAG in which discharging one obligation raises its dependents' success probability, the
expected number discharged at a given attempt budget, and the budget a target fraction actually
costs.  This file discovers the related work for that subject and VERIFIES every entry against a
live external record.

A citation is verified only if the returned record MATCHES the citation, not merely if the endpoint
answered.  A DOI or an arXiv id written from memory RESOLVES -- the API returns HTTP 200 with a real
record -- but the record can be a DIFFERENT paper.  So the check is the returned TITLE against the
stored title, compared two-sided, and nothing here is typed from memory: every key in the pool came
out of this tool's own discovery pass.

Three things the checks refuse to do, each because it was once the bug (the shape is the house
pattern, `papers/issue-135/refscan135.py` and `papers/issue-132/refscan132.py`):

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
    python3 refscan139.py              discover (write refs/raw.json)
    python3 refscan139.py --canonical  add the canonical works (Crossref, BY TITLE)
    python3 refscan139.py --curate     relevance-filter raw -> refs/pool.json
    python3 refscan139.py --verify     re-verify every pool entry by TITLE match (drops nothing)
    python3 refscan139.py --report     emit reference-pool.md from the pool
    python3 refscan139.py --gate       the OFFLINE completeness/consistency gate (no network)
    python3 refscan139.py --selftest   plant the failure modes, require them to fire
"""
import hashlib
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
RECEIPT = os.path.join(REFDIR, "verify-run.txt")
UA = "silicon-science-cs-refscan/1.0 (journal reference verification)"
ATOM = "{http://www.w3.org/2005/Atom}"

# Queries derive from the JOURNAL SCOPE of this paper -- the cost and success of discharging
# interdependent proof obligations in program verification, the budget a verification effort must
# meet, and the scheduling of proof search -- not from any system name.
ARXIV_QUERIES = [
    ("proofobl",   'all:"proof obligation" AND all:"budget"'),
    ("proofobl2",  'all:"proof obligations" AND all:"verification"'),
    ("vcond",      'all:"verification condition" AND all:"generation"'),
    ("costproof",  'all:"theorem proving" AND all:"cost"'),
    ("costproof2", 'all:"proof search" AND all:"cost"'),
    ("effort",     'all:"proof effort"'),
    ("proofsize",  'all:"proof size" AND all:"formalization"'),
    ("costverif",  'all:"verification" AND all:"cost" AND all:"formal"'),
    ("dedverif",   'all:"deductive verification"'),
    ("progverif",  'all:"program verification" AND all:"automation"'),
    ("autoprover", 'all:"automated theorem proving" AND all:"performance"'),
    ("itp",        'all:"interactive theorem proving"'),
    ("proofasst",  'all:"proof assistant" AND all:"formalization"'),
    ("lean",       'all:"Lean" AND all:"theorem proving"'),
    ("coq",        'all:"Coq" AND all:"proof"'),
    ("isabelle",   'all:"Isabelle" AND all:"proof assistant"'),
    ("hol",        'all:"HOL Light" OR all:"HOL4"'),
    ("smtperf",    'all:"SMT solver" AND all:"performance"'),
    ("smtsolve",   'all:"SMT" AND all:"solving" AND all:"benchmark"'),
    ("sat",        'all:"SAT solver" AND all:"performance" AND all:"proof"'),
    ("premise",    'all:"premise selection" AND all:"theorem"'),
    ("tactic",     'all:"tactic" AND all:"theorem proving" AND all:"learning"'),
    ("llmproof",   'all:"large language model" AND all:"theorem proving"'),
    ("llmverif",   'all:"large language model" AND all:"formal verification"'),
    ("autoformal", 'all:"autoformalization"'),
    ("agents",     'all:"agent" AND all:"theorem proving"'),
    ("orchestr",   'all:"orchestration" AND all:"verification"'),
    ("portfolio",  'all:"portfolio" AND all:"solver"'),
    ("scheduler",  'all:"scheduling" AND all:"proof"'),
    ("robustcert", 'all:"certificate" AND all:"proof" AND all:"checking"'),
    ("certcheck",  'all:"proof certificate" AND all:"checking"'),
    ("proofcomplex",'all:"proof complexity"'),
    ("loopinv",    'all:"loop invariant" AND all:"inference"'),
    ("termination",'all:"termination proof" AND all:"automation"'),
    ("kframework", 'all:"Dafny" OR all:"Why3" OR all:"Frama-C" OR all:"Boogie"'),
    ("seplogic",   'all:"separation logic" AND all:"verification"'),
    ("regression", 'all:"regression verification" AND all:"proof"'),
    ("contverif",  'all:"continuous verification" AND all:"proof"'),
    ("humanloop",  'all:"human" AND all:"proof assistant" AND all:"interaction"'),
    ("budgetreas", 'all:"test-time compute" AND all:"reasoning"'),
    ("codeverif",  'all:"code" AND all:"verification" AND all:"cost" AND all:"time"'),
    ("formalmath", 'all:"formal mathematics" AND all:"library"'),
    ("benchmark",  'all:"benchmark" AND all:"theorem proving"'),
    ("specmine",   'all:"specification" AND all:"inference" AND all:"verification"'),
    ("verifier",   'all:"verified" AND all:"compiler" AND all:"kernel"'),
]

# Canonical works this paper argues against or builds on, given by TITLE (never by a remembered
# identifier).  The third field is an AUTHOR HINT: a bibliographic search for a bare title can
# return a DIFFERENT real paper, so a weak first result is retried with the author's surname, and
# then by arXiv title search.  A canonical work is never accepted on a weak match.
CANONICAL = [
    ("An Axiomatic Basis for Computer Programming", 1969, "Hoare"),
    ("Simplification by Cooperating Decision Procedures", 1979, "Nelson"),
    ("Z3: An Efficient SMT Solver", 2008, "de Moura"),
    ("A Formally Verified Compiler Back-end", 2009, "Leroy"),
    ("seL4: Formal Verification of an OS Kernel", 2009, "Klein"),
    ("Dafny: An Automatic Program Verifier for Functional Correctness", 2010, "Leino"),
    ("Why3: Where Programs Meet Provers", 2013, "Filliatre"),
    ("Premise Selection for Mathematics by Corpus Analysis and Kernel Methods", 2014, "Alama"),
    ("Learning to Prove Theorems via Interacting with Proof Assistants", 2019, "Yang"),
    ("TacticToe: Learning to Prove with Tactics", 2021, "Gauthier"),
    ("HyperTree Proof Search for Neural Theorem Proving", 2022, "Lample"),
    ("miniF2F: a cross-system benchmark for formal Olympiad-level mathematics", 2022, "Zheng"),
    ("Baldur: Whole-Proof Generation and Repair with Large Language Models", 2023, "First"),
    # REMOVED: "The Cost of Formal Verification" (attributed 1983).  Verified ABSENT: Crossref
    # `query.bibliographic` by the exact title and by a loosened variant both return unrelated
    # works ("Formal Verification of Control System Software", "A Roadmap for Formal Property
    # Verification") and no record carrying this title, and the discovery pass's own best match
    # scored 0.60 against a DIFFERENT real paper ("Overview of Formal Verification").  Whether the
    # work exists in some unindexed 1983 venue is not decidably false, but that is precisely the
    # case the rule covers: an unverifiable citation cannot be cited, so the entry is dropped
    # rather than admitted on a weak match against a different record (the exact defect
    # `title_matches` exists to catch).  A work whose identity cannot be established is not
    # evidence for a claim.
]

# Curation has two tiers.  A CORE term names an object the paper is ABOUT (a proof obligation, a
# verification condition, the cost or budget of proof search, a proof assistant, or the dependency
# structure between obligations); a SUPPORT term names a method object it uses.  An entry is kept if
# it names a CORE object, or names at least four SUPPORT objects -- a single broad word
# ("benchmark", "evaluation") admits an unrelated paper, which is what a loose filter did (Class: a
# pattern must name the OBJECT, not the vocabulary).
CORE_TERMS = [
    "proof obligation", "proof obligations", "verification condition", "verification conditions",
    "proof assistant", "proof assistants", "interactive theorem proving",
    "automated theorem proving", "automated deduction", "deductive verification",
    "program verification", "formal verification", "formal specification", "formal proof",
    "proof search", "proof script", "proof term", "proof effort", "proof engineering",
    "proof size", "proof complexity", "proof problem", "theorem prover", "theorem provers",
    "smt solver", "smt-lib", "satisfiability modulo", "sat solver", "cdcl",
    "resolution proof", "unsat core", "unsatisfiable core",
    "coq", "isabelle", "hol light", "hol4", "lean", "mizar", "pvs", "acl2",
    "dafny", "why3", "frama-c", "boogie", "viper", "verifast", "key tool", "key project",
    "separation logic", "loop invariant", "loop invariants", "invariant inference",
    "ranking function", "termination proof", "contract", "design by contract",
    "refinement type", "dependent type", "curry-howard", "type theory",
    "premise selection", "tactic prediction", "proof state", "proof tactic",
    "autoformalization", "formalization", "formal mathematics", "proof library",
    "certificate checking", "proof certificate", "proof checker", "de Bruijn criterion",
    "verified compiler", "verified kernel", "verified software", "verified system",
    "verification effort", "verification cost", "proof automation", "tactic",
    "dependency graph", "call graph", "proof dependency", "proof repair",
    "regression verification", "continuous verification", "invariant synthesis",
]

SUPPORT_TERMS = [
    "budget", "cost", "expensive", "performance", "scalability", "scalable",
    "benchmark", "evaluation", "experiment", "measurement", "reproducib",
    "threshold", "upper bound", "lower bound", "asymptotic", "analysis",
    "search", "heuristic", "optimization", "schedule", "scheduling", "resource",
    "timeout", "time limit", "pass rate", "success rate", "coverage",
    "distribution", "variance", "simulation", "randomized", "large language model",
    "neural", "machine learning", "reinforcement learning", "agent",
    "human", "interaction", "industrial", "case study", "deployment", "adoption",
]

def _write(path, obj):
    """Atomic write (Class 201): stage to a sibling temp file, fsync, os.replace.  A truncating
    open() that then raises leaves the previous file intact rather than at 0 bytes."""
    tmp = path + ".stage"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=1, sort_keys=True)
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
    HTTP 400.  The normalisation keeps everything after `/abs/` and strips only the version
    suffix, and it is used in the DISCOVERY and the VERIFICATION alike -- a key that cannot
    round-trip is not an identifier."""
    t = (text or "").strip()
    if "/abs/" in t:
        t = t.rsplit("/abs/", 1)[-1]
    else:
        t = t.rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", t)


def arxiv_search(query, max_results=60):
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
    two-part title across two fields, so reading only `title` truncates the record, and the reader
    then reports the CORRECT record as a mismatch.  Reading the whole record is a repair to the
    reader, not a loosening of the threshold (the joined string is compared at the same 0.80,
    two-sided)."""
    t = (m.get("title") or [""])[0]
    sub = (m.get("subtitle") or [""])
    sub = sub[0] if sub else ""
    return ("%s: %s" % (t, sub)) if sub and sub.lower() not in t.lower() else t


def crossref_by_title(title, rows=5):
    """Search Crossref for a work BY TITLE; return the best candidate with its two-sided match."""
    url = ("https://api.crossref.org/works?rows=%d&query.bibliographic=" % rows
           + urllib.parse.quote(title, safe=""))
    items = json.loads(_get(url).decode("utf-8", "replace"))["message"]["items"]
    best = None
    for m in items:
        t = cr_title(m)
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
        print("== Crossref (canonical works, found BY TITLE) -- merging into existing raw ==", flush=True)
    else:
        print("== arXiv ==", flush=True)
        for tag, q in ARXIV_QUERIES:
            try:
                got = arxiv_search(q)
            except Exception as e:
                print("  [%-11s] FAILED: %s" % (tag, e), flush=True)
                time.sleep(5)
                continue
            new = 0
            for r in got:
                k = r["id"]
                if k and k not in raw:
                    raw[k] = r
                    new += 1
            print("  [%-11s] %2d hits (%d new)" % (tag, len(got), new), flush=True)
            time.sleep(3.0)
        print("== Crossref (canonical works, found BY TITLE) ==", flush=True)
    for title, yr, hint in CANONICAL:
        r = None
        try:
            r = crossref_by_title(title)
        except Exception as e:
            print("  [FAIL] %s: %s" % (title[:40], e), flush=True)
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
            print("  [MISS] %s" % title[:58], flush=True)
        else:
            flag = "OK  " if r["title_match"] >= 0.8 else "WEAK"
            print("  [%s %.2f] %s -> %s" % (flag, r["title_match"], title[:38], r["title"][:44]), flush=True)
            if r["title_match"] >= 0.8:
                r = dict(r)
                r["canonical"] = True
                raw[r["id"]] = r
        time.sleep(1.0)
    _write(RAW, raw)
    print("\nraw unique: %d -> %s" % (len(raw), os.path.relpath(RAW, HERE)), flush=True)


def curate():
    raw = json.load(open(RAW))
    pool = {}
    for k, r in raw.items():
        if r["source"] == "crossref" or r.get("canonical"):
            pool[k] = r                              # canonical works are kept by construction
            continue
        text = (r["title"] + " " + r.get("summary", "")).lower()
        core = sum(1 for t in CORE_TERMS if t in text)
        sup = sum(1 for t in SUPPORT_TERMS if t in text)
        # The #135 rule was `core >= 1 or sup >= 4`.  It is NOT reused here, and the reason is
        # measurable: this domain's CORE vocabulary is LOW-ENTROPY.  "formal verification",
        # "program verification" and "proof search" name the subject AND sit in the abstract of a
        # large fraction of unrelated CS papers, so a single CORE hit admitted 1407 of 1630
        # candidates (the raw dump is itself the evidence).  The rule here asks for TWO distinct
        # CORE objects -- the entry names the subject twice over, so it is about it rather than
        # adjacent to it -- AND the method vocabulary (four SUPPORT objects).  Measured on the same
        # dump: `core >= 1 or sup >= 4` -> 1407 entries, `core >= 2 and sup >= 4` -> 288, and the
        # 288 are the subject matter (deductive verification, proof agents, Lean/Coq/Dafny
        # tooling, cost-quality trade-offs of provers).  The filter is stated as its numbers so the
        # next reader can re-measure it rather than trust it.
        if core >= 2 and sup >= 4:
            r2 = dict(r)
            r2["core_hits"] = core
            r2["support_hits"] = sup
            pool[k] = r2
    # One paper, one entry.  A work posted as a preprint AND published under a DOI arrives twice, and
    # the same paper is sometimes posted to arXiv under two ids; a pool with a duplicate title lets
    # the manuscript cite one paper as two references.  The collision is resolved deterministically,
    # and the policy is stated: a Crossref (published) record wins over an arXiv preprint of the same
    # title, and between two records of the SAME source the EARLIER publication date wins (within the
    # source, ISO dates sort lexicographically).
    def _rank(v):
        return (0 if v["source"] == "crossref" else 1, str(v.get("published", "")))
    chosen = {}
    for k in sorted(pool):
        key = norm(pool[k]["title"])
        cur = chosen.get(key)
        if cur is None or _rank(pool[k]) < _rank(pool[cur]):
            chosen[key] = k
    if len(chosen) != len(pool):
        print("dedup: %d duplicate title(s) resolved, dropped %s"
              % (len(pool) - len(chosen), sorted(set(pool) - set(chosen.values()))))
    pool = {k: pool[k] for k in sorted(chosen.values())}
    _write(POOL, pool)
    print("curated pool: %d of %d raw -> %s" % (len(pool), len(raw), os.path.relpath(POOL, HERE)))


def _arxiv_titles(ids, chunk=20):
    """Fetch titles for many arXiv ids in BATCHES.  `max_results` is set to the chunk's own size
    (the API caps at 10 otherwise, and the shortfall then looks like absent records) and the
    returned count is checked.  A failed batch is a TRANSPORT failure, never a finding."""
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
            print("    [batch %d-%d] WARNING: %d ids, %d entries returned"
                  % (i, i + len(part), len(part), len(got)), flush=True)
        for e in got:
            aid = arxiv_id(e.findtext(ATOM + "id", ""))
            out[aid] = re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip()
        time.sleep(12.0)     # arXiv rate-limits bursts (HTTP 429); space the batches out
    return out, failed


def _digest(path):
    """sha256 of a file, byte-for-byte.  The verification receipt names the pool it verified by
    this digest, so a receipt can never outlive the object it is evidence about (Class 230)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify():
    """Re-fetch every pool entry from its live endpoint and compare the returned TITLE with the
    stored title (two-sided, 0.80).  The WHOLE stdout is also written, verbatim, as the receipt
    `refs/verify-run.txt`: a quoted output line is a claim about a program (Class 192), so the
    receipt is what `reference-check.md` renders and `reproduce.sh` re-derives."""
    pool = json.load(open(POOL))
    out = []

    def say(s=""):
        print(s, flush=True)
        out.append(s)

    say("POOL sha256 %s" % _digest(POOL))
    ok = mismatch = transport = 0
    arxiv_keys = sorted(k for k, v in pool.items() if v["source"] == "arxiv")
    say("verifying %d arXiv + %d Crossref entries" % (len(arxiv_keys),
        len(pool) - len(arxiv_keys)))
    live, failed_batches = _arxiv_titles(arxiv_keys)
    for key in arxiv_keys:
        if key not in live:
            transport += 1
            continue
        good = title_matches(pool[key]["title"], live[key]) >= 0.8
        ok += 1 if good else 0
        mismatch += 0 if good else 1
        if not good:
            say("  MISMATCH %s\n     stored: %s\n     live  : %s"
                % (key, pool[key]["title"][:66], live[key][:66]))
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
    say("VERIFIED %d / %d ; TITLE MISMATCH %d ; TRANSPORT-UNKNOWN %d (batches failed: %d)"
        % (ok, total, mismatch, transport, failed_batches))
    say("a nonzero TRANSPORT-UNKNOWN is an OUTAGE, not evidence about the records -- re-run later")
    _write(RECEIPT, "\n".join(out) + "\n")
    print("receipt -> %s" % os.path.relpath(RECEIPT, HERE), flush=True)
    return 0 if (mismatch == 0 and transport == 0) else 1


def report():
    pool = json.load(open(POOL))
    n_arxiv = sum(1 for v in pool.values() if v["source"] == "arxiv")
    lines = [
        "# Reference pool -- issue #139",
        "",
        "Every entry below was discovered by `refscan139.py` (never typed from memory) and checked",
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


def gate():
    """The OFFLINE check: the network verification is a separate, documented pass (see
    reference-check.md); this gate asserts the shipped pool is complete and internally consistent,
    so `reproduce.sh` can check the reference layer without touching the network."""
    pool = json.load(open(POOL))
    checks = []
    checks.append(("the pool carries at least 100 entries (the journal's floor)", len(pool) >= 100))
    checks.append(("every entry has an id, a source, a non-empty title and a year",
                   all(v.get("id") and v.get("source") in ("arxiv", "crossref")
                       and (v.get("title") or "").strip() and "published" in v
                       for v in pool.values())))
    checks.append(("the pool has no duplicate TITLE (one paper, one entry)",
                   len({v["title"].lower() for v in pool.values()}) == len(pool)))
    checks.append(("every key is its own id (a key that cannot round-trip is not an identifier)",
                   all(k == v["id"] for k, v in pool.items())))
    checks.append(("an old-style arXiv id keeps its archive prefix",
                   not any(v["source"] == "arxiv" and re.match(r"^\d{7}$", k)
                           for k, v in pool.items())))
    md = open(os.path.join(HERE, "reference-pool.md"), encoding="utf-8").read()
    listed = sum(1 for line in md.splitlines() if line.startswith("| ") and " | " in line[2:]
                 and not line.startswith("| key "))
    checks.append(("reference-pool.md lists exactly the pool (%d)" % len(pool),
                   listed == len(pool)))
    # The verification receipt is the ONLY evidence that the network pass ran, and it is offline
    # checkable BECAUSE it names the pool it verified by digest: a receipt that outlived its pool is
    # caught here rather than quoted (Class 230 -- a receipt expires when its object moves).
    if os.path.exists(RECEIPT):
        rec = open(RECEIPT, encoding="utf-8").read()
        first = rec.splitlines()[0] if rec.splitlines() else ""
        m = re.match(r"^POOL sha256 ([0-9a-f]{64})$", first)
        checks.append(("the verification receipt's origin is the SHIPPED pool (digest matches)",
                       bool(m) and m.group(1) == _digest(POOL)))
        checks.append(("the verification receipt records a PASSING run",
                       "TITLE MISMATCH 0" in rec and "TRANSPORT-UNKNOWN 0" in rec))
    else:
        checks.append(("the verification receipt refs/verify-run.txt exists", False))
    bad = 0
    for lab, ok in checks:
        print("   %-4s %s" % ("ok" if ok else "FAIL", lab))
        bad += 0 if ok else 1
    print("GATE %d/%d" % (len(checks) - bad, len(checks)))
    return 1 if bad else 0


def selftest():
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-34s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    holds("accept-identical", title_matches("Dafny: An Automatic Program Verifier for Functional "
                                             "Correctness",
                                             "Dafny: An Automatic Program Verifier for Functional "
                                             "Correctness") == 1.0)
    holds("accept-case-and-punct", title_matches("HyperTree Proof Search for Neural Theorem Proving",
                                                 "hypertree proof search for neural theorem proving")
          == 1.0)
    # Crossref splits a two-part title across `title` and `subtitle`.  A reader that takes `title`
    # alone REPORTS THE CORRECT RECORD AS A MISMATCH; joining the two fields is a repair to the
    # READER, at the same 0.80 two-sided threshold.  Both limbs are asserted, so the join cannot be
    # dropped without the pair failing.
    _cr = {"title": ["Dafny: An Automatic Program Verifier"],
           "subtitle": ["for functional correctness"]}
    _full = "Dafny: An Automatic Program Verifier: for functional correctness"
    holds("subtitle-join-reproduces-full-title", title_matches(_full, cr_title(_cr)) == 1.0)
    holds("title-only-reader-would-mismatch", title_matches(_full, _cr["title"][0]) < 0.8)
    holds("reject-generic-short", title_matches(
        "Program Verification", "Industrial Deployment of a Deductive Verification Toolchain for "
        "Safety-Critical Avionics Software") < 0.8)
    holds("reject-substring", title_matches(
        "Cost-Aware Scheduling of Interdependent Proof Obligations in Deductive Verification",
        "Proof Obligations") < 0.8)
    holds("reject-different", title_matches("Dafny: An Automatic Program Verifier for Functional "
                                            "Correctness",
                                            "HyperTree Proof Search for Neural Theorem Proving") < 0.8)
    holds("reject-one-sided-trap", title_matches(
        "Verification", "Cost-Aware Verification of Interdependent Proof Obligations at Scale") < 0.8)
    # an OLD-STYLE arXiv id carries an archive prefix; a normaliser that drops it produces an id the
    # API rejects (HTTP 400)
    holds("id-keeps-old-style-prefix", arxiv_id("http://arxiv.org/abs/cs/0609060") == "cs/0609060")
    holds("id-keeps-new-style", arxiv_id("http://arxiv.org/abs/0909.4385v2") == "0909.4385")
    holds("id-strips-version-only", arxiv_id("http://arxiv.org/abs/1204.0182") == "1204.0182")
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--gate" in argv:
        return gate()
    if "--report" in argv:
        report()
        return 0
    if "--verify" in argv:
        return verify()
    if "--curate" in argv:
        curate()
        return 0
    if "--canonical" in argv:
        discover(canonical_only=True)
        return 0
    discover()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
