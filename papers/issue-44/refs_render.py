#!/usr/bin/env python3
"""Render issue #44's `## References` section in the JOURNAL's house style.

The section is GENERATED from `refs_display.json` (built by `refs_build_display.py`), so the form is
owned here and the committed section cannot be hand-edited past this file.

ENTRY STYLE -- the form `README.md` (the journal's) -> *Presentation requirements* -> *Formal References
section* states, and the form `papers/issue-38/refs_render.py` / `papers/issue-42/refs_render.py` already
render:

    [n] Authors (Year). Title. Venue or identifier. <resolvable URL>
        Difference: <the one-line stated difference that closes the entry>

  * Authors are `Family, I.`, joined with `; `; four or more are abbreviated to the first three followed
    by `et al.` (one period) -- and because this file writes the period itself, a doubled period cannot
    be emitted.
  * The year is in **parentheses**, after the author block (required change 4).
  * The title is plain text in title case; the record's `*…*` emphasis is not carried into the
    bibliography, which is the form every published list in this journal uses.
  * The link is a **resolvable URL** -- `https://doi.org/…` or `https://arxiv.org/abs/…` -- never a
    backticked identifier (required change 3: all 103 entries printed one).
  * The stated difference closes the entry on its own indented line (required change 2: 1 of 103
    carried one).

ENTRIES ARE SEPARATED BY A BLANK LINE. That is required change 1 and the defect the reader meets: with
the entry lines adjacent, consecutive entries are ONE paragraph to every CommonMark renderer, so the
boundaries vanish and an entry's trailing identifier is read as part of the next entry's sentence.
Measured on the published head: `refgate.py` read `103 entries, 102 of them not separated from the entry
above by a blank line` and GitHub's own renderer returned **1** paragraph for the 103 entries. The
acceptance read is that line returning `0 of 103 not separated` and the renderer returning **103**
paragraphs.

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
DISPLAY = os.path.join(HERE, "refs_display.json")
MS = os.path.join(HERE, "manuscript.md")
MAX_AUTHORS = 3          # four or more authors -> first three + `et al.`
WIDTH = 100
HDR = re.compile(r"^##\s*(?:\d+\.\s*)?References\s*$")


def load():
    disp = json.load(io.open(DISPLAY, encoding="utf-8"))
    return [disp[k] for k in sorted(disp, key=lambda k: disp[k]["n"])]


def author_string(authors):
    """`Family, I.`, joined with `; `; four or more collapsed to the first three and `et al.`

    The list's authors are a single `; `-separated string in the source, already in house form.
    """
    comps = [c.strip() for c in str(authors or "").split(";") if c.strip()]
    if len(comps) >= 4:
        return "; ".join(comps[:MAX_AUTHORS]) + "; et al."
    return "; ".join(comps)


def entry_block(rec):
    bits = ["[%d] " % rec["n"] + author_string(rec.get("authors"))
            + ((" (%s)." % rec["year"]) if rec.get("year") else "."),
            rec["title"].rstrip(".") + "."]
    if rec.get("venue"):
        bits.append(rec["venue"].rstrip(".") + ".")
    bits.append(rec["url"])
    out = textwrap.wrap(" ".join(bits), width=WIDTH, subsequent_indent="    ",
                        break_long_words=False, break_on_hyphens=False)
    out += textwrap.wrap("Difference: " + (rec.get("difference") or "").strip(), width=WIDTH,
                         initial_indent="    ", subsequent_indent="    ",
                         break_long_words=False, break_on_hyphens=False)
    return "\n".join(out)


def render():
    body = ["## References", ""]
    for i, rec in enumerate(load()):
        if i:
            body.append("")
        body.append(entry_block(rec))
    return "\n".join(body) + "\n"


def section_of(ms):
    lines = ms.split("\n")
    return [i for i, l in enumerate(lines) if HDR.match(l)], lines


def readings(sec):
    """The properties the round's required changes name, read off the section itself.

    `entries_without_url` is the defect read, not `a token that looks like an identifier`: an arXiv
    entry's venue field legitimately NAMES the identifier (`arXiv preprint arXiv:<id>`, the house
    order's "venue or identifier"), so counting those tokens would report the style as the defect.
    What required change 3 names is an entry that prints its identifier and NO resolvable link.
    """
    ents = re.findall(r"(?ms)^\[\d+\] .*?(?=\n\[\d+\] |\Z)", sec)
    # A phrase read (`arXiv preprint arXiv:<id>`) must be taken on the section with its line wrapping
    # removed, or an entry whose wrap falls between the two halves of the phrase is read as if the
    # phrase were absent -- the first run of this check reported 23 of 31 for exactly that reason.
    flat = re.sub(r"\s+", " ", sec)
    return {
        "entries": len(re.findall(r"(?m)^\[\d+\] ", sec)),
        "blank_lines": sum(1 for l in sec.split("\n") if not l.strip()),
        "stated_differences": len(re.findall(r"(?m)^\s*Difference: ", sec)),
        "resolvable_urls": len(re.findall(r"https://", sec)),
        "entries_without_url": sum(1 for e in ents if "https://" not in e),
        "venue_named_identifiers": len(re.findall(r"arXiv preprint arXiv:\d", flat)),
        "backticks": sec.count("`"),
        "doubled_periods": len(re.findall(r"\.\.", sec)),
    }


def check(ms):
    starts, lines = section_of(ms)
    if len(starts) != 1:
        print("ABORT: expected exactly one '## ... References' heading, found %d" % len(starts))
        return 1
    committed = "\n".join(lines[starts[0]:]).rstrip("\n")
    fresh = render().rstrip("\n")
    same = committed == fresh
    print("references section matches the renderer: %s" % same)
    r = readings(fresh)
    print("  %d entries, %d blank line(s), %d stated difference(s), %d resolvable URL(s)"
          % (r["entries"], r["blank_lines"], r["stated_differences"], r["resolvable_urls"]))
    print("  backticked tokens: %d | entries with no resolvable URL: %d | venue-named identifiers: %d"
          % (r["backticks"], r["entries_without_url"], r["venue_named_identifiers"]))
    print("  doubled periods: %d | heading %r" % (r["doubled_periods"], fresh.split("\n")[0]))
    if not same:
        cl = committed.split("\n")
        fl = fresh.split("\n")
        first = next((i for i, (a, b) in enumerate(zip(cl, fl)) if a != b), min(len(cl), len(fl)))
        print("  the committed section differs at line %d: %r vs %r"
              % (first + 1, cl[first][:70] if first < len(cl) else "", fl[first][:70] if first < len(fl) else ""))
    return 0 if same else 1


def main():
    ms = io.open(MS, encoding="utf-8").read()
    if "--check" in sys.argv:
        return check(ms)
    starts, lines = section_of(ms)
    if len(starts) != 1:
        print("ABORT: expected exactly one '## ... References' heading, found %d" % len(starts))
        return 1
    io.open(MS, "w", encoding="utf-8").write(
        "\n".join(lines[:starts[0]]).rstrip("\n") + "\n\n" + render())
    print("rendered %d entries into %s" % (len(load()), os.path.basename(MS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
