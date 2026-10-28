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
    if year is not None and not authors:
        problems.append("the author position is empty in front of the year")
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
        "authors": None if authors is None else len(authors),
        "year": YEAR.search(rest).group(1) if year else "-",
        "middle": len(middle),
        "diff": len(diff.group(1).strip()) if diff else 0,
        "text": diff.group(1).strip() if diff else "",
    }
    return report, problems


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT
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
        ach = "-" if report["authors"] is None else "%dch" % report["authors"]
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

    print()
    print("entries=%d distinct Difference: %d/%d problems=%d"
          % (len(reports), distinct, len(reports), problems))
    if problems:
        print("GATE: FAIL")
        return 1
    print("GATE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
