#!/usr/bin/env python3
"""Issue #47 -- is every output this report quotes attributed to a copy of the journal's gate?

    python3 gate_read_v1.py            # check: the report's quotes are attributed to named copies
    python3 gate_read_v1.py --selftest # liveness: one planted wrong statement per case

WHY THIS FILE EXISTS.  The journal's citation gate is not vendored into this package: `reproduce.sh`
reads it at `../../.github/tools/refgate.py`, so the copy it runs is **the one the reader's tree
carries** -- and a path does not fix which copy that is.  `reference-check.md` quoted an output and
named "the head this file was generated at": a revision of THIS package, not of the tool.  The quote
was therefore a claim about an instrument that did not say which instrument.  Measured 2026-09-17 and
re-takeable from this tree: the manuscript branch never touches `.github/`, so an export of the branch
carries its BASE's copy of the gate, and the two copies differ in ways a reader would otherwise read as
the author's omissions -- the base copy prints **no** `window:` line and its `--selftest` holds fewer
cases than the journal `main` copy, while both return the same verdict on this manuscript.

WHAT IS CHECKED, and against what.  The check reads ONE artefact, `reference-check.md`, against itself.
A quote is attributed when it carries a named instrument, and a name is complete when it carries a
revision:

* **every `copy:` line names the revision it was read at.**  A reading that names no revision is a
  claim about an unnamed copy -- the defect this file exists for, in the form the report carried when
  this round opened: its primary line named a copy and did not say which revision of it.
* **every quoted gate run has its own `copy:` line above it.**  A quoted run with no `copy:` line
  before it, or a second quoted run sharing the first one's, is an output attributed to no instrument.
* **the report states the absent-tree fact** (`not in this tree`): a reader whose tree carries no
  `.github/` is otherwise told nothing about what step 7 does there.  Required in EVERY tree since
  correction round 3 -- the statement is about the report and about every reader's tree, so it is not
  conditional on the one that happens to lack `.github/`.

WHAT IS *NOT* CHECKED, and why -- the durability requirement of correction round 3.  This check does
**not** require the report to name the copy THIS tree carries, and it does not compare the report's
quote against that copy.  `.github/tools/refgate.py` is the journal's file and it moves as ordinary
journal work -- four revisions in five days while this round was open -- so a report required to
contain the identity of a copy outside its own tree goes red on every one of those edits, and the
re-take this round was opened with buys exactly ONE such edit.  The copy a reader's tree carries is
read where it exists: by the reader's OWN run (`reproduce.sh` step 7 prints the path it is about to
run, then runs it) and, when the tree carries one, printed here as a `reading:` line.  That line is an
OBSERVATION and never part of the verdict -- a journal edit to the gate cannot turn this check red,
because this check reads the report and nothing else.  The copy's own verdict is taken where the copy
runs, which is the only place that can take it.

The battery plants one wrong statement per case -- a missing revision on the primary line, a missing
revision on the other line, an orphaned quote, a second quote sharing the first one's name, a report
with no `copy:` line at all, and the absent-tree statement moved to a near-miss.  Each is DERIVED from
the report rather than pinned, and each arm of the check above has exactly one case that must fire it.
Every case is derivable in every tree, so this is the same battery in a checkout of the journal and in
a path-limited export of the package, and a run in which no case could be derived fails outright.
"""
import hashlib
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.normpath(os.path.join(HERE, "..", "..", ".github", "tools", "refgate.py"))
REPORT = os.path.join(HERE, "reference-check.md")
MANUSCRIPT = "manuscript.md"
ABSENT_ANCHOR = "not in this tree"
CHECK = "gate_read/quotes_are_attributed"

# A quoted gate run, in the shape the report prints one: a fence whose body carries the gate's verdict.
# Read as a fence, not as a line, so a run split across lines is one quote rather than several.
FENCED_RUN = r"(?ms)^```[^\n]*\n(.*?)^```[ \t]*$"
COPY_LINE = r"(?m)^copy: .*$"


def run(args, cwd=HERE):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.stdout + p.stderr, p.returncode


def reading(path):
    """The copy THIS tree carries, by RUNNING it -- an observation, never a verdict.

    Four facts and the copy's own output are read off the copy itself, the way the reader's own run
    reads them.  Nothing here can turn the check red: see WHAT IS NOT CHECKED above.
    """
    raw = io.open(path, "rb").read()
    src = raw.decode("utf-8")
    st, rc = run([sys.executable, path, "--selftest"])
    m = re.search(r"selftest: (\d+)/(\d+) cases ok", st)
    cases = ("--selftest %s/%s cases ok" % (m.group(1), m.group(2)) if m
             else "--selftest printed no `N/N cases ok` line (exit %d)" % rc)
    out, _ = run([sys.executable, path, MANUSCRIPT])
    window = ("prints the window line" if any(l.strip().startswith("window:")
                                             for l in out.splitlines()) else "prints no window line")
    return ("reading: %s -- %d lines, sha256 %s\u2026, %s, %s\n"
            "         (the copy THIS tree carries, taken by running it here; the report is not required "
            "to name this copy, and this line is not part of the verdict)"
            % (os.path.relpath(path, HERE), src.count("\n"),
               hashlib.sha256(raw).hexdigest()[:12], cases, window))


def copies_of(text):
    """[(start, end, line)] for every `copy:` line of the report."""
    return [(m.start(), m.end(), m.group(0)) for m in re.finditer(COPY_LINE, text)]


def runs_of(text):
    """The quoted gate runs of the report, as match objects in document order."""
    return [m for m in re.finditer(FENCED_RUN, text) if "GATE:" in m.group(1)]


def check(text):
    """The report against itself: every quote attributed, every name carrying a revision."""
    copies = copies_of(text)
    if not copies:
        return False, ("the report carries no `copy:` line, so any run it quotes is attributed to no "
                       "instrument -- the defect this file exists for")
    nameless = [l for _, _, l in copies if "read at " not in l]
    if nameless:
        return False, ("%d of %d `copy:` line(s) name no revision: %s -- a reading that names no "
                       "revision is a claim about an unnamed copy, which is the defect this file "
                       "exists for" % (len(nameless), len(copies), "; ".join(nameless[:2])))
    runs = runs_of(text)
    for i, r in enumerate(runs):
        above = [c for c in copies if c[0] < r.start()]
        if not above:
            return False, ("the run quoted at character %d carries no `copy:` line above it: a quote "
                           "attributed to no instrument" % r.start())
        if i and above[-1][0] < runs[i - 1].end():
            return False, ("the run quoted at character %d shares the `copy:` line of the run at "
                           "character %d: each quoted run owes its own named copy"
                           % (r.start(), runs[i - 1].start()))
    if ABSENT_ANCHOR not in text:
        return False, ("the report does not state the absent-tree fact (%r): a reader whose tree "
                       "carries no `.github/` is told nothing about what step 7 does there"
                       % ABSENT_ANCHOR)
    return True, ("%d `copy:` line(s), each naming the revision it was read at; %d quoted run(s), each "
                  "attributed to the copy named above it; the absent-tree fact is stated"
                  % (len(copies), len(runs)))


# One check, named by this module's own list (so the count a reader states about this tool's battery
# is the tool's own -- `readme_check_v1.py` asks for it).
CHECKS = [CHECK]

# One planted wrong statement per case, each DERIVED from the report in hand rather than pinned: a
# pinned anchor turns a legitimate edit of the report into a red battery.  The cases are chosen so
# that EVERY arm of `check()` above has exactly one case that must fire it, and no arm is left as
# decoration:
#
#   * `primary_revision` / `other_revision` -> the revision arm, on each of the report's two readings;
#   * `orphan_quote`  -> the arm requiring a `copy:` line above a quoted run;
#   * `shared_quote`  -> the arm requiring each quoted run to owe its own named copy;
#   * `no_copy`       -> the arm requiring the report to name a copy at all;
#   * `absent`        -> the arm requiring the absent-tree fact.
MUTATIONS = [
    (CHECK, "primary_revision"),
    (CHECK, "other_revision"),
    (CHECK, "orphan_quote"),
    (CHECK, "shared_quote"),
    (CHECK, "no_copy"),
    (CHECK, "absent"),
]


def strip_revision(line):
    """The line without its `, read at <rev>` -- the shape the report carried when this round opened."""
    return re.sub(r", read at \S+", "", line, count=1)


def cut_line(text, start, end):
    """The text without the line at [start, end) and the newline that ended it."""
    return text[:start] + text[end:].lstrip("\n")


def plant(kind, text):
    """The report with one statement broken, or None where this report cannot carry that case."""
    cs = copies_of(text)
    if kind in ("primary_revision", "other_revision"):
        if not cs or (kind == "other_revision" and len(cs) < 2):
            return None
        s, e, line = cs[0] if kind == "primary_revision" else cs[-1]
        new = strip_revision(line)
        return (text[:s] + new + text[e:]) if new != line else None
    if kind == "orphan_quote":
        # The `copy:` line that owns the report's first quoted run goes, and the quote stays: an
        # output attributed to no instrument.
        if not cs:
            return None
        s, e, _ = cs[0]
        return cut_line(text, s, e)
    if kind == "shared_quote":
        # A second quoted run, put directly under the first: it has a `copy:` line above it, but not
        # its own, so nothing names the instrument it came from.
        runs = runs_of(text)
        if not runs:
            return None
        r = runs[0]
        return text[:r.end()] + "\n" + text[r.start():r.end()] + text[r.end():]
    if kind == "no_copy":
        if not cs:
            return None
        out = text
        for s, e, _ in reversed(cs):
            out = cut_line(out, s, e)
        return out
    if kind == "absent":
        # EVERY occurrence goes -- the statement carries the anchor twice, and a planter that replaced
        # only the first left the read satisfied (measured in correction round 2: the case read
        # "NOT caught" the first time it ran, because the second occurrence still answered the test).
        if ABSENT_ANCHOR not in text:
            return None
        return text.replace(ABSENT_ANCHOR, "absent from this export")
    raise AssertionError(kind)


def main():
    text = io.open(REPORT, encoding="utf-8").read()
    if os.path.exists(GATE):
        print(reading(GATE))
    else:
        print("reading: %s\n         -- not in this tree: a path-limited export of this package carries "
              "no `.github/`, and the report states that fact in a paragraph of its own"
              % GATE)
    ok, detail = check(text)
    print("%s   %s   %s" % ("PASS" if ok else "FAIL", CHECK, detail))
    return 0 if ok else 1


def selftest():
    text = io.open(REPORT, encoding="utf-8").read()
    base_ok, base_detail = check(text)
    if not base_ok:
        print("FAIL   the battery needs a clean base; already failing: %s" % base_detail)
        return 1
    print("%-6s %-56s %s" % ("PASS", "control/unmodified_report", base_detail[:90]))
    bad = 0
    for name, kind in MUTATIONS:
        label = "%s [%s]" % (name, kind)
        planted = plant(kind, text)
        if planted is None:
            print("FAIL   %-56s the case could not be derived from the report in hand" % label)
            bad += 1
            continue
        if planted == text:
            print("FAIL   %-56s the planted report is identical to the shipped one" % label)
            bad += 1
            continue
        was_ok, was_detail = check(planted)
        good = not was_ok
        print("%-6s %-56s %s" % ("PASS" if good else "FAIL", label,
                                 ("caught: " + was_detail[:56]) if good else "NOT caught"))
        bad += 0 if good else 1
    print("selftest: %d case(s), %d failure(s) over 1 check" % (len(MUTATIONS) + 1, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
