#!/usr/bin/env python3
"""Verify the reference POOL of issue #130 against live external records.

This is the journal's citation-authenticity obligation (submission bar item 12).  It is done here
rather than asserted from memory, and it verifies the whole committed pool, not just what the
manuscript currently cites: `make_reference_check.py` later intersects the two and REFUSES to write
a report when a cited key carries no verdict, so verifying the pool once is what makes that refusal
meaningful rather than vacuous.

Three things it refuses to do, each because it was once the bug:

  * trust a resolver that merely answers -- a remembered identifier resolves to a *different* real
    paper, so the test is the returned TITLE against the stored title, not the HTTP status;
  * compare titles by dividing the overlap by ONE of them -- a short generic title then scores 1.00
    against a long specific one, so the score is the smaller of the two coverage fractions;
  * report a transport failure as a finding -- an outage is not evidence about the record, so a
    failure gets its own verdict (TRANSPORT-UNKNOWN) and makes the run fail as UNKNOWN.

It also reads the WHOLE record: Crossref splits a two-part title across `title` and `subtitle`, and
a reader that takes `title` alone reports a correct record as a mismatch (measured live on
`10.1145/872757.872770`, stored as "Winnowing" + "local algorithms for document fingerprinting").

Carriers: the arXiv `id_list` API (batched, `max_results` set to the chunk's own size so a silent
10-entry cap cannot masquerade as absent records), with the arXiv abstract page (`citation_title`
meta tag) as the per-id fallback; and Crossref `works/<doi>`.

Run:  python3 verify_citations.py            (verify the pool, write citation-verification.json)
      python3 verify_citations.py --selftest (plant both failure modes, require them to fire)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "refs", "pool.json")
OUT = os.path.join(HERE, "citation-verification.json")
THRESHOLD = 0.80
SLEEP = 1.0
ATOM = "{http://www.w3.org/2005/Atom}"

STOP = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "via", "using"}


def tokens(s):
    return {t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if t not in STOP and len(t) > 1}


def title_matches(a, b, min_frac=THRESHOLD):
    """TWO-SIDED: the smaller of the two overlap fractions.  Dividing by the shorter title lets a
    short generic record score 1.00 against a long specific citation."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return min(inter / len(ta), inter / len(tb))


def fetch(url, timeout=40, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs citation check"})
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(2.5 * (i + 1))
    raise last


def unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'"))


def cr_full_title(m):
    t = (m.get("title") or [""])[0]
    sub = (m.get("subtitle") or [""])
    sub = sub[0] if sub else ""
    return ("%s: %s" % (t, sub)) if sub and sub.lower() not in t.lower() else t


def arxiv_batch(ids, chunk=50):
    """({id: title}, n_failed_batches).  `max_results` is the chunk's own size: the API caps an
    `id_list` request at 10 otherwise, and the shortfall is then indistinguishable from records that
    do not exist."""
    out, failed = {}, 0
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        url = ("https://export.arxiv.org/api/query?id_list=" + ",".join(part)
               + "&max_results=%d" % len(part))
        try:
            root = ET.fromstring(fetch(url))
        except Exception as e:
            print("    [batch %d] TRANSPORT: %s" % (i, e), flush=True)
            failed += 1
            continue
        got = root.findall(ATOM + "entry")
        if len(got) < len(part):
            print("    [batch %d] WARNING: %d ids, %d entries" % (i, len(part), len(got)), flush=True)
        for e in got:
            aid = e.findtext(ATOM + "id", "").rsplit("/", 1)[-1]
            out[aid.split("v")[0]] = re.sub(r"\s+", " ", e.findtext(ATOM + "title", "")).strip()
        time.sleep(3.0)
    return out, failed


def arxiv_page_title(key):
    html = fetch("https://arxiv.org/abs/%s" % key)
    m = re.search(r'<meta name="citation_title" content="([^"]*)"', html)
    if not m:
        raise IOError("the abstract page carries no citation_title")
    return unescape(m.group(1).strip())


def main():
    pool = json.load(open(POOL))
    keys = sorted(pool)
    arxiv_keys = [k for k in keys if pool[k]["source"] == "arxiv"]
    print("verifying %d pool entries (%d arXiv, %d Crossref) ..."
          % (len(keys), len(arxiv_keys), len(keys) - len(arxiv_keys)), flush=True)
    live, failed_batches = arxiv_batch(arxiv_keys)
    rows = []
    for i, k in enumerate(keys):
        v = pool[k]
        rec = {"key": k, "source": v["source"], "stored_title": v["title"]}
        try:
            if v["source"] == "crossref":
                m = json.loads(fetch("https://api.crossref.org/works/%s"
                                     % urllib.parse.quote(k, safe="")))["message"]
                live_title = cr_full_title(m)
                rec["method"] = "Crossref works/<doi> (title+subtitle compare)"
            else:
                if k in live:
                    live_title = live[k]
                    rec["method"] = "arXiv id_list (batched, title compare)"
                else:
                    live_title = arxiv_page_title(k)     # per-id fallback carrier
                    rec["method"] = "arXiv abstract page, citation_title (title compare)"
            sc = title_matches(v["title"], live_title)
            rec["live_title"] = live_title
            rec["title_match"] = round(sc, 3)
            rec["verdict"] = "VERIFIED" if sc >= THRESHOLD else "MISMATCH"
        except Exception as e:
            rec["verdict"] = "TRANSPORT-UNKNOWN"
            rec["error"] = str(e)[:120]
        rows.append(rec)
        if v["source"] == "crossref":
            time.sleep(SLEEP)
    _write(rows)
    n = {"VERIFIED": 0, "MISMATCH": 0, "TRANSPORT-UNKNOWN": 0}
    for r in rows:
        n[r["verdict"]] += 1
    print("VERIFIED %d / %d ; TITLE MISMATCH %d ; TRANSPORT-UNKNOWN %d (batches failed: %d)"
          % (n["VERIFIED"], len(rows), n["MISMATCH"], n["TRANSPORT-UNKNOWN"], failed_batches))
    print("wrote %s" % os.path.relpath(OUT, HERE))
    if n["MISMATCH"] or n["TRANSPORT-UNKNOWN"]:
        print("REFUSING to pass: a mismatch must be repaired and a transport failure is UNKNOWN, "
              "not a finding")
        return 1
    worst = min(r["title_match"] for r in rows)
    print("worst live title match: %.3f (threshold %.2f)" % (worst, THRESHOLD))
    return 0


def _write(rows):
    tmp = OUT + ".stage"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, OUT)


def selftest():
    ok = True

    def fires(name, fn):
        nonlocal ok
        try:
            fn()
        except AssertionError:
            print("[%-28s] FIRED" % name)
            return
        print("[%-28s] *** DID NOT FIRE ***" % name)
        ok = False

    def holds(name, fn):
        nonlocal ok
        try:
            fn()
            print("[%-28s] holds" % name)
        except AssertionError as e:
            print("[%-28s] *** FIRED ON A HEALTHY CASE *** %s" % (name, str(e)[:36]))
            ok = False

    def n(a, b):
        s = title_matches(a, b)
        if s < THRESHOLD:
            raise AssertionError("score %.3f" % s)

    fires("reject-different-paper",
          lambda: n("Detecting Near-Duplicates for Web Crawling",
                    "Near-Optimal Hashing Algorithms for Approximate Nearest Neighbor"))
    fires("reject-generic-short",
          lambda: n("Machine Learning Benchmarks",
                    "Accounting for Variance in Machine Learning Benchmarks"))
    holds("accept-identical",
          lambda: n("Power-Law Distributions in Empirical Data",
                    "Power-Law Distributions in Empirical Data"))
    holds("accept-split-subtitle",
          lambda: n("Winnowing: Local Algorithms for Document Fingerprinting",
                    "Winnowing: local algorithms for document fingerprinting"))
    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


def pages_spotcheck(n=15, offset=0):
    """Verify a SAMPLE through a SECOND carrier -- the arXiv abstract page -- and report agreement.

    Why this exists: the main pass compares the title recorded at harvest time against the title the
    arXiv API returns for the same id.  Both come from the same backend field, so a perfect score is
    expected rather than informative -- the main pass is a REGRESSION check on the harvest (it would
    catch an id/title mismatch introduced by our own parsing, or a withdrawn/renamed record), not
    independent evidence that the id names the work we think it does.  A different carrier is the
    closest thing to that independent reading available without a second database, so it is measured
    and reported as a SPOT CHECK (a rate over a sample), never as the full pass.
    """
    pool = json.load(open(POOL))
    keys = sorted(k for k, v in pool.items() if v["source"] == "arxiv")[offset:offset + n]
    ok = mismatch = transport = 0
    for k in keys:
        try:
            live = arxiv_page_title(k)               # a DIFFERENT endpoint and field from id_list
        except Exception as e:
            print("  [%s] TRANSPORT: %s" % (k, e), flush=True)
            transport += 1
            time.sleep(2)
            continue
        good = title_matches(pool[k]["title"], live) >= THRESHOLD
        ok += 1 if good else 0
        mismatch += 0 if good else 1
        if not good:
            print("  MISMATCH %s\n     stored: %s\n     page  : %s"
                  % (k, pool[k]["title"][:62], live[:62]), flush=True)
        time.sleep(2.0)
    print("abstract-page SPOT CHECK (second carrier): agree %d / %d ; MISMATCH %d ; TRANSPORT %d"
          % (ok, len(keys), mismatch, transport))
    print("(a sample, not the full pass -- the API pass is the full pass)")
    return 0 if (mismatch == 0 and transport == 0) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--pages" in sys.argv:
        i = sys.argv.index("--pages")
        n = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 15
        off = int(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 0
        sys.exit(pages_spotcheck(n, off))
    sys.exit(main())
