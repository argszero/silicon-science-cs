#!/usr/bin/env python3
"""Issue #120 -- reference VERIFICATION.

Verification is NOT discovery and NOT curation.  This file re-fetches each CURATED entry by its own
identifier from the index that owns the id -- arXiv for an arXiv id, Crossref for a DOI -- and
compares the returned title against the curated title.  A citation that cannot be resolved, or whose
title does not match, is a defect and the run FAILS.

Two-sided control (`plant`): a corrupted title and an invented identifier are injected into a
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
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
CUR = "refs/curated.json"
LOG = "refs/verify.log"
CACHE = "refs/verify_cache"
MAILTO = "how2how2how2-arch@users.noreply.github.com"      # Crossref etiquette: a real contact


def norm(s):
    """Normalise for comparison: NFKC, lower, collapse non-alphanumerics."""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[^0-9a-z]+", " ", s.lower())
    return " ".join(s.split())


def fetch_arxiv(aid):
    url = "http://export.arxiv.org/api/query?id_list=%s&max_results=1" % aid
    with urllib.request.urlopen(url, timeout=45) as r:
        raw = r.read().decode("utf-8", "replace")
    # Parse through the XML parser, NOT a regex over the raw text: the feed carries entity
    # references (&amp; etc.), and a regex returns them literally, so any title containing '&'
    # was reported as a MISMATCH against a curated title that is identical (measured: 1 of 129).
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return None
    e = root.find("a:entry", NS)
    if e is None:
        return None
    t = e.find("a:title", NS)
    return " ".join(t.text.split()) if t is not None and t.text else None


def fetch_crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "silicon-science-cs/1.0 (mailto:%s)" % MAILTO})
    with urllib.request.urlopen(req, timeout=45) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    title = (j.get("message", {}).get("title") or [None])[0]
    return " ".join(title.split()) if title else None


def fetch_title(aid, refresh=False):
    """Route by identifier: a DOI (starts with '10.') goes to Crossref, everything else to arXiv."""
    os.makedirs(CACHE, exist_ok=True)
    key = ("doi_" if aid.startswith("10.") else "arx_") + aid.replace("/", "_")
    path = os.path.join(CACHE, key + ".json")
    if os.path.exists(path) and not refresh:
        return json.load(open(path))
    got = None
    for attempt in range(4):
        try:
            got = fetch_crossref(aid) if aid.startswith("10.") else fetch_arxiv(aid)
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
        cached = os.path.exists(os.path.join(
            CACHE, ("doi_" if aid.startswith("10.") else "arx_") + aid.replace("/", "_") + ".json"))
        got = fetch_title(aid, refresh)
        if got is None:
            verdict, detail = "UNRESOLVED", "no record returned for this identifier"
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
        lines.append("%-11s %-15s %-12s %s" % (verdict, e["bare"], e["role"], detail))
        if not cached or refresh:
            time.sleep(3)          # rate-limit only real fetches; a cached re-run is instant
    return lines, ok, bad


def cmd_verify(refresh):
    if not os.path.exists(CUR):
        print("missing %s -- run refs_curate.py first" % CUR, file=sys.stderr)
        sys.exit(1)
    entries = json.load(open(CUR))["entries"]
    n_doi = sum(1 for e in entries if e["id"].startswith("10."))
    print("verifying %d curated entries by identifier (%d via Crossref, %d via arXiv)"
          % (len(entries), n_doi, len(entries) - n_doi))
    lines, ok, bad = verify(entries, refresh)
    with open(LOG, "w") as f:
        f.write("# issue #120 reference verification -- resolved by identifier at the index that\n")
        f.write("# owns the id: arXiv (export.arxiv.org) for arXiv ids, Crossref (api.crossref.org)\n")
        f.write("# for DOIs.  %d entries: %d OK, %d PROBLEM\n" % (len(entries), ok, bad))
        f.write("\n".join(lines) + "\n")
    print("\n".join(l for l in lines if not l.startswith("OK")))
    print("\n%d OK, %d PROBLEM -> %s" % (ok, bad, LOG))
    return 1 if bad else 0


def cmd_plant():
    """Two-sided control on a throwaway copy: a corrupted title and an invented id must both FAIL."""
    entries = json.load(open(CUR))["entries"]
    arx = [e for e in entries if not e["id"].startswith("10.")]
    doi = [e for e in entries if e["id"].startswith("10.")]
    bad_title = dict(entries[0])
    bad_title["title"] = "A Deliberately Corrupted Title That Is Not Real"
    bad_id = dict(arx[0]); bad_id["id"] = "9999.99999"; bad_id["bare"] = "9999.99999"
    bad_doi = dict(doi[0]); bad_doi["id"] = "10.9999/not-a-real-doi"; bad_doi["bare"] = "10.9999/not-a-real-doi"
    print("plant: 1 corrupted title + 1 invented arXiv id + 1 invented DOI (all must fail)")
    lines, ok, bad = verify([bad_title, bad_id, bad_doi], refresh=True)
    for l in lines:
        print("   " + l)
    caught_title = any(l.startswith("MISMATCH") for l in lines)
    caught_arx = any(l.startswith(("UNRESOLVED", "MISMATCH")) and "9999.99999" in l for l in lines)
    caught_doi = any(l.startswith(("UNRESOLVED", "MISMATCH")) and "not-a-real-doi" in l for l in lines)
    print("   corrupted title caught: %s | invented arXiv id caught: %s | invented DOI caught: %s"
          % (caught_title, caught_arx, caught_doi))
    if not (caught_title and caught_arx and caught_doi):
        print("   !! the verifier is DECORATION -- a plant escaped", file=sys.stderr)
        sys.exit(9)
    print("   -> all three plants caught; the verifier can fail on both routes")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    refresh = "--refresh" in sys.argv
    if cmd == "verify":
        sys.exit(cmd_verify(refresh))
    elif cmd == "plant":
        sys.exit(cmd_plant())
    else:
        print("usage: refs_tool.py verify|plant [--refresh]", file=sys.stderr)
        sys.exit(2)
