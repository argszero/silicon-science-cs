#!/usr/bin/env python3
"""Build issue #50's bibliography data layer from the VERIFIED reference layer.

Inputs (all committed under `artefacts/`):

  refs_order.json          the citation order, derived by `assemble.py` from the manuscript
  refs_verified_v50.json   each row's locator re-read against the live record (R379)
  refs_selection_v50.json  the authored rows: section, anchor, one-line stated difference
  refs_year_supply_v50.json  the declared years, each naming its sources

Outputs (committed, and the only inputs `refs_render.py` has):

  references.json    the ordered entry list -- what the bibliography prints
  refs_display.json  the author/year/venue block per entry, in house form

The author form is `Family, I.` and THE COMMA IS THE DISCRIMINAND: Crossref states
`Family, Given`, arXiv states `Given Family`.  Measured over the 441 author strings of the
verified layer: 168 comma-form, 273 no-comma, and **zero** strings carrying a lowercase
particle before the family name, which is what makes "the last token is the family" a
reading of this corpus rather than an assumption about names.  The measurement is repeated
at build time and a particle, if one ever appears, fails the build instead of being
silently mangled.

An entry with no author is printed with no author block: 4 of 137 records carry no author
field, and inventing one would be an edit to the record.  `reference-check.md` names them.

Usage:
  python3 refs_build_display.py            build both outputs
  python3 refs_build_display.py --check    rebuild in memory and compare (no write)
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "artefacts")
ORDER = os.path.join(HERE, "refs_order.json")
REFERENCES = os.path.join(HERE, "references.json")
DISPLAY = os.path.join(HERE, "refs_display.json")


def load(name):
    return json.load(io.open(os.path.join(ART, name), encoding="utf-8"))


def initial(tok):
    """The house initial(s) of one given-name token.

    `Hyung-Chan` -> `H.-C.` and `X.-H.` -> `X.-H.` (the hyphen is preserved, because a
    hyphenated given name is one name and not two); `J.G.` -> `J. G.` (dotted initials are
    separate names the record printed without a space); `Cosmin` -> `C.`.
    """
    tok = tok.strip()
    if not tok:
        return ""
    if "-" in tok:
        segs = [s for s in re.split(r"[.\-]", tok) if s]
        return "-".join(s[0].upper() + "." for s in segs)
    if "." in tok:
        segs = [s for s in tok.split(".") if s]
        return " ".join(s[0].upper() + "." for s in segs)
    return tok[0].upper() + "."


def house_author(s):
    """One author string, in the record's own printed form, as `Family, I.`"""
    s = (s or "").strip()
    if not s:
        return ""
    if "," in s:                      # Crossref: Family, Given
        fam, given = s.split(",", 1)
        fam, given = fam.strip(), given.strip()
    else:                             # arXiv: Given Family (last token is the family)
        toks = s.split()
        fam, given = toks[-1], " ".join(toks[:-1])
    ini = " ".join(x for x in (initial(t) for t in given.split()) if x)
    return (fam + ", " + ini).strip().rstrip(",") if ini else fam


def particle_check(authors):
    """The property that makes the arXiv read a reading rather than an assumption."""
    bad = []
    for s in authors:
        if "," in s:
            continue
        toks = s.split()
        if len(toks) > 1 and any(t[:1].islower() for t in toks[:-1]):
            bad.append(s)
    return bad


def entry_title(rec_title, notes, key, problems):
    """The title this entry prints, and whether a declaration was applied.

    The entry prints the record's title VERBATIM.  A declaration may replace it -- measured:
    exactly one record of the 137 carries a title field polluted with something that is not a
    title -- and the declaration is accepted only when the title it states is a PREFIX of the
    record's title field, which is a property of the record rather than of the declaration.

    This function's first version cut every entry's title at the end of its anchor, on the
    theory that text past the anchor was pollution.  The anchor is a prefix of its own title in
    the ordinary case, so that rule truncated **66 of 137** titles to short phrases.  What
    caught it was the count being printed: a rule whose blast radius nobody counts is a rule
    nobody has read.
    """
    t = (rec_title or "").strip()
    dec = notes.get(key)
    if dec is None:
        return t, False
    claim = (dec.get("title") or "").strip()
    if not claim or not t.lower().startswith(claim.lower()):
        problems.append("declaration for %s states a title that is not a prefix of the record's "
                        "title field, so it cannot be read off the record: %r" % (key, claim))
        return t, False
    return t[:len(claim)].rstrip(" ,;:.") if len(t) > len(claim) else claim, True


def fold(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def declared_authors(rec_authors, dec, key, problems):
    """Whether a transposition declaration is a READING of the record.

    The property checked is mechanical: swapping the two fields of each record string must
    reproduce the declared author, after folding case and punctuation.  A declaration that does
    not satisfy it is a correction typed over the record -- which this package accepts only with
    evidence, and here the evidence is available, so it is required.
    """
    declared = dec.get("authors") or []
    if len(declared) != len(rec_authors):
        problems.append("author declaration for %s states %d author(s) for %d record string(s)"
                        % (key, len(declared), len(rec_authors)))
        return None
    for got, raw in zip(declared, rec_authors):
        if "," not in raw:
            problems.append("author declaration for %s: the record string %r carries no comma, so "
                            "there is no transposition to read" % (key, raw))
            return None
        a, b = [x.strip() for x in raw.split(",", 1)]
        if fold(b + " " + a) != fold(got):
            problems.append("author declaration for %s: swapping %r gives %r, not the declared %r"
                            % (key, raw, b + ", " + a, got))
            return None
    return declared


def build():
    order = json.load(io.open(ORDER, encoding="utf-8"))["keys"]
    sel = {r["key"]: r for r in load("refs_selection_v50.json")["rows"]}
    ver = {r["key"]: r for r in load("refs_verified_v50.json")["rows"]}
    sup = load("refs_year_supply_v50.json")["rows"]
    notes = load("refs_title_notes_v50.json")["rows"]
    auth_notes = load("refs_author_notes_v50.json")["rows"]

    problems, entries, disp = [], [], {}
    all_authors, declared = [], []
    declared_authors_applied = []
    for i, k in enumerate(order, 1):
        if k not in sel or k not in ver:
            problems.append("row %d (%s): no selection or no verification" % (i, k))
            continue
        s, v = sel[k], ver[k]
        year = v.get("record_year")
        if year is None:
            problems.append("row %d (%s): no year and no declaration" % (i, k))
            continue
        if v["locator_kind"] == "DOI":
            url, source, venue = "https://doi.org/" + v["locator"], "crossref", (v.get("record_venue") or "")
        else:
            url, source = "https://arxiv.org/abs/" + v["locator"], "arxiv"
            venue = "arXiv preprint arXiv:" + v["locator"]
        title, cut = entry_title(v.get("record_title"), notes, k, problems)
        if cut:
            declared.append((k, v.get("record_title")))
        raw_authors = v.get("record_authors") or []
        dec_a = auth_notes.get(k)
        authors = []
        if dec_a is not None:
            got = declared_authors(raw_authors, dec_a, k, problems)
            if got is not None:
                authors = list(got)
                declared_authors_applied.append(k)
        if not authors:
            authors = [house_author(a) for a in raw_authors if house_author(a)]
        all_authors.extend(v.get("record_authors") or [])
        entries.append({
            "key": i, "cite": k, "id": v["locator"], "source": source, "status": v["verdict"],
            "title": title, "recorded_title": v.get("record_title", ""),
            "url": url, "venue": venue, "difference": s["difference"],
            "year_field": v.get("record_year_field"), "section": s["section"],
        })
        disp[str(i)] = {"authors": authors, "year": str(year), "venue": venue,
                        "via": "%s %s" % ("api.crossref.org/works/" if source == "crossref"
                                          else "export.arxiv.org id_list", v["locator"])}

    parts = particle_check(all_authors)
    if parts:
        problems.append("%d author string(s) carry a lowercase particle, so the arXiv "
                        "family read is not a reading of this corpus: %s" % (len(parts), parts[:5]))
    if len(entries) != len(order):
        problems.append("%d entry(ies) built for %d ordered key(s)" % (len(entries), len(order)))
    if len(disp) != len(order):
        problems.append("%d display record(s) for %d ordered key(s)" % (len(disp), len(order)))
    years = sorted({e["year_field"] for e in entries})
    noauth = [e["cite"] for e in entries if not disp[str(e["key"])]["authors"]]
    return ({"what": "issue #50 bibliography, in citation order, built from the verified layer",
             "rule": "one entry per cited key; the order is the manuscript's first-citation order; "
             "titles are the record's own except where a declaration names one",
             "n": len(entries), "year_fields": years, "entries_without_author": noauth,
             "problems": problems},
            entries, disp, {"declared": declared, "declared_authors": declared_authors_applied, "no_author": noauth,
                            "n_authors": len(all_authors), "year_fields": years})


def main():
    doc, entries, disp, stats = build()
    doc["entries"] = entries
    if doc["problems"]:
        print("BUILD FAILED: %d problem(s)" % len(doc["problems"]))
        for p in doc["problems"]:
            print("  " + p)
        return 1
    fresh = {"refs": json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
             "disp": json.dumps(disp, ensure_ascii=False, indent=1) + "\n"}

    if "--check" in sys.argv:
        ok = True
        for path, key in ((REFERENCES, "refs"), (DISPLAY, "disp")):
            have = io.open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            same = have == fresh[key]
            ok = ok and same
            print("%s matches a fresh build: %s" % (os.path.basename(path), same))
        print("  %d entries, %d author string(s) read, year fields %s"
              % (len(entries), stats["n_authors"], doc["year_fields"]))
        return 0 if ok else 1

    io.open(REFERENCES, "w", encoding="utf-8").write(fresh["refs"])
    io.open(DISPLAY, "w", encoding="utf-8").write(fresh["disp"])
    print("built %d entr(ies) into references.json and refs_display.json" % len(entries))
    print("  author strings read: %d, of which 0 carry a lowercase particle (the read's precondition)"
          % stats["n_authors"])
    print("  year fields: " + ", ".join(doc["year_fields"]))
    print("  entries with no author block: %d of %d%s"
          % (len(stats["no_author"]), len(entries),
             "" if not stats["no_author"] else " (" + ", ".join(stats["no_author"]) + ")"))
    print("  entries whose author list came from a declaration (transposition read off the record): %d of %d%s"
          % (len(stats["declared_authors"]), len(entries),
             "" if not stats["declared_authors"] else " (" + ", ".join(stats["declared_authors"]) + ")"))
    print("  entries whose title came from a declaration (record title verified as its prefix): %d of %d%s"
          % (len(stats["declared"]), len(entries),
             "" if not stats["declared"] else " (" + ", ".join(k for k, _ in stats["declared"]) + ")"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
