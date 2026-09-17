#!/usr/bin/env python3
"""Render issue #38's `## References` section in the JOURNAL's house style.

The manuscript's `## References` section is the object of the presentation requirement, so it is
rendered from the two committed data files rather than typed:

    references.json      -> title, url, and the per-entry *stated difference*
    refs_display.json    -> authors, year, venue (built by refs_build_display.py)

ENTRY STYLE (stated once; the same style is written into README.md next to this script, and it is the
form `README.md` -> *Presentation requirements* -> *Formal References section* names):

    [n] Authors (Year). Title. Venue or identifier. <resolvable URL>
        Difference: <the one-line stated difference that closes the entry>

  * Authors are `Family, I.`, joined with `; `. **Four or more are abbreviated to the first three
    followed by `et al.`** (one period), which is the rule the house style states in as many words.
  * The year is in **parentheses**, after the author block; for an arXiv preprint with no stated
    publication date it is the arXiv submission year. The literal placeholders `n.d.` and `None.` are
    never emitted.
  * The title is in **title case**: an all-caps record title is folded, so `[10]` and `[15]` print as
    *Counterspeculation, Auctions, and Competitive Sealed Tenders* and *College Admissions and the
    Stability of Marriage* rather than in the record's capitals.
  * The venue is the container title (Crossref) or `arXiv preprint arXiv:<id>`.
  * The link is printed as a **resolvable URL** (arXiv abstract page or DOI), never as a bare
    identifier and never inside backticks.
  * The stated difference closes the entry on its own line, so every entry says what it is doing in
    this manuscript and not just what it is.
  * An entry whose record carries **no author** records the absence by naming the records that were
    read (`Author not established on Crossref/OpenAlex for this DOI`), with the same line carried in
    `reference-check.md`; the author position is never left silently empty and never filled by
    guesswork.

ENTRIES ARE SEPARATED BY A BLANK LINE.  This is the half the first correction round did not reach:
each entry was already on a line of its own, but with no blank line between entries consecutive entry
lines are ONE paragraph to every CommonMark renderer, so the boundaries vanish and a trailing URL is
read as part of the next entry's sentence.  Measured on the published head (2026-09-17, the round-2
decision's own instrument): `refgate.py`'s `block form:` line read `125 entries, 124 of them not
separated from the entry above by a blank line`, and GitHub's own renderer returned **2** paragraphs
for the 125 entries.  The acceptance read is that line returning `0 of 125 not separated` and the
renderer returning **125** paragraphs, and `refs_render.py --check` is what re-takes it.

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
MS = os.path.join(HERE, "manuscript.md")
MAX_AUTHORS = 3          # four or more authors -> first three + `et al.`
WIDTH = 100
# The heading this file EMITS is the unnumbered `## References` the house style names.  The numbered
# form is still accepted when reading, because the renderer rewrites a file whose heading it must
# first find, and a rewrite that cannot locate its own section would append a second one.
HDR = re.compile(r'^##\s*(?:\d+\.\s*)?References\s*$')

# Words that stay lowercase inside a title-cased phrase (never the first word).
SMALL = ("Of", "The", "And", "For", "In", "On", "To", "With", "A", "An")


def load():
    refs = json.load(io.open(os.path.join(HERE, "references.json"), encoding="utf-8"))["entries"]
    disp = json.load(io.open(os.path.join(HERE, "refs_display.json"), encoding="utf-8"))
    return refs, disp


def title_case(t):
    """Fold an ALL-CAPS record title to title case; leave a mixed-case title alone.

    The house style asks for the title in title case, and 2 of the 125 records return it in capitals
    (Crossref keeps the publisher's own casing).  A record whose letters are ALL upper-case is folded;
    anything else is printed as the record states it, because re-casing a title the publisher wrote in
    mixed case would be an edit to the record rather than a rendering of it.
    """
    letters = [c for c in t if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters):
        return t
    out = t.title()
    out = re.sub(r"\b(%s)\b" % "|".join(SMALL), lambda m: m.group(0).lower(), out)
    return out[0].upper() + out[1:] if out else out


def author_string(authors):
    """`Family, I.`, joined with `; `; four or more collapsed to the first three and `et al.`"""
    if not authors:
        return ""
    if len(authors) >= 4:
        return "; ".join(authors[:MAX_AUTHORS]) + "; et al."
    return "; ".join(authors)


def entry_line(e, d):
    au = author_string(d.get("authors") or [])
    year = d.get("year") or ""
    if au:
        head = au
    else:
        # No author could be established from any reachable record for this entry. The exception the
        # house style names wants the RECORD named, so a reviewer can check the claim against the
        # registry the entry points at; the same line is carried in reference-check.md.
        head = "Author not established on Crossref/OpenAlex for this DOI"
    head += (" (%s)." % year) if year else "."
    venue = d.get("venue") or ""
    bits = [("[%d] " % e["key"]) + head, title_case(e["title"]) + "."]
    if venue:
        bits.append(venue + ".")
    bits.append(e["url"])
    first = " ".join(bits)
    diff = "Difference: " + (e.get("difference") or "").strip()
    out = textwrap.wrap(first, width=WIDTH, subsequent_indent="    ",
                        break_long_words=False, break_on_hyphens=False)
    out += textwrap.wrap(diff, width=WIDTH, initial_indent="    ", subsequent_indent="    ",
                         break_long_words=False, break_on_hyphens=False)
    return "\n".join(out)


def render():
    refs, disp = load()
    body = ["## References", ""]
    for i, e in enumerate(refs):
        if i:
            body.append("")          # the blank line that makes each entry its own paragraph
        body.append(entry_line(e, disp[str(e["key"])]))
    return "\n".join(body) + "\n"


def main():
    check = "--check" in sys.argv
    ms = io.open(MS, encoding="utf-8").read()
    lines = ms.split("\n")
    starts = [i for i, l in enumerate(lines) if HDR.match(l)]
    if len(starts) != 1:
        print("ABORT: expected exactly one '## ... References' heading, found %d" % len(starts))
        return 1
    head_at = starts[0]
    old_sec = "\n".join(lines[head_at:])
    if check:
        same = old_sec.rstrip("\n") == render().rstrip("\n")
        print("references section matches the renderer: %s" % same)
        if same:
            sec = render()
            ents = len(re.findall(r"(?m)^\[\d+\] ", sec))
            blanks = sum(1 for l in sec.split("\n") if not l.strip())
            print("  %d entries, %d blank line(s) in the section, heading %r"
                  % (ents, blanks, sec.split("\n")[0]))
        return 0 if same else 1
    new_ms = "\n".join(lines[:head_at]).rstrip("\n") + "\n\n" + render()
    io.open(MS, "w", encoding="utf-8").write(new_ms)
    ents = sum(1 for l in render().split("\n") if re.match(r'^\[\d+\]', l))
    print("rendered %d entries into %s" % (ents, os.path.basename(MS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
