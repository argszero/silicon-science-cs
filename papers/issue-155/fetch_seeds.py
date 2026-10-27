#!/usr/bin/env python3
"""Issue #155 -- declared seed records, fetched by DOI from Crossref.

WHY THIS FILE EXISTS. The query-driven harvest (build_refs.py) cannot surface
three kinds of record this paper cannot do without:

  * the prior-art trio (Even-Itai 1971, Tarjan 1972, Pratt 1973) -- the works whose
    machinery `runs(p) = 1 + #{descents}` already belongs to. They are cited in the
    prior-art paragraph, so they must be verifiable records, not memories of records.
  * PIFO itself (Sivaraman et al. 2016) -- the query harvest searched construct
    names ("push-in first-out", "PIFO") and returned only works that *approximate*
    a PIFO. The originating paper does not use the phrase in its title.

A seed is therefore a DECLARED addition, not a silent one: each entry carries the
reason the harvest missed it, and each is verified against Crossref exactly like
every harvested candidate. `place_refs.py` reads this file and refuses a seed whose
DOI does not resolve -- an unverifiable seed never reaches the bibliography.

Run:  /usr/bin/python3 fetch_seeds.py        (writes seeds.json, offline after that)
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "seeds.json")
UA = "silicon-science-cs/1.0 (mailto:how2how2how2-arch@users.noreply.github.com)"

# key -> (doi, why the query harvest missed it)
SEEDS = [
    ("evenitai1971", "10.1016/b978-0-12-417750-5.50011-7",
     "prior-art trio; construct queries returned queueing theory, not this"),
    ("tarjan1972", "10.1145/321694.321704",
     "prior-art trio; the query 'networks of queues and stacks' surfaced the 2008 complexity paper, not the 1972 origin"),
    ("pratt1973", "10.1145/800125.804058",
     "prior-art trio; STOC-era record, no construct token in the indexed title"),
    ("pifo2016", "10.1145/2934872.2934899",
     "the originating PIFO paper; every query built on the phrase 'PIFO' returned only later approximations"),
]


def fetch(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as fh:
        return json.load(fh)["message"]


def year_of(m):
    for field in ("published-print", "published-online", "issued", "created"):
        parts = m.get(field, {}).get("date-parts", [[None]])[0]
        if parts and parts[0]:
            return int(parts[0])
    return None


def authors_of(m):
    out = []
    for a in m.get("author", []) or []:
        name = " ".join(x for x in (a.get("given"), a.get("family")) if x)
        if name:
            out.append(name)
    return out


def venue_of(m):
    for field in ("container-title", "event", "publisher"):
        v = m.get(field)
        if isinstance(v, list) and v:
            return v[0]
        if isinstance(v, str) and v:
            return v
    return ""


def main():
    import urllib.parse  # noqa: F401  (used by fetch via module attr above)
    records, failed = [], []
    for key, doi, why in SEEDS:
        try:
            m = fetch(doi)
        except Exception as exc:  # noqa: BLE001 -- any failure is a failed seed, recorded
            failed.append("%-14s %s -> %s: %s" % (key, doi, type(exc).__name__, exc))
            continue
        records.append({
            "key": key,
            "doi": doi.lower(),
            "title": (m.get("title") or [""])[0].strip(),
            "authors": authors_of(m),
            "venue": venue_of(m),
            "year": year_of(m),
            "type": m.get("type", ""),
            "seed_reason": why,
        })
        print("ok  %-14s %s | %s (%s)" % (key, m.get("type", ""), (m.get("title") or [""])[0][:70], year_of(m)))
        time.sleep(1)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"seeds": records, "failed": failed}, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("\nseeded %d / %d" % (len(records), len(SEEDS)))
    if failed:
        print("FAILED:")
        for f in failed:
            print("   " + f)
        return 1
    return 0


if __name__ == "__main__":
    import urllib.parse
    sys.exit(main())
