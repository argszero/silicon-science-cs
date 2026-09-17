#!/usr/bin/env python3
"""refgate — reference-section gate for SILICON SCIENCE manuscripts.

Checks the citation-integrity clause (README quality-bar item 11 and the
*Presentation requirements*): a formal `## References` section, numbered,
>= THRESHOLD entries, and in-text coverage (bibliography entries never cited
in the body are padding and do not count toward the total).

Why this is a tool rather than a paragraph of policy: a bibliography of >= 100
entries cannot be coverage-checked by hand, and a naive grep silently fails.
The manuscripts this journal has published use TWO numbering styles (`[1]` and
`1.`), sometimes a mix between bibliography and body, sometimes a wrapped entry
whose marker ends the line, and sometimes a numbered heading (`## 7 References`).

Under a naive `[n]`-marker count, three previously published manuscripts
(#33, #36, #91) report 0% coverage although they are correctly cited inline by
name — which is why the citation gate names an explicit in-text key (quality-bar
item 11, *Citation mechanics*) and why this checker reports entries with no key
rather than guessing.

Window. A reading owes the region it read and the forms it admits, so both are
printed with the reading. The region is the **LAST accepted heading to the end of
the file** — an appendix (or any numbered list) placed after the bibliography is
read as entries, and its markers can raise the duplicate-number warning. The
accepted forms are an **ATX heading** (`#`..`######`, optional section number,
case-insensitive, trailing whitespace tolerated) for the section, an **entry
marker** `[12]`, `12.` or `12)` at the start of a line, optionally indented
(1-3 digits — a 4-digit run at line start is a YEAR on a wrapped URL or title
line) for the entries, and an **in-text key** `[12]`, `[12,14]` or `[12-14]`
(hyphen or en dash) for the body citations, plus one **layout** form that none of
the three can see: an entry set is not a paragraph, so each entry begins on a line
of its own and the entries are separated from one another by a blank line. The
checker counts the entries and the entries that are **not separated from the entry
above by a blank line** — consecutive entry lines are ONE paragraph to any
CommonMark renderer (GitHub's preview included), so a list with none separated
prints as a single block whose entry boundaries are invisible to a reader. That
count is printed as the advisory `block form:` line; it is the instrument the
rendering requirement in quality-bar item 11 is read by, and like every advisory
line here it does not move the verdict. **It differs from the other advisory lines
in one respect, and the difference is what this paragraph is here to state: it is
a COUNT and it is printed in every run, `0 of them not separated` included** — a
verdict's name never clears it and no absence of it can be read as a pass. So it
cannot be a member of a "must not appear" list of markers (`--selftest`'s CLEAN
tuple, which names the marker strings alone) and it is asserted beside that tuple
as the layout read's **clean form**; a fixture whose entries are not separated
fails the control with the missing line named, which is what keeps the control's
set as wide as the lines this checker prints.

A second count is printed the same way, for the **entry component** instead of the
list's layout: `author form:` reads whether the author component is printed in a
form the house style **admits** — `Family, I.`, or, for a work whose record gives
one author token and no more, that token alone (`Student.`) — a family token printed
ALL-CAPS is the form a registry's stored field has, and a character reference
(`&#39;`, `&amp;`) is the form an undecoded field has. Its window is narrower than the
entry set and is printed with the counts (`window/entries`), because an entry whose
author component is printed in **neither** form is outside it and a zero over an
empty window is not a passing read. Like the layout
count, it is an advisory that does not move the verdict, and its clean form is
asserted beside the layout read's for every case that asserts the marker tuple — so
a fixture whose family token is printed ALL-CAPS fails the control with the missing
line named, exactly as a collapsed one does. The two counts differ in what they owe
the reader: the layout count is printed in every run because every entry set has a
layout, while the component count owes its **window** — the entries whose author
component is printed in one of the two forms the rule admits at all — because a list
that prints neither is outside the read and its zero must not be presented as a held
form.

Usage:
    python3 .github/tools/refgate.py papers/issue-<N>/manuscript.md ...
    python3 .github/tools/refgate.py --selftest

Exit status: 0 = gate PASS, 1 = FAIL (including unparseable input).
`--selftest` runs the checker over fixed fixtures and asserts its whole printed
output, with a case for **each form this window admits and each it drops** — the
printed-line set (the verdict line and every advisory line) is that set's floor,
not its extent, because a case set drawn from the lines exercises exactly the
fixtures it contains and leaves every other branch of the window untested. It is
a liveness control over those fixtures, not a proof about inputs they do not
contain.
Requires only the Python 3 standard library.
"""
import re
import sys
import unicodedata

THRESHOLD = 100

# A heading like "## References" or "## 7 References" (section-numbered).
HDR = re.compile(r'^#{1,6}\s*(?:\d+[.)]?\s*)?References\s*$', re.I)
# Entry marker: "[12] text" / "12. text" / "12) text", including a marker that
# ends its line (wrapped entry) and continuation lines of a wrapped entry.
# Capped at 3 digits: a 4-digit run at line start is a YEAR on a wrapped URL or
# title line, not an entry number.
ENTRY = re.compile(r'^\s*(?:\[(\d{1,3})\]|(\d{1,3})[.)])(?:\s|$)')
# In-text citation: [12]  [12,14]  [12-14]  [12, 14]
CITE = re.compile(r'\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]')
FENCE = re.compile(r'^\s*```')

# The AUTHOR COMPONENT's printed form (README → *Presentation requirements*: the
# component is stated as a form, `Family, I.` — **and the rule admits a second form
# for a member that has no initial to print**: a work whose *record* gives one author
# token and no more prints that token alone) — and the case and the encoding are part
# of that form, because a registry's stored field is not what an entry prints. Two
# failures are readable **by position**, and both are read only in a form the house
# style admits:
#
#   * the component's SHAPE — a family token of two or more letters closed by a comma
#     and an initial (COMPONENT), **or a lone family token at the author position
#     closed by a period and followed by the year's parenthesis (SOLO)**. That union
#     is this read's **window**: an entry whose component is printed in neither form
#     (a given-name-first list, or one that never names an author) is outside it, so
#     the line prints `window/entries` — a count taken over an empty window is not a
#     passing read, and the liveness figure is what tells the two apart. **The lone
#     token is admitted because the failure read inside the window — the component's
#     case and its encoding — is readable over it too**: the rule gives that member
#     no initial, and that is the rule's exception, never a licence for its family
#     token to print the capitals a record stores. A window narrower than the read it
#     bounds reports `0 print the family name ALL-CAPS` over entries that do
#     (measured over `#44`'s `[88] Student. (1908) …`: the member left outside the
#     window was 1 of the 2 published entries the rule's own exception covers, and
#     the only entry a record's capitals could hide in).
#   * inside that window, an entry whose family token is printed ALL-CAPS — read
#     off the SAME match as the window (`str.isupper()`), so the failure set is by
#     construction inside the set it is counted over. It is the form a record's
#     stored field has, and the form the fold removes, exactly as the title rule
#     folds an ALL-CAPS stored title to title case. Initials are the house style's
#     OWN capitals and are not read: `D.` is one letter, and a matcher that flags
#     any run of capitals in the entry flags middle initials, acronyms (`DOI`,
#     `IEEE`) and venue names instead — measured 2026-09-17 over `#38`'s entries,
#     where a loose run-of-capitals rule returned 4 hits and none of them was a
#     defect.
#   * a CHARACTER REFERENCE anywhere in the entry (CHARREF: `&#39;`, `&amp;`) —
#     the form a field has when it is copied out of JSON/XML undecoded. It has no
#     legitimate place in a printed entry, so it needs no window.
# A family token is a **letter** followed by one or more letters, apostrophes or
# hyphens — Unicode letters, because the window's own printed line names the class
# as "a family name", and an ASCII-only class silently drops a member the sentence
# says is in: *the ASCII form of this class returns exactly one entry fewer than this
# one over the five published bibliographies — `#38`'s `[54] Bilò, V.`, plainly in
# the house form. The two figures move with the set they are read over and with the
# window they are read through, so the mechanism is the sentence and the numbers
# carry their head and their reader: over the five lists at `13b2b1e`, **this** copy
# returns 499 (ASCII) → 500 (letter class) of 616 entries, while the copy of that same
# head — its window admitting `Family, I.` alone — returned 498 → 499.* `--selftest`
# pins the boundary from both sides.
FAMILY = r"[^\W\d_](?:[^\W\d_]|['\u2019-]){1,}"
COMPONENT = re.compile(r"(?<![\w'\u2019-])(" + FAMILY + r")\s*,\s*[A-Z]\.")
# The component's SECOND admitted form — a lone family token at the author position,
# closed by a period and followed by the year's parenthesis (the house order's own
# next component). Position is what keeps the class tight: the token must stand
# immediately after the entry marker, so a title-first list's first word is not read
# as an author (`BERT. arXiv:…` is outside, its successor being the venue rather than
# the year). It is read for the SAME failure as `Family, I.` — the component's case —
# so both forms share one window rather than one being read as a shape and the other
# as an exception to it.
SOLO = re.compile(r"^\s*(?:\[\d{1,3}\]|\d{1,3}[.)])\s+(" + FAMILY + r")\.\s*\(")
CHARREF = re.compile(r"&(?:#\d+|#x[0-9A-Fa-f]+|[a-zA-Z]+);")


def split_doc(text):
    """Return (body, references_section_or_None, region_or_None).

    Uses the LAST References heading so that an earlier, separate list cannot
    be relied on — quality-bar item 11 requires exactly one formal section.
    The section runs from that heading TO THE END OF THE FILE: every numbered
    line after it is read as an entry, so an appendix placed after the
    bibliography is counted as entries and its markers can raise a duplicate
    warning. The region is returned as (heading_line, last_line), 1-based, so
    report() can print the window it read — the reading names its object.
    """
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if HDR.match(l)]
    if not starts:
        return text, None, None
    s = starts[-1]
    return "\n".join(lines[:s]), "\n".join(lines[s + 1:]), (s + 1, len(lines))


def strip_fences(text):
    """Drop fenced code blocks so sample text inside them is not counted."""
    out, infence = [], False
    for l in text.splitlines():
        if FENCE.match(l):
            infence = not infence
            continue
        if not infence:
            out.append(l)
    return "\n".join(out)


def parse_entries(refsec):
    """Return ({entry_number: line}, {styles_seen})."""
    ents, style = {}, set()
    for l in refsec.splitlines():
        m = ENTRY.match(l)
        if not m:
            continue
        brack, plain = m.group(1), m.group(2)
        n = int(brack if brack else plain)
        style.add('[]' if brack else '.')
        ents.setdefault(n, l.strip()[:90])
    return ents, style


def block_form(refsec):
    """Return (n_entries, n_not_separated).

    The layout read: an entry is *not separated* when the line above it is not
    blank, i.e. when it sits directly under the tail of the entry before it —
    which is what merges the whole list into one paragraph. The first entry is
    excluded: a heading already ends its own line, so nothing merges into it.
    """
    lines = refsec.splitlines()
    idx = [i for i, l in enumerate(lines) if ENTRY.match(l)]
    unsep = sum(1 for k, i in enumerate(idx)
                if k > 0 and lines[i - 1].strip() != "")
    return len(idx), unsep


def author_form(refsec):
    """Return (n_entries, window, n_allcaps, n_charref).

    The entry COMPONENT read: whether the author component is printed in a form
    the house style admits. `window` is the number of entries this read could be
    taken over — the entries whose author component is printed in one of the
    rule's two forms: `Family, I.` (COMPONENT: a family token of two or more
    letters, a comma, an initial), or, for a work whose record gives one author
    token and no more, that token alone at the author position (SOLO). The second
    is not an exception *to* this read: the failure counted below is the
    component's **case**, and a lone token's case is read exactly as a
    `Family, I.`'s is — a window that dropped it would print `0` over an entry
    printing the capitals a record stores. `n_allcaps` counts those whose family
    token is printed ALL-CAPS (the form a registry's stored field has, which the
    fold removes, as the title rule folds an ALL-CAPS stored title); `n_charref`
    counts entries carrying a character reference anywhere (`&#39;`, `&amp;`) —
    the form an undecoded field has, read with no window because it has no
    legitimate place in a printed entry.

    The window is printed with the counts because the two failures are readable
    only inside it: `0` ALL-CAPS over a window of `0` is a read of nothing, and
    the same `0` over 123 entries is the reading that the form is held.
    """
    lines = refsec.splitlines()
    idx = [i for i, l in enumerate(lines) if ENTRY.match(l)]
    window = caps = refs = 0
    for i in idx:
        # NFC first: the class is stated over *letters*, and a decomposed
        # letter (`o` + U+0300) is the same letter as `ò` — reading the raw
        # bytes would put it outside a window its own line says it is in.
        l = unicodedata.normalize('NFC', lines[i])
        hits = list(COMPONENT.finditer(l))
        solo = SOLO.match(l)
        if hits or solo:
            window += 1
            # `any` and not "the first component": the line's own words are "N
            # print the family name ALL-CAPS", so an entry that prints one is
            # counted once, wherever in the entry it stands.
            if any(m.group(1).isupper() for m in hits) or (
                    solo and solo.group(1).isupper()):
                caps += 1
        if CHARREF.search(l):
            refs += 1
    return len(idx), window, caps, refs


def cited_numbers(body):
    """Numbers appearing as in-text bracket markers (fences stripped)."""
    nums = set()
    for m in CITE.finditer(strip_fences(body)):
        for part in m.group(1).split(','):
            part = part.strip()
            if re.search(r'[\u2013-]', part):
                try:
                    a, b = (int(x) for x in re.split(r'[\u2013-]', part, 1))
                    nums.update(range(a, b + 1))
                except ValueError:
                    pass
            elif part.isdigit():
                nums.add(int(part))
    return nums


def _dups(refsec):
    c = {}
    for l in refsec.splitlines():
        m = ENTRY.match(l)
        if m:
            n = int(m.group(1) or m.group(2))
            c[n] = c.get(n, 0) + 1
    return c


def report(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    body, refsec, region = split_doc(text)
    print(f"=== {path}")
    if refsec is None:
        # The message names what was SEARCHED FOR: a heading in another form is
        # a form finding, not a manuscript that has no References section.
        print("  FAIL: no `## References` heading found — searched: an ATX heading "
              "(`#`..`######`),\n        optional section number, case-insensitive")
        return False
    print(f"  window: the last `## References` heading (line {region[0]}) to the end "
          f"of the file (line {region[1]})\n          — its numbered lines are read as entries")
    ents, style = parse_entries(refsec)
    if not ents:
        print("  FAIL: References section has no parseable numbered entries — searched: a\n"
              "        marker `[12]`, `12.` or `12)` at the start of a line (1-3 digits)")
        return False

    cited = cited_numbers(body)
    total = len(ents)
    covered = sorted(n for n in ents if n in cited)
    uncited = sorted(n for n in ents if n not in cited)
    unmatched = sorted(n for n in cited if n not in ents)
    style_s = '+'.join(sorted(style)) or '?'

    print(f"  entries={total}  numbering={'[n]' if style_s == '[]' else style_s}")
    bf_total, bf_unsep = block_form(refsec)
    print(f"  block form: {bf_total} entries, {bf_unsep} of them not separated from the entry "
          f"above by a blank line — consecutive entry lines are ONE paragraph to a CommonMark "
          f"renderer (GitHub's preview included); read the page, not the source")
    af_total, af_window, af_caps, af_refs = author_form(refsec)
    print(f"  author form: {af_window}/{af_total} entry(s) carry the read's window "
          f"(a family name, a comma, an initial — or a lone family name before the "
          f"year); {af_caps} print the family name ALL-CAPS, "
          f"{af_refs} carry a character reference (&\u2026;) — a record's stored field is not "
          f"the form an entry prints")
    print(f"  in-text cited numbers={len(cited)}  covered={len(covered)}/{total}"
          f"  coverage={100.0 * len(covered) / total:.1f}%")
    if total >= THRESHOLD and len(covered) / total < 0.9:
        print("  NOTE: high entry count with low coverage — check whether measures "
              "were added to reach the threshold.")
    if style == {'.'} and cited:
        print("  WARN: bib uses '1.' but body uses '[n]' — style mismatch "
              "(a naive '[n]' bib-count would report 0 entries)")
    if uncited:
        show = uncited[:12]
        print(f"  uncited entries ({len(uncited)}): {show}"
              f"{' ...' if len(uncited) > 12 else ''}  <- padding, not counted")
    if unmatched:
        # Prose ranges like "[25,30]" (ms) are syntactically identical to citation
        # clusters "[25,30]" (refs 25 and 30). Never reported as a defect: the
        # author resolves these in reference-check.md, per quality-bar item 11.
        print(f"  AMBIGUOUS: bracket numbers matching no entry ({len(unmatched)}) "
              f"{unmatched[:12]} — could be numeric ranges in prose, or a missing "
              f"entry; verify manually (reference-check.md)")
    dup = [n for n, c in _dups(refsec).items() if c > 1]
    if dup:
        print(f"  WARN: duplicate entry numbers: {dup[:12]}")

    ok = total >= THRESHOLD and not uncited
    print(f"  GATE: {'PASS' if ok else 'FAIL'}"
          f"{'' if total >= THRESHOLD else f' (entries {total} < {THRESHOLD})'}"
          f"{' (uncited entries count as padding)' if uncited else ''}")
    return ok


# --------------------------------------------------------------------------
# self-test — the checker is EXECUTED over fixed fixtures and its WHOLE printed
# output asserted: the verdict line and every advisory line, one case per input
# form the matchers admit and per line the checker can print. The gate rule is
# stated once in this file, in report(); the control reads report()'s output
# instead of re-deriving the rule, so the two cannot drift apart.
# --------------------------------------------------------------------------

def _make(n_entries, cite_upto, style='[]', first_section_hi=0, separated=True):
    body = "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, cite_upto + 1)) + "\n\n"

    def section(lo, hi, sty):
        entries = []
        for i in range(lo, hi + 1):
            # `Family{i}, A.` is the house style's author component, so every
            # fixture built here exercises the COMPONENT read's window as well as
            # the entry counts: a fixture that cannot carry the form makes that
            # read vacuous in the control, which is how the layout read was green
            # over 13 collapsed fixtures before R359.
            if sty == '[]':
                entries.append(f"[{i}] Family, A. Title {i}. arXiv:2500.{i:05d}.")
            else:
                entries.append(f"{i}. Family, A. Title {i}. arXiv:2500.{i:05d}.")
        # A fixture is a bibliography in the house form unless a case wants the
        # collapsed one on purpose: entries on their own lines, separated by a
        # blank line, which is what the layout read below counts.
        return "## References\n\n" + ("\n\n" if separated else "\n").join(entries) + "\n\n"

    txt = body
    if first_section_hi:
        txt += section(1, first_section_hi, style)
    txt += section(first_section_hi + 1, n_entries, style)
    return txt


def _refs(lo, hi, style='[]', separated=True):
    sep = "\n\n" if separated else "\n"
    return "## References\n\n" + sep.join(
        (f"[{i}] Family, A. arXiv:2500.{i:05d}." if style == '[]'
         else f"{i}. Family, A. arXiv:2500.{i:05d}.")
        for i in range(lo, hi + 1)) + "\n"


def selftest():
    import contextlib
    import io
    import os
    import tempfile

    cases = []

    # (name, text, lines that MUST appear in report()'s output, lines that must NOT,
    #  expected verdict). Asserting on the printed output — not on values this
    # function recomputes — is what makes this a check of the checker.
    def case(name, text, appear=(), forbid=(), expect_pass=True):
        cases.append((name, text, list(appear), list(forbid), expect_pass))

    # A clean run prints none of these — the marker strings, which is the form a
    # "must not appear" list can hold. It is NOT the whole advisory set: the
    # layout read prints a COUNT and prints it in every run (`0 of them not
    # separated` included), so no member of this tuple can carry it. Its clean
    # form is asserted by name, for every case that asserts this tuple — a
    # fixture that asserts CLEAN and whose entries are not separated fails, with
    # the missing line stated.
    CLEAN = ("WARN", "NOTE", "AMBIGUOUS", "uncited entries")
    LAYOUT_CLEAN = re.compile(r"block form: \d+ entries, 0 of them not separated")
    # The component read's clean form, for the same reason and by the same
    # mechanism: it prints a COUNT of the form's two failures over a WINDOW, so no
    # marker tuple can hold it and a clean fixture has to assert it by name.
    AUTHOR_CLEAN = re.compile(
        r"author form: \d+/\d+ entry\(s\) carry the read's window.*?"
        r"0 print the family name ALL-CAPS, 0 carry a character reference")

    # --- the verdict line, over the input forms the matchers admit ---------
    # every run prints the window it read: the reading names its object
    case("pass_exactly_100", _make(100, 100),
         ["GATE: PASS", "entries=100", "window:"], CLEAN)
    case("wrapped_marker_ends_line",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}]\nFamily, A. Title {i}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("numbered_heading", _make(100, 100).replace("## References", "## 7 References"),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("mixed_numbering",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 121))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] Family, A. arXiv:2500.{i:05d}.\n\n" for i in range(1, 61))
         + "".join(f"{i}. Family, A. arXiv:2500.{i:05d}.\n\n" for i in range(61, 121)),
         ["GATE: PASS", "numbering=.+[]"], CLEAN)
    case("fail_uncited_padding", _make(120, 110),
         ["GATE: FAIL", "uncited entries (10)"], ("WARN", "NOTE", "AMBIGUOUS"),
         expect_pass=False)
    case("fail_below_threshold", _make(60, 60),
         ["GATE: FAIL", "entries 60 < 100"], CLEAN, expect_pass=False)
    # two sections: only the LAST counts, so 60+60 does not reach the threshold
    case("two_sections_do_not_sum", _make(120, 120, first_section_hi=60),
         ["GATE: FAIL", "entries 60 < 100", "AMBIGUOUS: bracket numbers matching no entry"],
         ("WARN", "NOTE", "uncited entries"), expect_pass=False)
    # a wrapped URL line starting with a year must not become a phantom entry
    case("year_not_an_entry", _make(100, 100).rstrip() + "\n2025. https://example.org/x\n",
         ["GATE: PASS", "entries=100"], CLEAN)
    # the two early failures: no verdict line is printed for either, and each
    # NAMES THE FORM IT SEARCHED FOR — the window stated, not an absence
    case("no_references_heading", "## Introduction\n\nsee [1]\n",
         ["FAIL: no `## References` heading found", "searched:", "ATX"], ("GATE",),
         expect_pass=False)
    # a heading in another form is a FORM finding, and the message says so: the
    # manuscript has a References section, in a form this checker does not admit
    case("heading_in_another_form",
         _make(100, 100).replace("## References", "**References**"),
         ["FAIL: no `## References` heading found", "searched:", "ATX"], ("GATE",),
         expect_pass=False)
    case("no_parseable_entries",
         "## Introduction\n\nsee [1]\n\n## References\n\nNot a numbered entry.\n",
         ["FAIL: References section has no parseable numbered entries", "searched:", "`[12]`"],
         ("GATE",), expect_pass=False)
    # the region runs to the end of the file, so a numbered appendix placed after
    # the bibliography is read as entries — and its markers raise the duplicate
    # warning about keys the bibliography does not duplicate. Pinned, not blessed:
    # a reader sees both the WARN and the window that produced it.
    case("region_runs_to_end_of_file",
         _make(101, 101) + "\n\n## Appendix\n\n1. Step one.\n2. Step two.\n3. Step three.\n",
         ["window:", "entries=101", "WARN: duplicate entry numbers: [1, 2, 3]"],
         ("NOTE", "AMBIGUOUS"))
    # and the count itself moves: an appendix numbered past the bibliography's own
    # last key raises `entries` above the number of bibliography entries
    case("appendix_numbered_list_counts_as_entries",
         _make(96, 96) + "\n\n## Appendix\n\n97. Step one.\n98. Step two.\n99. Step three.\n"
         "100. Step four.\n101. Step five.\n",
         ["window:", "entries=101", "uncited entries (5)"], ("WARN", "NOTE", "AMBIGUOUS"),
         expect_pass=False)

    # --- every advisory line the checker can print ------------------------
    case("note_low_coverage", _make(120, 100),
         ["NOTE: high entry count with low coverage", "uncited entries (20)"],
         ("WARN", "AMBIGUOUS"), expect_pass=False)
    case("warn_style_mismatch", _make(100, 100, style='.'),
         ["WARN: bib uses '1.' but body uses '[n]'", "GATE: PASS"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    # a repeated entry number: the WARN fires and the verdict still passes — the
    # advisory line is the finding, and no verdict clears it
    case("warn_duplicate_entry_numbers",
         _make(100, 100) + "[50] Duplicate Author, Duplicate Title, arXiv:2500.00050, 2026.\n",
         ["WARN: duplicate entry numbers: [50]", "GATE: PASS"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    # brackets matching no entry: reported, never a defect by itself
    case("ambiguous_unmatched_brackets",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + " over a latency span [900,901]\n\n" + _refs(1, 100),
         ["AMBIGUOUS: bracket numbers matching no entry (2)", "GATE: PASS"],
         ("WARN", "NOTE", "uncited entries"))

    # --- the LAYOUT read: the same entries, separated and collapsed ---------
    # one entry per line, entries separated by a blank line: renders as entries
    case("block_form_separated",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] Family, A. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "entries=100", "block form: 100 entries, 0 of them not separated"],
         CLEAN)
    # the same 100 entries with no blank lines: ONE paragraph on the page, and
    # the line says so — while the verdict does not move, because the layout read
    # is an advisory and the count and the coverage are still met
    case("block_form_collapsed",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n" + _refs(1, 100, separated=False),
         ["GATE: PASS", "entries=100",
          "block form: 100 entries, 99 of them not separated"],
         CLEAN)

    # --- the COMPONENT read: the stored form of a record is not the printed form
    # the window is live, and it is asserted WITH the counts: `100/100` is what
    # makes the two zeros below it a reading rather than a read of nothing
    case("author_form_window_live", _make(100, 100),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "0 print the family name ALL-CAPS", "0 carry a character reference"],
         CLEAN)
    # one family token printed ALL-CAPS — the form a registry's stored field has
    case("author_form_allcaps_family",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'GALE, D.' if i == 15 else 'Family, A.'} "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "1 print the family name ALL-CAPS, 0 carry a character reference"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    # an undecoded character reference — the form a field has out of JSON/XML
    case("author_form_character_reference",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'Li, Z.; O&#39;Brien, L.' if i == 95 else 'Family, A.'} "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "1 carry a character reference"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    # the read's WINDOW can be empty, and the line then says so: a list in another
    # order (given-name-first) is outside this read, so its zero is not a held form
    case("author_form_window_empty",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] Author {i}. Title {i}. arXiv:2500.{i:05d}.\n\n"
                   for i in range(1, 101)),
         ["GATE: PASS", "author form: 0/100 entry(s) carry the read's window"],
         ("WARN", "NOTE", "AMBIGUOUS", "uncited entries"))
    # ...and what the read must NOT flag: the house style's own capitals (initials,
    # middle initials), an acronym, and a venue — the four false positives a
    # run-of-capitals matcher returns (measured 2026-09-17 over #38: 4 hits, 0
    # defects). Only a family token in the component's own shape is read.
    case("author_form_capitals_not_read",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {('Smith, A. M. H. W.' if i == 28 else 'Chen, L.')} "
                   f"Title {i}. IEEE Trans. ACM. arXiv:2500.{i:05d}.\n\n"
                   for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "0 print the family name ALL-CAPS, 0 carry a character reference"],
         CLEAN)

    # --- the WINDOW's class, pinned from both sides ------------------------
    # A family token is a LETTER followed by letters/apostrophes/hyphens, and the
    # line names that class as "a family name". An ASCII-only class is narrower
    # than the name: over the five published bibliographies it returns exactly one
    # entry fewer than the letter class, #38's `[54] Bilò, V.` — the mechanism is the
    # sentence, and the figures carry their head and their reader (over the five lists
    # at 13b2b1e this copy reads 499 → 500 of 616 entries; the copy of that head, its
    # window admitting `Family, I.` alone, read 498 → 499). These two cases are that
    # boundary read from the inside and from the outside, so a future narrowing turns
    # the first red (99/100) rather than passing quietly.
    case("author_form_letter_class_in_window",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'Bilò, V.' if i == 54 else 'Family, A.'} "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "0 print the family name ALL-CAPS, 0 carry a character reference"],
         CLEAN)
    # ...and the same letter in a record's capitals is a defect, so the ALL-CAPS
    # count is read off the window's own match (`isupper()`) and not a second,
    # ASCII-only pattern that would leave this entry uncounted.
    case("author_form_letter_class_allcaps",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'BILÒ, V.' if i == 54 else 'Family, A.'} "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "1 print the family name ALL-CAPS, 0 carry a character reference"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    # ...and a decomposed letter is the same letter: the read normalises to NFC
    # first, so `Bilo` + U+0300 is in the window rather than outside it.
    case("author_form_decomposed_letter_in_window",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'Bilo\u0300, V.' if i == 54 else 'Family, A.'} "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "0 print the family name ALL-CAPS, 0 carry a character reference"],
         CLEAN)
    # the line's words are "N print the family name ALL-CAPS", so an entry that
    # prints ONE — wherever it stands in the component — is counted once.
    case("author_form_second_component_allcaps",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'Gale, D.; SHAPLEY, L.' if i == 15 else 'Family, A.'} "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "1 print the family name ALL-CAPS, 0 carry a character reference"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    # The component's SECOND admitted form: a work whose record gives one author
    # token and no more prints that token alone, and it is read for the SAME
    # failure — the component's case — so it stands INSIDE this read's window
    # rather than being a member the zero is silent about. Before this case's
    # form was admitted (filed at R370, fixed at R371), `STUDENT. (1908) …`
    # printed `102/103 … 0 print the family name ALL-CAPS` — a true sentence about
    # a window, and a false one about the entries.
    case("author_form_lone_token_in_window",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'Student.' if i == 88 else 'Family, A.'} (1908). "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "0 print the family name ALL-CAPS, 0 carry a character reference"],
         CLEAN)
    # ...and the capitals a record stores are that failure here too
    case("author_form_lone_token_allcaps",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'STUDENT.' if i == 88 else 'Family, A.'} (1908). "
                   f"Title {i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 100/100 entry(s) carry the read's window",
          "1 print the family name ALL-CAPS, 0 carry a character reference"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    # ...and the boundary from outside it: the lone-token form is pinned BY
    # POSITION and by the year's parenthesis, so a title-first list's first word
    # is not read as an author — the component that follows a title is the venue,
    # not the year. A window grown past the rule's own set turns this case red.
    case("author_form_lone_token_not_an_author",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] {'BERT.' if i == 54 else 'Family, A.'} arXiv:2500.{i:05d}, 2018. "
                   f"Title {i}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "author form: 99/100 entry(s) carry the read's window",
          "0 print the family name ALL-CAPS, 0 carry a character reference"],
         CLEAN)
    # A control owes the window's boundary: a case set drawn from the lines the
    # checker can print exercises exactly the fixtures it holds, so a branch of
    # the window no case reaches can be deleted with this run still green. Each
    # case below pins one form the window states, so removing that form from a
    # matcher must fail the control — measured: seven such mutations (six window
    # forms and one printed listing's cap) escaped the earlier 19-case set.
    case("heading_case_insensitive",
         _make(100, 100).replace("## References", "## references"),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("heading_at_any_level",
         _make(100, 100).replace("## References", "#### References"),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("heading_trailing_space",
         _make(100, 100).replace("## References", "## References  "),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("paren_entry_marker",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"{i}) Family, A. arXiv:2500.{i:05d}.\n" for i in range(1, 101)),
         ["GATE: PASS", "entries=100", "numbering=.",
          "WARN: bib uses '1.' but body uses '[n]'"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    case("indented_entry_marker",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"  [{i}] Family, A. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("en_dash_range_marker",
         "## Introduction\n\nsee [1\u201397] and [98, 99, 100]\n\n" + _refs(1, 100),
         ["GATE: PASS", "covered=100/100"], CLEAN)
    # the uncited listing is capped at twelve: a case for that printed form
    case("uncited_list_capped",
         _make(120, 100),
         ["uncited entries (20): [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112] ...",
          "NOTE: high entry count with low coverage"],
         ("WARN", "AMBIGUOUS"), expect_pass=False)

    # --- input forms: text that must NOT be read as an entry or a citation --
    # a fenced code sample is quoted text, not a citation
    case("fences_are_ignored",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n```\nsee [500] in a sample\n```\n\n" + _refs(1, 100),
         ["GATE: PASS", "covered=100/100"], CLEAN)
    # range and cluster markers both discharge coverage
    case("range_and_cluster_markers",
         "## Introduction\n\nsee [1-97] and [98, 99, 100]\n\n" + _refs(1, 100),
         ["GATE: PASS", "covered=100/100"], CLEAN)

    failures = []
    tmpdir = tempfile.mkdtemp(prefix="refgate-selftest-")
    try:
        for name, text, appear, forbid, expect_pass in cases:
            path = os.path.join(tmpdir, f"{name}.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                verdict = report(path)
            printed = buf.getvalue()
            missing = [s for s in appear if s not in printed]
            # ...and the layout read's clean form is asserted for every case that
            # asserts CLEAN — except the one case whose subject IS the layout
            # line, which pins the count in `appear` instead (the same assertion
            # read from the other side).
            if (tuple(forbid) == CLEAN
                    and not any(s.startswith("block form:") for s in appear)
                    and not LAYOUT_CLEAN.search(printed)):
                missing.append("<block form: T entries, 0 of them not separated>")
            # ...and the component read's clean form on the same terms: a case
            # whose subject IS that line pins the count in `appear` instead.
            if (tuple(forbid) == CLEAN
                    and not any(s.startswith("author form:") for s in appear)
                    and not AUTHOR_CLEAN.search(printed)):
                missing.append("<author form: W/T entry(s) carry the read's window, "
                               "0 print the family name ALL-CAPS, 0 carry a character reference>")
            spurious = [s for s in forbid if s in printed]
            ok = verdict == expect_pass and not missing and not spurious
            print(f"  [{'ok' if ok else 'FAIL'}] {name}: "
                  f"verdict={'PASS' if verdict else 'FAIL'}"
                  + (f"  MISSING={missing}" if missing else "")
                  + (f"  UNEXPECTED={spurious}" if spurious else ""))
            if not ok:
                failures.append(name)
    finally:
        for f in os.listdir(tmpdir):
            os.unlink(os.path.join(tmpdir, f))
        os.rmdir(tmpdir)

    print(f"selftest: {len(cases) - len(failures)}/{len(cases)} cases ok")
    return not failures


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__.strip().split("Usage:")[1].strip())
    if args == ['--selftest']:
        sys.exit(0 if selftest() else 1)
    sys.exit(0 if all([report(f) for f in args]) else 1)
