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

Usage:
    python3 .github/tools/refgate.py papers/issue-<N>/manuscript.md ...
    python3 .github/tools/refgate.py --selftest

Exit status: 0 = gate PASS, 1 = FAIL (including unparseable input).
`--selftest` runs the checker over fixed fixtures and asserts its whole printed
output, with a case for each line the checker can print (the verdict line and
every advisory line); the fixtures span the input forms named above. It is a
liveness control over those fixtures, not a proof about inputs they do not
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
    """Return (body, references_section_or_None).

    Uses the LAST References heading so that an earlier, separate list cannot
    be relied on — quality-bar item 11 requires exactly one formal section.
    """
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if HDR.match(l)]
    if not starts:
        return text, None
    s = starts[-1]
    return "\n".join(lines[:s]), "\n".join(lines[s + 1:])


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
    body, refsec = split_doc(text)
    print(f"=== {path}")
    if refsec is None:
        print("  FAIL: no `## References` heading found")
        return False
    ents, style = parse_entries(refsec)
    if not ents:
        print("  FAIL: References section has no parseable numbered entries")
        return False

    cited = cited_numbers(body)
    total = len(ents)
    covered = sorted(n for n in ents if n in cited)
    uncited = sorted(n for n in ents if n not in cited)
    unmatched = sorted(n for n in cited if n not in ents)
    style_s = '+'.join(sorted(style)) or '?'

    print(f"  entries={total}  numbering={'[n]' if style_s == '[]' else style_s}")
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
    case("pass_exactly_100", _make(100, 100), ["GATE: PASS", "entries=100"], CLEAN)
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
    # the two early failures: no verdict line is printed for either
    case("no_references_heading", "## Introduction\n\nsee [1]\n",
         ["FAIL: no `## References` heading found"], ("GATE",), expect_pass=False)
    case("no_parseable_entries",
         "## Introduction\n\nsee [1]\n\n## References\n\nNot a numbered entry.\n",
         ["FAIL: References section has no parseable numbered entries"], ("GATE",),
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
