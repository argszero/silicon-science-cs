#!/usr/bin/env python3
"""pointgate_v1 - the tree's named pointers, resolved at the carrier they name.

The rule (README.md -> Links; the requirement is collected by the editor's own
audit, carried outside this repository -- no tracked file holds its list):

    every cross-reference a tracked file makes is read by someone who has this
    repository and not necessarily anything else, so it must resolve *here*.

A cross-reference resolves in **three forms**, and this tool is the instrument
for the **second** - a **named pointer**, written `-> *Name*` or `see *Name*`.
Its **first** form (a markdown link target) is read by `.github/tools/linkgate.py`.
Its **third** - a reference by **position**, a number indexing a list - stays a
read, because which list a number indexes is what the citing sentence names and
no instrument can infer it.

**A named pointer is not of that third kind, and this tool exists because the
tree said it was.** `linkgate.py`'s header, and README.md -> Links, class the
pointer with the number: *"the rule's second and third forms ... resolve only
inside the namespace of a list the citing sentence or its carrier names. Which
list is meant is a read, not a computation."* That sentence is true of the
**number**. A named pointer indexes no list: it carries its target's **name**
and the **carrier** the name lives in, and the resolution it owes is stated in
the same clause that grants the exemption - *resolved against a heading, a bold
lead, an item's own name*. Name, carrier and resolver are all given, so nothing
is left to infer. **Measured at R399**: the clause's own three forms reach the
tree only after four further ones are stated, and the exemption is what kept
any instrument from stating them.

Resolution, as this tool performs it:

  carrier   the file the name lives in: the **nearest carrier the pointer's own
            sentence names to its left** (a backticked path, a markdown link
            target, a bare `NAME.md`, or the **stem** the tree also writes,
            `README`); where the sentence names a **chain** (`*A* -> *B*`), B is
            read in the carrier **A lives in**; a sentence naming neither reads
            the name in the **linking file**.
  name      the run after the arrow or after `see`, read as **rendered text**:
            the target's own inline emphasis is part of how it prints, not part
            of its name (`**What makes a concern *major*.**` is the name
            *What makes a concern major*).
  resolves  when the carrier holds the name as the **leading run** of a line - a
            **heading**, a **lead** (a bold or italic run at the start of the
            line **or of a sentence** in it) or a **blockquote item** - where the
            run is the name, or the name plus the **break** the tree writes
            between a name and its gloss (`.`, `,`, `:`, `;`, `-`, `-`, `)`).
            Read after the line's own indentation, blockquote and list markers,
            case-insensitively; a bold lead may **wrap across source lines**.

Class of one pointer, every class counted and named:

  resolved         the name is on one of the three lines of the named carrier
  UNRESOLVED       the carrier is in this tree and holds no such line <- member
  names-a-carrier  the name is itself a tracked file; resolves iff it is tracked
  out-of-tree      the pointer names a carrier this repository does not hold
  code-target      the arrow's **other sense**: `-> `v`` states what an input
                   *becomes* (`[1997]` -> `(1997)`, `.permissions` -> `"push"`),
                   not what it points at. No property of the line separates the
                   two senses, so this tool classes them and does not decide
                   them - the boundary linkgate.py draws for its own forms.

Usage:
  python3 .github/tools/pointgate.py            # report, exit 0
  python3 .github/tools/pointgate.py --check    # exit 1 on any UNRESOLVED pointer
  python3 .github/tools/pointgate.py --selftest # the tool's own cases

Run it from the repository root; the relative tool path resolves there.
"""

import io
import os
import re
import subprocess
import sys

# `-> *Name*` / `see *Name*` - the form the clause names.  A name may wrap across
# a source line (`*Label\n> state machine*`), so the run admits newlines and is
# collapsed before it is compared.
POINTER = re.compile(r"(?:→|(?<![\w*])see\b)\s*(?P<open>[*])(?P<name>[^`*]{2,90}?)(?P<close>[*])",
                     re.I)
# `-> `x`` / `see `x``: the same glyph and the words `see`, a code span target
CODE_TARGET = re.compile(r"(?:→|(?<![\w*])see\b)\s*`[^`\n]{1,70}`", re.I)

PATHLIKE = re.compile(
    r"`([\w./-]+\.(?:md|py|sh|json|gitignore|yml|txt))`"
    r"|\[[^\]]*\]\(([^)\s#]+\.(?:md|py|sh|json|gitignore|txt))"
    r"|(?<![\w`./-])([A-Za-z][\w.-]*\.(?:md|py|sh|json|gitignore|txt))"
    r"|(?<![\w`./-])(README|INSTANCES)(?![\w.])")   # the tree writes the stem too

# the emphasised runs a name can be: `***Name***`, `**Name**` (nested `*word*` inside)
# and `*Name*`.  A run is only a **lead** at an addressable position - see name_lines.
BOLD3 = re.compile(r"(?<![*\w])\*\*\*(?![*\s])((?:[^*]|\*(?!\*)){2,600}?)\*\*\*(?![*])")
BOLD = re.compile(r"(?<![*\w])\*\*(?![*\s])((?:[^*]|\*(?!\*)){2,600}?)\*\*(?![*])")
ITAL = re.compile(r"(?<![*\w])\*(?![*\s])([^*\n]{2,140}?)\*(?![*])")


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def tracked(root, args):
    out = subprocess.run(["git", "ls-files"] + args, cwd=root,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\n") if p]


def norm(s):
    s = re.sub(r"(?m)^\s*>+\s?", "", s)   # a name wrapped across a blockquote line
    s = render(s)
    return s.strip().strip(".,;:—-()").lower()


def render(s):
    """the text a reader sees: inline markup is a rendering of the line, not the line"""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)   # a link renders as its text
    s = re.sub(r"`([^`]*)`", r"\1", s)               # a code span renders as its content
    s = re.sub(r"[*_]{1,3}", "", s)                  # emphasis renders as its run
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def strip_markers(line):
    """drop the indentation, blockquote and list markers a lead may sit behind"""
    line = re.sub(r"^\s*(?:>\s?)+", "", line)
    line = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", "", line)
    return line.lstrip()


def name_lines(text):
    """the runs a name may resolve on: a heading, a lead, a blockquote item

    A **lead** is an emphasised run at an addressable position - the start of the
    line, or the start of a **sentence** in it (the tree writes `*Citation key.*`
    as the second sentence of a paragraph, and cites it twice).  A lead's text is
    read as **rendered text**: the target's own inline emphasis is part of how it
    prints, not part of its name (`**What makes a concern *major*.**` is the name
    *What makes a concern major*).
    """
    out = []
    for raw in text.split("\n"):
        line = strip_markers(raw)
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            out.append(render(m.group(1)))
            continue
        if raw.lstrip().startswith(">"):
            out.append(render(line))          # a blockquote item
        for m2 in ITAL.finditer(line):
            pre = line[:m2.start()]
            if pre == "" or re.search(r"[.!?:;]\s*$", render(pre)):
                out.append(render(m2.group(1)))
    for rx in (BOLD3, BOLD):
        for m2 in rx.finditer(text):          # a bold lead may wrap across lines
            ls = text.rfind("\n", 0, m2.start()) + 1
            pre = strip_markers(text[ls:m2.start()])
            if pre == "" or re.search(r"[.!?:;]\s*$", render(pre)):
                out.append(render(m2.group(1)))
    return out


def resolves(name, lines):
    """a name resolves on a leading run: the run is the name, or the name plus a break

    The break is where the tree ends a name and begins its gloss - `.`, `,`, `:`,
    `;`, `—`, `-`, `)` - or where the line ends.
    """
    want = norm(name)
    if not want:
        return False
    pat = re.compile(r"^" + re.escape(want) + r"(?=$|[\s.,;:)—\-)\]])")
    return any(pat.match(line.lower()) for line in lines)


def sentence_before(text, i):
    j = max(text.rfind("\n\n", 0, i), text.rfind(". ", 0, i), text.rfind("; ", 0, i))
    return text[j + 1:i]


def carrier_left(root, text, i, files):
    """the carrier the pointer names - the path it ends with, else the linker

    A carrier is named **immediately** before the pointer (only the arrow, `see`,
    `(`, whitespace between), which is how the tree writes it; a path elsewhere in
    a long sentence belongs to another clause and names no carrier (`R399`:
    `papers/issue-1/README.md:42`'s *Traceability* was read into
    `consistency_check.py` by the wider rule).
    """
    sent = sentence_before(text, i)
    last = None
    for m in PATHLIKE.finditer(sent):
        last = m
    if last is None:
        return None
    cand = last.group(1) or last.group(2) or last.group(3) or last.group(4)
    if last.group(4):
        cand += ".md"                      # a stem the tree writes stands for its file
    cand = cand.split("#")[0]
    if cand.startswith(("http://", "https://")):
        return "OUT"
    if cand in files:
        return cand
    hit = [f for f in files if os.path.basename(f) == os.path.basename(cand)]
    if hit:
        return hit[0]
    return "!" + cand


def prev_name(text, i):
    """the nearest name to the pointer's left inside its own sentence - a chain

    The tree writes `*A* -> *B*`: B is a name *inside* the section A names, so the
    carrier B is read in is A's, not any path in the sentence.
    """
    sent = sentence_before(text, i)
    base = i - len(sent)
    m = re.search(r"\*([^*\n]{2,90}?)\*\s*(?:\u2192|->)?\s*$", sent)
    return (m.group(1).strip() if m else None), base


def scan(root, files):
    allfiles = tracked(root, [])
    texts = {f: io.open(os.path.join(root, f), encoding="utf-8").read()
             for f in files}
    lines = {f: name_lines(t) for f, t in texts.items()}
    rows = []
    for f in files:
        t = texts[f]
        covered = []
        for m in CODE_TARGET.finditer(t):
            rows.append((f, t.count("\n", 0, m.start()) + 1, m.group(0).strip(),
                         "code-target"))
            covered.append((m.start(), m.end()))
        for m in POINTER.finditer(t):
            if any(a <= m.start() < b for a, b in covered):
                continue
            ln = t.count("\n", 0, m.start()) + 1
            name = m.group("name").strip()
            car = carrier_left(root, t, m.start(), files)
            selfname = [c for c in allfiles if os.path.basename(c) == norm(name)]
            if selfname:
                rows.append((f, ln, name, "names-a-carrier (%s)" % selfname[0]))
                continue
            if car == "OUT":
                rows.append((f, ln, name, "out-of-tree"))
                continue
            if car is None:
                prev, _ = prev_name(t, m.start())
                if prev:
                    # a chain: B is read in the carrier A lives in
                    car = next((g for g in files if resolves(prev, lines[g])), None)
                if car is None:
                    car = f                   # a bare `*Name*` reads in the linking file
            ok_car = car in files and resolves(name, lines[car])
            ok_link = car != f and resolves(name, lines[f])
            if ok_car:
                rows.append((f, ln, name, "resolved"))
            elif ok_link:
                # the name is not in the carrier the sentence names: the linking file
                # holds it, either as a chain (`*A* → *B*`) or because the path read as
                # the carrier belongs to another clause
                rows.append((f, ln, name, "resolved (linking file, not %s)" % car))
            elif car.startswith("!"):
                rows.append((f, ln, name, "out-of-tree (%s)" % car[1:]))
            else:
                rows.append((f, ln, name, "UNRESOLVED in " + car))
    return rows


def report(rows):
    """every class counted and named, then the members of the classes that need a reader"""
    kinds = {}
    for r in rows:
        kinds[r[3]] = kinds.get(r[3], 0) + 1
    print("pointgate_v1 - the tree's named pointers (`-> *Name*`, `see *Name*`), "
          "resolved at the carrier they name")
    print("rule: README.md -> Links; a name resolves on a heading, a lead (line- or "
          "sentence-initial) or a blockquote item\n"
          "      of the named carrier, read as rendered text and compared to the "
          "break before the lead's gloss")
    print("set: the tracked markdown carriers (`git ls-files '*.md'`)")
    print("pointers=%d" % len(rows))
    for k in sorted(kinds):
        print("  %-44s %d" % (k, kinds[k]))
    print()
    bad = 0
    for f, ln, name, v in rows:
        if not v.startswith("resolved") and not v.startswith("code-target"):
            bad += 1
            print("  %s:%d  *%s*  -> %s" % (f, ln, name.strip()[:60], v))
    print()
    print("not read here: the rule's first form (a markdown link target - "
          "`.github/tools/linkgate.py`)")
    print("not read here: the rule's third form (a number indexing a list - "
          "`.github/tools/numgate.py` reads the site and the list it indexes; "
          "the position it means is a read)")
    return bad


def selftest(root):
    ok = []
    bad = []

    def case(got, want, label):
        (ok if got == want else bad).append(label)

    case(resolves("Quality bar", name_lines("# Quality bar (non-negotiable)\n")), True,
         "a name on a heading resolves")
    case(resolves("A read that reports an absence",
                  name_lines("**A read that reports an absence.**\n")), True,
         "a name on a bold lead resolves")
    case(resolves("Anchor accuracy", name_lines("- **Anchor accuracy** - every cited\n")),
         True, "a bold lead behind a list marker resolves")
    case(resolves("How to Register", name_lines("> **How to Register**\n")), True,
         "a name on a blockquote item resolves")
    case(resolves("No Such Section Anywhere",
                  name_lines("# Quality bar\n**Presentation requirements.**\n")), False,
         "a name in no such line does not resolve")
    case(resolves("Citation mechanics",
                  name_lines("    **Citation mechanics.** *Counting.* Count the entries\n")),
         True, "a bold lead behind indentation resolves")
    case(resolves("What makes a concern major",
                  name_lines("**What makes a concern *major*.** The criterion above\n")), True,
         "a target's own inline emphasis is not part of its name")
    case(resolves("A review's concerns are one set",
                  name_lines("- ***A review's concerns are one set, and its list.***\n")), True,
         "a name ends where its gloss begins (a comma)")
    case(resolves("Citation key", name_lines("*Citation key.* Every entry carries\n")), True,
         "an italic lead resolves")
    case(resolves("Citation key",
                  name_lines("occurrence count. *Citation key.* Every entry carries\n")), True,
         "a lead at the start of a sentence, mid-line, resolves")
    case(resolves("A path is not an artefact",
                  name_lines("**A path is not an artefact - the copy a tree\ncarries is the "
                             "one that is read, and an export of a *branch*\nwhose `main` "
                             "differs.** rest\n")), True,
         "a bold lead wrapped across source lines resolves")
    files = tracked(root, ["*.md"])
    ch = "`README.md` → *Quality bar*"
    case(carrier_left(root, ch, len(ch) - 1, files), "README.md",
         "the carrier is the path to the pointer's left")
    ch2 = "`README.md` → *X* and `INSTANCES.md` → *Y*"
    case(carrier_left(root, ch2, len(ch2) - 1, files), "INSTANCES.md",
         "the nearest path to the left is read, not the first in the sentence")
    case(carrier_left(root, "see *A read that reports an absence* below", 3, files),
         None, "a sentence naming no carrier leaves the name to the linking file")
    rows = scan(root, files)
    case(any(r[3] == "code-target" for r in rows), True,
         "a code-span arrow is classed and not decided")
    case(any(r[3].startswith("resolved (linking file") for r in rows), True,
         "a name read in the linking file is classed apart from the named carrier")
    ch = "`README.md` → *A* → *B*"
    case(carrier_left(root, ch, len(ch) - 1, files), "README.md",
         "a path in the sentence is the carrier for the name that follows it")
    for label in ok:
        print("  ok   %s" % label)
    for label in bad:
        print("  FAIL %s" % label)
    print("cases: %d ok, %d fail" % (len(ok), len(bad)))
    print("POINTGATE SELFTEST: %s" % ("PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


def main(argv):
    root = repo_root()
    if "--selftest" in argv:
        return selftest(root)
    rows = scan(root, tracked(root, ["*.md"]))
    bad = report(rows)
    rc = 0 if bad == 0 else 1
    if "--check" in argv:
        print("POINTGATE: %s" % ("PASS" if rc == 0 else "FAIL"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
