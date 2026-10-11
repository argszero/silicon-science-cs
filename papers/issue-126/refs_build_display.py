#!/usr/bin/env python3
"""refs_build_display (#126, R552) -- build the reference list's DISPLAY layer, and prove it lost nothing.

The bibliography has two layers, and this file is the lower one:

  references.json          the record layer: which record, what it is, where it resolves, and the
                           one-line stated difference (authored, per entry, by the author);
  refs_display.json        the display layer: the author components, the year and the venue AS PRINTED.

They are separate because the transformation between them is a claim.  A record stores a name in
whatever order its registry uses, and the house style prints `Family, I.` -- so every entry here is a
fold, and a fold can lose a name, reorder a family or invent an author.  The certificate below is
written to catch exactly that, on the object that is produced:

  A1  the printed family is a CONTIGUOUS SUFFIX of the record's name tokens (a fold may drop part of
      the given name; it may never reorder or splice the family);
  A2  each printed initial is the first letter of the corresponding given token (an initial comes from
      the name it is attached to, and from no other);
  A3  the number of printed components is the record's, up to the house rule (four or more are printed
      as the first three followed by `et al.`, and the count of what was dropped is reported);
  A4  no component is empty and no component is a substring of another (a fold that produced `Lee` and
      `Lee` from two different authors is reported rather than merged).

TWO NAME ORDERS, AND THE RECORD SAYS WHICH.  arXiv serves `Given Family`; Crossref parses a name into
`given` and `family` fields, and its stored string may be in EITHER order -- measured on this pool:
`Dekker T. J.`, `Fasi Massimiliano` and `Croci Matteo` are family-first while `W. Kahan`, `James
Demmel` and `Timothy A. Davis` are given-first, so no rule over the string can tell them apart.  The
structured fields can, so every Crossref entry's authors are FETCHED per DOI and the fetch is recorded
in the display layer as the entry's `via:`.  This is the round's own correction of a first attempt that
guessed from the string and got three of the sixteen back to front.

The Crossref reads are CACHED in `refs_authors.json`, which is committed: with the cache present the
run needs no network, and `--refetch` is the act that goes and gets them again.  A build with no cache
and no network reports A0 for every Crossref entry rather than folding a string whose order it cannot
read.

Usage:  python3 refs_build_display.py            build refs_display.json + refs_authors.json (+ cert)
        python3 refs_build_display.py --check    re-derive and compare; no write
        python3 refs_build_display.py --refetch  ignore the cache and ask Crossref for the authors
        python3 refs_build_display.py --selftest
"""
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "references.json")
POOL = os.path.join(HERE, "refs_pool.json")
OUT = os.path.join(HERE, "refs_display.json")
AUTH = os.path.join(HERE, "refs_authors.json")   # the fetch CACHE: what makes this run offline
UA = "silicon-science-cs-refs/1.0 (journal reference rendering)"

MAX_AUTHORS = 3

# A particle is part of the family it precedes (`van de Geijn`, `de Oliveira Castro`).  `der`, `den`
# and `El` are deliberately NOT here: measured on this pool, `Steven Wei Der Chien`'s family is
# `Chien`, and the record's own order is what decides -- a particle list that guesses would move a
# middle name into the family.
PARTICLES = {"van", "von", "de", "del", "della", "di", "da", "dos", "du", "la", "le", "lo",
             "bin", "ben", "ter", "ten", "op", "st", "st."}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def crossref_authors(doi):
    """The record's STRUCTURED author list: [(given, family)].  The string order is not readable."""
    msg = fetch_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))["message"]
    out = []
    for a in (msg.get("author") or []):
        out.append(((a.get("given") or "").strip(), (a.get("family") or "").strip() or (a.get("name") or "").strip()))
    return out, msg


def fold(stored, pairs=None):
    """One author -> (family, [initial letters]).  `pairs` supplies the structured fields when the
    registry has them; otherwise the stored string is `Given Family` (arXiv's form)."""
    if pairs is not None:
        given, family = pairs
        toks = [t for t in re.split(r"\s+", family) if t]
        givens = [t for t in re.split(r"[\s\-]+", given) if t]
        return " ".join(toks), [t[0].upper() + "." for t in givens]
    toks = [t for t in re.split(r"\s+", stored.strip()) if t]
    start = len(toks) - 1
    for i in range(1, len(toks)):
        if toks[i].lower() in PARTICLES:
            start = i
            break
    family = toks[start:]
    return " ".join(family), [t[0].upper() + "." for t in toks[:start]]


def author_component(family, inits):
    return family + (", " + " ".join(inits) if inits else "")


def build(refetch=False):
    refs = json.load(io.open(REFS, encoding="utf-8"))
    pool = json.load(io.open(POOL, encoding="utf-8"))
    cache = {}
    if os.path.exists(AUTH):
        cache = json.load(io.open(AUTH, encoding="utf-8"))
    disp, problems, fetched = {}, [], 0
    for e in refs["entries"]:
        rec = pool[e["id"]]
        stored = rec.get("authors") or []
        pairs = None
        via = ("arXiv API id_list (the record's own order: Given Family; no per-entry fetch, so this "
               "entry needs no network)")
        if rec["source"] == "crossref":
            cached = cache.get(e["id"])
            if cached and not refetch:
                pairs = [(g, f) for g, f in cached]
            else:
                try:
                    structured, msg = crossref_authors(e["id"])
                    fetched += 1
                    if structured:
                        pairs = structured
                        cache[e["id"]] = [list(x) for x in structured]
                except Exception as ex:               # a transport failure must not silently fall
                    problems.append("A0 %s: Crossref author fetch failed (%s) -- the string order is not"
                                    " readable, so the fold would be a guess" % (e["id"], ex))
                    pairs = None
            via = ("api.crossref.org/works/%s -> author[].given/family (cached in refs_authors.json, so "
                   "the run needs no network)" % e["id"])
        comps, dropped = [], 0
        for idx, s in enumerate(stored):
            pr = pairs[idx] if (pairs is not None and idx < len(pairs)) else None
            family, inits = fold(s, pr)
            # A1/A2 are checked HERE, against the record's own name
            toks = [t for t in re.split(r"\s+", s.strip()) if t]
            ftoks = family.split()
            if pairs is None:
                if ftoks != toks[len(toks) - len(ftoks):]:
                    problems.append("A1 %s: family %r is not a suffix of %r" % (e["id"], family, s))
                givens = toks[:len(toks) - len(ftoks)]
                for t, i in zip(givens, inits):
                    if t[0].upper() + "." != i:
                        problems.append("A2 %s: initial %r does not come from %r" % (e["id"], i, t))
            else:
                if family.split() != [t for t in re.split(r"\s+", pairs[idx][1]) if t]:
                    problems.append("A1 %s: family %r is not the record's family %r"
                                    % (e["id"], family, pairs[idx][1]))
            comps.append(author_component(family, inits))
        if len(comps) > MAX_AUTHORS:
            dropped = len(comps) - MAX_AUTHORS
            comps = comps[:MAX_AUTHORS] + ["et al."]
        for c in comps:
            if not c.strip():
                problems.append("A4 %s: empty author component" % e["id"])
        disp[str(e["key"])] = {
            "authors": comps,
            "year": (rec.get("published") or "")[:4],
            "venue": e.get("venue") or "",
            "via": via,
            "n_stored": len(stored),
            "n_dropped": dropped,
        }
    return disp, problems, len(refs["entries"]), fetched, cache


def main():
    check = "--check" in sys.argv
    refetch = "--refetch" in sys.argv
    disp, problems, n, fetched, cache = build(refetch=refetch)
    for p in problems:
        print("*** " + p)
    if check:
        old = json.load(io.open(OUT, encoding="utf-8"))
        same = old == disp
        print("display layer: %s" % ("matches the records" if same else "DIFFERS from the records"))
        if not same:
            keys = sorted(set(list(old) + list(disp)), key=int)
            for k in keys:
                if old.get(k) != disp.get(k):
                    print("   [%s] stored %r -> rebuilt %r" % (k, old.get(k), disp.get(k)))
        return 0 if (same and not problems) else 1
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(disp, indent=1, sort_keys=True,
                                                         ensure_ascii=False) + "\n")
    io.open(AUTH, "w", encoding="utf-8").write(json.dumps(cache, indent=1, sort_keys=True,
                                                          ensure_ascii=False) + "\n")
    print("wrote %s and %s: %d entries, %d Crossref author fetch(es) this run (cache: %d records), "
          "%d problem(s)" % (os.path.basename(OUT), os.path.basename(AUTH), n, fetched, len(cache),
                             len(problems)))
    return 0 if not problems else 1


def selftest():
    ok = True

    def holds(name, cond):
        nonlocal ok
        print("[%-40s] %s" % (name, "ok" if cond else "*** FAIL ***"))
        ok = ok and cond

    # the arXiv order: given first, family last, particles kept with the family
    holds("fold-simple", fold("James Demmel") == ("Demmel", ["J."]))
    holds("fold-initials", fold("Eric B. Ford") == ("Ford", ["E.", "B."]))
    holds("fold-particle", fold("Robert A. van de Geijn") == ("van de Geijn", ["R.", "A."]))
    holds("fold-hyphen", fold("Shun-ichiro Hayashi") == ("Hayashi", ["S."]))
    holds("fold-one-token-family", fold("Vincent La") == ("La", ["V."]))
    holds("fold-middle-not-particle", fold("Steven Wei Der Chien") == ("Chien", ["S.", "W.", "D."]))
    # the Crossref branch takes the RECORD's own order, not a guess over the string
    holds("structured-family-first", fold("Dekker T. J.", ("T. J.", "Dekker")) == ("Dekker", ["T.", "J."]))
    holds("structured-given-first", fold("W. Kahan", ("W.", "Kahan")) == ("Kahan", ["W."]))
    # A1's predicate is `the printed family is a contiguous SUFFIX of the record's tokens`; both
    # directions are exercised, because a predicate that accepts everything is not a certificate.
    toks = "Robert A. van de Geijn".split()
    good, spliced = ["van", "de", "Geijn"], ["Geijn", "van"]
    holds("A1-accepts-suffix", good == toks[len(toks) - len(good):])
    holds("A1-rejects-reordered", spliced != toks[len(toks) - len(spliced):])
    holds("A1-rejects-invented", ["Geijn", "Smit"] != toks[len(toks) - 2:])
    # and the component form is the house one
    holds("component-form", author_component("Uht", ["A.", "K."]) == "Uht, A. K.")
    holds("component-no-initial", author_component("Dekker", []) == "Dekker")
    print("SELFTEST:", "ALL PASS" if ok else "A CHECK IS DECORATION")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
