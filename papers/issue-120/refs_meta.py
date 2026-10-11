#!/usr/bin/env python3
"""Issue #120 -- reference METADATA (authors + year) for the curated set.

Discovery kept id/title/date/categories; a reference list needs AUTHORS.  This fetches them from the
index that owns each id -- arXiv (batched id_list, up to 50 ids per call) for arXiv ids, Crossref for
DOIs -- and writes refs/meta.json.  It re-reads the TITLE in the same pass and refuses to continue if
any title disagrees with the curated one, so metadata and verification cannot drift apart.

TRANSPORT (measured R516): the arXiv *API* endpoint is unreachable from this host -- a query hangs
until timeout and the socket is never answered (throttled after a heavy discovery burst), while the
*abstract page* answers 200 and carries the same fields as schema.org citation_* meta tags.  So this
script PROBES the API and falls back to abstract pages per id, which is the route the reference
layer was actually built on.  Whichever route fills a record, the title it read is compared with the
curated title, so the fallback cannot silently substitute a different paper.

CACHE: keys are sha256 of the request, NOT python's hash(), whose string seed is randomized per
process -- an unstable key makes a cache that never hits (three runs of the earlier version wrote
three different files for the same batch).

Usage:  /usr/bin/python3 refs_meta.py [--refresh]
Out:    refs/meta.json
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

NS = {"a": "http://www.w3.org/2005/Atom"}
CUR = "refs/curated.json"
OUT = "refs/meta.json"
CACHE = "refs/meta_cache"
BATCH = 50
MAILTO = "how2how2how2-arch@users.noreply.github.com"
UA = "silicon-science-cs/1.0 (mailto:%s)" % MAILTO


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    return " ".join(re.sub(r"[^0-9a-z]+", " ", s.lower()).split())


def key_of(*parts):
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:24]


def cache_path(kind, body):
    os.makedirs(CACHE, exist_ok=True)
    return os.path.join(CACHE, "%s_%s.json" % (kind, key_of(body)))


def cached(kind, body, fetch, refresh=False):
    p = cache_path(kind, body)
    if os.path.exists(p) and not refresh:
        return json.load(open(p))
    got = fetch()
    json.dump(got, open(p, "w"))
    return got


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ---------------------------------------------------------------- arXiv: API
def fetch_arxiv_batch(ids):
    raw = get("http://export.arxiv.org/api/query?id_list=%s&max_results=%d"
              % (",".join(ids), len(ids)), timeout=30)
    root = ET.fromstring(raw)
    got = {}
    for e in root.findall("a:entry", NS):
        aid = e.find("a:id", NS).text.replace("http://arxiv.org/abs/", "")
        bare = re.sub(r"v\d+$", "", aid)
        t = e.find("a:title", NS)
        authors = [" ".join(a.find("a:name", NS).text.split())
                   for a in e.findall("a:author", NS)]
        got[bare] = {"title": " ".join(t.text.split()) if t is not None else None,
                     "authors": authors, "year": e.find("a:published", NS).text[:4]}
    return got


def api_alive():
    try:
        get("https://export.arxiv.org/api/query?id_list=2206.02878&max_results=1", timeout=12)
        return True
    except Exception as e:
        print("  arXiv API probe failed (%s: %s) -- falling back to abstract pages"
              % (type(e).__name__, e))
        return False


# ------------------------------------------------------- arXiv: abstract page
def meta_tag(page, name):
    return re.findall(r'<meta\s+name="%s"\s+content="([^"]*)"' % name, page)


def fetch_arxiv_page(bare):
    page = get("https://arxiv.org/abs/" + urllib.parse.quote(bare))
    authors = []
    for a in meta_tag(page, "citation_author"):
        a = html.unescape(a).strip()
        authors.append(" ".join(a.split(", ")[::-1]) if ", " in a else a)
    titles = meta_tag(page, "citation_title")
    dates = meta_tag(page, "citation_date")
    return {"title": html.unescape(titles[0]).strip() if titles else None,
            "authors": authors,
            "year": dates[0][:4] if dates else None}


# ------------------------------------------------------------------ Crossref
def fetch_crossref(doi):
    j = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(doi), timeout=45))
    m = j.get("message", {})
    authors = []
    for a in m.get("author", []) or []:
        nm = (" ".join(x for x in [a.get("given"), a.get("family")] if x)).strip()
        if nm:
            authors.append(nm)
    return {"title": (m.get("title") or [None])[0], "authors": authors,
            "year": str((m.get("issued", {}).get("date-parts", [[None]]) or [[None]])[0][0])}


def main():
    refresh = "--refresh" in sys.argv
    entries = json.load(open(CUR))["entries"]
    arx = [e for e in entries if not e["id"].startswith("10.")]
    doi = [e for e in entries if e["id"].startswith("10.")]
    meta, bad = {}, []

    use_api = api_alive()
    route = "API batch" if use_api else "abstract pages"
    print("fetching metadata for %d arXiv ids via %s, %d DOIs via Crossref"
          % (len(arx), route, len(doi)))

    if use_api:
        for i in range(0, len(arx), BATCH):
            chunk = arx[i:i + BATCH]
            ids = [e["id"] for e in chunk]
            try:
                got = cached("batch", ",".join(ids), lambda: fetch_arxiv_batch(ids), refresh)
            except Exception as e:
                print("  ! batch failed: %s" % e, file=sys.stderr)
                got = {}
            for e in chunk:
                g = got.get(e["bare"])
                if g is None or g.get("title") is None:
                    bad.append(("MISSING", e["bare"]))
                    continue
                if norm(g["title"]) != norm(e["title"]):
                    bad.append(("TITLE", e["bare"]))
                    continue
                meta[e["bare"]] = {"authors": g["authors"], "year": g["year"], "title": g["title"]}
            print("   batch %d/%d: %d of %d resolved"
                  % (i // BATCH + 1, (len(arx) + BATCH - 1) // BATCH, len(got), len(chunk)))
            time.sleep(3)
    else:
        for n, e in enumerate(arx, 1):
            try:
                g = cached("abs", e["bare"], lambda e=e: fetch_arxiv_page(e["bare"]), refresh)
            except Exception as ex:
                bad.append(("FETCH", e["bare"]))
                print("  ! page failed %s: %s" % (e["bare"], ex), file=sys.stderr)
                continue
            if g.get("title") is None:
                bad.append(("MISSING", e["bare"]))
            elif norm(g["title"]) != norm(e["title"]):
                bad.append(("TITLE", e["bare"]))
            elif not g["authors"]:
                bad.append(("NOAUTHORS", e["bare"]))
            else:
                meta[e["bare"]] = {"authors": g["authors"], "year": g["year"], "title": g["title"]}
            if n % 20 == 0 or n == len(arx):
                print("   %d/%d pages read, %d ok, %d problems"
                      % (n, len(arx), len(meta), len(bad)))
            time.sleep(1.5)

    for e in doi:
        try:
            g = cached("doi", e["id"], lambda e=e: fetch_crossref(e["id"]), refresh)
        except Exception as ex:
            bad.append(("FETCH", e["bare"]))
            print("  ! DOI fetch failed %s: %s" % (e["id"], ex), file=sys.stderr)
            continue
        if g["title"] is None or norm(g["title"]) != norm(e["title"]):
            bad.append(("TITLE", e["bare"]))
        elif not g["authors"]:
            bad.append(("NOAUTHORS", e["bare"]))
        else:
            meta[e["bare"]] = {"authors": g["authors"], "year": g["year"], "title": g["title"]}
        time.sleep(1)

    with_authors = sum(1 for m in meta.values() if m["authors"])
    print("\n%d of %d entries carry author metadata; %d problems"
          % (with_authors, len(entries), len(bad)))
    for kind, b in bad:
        print("   %-9s %s" % (kind, b))
    json.dump({"n": len(meta), "with_authors": with_authors, "route": route,
               "problems": bad, "meta": meta}, open(OUT, "w"), indent=1, sort_keys=True)
    print("-> %s" % OUT)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
