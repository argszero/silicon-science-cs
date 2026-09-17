#!/usr/bin/env python3
"""Build issue #44's display metadata -- `refs_display.json`.

The manuscript's `## References` section is GENERATED; `refs_render.py` owns its FORM and this file
owns its DATA.  The inputs are both committed and both are checks of their own:

    references.md            [@key] Authors. *Title*. Venue, Year. `identifier`
                             -- written by `verify_refs.py` from the records Crossref / arXiv
                             returned; one line per verified key.
    refs_differences.json    [@key] -> the one-line stated difference, AUTHORED per entry
                             (correction round 2, required change 2: 1 of 103 carried one).
    manuscript_part1..3.md   the BODY, read only for the order the keys are first cited in -- the
                             order `assemble.py` numbers them in, so the printed list and the running
                             text carry one numbering.

From those this build produces, per entry:

  * the link as a **RESOLVABLE URL** -- `https://doi.org/<doi>` for a DOI,
    `https://arxiv.org/abs/<id>` for an arXiv identifier (required change 3: all 103 entries printed
    their identifier inside backticks and no URL);
  * the year as a string, printed **in parentheses after the author block** by the renderer
    (required change 4: all 103 printed it bare, before the venue);
  * the title with the record's `*…*` emphasis removed and, for an all-caps record title, folded to
    title case -- the house style asks for the title in title case as plain text;
  * the venue, or `arXiv preprint arXiv:<id>` for an arXiv record;
  * the authors unchanged: this list already prints `Family, I.` and the decision says the author
    component is right on the entries checked.

It REFUSES to build an entry that lacks its stated difference, refuses to write the file if the entry
count does not match the cited keys, and refuses if the reference set and the cited set differ (an
uncited entry is padding, and a cited key with no entry is a dangling citation) -- so the gap round 2
closes cannot come back silently.

Usage:
    python3 refs_build_display.py            rebuild refs_display.json
    python3 refs_build_display.py --check    exit non-zero if the committed file differs (no write)
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "references.md")
DIFFS = os.path.join(HERE, "refs_differences.json")
OUT = os.path.join(HERE, "refs_display.json")
PARTS = ["manuscript_part1.md", "manuscript_part2.md", "manuscript_part3.md"]

CITE = re.compile(r"\[@([A-Za-z0-9_.:-]+)\]")
LINE = re.compile(r"^\[@([A-Za-z0-9_]+)\]\s+(.*)$")
IDENT = re.compile(r"`([^`]+)`\s*$")
YEAR = re.compile(r",\s*(\d{4}|n\.d\.)\s*$")
SMALL = ("Of", "The", "And", "For", "In", "On", "To", "With", "A", "An")


def title_case(t):
    """Fold an ALL-CAPS record title to title case; leave a mixed-case title alone (house style)."""
    letters = [c for c in t if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters):
        return t
    out = t.title()
    out = re.sub(r"\b(%s)\b" % "|".join(SMALL), lambda m: m.group(0).lower(), out)
    return out[0].upper() + out[1:] if out else out


def citation_order():
    """The keys in order of first citation in the BODY -- the order `assemble.py` numbers them in."""
    order = []
    for part in PARTS:
        path = os.path.join(HERE, part)
        if not os.path.exists(path):
            raise SystemExit("BUILD FAILED: %s is missing, so the citation order is unknown" % part)
        for key in CITE.findall(io.open(path, encoding="utf-8").read()):
            if key not in order:
                order.append(key)
    return order


def parse(path):
    """`references.md` -> the records, with the identifier split out of the entry line."""
    rows = {}
    for raw in io.open(path, encoding="utf-8").read().split("\n"):
        if not raw.startswith("[@"):
            continue
        m = LINE.match(raw)
        if not m:
            raise SystemExit("BUILD FAILED: unparsable reference line: %r" % raw[:90])
        key, rest = m.group(1), m.group(2).strip()
        mi = IDENT.search(rest)
        if not mi:
            raise SystemExit("BUILD FAILED: entry [@%s] carries no backticked identifier" % key)
        ident = mi.group(1).strip()
        # An arXiv identifier is stored WITH its `arXiv:` prefix and a DOI without one, so the
        # prefix is split off here: kept, the URL would read `https://arxiv.org/abs/arXiv:2609.12582`
        # and the venue `arXiv preprint arXiv:arXiv:2609.12582`.
        is_arxiv = ident.lower().startswith("arxiv:")
        if is_arxiv:
            ident = ident[6:].strip()
        rest = rest[:mi.start()].strip()
        if rest.endswith("."):
            rest = rest[:-1]
        stars = [j for j, c in enumerate(rest) if c == "*"]
        if len(stars) != 2:
            raise SystemExit("BUILD FAILED: entry [@%s] does not carry exactly one *title* span" % key)
        # The author component is printed as the record states it, and the renderer appends
        # ` (Year).` -- so it must END in the period this list already prints after the initials
        # (`Wald, A.`), or the printed form would read `Wald, A (1945).`
        authors = rest[:stars[0]].strip().rstrip(".").strip() + "."
        title = rest[stars[0] + 1:stars[1]].strip()
        tail = rest[stars[1] + 1:].strip().lstrip(".").strip()
        ym = YEAR.search(tail)
        if not ym:
            raise SystemExit("BUILD FAILED: entry [@%s] carries no readable year" % key)
        rows[key] = {"key": key, "authors": authors, "title": title,
                     "venue": tail[:ym.start()].strip(), "year": ym.group(1),
                     "ident": ident, "is_arxiv": is_arxiv}
    return rows


def url_of(r):
    if r["is_arxiv"]:
        return "https://arxiv.org/abs/%s" % r["ident"]
    return "https://doi.org/%s" % r["ident"]


def venue_of(r):
    """The venue, or the identifier where the record's container IS the preprint server."""
    if r["is_arxiv"] and (not r["venue"] or r["venue"] == "arXiv preprint"):
        return "arXiv preprint arXiv:%s" % r["ident"]
    return r["venue"]


def build(rows, order, diffs):
    out, nodiff = {}, []
    for i, key in enumerate(order, 1):
        r = rows[key]
        d = (diffs.get(key) or "").strip()
        if not d:
            nodiff.append(key)
        out[key] = {"n": i, "key": key, "authors": r["authors"], "year": r["year"],
                    "title": title_case(r["title"]), "venue": venue_of(r),
                    "url": url_of(r), "difference": d}
    return out, nodiff


def main():
    check = "--check" in sys.argv
    rows = parse(SRC)
    order = citation_order()
    diffs = json.load(io.open(DIFFS, encoding="utf-8"))
    if set(order) != set(rows):
        print("BUILD FAILED: cited but no reference entry: %s ; entry never cited: %s"
              % (sorted(set(order) - set(rows))[:5], sorted(set(rows) - set(order))[:5]))
        return 1
    out, nodiff = build(rows, order, diffs)
    if nodiff:
        print("BUILD FAILED: %d entr(y|ies) carry no stated difference: %s" % (len(nodiff), nodiff[:8]))
        return 1
    if len(out) != len(order):
        print("BUILD FAILED: %d display records for %d cited keys" % (len(out), len(order)))
        return 1
    text = json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True)
    urls = sum(1 for v in out.values() if v["url"].startswith("https://"))
    folded = sum(1 for k, v in out.items() if v["title"] != rows[k]["title"])
    if check:
        committed = io.open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        same = committed == text
        print("refs_display.json matches a fresh build: %s" % same)
        print("  %d entries, %d carrying a stated difference, %d resolvable URL(s), %d title(s) folded"
              % (len(out), sum(1 for v in out.values() if v["difference"]), urls, folded))
        if not same:
            print("  the committed file differs: %d bytes committed, %d built"
                  % (len(committed.encode()), len(text.encode())))
        return 0 if same else 1
    io.open(OUT, "w", encoding="utf-8").write(text)
    print("wrote %s: %d entries, citation order taken from the body" % (os.path.basename(OUT), len(out)))
    print("  entries carrying a stated difference: %d/%d" % (len(out) - len(nodiff), len(out)))
    print("  resolvable URLs: %d/%d ; titles folded from capitals: %d" % (urls, len(out), folded))
    print("  arXiv records: %d (their venue prints the identifier, their link the abstract page)"
          % sum(1 for v in out.values() if v["url"].startswith("https://arxiv.org/abs/")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
