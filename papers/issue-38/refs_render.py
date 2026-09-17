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
    A record that states an author in **ALL CAPITALS is folded, the way its title is** (`[15]` ->
    `Gale, D.; Shapley, L.`, `[20]` -> `Smith, R. G.`); a mixed-case author field is printed as the
    record states it.  The fold is the title's fold **minus its small-word rule**: that rule is written
    for title phrases, and over an author component it would lowercase an initial
    (`SMITH, A. B.` -> `Smith, a. B.`), which is the one thing an author component must not lose.
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

THE AUTHOR COMPONENT'S CASE IS PART OF THE SAME STYLE.  The round-3 decision found it by reading the 125
entries against `README.md`'s claim that one style is applied to all of them: **3 components over 2
records** (`[15]` twice, `[20]` once) printed the record's capitals where the other components print
`Family, I.`, and across the journal's four other published bibliographies **0 of 491** entries carry
one.  The fold is applied to the component on the way to the page, so the data files keep the casing the
registry returned (`refs_display.json` is the record as read) and every rendered component carries the
same form.  Acceptance read: `author case: 0` over the 125 entries, printed by `--check` together with
the liveness line that says how many components the records state in capitals.  That line is a FACT and
not a failure: an artefact in which nothing needed folding is correct.  What must fail when the fold has
nothing to fold is the round's CONTROL, so it is `verify_correction_r3.py` -- not `--check` -- that
fails when the control cannot be derived.  `verify_correction_r3.py` takes the read with the control
that removes the fold.

ONE ENTRY'S TEXT CARRIED THE REGISTRY'S XML ESCAPE FOR A NAME, and the same read found it: `[95]`'s
author component printed `O&#39;Brien, L.` because the arXiv metadata ships `&#39;` where the name has
an apostrophe.  Measured: 1 of the 125 entries' text carries such an escape, and CommonMark **renders
both forms identically** (`gh api -X POST /markdown` returns `<p>X O'Brien</p>` for each), so this is a
repair to the TEXT -- the object `refgate.py`, a grep, a diff and every other text reader sees -- and
not a claim that the page was broken.  The record files keep what the registry returned; the renderer
decodes, because printing the record's name is what the entry style asks for.

Every entry is wrapped at 100 columns with a 4-space hanging indent, so continuation lines never begin
with an entry marker and the citation gate's entry parse stays exact.

Usage:
    python3 refs_render.py            rewrite the section in manuscript.md
    python3 refs_render.py --check    exit non-zero if the committed section differs (no write)
"""
import html
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


def author_case(a):
    """Fold an ALL-CAPS record author component the way this file folds an ALL-CAPS title.

    Deliberately NOT `title_case`: that function's small-word rule is written for title phrases, and
    over an author component it lowercases an initial (`SMITH, A. B.` -> `Smith, a. B.`, where
    `.title()` alone gives `Smith, A. B.`).  A component whose letters are all upper-case is folded;
    anything else is printed as the record states it, because re-casing a name the registry wrote in
    mixed case would be an edit to the record rather than a rendering of it.
    """
    letters = [c for c in a if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters):
        return a
    return a.title()


def record_text(s):
    """Decode the XML/HTML character references the registries ship inside their metadata.

    `refs_display.json` is the record AS READ, so the escape stays there; the page wants the name.
    Measured at round 3: exactly one of the 125 entries' text carried one (`[95]`, `O&#39;Brien, L.`
    from the arXiv `citation_author` meta tag), and CommonMark renders the escaped and decoded forms
    identically -- so this is a repair to the text, not to the rendered page, and the read that
    watches it is `--check`'s `record text:` line.
    """
    return html.unescape(s) if s else s


def author_string(authors):
    """`Family, I.`, joined with `; `; four or more collapsed to the first three and `et al.`"""
    if not authors:
        return ""
    names = [author_case(record_text(a)) for a in authors]
    if len(names) >= 4:
        return "; ".join(names[:MAX_AUTHORS]) + "; et al."
    return "; ".join(names)


def caps_author_components(sec):
    """The ALL-CAPS author components of a RENDERED section, read from the text a reader sees.

    An entry's author block runs from `[n] ` to its year in parentheses -- an author component carries
    no parentheses -- and components are separated by `; `, which is also why `et al.` is a component of
    its own and is correctly not in capitals.  Whitespace is collapsed first, so a block the wrapper
    broke across lines is read as the one block it is.
    """
    out = []
    for blk in re.split(r"(?m)^(?=\[\d+\] )", sec.strip("\n")):
        m = re.match(r"^\[(\d+)\] (.*?) \((?:19|20)\d\d\)\.", re.sub(r"\s+", " ", blk).strip())
        if not m:
            continue
        # split on `; ` and not on `;`: a character reference ENDS in a semicolon (`&#39;`), and
        # splitting on the bare semicolon cuts a component in half -- which is how this read first
        # reported `[95] O&#39` as an ALL-CAPS component, a false positive.
        for comp in m.group(2).split("; "):
            comp = comp.strip()
            letters = [c for c in comp if c.isalpha()]
            if letters and all(c.isupper() for c in letters):
                out.append((m.group(1), comp))
    return out


ENT = re.compile(r"&#?[0-9A-Za-z]+;")


def escaped_entities(text):
    """The character references left in TEXT -- the object every text reader sees."""
    return ENT.findall(text or "")


def source_entities(disp, refs):
    """The escapes the RECORDS state in the fields this renderer prints -- the liveness fact."""
    out = []
    for k, rec in disp.items():
        for a in (rec.get("authors") or []):
            if escaped_entities(a):
                out.append((k, a))
        if escaped_entities(rec.get("venue") or ""):
            out.append((k, rec["venue"]))
    for e in refs:
        if escaped_entities(e.get("title") or ""):
            out.append((str(e["key"]), e["title"]))
    out.sort(key=lambda kv: int(kv[0]))
    return out


def source_caps(disp):
    """The author components the RECORD states in capitals -- the liveness precondition of that read.

    With none of these, `caps_author_components` returns 0 over the section whatever the renderer did,
    so the acceptance read would be satisfied by there being nothing to fold.
    """
    out = []
    for k, rec in disp.items():
        for a in (rec.get("authors") or []):
            letters = [c for c in a if c.isalpha()]
            if letters and all(c.isupper() for c in letters):
                out.append((k, a))
    out.sort(key=lambda kv: int(kv[0]))
    return out


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
        sec = render()
        same = old_sec.rstrip("\n") == sec.rstrip("\n")
        print("references section matches the renderer: %s" % same)
        refs, disp = load()
        ents = len(re.findall(r"(?m)^\[\d+\] ", sec))
        blanks = sum(1 for l in sec.split("\n") if not l.strip())
        print("  %d entries, %d blank line(s) in the section, heading %r"
              % (ents, blanks, sec.split("\n")[0]))
        # The author component's case is read on the SECTION, the object the reader's page comes from,
        # and not on the renderer's own behaviour: a section regenerated by a renderer that lost the
        # fold agrees with that renderer, so the comparison above cannot see it and this read can.
        caps = caps_author_components(sec)
        src = source_caps(disp)
        print("  author case: %d ALL-CAPS author component(s) over %d entries%s"
              % (len(caps), ents, "" if not caps else " -- " + "; ".join("[%s] %s" % c for c in caps)))
        print("  liveness: %d component(s) in %d record(s) are stated in capitals by the record read"
              % (len(src), len(set(k for k, _ in src))))
        esc = escaped_entities(sec)
        srce = source_entities(disp, refs)
        print("  record text: %d escaped character reference(s) over %d entries%s"
              % (len(esc), ents, "" if not esc else " -- " + ", ".join(sorted(set(esc)))))
        print("  liveness: %d escaped reference(s) in %d record(s) are stated by the record read"
              % (len(srce), len(set(k for k, _ in srce))))
        # the two liveness lines are FACTS, not failures: an artefact in which nothing needed folding or
        # decoding is correct.  What must fail when a rule has nothing to exercise is the round's
        # control, which verify_correction_r3.py derives and refuses to skip.
        return 0 if (same and not caps and not esc) else 1
    new_ms = "\n".join(lines[:head_at]).rstrip("\n") + "\n\n" + render()
    io.open(MS, "w", encoding="utf-8").write(new_ms)
    ents = sum(1 for l in render().split("\n") if re.match(r'^\[\d+\]', l))
    print("rendered %d entries into %s" % (ents, os.path.basename(MS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
