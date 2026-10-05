#!/usr/bin/env python3
"""Verify every reference CITED in manuscript.md against a live external record.

This is the journal's citation-authenticity obligation (submission bar item 12), so it is done here
rather than asserted from memory.  Three things it refuses to do:

  * trust a resolver that merely answers -- a remembered identifier resolves to a *different* real
    paper, so the test is the returned TITLE against the stored title, not the HTTP status;
  * compare titles by dividing the overlap by ONE of them -- a short generic title then scores 1.00
    against a long specific one, so the score is the smaller of the two coverage fractions;
  * report a transport failure as a finding -- an outage is not evidence about the record, so a
    failure gets its own verdict (TRANSPORT-UNKNOWN) and makes the run fail as UNKNOWN.

Carriers: arXiv abstract pages (`citation_title` meta) and Crossref `works/<doi>`.  The arXiv
`id_list` API is throttled in this environment (HTTP 429) and the abstract page carries the same
field, so the page is used and the endpoint is recorded per entry.

Run:  python3 verify_citations.py            (verify the cited set, write citation-verification.json)
      python3 verify_citations.py --selftest (plant both failure modes, require them to fire)
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, "refs", "pool.json")
MAN = os.path.join(HERE, "manuscript.md")
OUT = os.path.join(HERE, "citation-verification.json")
THRESHOLD = 0.80
SLEEP = 1.2

STOP = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "via", "using"}


def tokens(s):
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in STOP and len(t) > 1}


def title_matches(a, b, min_frac=THRESHOLD):
    """TWO-SIDED: the smaller of the two overlap fractions.  Dividing by the shorter title lets a
    short generic record score 1.00 against a long specific citation."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return min(inter / len(ta), inter / len(tb))


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs citation check"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def live_title_arxiv(key):
    html = fetch("https://arxiv.org/abs/%s" % key)
    m = re.search(r'<meta name="citation_title" content="([^"]*)"', html)
    if not m:
        raise IOError("the abstract page carries no citation_title")
    return m.group(1).strip()


def unescape(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&#39;", "'"))


def live_title_crossref(doi):
    d = json.loads(fetch("https://api.crossref.org/works/%s" % urllib.parse.quote(doi)))
    return (d["message"].get("title") or [""])[0].strip()


def cited_keys():
    pool = json.load(open(POOL))
    refs = open(MAN).read().split("## References", 1)[1]
    keys = []
    for line in refs.splitlines():
        m = re.match(r"^(\d+)\.\s", line)
        if not m:
            continue
        a = re.search(r"arXiv:([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)", line)
        if a:
            keys.append(a.group(1).split("v")[0])
            continue
        d = re.search(r"\b(10\.[0-9]{4,9}/\S+?)(?=\s|$)", line)
        if d:
            keys.append(d.group(1).rstrip("."))
    out = []
    for k in keys:
        if k not in pool:
            raise SystemExit("cited key %s is not in the verified pool" % k)
        out.append(k)
    return out, pool


def verify(keys, pool, sleeper=time.sleep):
    rows = []
    for i, k in enumerate(keys):
        v = pool[k]
        stored = v["title"]
        rec = {"key": k, "source": v["source"], "stored_title": stored}
        try:
            if v["source"] == "crossref":
                live = unescape(live_title_crossref(k))
                rec["method"] = "Crossref works/<doi> (title compare)"
            else:
                live = unescape(live_title_arxiv(k))
                rec["method"] = "arXiv abstract page, citation_title (title compare)"
            sc = title_matches(stored, live)
            rec["live_title"] = live
            rec["title_match"] = round(sc, 3)
            rec["verdict"] = "VERIFIED" if sc >= THRESHOLD else "MISMATCH"
        except Exception as e:
            rec["verdict"] = "TRANSPORT-UNKNOWN"
            rec["error"] = str(e)[:120]
        rows.append(rec)
        if i + 1 < len(keys):
            sleeper(SLEEP)
    return rows


def main():
    keys, pool = cited_keys()
    print("verifying %d cited references live ..." % len(keys))
    rows = verify(keys, pool)
    json.dump(rows, open(OUT, "w"), indent=1)
    n = {"VERIFIED": 0, "MISMATCH": 0, "TRANSPORT-UNKNOWN": 0}
    for r in rows:
        n[r["verdict"]] += 1
    print("VERIFIED %d / %d ; TITLE MISMATCH %d ; TRANSPORT-UNKNOWN %d"
          % (n["VERIFIED"], len(rows), n["MISMATCH"], n["TRANSPORT-UNKNOWN"]))
    print("wrote %s" % os.path.relpath(OUT, HERE))
    if n["MISMATCH"] or n["TRANSPORT-UNKNOWN"]:
        print("REFUSING to pass: a mismatch must be repaired and a transport failure is UNKNOWN, "
              "not a finding")
        return 1
    worst = min(r["title_match"] for r in rows)
    print("worst live title match: %.3f (threshold %.2f)" % (worst, THRESHOLD))
    return 0


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

    n = lambda a, b: (lambda s: (s >= THRESHOLD) or (_ for _ in ()).throw(AssertionError()))(
        title_matches(a, b))
    # a real record whose title differs must be rejected ...
    fires("reject-different-paper",
          lambda: n("How Many Random Seeds? Statistical Power Analysis in Deep Reinforcement Learning Experiments",
                    "Deep Reinforcement Learning that Matters"))
    # ... and the TWO-SIDED metric must reject a short generic title scoring 1.00 one-sided
    fires("reject-generic-short",
          lambda: n("Machine Learning Benchmarks", "Accounting for Variance in Machine Learning Benchmarks"))
    holds("accept-identical",
          lambda: n("Statistical power for cluster analysis", "Statistical power for cluster analysis"))
    holds("accept-subtitle",
          lambda: n("How Many Random Seeds? Statistical Power Analysis in Deep Reinforcement Learning Experiments",
                    "How Many Random Seeds? Statistical Power Analysis in Deep RL Experiments"))
    print()
    print("SELFTEST:", "ALL PLANTS CAUGHT" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    import urllib.parse  # noqa: F401  (used inside live_title_crossref)
    sys.exit(selftest() if "--selftest" in sys.argv else main())
