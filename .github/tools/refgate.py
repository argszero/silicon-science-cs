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
line here it does not move the verdict.

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

def _make(n_entries, cite_upto, style='[]', first_section_hi=0):
    body = "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, cite_upto + 1)) + "\n\n"

    def section(lo, hi, sty):
        out = ["## References", ""]
        for i in range(lo, hi + 1):
            if sty == '[]':
                out.append(f"[{i}] Author {i}, Title {i}, arXiv:2500.{i:05d}, 2026.")
            else:
                out.append(f"{i}. Author {i}, Title {i}, arXiv:2500.{i:05d}, 2026.")
        return "\n".join(out) + "\n\n"

    txt = body
    if first_section_hi:
        txt += section(1, first_section_hi, style)
    txt += section(first_section_hi + 1, n_entries, style)
    return txt


def _refs(lo, hi, style='[]'):
    return "## References\n\n" + "".join(
        (f"[{i}] A{i}. arXiv:2500.{i:05d}.\n" if style == '[]' else f"{i}. A{i}. arXiv:2500.{i:05d}.\n")
        for i in range(lo, hi + 1))


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

    # a clean run prints none of these
    CLEAN = ("WARN", "NOTE", "AMBIGUOUS", "uncited entries")

    # --- the verdict line, over the input forms the matchers admit ---------
    # every run prints the window it read: the reading names its object
    case("pass_exactly_100", _make(100, 100),
         ["GATE: PASS", "entries=100", "window:"], CLEAN)
    case("wrapped_marker_ends_line",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"[{i}]\nAuthor {i}, Title {i}.\n" for i in range(1, 101)),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("numbered_heading", _make(100, 100).replace("## References", "## 7 References"),
         ["GATE: PASS", "entries=100"], CLEAN)
    case("mixed_numbering",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 121))
         + "\n\n## References\n\n"
         + "".join(f"[{i}] A{i}. arXiv:2500.{i:05d}.\n" for i in range(1, 61))
         + "".join(f"{i}. A{i}. arXiv:2500.{i:05d}.\n" for i in range(61, 121)),
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
         + "".join(f"[{i}] A{i}. arXiv:2500.{i:05d}.\n\n" for i in range(1, 101)),
         ["GATE: PASS", "entries=100", "block form: 100 entries, 0 of them not separated"],
         CLEAN)
    # the same 100 entries with no blank lines: ONE paragraph on the page, and
    # the line says so — while the verdict does not move, because the layout read
    # is an advisory and the count and the coverage are still met
    case("block_form_collapsed",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n" + _refs(1, 100),
         ["GATE: PASS", "entries=100",
          "block form: 100 entries, 99 of them not separated"],
         CLEAN)

    # --- one case per WINDOW FORM, not per printed line --------------------
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
         + "".join(f"{i}) A{i}. arXiv:2500.{i:05d}.\n" for i in range(1, 101)),
         ["GATE: PASS", "entries=100", "numbering=.",
          "WARN: bib uses '1.' but body uses '[n]'"],
         ("NOTE", "AMBIGUOUS", "uncited entries"))
    case("indented_entry_marker",
         "## Introduction\n\n" + " ".join(f"see [{i}]" for i in range(1, 101))
         + "\n\n## References\n\n"
         + "".join(f"  [{i}] A{i}. arXiv:2500.{i:05d}.\n" for i in range(1, 101)),
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
