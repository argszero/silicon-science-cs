#!/usr/bin/env python3
"""harvest_authors.py -- recover the FULL author list for every pooled DOI, from Crossref.

Why this exists (revision round 1, issue #145, required change R1). The corpus stores one author per
entry -- the registry field it kept -- so the published reference list printed `Ladisa (2023)` for a
four-author work. The editor's receipt was that the pool's own author-length distribution is
`{0: 3, 1: 127}` while Crossref names 4, 3, 3, 4, 6 and 6 authors for sampled entries, and that the
sentence disclosing the truncation lived in `reference-check.md` and nowhere in the manuscript, so the
only reader who met the truncated list was the only reader never told it was truncated.

This script fixes the list rather than the disclosure: it re-queries Crossref by DOI for every entry
that has one, and records the author list in the house form (`Family, I.`), one per author.

The result is CACHED in `authors_by_doi.json` and committed, because a reproduction path must not
depend on the network: `export_pool.py` reads the cache, so `reproduce.sh` regenerates the pool
offline and byte-identically. Re-running this script is how the cache is refreshed.

A 429 is never retried (the registry is telling us to stop, and a retry loop turns a quiet limit into
a hammering one); it is recorded as an unresolved DOI and printed, so a short cache is visible rather
than silent.

Usage:
  python3 harvest_authors.py            # refresh the cache from Crossref
  python3 harvest_authors.py --check    # report coverage of the cache, no network
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "refs_pool.json")
CACHE = os.path.join(HERE, "authors_by_doi.json")
UA = "silicon-science-cs/1.0 (mailto:how2how2how2-arch@users.noreply.github.com)"
PAUSE = 0.6          # seconds between requests: polite pooling, not a scrape
TIMEOUT = 25


def initials(given):
    """`Kristen B.` -> `K. B.` -- the house form's initial component."""
    parts = [p for p in re.split(r"[\s.]+", given or "") if p]
    return " ".join(p[0].upper() + "." for p in parts if p[0].isalpha())


def house(author):
    """A Crossref author dict as the reference list prints it: `Family, I. I.`"""
    fam = (author.get("family") or "").strip()
    giv = initials(author.get("given") or "")
    if fam and giv:
        return "%s, %s" % (fam, giv)
    return fam or (author.get("name") or "").strip()


def fetch(doi):
    """Return (authors, status) for one DOI. status is 'ok', 'no-author' or an error word."""
    req = urllib.request.Request("https://api.crossref.org/works/" + doi, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as fh:
            msg = json.load(fh)["message"]
    except urllib.error.HTTPError as e:
        # 429 included: never retried, just reported
        return None, "http-%d" % e.code
    except Exception as e:                                  # noqa: BLE001 -- reported, not raised
        return None, type(e).__name__.lower()
    got = [house(a) for a in (msg.get("author") or [])]
    got = [g for g in got if g]
    if not got:
        return [], "no-author"
    return got, "ok"


def load_pool_dois():
    with io.open(POOL, encoding="utf-8") as fh:
        pool = json.load(fh)
    out = []
    for e in pool["entries"]:
        if e.get("doi"):
            out.append((e["key"], e["doi"]))
    return out


def check():
    pairs = load_pool_dois()
    if not os.path.exists(CACHE):
        print("AUTHORS: NOT RUN -- no cache at %s" % os.path.basename(CACHE))
        return 1
    with io.open(CACHE, encoding="utf-8") as fh:
        cache = json.load(fh)
    by = cache["by_doi"]
    full = [k for k, d in pairs if len((by.get(d) or {}).get("authors") or []) > 1]
    one = [k for k, d in pairs if len((by.get(d) or {}).get("authors") or []) == 1]
    none = [k for k, d in pairs if not (by.get(d) or {}).get("authors")]
    missing = [k for k, d in pairs if d not in by]
    print("AUTHORS: %d entries with a DOI -- %d carry more than one author, %d exactly one, "
          "%d none in the registry record, %d not in the cache"
          % (len(pairs), len(full), len(one), len(none), len(missing)))
    if missing:
        print("  not cached: %s" % ", ".join(missing[:8]))
    hist = {}
    for k, d in pairs:
        n = len((by.get(d) or {}).get("authors") or [])
        hist[n] = hist.get(n, 0) + 1
    print("  author-count distribution: %s" % dict(sorted(hist.items())))
    return 0 if not missing else 1


def main(argv):
    if "--check" in argv:
        return check()
    pairs = load_pool_dois()
    by = {}
    if os.path.exists(CACHE):
        with io.open(CACHE, encoding="utf-8") as fh:
            by = json.load(fh).get("by_doi", {})
    statuses = {}
    for i, (key, doi) in enumerate(pairs, 1):
        authors, status = fetch(doi)
        statuses[status] = statuses.get(status, 0) + 1
        if authors is not None:
            by[doi] = {"authors": authors, "status": status, "queried_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        print("[%3d/%3d] %-6s %-34s %s" % (i, len(pairs), status, doi, (authors or "")[:3]))
        sys.stdout.flush()
        time.sleep(PAUSE)
    out = {
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": "Crossref REST API, /works/<doi>, re-queried by DOI",
        "how_form": "Family, I. -- one string per author, in Crossref's order",
        "by_doi": by,
    }
    with io.open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("\nwrote %s -- %d DOI(s); statuses %s" % (os.path.basename(CACHE), len(by), statuses))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
