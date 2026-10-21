#!/usr/bin/env python3
"""issue #141 -- the reference layer: discover, then verify, then count.

This package's reference layer is self-contained (it does not import the #142 package: an EXPORT of
this directory must run on its own).  The helpers below are the shape the journal has settled on, with
the reasons carried in their docstrings.

  python3 refscan141.py --discover      arXiv discovery -> refs/raw.json
  python3 refscan141.py --canonical     Crossref/arXiv BY TITLE for the works a referee expects
  python3 refscan141.py --pool          build refs/pool.json + refs/canonical-status.json
  python3 refscan141.py --selftest      the plants (offline; no network)
  python3 refscan141.py --checkdoc      write reference-check.md from the pool

A reference is entered only on a VERIFIED title match against a real record.  A title that cannot be
found is REPORTED unresolved -- never entered on a remembered identifier.  That rule is the journal's
citation-integrity bar, and it is why every route below searches by title and stores its score.
"""
import hashlib
import html
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
STATUS = os.path.join(REFDIR, "canonical-status.json")
RECEIPT = os.path.join(REFDIR, "verify-run.txt")
UA = "silicon-science-cs-refscan/1.0 (journal reference verification)"
ATOM = "{http://www.w3.org/2005/Atom}"

# Queries derive from the JOURNAL SCOPE of this paper -- an evaluation protocol as a measured object:
# how opponents are selected, how outcomes are aggregated into a score, and whether the induced
# ordering survives a change of population.  They are subject terms, not system names.
ARXIV_QUERIES = [
    ("auction",      'all:"auction theory"'),
    ("fpauction",    'all:"first-price auction" AND all:"equilibrium"'),
    ("spauction",    'all:"second-price auction"'),
    ("wincurse",     'all:"winner\'s curse" AND all:"common value"'),
    ("mechdesign",   'all:"mechanism design" AND all:"incentive"'),
    ("scoring",      'all:"scoring rule" AND all:"incentive"'),
    ("rankagg",      'all:"rank aggregation"'),
    ("kendall",      'all:"Kendall tau" AND all:"ranking"'),
    ("leaderboard",  'all:"leaderboard" AND all:"evaluation"'),
    ("benchmarkeval",'all:"benchmark" AND all:"evaluation" AND all:"reliability"'),
    ("benchcontam",  'all:"benchmark" AND all:"contamination"'),
    ("llmeval",      'all:"LLM" AND all:"evaluation" AND all:"benchmark"'),
    ("gamebench",    'all:"agent" AND all:"benchmark" AND all:"evaluation"'),
    ("goodhart",     'all:"Goodhart"'),
    ("gamingmetric", 'all:"gaming" AND all:"metric"'),
    ("evalprotocol", 'all:"evaluation protocol" AND all:"benchmark"'),
    ("tournament",   'all:"tournament" AND all:"ranking" AND all:"selection"'),
    ("pairwise",     'all:"pairwise comparison" AND all:"ranking"'),
    ("multicompar",  'all:"multiple comparisons" AND all:"ranking"'),
    ("construct",    'all:"construct validity" AND all:"benchmark"'),
    ("transferrank", 'all:"ranking" AND all:"transfer" AND all:"population"'),
    ("bootstrap_rank", 'all:"bootstrap" AND all:"rank" AND all:"confidence"'),
    ("sensitivity",  'all:"sensitivity analysis" AND all:"ranking"'),
    ("robustrank",   'all:"robust" AND all:"ranking" AND all:"noise"'),
    ("syntheticbench", 'all:"synthetic" AND all:"benchmark" AND all:"validity"'),
    ("rewardhack",   'all:"reward hacking"'),
    ("proxy",        'all:"proxy" AND all:"objective" AND all:"optimization"'),
    ("benchdesign",  'all:"benchmark design"'),
    ("reproduc",     'all:"reproducibility" AND all:"benchmark"'),
    ("llmjudge",     'all:"LLM-as-a-judge"'),
    ("elo",          'all:"Elo" AND all:"rating" AND all:"ranking"'),
    ("socialchoice", 'all:"social choice" AND all:"aggregation"'),
    ("arrow",        'all:"Arrow" AND all:"impossibility"'),
    ("principalagent", 'all:"principal" AND all:"agent" AND all:"moral hazard"'),
    ("measurement",  'all:"measurement" AND all:"validity" AND all:"metric"'),
    ("incentivecompat", 'all:"incentive compatibility"'),
    ("multiagent_eval", 'all:"multi-agent" AND all:"evaluation" AND all:"benchmark"'),
    ("rankingstability", 'all:"ranking" AND all:"stability" AND all:"perturbation"'),
    ("noiseorder",   'all:"noise" AND all:"ordering" AND all:"estimation"'),
    ("poptransfer",  'all:"distribution shift" AND all:"evaluation"'),
]

# Works a referee would expect this paper to know, named BY TITLE AND YEAR (never by a remembered
# DOI).  The year is not decoration: it is the second, independent test of a title match, and it is
# what separates "the work" from "a reprint, a chapter, or a differently-titled paper that shares the
# words".  Measured 2026-10-20: `Optimal Multi-unit Auctions` (Maskin & Riley, 1989) matched at 0.80
# to `Optimal multi-unit combinatorial auctions` (2011) -- a DIFFERENT PAPER -- and a title-only rule
# at 0.80 accepts it.  The canon follows:
# auction and mechanism-design canon the construction rests on, the measurement literature the
# distinction between a score and the thing it indexes comes from, and the four works §10 compares
# against.  A title that cannot be found is reported unresolved rather than entered.
CANONICAL = [
    ("vickrey1961", "Counterspeculation, Auctions, and Competitive Sealed Tenders", 1961),
    ("myerson1981", "Optimal Auction Design", 1981),
    ("riley-samuelson", "Optimal Auctions", 1981),
    ("milgrom-weber", "A Theory of Auctions and Competitive Bidding", 1982),
    ("holmstrom-milgrom", "Aggregation and Linearity in the Provision of Intertemporal Incentives", 1987),
    ("holmstrom-obs", "Moral Hazard and Observability", 1979),
    ("bulow-klemperer", "Auctions Versus Negotiations", 1996),
    ("klemperer", "Auction Theory: A Guide to the Literature", 1999),
    ("krishna", "Auction Theory", 2002),
    ("milgrom1989", "Auctions and Bidding: A Primer", 1989),
    ("maskin-riley", "Optimal Multi-unit Auctions", 1989),
    ("wilson1977", "A Bidding Model of Perfect Competition", 1977),
    ("kremer", "Auctions with Private Information", None),
    ("nash1950", "Equilibrium Points in N-Person Games", 1950),
    ("arrow1951", "Social Choice and Individual Values", 1951),
    ("kendall1938", "A New Measure of Rank Correlation", 1938),
    ("spearman1904", "The Proof and Measurement of Association between Two Things", 1904),
    ("goodhart", "Problems of Monetary Management: The U.K. Experience", 1975),
    ("campbell", "Assessing the Impact of Planned Social Change", 1969),
    ("strathern", "Improving Ratings: Audit in the British University System", 1997),
    ("sculley", "Hidden Technical Debt in Machine Learning Systems", 2015),
    ("recht2019", "Do ImageNet Classifiers Generalize to ImageNet?", 2019),
    ("ethayarajh", "Utility is in the Eye of the User: A Critique of NLP Leaderboards", 2020),
    ("bowman-dahl", "What Will it Take to Fix Benchmarking in Natural Language Understanding?", 2021),
    ("burnell2023", "Rethinking Model Evaluation as Narrowing the Socio-Technical Gap", 2023),
    ("sclar2023", "Minding Language Models' (Lack of) Theory of Mind", 2023),
    ("liang2022", "Holistic Evaluation of Language Models", 2022),
    ("srivastava2022", "Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models", 2022),
    ("kiela2021", "Dynabench: Rethinking Benchmarking in NLP", 2021),
    ("sutton2022", "The AI Index 2022 Annual Report", 2022),
    ("casper2023", "Explore, Establish, Exploit: Red Teaming Language Models from Scratch", 2023),
    ("perez2022", "Red Teaming Language Models with Language Models", 2022),
    ("mmmu", "MMMU: A Massive Multi-discipline Multimodal Understanding and Reasoning Benchmark", 2024),
    ("erpbench", "ERPBench", 2026),
    ("leaderboard-inference", "Leaderboard", 2026),
    ("principal-measure", "The Principal's Choice of Measure", 1993),
    ("wilson-ci", "Probable Inference, the Law of Succession, and Statistical Inference", 1927),
    ("dietterich", "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms", 1998),
    ("demvsar", "Statistical Comparisons of Classifiers over Multiple Data Sets", 2006),
]


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False)
    os.replace(tmp, path)


def _get(url, timeout=45, tries=3):
    """GET with retries; raises on repeated failure so a transport outage is never read as a finding."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:      # noqa: BLE001 -- the retry IS the handling
            last = e
            # NEVER retry a 429: the throttle is the response to OUR requests, so another one
            # extends it.  Measured 2026-10-20: a per-query 3-try loop turned a throttle into a
            # 30-minute stall that wrote nothing.
            if "429" in str(e):
                raise RuntimeError("transport: %s (throttled -- not retried)" % e)
            if attempt + 1 < tries:
                time.sleep(2.0 * (attempt + 1))
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
    a named house bug: a short generic title scores 1.00 against a long specific one."""
    wa, wb = set(norm(a).split()), set(norm(b).split())
    if not wa or not wb:
        return 0.0
    inter = len(wa & wb)
    return min(inter / len(wa), inter / len(wb))


def arxiv_id(text):
    """Bare arXiv id from an abs URL, keeping an old-style archive prefix and dropping the version."""
    if not text:
        return ""
    m = re.search(r"abs/(.+?)(v\d+)?$", text.strip())
    if m:
        return m.group(1)
    tail = text.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", tail)


def cr_title(m):
    """Join a Crossref record's `title` and `subtitle`; the split is a property of the RECORD."""
    parts = []
    for k in ("title", "subtitle"):
        v = m.get(k)
        if isinstance(v, list) and v:
            parts.append(v[0])
        elif isinstance(v, str) and v:
            parts.append(v)
    return ": ".join(p.strip() for p in parts if p and p.strip())


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


def arxiv_search(query, max_results=60):
    url = ("https://export.arxiv.org/api/query?search_query=%s"
           "&sortBy=submittedDate&sortOrder=descending&max_results=%d"
           % (urllib.parse.quote(query), max_results))
    return arxiv_search_raw(url)


def crossref_by_title(title, rows=8):
    url = ("https://api.crossref.org/works?query.bibliographic=%s&rows=%d"
           % (urllib.parse.quote(title), rows))
    return json.loads(_get(url).decode("utf-8", "replace")).get("message", {}).get("items", [])


def crossref_by_query_title(title, rows=8):
    url = ("https://api.crossref.org/works?query.title=%s&rows=%d"
           % (urllib.parse.quote(title), rows))
    return json.loads(_get(url).decode("utf-8", "replace")).get("message", {}).get("items", [])


def arxiv_by_title(title, max_results=8):
    """Find an arXiv record BY TITLE: the third route, and it exists because the other two have holes
    in OPPOSITE places -- `search_query` is sorted by submission date so it can never reach an old
    paper, and Crossref has no record for a workshop paper published without a DOI."""
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


ARXIV_STATE = {"ok": None, "detail": ""}


def arxiv_probe():
    """Is the arXiv API answering?  Probed ONCE, before a stage that would otherwise pay its timeout
    on every entry.

    A route that is unreachable is a leg that could NOT RUN, and it is reported as such -- never
    silently skipped, and never retried per-entry until the round's budget is gone (measured
    2026-10-20: `export.arxiv.org` timed out at 45 s while Crossref, api.github.com and a control
    URL all answered 200 in the same batch)."""
    if ARXIV_STATE["ok"] is not None:
        return ARXIV_STATE["ok"]
    try:
        _get("https://export.arxiv.org/api/query?search_query=all:%22auction%22&max_results=1",
             timeout=20, tries=1)
        ARXIV_STATE.update(ok=True, detail="reachable")
    except Exception as e:                                       # noqa: BLE001
        d = str(e)
        # a THROTTLE is not an outage: HTTP 429 says the API is alive and refusing this client, and
        # retrying inside the same round is what produces the next 429.  Named separately so the
        # receipt says which one happened -- "unreachable" and "throttled" support different actions.
        if "429" in d:
            ARXIV_STATE.update(ok=False, detail="THROTTLED (HTTP 429) -- retry in a later round")
        else:
            ARXIV_STATE.update(ok=False, detail=d[:120])
    return ARXIV_STATE["ok"]


def crossref_find(title, min_frac=0.80, routes=None):
    """Find a work BY TITLE over TWO declarative Crossref routes, returning the best (record, score).

    The routes are not redundancy for its own sake: `query.bibliographic` is a fuzzy all-fields match
    that returns nothing usable for a short classic title, while `query.title` is scoped to the title
    field and finds it outright.  Trying only the first reports a WORK THAT EXISTS as unresolved -- a
    claim about the QUERY read as a claim about the corpus.  Neither route consults a remembered DOI.
    `routes` is injectable so `--selftest` can plant a weak route beside a strong one."""
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


def record_year(best):
    """The record's own year, from whichever field its source uses."""
    if not best:
        return None
    if best.get("published"):
        m = re.match(r"(\d{4})", str(best["published"]))
        if m:
            return int(m.group(1))
    dp = (best.get("issued") or {}).get("date-parts") or [[None]]
    try:
        return int(dp[0][0])
    except (TypeError, ValueError, IndexError):
        return None


def verdict(best, score, year, exact_only=False):
    """matched | matched-edition | unresolved, from TWO independent tests.

    A title score alone is not a match.  Measured 2026-10-20 on this very list:
      * `Optimal Multi-unit Auctions` (1989) scored **0.80** against `Optimal multi-unit
        combinatorial auctions` (2011) -- a DIFFERENT PAPER, accepted by a 0.80 rule;
      * `Equilibrium Points in N-Person Games` scored **1.00** against a 2020 JSTOR reprint of the
        1950 paper -- the right work in the wrong edition, which a score cannot see either.

    So: a score below 0.90 is `unresolved` unless the year also agrees; and a score at or above it is
    `matched-edition` when the declared year and the record's year disagree by more than a year.  The
    edition case is not a rejection -- a reprint is sometimes the only registered record -- it is a
    state the bibliography must SAY, because printing the reprint's year as the paper's year is a
    false statement about the work.
    """
    if best is None:
        return "unresolved", "no record"
    ry = record_year(best)
    if score >= 0.999:
        if year is None or ry is None:
            return "matched", "exact title; year unchecked"
        if abs(ry - year) <= 1:
            return "matched", "exact title, year %d" % ry
        # THE THIRD TEST, and it is the one that was missing.  When the years DISAGREE the title is
        # exactly what cannot be the second test -- it is the field the edition claim rests on -- so
        # the record has to corroborate the work through something else.  Its author is that
        # something else.  A record that carries no author corroborates nothing, and a bare title
        # match is how a DIFFERENT work enters a bibliography: measured 2026-10-20, `Auction Theory`
        # (Krishna, 2002) scored 1.00 against a chapter of the 2021 Cambridge Element *Economics of
        # Visual Art* -- a chapter with no author on its record, on a subject the paper never touches.
        # The edition state is a STATE the bibliography says, so a state it cannot support is
        # `unresolved`, not the benefit of the doubt.
        if not (best.get("author") or best.get("authors")):
            return "unresolved", ("exact title, but the record carries no author: an edition cannot "
                                  "be corroborated by the title it is an edition of (record %s, %s)"
                                  % (best.get("DOI") or best.get("id"), ry))
        return "matched-edition", "exact title, but the record is the %d edition of a %d work" % (ry, year)
    if score >= 0.90:
        if year is not None and ry is not None and abs(ry - year) <= 1:
            return "matched", "near title (%.2f) with year %d" % (score, ry)
        return "unresolved", ("near title (%.2f) but year %s != %s" % (score, ry, year))
    return "unresolved", "title score %.2f below 0.90" % score


def reaudit():
    """Re-derive every canon VERDICT from the records already in the store -- offline.

    `verdict()` is a pure function of (record, title score, declared year), so a rule added to it
    does not require the network pass that found the records: it requires the verdicts to be
    RE-DERIVED from what is already stored.  This stage does exactly that and rewrites the status
    file only through that function, so the two carriers cannot disagree.

    It exists because the third test below (a record with no author cannot corroborate an edition)
    is not reachable by re-running `--canonical` on a throttled route, and a status file edited by
    hand to reflect a rule would be a verdict nobody can reproduce.  Measured 2026-10-20: the
    network pass hung on the first work and wrote nothing to this file, which is the failure mode a
    network-only stage has and this one does not.
    """
    with open(STATUS, encoding="utf-8") as fh:
        st = json.load(fh)
    with open(RAW, encoding="utf-8") as fh:
        raw = json.load(fh)
    matched, unresolved, changed = [], list(st.get("unresolved") or []), []
    for m in st["matched"]:
        rec = raw.get(m["id"])
        if rec is None:
            matched.append(m)
            continue
        # `verdict` reads the record's year from its own fields; the score and route are the
        # recorded FINDING and are carried unchanged -- this stage judges, it does not search.
        probe = dict(rec)
        state, why = verdict(probe, m["score"], m["year"])
        if state == m["status"] and why == m["why"]:
            matched.append(m)
            continue
        changed.append((m["key"], m["status"], state, why))
        if state in ("matched", "matched-edition"):
            matched.append(dict(m, status=state, why=why))
        else:
            unresolved.append({"key": m["key"], "title": m["title"], "year": m["year"],
                               "status": "unresolved", "score": m["score"], "why": why,
                               "best_candidate": rec.get("title"),
                               "best_year": record_year(rec),
                               "arxiv_route": st.get("arxiv_route", "not recorded")})
    out = {"matched": matched, "unresolved": unresolved,
           "arxiv_route": st.get("arxiv_route", "not recorded")}
    _write(STATUS, out)
    for key, was, now, why in changed:
        print("[reaudit] %-16s %-15s -> %-15s %s" % (key, was, now, why))
    print("[reaudit] %d verdict(s) re-derived from the stored records, %d changed; "
          "matched %d, unresolved %d" % (len(matched) + len(unresolved), len(changed),
                                         len(matched), len(unresolved)))
    return 0


def merge_record(store, e, name):
    """Insert one fetched record: "new" | "seen" | "amended".

    A lookup that keeps the first write cannot represent the state this store is in -- the same work
    reached by a later, better query.  An amendment is recorded, never silent."""
    key = e["id"]
    if key not in store:
        e = dict(e)
        e["found_by"] = [name]
        store[key] = e
        return "new"
    cur = store[key]
    if name not in cur.setdefault("found_by", []):
        cur["found_by"].append(name)
        # an amendment may enrich the record; a FIELD CONFLICT is a finding worth seeing
        for k in ("title", "published"):
            if e.get(k) and not cur.get(k):
                cur[k] = e[k]
        return "amended"
    return "seen"


# ---------------------------------------------------------------------------------------------
def discover():
    if not arxiv_probe():
        print("[discover] arXiv route NOT RUN: %s" % ARXIV_STATE["detail"], flush=True)
        print("[discover] no query was attempted -- an unreachable API is a leg that could not run, "
              "not a finding about the corpus", flush=True)
        return
    store = {}
    if os.path.exists(RAW):
        with open(RAW, encoding="utf-8") as fh:
            store = json.load(fh)
    n_failed = 0
    for name, q in ARXIV_QUERIES:
        try:
            ents = arxiv_search(q)
        except Exception as e:                                   # noqa: BLE001
            print("[discover] %-18s TRANSPORT FAILURE: %s" % (name, e), flush=True)
            n_failed += 1
            continue
        added = amended = 0
        for e in ents:
            o = merge_record(store, e, name)
            added += 1 if o == "new" else 0
            amended += 1 if o == "amended" else 0
        print("[discover] %-18s n=%-3d new=%d amended=%d" % (name, len(ents), added, amended),
              flush=True)
        time.sleep(3.0)      # arXiv rate-limits bursts (HTTP 429)
        _write(RAW, store)   # checkpoint per query: a later failure must not discard the expensive part
    print("[discover] queries failed: %d" % n_failed, flush=True)
    print("[discover] raw store: %d entries" % len(store), flush=True)


def canonical():
    store = {}
    if os.path.exists(RAW):
        with open(RAW, encoding="utf-8") as fh:
            store = json.load(fh)
    unresolved, matched = [], []
    for key, title, year in CANONICAL:
        best, bs, route = crossref_find(title)
        if best is None or bs < 0.80:
            if arxiv_probe():
                ent, as_ = arxiv_by_title(title)
                if ent is not None and as_ > bs:
                    best, bs, route = ent, as_, "arxiv-title"
                time.sleep(3.0)
            else:
                # the route did not run; the entry is still reported, with the reason
                pass
        state, why = verdict(best, bs, year)
        if state in ("matched", "matched-edition"):
            if route == "arxiv-title":
                best["canonical"] = True
                merge_record(store, best, "canonical-arxiv")
                store[best["id"]]["canonical"] = True
                ident = best["id"]
            else:
                ident = best.get("DOI") or ("key:" + key)
                merge_record(store, {
                    "id": ident, "source": "crossref", "canonical": True,
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
                }, "canonical")
                store[ident]["canonical"] = True
            matched.append({"key": key, "title": title, "year": year, "id": ident, "score": bs,
                            "route": route, "status": state, "why": why})
            print("[canonical] %-20s %-18s %.2f (%s)  %s"
                  % (key, state, bs, route, ident), flush=True)
            if state == "matched-edition":
                print("             %s" % why, flush=True)
        else:
            unresolved.append({"key": key, "title": title, "year": year, "status": "unresolved",
                               "score": bs, "why": why,
                               "best_candidate": (cr_title(best) if best is not None else None),
                               "best_year": record_year(best),
                               "arxiv_route": ("not attempted" if arxiv_probe()
                                               else "NOT RUN: " + ARXIV_STATE["detail"])})
            print("[canonical] %-20s UNRESOLVED  %.2f  %s" % (key, bs, why), flush=True)
        time.sleep(1.0)
        _write(RAW, store)
    _write(STATUS, {"matched": matched, "unresolved": unresolved,
                    "arxiv_route": ("reachable" if arxiv_probe()
                                    else "NOT RUN: " + ARXIV_STATE["detail"])})
    print("canonical matched %d, unresolved %d" % (len(matched), len(unresolved)))


# The named objects this paper's claims are ABOUT.  An entry is kept only if it is on-subject by one
# of these; the lists are declarative and counted, and the drops are reported so nothing vanishes
# silently (the #142 lesson).
CORE_TERMS = ["auction", "mechanism design", "incentive compatibility", "scoring rule",
              "rank aggregation", "kendall", "leaderboard", "benchmark", "evaluation protocol",
              "construct validity", "goodhart", "gaming", "reward hacking", "winning", "bidding",
              "equilibrium", "social choice", "pairwise", "ranking", "measurement"]
SUPPORT_TERMS = ["evaluation", "metric", "score", "competition", "tournament", "selection",
                 "reproducibility", "validity", "reliability", "statistical", "comparison",
                 "agent", "language model", "robustness", "sensitivity", "distribution shift"]

# Off-domain noise: a broad query reaches work that shares a METHOD WORD while being about another
# subject.  Declared, applied to the TITLE only, and the count is reported.
OFF_DOMAIN = ["quantum", "qubit", "rydberg", "kagome", "hamiltonian", "vqe", "qaoa", "ansatz",
              "eigenstate", "photonic", "molecule", "chemistry", "protein", "drug discovery",
              "crispr", "gene expression", "galaxy", "cosmology", "stellar", "particle physics",
              "black hole", "weather", "climate model", "seismic"]


def _fold(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()) if s else ""


def classify(rec):
    """Keep / drop, with the reason.  Returns (keep, why)."""
    title = _fold(rec.get("title", ""))
    text = _fold(rec.get("title", "") + " " + rec.get("summary", ""))
    for bad in OFF_DOMAIN:
        if _fold(bad) in title:
            return False, "off-domain:%s" % bad
    for t in CORE_TERMS:
        if _fold(t) in text:
            return True, "core:%s" % t
    for t in SUPPORT_TERMS:
        if _fold(t) in text:
            return True, "support:%s" % t
    return False, "no-term"


def build_pool():
    with open(RAW, encoding="utf-8") as fh:
        store = json.load(fh)
    pool, dropped, kept_by = {}, {}, {}
    for key, rec in sorted(store.items()):
        if rec.get("canonical"):
            pool[key] = rec
            kept_by[key] = "canonical"
            continue
        ok, why = classify(rec)
        if ok:
            pool[key] = rec
            kept_by[key] = why
        else:
            dropped[why] = dropped.get(why, 0) + 1
    _write(POOL, pool)
    n_can = sum(1 for r in pool.values() if r.get("canonical"))
    print("pool: %d entries (%d canonical, %d discovered); dropped %d"
          % (len(pool), n_can, len(pool) - n_can, sum(dropped.values())))
    for why, n in sorted(dropped.items(), key=lambda kv: -kv[1])[:12]:
        print("   dropped %-28s %d" % (why, n))
    return pool


# ---------------------------------------------------------------------------------------------
BYID = os.path.join(REFDIR, "byid.txt")
SELECTED = os.path.join(REFDIR, "selected.json")
SELSTATUS = os.path.join(REFDIR, "selected-status.json")
SRC = os.path.join(HERE, "manuscript.src.md")
OUT = os.path.join(HERE, "manuscript.md")
KEY = r"[A-Za-z0-9_.:/-]+"
# a marker may name several works: `{{ref:a,b,c}}` renders as `[1,2,3]` in ONE bracket, because
# three adjacent brackets are a punctuation artefact and a reader cannot tell it from a typo
MARK = re.compile(r"\{\{ref:(%s(?:\s*,\s*%s)*)\}\}" % (KEY, KEY))


def _crossref_record(m):
    """Normalise a Crossref `message` into the store's shape, keeping its OWN year."""
    return {
        "id": (m.get("DOI") or "").lower(), "source": "crossref",
        "title": cr_title(m),
        "published": str(((m.get("issued") or {}).get("date-parts") or [[None]])[0][0] or ""),
        "issued": m.get("issued") or {},
        "authors": [" ".join(x for x in (a.get("given"), a.get("family")) if x).strip()
                    for a in (m.get("author") or [])],
        "container": (m.get("container-title") or [""])[0] if m.get("container-title") else "",
        "doi": m.get("DOI") or "",
        "type": m.get("type", ""),
    }


def fetch_by_id(ident):
    """One record, by the identifier the text prints.  Raises if the record cannot be fetched."""
    if ident.startswith("arxiv:"):
        aid = ident.split(":", 1)[1]
        url = "https://export.arxiv.org/api/query?id_list=%s&max_results=1" % urllib.parse.quote(aid)
        ents = arxiv_search_raw(url)
        if not ents:
            raise RuntimeError("arXiv id_list returned no entry")
        rec = ents[0]
        rec["verified_by"] = "arxiv-id"
        return rec
    if ident.startswith("doi:"):
        doi = ident.split(":", 1)[1]
        m = json.loads(_get("https://api.crossref.org/works/%s" % urllib.parse.quote(doi))
                       .decode("utf-8", "replace"))["message"]
        rec = _crossref_record(m)
        rec["verified_by"] = "doi"
        return rec
    raise RuntimeError("unknown identifier form: %s" % ident)


def byid():
    """Verify every INLINE identifier against the API that owns it.

    Why this stage exists: the draft cited four works by identifier while the store held none of
    them -- `arXiv:2609.04667`, `arXiv:2603.08371`, `arXiv:2609.33012` and `10.3386/w4480` were
    written into the prose from a note.  An identifier in the text and a record in the store are
    two different claims, and only the second one is verifiable.
    """
    if not os.path.exists(BYID):
        print("[byid] no %s -- nothing to verify" % os.path.relpath(BYID, HERE))
        return 1
    idents = [l.strip() for l in open(BYID, encoding="utf-8")
              if l.strip() and not l.strip().startswith("#")]
    store = {}
    if os.path.exists(RAW):
        with open(RAW, encoding="utf-8") as fh:
            store = json.load(fh)
    bad = 0
    for ident in idents:
        try:
            rec = fetch_by_id(ident)
        except Exception as e:                                   # noqa: BLE001
            print("[byid] %-24s FAILED: %s" % (ident, e))
            bad += 1
            continue
        store[rec["id"]] = rec
        store[rec["id"]]["found_by"] = ["byid"]
        print("[byid] %-24s -> %-14s %s (%s)"
              % (ident, rec["id"], rec["title"][:70], record_year(rec)))
        time.sleep(3.0)
    _write(RAW, store)
    print("[byid] verified %d, failed %d; store %d entries"
          % (len(idents) - bad, bad, len(store)))
    return 0 if bad == 0 else 1


def load_selected():
    with open(SELECTED, encoding="utf-8") as fh:
        return json.load(fh)


def resolve(key, raw):
    """A selected key -> its verified record, or None.

    Two key spaces exist and both are legitimate: a DISCOVERED work is keyed by the identifier the
    API gave it, while a CANONICAL work is keyed by the short name a sentence can read
    (`kendall1938`).  The canonical pass is where that second name was verified, so its map is the
    bridge -- and a key that resolves in neither place has no record and cannot be cited.
    """
    if key in raw:
        return raw[key]
    try:
        with open(STATUS, encoding="utf-8") as fh:
            st = json.load(fh)
    except (OSError, ValueError):
        return None
    for m in st.get("matched", []):
        if m["key"] == key:
            return raw.get(m["id"])
    return None


def select():
    """Check the SELECTION: every chosen key must be a verified record in the store.

    The selection is the author's judgement (which works this paper is obliged to know) written
    into `refs/selected.json`; this stage is the part that is not judgement -- it refuses a key
    whose record is not in the store, and it counts against the journal's threshold.
    """
    sel = load_selected()
    with open(RAW, encoding="utf-8") as fh:
        raw = json.load(fh)
    src = open(SRC, encoding="utf-8").read()
    cited = set(k.strip() for grp in MARK.findall(src) for k in grp.split(",") if k.strip())
    rows, missing, uncited = [], [], []
    for key, meta in sorted(sel.items()):
        rec = resolve(key, raw)
        if rec is None:
            missing.append(key)
            continue
        rows.append({"key": key, "record": rec.get("id"), "title": rec.get("title", ""),
                     "year": record_year(rec), "source": rec.get("source", ""),
                     "verified_by": rec.get("verified_by") or ("arXiv id" if rec.get("source") == "arxiv"
                                                               else "Crossref DOI"),
                     "section": meta.get("section", ""), "role": meta.get("role", ""),
                     "cited": key in cited})
        if key not in cited:
            uncited.append(key)
    stray = sorted(k for k in cited if k not in sel)
    _write(SELSTATUS, {"selected": rows, "missing": missing, "uncited": uncited, "stray": stray})
    print("select: %d chosen, %d with a verified record, %d missing a record"
          % (len(sel), len(rows), len(missing)))
    if missing:
        print("   MISSING RECORD (cannot be cited): %s" % ", ".join(missing[:20]))
    if uncited:
        print("   chosen but NOT CITED in the manuscript: %d -- %s"
              % (len(uncited), ", ".join(uncited[:12])))
    if stray:
        print("   cited in the manuscript but not chosen: %s" % ", ".join(stray[:12]))
    print("   threshold: %d chosen against the journal's 100" % len(rows))
    ok = not missing and not uncited and not stray and len(rows) >= 100
    print("SELECT:", "OK" if ok else "NOT READY")
    return 0 if ok else 1


# ---------------------------------------------------------------------------------------------
# The bibliography's ENTRY FORM.  The journal's *Presentation requirements* names one order --
# `[n] `, authors `Family, I.`, the year in parentheses, the title in title case, the venue or the
# identifier, a resolvable URL, and the entry closing with its one-line `Difference: ...` -- and
# states that it is a test over EVERY entry rather than over the list.  So this is a renderer with
# rules, not a formatter with defaults: every component below states the rule it applies and the
# measurement that produced it, because each of them was a defect on the first rendered run
# (2026-10-20: `[n]` markers 0/130, author form 0/130, year-in-parentheses 0/130, Difference 0/130).
DIFFS = os.path.join(REFDIR, "differences.json")

# a family name may carry a particle, and the particle belongs to the family (`van Beek`, not `Beek`)
PARTICLES = {"van", "von", "de", "der", "den", "da", "di", "du", "la", "le", "del", "della",
             "bin", "al", "ter", "ten", "st.", "mac", "mc"}

# Words that stay lower-case inside a title (the first and last word are always capitalised).
SMALL = {"a", "an", "the", "of", "for", "and", "or", "nor", "but", "in", "on", "at", "to", "by",
         "with", "from", "as", "is", "are", "was", "were", "be", "not", "into", "onto", "over",
         "under", "between", "among", "through", "without", "within", "per", "via", "vs", "vs.",
         "upon", "off", "than", "that", "this", "these", "those", "its", "it", "we", "you", "how",
         "when", "where", "why", "what", "which", "who", "so", "if", "then", "else", "both",
         "each", "all", "any", "some", "no", "can", "do", "does", "did"}

# An acronym is a word that is entirely upper-case AND short.  The threshold is a judgment written
# down so a reader can disagree with it: `LLM`, `AI`, `ELO`, `NP`, `RL`, `GPU`, `API`, `MCP` are all
# <= 5 characters, while an all-caps TITLE WORD (`COUNTERSPECULATION`) is not an acronym and is the
# form a registry stores a title in -- which is what the title-case rule exists to normalise.
ACRONYM_MAX = 5


def _mixed_case_zero_width(tok):
    """A registry's ALL-CAPS token -> mixed case, and nothing else.

    The house rule is that the family name is printed in mixed case, *never* in the capitals a
    registry holds it in -- so this function only ever LOWERS letters and never invents one.
    """
    letters = [c for c in tok if c.isalpha()]
    if len(letters) < 2 or not all(c.isupper() for c in letters):
        return tok
    out, seen = [], False
    for c in tok:
        if not c.isalpha():
            out.append(c)
            continue
        out.append(c.upper() if not seen else c.lower())
        seen = True
    return "".join(out)


def _initials(given):
    """`Andrew M.` -> `A. M.`; `Wei-Jung` -> `W.`  (one initial per whitespace-separated token)."""
    out = []
    for tok in given.replace(".", " ").split():
        if tok and tok[0].isalpha():
            out.append(tok[0].upper() + ".")
    return " ".join(out)


def split_author(name):
    """`Given Family` -> (family, given).  The split is taken from the RIGHT, and particles move
    left: `Andries van Beek` -> (`van Beek`, `Andries`).  The first rendered run printed 120 of 130
    entries with a forename first because the record's field order was used unchanged."""
    toks = [t for t in name.replace("\u00a0", " ").split() if t]
    if not toks:
        return "", ""
    i = len(toks) - 1
    while i - 1 >= 0 and toks[i - 1].lower().strip(",") in PARTICLES:
        i -= 1
    return " ".join(toks[i:]), " ".join(toks[:i])


def author_str(rec, key=None):
    """The authors in the house form: `Family, I.`, `A, X.; B, Y.` up to three, `et al.` for four or
    more -- ONE period, the family name first, family names in mixed case.

    Two members of the rule are exempt and are named here rather than left to a default:
      * a record whose author field is EMPTY -- the entry names the body responsible where the work
        states one, and otherwise records the absence by naming the record that was read, because an
        unnamed `n.a.` is a position no reviewer can check;
      * a record that gives ONE author token and no more -- a mononym or a corporate name -- prints
        that token alone, never padded to `Family, I.` (an initial no record carries is a fabricated
        author).
    """
    au = [html.unescape(a).strip().rstrip(".") for a in (rec.get("authors") or []) if a and a.strip()]
    if not au:
        # The absence is RECORDED BY NAMING THE RECORD THAT WAS READ, in the author position itself,
        # so a reader can check it.  Two forms a first version printed are ruled out on measurement:
        #   `n.a.` names no record (the editorial return of 2026-10-20, item 1);
        #   the CONTAINER title is not a responsible body -- `Economics of Visual Art` is the
        #   containing Cambridge Element, and printing a container in the author position states an
        #   authorship the record does not.  Where the work states a body, this rule names it; a
        #   container is not that, and the DOI is what a reader can open.
        src = "Crossref" if rec.get("source") == "crossref" else "arXiv"
        ident = rec.get("doi") or rec.get("id")
        field = "DOI" if str(ident).startswith("10.") else "identifier"
        return "author not established on %s for the %s %s" % (src, field, ident)
    parts = []
    for name in au:
        fam, giv = split_author(name)
        fam = _mixed_case_zero_width(fam)
        ini = _initials(giv)
        parts.append("%s, %s" % (fam, ini) if ini else fam)
    if len(parts) == 1:
        return parts[0]
    if len(parts) <= 3:
        return "; ".join(parts[:-1]) + "; " + parts[-1]
    return parts[0] + "; et al."


def _caps_title(t):
    """True when the record stores its WHOLE title in capitals -- a registry export, not an acronym.

    This is the only signal that separates a word from an acronym without a dictionary: `CORE` (4)
    and `GAMES` (5) differ by nothing in shape, but `CORE` arrives inside a normally-cased title and
    `GAMES` arrives inside a title whose every word is capitalised. Measured over the 132 selected
    works at R673, exactly **2** records are caps-titles ([19] and [127]); the other 19 all-caps
    tokens all sit in normally-cased titles, which is why the acronym guard must keep them (and why
    `INCONVENIENT`, the name of a benchmark, must stay as its record spells it).

    ASCII letters only: the mathematical italic in `𝑛-PERSON` is a letter but is neither upper nor
    lower, and testing it directly would make [127] fail the very test meant to catch it.
    """
    for w in (t or "").split(" "):
        asc = [c for c in w if c.isascii() and c.isalpha()]
        if len(asc) > 1 and not all(c.isupper() for c in asc):
            return False
    return bool((t or "").strip())


def title_case(title):
    """The title in title case, WITHOUT touching what a word already states.

    The rule this implements is deliberately conservative, because a title-caser that re-cases freely
    is a fabricator: a word that already carries an upper-case letter after its first position is
    left exactly as the record spells it (`ERPBench`, `Goodhart's`, `Chatterjee's`, `INCONVENIENT`),
    an all-caps word is normalised only when it is too long to be an acronym, and a word inside a
    hyphenation is treated as a word.
    """
    t = html.unescape(title or "").strip().rstrip("*").strip()
    if not t:
        return ""
    words = t.split(" ")
    n = len(words)
    out = []
    for i, w in enumerate(words):
        core = w.strip("\u002c\u003b\u003a\u0021\u003f\u0028\u0029\u0027")
        if not core:
            out.append(w)
            continue
        # A word the record already mixed-cases is left alone -- unless the whole title is a caps
        # export, in which case every word is a word and the two "leave it exactly as stored"
        # shortcuts below are precisely what printed the registry's capitals (R673: [19], [127]).
        caps_export = _caps_title(t)
        has_inner_upper = any(c.isupper() for c in core[1:])
        if has_inner_upper and not caps_export:
            out.append(w)
            continue
        letters = [c for c in core if c.isalpha()]
        if letters and all(c.isupper() for c in letters):
            if len(letters) <= ACRONYM_MAX and not caps_export:
                out.append(w)                      # `LLM`, `AI`, `ELO` are acronyms, not words
                continue
            core_norm = _mixed_case_zero_width(core)      # COUNTERSPECULATION -> Counterspeculation
        else:
            core_norm = core
        # a hyphenated word is title-cased per part
        bits = []
        for k, part in enumerate(core_norm.split("-")):
            if not part:
                bits.append(part)
                continue
            low = part.lower()
            if 0 < i < n - 1 and low in SMALL and k == 0:
                bits.append(low)
            else:
                bits.append(part[0].upper() + part[1:] if part[0].isalpha() else part)
        newcore = "-".join(bits)
        out.append(w.replace(core, newcore, 1))
    return " ".join(out)


def venue_str(rec):
    if rec.get("source") == "arxiv":
        return "arXiv:%s" % rec["id"]
    c = html.unescape(rec.get("container") or "")
    return c if c else ("DOI:%s" % rec.get("doi", rec["id"]))


def link_str(rec):
    if rec.get("source") == "arxiv":
        return "https://arxiv.org/abs/%s" % rec["id"]
    doi = rec.get("doi") or (rec["id"] if rec["id"].startswith("10.") else "")
    return "https://doi.org/%s" % doi if doi else ""


def entry_line(i, key, rec, diffs):
    """One bibliography entry, in the house order, with its own closing difference."""
    y = record_year(rec)
    year = "(%s)" % y if y else "(year not stated on the record)"
    diff = diffs.get(key)
    if not diff:
        raise RuntimeError("no stated difference for `%s`" % key)
    return ("[%d] %s %s. %s. %s. %s -- Difference: %s"
            % (i, author_str(rec, key), year, title_case(rec.get("title", "")).rstrip("."),
               venue_str(rec), link_str(rec), diff.strip()))


def render():
    """Expand `{{ref:key}}` into numbered citations and a References section.

    Numbered in ORDER OF FIRST APPEARANCE, and every number is used.  The stage fails -- writing
    nothing -- on any of: a marker whose record is not in the store, a selection entry that the
    body never cites, fewer than 100 cited works.  A bibliography that renders while the body does
    not cite it is padding, so the check is the render, not a separate count.
    """
    sel = load_selected()
    with open(RAW, encoding="utf-8") as fh:
        raw = json.load(fh)
    src = open(SRC, encoding="utf-8").read()

    order, bad = [], []

    def number(m):
        nums = []
        for key in [k.strip() for k in m.group(1).split(",") if k.strip()]:
            rec = resolve(key, raw)
            if key not in sel or rec is None:
                bad.append(key)
                return m.group(0)
            if key not in order:
                order.append(key)
            nums.append(order.index(key) + 1)
        return "[%s]" % ",".join(str(n) for n in nums)

    body = MARK.sub(number, src)
    if bad:
        print("render: REFUSED -- %d marker(s) without a verified record: %s"
              % (len(set(bad)), ", ".join(sorted(set(bad))[:12])))
        return 1
    uncited = [k for k in sel if k not in order]
    if uncited:
        print("render: REFUSED -- %d chosen work(s) never cited in the body: %s"
              % (len(uncited), ", ".join(sorted(uncited)[:12])))
        return 1
    if len(order) < 100:
        print("render: REFUSED -- %d cited works against the journal's 100" % len(order))
        return 1

    diffs = {}
    if os.path.exists(DIFFS):
        with open(DIFFS, encoding="utf-8") as fh:
            diffs = json.load(fh)
    missing_diff = [k for k in order if not diffs.get(k)]
    if missing_diff:
        print("render: REFUSED -- %d cited work(s) carry no stated difference: %s"
              % (len(missing_diff), ", ".join(missing_diff[:12])))
        return 1
    lines = [body.rstrip(), "", "## References", ""]
    for i, key in enumerate(order, 1):
        # A BLANK LINE BETWEEN ENTRIES IS LOAD-BEARING.  Consecutive `[n]` lines are ONE paragraph to
        # every CommonMark renderer -- GitHub's preview included -- so without the blank line the
        # entry boundaries vanish and a trailing URL is read as part of the next entry's sentence.
        # Ordered-list markers (`1. `) would protect the layout instead, but the house marker is
        # `[n] ` and the protection has to come from the separation (`refgate.py` prints it as
        # `block form:`; its clean form is `0 of them not separated`).
        lines.append(entry_line(i, key, resolve(key, raw), diffs))
        lines.append("")
    text = "\n".join(lines) + "\n"
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, OUT)
    print("render: OK -- %d cited works, %d markers, %d lines -> %s"
          % (len(order), len(MARK.findall(src)), text.count("\n"), os.path.basename(OUT)))
    return 0


# ---------------------------------------------------------------------------------------------
def repo_root_of(start):
    """The journal repository root above `start`, or None -- found by the gate it is recognised by.

    The gate is not vendored in this package: it belongs to the journal (`.github/tools/`), so a
    report that quoted its readings without running it would be quoting a remembered output. When
    the package is read outside the repository there is no root, and the report says NOT RUN.
    """
    d = os.path.abspath(start)
    for _ in range(8):
        if os.path.exists(os.path.join(d, ".github", "tools", "refgate.py")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def run_refgate(root, rel_manuscript):
    """Run the journal's gate from the repository root and return its output lines."""
    import subprocess
    try:
        pr = subprocess.run([sys.executable, ".github/tools/refgate.py", rel_manuscript],
                            cwd=root, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return ["(the gate could not be run: %s)" % exc]
    out = (pr.stdout or "") + (pr.stderr or "")
    return [l.rstrip() for l in out.strip().splitlines()]


def checkdoc():
    """Write reference-check.md FROM the verified status -- never by hand.

    Three states, because two would lie:
      matched           the work, in the edition the citation names
      matched-edition   the work, but the registered record is another edition; the year each
                        citation prints must then be the ORIGINAL's, with the record named
      unresolved        no record at this title+year; listed with the near-miss so a reader can
                        see what the search nearly took
    """
    with open(STATUS, encoding="utf-8") as fh:
        st = json.load(fh)
    with open(RAW, encoding="utf-8") as fh:
        raw = json.load(fh)
    matched = st["matched"]
    unresolved = st["unresolved"]
    # the bibliography's own records, for the two duties the report owes beyond the canon pass: the
    # no-author exemption is read off the DECLARED bibliography (the 130), not the canon list of 39.
    try:
        with open(SELSTATUS, encoding="utf-8") as fh:
            _sst = json.load(fh)
    except (OSError, ValueError):
        _sst = None
    noauthor = []
    if _sst:
        for r in _sst["selected"]:
            rec = raw.get(r.get("record") or "")
            if rec is not None and not (rec.get("authors") or []):
                noauthor.append((r["key"], rec))
    # probe at GENERATION time: the doc's statement about a route must be current when it is
    # written, not a replay of what the discovery run saw hours ago
    # TWO facts, kept apart because they answer different questions.  (i) Which route VERIFIED each
    # entry -- a property of the record, read off the carried status file.  (ii) Whether the arXiv API
    # answers a probe at GENERATION time -- a property of this moment, and a transient timeout there
    # says nothing about entries verified earlier.  Publishing only (ii) made the report contradict its
    # own table: it read "arXiv: NOT RUN (timed out)" above rows whose route is `arxiv-title`.
    n_arx = len([m for m in matched if m["route"] == "arxiv-title"])
    if arxiv_probe():
        probe = "answered at generation"
    else:
        probe = "NOT RUN at generation: %s" % ARXIV_STATE["detail"]
    # no bold around the whole cell: the phrase already carries bold inside it, and nested emphasis
    # renders as a literal run of asterisks (caught on the first generated copy, 2026-10-20)
    arx = ("%d entr%s verified by this route (recorded at match time); live probe: %s"
           % (n_arx, "y" if n_arx == 1 else "ies", probe))

    lines = []
    lines.append("# issue #141 -- reference verification")
    lines.append("")
    lines.append("Generated by `refscan141.py --checkdoc` from `refs/canonical-status.json`. Do not")
    lines.append("hand-edit: edit the canonical list or the matcher, then regenerate.")
    lines.append("")
    lines.append("**Verification method.** Every entry is found **by title** against Crossref (two")
    lines.append("declarative routes: `query.bibliographic` and `query.title`) and accepted only on a")
    lines.append("**two-test** verdict -- title coverage AND the record's own year. A title score")
    lines.append("alone is not a match: on this list, `Optimal Multi-unit Auctions` (1989) scores")
    lines.append("0.80 against `Optimal multi-unit combinatorial auctions` (2011), a different")
    lines.append("paper, and `Equilibrium Points in N-Person Games` scores 1.00 against a 2020")
    lines.append("reprint of the 1950 work. No entry is ever entered on a remembered DOI.")
    lines.append("")
    lines.append("**A route that could not run is named, not silently skipped.**")
    lines.append("")
    lines.append("| route | state |")
    lines.append("|---|---|")
    lines.append("| Crossref (by title) | ran |")
    lines.append("| arXiv (by title / `search_query`) | %s |" % arx)
    lines.append("")
    if "NOT RUN" in str(probe):
        lines.append("The arXiv leg could not be probed at generation time. It is the only route that reaches the")
        lines.append("works published without a DOI (the four §10 comparisons among them), so the")
        lines.append("unresolved set below is **not** evidence that those works do not exist -- it is")
        lines.append("evidence about the routes that ran. They are carried as unresolved, never")
        lines.append("entered on a remembered identifier.")
        lines.append("")
    # ---- duty (ii) of the journal's citation item: COVERAGE AND AMBIGUITY, read by the journal's
    # own gate.  The item names the command and the directory it is run from, so this section runs
    # exactly that and quotes what it printed -- the three readings are then resolved here rather
    # than treated as lines the verdict cleared.
    lines.append("## Coverage and ambiguity -- the journal's own gate, run from the repository root")
    lines.append("")
    gate_dir = repo_root_of(HERE)
    ms = os.path.join(HERE, "manuscript.md")
    if gate_dir is None:
        lines.append("**NOT RUN** -- `.github/tools/refgate.py` is not in this tree (the package was")
        lines.append("read outside the journal repository). The gate is the editor's instrument and it")
        lines.append("is not vendored here, so no reading is quoted rather than a remembered one.")
    else:
        rel = os.path.relpath(ms, gate_dir)
        shown = "python3 .github/tools/refgate.py %s" % rel
        out = run_refgate(gate_dir, rel)
        lines.append("```")
        lines.append("$ " + shown)
        lines.extend(out if out else ["(the tool produced no output)"])
        lines.append("```")
        lines.append("")
        if out:
            lines.append("Each of its three readings, resolved:")
            lines.append("")
            lines.append("- **`entries=` / `in-text cited numbers=`** -- the count and the coverage. Every")
            lines.append("  entry is cited at least once and no citation lacks an entry.")
            lines.append("- **`block form:`** -- the layout. `[n] ` markers do **not** protect themselves the")
            lines.append("  way an ordered-list marker does: consecutive `[n]` lines are one paragraph to a")
            lines.append("  CommonMark renderer, so the blank line between entries is what makes the")
            lines.append("  boundaries visible on the rendered page. The reading must be `0 of them not")
            lines.append("  separated`, and it is -- the renderer emits the blank line as a load-bearing")
            lines.append("  part of the entry set, not as decoration.")
            lines.append("- **`author form:`** -- the author component. The short count is the rule's own")
            lines.append("  exemption, named entry by entry in the section below: a record whose author")
            lines.append("  field is empty prints an absence that names the record read. No entry prints")
            lines.append("  the ALL-CAPS form a registry stores, and none carries a character reference.")
    lines.append("")
    lines.append("## Entries whose record carries no author (%d)" % len(noauthor))
    lines.append("")
    if noauthor:
        lines.append("The journal's author rule exempts a work whose record carries no author, on the")
        lines.append("condition that the **absence is recorded by naming the record that was read** --")
        lines.append("the same line the bibliography prints, so a reviewer can check it. `n.a.` failed")
        lines.append("that condition (it names no record), and so did printing the CONTAINER title in")
        lines.append("the author position (a container is not a responsible body: it states an")
        lines.append("authorship the record does not).")
        lines.append("")
        lines.append("| key | record read | printed in the author position |")
        lines.append("|---|---|---|")
        for key, rec in noauthor:
            lines.append("| `%s` | `%s` | %s |" % (key, rec.get("id"), author_str(rec, key)))
    else:
        lines.append("None: every record in the bibliography carries at least one author.")
    lines.append("")
    lines.append("## Matched (%d)" % len([m for m in matched if m["status"] == "matched"]))
    lines.append("")
    lines.append("| key | declared | record | year | title score | route |")
    lines.append("|---|---|---|---|---|---|")
    for m in sorted(matched, key=lambda x: x["key"]):
        if m["status"] != "matched":
            continue
        r = raw.get(m["id"], {})
        lines.append("| `%s` | %d | `%s` | %s | %.2f | %s |"
                     % (m["key"], m["year"], m["id"], record_year(r), m["score"], m["route"]))
    lines.append("")
    ed = [m for m in matched if m["status"] == "matched-edition"]
    lines.append("## Matched, but as a DIFFERENT EDITION (%d)" % len(ed))
    lines.append("")
    if ed:
        lines.append("The work is the right one; the registered record is another edition. The")
        lines.append("citation prints the **original** year and names the record actually verified --")
        lines.append("printing the reprint's year as the paper's year is a false statement about the")
        lines.append("work, and a title score cannot see it.")
        lines.append("")
        lines.append("| key | declared | record | record year | why |")
        lines.append("|---|---|---|---|---|")
        for m in sorted(ed, key=lambda x: x["key"]):
            r = raw.get(m["id"], {})
            lines.append("| `%s` | %d | `%s` | %s | %s |"
                         % (m["key"], m["year"], m["id"], record_year(r), m["why"]))
    lines.append("")
    lines.append("## Unresolved (%d)" % len(unresolved))
    lines.append("")
    lines.append("| key | declared | best score | nearest record found | why not entered |")
    lines.append("|---|---|---|---|---|")
    for u in sorted(unresolved, key=lambda x: x["key"]):
        lines.append("| `%s` | %s | %.2f | %s | %s |"
                     % (u["key"], u.get("year"), u["score"],
                        (u.get("best_candidate") or "-")[:58], u["why"]))
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("- canonical entries declared: **%d**" % (len(matched) + len(unresolved)))
    lines.append("- matched: **%d** (of which %d are another edition)" % (len(matched), len(ed)))
    lines.append("- unresolved: **%d**" % len(unresolved))
    lines.append("- arXiv route: **%s**" % arx)
    lines.append("")
    lines.append("## The submitted bibliography (%s)" % "from `refs/selected.json`")
    lines.append("")
    lines.append("The journal requires **>= 100 references, every one cited in the body**. The")
    lines.append("bibliography below is the one `--render` numbers into `manuscript.md`; each row is")
    lines.append("one cited work, the identifier of the real record it resolved to, and the route")
    lines.append("that verified it. `verify-by` says how the record was obtained: `arxiv-id` and")
    lines.append("`doi` mean the identifier the text prints was fetched from the API that owns it;")
    lines.append("`Crossref`/`arXiv id` mean the record came from the by-title pass or the")
    lines.append("discovery pass, which search by the work's own title.")
    lines.append("")
    try:
        with open(SELSTATUS, encoding="utf-8") as fh:
            sst = json.load(fh)
    except (OSError, ValueError):
        sst = None
    if sst is None:
        lines.append("**NOT RUN** -- `refs/selected-status.json` does not exist; run `--select`.")
    else:
        lines.append("- chosen: **%d**" % len(sst["selected"]))
        lines.append("- with a verified record: **%d**"
                     % len([r for r in sst["selected"] if r.get("record")]))
        lines.append("- cited in the body: **%d**" % len([r for r in sst["selected"] if r["cited"]]))
        lines.append("- missing a record: **%d**  ·  chosen but never cited: **%d**  ·  "
                     "cited but undeclared: **%d**"
                     % (len(sst["missing"]), len(sst["uncited"]), len(sst["stray"])))
        lines.append("")
        lines.append("| # | key | record | title | year | verify-by | cited |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, r in enumerate(sst["selected"], 1):
            lines.append("| %d | `%s` | `%s` | %s | %s | %s | %s |"
                         % (i, r["key"], r.get("record") or "-",
                            (r.get("title") or "")[:70].replace("|", "/"),
                            r.get("year") or "-", r.get("verified_by") or "-",
                            "yes" if r["cited"] else "**NO**"))
    lines.append("")
    # the report lives at the PACKAGE ROOT, because that is the path the journal's completeness
    # bar names (`papers/issue-<N>/reference-check.md`).  Generated one directory deeper, it would be
    # a correct report at a path the editor does not look at -- and a hand-copy placed at the root
    # would be a second carrier that goes stale the next time this comment is not re-run.
    path = os.path.join(HERE, "reference-check.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s (%d matched, %d edition, %d unresolved)"
          % (os.path.relpath(path, HERE), len(matched) - len(ed), len(ed), len(unresolved)))
    return 0


def main(argv):
    if "--selftest" in argv:
        ok = True

        def holds(name, cond):
            nonlocal ok
            print("[%-62s] %s" % (name, "ok" if cond else "*** FAIL ***"))
            ok = ok and cond

        # the title score is the SMALLER coverage: a short generic title must not score 1.00
        holds("a short title does not match a long one",
              title_score("Auction Theory", "Auction Theory: A Guide to the Literature") < 0.8)
        holds("an exact title scores 1.00", abs(title_score("Optimal Auctions", "Optimal auctions") - 1.0) < 1e-9)
        holds("a reordered title still matches",
              title_score("Auctions versus Negotiations", "Negotiations Versus Auctions") == 1.0)
        # an old-style arXiv id survives, a version suffix does not
        holds("old-style archive prefix is kept", arxiv_id("http://arxiv.org/abs/cs/0609060v2") == "cs/0609060")
        holds("a version suffix is stripped", arxiv_id("https://arxiv.org/abs/2609.04667v3") == "2609.04667")
        # the two-route finder: a strong route must beat a weak one
        weak = lambda t: [{"title": ["Something Else Entirely"], "DOI": "10.1/weak"}]
        strong = lambda t: [{"title": ["Optimal Auction Design"], "DOI": "10.1/strong"}]
        best, sc, route = crossref_find("Optimal Auction Design",
                                        routes=(("weak", weak), ("strong", strong)))
        holds("the strong route wins over the weak one",
              route == "strong" and best["DOI"] == "10.1/strong" and sc > 0.8)
        # PLANT: a corpus with only the weak route must report UNRESOLVED, not enter the wrong record
        best2, sc2, _r2 = crossref_find("Optimal Auction Design", routes=(("weak", weak),))
        holds("PLANT: one weak route alone is unresolved, not a wrong entry", sc2 < 0.8)
        # merge is honest about its three states
        st = {}
        holds("merge reports 'new'", merge_record(st, {"id": "x", "title": "T"}, "q1") == "new")
        holds("merge reports 'seen'", merge_record(st, {"id": "x", "title": "T"}, "q1") == "seen")
        holds("merge reports 'amended' on a second provenance",
              merge_record(st, {"id": "x", "title": "T"}, "q2") == "amended")
        holds("both provenances are recorded", st["x"]["found_by"] == ["q1", "q2"])
        # classify keeps an on-subject title and drops an off-domain one
        holds("an on-subject title is kept",
              classify({"title": "Optimal Auction Design", "summary": ""})[0])
        holds("an off-domain title is dropped even with a soft term",
              not classify({"title": "Quantum annealing for the protein folding benchmark",
                            "summary": "ranking evaluation"})[0])
        # ---- the verdict: TWO tests, each with the real defect it was found on
        def rec(title, year):
            return {"title": [title], "issued": {"date-parts": [[year]]}}

        # the measured wrong-paper match: different title, adjacent words, 0.80
        holds("PLANT: a 0.80 title match to a DIFFERENT paper is unresolved",
              verdict(rec("Optimal multi-unit combinatorial auctions", 2011), 0.80, 1989)[0]
              == "unresolved")
        # the measured right-work/wrong-edition match: exact title, 70 years out
        # this is the MEASURED nash1950 case, whose reprint record names John F. Nash; the author is
        # carried here because the edition state now requires it to be corroborated (see `verdict`)
        nash_reprint = rec("EQUILIBRIUM POINTS IN n-PERSON GAMES", 2020)
        nash_reprint["author"] = [{"family": "Nash"}]
        holds("PLANT: an exact title in the wrong edition is matched-edition, not matched",
              verdict(nash_reprint, 1.00, 1950)[0] == "matched-edition")
        holds("an exact title with the declared year is matched",
              verdict(rec("Optimal Auction Design", 1981), 1.00, 1981)[0] == "matched")
        holds("PLANT: an exact title whose record carries NO author and a year gap is unresolved",
              verdict(rec("Auction Theory", 2021), 1.00, 2002)[0] == "unresolved")
        holds("PLANT: an exact title in a later edition WITH an author is matched-edition",
              verdict({"title": ["Auction Theory"], "author": [{"family": "Krishna"}],
                       "issued": {"date-parts": [[2010]]}}, 1.00, 2002)[0] == "matched-edition")
        holds("a near title WITH the year is accepted",
              verdict(rec("A Theory of Auctions and Competitive Bidding", 1982), 0.95, 1982)[0]
              == "matched")
        holds("a near title WITHOUT the year is not accepted",
              verdict(rec("A Theory of Auctions and Competitive Bidding", 2001), 0.95, 1982)[0]
              == "unresolved")
        holds("no record is unresolved", verdict(None, 0.0, 1981)[0] == "unresolved")
        # the year is read from either source shape
        holds("an arXiv-style year is read",
              record_year({"published": "2026-09-04"}) == 2026)
        holds("a Crossref-style year is read",
              record_year({"issued": {"date-parts": [[1950, 1]]}}) == 1950)
        holds("a missing year is None, not a guess", record_year({"title": ["x"]}) is None)

        # ---- the SELECTION and the RENDER: each guard must be shown to REFUSE the defect it
        # names, on a temporary tree, so the demonstration never edits the real package.  A guard
        # nobody has seen fire is a guard that may be a comment.
        import tempfile
        tmpd = tempfile.mkdtemp(prefix="refscan-plant-")

        def plant(files, fn):
            g = globals()
            # EVERY path a stage writes must be redirected.  The first version of this harness
            # forgot SELSTATUS, and the 100-work plant's status file overwrote the real
            # `refs/selected-status.json` -- a test that edits the artefact it is testing
            # (measured 2026-10-20: `--checkdoc` then reported the plant's 100, not the 130).
            old = {k: g[k] for k in ("RAW", "STATUS", "SELECTED", "SELSTATUS", "SRC", "OUT",
                                      "DIFFS")}
            try:
                for name, obj in files.items():
                    path = os.path.join(tmpd, name)
                    with open(path, "w", encoding="utf-8") as fh:
                        if isinstance(obj, str):
                            fh.write(obj)
                        else:
                            json.dump(obj, fh)
                # DIFFS is redirected too, and its content is DERIVED from the plant's own store:
                # an unredirected one made the real `differences.json` decide the plant (every
                # plant key is absent from it, so the clean render refused and wrote nothing --
                # measured 2026-10-20, the selftest died on a missing `out.md`).
                if "differences.json" not in files:
                    pool = files.get("raw.json") or {}
                    with open(os.path.join(tmpd, "differences.json"), "w", encoding="utf-8") as fh:
                        json.dump({k: "plant difference for %s" % k for k in pool}, fh)
                g.update(RAW=os.path.join(tmpd, "raw.json"),
                         STATUS=os.path.join(tmpd, "status.json"),
                         SELECTED=os.path.join(tmpd, "selected.json"),
                         SELSTATUS=os.path.join(tmpd, "selected-status.json"),
                         SRC=os.path.join(tmpd, "src.md"),
                         OUT=os.path.join(tmpd, "out.md"),
                         DIFFS=os.path.join(tmpd, "differences.json"))
                return fn()
            finally:
                g.update(old)

        def quiet(fn, *a):
            """Run a stage with its stdout swallowed; return its exit code."""
            import contextlib, io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = fn(*a)
            return rc, buf.getvalue()

        def mkpool(n):
            raw, sel = {}, {}
            for i in range(n):
                raw["k%03d" % i] = {"id": "k%03d" % i, "source": "arxiv", "title": "Work %d" % i,
                                    "published": "2020-01-01", "authors": ["A. Author"]}
                sel["k%03d" % i] = {"section": "S1", "role": "plant"}
            return raw, sel

        raw, sel = mkpool(100)
        src = " ".join("{{ref:k%03d}}" % i for i in range(100))
        files = {"raw.json": raw, "status.json": {"matched": [], "unresolved": []},
                 "selected.json": sel, "src.md": src}
        rc, out = plant(files, lambda: quiet(render))
        holds("PLANT: a clean 100-work render succeeds",
              rc == 0 and "100 cited works" in out and "REFUSED" not in out)
        holds("PLANT: a comma marker renders as ONE bracket",
              "[1] [2] [3]" in plant(dict(files, **{"src.md": "{{ref:k000,k001,k002}}"}),
                                     lambda: (quiet(render), open(os.path.join(tmpd, "out.md"),
                                                                  encoding="utf-8").read())[1]))
        # the defect: a cited work with NO record in the store
        raw2 = {k: v for k, v in raw.items() if k != "k007"}
        rc, out = plant(dict(files, **{"raw.json": raw2}), lambda: quiet(render))
        holds("PLANT: a marker with no record is REFUSED", rc == 1 and "no verified record" in out
              or "without a verified record" in out)
        # the defect: a selected work the body never cites
        rc, out = plant(dict(files, **{"src.md": src.replace("{{ref:k042}}", "k042")}),
                        lambda: quiet(render))
        holds("PLANT: a selected-but-uncited work is REFUSED", rc == 1 and "never cited" in out)
        # the defect: a cited work whose entry would carry NO stated difference.  The entry line
        # ends in that claim, so an absent one prints a hole in the bibliography rather than a
        # shorter entry -- the render refuses instead.
        dd = {k: "plant difference for %s" % k for k in raw}
        dd.pop("k009")
        rc, out = plant(dict(files, **{"differences.json": dd}), lambda: quiet(render))
        holds("PLANT: a cited work with no stated difference is REFUSED",
              rc == 1 and "no stated difference" in out)
        # the defect: below the journal's threshold
        raw3, sel3 = mkpool(99)
        rc, out = plant({"raw.json": raw3, "status.json": {"matched": [], "unresolved": []},
                         "selected.json": sel3,
                         "src.md": " ".join("{{ref:k%03d}}" % i for i in range(99))},
                        lambda: quiet(render))
        holds("PLANT: 99 works are REFUSED against the 100 threshold", rc == 1 and "100" in out)
        # the defect: a key the body cites but the selection never declared
        rc, out = plant(dict(files, **{"src.md": src + " {{ref:9100.00000/x}}"}),
                        lambda: quiet(select))
        holds("PLANT: an undeclared citation is reported as stray",
              "not chosen" in out and "NOT READY" in out)
        # resolve(): a canonical key reaches its record through the canonical map, an unknown key not
        rc = plant({"raw.json": {"10.1/x": {"id": "10.1/x", "title": "Canon"}},
                    "status.json": {"matched": [{"key": "canon", "id": "10.1/x"}], "unresolved": []},
                    "selected.json": {}, "src.md": ""},
                   lambda: (resolve("canon", json.load(open(os.path.join(tmpd, "raw.json")))) is not None,
                            resolve("nope", json.load(open(os.path.join(tmpd, "raw.json")))) is None))
        holds("a canonical key resolves through its record; an unknown key does not", rc == (True, True))

        print("REFSCAN:", "ALL PASS" if ok else "A CHECK IS DECORATION")
        return 0 if ok else 1

    if "--discover" in argv:
        discover()
        return 0
    if "--canonical" in argv:
        canonical()
        return 0
    if "--pool" in argv:
        build_pool()
        return 0
    if "--reaudit" in argv:
        return reaudit()
    if "--byid" in argv:
        return byid()
    if "--select" in argv:
        return select()
    if "--render" in argv:
        return render()
    if "--checkdoc" in argv:
        return checkdoc()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
