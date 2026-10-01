#!/usr/bin/env python3
"""#93 R417 -- the citation keys: one stable key per built record, so a section can cite before the list exists.

Why keys exist at all.  The house bibliography is **numbered `[1]`-`[n]` in the order of first citation**, and
a manuscript is written over many rounds: a section written today must not have to be renumbered when the next
section cites an earlier work.  The manuscript therefore cites by a **key**, and the numbering is derived from
the finished text's first-citation order by the assembly step -- the same arrangement this journal's #87 uses.

The keys are **derived from the built records, never typed**: `Family+year`, ASCII-folded and lowercased, with a
letter suffix on collision (two works by the same first author in the same year).  A key I typed by hand would be
a second carrier of the record's identity, which is exactly the class of defect this round's own build step
exists to catch.

Input : refs_built.json
Output: refs_keys.json  (key -> identifier, source, title, year, authors, url, difference)

Run:  python3 refs_keys.py            (writes refs_keys.json; refuses on a collision it cannot resolve)
      python3 refs_keys.py --check    (re-derives and compares against the committed file; exit 1 on drift)
"""
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_keys.json")


def ascii_fold(s):
    """strip accents and everything that is not a letter or digit."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())


def family_of(authors_raw):
    """Two record shapes: arXiv stores 'Given Family'; Crossref stores 'Family, Given'."""
    if not authors_raw:
        return ""
    a = authors_raw[0].strip()
    if ", " in a:
        return a.split(", ", 1)[0]
    return a.split()[-1] if a.split() else ""


def build_keys():
    rep = json.loads(io.open(os.path.join(HERE, "refs_built.json"), encoding="utf-8").read())
    keys, taken = {}, {}
    for e in rep["entries"]:
        base = ascii_fold(family_of(e.get("authors_raw"))) + str(e.get("year") or "")
        if not base[:-4] or not e.get("year"):
            raise SystemExit("refusing: cannot form a key for %s (family=%r year=%r)"
                             % (e["key"], family_of(e.get("authors_raw")), e.get("year")))
        k, n = base, 0
        while k in keys:
            n += 1
            k = base + chr(96 + n)          # a, b, c ... deterministic, given the entry order
        keys[k] = dict(key=k, identifier=e["key"], source=e["source"], title=e["title"],
                       pool_title=e.get("pool_title"), year=e["year"], authors=e["authors"],
                       url=e["url"], difference=e["difference"])
        taken.setdefault(base, []).append(k)
    # The round label is a PROVENANCE claim about this file, and a constant would keep saying R417 after a later
    # round re-derives it -- the same defect as a label that names nothing (R424 fixed the build's `?` DOI label).
    # It therefore names the last round that wrote the file, and the round the pipeline was first built in.
    return dict(round="R417; re-derived at R424", n=len(keys),
                collisions={b: v for b, v in taken.items() if len(v) > 1},
                keys=keys)


def main():
    got = build_keys()
    text = json.dumps(got, indent=1, sort_keys=True)
    if "--check" in sys.argv:
        have = io.open(OUT, encoding="utf-8").read()
        same = have == text
        print("refs_keys.json: %d keys | %s" % (got["n"], "identical" if same else "DRIFT"))
        if not same:
            print("  re-derived %d chars, committed %d chars" % (len(text), len(have)))
        return 0 if same else 1
    io.open(OUT, "w", encoding="utf-8").write(text)
    print("wrote %d keys | collisions %d (%s)" % (got["n"], len(got["collisions"]), got["collisions"]))
    fams = sorted(got["keys"])
    print("  first %s ... last %s" % (fams[0], fams[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
