#!/usr/bin/env python3
"""Render issue #38's `## References` section in the package's one human-readable style.

The manuscript's `## References` section is the object of the presentation requirement, so it is
rendered from the two committed data files rather than typed:

    references.json      -> title, url, and the per-entry *stated difference* (never rendered before)
    refs_display.json    -> authors, year, venue (built by refs_build_display.py)

ENTRY STYLE (stated once; the same style is written into README.md next to this script):

    [N] <Authors> (<Year>). <Title>. <Venue or identifier>. <Link>
        Difference: <the one-line stated difference that closes the entry>

  * Authors are "Family, I. I.", joined with "; ". **Up to six are listed; a longer list is
    truncated to the first six followed by "et al."** (16 entries have more than six authors).
  * Year is the source's publication year; for an arXiv preprint with no stated publication date it
    is the arXiv submission year. The literal placeholders `n.d.` and `None.` are never emitted.
  * Venue is the container title (Crossref) or `arXiv preprint arXiv:<id>`.
  * The link is the entry's own URL (arXiv abstract page or DOI).
  * The stated difference is printed on its own indented line, so every entry says what it is doing
    in this manuscript and not just what it is.

Every entry is wrapped at 100 columns with a 4-space hanging indent. Continuation lines therefore
never begin with an entry marker, which keeps the citation gate's entry parse exact.

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
MAX_AUTHORS = 6
WIDTH = 100
HDR = re.compile(r'^##\s*\d*\.?\s*References\s*$')


def load():
    refs = json.load(io.open(os.path.join(HERE, "references.json"), encoding="utf-8"))["entries"]
    disp = json.load(io.open(os.path.join(HERE, "refs_display.json"), encoding="utf-8"))
    return refs, disp


def author_string(authors):
    if not authors:
        return ""
    if len(authors) > MAX_AUTHORS:
        return "; ".join(authors[:MAX_AUTHORS]) + "; et al."
    return "; ".join(authors)


def entry_line(e, d):
    au = author_string(d.get("authors") or [])
    year = d.get("year") or ""
    head = ""
    if au:
        head = au
    else:
        # No author could be established from any reachable record for this entry. Say so in the
        # entry rather than guessing, and let the section note repeat it.
        head = "Author not established from the record"
    if year:
        head += (" (%s)." % year) if au else (" [%s]." % year)
    else:
        head += "."
    venue = d.get("venue") or ""
    bits = [("[%d] " % e["key"]) + head, e["title"] + "."]
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
    note = ("One entry, **[51]**, is printed without an author: no reachable record carries one for "
            "its DOI (Crossref has none, OpenAlex reports no authorships, and the publisher's landing "
            "page refuses automated access). The obstacle is stated on the issue thread rather than "
            "filled in by guesswork.")
    body = ["## 9. References", ""]
    body += textwrap.wrap(note, width=WIDTH, break_long_words=False, break_on_hyphens=False)
    body += [""]
    for e in refs:
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
    new_head = lines[:head_at]
    new_ms = "\n".join(new_head).rstrip("\n") + "\n\n" + render()
    old_sec = "\n".join(lines[head_at:])
    if check:
        same = old_sec.rstrip("\n") == render().rstrip("\n")
        print("references section matches the renderer: %s" % same)
        return 0 if same else 1
    io.open(MS, "w", encoding="utf-8").write(new_ms)
    ents = sum(1 for l in render().split("\n") if re.match(r'^\[\d+\]', l))
    print("rendered %d entries into %s" % (ents, os.path.basename(MS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
