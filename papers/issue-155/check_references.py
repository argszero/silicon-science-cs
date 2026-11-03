#!/usr/bin/env python3
"""Entry-form read of the bibliography, made by entry block.

Why a block and not a line: the return that asked for this was measured by entry block, and a
line-based read misses the two things that were wrong here. It misses the year's *position* (the
entry contained a year either way -- `... Journal of Scheduling, 1998.` passes any test that asks
whether a year is present), and it mis-counts the moment an entry wraps onto a second line. One
block is one entry: a block is the text between blank lines, which is also the unit every
CommonMark renderer prints as one paragraph.

The house style resolves the components in one pass, so they are asserted in that order:

    [n] <authors> (<YYYY>). <title>. <venue or identifier>. <resolvable URL> -- Difference: <line>

A year after the venue is not the same entry as a year before the title, even though both contain
one, so the check is on positions and not on presence. Prints one line per entry and exits
non-zero if any entry fails. Reads only -- it writes nothing, so no other step's comparison of a
committed artifact can be changed by running it.
"""

import re
import sys

DEFAULT = "manuscript.md"

HEADING = re.compile(r"^## References\s*$", re.M)
NEXT_HEADING = re.compile(r"^## ", re.M)
ENTRY_HEAD = re.compile(r"^\[(\d+)\]\s+(\S.*)$", re.S)
YEAR = re.compile(r"\((\d{4})\)\.")
URL = re.compile(r"https://(?:doi\.org/|arxiv\.org/)\S+")
DIFF = re.compile(r"\s--\sDifference:\s*(\S.*)$", re.S)

# The house author component: `Family, I.`, with further initials after it. A bare family list is
# NOT that component even though it is not empty -- which is the whole finding of this round: the
# step's title claimed the house form while its only assertion was that the position in front of
# the year was non-empty, and it was green over 82 entries printing `Kang; Tian; Hu.`. The one
# form a record can legitimately fail to carry is a given name, and that case prints its own
# marker rather than an initial this package would have invented.
ET_AL = re.compile(r"^et al\.$")
NO_GIVEN = re.compile(r"^[^,;]+ \(no given name in the record\)\.$")
NO_AUTHOR_FIELD = re.compile(r"^\(no author field in the record\)\.$")


def in_house_form(part):
    """Is this one author component in the form the step's title claims?

    A capital initial, not an ASCII one: `Maślanka, Ł.` is in the house form and a `[A-Z]` class
    reports it as a defect -- which is how this predicate's first draft produced four failures
    that were defects of the check. The initial is a single letter, in whatever script the
    record's family name is written in, and it must be upper-case.
    """
    if ET_AL.match(part) or NO_GIVEN.match(part) or NO_AUTHOR_FIELD.match(part):
        return True
    family, sep, rest = part.partition(",")
    if not sep or not family.strip():
        return False
    initials = [t for t in rest.replace(".", ". ").split() if t]
    if not initials:
        return False
    return all(len(t) == 2 and t.endswith(".") and t[0].isupper() for t in initials)


def window(text):
    """The References section, and nothing after it."""
    heads = list(HEADING.finditer(text))
    if len(heads) != 1:
        return None, "this bibliography is %d `## References` headings, not one" % len(heads)
    start = heads[0].end()
    nxt = NEXT_HEADING.search(text, start)
    return text[start:nxt.start() if nxt else len(text)], None


def blocks(body):
    return [b.strip() for b in re.split(r"\n[ \t]*\n", body) if b.strip()]


def read_entry(block):
    """One entry's components, or the list of what is missing from it.

    Returns (report, problems). `report` is what gets printed for this entry; `problems` is empty
    when the entry is in the house form.
    """
    problems = []
    head = ENTRY_HEAD.match(block)
    if not head:
        return None, ["this block is not an entry (it does not begin `[n] `)"]
    num = int(head.group(1))
    rest = head.group(2).strip()
    if "\n" in rest.strip():
        problems.append("this entry wraps onto %d lines, so one block prints as more than one "
                        "entry to a reader" % (rest.count("\n") + 1))
        rest = " ".join(rest.split())

    year = YEAR.search(rest)
    url = URL.search(rest)
    diff = DIFF.search(rest)

    # 1. the authors, in front of the year
    if year is None:
        problems.append("no parenthesised year `(YYYY).` anywhere in the entry")
        authors = None
    else:
        authors = rest[:year.start()].strip().rstrip(",;")
    author_parts, in_form = [], 0
    if year is not None and not authors:
        problems.append("the author position is empty in front of the year")
    elif authors:
        author_parts = [a.strip() for a in authors.split(";") if a.strip()]
        off = [a for a in author_parts if not in_house_form(a)]
        in_form = len(author_parts) - len(off)
        if off:
            problems.append("the author component is not the house form `Family, I.` (or `et al.`): "
                            "%s -- a bare family list is a component that is present in the wrong "
                            "form, which a presence test cannot tell apart from a correct one"
                            % "; ".join(off))
    if year is not None and not rest[year.end():year.end() + 1].isspace():
        problems.append("the year is not closed by `(YYYY). ` before the title")

    # 2. the link, and it must come after the year -- the identifier is the last thing before the
    #    stated difference, never in front of the title
    if url is None:
        problems.append("no resolvable `https://doi.org/` or `https://arxiv.org/` link")
    elif year is not None and url.start() < year.end():
        problems.append("the link is printed before the year, which is not the stated order")

    # 3. the entry closes with its one-line stated difference
    if diff is None:
        problems.append("the entry does not close with its one-line `Difference: ...`")
    elif url is not None and diff.start() < url.end():
        problems.append("`Difference:` is printed before the link, so it is not the closing "
                        "component")
    elif not diff.group(1).strip():
        problems.append("`Difference:` is printed with no text after it")

    # 4. between the year and the link there must be a title and a venue, not an empty gap
    if year is not None and url is not None:
        middle = rest[year.end():url.start()].strip()
        if len(middle) < 3:
            problems.append("no title or venue between the year and the link")
        elif middle.count(". ") < 1:
            problems.append("title and venue are not separated, so one of them is missing")
    elif year is None or url is None:
        middle = ""

    report = {
        "num": num,
        "authors": None if not author_parts else len(author_parts),
        "in_form": in_form,
        "year": YEAR.search(rest).group(1) if year else "-",
        "middle": len(middle),
        "diff": len(diff.group(1).strip()) if diff else 0,
        "text": diff.group(1).strip() if diff else "",
    }
    return report, problems


def plant_bare_authors(text):
    """Prove the form check fires on a bare family list, using the gate's own read.

    The defect this round repaired was GREEN under this file: entries printing `Kang; Tian; Hu.`
    passed, because the only assertion about the author component was that the position in front
    of the year was not empty. So the plant doctors a copy of this manuscript -- one entry's
    author run replaced by a bare family list -- and requires `read_entry`, the same read the gate
    runs, to report a problem that names the form. A fixture calling a copy of the predicate would
    be testing the copy, which is the failure this journal has paid for twice.
    """
    body, problem = window(text)
    if problem:
        print("   [FAIL] the plant cannot read the bibliography: %s" % problem)
        return False
    entries = blocks(body)
    if not entries:
        print("   [FAIL] the plant found no entries to doctor")
        return False
    block = entries[0]
    head = ENTRY_HEAD.match(block)
    rest = head.group(2)
    year = YEAR.search(rest)
    if year is None:
        print("   [FAIL] the plant's entry has no year to anchor the author position")
        return False

    report, found = read_entry(block)
    control_ok = not any("house form" in f for f in found)
    if not control_ok:
        print("   [FAIL] the control entry is not in the house form, so the plant proves nothing")
        return False
    print("   [ok] control: entry [%03d] as it stands passes the form check" % report["num"])

    doctored = block[:head.start(2)] + "Kang; Tian; Hu. " + rest[year.start():]
    report, found = read_entry(doctored)
    hits = [f for f in found if "house form" in f]
    if not hits:
        print("   [FAIL] a bare family list in the author position is NOT refused -- the check "
              "cannot fire on the defect it was widened for")
        return False
    print("   [ok] the same entry with `Kang; Tian; Hu.` is refused: %s" % hits[0][:96])
    return True


def main(argv):
    flags = [a for a in argv[1:] if a.startswith("--")]
    args = [a for a in argv[1:] if not a.startswith("--")]
    path = args[0] if args else DEFAULT
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as exc:
        print("[FAIL] cannot read %s: %s" % (path, exc))
        return 1
    body, problem = window(text)
    if problem:
        print("[FAIL] %s" % problem)
        return 1

    entries = blocks(body)
    if not entries:
        print("[FAIL] the References section contains no entries, so this read saw nothing")
        return 1

    problems = 0
    reports = []
    for block in entries:
        report, found = read_entry(block)
        if report is None:
            print("[FAIL] %s" % found[0])
            problems += 1
            continue
        reports.append(report)
        state = "ok" if not found else "FAIL"
        # lengths, not counts: `authors=11` would read as eleven authors; and a component the read
        # could not locate prints `-`, never `0`, because "no authors" is a different claim from
        # "this entry failed before the author position was reached"
        # the column is the FORM, not a length: `authors=16ch` was a measurement of the string
        # that a bare family list also passes, and the step's title claims the form
        ach = ("-" if report["authors"] is None
               else "%d/%d" % (report["in_form"], report["authors"]))
        print("[%03d] %-4s authors=%5s (%s) title+venue=%3dch url=%s diff=%3dch"
              % (report["num"], state, ach, report["year"], report["middle"],
                 "ok" if not any("link" in f for f in found) else "FAIL", report["diff"]))
        for f in found:
            print("       [FAIL] %s" % f)
            problems += 1

    # numbering: the keys the in-text citations resolve through
    nums = [r["num"] for r in reports]
    if nums != list(range(1, len(nums) + 1)):
        print("[FAIL] the entries are not numbered 1..%d in order" % len(nums))
        problems += 1

    # Reported, not gated: the house style asks every entry to close with *its* difference and
    # says nothing about how many may coincide. The published bibliographies carry 132/132,
    # 125/125 and 117/117 distinct lines, so the number is printed beside the gate for a reader
    # to check rather than turned into a threshold this file would have invented.
    distinct = len(set(r["text"] for r in reports if r["text"]))

    total_parts = sum(r["authors"] or 0 for r in reports)
    total_form = sum(r["in_form"] for r in reports)
    in_form_entries = sum(1 for r in reports if r["authors"] and r["in_form"] == r["authors"])

    rc = 0
    if "--plant-authors" in argv:
        print()
        print("== plant: a bare family list in the author position")
        ok = plant_bare_authors(text)
        print("   author-form plant: %s" % ("GREEN -- the check fires on a bare family list"
                                            if ok else "RED"))
        rc = 1 if not ok else 0

    print()
    print("author form: %d of %d entries print every author component in the house form "
          "(%d of %d components)" % (in_form_entries, len(reports), total_form, total_parts))
    print("entries=%d distinct Difference: %d/%d problems=%d"
          % (len(reports), distinct, len(reports), problems))
    if problems:
        print("GATE: FAIL")
        return 1
    print("GATE: PASS")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
