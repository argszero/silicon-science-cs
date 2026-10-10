#!/usr/bin/env python3
"""#93 R482 -- the BY-ID RE-READ limb: ids read from the registry again, because the committed sources are stale.

Why this limb exists (measured this round, two separate findings).

  A. A WORK THAT APPEARED AFTER THE REGISTRATION.  This study registered 2026-09-21 and its bibliography was
     built from the harvest pools plus the registration's own anchors.  On 2026-09-30 -- the day before the
     manuscript was submitted -- `2609.38983` appeared, systematizing the exact substitution this study prices
     and naming the same channel.  It is in no harvest pool (the harvests closed before it existed) and it is not
     an anchor of the registration, so neither existing limb can carry it without being mislabelled.
  B. A POOL ROW WHOSE TITLE WENT STALE.  `refs_build_v93.py` says of `pool_title`: "the title the difference
     line was written against, so a later read can check the live record still bears it".  This round ran that
     check -- `refs/reference_check.py --query` -- and it fired: arXiv `2609.08472` carried
     "Beyond Agent Harnesses: Cross-Substrate Authority for Multi-Agent Systems" in the harvest and reads
     "From Evidence to Effect: Authority Semantics and Runtime Infrastructure for Stateful Agents" live (v3).
     The entry was therefore citing a title the link no longer shows.  A re-read is the repair; guessing the
     new title by hand is the failure this journal recorded as R404 (a field recalled is a claim the registry
     refutes).

The distinction the labels carry matters for the record: an ANCHOR is a work the registration rested on, and
`refs_anchors.json`'s `declared` list is what C6/C15 of `refs_check2.py` read.  Neither set below adds anything
to that list, so a work that appeared after the registration cannot enter the registration's evidence base.

CONTROLS (a limiter that cannot fire is decoration)
  C1  every requested id is returned exactly once.  An id_list that silently returns fewer rows is the classic
      silent-truncation defect: a missing row looks identical to a typo (measured in this journal's search
      instrument, where an unencoded query returned an empty body printed as "returned 0" -- and measured again
      in this round's first probe, where an http:// request followed no redirect to https:// and returned a
      0-byte body that a parser reported as `entries: 0`).
  C2  the declared expectation: year >= the floor AND >=1 declared topical token present in the title.  Written
      BEFORE the fetch, from the abstract (A) or the live record's own fields (B) -- never from the title the
      fetch returns, which is the control's point.  It is a DISJUNCTION and declared as such: it catches an id
      that resolves to an unrelated work, it does not prove identity.
  C4  the format's own fields are non-empty (authors, year, title >= 3 words), so a stub record cannot pass.
  C5  (refreshed ids only) the re-read's title DIFFERS from the pool title it replaces -- a "refresh" that
      changed nothing is not a refresh, and its presence here would misreport the pools as stale.

OUTPUT  refs_reread.json  -- same shape as refs_raw.json (`arxiv[label].rows`), so one loader reads all.
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
OUT = os.path.join(HERE, "refs_reread.json")
SCAN_DATE = "2026-10-01"

ATOM = "{http://www.w3.org/2005/Atom}"
ARX = "{http://arxiv.org/schemas/atom}"

# A: (id, year floor, declared topical tokens (any one must appear), what the round read before fetching)
CONCURRENT = [
    ("2609.38983", 2026, ["laundering", "binding", "harness"],
     "six failure classes by which a harness substitutes the executed action for the approved one, a measured "
     "bound-gap rate per class in one harness, and a keyed-token defence; published 2026-09-30, after this "
     "study's registration (2026-09-21) and the day before its submission"),
]

# B: (id, year floor, declared topical tokens, why the pool row is being re-read)
REFRESHED = [
    ("2609.08472", 2026, ["evidence", "authority", "agents"],
     "the pool's title no longer matches the live record: the entry cited the harvest's reading of v1 while the "
     "link now serves a retitled v3, so the bibliography is re-pointed at the title the record carries"),
]

LABEL = "concurrent-by-id"
REFRESHED_LABEL = "refreshed-by-id"


def fetch(url, tries=3, timeout=60):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/refreread93"})
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


def pool_titles():
    """What the committed pools say about each id -- the reading a refresh replaces."""
    out = {}
    for name in ("refs_raw.json", "refs_raw2.json", "refs_anchors.json"):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            continue
        for blk in json.loads(io.open(p, encoding="utf-8").read()).get("arxiv", {}).values():
            for r in blk.get("rows", []):
                out.setdefault(r["id"], (name, r.get("title", "")))
    return out


def norm(s):
    return " ".join((s or "").lower().split())


def check_set(name, declared, by_id, errors, prev=None):
    """C1/C2/C4 (+C5 for a refresh) over one declared set; returns the check dict."""
    ids = [a[0] for a in declared]
    missing = [i for i in ids if i not in by_id]
    dupes = sorted({i for i in ids if sum(1 for r in by_id.values() if r["id"] == i) > 1})
    decl_dupes = sorted({i for i in ids if ids.count(i) > 1})
    ok = not (missing or dupes or decl_dupes)
    if not ok:
        errors.append(dict(control="C1", set=name,
                           why="requested %d ids, missing %s, dupes %s/%s" % (len(ids), missing, dupes, decl_dupes)))
    per = []
    for ident, floor, tokens, desc in declared:
        r = by_id.get(ident)
        if r is None:
            per.append(dict(id=ident, ok=False, why="not returned"))
            continue
        t = norm(r["title"])
        hit = [x for x in tokens if norm(x) in t]
        ok_year = r.get("year") is not None and r["year"] >= floor
        ok_title = len(t.split()) >= 3
        ok_authors = bool(r.get("authors"))
        good = bool(hit) and ok_year and ok_title and ok_authors
        entry = dict(id=ident, title=r["title"], version=r.get("version"), year=r["year"],
                     n_authors=len(r.get("authors") or []),
                     expectation=dict(declared_tokens=tokens, hit=hit, year_floor=floor,
                                      form="DISJUNCTION: >=1 token, declared before the fetch from the abstract "
                                           "(new work) or the live record's own fields (refresh) -- it catches "
                                           "an unrelated work, it does not prove identity"),
                     desc=desc, ok=good, ok_year=ok_year, ok_title=ok_title, ok_authors=ok_authors)
        if prev is not None:
            pool, old = prev.get(ident, ("", ""))
            entry["replaces"] = dict(pool=pool, title=old)
            changed = norm(old) != t
            entry["changed"] = changed
            entry["ok_changed"] = changed
            good = good and changed
            entry["ok"] = good
            if not changed:
                errors.append(dict(control="C5", set=name,
                                   why="%s: the re-read returned the pool's own title; nothing was refreshed" % ident))
        per.append(entry)
        if not good:
            errors.append(dict(control="C2/C4", set=name,
                               why="%s: hit=%s year_ok=%s title_ok=%s authors_ok=%s"
                                   % (ident, hit, ok_year, ok_title, ok_authors)))
    return dict(id="C1-completeness+%s" % name, requested=len(ids), returned=len(ids) - len(missing),
                missing=missing, duplicated_in_response=dupes, duplicated_in_declaration=decl_dupes, ok=ok,
                per_entry=per, n_ok=sum(1 for p in per if p.get("ok")), n=len(declared))


def main():
    declared = CONCURRENT + REFRESHED
    ids = [a[0] for a in declared]
    rows = fetch_ids(ids)
    by_id = {}
    for r in rows:
        by_id.setdefault(r["id"], r)
    errors = []
    prev = pool_titles()
    c1 = check_set("concurrent", CONCURRENT, by_id, errors)
    c2 = check_set("refreshed", REFRESHED, by_id, errors, prev=prev)

    def block(label, lst, check):
        return {label: dict(query="id_list=" + ",".join(a[0] for a in lst), window=None,
                            n_returned=len(ids) - len(check["missing"]),
                            rows=[by_id[a[0]] for a in lst if a[0] in by_id])}

    rep = dict(round="R482", scan_date=SCAN_DATE,
               form=dict(index="arXiv API (export.arxiv.org)", endpoint="query?id_list=<ids>",
                         date_field="published", sort="(id_list: no sort)", scan_date=SCAN_DATE,
                         why="(A) a work discovered after the submission was opened (published 2026-09-30), in "
                             "no harvest pool and not one of the registration's anchors; (B) an id whose pool "
                             "title no longer matches the live record"),
               declared=[dict(id=a[0], year_floor=a[1], tokens=a[2], desc=a[3]) for a in CONCURRENT],
               declared_refreshed=[dict(id=a[0], year_floor=a[1], tokens=a[2], desc=a[3]) for a in REFRESHED],
               n_returned=len(rows), checks=[c1, c2], errors=errors,
               arxiv=dict(**block(LABEL, CONCURRENT, c1), **block(REFRESHED_LABEL, REFRESHED, c2)))
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    for check in (c1, c2):
        print("%-11s requested %d | returned %d | missing %s | dupes %s/%s | expectation %d/%d ok"
              % (check["id"].split("+")[1], check["requested"], check["returned"], check["missing"],
                 check["duplicated_in_response"], check["duplicated_in_declaration"], check["n_ok"], check["n"]))
        for p in check["per_entry"]:
            extra = ""
            if "replaces" in p:
                extra = " | replaced %r -> %r" % (p["replaces"]["title"][:40], p["title"][:40])
            print("   %-12s %-4s hit=%s%s" % (p["id"], p.get("year"),
                                              p.get("expectation", {}).get("hit"), extra))
    print("errors %d | wrote %s" % (len(errors), os.path.basename(OUT)))
    for e in errors:
        print("  ERR %s %s: %s" % (e["control"], e.get("set", ""), e["why"]))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
