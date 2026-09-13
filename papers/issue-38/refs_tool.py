#!/usr/bin/env python3
"""Bibliography builder for issue #38.

Two stages, both driven by live API responses so that reference-check.md is a
report of what was actually retrieved rather than a hand-written claim:

    harvest  -> search arXiv (by term, by category) and Crossref (bibliographic
                query) and store every candidate with the record the API returned
    verify   -> re-fetch each SELECTED entry by its own identifier, compare the
                returned title against the title recorded in the selection, and
                write references.json plus the reference-check.md report lines

Usage:
    python3 refs_tool.py harvest
    python3 refs_tool.py verify

Only the Python 3 standard library is used. Network endpoints:
    arXiv   https://export.arxiv.org/api/query   (https only; http 301s)
    Crossref https://api.crossref.org/works      (mailto= enters the polite pool)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# The harvested candidate pool is a scratch artefact: it lives in the git-ignored
# research/ workspace so that `git add papers/issue-38/` can never stage it.
CAND = os.path.join(HERE, "research", "refs_candidates.json")
SEL = os.path.join(HERE, "refs_selected.json")
OUT = os.path.join(HERE, "references.json")
UA = "silicon-science-cs-issue38/1.0 (mailto:how2how2how2-arch@users.noreply.github.com)"
ARXIV = "https://export.arxiv.org/api/query?"
CROSSREF = "https://api.crossref.org/works"
SLEEP_ARXIV = 3.2
SLEEP_CROSSREF = 1.2


def fetch(url, tries=3, timeout=45):
    """Fetch a URL, returning text or None.

    The timeout is explicit because a degraded endpoint must not stall a whole
    verification run: a per-request bound turns "the API is down" into a
    recorded fallback rather than an unbounded wait.
    """
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as fh:
                return fh.read().decode("utf-8", "replace")
        except Exception as exc:          # network hiccup, rate limit, 5xx
            last = exc
            time.sleep(2.0 * (k + 1))
    print("    fetch failed: %s" % last)
    return None


# Greek letters arrive in two forms depending on the endpoint: the export API and
# the search index return the LaTeX macro, the abstract page returns the Unicode
# character. Folding both to a latin name keeps the comparison a title comparison
# rather than a rendering comparison.
GREEK = {
    "alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta",
    "epsilon": "epsilon", "varepsilon": "epsilon", "zeta": "zeta", "eta": "eta",
    "theta": "theta", "kappa": "kappa", "lambda": "lambda", "mu": "mu",
    "nu": "nu", "xi": "xi", "pi": "pi", "rho": "rho", "sigma": "sigma",
    "tau": "tau", "phi": "phi", "varphi": "phi", "chi": "chi", "psi": "psi",
    "omega": "omega",
}
UNICODE_GREEK = {
    "\u03b1": "alpha", "\u03b2": "beta", "\u03b3": "gamma", "\u03b4": "delta",
    "\u03b5": "epsilon", "\u03f5": "epsilon", "\u03b6": "zeta", "\u03b7": "eta",
    "\u03b8": "theta", "\u03ba": "kappa", "\u03bb": "lambda", "\u03bc": "mu",
    "\u03bd": "nu", "\u03be": "xi", "\u03c0": "pi", "\u03c1": "rho",
    "\u03c3": "sigma", "\u03c4": "tau", "\u03c6": "phi", "\u03d5": "phi",
    "\u03c7": "chi", "\u03c8": "psi", "\u03c9": "omega",
}


def norm(s):
    s = (s or "").lower()
    for macro, name in GREEK.items():
        s = re.sub(r"\\" + macro + r"\b", name, s)
    for ch, name in UNICODE_GREEK.items():
        s = s.replace(ch, name)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    return s


def flat(s):
    return re.sub(r"\s+", " ", s or "").strip()


def arxiv_entries(xml):
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", xml or "", re.S):
        def g(tag):
            m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), e, re.S)
            return flat(m.group(1)) if m else ""
        link = g("id")
        m = re.search(r"arxiv.org/abs/([^v\s]+)", link)
        out.append({
            "source": "arxiv",
            "id": m.group(1) if m else "",
            "title": g("title"),
            "published": g("published")[:10],
            "url": "https://arxiv.org/abs/" + (m.group(1) if m else ""),
        })
    return out


def arxiv_search(query, n):
    url = ARXIV + urllib.parse.urlencode({
        "search_query": query, "sortBy": "relevance",
        "sortOrder": "descending", "max_results": n})
    return arxiv_entries(fetch(url))


def arxiv_ids(ids):
    url = ARXIV + urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
    return arxiv_entries(fetch(url))


def unescape(t):
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(a, b)
    return t


def arxiv_abs_title(aid):
    """Title of an arXiv entry, read from its own abstract page.

    The arXiv export API is a separate service from the abstract pages and is
    periodically degraded (observed returning HTTP 503 with 60 s latency while
    arxiv.org/abs responded in under 1 s). This endpoint is the declared
    fallback: the entry is still resolved by its own identifier, and the
    resolved title is still the authority -- only the transport changes.
    """
    raw = fetch("https://arxiv.org/abs/" + aid, tries=2, timeout=25)
    if not raw:
        return None
    m = re.search(r'<meta\s+name="citation_title"\s+content="([^"]*)"', raw)
    if not m:
        return None
    return unescape(flat(m.group(1)))


def crossref_query(title, n=3):
    url = CROSSREF + "?" + urllib.parse.urlencode({
        "query.bibliographic": title, "rows": n,
        "mailto": "how2how2how2-arch@users.noreply.github.com"})
    raw = fetch(url)
    if not raw:
        return []
    try:
        items = json.loads(raw)["message"]["items"]
    except Exception:
        return []
    out = []
    for it in items:
        t = (it.get("title") or [""])[0]
        out.append({
            "source": "crossref",
            "id": it.get("DOI", ""),
            "title": flat(t),
            "published": str((it.get("issued", {}).get("date-parts") or [[""]])[0][0]),
            "url": "https://doi.org/" + it.get("DOI", ""),
            "venue": flat((it.get("container-title") or [""])[0]),
        })
    return out


def crossref_doi(doi):
    raw = fetch(CROSSREF + "/" + urllib.parse.quote(doi))
    if not raw:
        return None
    try:
        it = json.loads(raw)["message"]
    except Exception:
        return None
    return {
        "source": "crossref",
        "id": it.get("DOI", ""),
        "title": flat((it.get("title") or [""])[0]),
        "published": str((it.get("issued", {}).get("date-parts") or [[""]])[0][0]),
        "url": "https://doi.org/" + it.get("DOI", ""),
        "venue": flat((it.get("container-title") or [""])[0]),
    }


# ---------------------------------------------------------------- harvest ---
# Queries derive from the study's actual field -- decentralised allocation by bidding
# versus a central planner with limited attention under misestimated costs -- and cover
# five clusters: (i) the assignment problem and its solvers, (ii) mechanism/market design
# and auction theory, (iii) bounded rationality, attention limits and estimation error,
# (iv) decentralised coordination in engineered systems, (v) recent LLM-agent markets and
# inference-time allocation. They are searches, not authorities: every selected entry is
# re-fetched by its own identifier before it is counted.
QUERIES = [
    ("arxiv", 'all:"assignment problem" AND all:"auction algorithm"'),
    ("arxiv", 'all:"Hungarian method" AND all:"assignment"'),
    ("arxiv", 'all:"linear assignment problem" AND all:"algorithm"'),
    ("arxiv", 'all:"assignment problem" AND all:"approximation"'),
    ("arxiv", 'all:"mechanism design" AND all:"resource allocation"'),
    ("arxiv", 'all:"market design" AND all:"matching"'),
    ("arxiv", 'all:"combinatorial auction" AND all:"allocation"'),
    ("arxiv", 'all:"auction" AND all:"task allocation" AND all:"multi-agent"'),
    ("arxiv", 'all:"contract net protocol"'),
    ("arxiv", 'all:"market-based" AND all:"resource allocation" AND all:"multi-agent"'),
    ("arxiv", 'all:"bounded rationality" AND all:"decision"'),
    ("arxiv", 'all:"rational inattention"'),
    ("arxiv", 'all:"limited attention" AND all:"choice"'),
    ("arxiv", 'all:"satisficing" AND all:"search"'),
    ("arxiv", 'all:"attention" AND all:"information overload"'),
    ("arxiv", 'all:"decentralized" AND all:"coordination" AND all:"team"'),
    ("arxiv", 'all:"auction" AND all:"estimation error"'),
    ("arxiv", 'all:"winner\'s curse" AND all:"common value"'),
    ("arxiv", 'all:"price of anarchy" AND all:"congestion"'),
    ("arxiv", 'all:"selfish routing"'),
    ("arxiv", 'all:"Nash equilibrium" AND all:"congestion game"'),
    ("arxiv", 'all:"online matching" AND all:"competitive ratio"'),
    ("arxiv", 'all:"online resource allocation" AND all:"regret"'),
    ("arxiv", 'all:"bandit" AND all:"allocation" AND all:"assignment"'),
    ("arxiv", 'all:"ranking and selection" AND all:"simulation optimization"'),
    ("arxiv", 'all:"LLM agents" AND all:"market"'),
    ("arxiv", 'all:"agent economy"'),
    ("arxiv", 'all:"LLM" AND all:"multi-agent" AND all:"orchestration"'),
    ("arxiv", 'all:"LLM" AND all:"multi-agent" AND all:"coordination" AND cat:cs.MA'),
    ("arxiv", 'all:"mixture of experts" AND all:"routing"'),
    ("arxiv", 'all:"LLM routing" AND all:"cost"'),
    ("arxiv", 'all:"model cascade" AND all:"inference"'),
    ("arxiv", 'all:"market-based scheduling" AND all:"cluster"'),
    ("arxiv", 'all:"spot pricing" AND all:"cloud"'),
    ("arxiv", 'all:"data center" AND all:"auction" AND all:"allocation"'),
    ("arxiv", 'all:"decentralized" AND all:"allocation" AND all:"failure"'),
    ("arxiv", 'all:"phase transition" AND all:"optimization" AND all:"noise"'),
    ("arxiv", 'all:"combinatorial optimization" AND all:"uncertainty" AND all:"stochastic"'),
    ("arxiv", 'all:"robust optimization" AND all:"assignment" AND all:"uncertainty"'),
    ("arxiv", 'all:"multi-armed bandit" AND all:"regret"'),
    ("arxiv", 'all:"prediction with expert advice"'),
    ("arxiv", 'all:"market mechanism" AND all:"large language model"'),
    ("arxiv", 'all:"agent-based simulation" AND all:"market" AND all:"efficiency"'),
    ("arxiv", 'all:"auction" AND all:"allocation" AND cat:cs.GT'),
    ("arxiv", 'all:"coordination" AND all:"market" AND cat:cs.MA'),
    ("arxiv", 'all:"mechanism design" AND all:"language model"'),
    ("arxiv", 'all:"centralized planning" AND all:"learning"'),
]

# Classic works in the field, as authoritative DOIs (discovery only -- each is re-fetched
# by its own DOI in the verify stage, and the returned title must match the recorded one).
CROSSREF_TITLES = [
    "The Hungarian method for the assignment problem",
    "Counterspeculation auctions and competitive sealed tenders",
    "Optimal auction design",
    "The assignment game I the core",
    "College admissions and the stability of marriage",
    "The market for lemons quality uncertainty and the market mechanism",
    "Anomalies the winner's curse",
    "A behavioral model of rational choice",
    "Implications of rational inattention",
    "A theory of auctions and competitive bidding",
    "Efficient mechanisms for bilateral trading",
    "Incentives in teams",
    "How bad is selfish routing",
    "The price of anarchy of congestion games",
    "The contract net protocol high-level communication and control in a distributed problem solver",
    "The architecture of complexity",
    "Judgment under uncertainty heuristics and biases",
    "Prospect theory an analysis of decision under risk",
    "The economics of information",
    "The theory of teams",
    "The problem of social cost",
    "Equilibrium points in n-person games",
    "Regret in decision making under uncertainty",
    "Mesos a platform for fine-grained resource sharing in the data center",
    "Sparrow distributed low latency scheduling",
    "Large-scale cluster management at Google with Borg",
    "Apache Hadoop YARN yet another resource negotiator",
    "Market-oriented cloud computing vision hype and reality for delivering IT services as computing utilities",
    "Assignment problems",
    "Scheduling theory algorithms and systems",
    "The complexity of the marriage problem",
    "Optimal statistical decisions",
    "Attention and effort",
    "A theory of human motivation",
    "The psychology of attention",
]


def harvest():
    cands = []
    print("arXiv term searches")
    for kind, q in QUERIES:
        print("  %s" % q[:70])
        got = arxiv_search(q, 8)
        for g in got:
            g["query"] = q
        cands += got
        time.sleep(SLEEP_ARXIV)
    print("Crossref bibliographic searches")
    for t in CROSSREF_TITLES:
        print("  %s" % t[:70])
        got = crossref_query(t, 2)
        for g in got:
            g["query"] = "crossref:" + t
        cands += got
        time.sleep(SLEEP_CROSSREF)
    # de-duplicate by (source, id)
    seen, uniq = set(), []
    for c in cands:
        k = (c["source"], c["id"])
        if not c["id"] or k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    os.makedirs(os.path.dirname(CAND), exist_ok=True)
    json.dump({"candidates": uniq}, open(CAND, "w", encoding="utf-8"), indent=1, sort_keys=True)
    print("candidates: %d -> %s" % (len(uniq), CAND))


# ----------------------------------------------------------------- verify ---
def verify():
    sel = json.load(open(SEL, encoding="utf-8"))["entries"]

    # Resolve arXiv entries through the export API in batches first (one request
    # per batch instead of one per entry); anything the API does not return --
    # including all of it, when the API is down -- is resolved through the
    # abstract-page endpoint instead.
    arxiv_ids_selected = [e["id"] for e in sel if e["source"] == "arxiv"]
    resolved = {}
    BATCH = 15
    for i in range(0, len(arxiv_ids_selected), BATCH):
        chunk = arxiv_ids_selected[i:i + BATCH]
        got = arxiv_ids(chunk)
        for g in got:
            resolved[g["id"].split("v")[0]] = g
        print("  arxiv api batch %d: %d/%d resolved" % (i // BATCH + 1, len(got), len(chunk)))
        time.sleep(1.0)
    via_abs, via_api = 0, 0

    records, problems = [], []
    for e in sel:
        src, ident = e["source"], e["id"]
        transport = ""
        if src == "crossref":
            rec = crossref_doi(ident)
            transport = "crossref-api"
            time.sleep(SLEEP_CROSSREF)
        else:
            rec = resolved.get(ident)
            if rec:
                transport = "arxiv-api"
            else:
                # API miss (down, rate-limited, or stale id) -> declared fallback
                t = arxiv_abs_title(ident)
                if t:
                    rec = {"title": t, "url": "https://arxiv.org/abs/" + ident, "published": ""}
                    transport = "arxiv-abs-page"
        if transport == "arxiv-api":
            via_api += 1
        elif transport == "arxiv-abs-page":
            via_abs += 1
        status = "UNVERIFIED"
        if rec:
            a, b = norm(rec["title"]), norm(e["title"])
            if a == b:
                status = "exact"
            elif b in a or a in b:
                status = "substring"
            else:
                status = "MISMATCH"
        else:
            rec = {"title": "", "url": "", "published": ""}
        if status in ("UNVERIFIED", "MISMATCH"):
            problems.append((e["key"], status, e["title"], rec.get("title", "")))
        records.append({
            "key": e["key"],
            "verified_via": transport,
            "title": rec.get("title") or e["title"],
            "recorded_title": e["title"],
            "source": src,
            "id": ident,
            "url": rec.get("url") or e["url"],
            "published": rec.get("published", ""),
            "status": status,
            "venue": rec.get("venue", ""),
            "difference": e["difference"],
        })
    json.dump({"entries": records, "problems": problems},
              open(OUT, "w", encoding="utf-8"), indent=1, sort_keys=True)
    ok = sum(1 for r in records if r["status"] in ("exact", "substring"))
    print("transport: arxiv-api=%d arxiv-abs-page=%d crossref-api=%d"
          % (via_api, via_abs, sum(1 for r in records if r["source"] == "crossref")))
    print("verified %d/%d, entries=%d, problems=%d" % (ok, len(records), len(records), len(problems)))
    for p in problems:
        print("  PROBLEM %s %s | recorded=%s | resolved=%s" % p)
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "harvest":
        harvest()
    elif cmd == "verify":
        verify()
    else:
        print(__doc__)
