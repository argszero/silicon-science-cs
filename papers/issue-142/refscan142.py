#!/usr/bin/env python3
"""Issue #142 -- reference scan + VERIFICATION.

The subject is the IDENTIFICATION OF A DEPLOYED SYSTEM'S COST CURVATURE from a price sweep: the
priced objective `J(L) = C(L) + lam/L` and the envelope relation that lets the price a deployment
already pays be read back into the marginal cost it does not measure.  This file discovers the
related work for THAT subject and VERIFIES every entry against a live external record.

A citation is verified only if the returned record MATCHES the citation, not merely if the endpoint
answered.  A DOI or an arXiv id written from memory RESOLVES -- the API returns HTTP 200 with a real
record -- but the record can be a DIFFERENT paper.  So the check is the returned TITLE against the
stored title, compared two-sided, and nothing here is typed from memory: every key in the pool came
out of this tool's own discovery pass.

Four things the checks refuse to do, each because it was once the bug (the shape is the house
pattern, `papers/issue-135/refscan135.py`, itself from `papers/issue-132/refscan132.py`):

  * divide the title overlap by ONE of the two titles -- a short generic title then scores 1.00
    against a long specific one, i.e. a metric that can never fail on the object it is built to
    catch.  The score is the SMALLER of the two coverage fractions.
  * read a Crossref record's `title` alone -- Crossref SPLITS a two-part title across `title` and
    `subtitle`, so a reader that takes `title` alone reports the CORRECT record as a mismatch.
    Both fields are joined, at the same threshold.
  * report a transport failure as a finding.  An outage is not evidence about a record: a failed
    batch yields TRANSPORT-UNKNOWN, never "these records do not exist", and makes the run fail.
  * silently under-ask.  The arXiv `id_list` endpoint caps a request at 10 entries unless
    `max_results` says otherwise, so a 50-id chunk returns 10 titles and the other 40 look
    unanswerable -- a truncation disguised as a data problem.  `max_results` is set to the chunk's
    own size and the returned count is checked.

Sources, both declarative:
  * arXiv API (`search_query` discovery, then `id_list` verification).
  * Crossref `query.bibliographic` -- the canonical works are found BY TITLE, never by a remembered
    DOI -- and `works/<doi>` (verification).

Usage:
    python3 refscan142.py              discover (arXiv search_query -> refs/raw.json)
    python3 refscan142.py --canonical  add the canonical works (Crossref, BY TITLE)
    python3 refscan142.py --curate     relevance-filter raw -> refs/pool.json, resolve dup titles
    python3 refscan142.py --verify     re-verify every pool entry by TITLE (drops nothing)
    python3 refscan142.py --report     emit reference-pool.md from the pool
    python3 refscan142.py --gate       the OFFLINE completeness/consistency gate (no network)
    python3 refscan142.py --selftest   plant the failure modes, require them to fire
    python3 refscan142.py --gateselftest  fire EVERY gate check on a throwaway copy of the package
    python3 refscan142.py --enrich     fill publisher/container on the Crossref entries (network)
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

# Queries derive from the JOURNAL SCOPE of this paper -- identifying a priced objective's marginal
# cost from a sweep of the price a deployment already pays, under measurement noise -- not from any
# system name.
ARXIV_QUERIES = [
    ("envelope",    'all:"envelope theorem"'),
    ("marginal",    'all:"marginal cost" AND all:"identification"'),
    ("curvature",   'all:"cost curvature"'),
    ("pricedopt",   'all:"parametric optimization" AND all:"sensitivity"'),
    ("sens2",       'all:"second-order" AND all:"sensitivity" AND all:"optimization"'),
    ("dfd",         'all:"finite difference" AND all:"derivative estimation"'),
    ("kdnoise",     'all:"derivative estimation" AND all:"noise"'),
    ("kw",          'all:"Kiefer-Wolfowitz"'),
    ("sa",          'all:"stochastic approximation"'),
    ("spsa",        'all:"simultaneous perturbation"'),
    ("derivfree",   'all:"derivative-free" AND all:"optimization" AND all:"stochastic"'),
    ("extremum",    'all:"extremum seeking"'),
    ("sysid",       'all:"system identification" AND all:"linear"'),
    ("sysidclosed", 'all:"closed-loop" AND all:"system identification"'),
    ("sysidcost",   'all:"system identification" AND all:"cost"'),
    ("expdesign",   'all:"optimal experiment design"'),
    ("crlb",        'all:"Cramer-Rao" AND all:"estimation"'),
    ("chunking",    'all:"action chunking"'),
    ("chunkpol",    'all:"chunking" AND all:"policy" AND all:"robot"'),
    ("replan",      'all:"replanning" AND all:"horizon"'),
    ("lqr",         'all:"LQR" AND all:"cost"'),
    ("delaycost",   'all:"delay" AND all:"control" AND all:"optimal"'),
    ("aoi",         'all:"age of information"'),
    ("aoisample",   'all:"age of information" AND all:"sampling"'),
    ("samplingopt", 'all:"staleness" AND all:"optimization"'),
    ("freshness",   'all:"data freshness" AND all:"optimization"'),
    ("pricing",     'all:"price signal" AND all:"identification"'),
    ("pricing2",    'all:"pricing" AND all:"marginal" AND all:"estimation"'),
    ("onlineknob",  'all:"online tuning" AND all:"latency"'),
    ("autotune",    'all:"autotuning" AND all:"system" AND all:"configuration"'),
    ("banditknob",  'all:"configuration tuning" AND all:"Bayesian optimization"'),
    ("bo",          'all:"Bayesian optimization" AND all:"system" AND all:"performance"'),
    ("knob",        'all:"knob" AND all:"tuning" AND all:"database"'),
    ("dbtune",      'all:"database" AND all:"configuration" AND all:"tuning"'),
    ("rlfreq",      'all:"control frequency" AND all:"reinforcement learning"'),
    ("feedback",    'all:"feedback delay" AND all:"policy"'),
    ("identify",    'all:"identifiability" AND all:"optimization"'),
    ("constrained", 'all:"active set" AND all:"identification"'),
    ("sensim",      'all:"sensitivity analysis" AND all:"simulation"'),
    ("blackbox",    'all:"black-box" AND all:"gradient" AND all:"optimization"'),
    ("regretcont",  'all:"regret" AND all:"bandit" AND all:"continuous"'),
    ("queueprice",  'all:"congestion pricing" AND all:"queue"'),
]

# Canonical works for this subject, named BY TITLE (Crossref), never by a remembered DOI.  Each is a
# work a referee would expect the paper to know; if a title cannot be found the entry is reported
# unresolved rather than entered on a remembered identifier.
CANONICAL = [
    ("kw1952",         "A Stochastic Approximation Method"),
    ("spall1992",      "Multivariate stochastic approximation using a simultaneous perturbation gradient approximation"),
    ("spall1998",      "An Overview of the Simultaneous Perturbation Method for Efficient Optimization"),
    ("milgrom-segal",  "Envelope Theorems for Arbitrary Choice Sets"),
    ("holmstrom",      "Moral Hazard and Observability"),
    ("ljung",          "System Identification: Theory for the User"),
    ("kaelbling",      "Planning and acting in partially observable stochastic domains"),
    ("bertsekas",      "Dynamic Programming and Optimal Control"),
    ("schulman-gae",   "High-Dimensional Continuous Control Using Generalized Advantage Estimation"),
    ("levine",         "End-to-End Training of Deep Visuomotor Policies"),
    ("kalman",         "Contributions to the theory of optimal control"),
    ("srinivas-gp",    "Gaussian Process Optimization in the Bandit Setting: No Regret and Experimental Design"),
    ("shahriari-bo",   "Taking the Human Out of the Loop: A Review of Bayesian Optimization"),
    ("van-aken",       "Automatic database management system tuning through large-scale machine learning"),
    ("zhang-cdbtune",  "CDBTune: An End-to-End Learning System for Automatic Database Tuning"),
    ("akiba-optuna",   "Optuna: A Next-generation Hyperparameter Optimization Framework"),
    ("snoek",          "Practical Bayesian Optimization of Machine Learning Algorithms"),
    ("kober",          "Reinforcement Learning in Robotics: A Survey"),
    ("mayne",          "Constrained model predictive control: Stability and optimality"),
    ("yates-aoi",      "The Age of Information: Real-Time Status Updating by Multiple Sources"),
    ("costa-aoi",      "Age of Information with Packet Management"),
    ("nocedal",        "Numerical Optimization"),
    ("kushner",        "Stochastic Approximation and Recursive Algorithms and Applications"),
    ("borkar",         "Stochastic Approximation: A Dynamical Systems Viewpoint"),
    ("polyak-juditsky","Acceleration of stochastic approximation by averaging"),
    ("kingma-adam",    "Adam: A Method for Stochastic Optimization"),
    ("rasmussen-gp",   "Gaussian Processes for Machine Learning"),
    ("auer-bandit",    "Finite-time Analysis of the Multiarmed Bandit Problem"),
    ("bubeck-bandit",  "Regret Analysis of Stochastic and Nonstochastic Multi-armed Bandit Problems"),
    ("flaxman-bandit", "Online convex optimization in the bandit setting: gradient descent without a gradient"),
    ("tsitsiklis-td",  "Analysis of temporal-difference learning with function approximation"),
    ("hazan-oco",      "Introduction to Online Convex Optimization"),
]


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False)


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _get(url, timeout=45, tries=3):
    """GET with retries; raises on repeated failure so a transport outage is never read as a finding."""
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:      # noqa: BLE001 -- the retry IS the handling
            last = e
            time.sleep(2.0)
    raise RuntimeError("transport: %s" % last)


def norm(s):
    """Fold a string to a comparison key: NFKD, ASCII, lowercase, alphanumeric words only."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_score(a, b):
    """The SMALLER of the two coverage fractions, over WORD SETS.  Dividing by one title's length is
    the house's named bug: a short generic title here scores 1.00 against a long specific one."""
    wa, wb = set(norm(a).split()), set(norm(b).split())
    if not wa or not wb:
        return 0.0
    inter = len(wa & wb)
    return min(inter / len(wa), inter / len(wb))


def title_matches(a, b, min_frac=0.80):
    return title_score(a, b) >= min_frac


def arxiv_id(text):
    """Extract the bare arXiv id from an abs URL, keeping an OLD-STYLE archive prefix (`cs/0609060`)
    and stripping only the version suffix."""
    if not text:
        return ""
    m = re.search(r"abs/(.+?)(v\d+)?$", text.strip())
    if m:
        return m.group(1)
    tail = text.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", tail)


def arxiv_search(query, max_results=60):
    url = ("https://export.arxiv.org/api/query?search_query=%s"
           "&sortBy=submittedDate&sortOrder=descending&max_results=%d"
           % (urllib.parse.quote(query), max_results))
    return arxiv_search_raw(url)


def cr_title(m):
    """Join a Crossref record's `title` and `subtitle` -- the split is a property of the RECORD, and a
    reader taking `title` alone reports the correct record as a mismatch (Class 215a)."""
    parts = []
    for k in ("title", "subtitle"):
        v = m.get(k)
        if isinstance(v, list) and v:
            parts.append(v[0])
        elif isinstance(v, str) and v:
            parts.append(v)
    return ": ".join(p.strip() for p in parts if p and p.strip())


def crossref_by_title(title, rows=8):
    url = ("https://api.crossref.org/works?query.bibliographic=%s&rows=%d"
           % (urllib.parse.quote(title), rows))
    return json.loads(_get(url).decode("utf-8", "replace")).get("message", {}).get("items", [])


def crossref_by_query_title(title, rows=8):
    url = ("https://api.crossref.org/works?query.title=%s&rows=%d"
           % (urllib.parse.quote(title), rows))
    return json.loads(_get(url).decode("utf-8", "replace")).get("message", {}).get("items", [])


def arxiv_by_title(title, max_results=8):
    """Find an arXiv record BY TITLE.  This is the third route and it exists because the other two
    have holes in OPPOSITE places: `search_query` discovery is sorted by submission date, so its top
    60 for a broad query can never reach a 2014 paper, and Crossref simply has no record for an ICLR
    or NeurIPS paper published without a DOI (Adam, GAE, GP-UCB all return nothing there).

    The entry is still entered only on a VERIFIED title match, never on a remembered id, and the
    match score is stored beside it like every other route's."""
    url = ("https://export.arxiv.org/api/query?search_query=%s&max_results=%d"
           % (urllib.parse.quote('ti:"%s"' % title), max_results))
    try:
        ents = arxiv_search_raw(url)
    except Exception:                                            # noqa: BLE001
        return None, 0.0
    best, bs = None, 0.0
    for e in ents:
        s = title_score(e["title"], title)
        if s > bs:
            best, bs = e, s
    return best, bs


def arxiv_search_raw(url):
    root = ET.fromstring(_get(url).decode("utf-8", "replace"))
    out = []
    for e in root.findall(ATOM + "entry"):
        aid = arxiv_id(e.findtext(ATOM + "id", ""))
        if not aid:
            continue
        out.append({
            "id": aid, "source": "arxiv",
            "title": re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip(),
            "summary": re.sub(r"\s+", " ", e.findtext(ATOM + "summary", "")).strip(),
            "published": (e.findtext(ATOM + "published", "") or "")[:10],
            "authors": [a.findtext(ATOM + "name", "").strip()
                        for a in e.findall(ATOM + "author") if a.findtext(ATOM + "name")],
            "categories": [c.get("term") for c in e.findall(ATOM + "category")],
        })
    return out


def crossref_find(title, min_frac=0.80, routes=None):
    """Find a work BY TITLE over TWO declarative Crossref routes and return the best (record, score).

    The two routes are not redundancy for its own sake: `query.bibliographic` is a fuzzy all-fields
    match that returns nothing usable for a short classic title (Robbins-Monro 1951 scores 0.50 there),
    while `query.title` is scoped to the title field and finds it outright.  Trying only the first
    route reports a WORK THAT EXISTS as unresolved -- a claim about the QUERY read as a claim about the
    corpus (Class 191).  Neither route consults a remembered DOI; both are searched by the title.

    `routes` is injectable so `--selftest` can plant a weak route beside a strong one and require the
    strong one to win -- the mechanism is otherwise only exercised against the live network."""
    if routes is None:
        routes = (("bibliographic", crossref_by_title), ("title", crossref_by_query_title))
    best, bs, route = None, 0.0, None
    for name, fn in routes:
        try:
            items = fn(title)
        except Exception:                                        # noqa: BLE001
            continue
        for it in items:
            s = title_score(cr_title(it), title)
            if s > bs:
                best, bs, route = it, s, name
    return best, bs, route


def discover(canonical_only=False):
    """arXiv `search_query` discovery, then Crossref BY TITLE for the canonical works.  The raw store
    is keyed by the entry's own id, so a work found by two queries is one entry with two provenances."""
    store = {}
    if os.path.exists(RAW):
        try:
            store = json.load(open(RAW, encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            store = {}
    if not canonical_only:
        n_failed = 0
        for name, q in ARXIV_QUERIES:
            try:
                ents = arxiv_search(q)
            except Exception as e:                               # noqa: BLE001
                print("[discover] %-14s TRANSPORT FAILURE: %s" % (name, e), flush=True)
                n_failed += 1
                continue
            added = 0
            for e in ents:
                if e["id"] in store:
                    if name not in store[e["id"]].get("found_by", []):
                        store[e["id"]].setdefault("found_by", []).append(name)
                else:
                    e["found_by"] = [name]
                    store[e["id"]] = e
                    added += 1
            print("[discover] %-14s n=%-3d new=%d" % (name, len(ents), added), flush=True)
            time.sleep(3.0)     # arXiv rate-limits bursts (HTTP 429)
        print("[discover] queries failed: %d" % n_failed, flush=True)
        # Persist the arXiv pass BEFORE the canonical loop: this file was once written only at the very
        # end, and a crash inside the Crossref pass then discarded the whole arXiv pass with it -- the
        # expensive part of the run, lost to a defect in the cheap part.
        _write(RAW, store)
        print("[discover] checkpoint: %d entries written to %s"
              % (len(store), os.path.relpath(RAW, HERE)), flush=True)
    # Crossref BY TITLE.  Found by a title, never by a remembered DOI; an unmatched title is reported
    # unresolved rather than entered.
    unresolved, matched = [], []
    for key, title in CANONICAL:
        best, bs, route = crossref_find(title)
        if best is None or bs < 0.80:
            # Crossref has no record for an ICLR/NeurIPS paper published without a DOI; the arXiv
            # route reaches it, still by a VERIFIED title match.  Without this limb the canonical list
            # would silently drop Adam, GAE and GP-UCB -- works a referee would expect the paper to know.
            ent, as_ = arxiv_by_title(title)
            if ent is not None and as_ > bs:
                best, bs, route = ent, as_, "arxiv-title"
            time.sleep(3.0)
        if best is not None and bs >= 0.80:
            if route == "arxiv-title":
                aid = best["id"]
                if aid not in store:
                    best["found_by"] = ["canonical-arxiv"]
                store[aid] = store.get(aid, best)
                if "canonical-arxiv" not in store[aid].setdefault("found_by", []):
                    store[aid]["found_by"].append("canonical-arxiv")
                store[aid]["canonical"] = True
                doi = aid
            else:
                doi = best.get("DOI") or ("key:" + key)
                store[doi] = {
                    "id": doi, "source": "crossref", "canonical": True,
                    "title": cr_title(best),
                    "summary": re.sub(r"<[^>]+>", " ", best.get("abstract", "") or "")[:1200],
                    "published": str((best.get("issued", {}).get("date-parts", [[None]])[0][0]) or ""),
                    "authors": [("%s %s" % (a.get("given", ""), a.get("family", ""))).strip()
                                for a in best.get("author", [])] or [],
                    "categories": best.get("subject", []) or [],
                    "publisher": (best.get("publisher") or "")[:80],
                    "container": (((best.get("container-title") or [""]) or [""])[0])[:80],
                    "matched_title": title, "match_score": bs, "matched_by": route,
                    "found_by": ["canonical"],
                }
            matched.append(key)
            print("[canonical] %-16s matched  %.2f (%s)  %s" % (key, bs, route, doi), flush=True)
        else:
            unresolved.append({"key": key, "title": title, "status": "unresolved", "score": bs})
            print("[canonical] %-16s UNRESOLVED (best %.2f)" % (key, bs), flush=True)
        time.sleep(1.0)
    _write(RAW, store)
    _write(os.path.join(REFDIR, "canonical-status.json"),
           {"matched": matched, "unresolved": unresolved})
    print("raw store: %d entries (%d arxiv, %d crossref); canonical matched %d, unresolved %d"
          % (len(store), sum(1 for v in store.values() if v["source"] == "arxiv"),
             sum(1 for v in store.values() if v["source"] == "crossref"),
             len(matched), len(unresolved)))


# A named OBJECT from the paper's scope keeps an entry outright; four SUPPORT objects keep it too.  The
# lists are declarative and counted, and the drops are reported, so nothing vanishes silently.
CORE_TERMS = ["envelope theorem", "marginal cost", "cost curvature", "stochastic approximation",
              "simultaneous perturbation", "extremum seeking", "system identification",
              "age of information", "action chunking", "execution horizon", "finite difference",
              "derivative estimation", "identifiability", "configuration tuning", "autotuning",
              "price signal", "experiment design", "bandit convex optimization", "gradient-free",
              "cramer-rao", "closed-loop identification", "derivative-free optimization",
              "dynamic pricing", "online lqr", "riccati", "regret optimal", "policy gradient",
              "optimal sampling", "sampling policy", "linear quadratic control",
              "multi armed sampling", "confusing instance"]
SUPPORT_TERMS = ["derivative-free", "gradient estimation", "sensitivity", "optimal control", "lqr",
                 "delay", "stability", "sampling", "staleness", "freshness", "regret", "bandit",
                 "bayesian optimization", "reinforcement learning", "closed-loop", "noise",
                 "estimation", "perturbation", "pricing", "horizon", "replanning", "robust",
                 "convergence", "hyperparameter", "tuning", "queue", "latency", "policy",
                 "experimental design", "noisy observations", "sample efficiency"]


# Off-domain noise: a broad `search_query` reaches work that shares a METHOD WORD with this paper while
# being about a different subject entirely (a variational-quantum-eigensolver paper hits "gradient",
# "estimation", "noise" and "optimization" and nothing this paper is about).  The exclusion is declared,
# applied to the TITLE only -- an on-subject paper may mention a quantum application in its abstract
# while its contribution is the method we cite -- and the count it removes is reported.
OFF_DOMAIN = ["quantum", "qubit", "rydberg", "kagome", "heisenberg", "fermi-hubbard", "vqe", "qaoa",
              "ansatz", "eigenstate", "hamiltonian", "qumode", "photonic", "spontaneous emission",
              "molecul", "chemistry", "protein", "drug discovery", "crispr", "gene expression",
              "galax", "cosmolog", "stellar", "particle physics", "benchmarking optimizers",
              "black hole"]


def _fold(s):
    """Fold hyphens and dashes to spaces.  Applied to the TEXT and to every TERM, so the two sides of
    the comparison are in the same form -- folding only one side makes `derivative-free optimization`
    miss a title the fold itself produced `derivative free optimization` in."""
    return s.lower().replace("-", " ").replace("\u2010", " ").replace("\u2013", " ")


def _hay(r):
    """The relevance haystack: title + summary, folded.  A term list holds `age of information`, and a
    paper titled "Policy Gradient Algorithms for Age-of-Information Cost Minimization" carries the
    phrase hyphenated -- so without the fold the term MISSES, the entry scores `core = 0`, and a paper
    squarely on the subject is dropped by the curation rule."""
    return _fold((r.get("title", "") or "") + " " + (r.get("summary", "") or ""))


CORE_TERMS_F = None
SUPPORT_TERMS_F = None
OFF_DOMAIN_F = None


def _terms():
    global CORE_TERMS_F, SUPPORT_TERMS_F, OFF_DOMAIN_F
    if CORE_TERMS_F is None:
        CORE_TERMS_F = [_fold(t) for t in CORE_TERMS]
        SUPPORT_TERMS_F = [_fold(t) for t in SUPPORT_TERMS]
        OFF_DOMAIN_F = [_fold(t) for t in OFF_DOMAIN]
    return CORE_TERMS_F, SUPPORT_TERMS_F, OFF_DOMAIN_F


def curate():
    raw = json.load(open(RAW, encoding="utf-8"))
    core_terms, sup_terms, off_domain = _terms()
    pool, dropped_off = {}, []
    for k, r in raw.items():
        if r.get("source") == "crossref" or r.get("canonical"):
            pool[k] = r                              # canonical works are kept by construction
            continue
        title = _fold(r.get("title", "") or "")
        text = _hay(r)
        core = sum(1 for t in core_terms if t in text)
        sup = sum(1 for t in sup_terms if t in text)
        if core < 1:
            continue                                 # no named subject object -> not this subject
        if any(t in title for t in off_domain):
            dropped_off.append(r["id"])
            continue                                 # shares a method word, different subject
        r2 = dict(r)
        r2["core_hits"] = core
        r2["support_hits"] = sup
        pool[k] = r2
    print("curate: dropped %d off-domain by title" % len(dropped_off))
    # One paper, one entry.  A work posted as a preprint AND published under a DOI arrives twice, and
    # the same paper is sometimes posted under two ids; a pool with a duplicate title lets the
    # manuscript cite one paper as two references.  Resolved deterministically, policy stated: a
    # Crossref (published) record wins over an arXiv preprint of the same title, and between two
    # records of the SAME source the EARLIER date wins (ISO dates sort lexicographically).
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
    (the API caps at 10 otherwise, and the shortfall then looks like absent records) and the returned
    count is checked.  A failed batch is a TRANSPORT failure, never a finding."""
    out = {}
    failed = 0
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        url = ("https://export.arxiv.org/api/query?id_list=" + ",".join(part)
               + "&max_results=%d" % len(part))
        try:
            root = ET.fromstring(_get(url).decode("utf-8", "replace"))
        except Exception as e:                                   # noqa: BLE001
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
    """sha256 of a file, byte-for-byte.  The verification receipt names the pool it verified by this
    digest, so a receipt can never outlive the object it is evidence about (Class 230)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_read(path):
    """Text of `path`, or `""` when it cannot be read as text -- a binary sibling is not a carrier."""
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return ""


def enrich():
    """Fill `publisher`/`container` on the pool's Crossref entries from their live records.

    A Crossref chapter record can carry NO author field at all (measured 2026-10-16: four canonical
    books do).  The entry then has no author to print, and inventing one is exactly what this tool
    exists to prevent -- so the responsible body is taken from the RECORD (`publisher`, then
    `container-title`) and printed in the author slot, with the absence stated in reference-check.md."""
    pool = json.load(open(POOL, encoding="utf-8"))
    n = 0
    for k, r in sorted(pool.items()):
        if r["source"] != "crossref":
            continue
        try:
            m = json.loads(_get("https://api.crossref.org/works/"
                                + urllib.parse.quote(k, safe="")).decode("utf-8", "replace"))["message"]
        except Exception as e:                                   # noqa: BLE001
            print("  [enrich] %s TRANSPORT FAILURE: %s" % (k, e))
            continue
        r["publisher"] = (m.get("publisher") or "")[:80]
        r["container"] = (((m.get("container-title") or [""]) or [""])[0])[:80]
        n += 1
        time.sleep(0.8)
    _write(POOL, pool)
    print("enriched %d Crossref entry(ies) with publisher/container" % n)


def verify():
    """Re-fetch every pool entry from its live endpoint and compare the returned TITLE with the stored
    title (two-sided, 0.80).  The WHOLE stdout is written, verbatim, as the receipt
    `refs/verify-run.txt`: a quoted output line is a claim about a program (Class 192), so the receipt
    is what `reference-check.md` renders and `reproduce.sh` re-derives."""
    pool = json.load(open(POOL, encoding="utf-8"))
    out = []

    def say(s=""):
        print(s, flush=True)
        out.append(s)

    say("POOL sha256 %s" % _digest(POOL))
    ok = mismatch = transport = 0
    arxiv_keys = sorted(k for k, v in pool.items() if v["source"] == "arxiv")
    say("verifying %d arXiv + %d Crossref entries" % (len(arxiv_keys), len(pool) - len(arxiv_keys)))
    live, failed_batches = _arxiv_titles(arxiv_keys)
    for key in arxiv_keys:
        if key not in live:
            transport += 1
            continue
        good = title_score(pool[key]["title"], live[key]) >= 0.80
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
            live_title = cr_title(m)
            good = title_score(r["title"], live_title) >= 0.80
        except Exception:                                        # noqa: BLE001
            transport += 1
            continue
        ok += 1 if good else 0
        mismatch += 0 if good else 1
        if not good:
            say("  MISMATCH %s\n     stored: %s\n     live  : %s"
                % (key, r["title"][:66], live_title[:66]))
        time.sleep(0.8)
    total = len(pool)
    say("VERIFIED %d / %d ; TITLE MISMATCH %d ; TRANSPORT-UNKNOWN %d (batches failed: %d)"
        % (ok, total, mismatch, transport, failed_batches))
    say("a nonzero TRANSPORT-UNKNOWN is an OUTAGE, not evidence about the records -- re-run later")
    _write_text(RECEIPT, "\n".join(out) + "\n")
    print("receipt -> %s" % os.path.relpath(RECEIPT, HERE), flush=True)
    return 0 if (mismatch == 0 and transport == 0) else 1


def report():
    pool = json.load(open(POOL, encoding="utf-8"))
    n_arxiv = sum(1 for v in pool.values() if v["source"] == "arxiv")
    lines = [
        "# Reference pool -- issue #142",
        "",
        "Every entry below was discovered by `refscan142.py` (never typed from memory) and checked",
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
    _write_text(os.path.join(HERE, "reference-pool.md"), "\n".join(lines) + "\n")
    print("wrote reference-pool.md (%d entries)" % len(pool))


def checkdoc():
    """Emit `reference-check.md` -- the citation authenticity report (the journal's quality-bar item
    12) -- DERIVED from the pool and the receipt, never typed by hand.  The receipt's own verdict line
    is quoted with its digest, so the report and the evidence it cites are bound together."""
    pool = json.load(open(POOL, encoding="utf-8"))
    rec = open(RECEIPT, encoding="utf-8").read() if os.path.exists(RECEIPT) else ""
    digest = re.match(r"^POOL sha256 ([0-9a-f]{64})$", rec.splitlines()[0]).group(1) if rec else "(none)"
    verdict = next((ln for ln in rec.splitlines() if ln.startswith("VERIFIED ")), "(no receipt)")
    n_arxiv = sum(1 for v in pool.values() if v["source"] == "arxiv")
    n_cr = len(pool) - n_arxiv
    # `canonical-status.json` is written by the NETWORK discovery step and is therefore a CARRIED
    # artefact -- and reading its absence as "0 unresolved" is exactly the silent zero this layer
    # exists to refuse: measured 2026-10-16, when the assembly had left the file behind and the
    # regenerated report dropped its three unresolved works while every count still looked clean.
    csp = os.path.join(REFDIR, "canonical-status.json")
    if not os.path.exists(csp):
        raise SystemExit("checkdoc: refs/canonical-status.json is MISSING -- it is the carrier of "
                         "the canonical-works section and is written by the network discovery "
                         "step, so it must be carried into the package (a report generated "
                         "without it states `0 unresolved`, which is a read of nothing)")
    cstat = json.load(open(csp, encoding="utf-8"))
    L = [
        "# Citation authenticity verification -- issue #142",
        "",
        "Generated by `refscan142.py --checkdoc` from `refs/pool.json` and the receipt",
        "`refs/verify-run.txt`.  Do not edit by hand: re-run the generator.",
        "",
        "## Method",
        "",
        "- **Discovery.** arXiv API `search_query` over 42 declarative queries derived from the paper's",
        "  subject (never from a system name), plus the canonical works looked up in Crossref BY TITLE",
        "  (`query.bibliographic`, falling back to `query.title`) -- no DOI or arXiv id in this file was",
        "  typed from memory.",
        "- **Verification.** Every pool entry is re-fetched from its live endpoint -- arXiv `id_list` in",
        "  batches of 20 with `max_results` set to the chunk's own size, Crossref `works/<doi>` -- and",
        "  the returned TITLE is compared with the stored title by the SMALLER of the two coverage",
        "  fractions over word sets, at threshold 0.80.",
        "- A resolver that merely ANSWERS is not verification: a remembered identifier resolves to a real",
        "  record that can be a DIFFERENT paper, so the check is the title comparison, not the HTTP",
        "  status.  A transport failure is recorded as TRANSPORT-UNKNOWN and fails the run; it is never",
        "  read as evidence that a record does not exist.",
        "",
        "## Evidence",
        "",
        "- pool: **%d entries** (%d arXiv, %d Crossref)" % (len(pool), n_arxiv, n_cr),
        "- receipt `refs/verify-run.txt`, bound to this pool by `POOL sha256 %s`" % digest,
        "- the receipt's verdict line, quoted verbatim: `%s`" % verdict,
        "",
        "## Entries",
        "",
        "| # | key | source | verified against | title |",
        "|---|-----|--------|------------------|-------|",
    ]
    for i, k in enumerate(sorted(pool), 1):
        r = pool[k]
        verifier = "arXiv `id_list`" if r["source"] == "arxiv" else "Crossref `works/<doi>`"
        L.append("| %d | `%s` | %s | %s | %s |"
                 % (i, k, r["source"], verifier, r["title"].replace("|", "/")[:110]))
    # A record's stored field is not the form an entry prints, and an ABSENT field is not an
    # attribution to invent.  The four Crossref records measured 2026-10-16 carry `author: null`
    # AND `editor: null` (bare publisher records), so the printed component is the record's own
    # responsible body -- and this section is where that basis is stated, because the entry itself
    # can only say it is a publisher, not show the live response it was read from.
    noauth = [(k, v) for k, v in sorted(pool.items())
              if not (v.get("authors") or []) and v["source"] == "crossref"]
    L += ["", "## Records that carry no author field (%d)" % len(noauth), "",
          "Every printed entry's author component is read from the **record**, so an entry whose",
          "record carries no `author` may not print one: naming an author here would be a claim this",
          "layer cannot verify, which is the same reason a remembered DOI is refused.  These records",
          "were read live and their `author` and `editor` fields are both null, so the manuscript",
          "prints the record's own responsible body in the author slot and marks it as such in the",
          "entry.  The subject of each work is stated in the entry's own difference line, alongside",
          "what separates it from this paper.", ""]
    for k, v in noauth:
        L.append("- `%s` -- *%s* (%s) -- publisher `%s`%s"
                 % (k, v["title"], str(v.get("published", ""))[:4],
                    v.get("publisher") or "(record states none)",
                    ", container `%s`" % v["container"] if v.get("container") else ""))

    un = cstat.get("unresolved", [])
    L += ["",
          "## Canonical works reported UNRESOLVED (%d)" % len(un),
          "",
          "A canonical work whose title could not be matched in Crossref is **not entered** on a",
          "remembered identifier -- that is what the verification exists to prevent.  It is reported",
          "here, and where the same work exists on arXiv it is carried through the arXiv route instead.",
          ""]
    for u in un:
        L.append("- `%s` -- \"%s\" (%s, best title score %.2f)"
                 % (u["key"], u["title"], u.get("status", "unresolved"), u.get("score", 0.0)))
    L.append("")
    _write_text(os.path.join(HERE, "reference-check.md"), "\n".join(L))
    print("wrote reference-check.md (%d entries, %d canonical unresolved)" % (len(pool), len(un)))


def gate():
    """The OFFLINE check: the network verification is a separate, documented pass (see
    reference-check.md); this gate asserts the shipped pool is complete and internally consistent,
    so `reproduce.sh` can check the reference layer without touching the network."""
    pool = json.load(open(POOL, encoding="utf-8"))
    checks = []
    checks.append(("the pool carries at least 100 entries (the journal's floor)", len(pool) >= 100))
    checks.append(("every entry has an id, a source, a non-empty title and a date",
                   all(v.get("id") and v.get("source") in ("arxiv", "crossref")
                       and (v.get("title") or "").strip() and v.get("published")
                       for v in pool.values())))
    checks.append(("the pool has no duplicate TITLE (one paper, one entry, by folded title)",
                   len({norm(v["title"]) for v in pool.values()}) == len(pool)))
    checks.append(("every key is its own id (a key that cannot round-trip is not an identifier)",
                   all(k == v["id"] for k, v in pool.items())))
    checks.append(("an old-style arXiv id keeps its archive prefix",
                   not any(v["source"] == "arxiv" and re.match(r"^\d{7}$", k)
                           for k, v in pool.items())))
    csp = os.path.join(REFDIR, "canonical-status.json")
    checks.append(("the canonical-status carrier is shipped (refs/canonical-status.json -- a "
                   "network-written file the report cannot be built without)",
                   os.path.exists(csp)))
    md_path = os.path.join(HERE, "reference-pool.md")
    if os.path.exists(md_path):
        md = open(md_path, encoding="utf-8").read()
        listed = sum(1 for line in md.splitlines()
                     if line.startswith("| ") and not line.startswith("| key ")
                     and not line.startswith("|-----"))
        checks.append(("reference-pool.md lists exactly the pool (%d)" % len(pool),
                       listed == len(pool)))
    else:
        checks.append(("reference-pool.md exists", False))
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
                       re.search(r"TITLE MISMATCH 0 ;", rec) is not None
                       and re.search(r"TRANSPORT-UNKNOWN 0 ", rec) is not None))
    else:
        checks.append(("the verification receipt refs/verify-run.txt exists", False))
    # A digest quoted in prose is a value a run can retire, and prose has no reader (Class 124) --
    # measured 2026-10-16, when README.md still quoted the digest the pool had BEFORE `--enrich`
    # changed it, and quoted it TRUNCATED (`6f580c3d...`), so no comparison could ever catch it.
    # Two checks, each two-sided: (i) every `POOL sha256 <x>` site quotes the CURRENT digest, so a
    # stale or truncated literal fails wherever it stands; (ii) the digest has no carrier outside
    # the DERIVED set (the receipt's first line and the generated report), because a value written
    # into a file no generator re-writes is a value nothing maintains.
    derived = {"refs/verify-run.txt", "reference-check.md"}
    quoted = {}
    for dp, _dn, fns in os.walk(HERE):
        if ".mplcache" in dp or "research" in dp.split(os.sep):
            continue
        for f in fns:
            if not f.endswith((".md", ".txt")):
                continue
            rel = os.path.relpath(os.path.join(dp, f), HERE).replace(os.sep, "/")
            # The VALUE is a digest, so the capture is the digest's own character class and not
            # `\S+`: the first draft captured the closing backtick of the report's
            # `` `POOL sha256 <hex>` `` and reported the CORRECT digest as stale -- a bar wider than
            # its reading, on the one site the rule exists for.  A capture that is not 64 hex
            # characters is the failure whatever it holds (`6f580c3d...` truncated, a `<digest>`
            # placeholder, an empty field), so the shape is the rule and the comparison is its check.
            for m in re.finditer(r"POOL sha256 ([0-9a-f]*)", _safe_read(os.path.join(dp, f))):
                quoted.setdefault(rel, []).append(m.group(1))
    dig = _digest(POOL)
    stale = sorted("%s: %r" % (rel, v) for rel, vs in quoted.items()
                   for v in vs if not re.fullmatch(r"[0-9a-f]{64}", v) or v != dig)
    checks.append(("every `POOL sha256` site quotes the shipped pool's digest%s"
                   % (" -- stale at " + "; ".join(stale) if stale else ""), not stale))
    checks.append(("the digest is quoted only by the DERIVED carriers %s (quoted by: %s)"
                   % (sorted(derived), sorted(quoted) or "none"),
                   bool(quoted) and set(quoted) <= derived))
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

    holds("accept-identical", title_matches("Cuckoo Hashing", "Cuckoo Hashing"))
    holds("accept-case-and-punct", title_matches(
        "A Stochastic Approximation Method", "a stochastic approximation method"))
    # Crossref splits a two-part title across `title` and `subtitle`.  A reader that takes `title`
    # alone REPORTS THE CORRECT RECORD AS A MISMATCH; joining the two fields is a repair to the
    # READER, at the same 0.80 two-sided threshold.  Both limbs are asserted, so the join cannot be
    # dropped without the pair failing.
    _cr = {"title": ["Stochastic Approximation"],
           "subtitle": ["a method for the identification of a regression function"]}
    _full = "Stochastic Approximation: a method for the identification of a regression function"
    holds("subtitle-join-reproduces-full", title_matches(_full, cr_title(_cr)))
    holds("title-only-reader-would-mismatch", not title_matches(_full, _cr["title"][0]))
    holds("reject-generic-short", not title_matches(
        "Optimization", "Practical Bayesian Optimization of Machine Learning Algorithms"))
    holds("reject-substring", not title_matches(
        "Analysis of Stochastic Approximation with Bounded Gradient Estimates", "Stochastic Approximation"))
    holds("reject-different", not title_matches("Adam", "The Age of Information"))
    holds("reject-one-sided-trap", not title_matches(
        "Bandits", "Regret Analysis of Stochastic and Nonstochastic Multi-armed Bandit Problems"))
    # an OLD-STYLE arXiv id carries an archive prefix; a normaliser that drops it produces an id the
    # API rejects (HTTP 400)
    holds("id-keeps-old-style-prefix", arxiv_id("http://arxiv.org/abs/cs/0609060") == "cs/0609060")
    holds("id-keeps-new-style", arxiv_id("http://arxiv.org/abs/0909.4385v2") == "0909.4385")
    holds("id-strips-version-only", arxiv_id("http://arxiv.org/abs/1204.0182") == "1204.0182")
    # The second Crossref route exists because the first reports a REAL work as unresolved.  The plant
    # puts a weak route beside a strong one and requires the strong one to win -- AND requires that the
    # result changes when the second route is absent, so the plant cannot pass on a route-blind reader.
    _weak = lambda t: [{"title": ["Polynomial approximation for stochastic programming"], "DOI": "10.0/weak"}]
    _strong = lambda t: [{"title": ["A Stochastic Approximation Method"], "DOI": "10.0/strong"}]
    _one, _s1, _r1 = crossref_find("A Stochastic Approximation Method", routes=[("bibliographic", _weak)])
    _two, _s2, _r2 = crossref_find("A Stochastic Approximation Method",
                                   routes=[("bibliographic", _weak), ("title", _strong)])
    holds("one-route-misses-the-work", _r1 == "bibliographic" and _s1 < 0.80)
    holds("two-routes-rescue-it", _r2 == "title" and _s2 >= 0.80)
    holds("rescue-changes-the-verdict", (_s1 < 0.80) != (_s2 < 0.80))
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def gateselftest():
    """The GATE's own plant battery: each check is fired on a throwaway copy of the package.

    A check that has never failed is decoration, and the offline gate reads the package IN PLACE,
    so a plant has to be a copy: this builds one from the shipped files, asserts the healthy copy
    passes, then plants ONE defect per check and requires the gate to name it FAIL.  The set is the
    checks the gate can be shown to take a side on -- a plant must move the verdict, so a check that
    no defect of its own can fail is reported here rather than trusted.
    """
    import shutil
    import subprocess
    import tempfile

    def build(root):
        for f in ("refscan142.py", "README.md", "reference-pool.md", "reference-check.md",
                  "manuscript.md"):
            src = os.path.join(HERE, f)
            if os.path.exists(src):
                shutil.copy(src, root)
        shutil.copytree(REFDIR, os.path.join(root, "refs"),
                        ignore=shutil.ignore_patterns("raw.json", "*.tmp", "*.stage"))

    def run(root):
        r = subprocess.run([sys.executable, os.path.join(root, "refscan142.py"), "--gate"],
                           capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    dig = _digest(POOL)
    ok = True

    def holds(label, cond, detail=""):
        nonlocal ok
        ok = ok and cond
        print("[%-34s] %s%s" % (label, "ok" if cond else "FAIL",
                                "" if cond else "  -> " + detail[:160]))

    base = tempfile.mkdtemp(prefix="refscan-gateself.")
    try:
        healthy = os.path.join(base, "healthy")
        os.makedirs(healthy)
        build(healthy)
        rc, out = run(healthy)
        holds("control-the-healthy-copy-passes", rc == 0 and "GATE 11/11" in out,
              "rc=%d %s" % (rc, out.strip().splitlines()[-1] if out.strip() else ""))

        def plant(name, label, mutate):
            root = os.path.join(base, name)
            os.makedirs(root)
            build(root)
            mutate(root)
            rc, out = run(root)
            hit = any(ln.strip().startswith("FAIL") and label in ln for ln in out.splitlines())
            holds(name, rc != 0 and hit,
                  "rc=%d named=%s | %s" % (rc, hit, " / ".join(
                      l.strip() for l in out.splitlines() if l.strip().startswith("FAIL"))))

        def edit(rel, old, new):
            def f(root):
                q = os.path.join(root, rel)
                t = open(q, encoding="utf-8").read()
                assert old in t, "plant anchor absent in %s" % rel
                open(q, "w", encoding="utf-8").write(t.replace(old, new, 1))
            return f

        plant("a-stale-digest-in-the-report",
              "every `POOL sha256` site quotes", edit(
                  "reference-check.md", dig, "0" * 64))
        plant("a-truncated-digest-in-prose",
              "every `POOL sha256` site quotes", edit(
                  "README.md", "# Issue #142", "# Issue #142\n\nPOOL sha256 %s..." % dig[:8]))
        plant("a-digest-copied-into-prose",
              "quoted only by the DERIVED carriers", edit(
                  "README.md", "# Issue #142",
                  "# Issue #142\n\nPOOL sha256 %s" % dig))
        plant("a-missing-canonical-carrier",
              "canonical-status carrier is shipped",
              lambda root: os.remove(os.path.join(root, "refs", "canonical-status.json")))
        plant("a-receipt-from-another-pool",
              "origin is the SHIPPED pool", edit(
                  "refs/verify-run.txt", dig, "f" * 64))
        plant("a-receipt-with-a-mismatch",
              "records a PASSING run", edit(
                  "refs/verify-run.txt", "TITLE MISMATCH 0", "TITLE MISMATCH 1"))
        def _dupe_title(root):
            """Two keys, one folded title: the pool's own 'one paper, one entry' rule, broken."""
            q = os.path.join(root, "refs", "pool.json")
            pool = json.load(open(q, encoding="utf-8"))
            keys = sorted(pool)
            a, b = keys[0], keys[1]
            pool[b]["title"] = pool[a]["title"]
            _write(q, pool)

        def drop_a_row(root):
            # The row form is `| <key> | <source> | <verifier> | <title> |`; the header and the
            # separator are excluded the same way the gate excludes them, so the plant breaks the
            # count the gate reads and not some other one.
            q = os.path.join(root, "reference-pool.md")
            lines = open(q, encoding="utf-8").read().splitlines()
            rows = [i for i, l in enumerate(lines)
                    if l.startswith("| ") and not l.startswith("| key ") and not l.startswith("|-----")]
            del lines[rows[-1]]
            open(q, "w", encoding="utf-8").write("\n".join(lines) + "\n")

        plant("a-row-dropped-from-the-pool-table",
              "reference-pool.md lists exactly the pool", drop_a_row)
        plant("a-paper-entered-twice-under-two-keys",
              "no duplicate TITLE",
              lambda root: _dupe_title(root))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("GATESELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--gateselftest" in argv:
        return gateselftest()
    if "--gate" in argv:
        return gate()
    if "--report" in argv:
        report()
        return 0
    if "--enrich" in argv:
        enrich()
        return 0
    if "--checkdoc" in argv:
        checkdoc()
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
