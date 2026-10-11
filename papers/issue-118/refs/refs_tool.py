#!/usr/bin/env python3
"""Issue #118 -- reference VERIFICATION.

Verification is NOT discovery and NOT curation.  This file re-fetches each CURATED entry by its own
identifier from the index that owns the id (arXiv) and compares the returned title against the
curated title.  A citation that cannot be resolved, or whose title does not match, is a defect and
the run FAILS.

The fetch reads the **whole record**, not the title alone: the authors the record states are captured
in the SAME request that resolves the title, because the author component of a bibliography entry is
evidence about the same record the title check is evidence about.  A separate, later request could
resolve a different revision of the record, and an author list typed from memory is not evidence at
all.  They are written to `refs/authors.json` -- the renderer reads them from there, and
`refs_report.py` prints the raw string the record gave beside the rendered form.

Two-sided control (`--plant`): a corrupted title and an invented identifier are injected into a
throwaway copy of the curated set; BOTH must produce a failure, or the verifier is decoration.

Usage:  /usr/bin/python3 refs_tool.py verify [--refresh]
        /usr/bin/python3 refs_tool.py plant
Out:    refs/verify.log, refs/authors.json
"""
import datetime
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

NS = {"a": "http://www.w3.org/2005/Atom"}
CUR = "refs/curated.json"
LOG = "refs/verify.log"
AUTH = "refs/authors.json"
CACHE = "refs/verify_cache"
BATCH = 40

def norm(s):
    """Normalise for comparison: NFKC, lower, collapse non-alphanumerics."""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[^0-9a-z]+", " ", s.lower())
    return " ".join(s.split())

def parse_entry(block):
    """One `<entry>` as the record states it: its title, and its author names IN THE RECORD'S OWN ORDER.

    The arXiv API carrier states names as `Given Family`; a name that carries a comma is already
    `Family, Given` (the abstract-page carrier's order).  Both are kept VERBATIM here -- deciding
    which token is the family is the renderer's job, and it is auditable there because the raw
    string is printed beside the rendered form.
    """
    t = re.search(r"<title>(.*?)</title>", block, re.S)
    if not t:
        return None
    authors = [" ".join(a.split())
               for a in re.findall(r"<author>\s*<name>(.*?)</name>", block, re.S)]
    return {"title": " ".join(t.group(1).split()), "authors": authors}


def cache_path(aid):
    return os.path.join(CACHE, aid.replace("/", "_") + ".json")


def cached_record(aid):
    """The cached whole record, or None.  A cache entry written by an older revision of this file
    (a bare title string) is NOT trusted -- it carries no author evidence, and reading it as one
    would print a title-only entry while claiming the record had no authors."""
    p = cache_path(aid)
    if not os.path.exists(p):
        return None
    rec = json.load(open(p))
    return rec if isinstance(rec, dict) and "title" in rec else None


def _get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:                                       # noqa: BLE001
            if attempt == 3:
                return None
            time.sleep(3 * (attempt + 1))
    return None


def prefetch(ids):
    """Fill the cache for `ids` in FEW requests, without changing what a cache entry MEANS.

    `id_list` answers with at most `max_results` entries and its default is 10, so a chunk larger
    than the default is SILENTLY TRUNCATED: the parameter is passed explicitly, the number of
    entries returned is compared against the number asked for, and a short answer is reported
    rather than absorbed.  An identifier the batch did not answer for simply falls through to the
    single-id route in `fetch_record`.
    """
    todo = [i for i in ids if cached_record(i) is None]
    if not todo:
        return 0, 0
    got_all, asked = 0, len(todo)
    for k in range(0, len(todo), BATCH):
        part = todo[k:k + BATCH]
        url = ("https://export.arxiv.org/api/query?id_list=%s&max_results=%d"
               % (urllib.parse.quote(",".join(part)), len(part)))
        raw = _get(url)
        if raw is None:
            print("   (batch %d-%d unavailable -- those entries use the single-id route)"
                  % (k, k + len(part)))
            continue
        blocks = re.findall(r"<entry>(.*?)</entry>", raw, re.S)
        if len(blocks) < len(part):
            print("   (batch %d-%d returned %d entries for %d identifiers -- the shortfall falls"
                  " through to the single-id route)" % (k, k + len(part), len(blocks), len(part)))
        by_key = {}
        for blk in blocks:
            rec = parse_entry(blk)
            m = re.search(r"<id>\s*(?:https?://)?[^<]*?/abs/([^<]+?)\s*</id>", blk)
            if not (rec and m):
                continue
            full = m.group(1)
            by_key[full] = rec
            by_key[full.split("v")[0]] = rec          # a bare id answers for its versioned form too
        for i in part:
            rec = by_key.get(i) or by_key.get(i.split("v")[0])
            if rec:
                json.dump(rec, open(cache_path(i), "w"))
                got_all += 1
        time.sleep(3)                                  # one pause per REQUEST, not per identifier
    return got_all, asked


def fetch_record(aid):
    """The whole record for one identifier: title and authors from ONE fetch."""
    rec = cached_record(aid)
    if rec is not None:
        return rec
    os.makedirs(CACHE, exist_ok=True)
    url = "https://export.arxiv.org/api/query?id_list=%s&max_results=1" % urllib.parse.quote(aid)
    raw = _get(url)
    if raw is None:
        return {"title": None, "authors": []}
    m = re.search(r"<entry>(.*?)</entry>", raw, re.S)
    rec = parse_entry(m.group(1)) if m else None
    if rec is None:
        return {"title": None, "authors": []}
    json.dump(rec, open(cache_path(aid), "w"))
    return rec


def verify(entries, refresh=False):
    """Return (lines, n_ok, n_bad, authors_by_bare)."""
    if refresh:
        ids = [e["id"] for e in entries]
        for e in entries:
            p = cache_path(e["id"])
            if os.path.exists(p):
                os.remove(p)
        prefetch(ids)
    else:
        prefetch([e["id"] for e in entries])
    lines, ok, bad, authors = [], 0, 0, {}
    for e in entries:
        aid, bare, want = e["id"], e["bare"], e["title"]
        rec = fetch_record(aid)
        got = rec["title"]
        if got is None:
            verdict, detail = "UNRESOLVED", "no entry returned for this identifier"
            bad += 1
        elif norm(got) == norm(want):
            verdict, detail = "OK", got
            ok += 1
            authors[bare] = rec["authors"]
        else:
            verdict, detail = "MISMATCH", "index=%r curated=%r" % (got, want)
            bad += 1
        lines.append("%-11s %-14s %-30s %s" % (verdict, bare, e["role"], detail))
    return lines, ok, bad, authors


def cmd_verify(refresh):
    if not os.path.exists(CUR):
        print("missing %s -- run refs_curate.py first" % CUR, file=sys.stderr); sys.exit(1)
    entries = json.load(open(CUR))["entries"]
    print("verifying %d curated entries by identifier" % len(entries))
    lines, ok, bad, authors = verify(entries, refresh)
    with open(LOG, "w") as f:
        f.write("# issue #118 reference verification -- resolved by identifier against arXiv\n")
        f.write("# %d entries: %d OK, %d PROBLEM\n" % (len(entries), ok, bad))
        f.write("\n".join(lines) + "\n")
    # The author component is written only for entries whose record RESOLVED and whose title
    # matched: an entry the run could not confirm is one whose authors are not evidence either.
    missing = sorted(e["bare"] for e in entries if e["bare"] not in authors)
    json.dump({"transport": "arXiv API (export.arxiv.org/api/query?<id>) -- names as the record "
                             "states them, verbatim; the API carrier's order is `Given Family`",
               "captured": "in the same fetch that resolved each title",
               "retrieved": datetime.date.today().isoformat(),
               "n": len(authors),
               "authors": {k: authors[k] for k in sorted(authors)}},
              open(AUTH, "w"), indent=1, ensure_ascii=False)
    print("\n".join(l for l in lines if not l.startswith("OK")))
    if missing:
        print("\n!! %d resolved entries carry no author record: %s"
              % (len(missing), missing[:8]), file=sys.stderr)
        ok = 0
    print("\n%d OK, %d PROBLEM -> %s; %d author records -> %s"
          % (ok, bad, LOG, len(authors), AUTH))
    return 1 if (bad or missing) else 0

def cmd_plant():
    """Two-sided control on a throwaway copy: a corrupted title and an invented id must both FAIL."""
    entries = json.load(open(CUR))["entries"]
    bad_title = dict(entries[0]); bad_title["title"] = "A Deliberately Corrupted Title That Is Not Real"
    bad_id = dict(entries[1]); bad_id["id"] = "9999.99999"; bad_id["bare"] = "9999.99999"
    print("plant: 1 corrupted title + 1 invented identifier (must BOTH fail)")
    lines, ok, bad, _auth = verify([bad_title, bad_id], refresh=True)
    for l in lines:
        print("   " + l)
    caught_title = any(l.startswith("MISMATCH") for l in lines)
    caught_id = any(l.startswith(("UNRESOLVED", "MISMATCH")) and "9999.99999" in l for l in lines)
    print("   corrupted title caught: %s | invented id caught: %s" % (caught_title, caught_id))
    if not (caught_title and caught_id):
        print("   !! the verifier is DECORATION -- a plant escaped", file=sys.stderr); sys.exit(9)
    print("   -> both plants caught; the verifier can fail")
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    refresh = "--refresh" in sys.argv
    if cmd == "verify":
        sys.exit(cmd_verify(refresh))
    elif cmd == "plant":
        sys.exit(cmd_plant())
    else:
        print("usage: refs_tool.py verify|plant [--refresh]", file=sys.stderr); sys.exit(2)
