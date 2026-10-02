#!/usr/bin/env python3
"""Issue #118 -- reference VERIFICATION.

Verification is NOT discovery and NOT curation.  This file re-fetches each CURATED entry by its own
identifier from the index that owns the id (arXiv) and compares the returned title against the
curated title.  A citation that cannot be resolved, or whose title does not match, is a defect and
the run FAILS.

Two-sided control (`--plant`): a corrupted title and an invented identifier are injected into a
throwaway copy of the curated set; BOTH must produce a failure, or the verifier is decoration.

Usage:  /usr/bin/python3 refs_tool.py verify [--refresh]
        /usr/bin/python3 refs_tool.py plant
Out:    refs/verify.log
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
CUR = "refs/curated.json"
LOG = "refs/verify.log"
CACHE = "refs/verify_cache"

def norm(s):
    """Normalise for comparison: NFKC, lower, collapse non-alphanumerics."""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[^0-9a-z]+", " ", s.lower())
    return " ".join(s.split())

def fetch_title(aid, refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, aid.replace("/", "_") + ".json")
    if os.path.exists(path) and not refresh:
        return json.load(open(path))
    url = "http://export.arxiv.org/api/query?id_list=%s&max_results=1" % aid
    got = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                raw = r.read().decode("utf-8", "replace")
            m = re.search(r"<entry>(.*?)</entry>", raw, re.S)
            if m:
                t = re.search(r"<title>(.*?)</title>", m.group(1), re.S).group(1)
                got = " ".join(t.split())
            else:
                got = None
            break
        except Exception as e:
            if attempt == 3:
                got = "FETCH_ERROR: %s" % e
            time.sleep(3 * (attempt + 1))
    json.dump(got, open(path, "w"))
    return got

def verify(entries, refresh=False):
    """Return (lines, n_ok, n_bad)."""
    lines, ok, bad = [], 0, 0
    for e in entries:
        aid, want = e["id"], e["title"]
        cached = os.path.exists(os.path.join(CACHE, aid.replace("/", "_") + ".json"))
        got = fetch_title(aid, refresh)
        if got is None:
            verdict, detail = "UNRESOLVED", "no entry returned for this identifier"
            bad += 1
        elif got.startswith("FETCH_ERROR"):
            verdict, detail = "UNRESOLVED", got
            bad += 1
        elif norm(got) == norm(want):
            verdict, detail = "OK", got
            ok += 1
        else:
            verdict, detail = "MISMATCH", "index=%r curated=%r" % (got, want)
            bad += 1
        lines.append("%-11s %-14s %-30s %s" % (verdict, e["bare"], e["role"], detail))
        if not cached or refresh:
            time.sleep(3)          # rate-limit only real fetches; a cached re-run is instant
    return lines, ok, bad

def cmd_verify(refresh):
    if not os.path.exists(CUR):
        print("missing %s -- run refs_curate.py first" % CUR, file=sys.stderr); sys.exit(1)
    entries = json.load(open(CUR))["entries"]
    print("verifying %d curated entries by identifier" % len(entries))
    lines, ok, bad = verify(entries, refresh)
    with open(LOG, "w") as f:
        f.write("# issue #118 reference verification -- resolved by identifier against arXiv\n")
        f.write("# %d entries: %d OK, %d PROBLEM\n" % (len(entries), ok, bad))
        f.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if not l.startswith("OK")))
    print("\n%d OK, %d PROBLEM -> %s" % (ok, bad, LOG))
    return 1 if bad else 0

def cmd_plant():
    """Two-sided control on a throwaway copy: a corrupted title and an invented id must both FAIL."""
    entries = json.load(open(CUR))["entries"]
    bad_title = dict(entries[0]); bad_title["title"] = "A Deliberately Corrupted Title That Is Not Real"
    bad_id = dict(entries[1]); bad_id["id"] = "9999.99999"; bad_id["bare"] = "9999.99999"
    print("plant: 1 corrupted title + 1 invented identifier (must BOTH fail)")
    lines, ok, bad = verify([bad_title, bad_id], refresh=True)
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
