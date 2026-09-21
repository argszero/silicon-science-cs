#!/usr/bin/env python3
"""#87 R404 -- build the bibliography's records from the committed pools, in the journal's house entry form.

Input :  refs_selection_v87.py  (the authored selection: id -> one-line difference)
         refs_raw.json / refs_pool2.json / refs_classic.json  (the harvest; the pooled record is kept as
         `pool_title` so the verifier can check that the live record still bears the title the difference
         line was written against)
Output:  refs_built.json

House entry form (README -> Presentation requirements): `[n] ` authors (`Family, I.`; `et al.` for four or
more, family first, mixed case) -- the year in parentheses -- the title in title case -- the venue or the
identifier -- the link as a resolvable URL -- the entry closing with its one-line `Difference: ...`.

The record's own fields are never typed by hand: a field the pipeline cannot resolve is an ERROR, not a blank.
"""
import io
import json
import os
import re
import sys

import refs_selection_v87 as SEL

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "refs_built.json")

SMALL = {"a", "an", "the", "and", "but", "or", "for", "nor", "of", "on", "in", "to", "with", "at", "by",
         "from", "as", "into", "over", "under", "vs", "via", "per"}
KEEP_UPPER = re.compile(r"^[A-Z0-9]{2,}$|^[A-Z][a-z]*[A-Z]")     # acronyms and CamelCase are not folded


def title_case(s):
    """Title case that leaves acronyms alone (NISQ, QSVM, ZZ, RKHS)."""
    words = (s or "").split()
    out = []
    for i, w in enumerate(words):
        core = w.strip("()[]{}:;,.?!\"'")
        starts_clause = i == 0 or (out and out[-1][-1:] in "?.!:")
        if KEEP_UPPER.match(core):
            out.append(w)
        elif core.lower() in SMALL and not starts_clause and i != len(words) - 1:
            out.append(w.lower())
        elif "-" in core and len(core) > 1:
            out.append("-".join(p[:1].upper() + p[1:] if p and not KEEP_UPPER.match(p) else p
                                for p in w.split("-")))
        else:
            out.append(w[:1].upper() + w[1:] if w else w)
    return " ".join(out)


def family_initial(name):
    """Two record shapes, both handled: 'Yunseo Hwang' (a full name) and 'Hwang, Yunseo' (family first).

    A mononym has no initial to print and is never padded with one (the house rule's second member); an
    initial no record carries would be a fabricated author.
    """
    s = (name or "").strip()
    if not s:
        return ""
    if ", " in s:
        fam, given = s.split(", ", 1)
        given = given.strip()
        return "%s, %s." % (fam.strip(), given[0].upper()) if given else fam.strip()
    parts = s.split()
    if len(parts) == 1:
        # a mononym: the token alone, closed by a period, which is the house form's second admitted
        # shape (`Student. (1908). ...`).  Never padded out with an initial the record does not carry.
        return parts[0] + "."
    return "%s, %s." % (parts[-1], parts[0][0].upper())


def author_string(names, n_authors=None):
    """House form: `Family, I.`; `et al.` for four or more, family name first, one period."""
    if not names:
        return ""
    n = n_authors if n_authors else len(names)
    if n >= 4:
        return family_initial(names[0]) + " et al."
    return ", ".join(family_initial(x) for x in names)


def load_pools():
    raw = json.loads(io.open(os.path.join(HERE, "refs_raw.json"), encoding="utf-8").read())
    p2 = json.loads(io.open(os.path.join(HERE, "refs_pool2.json"), encoding="utf-8").read())
    classic = json.loads(io.open(os.path.join(HERE, "refs_classic.json"), encoding="utf-8").read())
    arxiv = {}
    for blk in raw["arxiv"].values():
        for r in blk["rows"]:
            arxiv.setdefault(r["id"], r)
    for blk in p2["queries"].values():
        for r in blk["rows"]:
            arxiv.setdefault(r["id"], r)
    doi = {}
    for d, r in raw["crossref"].items():
        doi[d.lower()] = r
    for q, v in classic["queries"].items():
        m = v.get("matched")
        if m:
            doi[m["doi"].lower()] = dict(doi=m["doi"], title=m["title"], year=m["year"],
                                         authors=m.get("authors"), n_authors=m.get("n_authors"),
                                         venue=m.get("venue"), type=m.get("type"),
                                         url="https://doi.org/" + m["doi"])
    return arxiv, doi


def main():
    arxiv, doi = load_pools()
    entries, errors = [], []
    for src, pairs in (("arxiv", SEL.ARXIV), ("doi", SEL.CROSSREF)):
        for ident, difference in pairs:
            key = ident.lower()
            rec = arxiv.get(ident) if src == "arxiv" else doi.get(key)
            if rec is None:
                errors.append(dict(source=src, id=ident, why="not found in the committed pools"))
                continue
            if src == "arxiv":
                e = dict(source="arxiv", id=ident, url="https://arxiv.org/abs/" + ident,
                         pool_title=rec["title"], authors_raw=rec["authors"], year=rec["year"],
                         venue="arXiv:%s" % ident, primary=rec.get("primary", ""))
            else:
                e = dict(source="crossref", doi=rec["doi"], url=rec.get("url") or ("https://doi.org/" + rec["doi"]),
                         pool_title=rec["title"], authors_raw=rec.get("authors") or [],
                         n_authors=rec.get("n_authors"), year=rec.get("year"),
                         venue=rec.get("venue") or "Crossref record", type=rec.get("type", ""))
            e["difference"] = " ".join(difference.split())
            e["title"] = title_case(e["pool_title"])
            e["authors"] = author_string(e["authors_raw"], e.get("n_authors") or len(e["authors_raw"]))
            if not e["authors"]:
                errors.append(dict(source=src, id=ident, why="no author resolved by the pool record"))
            if not e["year"]:
                errors.append(dict(source=src, id=ident, why="no year resolved by the pool record"))
            entries.append(e)
    rep = dict(round="R404", n_arxiv=len(SEL.ARXIV), n_doi=len(SEL.CROSSREF),
               n_entries=len(entries), errors=errors, entries=entries)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(rep, indent=1, sort_keys=True))
    print("built %d of %d entries | errors %d | wrote %s"
          % (len(entries), len(SEL.ARXIV) + len(SEL.CROSSREF), len(errors), os.path.basename(OUT)))
    for e in errors:
        print("  ERR %s %s: %s" % (e["source"], e["id"], e["why"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
