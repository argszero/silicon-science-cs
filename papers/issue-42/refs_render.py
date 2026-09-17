#!/usr/bin/env python3
"""Render issue #42's `## References` section in the JOURNAL's house style.

The section is GENERATED from `artefacts/refs_display.json` (built by `refs_build_display.py`), so the
form is owned here and the committed section cannot be hand-edited past this file.

ENTRY STYLE -- the form `README.md` (the journal's) -> *Presentation requirements* -> *Formal References
section* states, and the form `papers/issue-38/refs_render.py` already renders (accepted twice):

    [n] Authors (Year). Title. Venue or identifier. <resolvable URL>
        Difference: <the one-line stated difference that closes the entry>

  * Authors are `Family, I.`, joined with `; `; **four or more are abbreviated to the first three
    followed by `et al.`** (one period) -- the round-1 decision's required change 6, and the doubled
    period it named (`et al..`) cannot be emitted because this file writes the period itself.
  * The year is in **parentheses**, after the author block. Where the registry states none it is
    supplied by declaration in `refs_build_display.py` (`viola2001cascade`), with the evidence printed
    by the build.
  * The title is in **title case**: an all-caps record title is folded; a mixed-case title prints as
    the record states it.
  * The link is a **resolvable URL** (`https://doi.org/…`, `https://arxiv.org/abs/…`), never a bare
    identifier.
  * The stated difference closes the entry on its own indented line. It is AUTHORED data
    (`refs_differences.json`), one line per entry; the build refuses to write an entry without one.

ENTRIES ARE SEPARATED BY A BLANK LINE. This is required change 1 and the defect the reader sees: with
entry lines adjacent, consecutive entries are ONE paragraph to every CommonMark renderer, so the
boundaries vanish and an entry's trailing URL is read as part of the next entry's sentence. Measured on
the published head: `refgate.py` read `117 entries, 116 of them not separated from the entry above by a
blank line` and GitHub's own renderer returned **1** paragraph for the 117 entries. The acceptance read
is that line returning `0 of 117 not separated` and the renderer returning **117** paragraphs.

Every entry is wrapped at 100 columns with a 4-space hanging indent, so continuation lines never begin
with an entry marker and the citation gate's entry parse stays exact.

Usage:
    python3 refs_render.py            rewrite the section in manuscript.md
    python3 refs_render.py --check    exit non-zero if the committed section differs (no write)
"""
import io
import json
import os
import re
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
DISPLAY = os.path.join(HERE, "artefacts", "refs_display.json")
MS = os.path.join(HERE, "manuscript.md")
MAX_AUTHORS = 3          # four or more authors -> first three + `et al.`
WIDTH = 100
HDR = re.compile(r"^##\s*(?:\d+\.\s*)?References\s*$")


def load():
    disp = json.load(io.open(DISPLAY, encoding="utf-8"))
    return [disp[k] for k in sorted(disp, key=lambda k: disp[k]["n"])]


def author_string(authors):
    """`Family, I.`, joined with `; `; four or more collapsed to the first three and `et al.`"""
    if not authors:
        return ""
    if len(authors) >= 4:
        return "; ".join(authors[:MAX_AUTHORS]) + "; et al."
    return "; ".join(authors)


def entry_block(rec):
    """One entry: the citation line (wrapped at WIDTH) then its indented stated difference."""
    au = author_string(rec.get("authors") or [])
    year = rec.get("year") or ""
    head = au if au else "Author not established"
    head += (" (%s)." % year) if year else "."
    bits = [("[%d] " % rec["n"]) + head, rec["title"].rstrip(".") + "."]
    venue = rec.get("venue") or ""
    if venue:
        bits.append(venue.rstrip(".") + ".")
    bits.append(rec["url"])
    out = textwrap.wrap(" ".join(bits), width=WIDTH, subsequent_indent="    ",
                        break_long_words=False, break_on_hyphens=False)
    diff = "Difference: " + (rec.get("difference") or "").strip()
    out += textwrap.wrap(diff, width=WIDTH, initial_indent="    ", subsequent_indent="    ",
                         break_long_words=False, break_on_hyphens=False)
    return "\n".join(out)


def render():
    """The whole section, INCLUDING its heading line, with a blank line between entries."""
    body = ["## References", ""]
    for i, rec in enumerate(load()):
        if i:
            body.append("")
        body.append(entry_block(rec))
    return "\n".join(body) + "\n"


def check(ms):
    """Read the committed section and report whether it is what this file renders."""
    lines = ms.split("\n")
    starts = [i for i, l in enumerate(lines) if HDR.match(l)]
    if len(starts) != 1:
        print("ABORT: expected exactly one '## ... References' heading, found %d" % len(starts))
        return 1
    committed = "\n".join(lines[starts[0]:]).rstrip("\n")
    fresh = render().rstrip("\n")
    same = committed == fresh
    print("references section matches the renderer: %s" % same)
    sec = fresh
    ents = len(re.findall(r"(?m)^\[\d+\] ", sec))
    blanks = sum(1 for l in sec.split("\n") if not l.strip())
    diffs = len(re.findall(r"Difference: ", sec))
    bare = len(re.findall(r"(?m)\bDOI: 10\.", sec))
    doubled = len(re.findall(r"et al\.\.", sec))
    urls = len(re.findall(r"https://", sec))
    print("  %d entries, %d blank line(s), %d stated difference(s), %d resolvable URL(s)"
          % (ents, blanks, diffs, urls))
    print("  bare `DOI: ` identifiers: %d | doubled `et al..`: %d | heading %r"
          % (bare, doubled, sec.split("\n")[0]))
    return 0 if same else 1


def main():
    ms = io.open(MS, encoding="utf-8").read()
    if "--check" in sys.argv:
        return check(ms)
    lines = ms.split("\n")
    starts = [i for i, l in enumerate(lines) if HDR.match(l)]
    if len(starts) != 1:
        print("ABORT: expected exactly one '## ... References' heading, found %d" % len(starts))
        return 1
    head_at = starts[0]
    new_ms = "\n".join(lines[:head_at]).rstrip("\n") + "\n\n" + render()
    io.open(MS, "w", encoding="utf-8").write(new_ms)
    ents = len(re.findall(r"(?m)^\[\d+\] ", render()))
    print("rendered %d entries into %s" % (ents, os.path.basename(MS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
