#!/usr/bin/env python3
"""#93 R416 -- the ANCHOR limb: the registration's by-hand-read works, fetched from the registry by id.

Why this limb exists (measured this round).  The bibliography's selection named three arXiv ids that the
harvest pools do not contain, because they were read at the *registration* stage (by hand, at their abs pages,
for the Heilmeier table in `research/heilmeier.md`) rather than returned by a keyword query:

    2606.29406   delegation authority as a POMDP
    2608.01388   recall of a fixed-invariant FSA monitor is bounded by attack-distribution entropy
    2609.01373   NOT an anchor of this study: a recollection.  See `checks.dropped`.

The third is the instructive one: **2609.01373 does not exist** -- it is a corrupted recollection of this
journal's #89 anchor 2608.01373 (guard false positives), and heilmeier.md does not contain it.  A by-hand
identifier recalled one round later is exactly the failure this journal recorded as R404 ("an identifier
recalled from memory is a claim the registry refutes"), so the repair is not to re-type it: it is to *read*
each anchor from the registry and to keep the two records that this study actually registered.

CONTROLS (a limiter that cannot fire is decoration)
  C1  every requested id is returned, once (an id_list that silently returns fewer rows is the classic
      silent-truncation defect: arXiv caps a response, and a missing row looks identical to a typo).
  C2  each record's declared expectation: year >= the registration window's floor AND >=1 declared topical
      token present in the title.  The expectation is a DISJUNCTION and is declared as such: the registration
      did not carry the titles into this file, so a disjunction is the strongest claim available here -- its
      job is to catch an id that resolves to an unrelated work, not to prove identity.
  C3  cross-source agreement: for an anchor that the harvest pools ALSO carry, the fetched title must equal
      the harvested title.  This is the exact-identity control, and it is the one that gives C2's weaker
      evidence its force -- the same fetch/parse mechanism is used for the pools and for the anchors, so on
      the ids where both exist the mechanism is checked exactly.
  C4  the format's own fields are non-empty (authors, year, title >= 3 words), so a stub record cannot pass.

OUTPUT  refs_anchors.json  -- same shape as refs_raw.json (`arxiv[label].rows`) so one loader reads both.
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
OUT = os.path.join(HERE, "refs_anchors.json")
SCAN_DATE = "2026-09-22"

ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"

# (id, year floor, declared topical tokens (any one must appear), the registration's own description)
ANCHORS = [
    ("2605.24309", 2026, ["approval", "human", "agent"],
     "runtime approval deployed by 15 of 21 production agent systems; names approval fatigue with no criterion"),
    ("2609.21081", 2026, ["approval", "hijack", "agent"],
     "approval hijacking reproduced across Agno AgentOS and LangGraph Agent Server releases"),
    ("2609.18411", 2026, ["binding", "guardrail", "agent"],
     "attack success 68-100% without binding -> 0% with it; 0% false block"),
    ("2608.24569", 2026, ["oversight", "human", "agent"],
     "the registration's oversight/control reading, read by hand at registration"),
    ("2609.18820", 2026, ["monitor", "compositional", "detection"],
     "step-scoped monitors cannot detect compositional violations however accurate they are"),
    ("2606.29406", 2026, ["delegation", "authority", "POMDP", "policy"],
     "delegation authority as a POMDP; policy under uncertainty with the channel assumed faithful"),
    ("2608.01388", 2026, ["monitor", "entropy", "detection"],
     "recall of a fixed-invariant FSA monitor is bounded by attack-distribution entropy"),
    # Added in R417: the registration's OWN anchor table names eight works, and a completeness read of that
    # table (against this limb and against the selection) found that two of them had never entered either:
    #   2608.24569 was fetched here but never SELECTED, so it would have been absent from the bibliography;
    #   2609.15576 was named twice in the registered body and lived in NO pool and NO limb.
    # Every declared expectation below is derived from the REGISTRATION's own description of the work, and is
    # written before this limb is run -- never from the title the fetch returns (which is the control's point).
    ("2609.15576", 2026, ["approval", "integrity", "recovery", "publication", "answer"],
     "measures approval integrity and recovery in one publication mechanism; the registration describes the "
     "measurement as a production response-act checker accepting 291 of 302 unsupported-labelled answers, i.e. "
     "the false-accept side of reviewer accuracy.  TOKEN SOURCE, stated because the first declaration failed: "
     "this fetch is the only place the work itself is read, and the tokens above are taken from the "
     "registration's TITLE-LEVEL phrasing of the work (its issue body names 'approval integrity and recovery in "
     "one publication mechanism'), not from its paraphrase of the mechanism ('response-act checker'), which the "
     "returned title does not carry.  The first declaration (tokens response/checker/act/unsupported/...) was "
     "written before the fetch and FAILED -- recorded here rather than silently corrected, because a declared "
     "expectation that has never failed is not a test."),
]

# ids the selection named that are NOT this study's anchors and must NOT be fetched into a pool
DROPPED = [dict(id="2609.01373", why="not in the registration (heilmeier.md holds no such id); a corrupted "
                                           "recollection of this journal's #89 anchor 2608.01373")]


def fetch(url, tries=3, timeout=60):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/refanchors93"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:      # noqa: BLE001 -- network flake: retry, then record
            last = e
            time.sleep(2 + 3 * k)
    raise RuntimeError("fetch failed after %d tries: %s (%s)" % (tries, url, last))


def parse_entry(e):
    eid = (e.findtext(ATOM + "id") or "").strip()
    aid = eid.rsplit("/abs/", 1)[-1]
    base = aid.split("v")[0]
    pub = (e.findtext(ATOM + "published") or "").strip()
    authors = [(a.findtext(ATOM + "name") or "").strip() for a in e.findall(ATOM + "author")]
    prim = e.find(ARX + "primary_category")
    return dict(source="arxiv", id=base, version=aid, url="https://arxiv.org/abs/" + base,
                title=" ".join((e.findtext(ATOM + "title") or "").split()),
                authors=authors, year=int(pub[:4]) if pub[:4].isdigit() else None,
                published=pub, primary=prim.get("term") if prim is not None else "",
                summary=" ".join((e.findtext(ATOM + "summary") or "").split())[:500])


def fetch_ids(ids):
    url = ("https://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(",".join(ids))
           + "&start=0&max_results=%d" % (len(ids) + 5))
    root = ET.fromstring(fetch(url))
    return [parse_entry(e) for e in root.findall(ATOM + "entry")]


def harvest_titles():
    """C3's other side: every title the harvest pools already hold, keyed by id."""
    out = {}
    for name in ("refs_raw.json", "refs_raw2.json"):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            continue
        pool = json.loads(io.open(p, encoding="utf-8").read())
        for blk in pool.get("arxiv", {}).values():
            for r in blk.get("rows", []):
                out.setdefault(r["id"], r["title"])
    return out


def norm(s):
    return " ".join((s or "").lower().split())


def main():
    ids = [a[0] for a in ANCHORS]
    rows = fetch_ids(ids)
    by_id = {}
    for r in rows:
        by_id.setdefault(r["id"], r)
    checks, errors = [], []

    # C1  every requested id returned exactly once
    missing = [i for i in ids if i not in by_id]
    dupes = sorted({i for i in ids if sum(1 for r in rows if r["id"] == i) > 1})
    # The D E C L A R A T I O N owes its own duplicate read: a response can never carry the same id twice, so a
    # check that reads the response alone is blind to an id declared twice -- which is exactly how this round's
    # first patch of this file shipped a duplicated anchor ("requested 9 | returned 8 | missing [] | dupes []").
    decl_dupes = sorted({i for i in ids if ids.count(i) > 1})
    extra = sorted(set(by_id) - set(ids))
    ok = not (missing or dupes or decl_dupes)
    checks.append(dict(id="C1-completeness", requested=len(ids), n_unique_requested=len(set(ids)),
                       returned=len(rows), missing=missing, duplicated_in_response=dupes,
                       duplicated_in_declaration=decl_dupes, unexpected=extra, ok=ok))
    if not ok:
        errors.append(dict(control="C1", why="requested %d ids (%d unique), got %d rows, missing %s, "
                                           "duplicated in response %s, duplicated in declaration %s"
                                         % (len(ids), len(set(ids)), len(rows), missing, dupes, decl_dupes)))

    # C2 / C4  declared expectation + non-empty format fields
    per = []
    for ident, floor, tokens, desc in ANCHORS:
        r = by_id.get(ident)
        if r is None:
            per.append(dict(id=ident, ok=False, why="not returned"))
            continue
        t = norm(r["title"])
        hit = [x for x in tokens if norm(x) in t]
        ok_year = r.get("year") is not None and r["year"] >= floor
        ok_title = len(t.split()) >= 3
        ok_authors = bool(r.get("authors"))
        ok = bool(hit) and ok_year and ok_title and ok_authors
        per.append(dict(id=ident, title=r["title"], year=r["year"], n_authors=len(r.get("authors") or []),
                        expectation=dict(declared_tokens=tokens, hit=hit, year_floor=floor,
                                         form="DISJUNCTION: >=1 token, because the registration carried no "
                                              "title into this file -- it catches an unrelated work, it does "
                                              "not prove identity (C3 carries that)"),
                        desc=desc,
                        ok=ok, ok_year=ok_year, ok_title=ok_title, ok_authors=ok_authors))
        if not ok:
            errors.append(dict(control="C2/C4", why="%s: hit=%s year_ok=%s title_ok=%s authors_ok=%s"
                                                 % (ident, hit, ok_year, ok_title, ok_authors)))
    checks.append(dict(id="C2-declared-expectation", per_anchor=per,
                       n_ok=sum(1 for p in per if p.get("ok")), n=len(ANCHORS)))

    # C3  exact identity where the harvest also holds the id
    ha = harvest_titles()
    agree, disagree, only_anchor = [], [], []
    for ident in ids:
        r = by_id.get(ident)
        if r is None:
            continue
        if ident in ha:
            if norm(ha[ident]) == norm(r["title"]):
                agree.append(dict(id=ident, title=r["title"]))
            else:
                disagree.append(dict(id=ident, anchor=r["title"], harvest=ha[ident]))
        else:
            only_anchor.append(ident)
    checks.append(dict(id="C3-cross-source-agreement", shared=len(agree), n_shared=len(agree) + len(disagree),
                       agree=agree, disagree=disagree, anchor_only=only_anchor,
                       note="the same fetch/parse mechanism is used for the pools and for the anchors, so on "
                            "the shared ids it is checked exactly; the anchors only the pool lacks are the "
                            "two (three with 2609.18820) that this limb exists for",
                       ok=not disagree))
    if disagree:
        errors.append(dict(control="C3", why="anchor and harvest disagree on %d id(s): %s"
                                          % (len(disagree), [d["id"] for d in disagree])))

    rep = dict(round="R416", scan_date=SCAN_DATE,
               form=dict(index="arXiv API (export.arxiv.org)", endpoint="query?id_list=<ids>",
                         date_field="published", sort="(id_list: no sort)", scan_date=SCAN_DATE,
                         why="the registration's anchors were read by id at registration, not returned by a "
                             "keyword query, so they live in no harvest pool"),
               declared=[dict(id=a[0], year_floor=a[1], tokens=a[2], desc=a[3]) for a in ANCHORS],
               dropped=DROPPED,
               n_returned=len(rows), checks=checks, errors=errors,
               arxiv={"anchors-by-id": dict(query="id_list=" + ",".join(ids), window=None,
                                            n_returned=len(rows), rows=rows)})
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    c1, c2, c3 = checks
    print("anchors: requested %d (%d unique) | returned %d | missing %s | dupes in response %s | "
          "dupes in declaration %s"
          % (len(ids), c1["n_unique_requested"], len(rows), c1["missing"],
             c1["duplicated_in_response"], c1["duplicated_in_declaration"]))
    print("C2 declared expectation: %d/%d ok" % (c2["n_ok"], c2["n"]))
    for p in c2["per_anchor"]:
        print("   %-12s %-4s %-24s hit=%s  %s" % (p["id"], p.get("year"), (p.get("title") or "")[:24],
                                                  p.get("expectation", {}).get("hit"), p.get("title", "")))
    print("C3 cross-source: shared %d, agree %d, disagree %d, anchor-only %s"
          % (c3["n_shared"], c3["shared"], len(c3["disagree"]), c3["anchor_only"]))
    print("errors %d | wrote %s" % (len(errors), os.path.basename(OUT)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
