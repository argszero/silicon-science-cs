#!/usr/bin/env python3
"""Build issue #42's display metadata -- `artefacts/refs_display.json`.

The manuscript's `## References` section is GENERATED (see `refs_render.py`), so the entry's parts come
from data rather than from the assembly loop:

    artefacts/refs_ordered.json   the verified references, in citation order (key, authors, year, title,
                                  venue, doi, kind, ident) -- the record AS READ
    refs_differences.json         the one-line stated difference, AUTHORED per entry (round 1, required
                                  change 2: 0 of 117 entries carried one)

This file builds the display fields from those two:

  * authors are normalised to `Family, I.` (the house style), from either `Family, Given` or `Given
    Family`, collapsing on whitespace and dropping a trailing period; four or more are abbreviated by
    the renderer, not here, so the full list stays in the data;
  * the year is the record's year, and where the registry returns NONE it is supplied by DECLARATION --
    `YEAR_SUPPLY` names the entry, the value and the evidence, and the build prints it.  An entry with
    no year at all FAILS the build rather than printing a blank (the absence-blindness defect this
    family has recorded: Crossref's `issued: [[None]]` for a DOI whose venue states the year);
  * the venue is the container title, or `arXiv preprint arXiv:<id>` for an arXiv record;
  * the link is a RESOLVABLE URL built from the identifier (round 1, required change 3: every entry
    printed a bare `DOI: 10.…` string);
  * the title is passed through the all-caps fold (no record here needs it, but the rule is the house
    style's and is applied rather than assumed).

Usage:  python3 refs_build_display.py            rebuild artefacts/refs_display.json
        python3 refs_build_display.py --check    exit non-zero if the committed file differs from a
                                                 fresh build (no write) -- the read `reproduce.sh` takes
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = os.path.join(HERE, "artefacts", "refs_ordered.json")
DIFFS = os.path.join(HERE, "refs_differences.json")
OUT = os.path.join(HERE, "artefacts", "refs_display.json")

# Years the registries do not state, supplied BY DECLARATION with the evidence, never guessed.
YEAR_SUPPLY = {
    "viola2001cascade": (2001, "Crossref returns `issued: [[None]]` for 10.1109/CVPR.2001.990517 (read "
                               "2026-09-17); the venue string names `CVPR 2001` and the DOI itself carries "
                               "`CVPR.2001`"),
}

SMALL = ("Of", "The", "And", "For", "In", "On", "To", "With", "A", "An")


def initials(given):
    """'Joseph E.' -> 'J. E.' ; 'Herbert Alexander' -> 'H. A.' ; 'C.' -> 'C.'"""
    out = []
    for tok in re.split(r"[\s\-]+", given.strip()):
        tok = tok.strip(". ")
        if not tok:
            continue
        out.append(tok[0].upper() + ".")
    return " ".join(out)


def format_name(raw):
    """Normalise a name to `Family, I.` from either `Family, Given` or `Given Family`."""
    s = re.sub(r"\s+", " ", (raw or "").replace("\u00a0", " ")).strip().rstrip(".")
    if not s:
        return ""
    if "," in s:
        fam, giv = s.split(",", 1)
        fam, giv = fam.strip(), giv.strip()
    else:
        parts = s.split(" ")
        if len(parts) == 1:
            return parts[0]
        fam, giv = parts[-1], " ".join(parts[:-1])
    ini = initials(giv)
    return ("%s, %s" % (fam, ini)).strip().rstrip(",") if ini else fam


def title_case(t):
    """Fold an ALL-CAPS record title to title case; leave a mixed-case title alone (house style)."""
    letters = [c for c in t if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters):
        return t
    out = t.title()
    out = re.sub(r"\b(%s)\b" % "|".join(SMALL), lambda m: m.group(0).lower(), out)
    return out[0].upper() + out[1:] if out else out


def venue_of(r):
    if r.get("kind") == "arxiv":
        return "arXiv preprint arXiv:%s" % r["ident"]
    return r.get("venue") or ("doi:%s" % r["ident"])


def url_of(r):
    if r.get("kind") == "arxiv":
        return "https://arxiv.org/abs/%s" % r["ident"]
    return "https://doi.org/%s" % r["ident"]


def build(rows, diffs):
    """The whole display table, with the failures the build refuses to paper over."""
    supplied, out, missing = [], {}, []
    for r in rows:
        k = r["key"]
        year = r.get("year")
        if not year:
            if k in YEAR_SUPPLY:
                year, why = YEAR_SUPPLY[k]
                supplied.append((k, year, why))
            else:
                missing.append(k)
        rec = {
            "n": r["n"],
            "key": k,
            "authors": [a for a in (format_name(x) for x in (r.get("authors") or [])) if a],
            "year": str(year) if year else "",
            "title": title_case(r["title"].rstrip(".")),
            "venue": venue_of(r),
            "url": url_of(r),
            "difference": (diffs.get(k) or "").strip(),
        }
        out[k] = rec
    return out, supplied, missing


def main():
    check = "--check" in sys.argv
    rows = json.load(io.open(ORDER, encoding="utf-8"))
    diffs = json.load(io.open(DIFFS, encoding="utf-8"))
    out, supplied, missing = build(rows, diffs)
    if missing:
        print("BUILD FAILED: no year for %s and none declared in YEAR_SUPPLY" % missing)
        return 1
    nodiff = sorted([k for k, v in out.items() if not v["difference"]], key=lambda k: out[k]["n"])
    if nodiff:
        print("BUILD FAILED: %d entr(y|ies) carry no stated difference: %s" % (len(nodiff), nodiff))
        return 1
    if len(out) != len(rows):
        print("BUILD FAILED: %d records for %d ordered references" % (len(out), len(rows)))
        return 1
    text = json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True)
    if check:
        committed = io.open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        same = committed == text
        print("artefacts/refs_display.json matches a fresh build: %s" % same)
        print("  %d entries, every entry carrying a stated difference, %d declarative date(s)"
              % (len(out), len(supplied)))
        if not same:
            print("  the committed file differs: %d bytes committed, %d built"
                  % (len(committed.encode()), len(text.encode())))
        return 0 if same else 1
    io.open(OUT, "w", encoding="utf-8").write(text)
    print("wrote %s: %d entries" % (os.path.basename(OUT), len(out)))
    print("  every entry carries a stated difference: %d/%d" % (len(out) - len(nodiff), len(out)))
    print("  dates supplied by declaration: %d" % len(supplied))
    for k, y, why in supplied:
        print("    %s -> %s : %s" % (k, y, why))
    print("  longest author list: %d" % max(len(v["authors"]) for v in out.values()))
    print("  resolvable URLs: %d/%d" % (sum(1 for v in out.values() if v["url"].startswith("https://")), len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
